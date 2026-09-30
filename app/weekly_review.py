"""Weekly recap calculated from recorded local data; no inferred missing values."""
from datetime import date,timedelta
from html import escape

def last_week(today=None):
    today=today or date.today();return today-timedelta(days=today.weekday()+7)

def duration(seconds):
    minutes=round(seconds/60);return f'{minutes//60} h {minutes%60:02} min'

def summary(storage,start=None,today=None):
    today=today or date.today();start=start or last_week(today);start-=timedelta(days=start.weekday())
    if start+timedelta(days=6)>=today:raise ValueError('Choose a completed week.')
    days=[start+timedelta(days=i) for i in range(7)];result={'start':start,'end':days[-1],'activities':{},'has_data':False,'edited_days':0}
    for kind in ('work','learning'):
        values=[storage.seconds_for_day(kind,d.isoformat()) for d in days];known=[storage.has_activity_record(kind,d.isoformat()) for d in days];target=storage.target(kind)*3600
        hits=[k and v>=target for k,v in zip(known,values)];longest=run=0
        for hit in hits:run=run+1 if hit else 0;longest=max(longest,run)
        previous_days=[d-timedelta(days=7) for d in days];previous_known=sum(storage.has_activity_record(kind,d.isoformat()) for d in previous_days)
        previous=sum(storage.seconds_for_day(kind,d.isoformat()) for d in previous_days)
        best=max(range(7),key=lambda i:values[i]) if any(v>0 for v in values) else None
        result['activities'][kind]={'values':values,'known':known,'total':sum(values),'recorded':sum(known),'goal_days':sum(hits),'streak':longest,'best':None if best is None else (days[best],values[best]),'previous':previous if previous_known else None,'previous_recorded':previous_known}
        result['has_data']|=any(known)
    creatives=[];meal_values=[];complete_meals=0;sleep=[]
    for day in days:
        key=day.isoformat();value=storage.manual_value('creatives',key)
        if value is not None:creatives.append(value)
        meals=[storage.manual_value(k,key) for k in ('breakfast','lunch','dinner')];meal_values.extend(v for v in meals if v is not None);complete_meals+=all(v==1 for v in meals)
        minutes=storage.existing_day(key).get('sleep_minutes')
        if minutes is not None:sleep.append(minutes)
        result['edited_days']+=bool(storage.conn.execute('SELECT 1 FROM edit_history WHERE day=? LIMIT 1',(key,)).fetchone())
    result.update(creatives=sum(creatives),creative_days=len(creatives),meals=sum(meal_values),meal_entries=len(meal_values),complete_meal_days=complete_meals,sleep_average=sum(sleep)/len(sleep) if sleep else None,sleep_nights=len(sleep))
    result['has_data']|=bool(creatives or meal_values or sleep)
    return result

from PySide6.QtCore import QDate
from PySide6.QtGui import QPainter,QColor
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QDateEdit,QTextBrowser

class WeeklyReview(QWidget):
    def __init__(self,window):
        super().__init__(window);self.window=window;root=QVBoxLayout(self);root.setContentsMargins(16,18,16,36)
        back=QPushButton('‹ Settings');back.clicked.connect(window.return_to_settings);root.addWidget(back)
        title=QLabel('Your week in PACT');title.setStyleSheet('font-size:24px;font-weight:bold;');root.addWidget(title)
        nav=QHBoxLayout();previous=QPushButton('‹');previous.setAccessibleName('Previous week');previous.clicked.connect(lambda:self.week.setDate(self.week.date().addDays(-7)));nav.addWidget(previous)
        self.week=QDateEdit(QDate(last_week()));self.week.setCalendarPopup(True);self.week.setDisplayFormat('dd MMM yyyy');self.week.setMinimumDate(QDate(2000,1,3));self.week.setMaximumDate(QDate(last_week()+timedelta(days=6)));nav.addWidget(self.week,1)
        self.next=QPushButton('›');self.next.setAccessibleName('Next week');self.next.clicked.connect(lambda:self.week.setDate(self.week.date().addDays(7)));nav.addWidget(self.next);root.addLayout(nav)
        self.body=QTextBrowser();self.body.setOpenExternalLinks(False);root.addWidget(self.body);self.week.dateChanged.connect(self.reload);self.reload()
    def paintEvent(self,event):
        from panels import colors
        p=QPainter(self);p.fillRect(self.rect(),QColor(colors(self.window)[0]));p.end()
    def flush(self):pass
    def reload(self,*args):
        from panels import colors
        r=summary(self.window.storage,self.week.date().toPython());self.week.blockSignals(True);self.week.setDate(QDate(r['start']));self.week.blockSignals(False);self.next.setEnabled(r['start']<last_week())
        _,ink=colors(self.window);rule=f'<hr color="{ink}">';parts=[f"<p>{r['start']:%d %b} – {r['end']:%d %b %Y}</p>"]
        if not r['has_data']:parts.append('<h2>No recorded data for this week yet.</h2><p>Imported or corrected entries will appear here automatically.</p>')
        else:
            for kind,a in r['activities'].items():
                parts.append(f'<h2>{kind.title()} · {duration(a["total"])}</h2><p>{a["recorded"]}/7 days recorded · {a["goal_days"]} days reached your current goal.<br>Longest goal streak this week: {a["streak"]} days.</p>')
                if a['best']:parts.append(f'<p>Busiest day: {a["best"][0]:%A, %d %b} · <b>{duration(a["best"][1])}</b></p>')
                if a['previous'] is not None:
                    delta=a['total']-a['previous'];parts.append(f'<p>{duration(abs(delta))} {"more" if delta>=0 else "less"} than the previous week ({a["previous_recorded"]}/7 days recorded).</p>')
                parts.append(rule)
            parts.append('<h2>Daily habits</h2>')
            parts.append(f'<p>Creatives: <b>{r["creatives"]}</b> across {r["creative_days"]} days with entries.<br>Meals checked: <b>{r["meals"]}</b> from {r["meal_entries"]}/21 recorded meal entries.<br>All three meals checked on {r["complete_meal_days"]} days.</p>')
            parts.append('<h2>Sleep</h2><p>'+('No sleep records.' if r['sleep_average'] is None else f'Average: <b>{duration(r["sleep_average"]*60)}</b> across {r["sleep_nights"]} recorded nights.')+'</p>'+rule)
            parts.append('<h2>Day by day</h2>')
            for i in range(7):
                day=r['start']+timedelta(days=i);values=[]
                for kind,a in r['activities'].items():values.append(kind.title()+': '+(duration(a['values'][i]) if a['known'][i] else 'Not recorded'))
                parts.append(f'<p><b>{day:%A, %d %b}</b><br>'+escape(' · '.join(values))+'</p>')
            parts.append(rule+f'<p>{r["edited_days"]} dates have edits/imports. Review them in Edit history. Goals use your current targets. Missing entries are not treated as failures.</p>')
        self.body.setHtml(''.join(parts))
