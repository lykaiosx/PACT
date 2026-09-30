"""One highlight per animated, theme-native PACT story slide."""
import calendar,math
from datetime import date,timedelta
from PySide6.QtCore import Qt,QDate,QRectF,QPointF,QTimer,QVariantAnimation,QEasingCurve
from PySide6.QtGui import QPainter,QColor,QPen,QFont,QFontMetricsF
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QComboBox,QDateEdit,QLabel

def compact(seconds):
    minutes=round(seconds/60);return f'{minutes//60}h'+(f' {minutes%60:02}m' if minutes%60 else '')

def make_slides(s,mode,selected,today=None):
    from weekly_review import summary
    today=today or date.today()
    if mode=='Monthly':
        start=selected.replace(day=1);last=start.replace(day=calendar.monthrange(start.year,start.month)[1]);end=min(last,today);r=summary(s,start,today,end);partial=end>=today;period=f'{start:%B %Y}'+(' · so far' if partial else '')
    else:r=summary(s,selected,today);partial=False;period=f'{r["start"]:%d %b} – {r["end"]:%d %b %Y}'
    n=len(r['days']);work=r['activities']['work'];learning=r['activities']['learning'];best=work['best'];edited='Includes edited/imported entries.' if r['edited_days'] else 'Based on your recorded entries.'
    slides=[
      dict(tag='YOUR PACT, REVISITED',title='Small days.\nA bigger picture.',metric=f'{r["covered_days"]}',unit='days with a story',graphic='orbit',values=[],note=period,detail=edited if r['has_data'] else 'No recorded data for this period yet.'),
      dict(tag='THE WORK YOU PUT IN',title='You made\ntime count.',metric=compact(work['total']) if work['recorded'] else '—',unit='of recorded work',graphic='bars',values=work['values'],note=f'{work["recorded"]} of {n} days recorded',detail='Every bar is one day. Unrecorded days stay blank.'),
      dict(tag='YOUR STANDOUT DAY',title='One day\nstood taller.',metric=compact(best[1]) if best else '—',unit='on your busiest work day',graphic='peak',values=work['values'],note=best[0].strftime('%A, %d %B') if best else 'No work time recorded yet',detail='Your highest recorded work total in this period.'),
      dict(tag='ROOM TO GROW',title='You kept\nyour curiosity.',metric=compact(learning['total']) if learning['recorded'] else '—',unit='of recorded learning',graphic='steps',values=learning['values'],note=f'{learning["recorded"]} of {n} days recorded',detail='One step, one session, one thing learned.' if learning['total'] else 'Your next learning session starts the story.'),
      dict(tag='SHOWING UP',title='Consistency\nhas a rhythm.',metric=str(work['streak']) if work['recorded'] else '—',unit='days in your longest work-goal streak',graphic='grid',values=[int(k and v>=s.target('work')*3600) for k,v in zip(work['known'],work['values'])],note=f'{work["goal_days"]} work-goal days in total',detail=f'Filled squares met your current {s.target("work"):g}h work target. Missing days do not extend a streak.'),
      dict(tag='THINGS YOU CREATED',title='Ideas became\nsomething real.',metric=str(r['creatives']) if r['creative_days'] else '—',unit='creatives recorded',graphic='tiles',values=r['creative_values'],note=f'{r["creative_days"]} of {n} days with entries',detail='One square for each creative.' if r['creatives']<=64 else 'The first 64 creatives, one square at a time.'),
      dict(tag='THE EVERYDAY BASICS',title='You made room\nfor yourself.',metric=str(r['meals']) if r['meal_entries'] else '—',unit='meals checked in',graphic='meals',values=r['meal_types'],note=f'{r["complete_meal_days"]} days with all three meals checked',detail=f'{r["meal_entries"]} of {n*3} meal entries recorded. Empty entries are unknown.'),
      dict(tag='TIME TO RECHARGE',title='Rest was part\nof the picture.',metric=compact(r['sleep_average']*60) if r['sleep_average'] is not None else '—',unit='average recorded sleep',graphic='moon',values=r['sleep_values'],note=f'{r["sleep_nights"]} recorded nights',detail='From Garmin sleep records. Here’s to your next chapter.' if r['sleep_nights'] else 'No sleep records for this period yet.')]
    for slide in slides:
        if slide['metric']=='—':slide['title']='A chapter\nstill unwritten.'
    return slides,period,r

