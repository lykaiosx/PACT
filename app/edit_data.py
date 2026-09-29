"""Dated manual entries and a visible, preserved correction trail."""
import json
from PySide6.QtCore import QDate
from PySide6.QtWidgets import QWidget,QVBoxLayout,QFormLayout,QLabel,QComboBox,QSpinBox,QDateEdit,QPushButton,QTabWidget,QPlainTextEdit,QCheckBox
from time_editor import TimeEditor

def display_value(raw,field):
    value=json.loads(raw)
    if value is None:return 'Not entered / none'
    if field in ('breakfast','lunch','dinner'):return 'Yes' if value else 'No'
    if isinstance(value,dict):
        if value.get('type')=='daily':
            parts=[r['started_at'].replace('T',' ')+' to '+r['ended_at'].replace('T',' ') for r in value.get('sessions',[])]
            if value.get('imported'):parts.append(str(value['imported']['seconds'])+' imported seconds')
            return '; '.join(parts) or 'No time'
        if 'started_at' in value:return value['started_at'].replace('T',' ')+' to '+str(value.get('ended_at')).replace('T',' ')
    return str(value)

class EditHistory(QWidget):
    def __init__(self,window):
        super().__init__();self.window=window;self.limit=200;root=QVBoxLayout(self)
        note=QLabel('Local edit history. Undo stays in the history. Earlier unlogged changes cannot be reconstructed.');note.setWordWrap(True);root.addWidget(note)
        self.text=QPlainTextEdit();self.text.setReadOnly(True);root.addWidget(self.text)
        more=QPushButton('Show more history');more.clicked.connect(self.more);root.addWidget(more);self.reload()
    def more(self):self.limit+=200;self.reload()
    def reload(self):
        rows=self.window.storage.conn.execute('SELECT * FROM edit_history ORDER BY id DESC LIMIT ?',(self.limit,)).fetchall()
        self.text.setPlainText('\n\n'.join(f"{r['edited_at'].replace('T',' ')} · {r['action']}\n{r['day']} · {r['field'].title()}\nBefore: {display_value(r['before_json'],r['field'])}\nAfter: {display_value(r['after_json'],r['field'])}" for r in rows) or 'No recorded edits yet.')

class DailyEditor(QWidget):
    def __init__(self,window):
        super().__init__();self.window=window;self.loading=False;form=QFormLayout(self);form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        self.day=QDateEdit(QDate.currentDate());self.day.setCalendarPopup(True);self.day.setDisplayFormat('dd MMM yyyy');self.day.setMinimumDate(QDate(2000,1,1));self.day.setMaximumDate(QDate.currentDate());form.addRow('Date',self.day)
        self.summary=QLabel();self.summary.setWordWrap(True);form.addRow(self.summary)
        self.creatives=QSpinBox();self.creatives.setRange(-1,999999);self.creatives.setSpecialValueText('Not entered');self.creatives.setKeyboardTracking(False);form.addRow('Creatives',self.creatives)
        self.meals={}
        for field in ('breakfast','lunch','dinner'):
            box=QComboBox();box.addItems(['Not entered','No','Yes']);form.addRow(field.title(),box);self.meals[field]=box;box.currentIndexChanged.connect(lambda _,key=field:self.save(key))
        self.creatives.valueChanged.connect(lambda _:self.save('creatives'))
        self.health=QLabel();self.health.setWordWrap(True);form.addRow('Garmin · read-only',self.health)
        self.note=QLabel('Changes save automatically and appear in Edit history. Older zero entries without recording status appear as Not entered.');self.note.setWordWrap(True);form.addRow(self.note)
        undo=QPushButton('Undo last daily edit');undo.clicked.connect(self.undo);form.addRow(undo);self.day.dateChanged.connect(self.reload);self.reload()
    def reload(self,*args):
        self.loading=True;s=self.window.storage;day=self.day.date().toString('yyyy-MM-dd')
        value=s.manual_value('creatives',day);self.creatives.setValue(-1 if value is None else value)
        for field,box in self.meals.items():value=s.manual_value(field,day);box.setCurrentIndex(0 if value is None else 2 if value else 1)
        count=s.conn.execute('SELECT COUNT(*) FROM edit_history WHERE day=?',(day,)).fetchone()[0]
        totals=[]
        for kind in ('work','learning'):
            seconds=s.seconds_for_day(kind,day);totals.append(f'{kind.title()}: {seconds//3600} h {(seconds%3600)//60} min')
        self.summary.setText(' · '.join(totals)+f'\n{count} recorded edits/imports. See Edit history.');base=s.existing_day(day)
        self.health.setText(' · '.join(label+': '+str(base.get(key) if base.get(key) is not None else 'Not available') for key,label in [('sleep_minutes','Sleep minutes'),('steps','Steps'),('resting_hr','Resting HR')]))
        self.loading=False
    def save(self,field):
        if self.loading:return
        value=self.creatives.value() if field=='creatives' else self.meals[field].currentIndex()-1
        self.window.storage.edit_manual(field,None if value<0 else value,self.day.date().toString('yyyy-MM-dd'));self.window.history_at=0;self.window.refresh();self.reload()
    def undo(self):
        try:self.window.storage.undo_manual();self.window.history_at=0;self.window.refresh();self.reload();self.note.setText('Last daily edit undone. The undo is recorded in history.')
        except ValueError as e:self.note.setText(str(e))
    def flush(self):self.creatives.interpretText()

class EditData(QTabWidget):
    def __init__(self,window):
        super().__init__();self.daily=DailyEditor(window);self.time=TimeEditor(window,'work',embedded=True)
        from PySide6.QtWidgets import QScrollArea
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(self.daily);self.addTab(scroll,'Meals / creatives');self.addTab(self.time,'Work / learning');self.currentChanged.connect(lambda _:self.daily.reload())
    def flush(self):self.daily.flush()
