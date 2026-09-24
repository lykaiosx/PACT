"""Time correction panel, kept inside the PACT sidebar."""
from datetime import date,datetime,timedelta
from PySide6.QtCore import Qt,QDate,QDateTime
from PySide6.QtGui import QPainter,QColor
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QComboBox,QDateEdit,QDateTimeEdit,QFormLayout,QScrollArea,QDoubleSpinBox

class TimeEditor(QWidget):
    def __init__(self,window,kind):
        super().__init__(window);self.window=window;self.setAutoFillBackground(True)
        root=QVBoxLayout(self);root.setContentsMargins(16,18,16,36)
        head=QHBoxLayout();back=QPushButton('‹');back.clicked.connect(window.close_settings);head.addWidget(back);head.addWidget(QLabel('Correct time'),1);root.addLayout(head)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setFrameShape(QScrollArea.NoFrame);body=QWidget();form=QFormLayout(body);form.setRowWrapPolicy(QFormLayout.WrapLongRows);scroll.setWidget(body);root.addWidget(scroll)
        self.kind=QComboBox();self.kind.addItems(['Work','Learning']);self.kind.setCurrentText(kind.title());form.addRow('Activity',self.kind)
        self.day=QDateEdit(QDate.currentDate());self.day.setCalendarPopup(True);self.day.setDisplayFormat('dd MMM yyyy');self.day.setMaximumDate(QDate.currentDate());form.addRow('Date',self.day)
        self.sessions=QComboBox();self.sessions.setMinimumWidth(0);self.sessions.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon);form.addRow('Session',self.sessions)
        self.start=QDateTimeEdit();self.end=QDateTimeEdit()
        for label,field in [('Start',self.start),('End',self.end)]:field.setDisplayFormat('dd MMM yyyy HH:mm:ss');field.setCalendarPopup(True);form.addRow(label,field)
        self.apply=QPushButton('Add missed time');self.apply.clicked.connect(self.save);form.addRow(self.apply)
        self.subtract=QDoubleSpinBox();self.subtract.setRange(0.01,10000);self.subtract.setDecimals(2);self.subtract.setValue(2);self.subtract.setSuffix(' h');form.addRow('Deduct from end',self.subtract)
        self.deduct=QPushButton('Deduct time');self.deduct.clicked.connect(self.deduct_time);form.addRow(self.deduct)
        self.remove=QPushButton('Remove selected session');self.remove.clicked.connect(self.remove_session);form.addRow(self.remove)
        undo=QPushButton('Undo last correction');undo.clicked.connect(self.undo);form.addRow(undo)
        note=QLabel('Choose a recorded session to adjust it, or add missed time. Stop a running timer before editing its session. Changes update all charts and exports.');note.setWordWrap(True);form.addRow(note)
        self.message=QLabel('');self.message.setWordWrap(True);form.addRow(self.message)
        self.kind.currentIndexChanged.connect(self.reload);self.day.dateChanged.connect(self.reload);self.sessions.currentIndexChanged.connect(self.select);self.reload()
    def paintEvent(self,event):
        from panels import colors
        p=QPainter(self);p.fillRect(self.rect(),QColor(colors(self.window)[0]));p.end()
    def flush(self):pass
    def reload(self,*args):
        self.rows=self.window.storage.sessions_for_day(self.kind.currentText().lower(),self.day.date().toString('yyyy-MM-dd'))
        self.sessions.blockSignals(True);self.sessions.clear();self.sessions.addItem('Add missed time',None)
        for r in self.rows:self.sessions.addItem(r['started_at'].replace('T',' ')+' → '+(r['ended_at'].replace('T',' ') if r['ended_at'] else 'Running'),r['id'])
        self.sessions.blockSignals(False);self.select()
    def selected(self):return next((r for r in self.rows if r['id']==self.sessions.currentData()),None)
    def select(self,*args):
        r=self.selected();end=datetime.now().replace(microsecond=0) if self.day.date()==QDate.currentDate() else datetime.combine(self.day.date().toPython(),datetime.min.time())+timedelta(hours=12)
        start=end-timedelta(hours=1)
        if r:start=datetime.fromisoformat(r['started_at']);end=datetime.fromisoformat(r['ended_at']) if r['ended_at'] else datetime.now()
        self.start.setDateTime(QDateTime(start));self.end.setDateTime(QDateTime(end));running=bool(r and not r['ended_at'])
        self.apply.setText('Save correction' if r else 'Add missed time');self.apply.setEnabled(not running);self.deduct.setEnabled(bool(r) and not running);self.remove.setEnabled(bool(r) and not running)
    def changed(self,message):self.window.history_at=0;self.window.refresh();self.reload();self.message.setText(message)
    def save(self):
        try:self.window.storage.correct_session(self.kind.currentText().lower(),self.start.dateTime().toPython().isoformat(),self.end.dateTime().toPython().isoformat(),self.sessions.currentData());self.changed('Time saved. All totals are updated.')
        except ValueError as e:self.message.setText(str(e))
    def deduct_time(self):
        r=self.selected()
        if not r:return
        try:
            end=datetime.fromisoformat(r['ended_at'])-timedelta(seconds=round(self.subtract.value()*3600))
            self.window.storage.correct_session(r['kind'],r['started_at'],end.isoformat(),r['id']);self.changed('Time deducted. Undo is available below.')
        except ValueError as e:self.message.setText(str(e)+' To remove the whole session, use Remove selected session.')
    def remove_session(self):
        r=self.selected()
        if not r:return
        try:self.window.storage.correct_session(r['kind'],session_id=r['id'],remove=True);self.changed('Session removed. Undo is available below.')
        except ValueError as e:self.message.setText(str(e))
    def undo(self):
        try:self.window.storage.undo_time_edit();self.changed('Last correction undone.')
        except ValueError as e:self.message.setText(str(e))