class StoryCanvas(QWidget):
    def __init__(self,owner):
        super().__init__();self.owner=owner;self.setMinimumSize(180,250);self.setFocusPolicy(Qt.StrongFocus)
    def paintEvent(self,event):
        from panels import colors,intensity_colors
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing);bg,ink=colors(self.owner.window);p.fillRect(self.rect(),QColor(bg));scale=min(self.width()/360,self.height()/600);p.translate((self.width()-360*scale)/2,(self.height()-600*scale)/2);p.scale(scale,scale);p.setClipRect(QRectF(0,0,360,600))
        t=self.owner.progress;previous=self.owner.previous
        if previous is not None and t<1:
            p.save();p.translate(-self.owner.direction*360*t,0);self.draw(p,self.owner.slides[previous],1,bg,ink);p.restore()
        p.save();p.translate(self.owner.direction*360*(1-t) if previous is not None else 0,0)
        if previous is None:p.setOpacity(t)
        self.draw(p,self.owner.slides[self.owner.index],t,bg,ink);p.restore();p.end()
    def draw(self,p,s,t,bg,ink):
        fg=QColor(ink);paper=QColor(bg)
        def text(y,h,value,size=18,bold=False,italic=False,fit=True):
            font=QFont('Newsreader');font.setPixelSize(size);font.setBold(bold);font.setItalic(italic)
            while fit and size>10 and max(QFontMetricsF(font).horizontalAdvance(line) for line in value.split('\n'))>320:size-=1;font.setPixelSize(size)
            p.setFont(font);p.setPen(fg);p.drawText(QRectF(20,y,320,h),Qt.AlignHCenter|Qt.AlignVCenter|Qt.TextWordWrap,value)
        p.setPen(QPen(fg,1));p.drawLine(QPointF(20,36),QPointF(340,36));text(9,20,s['tag'],11)
        text(52,92,s['title'],39,False,True);text(149,89,s['metric'],78,True);text(242,36,s['unit'],17)
        p.save();p.setClipRect(QRectF(20,292,320,190));p.setPen(QPen(fg,1.2));p.setBrush(fg);kind=s['graphic'];values=s['values'];grow=max(.03,t)
        if kind=='orbit':
            p.setBrush(Qt.NoBrush)
            for i in range(5):
                w=170-i*28;p.drawEllipse(QRectF(180-w/2,385-w/2,w,w))
            angle=t*math.pi*1.5;p.setBrush(fg);p.drawEllipse(QPointF(180+72*math.cos(angle),385+72*math.sin(angle)),11,11)
        elif kind in ('bars','steps'):
            vals=[v or 0 for v in values];maximum=max(vals,default=0) or 1;slot=300/max(1,len(vals));bar=max(2,slot*.65)
            p.drawLine(QPointF(30,460),QPointF(330,460))
            for i,v in enumerate(vals):
                height=140*v/maximum*grow
                if kind=='steps':
                    p.setBrush(Qt.NoBrush);p.drawRect(QRectF(30+i*slot,460-height,bar,max(1,height))) if v else None
                elif v:p.fillRect(QRectF(30+i*slot,460-height,bar,height),fg)
        elif kind=='peak':
            if any(values):
                for i in range(18):
                    a=2*math.pi*i/18;p.drawLine(QPointF(180+52*math.cos(a),385+52*math.sin(a)),QPointF(180+(55+35*grow)*math.cos(a),385+(55+35*grow)*math.sin(a)))
                p.drawEllipse(QRectF(140,345,80,80))
            else:p.setBrush(Qt.NoBrush);p.drawEllipse(QRectF(140,345,80,80))
        elif kind=='tiles':
            count=min(64,sum(v or 0 for v in values));side=18;gap=5
            for i in range(count):
                p.setBrush(fg if i<count*grow else Qt.NoBrush);p.drawRect(QRectF(90+(i%8)*(side+gap),300+(i//8)*(side+gap),side,side))
            if not count:p.setBrush(Qt.NoBrush);p.drawRect(QRectF(144,350,72,72))
        elif kind=='grid':
            columns=7;rows=math.ceil(len(values)/columns);gap=7;size=min(32,(150-gap*(rows-1))/max(1,rows));left=180-(columns*(size+gap)-gap)/2
            for i,value in enumerate(values):
                p.setBrush(fg if value and i<len(values)*grow else Qt.NoBrush);p.drawRect(QRectF(left+(i%columns)*(size+gap),310+(i//columns)*(size+gap),size,size))
        elif kind=='meals':
            maximum=max(1,len(self.owner.report['days']))
            for i,value in enumerate(values):
                rect=QRectF(30+105*i,333,80,80);p.setBrush(Qt.NoBrush);p.drawEllipse(rect)
                if value:p.setBrush(fg);p.drawPie(rect,90*16,-round(360*16*value/maximum*grow))
                font=QFont('Newsreader');font.setPixelSize(13);p.setFont(font);p.drawText(QRectF(20+105*i,425,100,30),Qt.AlignCenter,('Breakfast','Lunch','Dinner')[i])
        elif kind=='moon':
            if any(v is not None for v in values):
                p.setPen(Qt.NoPen);p.setBrush(fg);p.drawEllipse(QRectF(101,310,156,156));p.setBrush(paper);p.drawEllipse(QRectF(138+10*grow,292,143,143));p.setBrush(fg)
                for x,y,r in [(88,331,3),(264,419,4),(285,333,2)]:p.drawEllipse(QPointF(x,y),r,r)
            else:p.setBrush(Qt.NoBrush);p.drawEllipse(QRectF(101,310,156,156))
        p.restore();text(490,36,s['note'],18,True);text(532,56,s['detail'],14,fit=False)
    def keyPressEvent(self,event):self.owner.keyPressEvent(event)

class WrappedReview(QWidget):
    def __init__(self,window):
        super().__init__(window);self.window=window;self.index=0;self.previous=None;self.progress=1.;self.direction=1;self.slides=[];root=QVBoxLayout(self);root.setContentsMargins(12,14,12,22);root.setSpacing(8)
        top=QHBoxLayout();back=QPushButton('‹');back.setAccessibleName('Back to Settings');back.clicked.connect(window.return_to_settings);top.addWidget(back);self.mode=QComboBox();self.mode.addItems(['Monthly','Weekly']);top.addWidget(self.mode,1);self.play=QPushButton('Play');self.play.setCheckable(True);self.play.toggled.connect(self.toggle_play);top.addWidget(self.play);root.addLayout(top)
        nav=QHBoxLayout();prev=QPushButton('‹');prev.setAccessibleName('Previous period');prev.clicked.connect(lambda:self.move_period(-1));nav.addWidget(prev);self.date=QDateEdit(QDate.currentDate());self.date.setCalendarPopup(True);self.date.setMinimumDate(QDate(2000,1,3));self.date.setMaximumDate(QDate.currentDate());self.date.setDisplayFormat('MMM yyyy');nav.addWidget(self.date,1);self.next_period=QPushButton('›');self.next_period.setAccessibleName('Next period');self.next_period.clicked.connect(lambda:self.move_period(1));nav.addWidget(self.next_period);root.addLayout(nav)
        self.period_note=QLabel();self.period_note.setAlignment(Qt.AlignCenter);root.addWidget(self.period_note)
        self.canvas=StoryCanvas(self);root.addWidget(self.canvas,1);dots=QHBoxLayout();dots.setSpacing(4);self.dots=[]
        for i in range(8):
            b=QPushButton();b.setFixedHeight(9);b.setAccessibleName(f'Go to slide {i+1}');b.clicked.connect(lambda _,n=i:self.go(n));dots.addWidget(b);self.dots.append(b)
        root.addLayout(dots);bottom=QHBoxLayout();self.back_slide=QPushButton('Previous');self.back_slide.clicked.connect(lambda:self.go(self.index-1));bottom.addWidget(self.back_slide);self.counter=QLabel();self.counter.setAlignment(Qt.AlignCenter);bottom.addWidget(self.counter,1);self.next_slide=QPushButton('Next');self.next_slide.clicked.connect(lambda:self.go(self.index+1));bottom.addWidget(self.next_slide);root.addLayout(bottom)
        self.animation=QVariantAnimation(self);self.animation.setDuration(650);self.animation.setStartValue(0.);self.animation.setEndValue(1.);self.animation.setEasingCurve(QEasingCurve.InOutCubic);self.animation.valueChanged.connect(self.animate);self.timer=QTimer(self);self.timer.setInterval(5500);self.timer.timeout.connect(self.advance);self.mode.currentIndexChanged.connect(self.change_mode);self.date.dateChanged.connect(self.reload);self.reload()
    def paintEvent(self,event):
        from panels import colors
        p=QPainter(self);p.fillRect(self.rect(),QColor(colors(self.window)[0]));p.end()
    def flush(self):pass
    def toggle_play(self,on):
        self.play.setText('Pause' if on else 'Play')
        if not hasattr(self,'timer'):return
        if on:
            if self.index==7:self.go(0)
            self.timer.start()
        else:self.timer.stop()
    def advance(self):
        if self.index==7:self.play.setChecked(False)
        else:self.go(self.index+1)
    def change_mode(self,*args):
        from weekly_review import last_week
        self.date.blockSignals(True);self.date.setDisplayFormat('MMM yyyy' if self.mode.currentIndex()==0 else 'dd MMM yyyy');self.date.setMaximumDate(QDate.currentDate() if self.mode.currentIndex()==0 else QDate(last_week()+timedelta(days=6)));self.date.setDate(QDate.currentDate() if self.mode.currentIndex()==0 else QDate(last_week()));self.date.blockSignals(False);self.reload()
    def move_period(self,step):self.date.setDate(self.date.date().addMonths(step) if self.mode.currentIndex()==0 else self.date.date().addDays(step*7))
    def reload(self,*args):
        from weekly_review import last_week
        self.animation.stop();self.play.setChecked(False);self.slides,self.period,self.report=make_slides(self.window.storage,self.mode.currentText(),self.date.date().toPython());self.index=0;self.previous=None;self.progress=0.
        self.period_note.setText(self.period);self.date.blockSignals(True);self.date.setDate(QDate(self.report['start']));self.date.blockSignals(False);self.next_period.setEnabled(self.report['start']<(date.today().replace(day=1) if self.mode.currentIndex()==0 else last_week()));self.controls();self.animation.start()
    def controls(self):
        from panels import colors
        bg,ink=colors(self.window);self.counter.setText(f'{self.index+1} / 8');self.back_slide.setEnabled(self.index>0);self.next_slide.setEnabled(self.index<7)
        for i,b in enumerate(self.dots):b.setStyleSheet(f'padding:0;border:1px solid {ink};background:{ink if i<=self.index else bg};')
        self.canvas.setAccessibleName(self.slides[self.index]['title'].replace('\n',' ')+' '+self.slides[self.index]['metric']+' '+self.slides[self.index]['unit'])
    def animate(self,value):self.progress=float(value);self.canvas.update()
    def go(self,index):
        if not 0<=index<8 or index==self.index:return
        self.animation.stop();self.previous=self.index;self.direction=1 if index>self.index else -1;self.index=index;self.progress=0.;self.controls();self.animation.start()
    def keyPressEvent(self,event):
        if event.key()==Qt.Key_Right:self.go(self.index+1)
        elif event.key()==Qt.Key_Left:self.go(self.index-1)
        elif event.key()==Qt.Key_Space:self.play.toggle()
        else:super().keyPressEvent(event)
    def hideEvent(self,event):
        self.play.setChecked(False);self.animation.stop();self.progress=1.;self.previous=None;self.canvas.update();super().hideEvent(event)
