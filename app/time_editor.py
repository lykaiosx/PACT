"""Time correction panel, kept inside the PACT sidebar."""
from datetime import date,datetime,timedelta
from PySide6.QtCore import Qt,QDate,QDateTime,QTime
from PySide6.QtGui import QPainter,QColor
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QComboBox,QDateEdit,QDateTimeEdit,QFormLayout,QScrollArea,QDoubleSpinBox,QSpinBox,QTimeEdit

class TimeEditor(QWidget):
    def __init__(self,window,kind,embedded=False):
        super().__init__(window);self.window=window;self.setAutoFillBackground(True)
        if window.storage.get_setting('display_auto_adjust',False):self.setStyleSheet('QWidget{font-size:18px;}')
        root=QVBoxLayout(self);root.setContentsMargins(16,18,16,36)
        head=QHBoxLayout();back=QPushButton('‹');back.clicked.connect(window.close_settings);head.addWidget(back);head.addWidget(QLabel('Correct time'),1);root.addLayout(head)
        if embedded:back.hide();root.setContentsMargins(0,0,0,0)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setFrameShape(QScrollArea.NoFrame);body=QWidget();form=QFormLayout(body);form.setRowWrapPolicy(QFormLayout.WrapLongRows);scroll.setWidget(body);root.addWidget(scroll)
        self.kind=QComboBox();self.kind.addItems(['Work','Learning']);self.kind.setCurrentText(kind.title());form.addRow('Activity',self.kind)
        self.day=QDateEdit(QDate.currentDate());self.day.setCalendarPopup(True);self.day.setDisplayFormat('dd MMM yyyy');self.day.setMaximumDate(QDate.currentDate());form.addRow('Date',self.day)
        self.mode=QComboBox();self.mode.addItems(['Add time','Deduct time','Edit exact start / end']);form.addRow('I want to',self.mode)
        self.quick=QWidget();quick_form=QFormLayout(self.quick);quick_form.setContentsMargins(0,0,0,0);quick_form.setRowWrapPolicy(QFormLayout.WrapLongRows);form.addRow(self.quick)
        now=QTime.currentTime();initial=QTime(now.hour(),now.minute());initial=initial.addSecs(-1800) if now.hour() or now.minute()>=30 else QTime(0,0)
        self.quick_start=QTimeEdit(initial);self.quick_start.setDisplayFormat('h:mm AP');self.start_label=QLabel('Start at');quick_form.addRow(self.start_label,self.quick_start)
        amount=QWidget();amount_layout=QHBoxLayout(amount);amount_layout.setContentsMargins(0,0,0,0)
        self.hours=QSpinBox();self.hours.setRange(0,24);self.hours.setSuffix(' h');self.minutes=QSpinBox();self.minutes.setRange(0,59);self.minutes.setValue(30);self.minutes.setSuffix(' min')
        amount_layout.addWidget(self.hours);amount_layout.addWidget(self.minutes);quick_form.addRow('Amount',amount)
        self.preview=QLabel();self.preview.setWordWrap(True);quick_form.addRow(self.preview)
        self.quick_apply=QPushButton('Add time');self.quick_apply.clicked.connect(self.quick_save);quick_form.addRow(self.quick_apply)
        self.advanced=QWidget();advanced_form=QFormLayout(self.advanced);advanced_form.setContentsMargins(0,0,0,0);advanced_form.setRowWrapPolicy(QFormLayout.WrapLongRows);form.addRow(self.advanced)
        outer_form=form;form=advanced_form
        self.sessions=QComboBox();self.sessions.setMinimumWidth(0);self.sessions.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon);form.addRow('Session',self.sessions)
        self.start=QDateTimeEdit();self.end=QDateTimeEdit()
        for label,field in [('Start',self.start),('End',self.end)]:field.setDisplayFormat('dd MMM yyyy HH:mm:ss');field.setCalendarPopup(True);form.addRow(label,field)
        self.apply=QPushButton('Add missed time');self.apply.clicked.connect(self.save);form.addRow(self.apply)
        self.subtract=QDoubleSpinBox();self.subtract.setRange(0.01,10000);self.subtract.setDecimals(2);self.subtract.setValue(2);self.subtract.setSuffix(' h');form.addRow('Deduct from end',self.subtract)
        self.deduct=QPushButton('Deduct time');self.deduct.clicked.connect(self.deduct_time);form.addRow(self.deduct)
        self.remove=QPushButton('Remove selected session');self.remove.clicked.connect(self.remove_session);form.addRow(self.remove)
        form=outer_form
        undo=QPushButton('Undo last correction');undo.clicked.connect(self.undo);form.addRow(undo)
        note=QLabel('Changes update your charts and exports. Undo restores the last correction. Use Edit exact start / end for individual sessions.');note.setWordWrap(True);form.addRow(note)
        self.message=QLabel('');self.message.setWordWrap(True);form.addRow(self.message)
        self.kind.currentIndexChanged.connect(self.reload);self.day.dateChanged.connect(self.reload);self.sessions.currentIndexChanged.connect(self.select);self.reload()
        self.mode.currentIndexChanged.connect(self.update_quick)
        self.quick_start.timeChanged.connect(self.update_quick);self.hours.valueChanged.connect(self.update_quick);self.minutes.valueChanged.connect(self.update_quick);self.update_quick()
    def update_quick(self,*args):
        mode=self.mode.currentIndex();self.quick.setVisible(mode!=2);self.advanced.setVisible(mode==2);self.quick_start.setVisible(mode==0);self.start_label.setVisible(mode==0)
        self.quick_apply.setText('Add time' if mode==0 else 'Deduct time')
        if mode==0:
            start=datetime.combine(self.day.date().toPython(),self.quick_start.time().toPython());end=start+timedelta(hours=self.hours.value(),minutes=self.minutes.value());self.preview.setText('Ends at '+end.strftime('%I:%M %p · %d %b').lstrip('0')+'.')
        else:
            seconds=self.window.storage.seconds_for_day(self.kind.currentText().lower(),self.day.date().toString('yyyy-MM-dd'));self.preview.setText(f'Recorded: {seconds//3600} h {(seconds%3600)//60} min. Removes the latest time on this date, including imported totals. Stop the timer first if it is running.')
    def quick_save(self):
        self.hours.interpretText();self.minutes.interpretText()
        try:
            seconds=self.hours.value()*3600+self.minutes.value()*60
            if seconds<=0:raise ValueError('Enter an amount greater than zero.')
            kind=self.kind.currentText().lower();day=self.day.date().toString('yyyy-MM-dd')
            if self.mode.currentIndex()==1:self.window.storage.deduct_day(kind,day,seconds);message='Time deducted. Undo is available below.'
            else:
                start=datetime.combine(self.day.date().toPython(),self.quick_start.time().toPython());self.window.storage.correct_session(kind,start.isoformat(),(start+timedelta(seconds=seconds)).isoformat());message='Time added. All totals are updated.'
            self.changed(message)
        except ValueError as e:self.message.setText(str(e))
    def paintEvent(self,event):
        from panels import colors
        p=QPainter(self);p.fillRect(self.rect(),QColor(colors(self.window)[0]));p.end()
    def flush(self):pass
    def reload(self,*args):
        self.rows=self.window.storage.sessions_for_day(self.kind.currentText().lower(),self.day.date().toString('yyyy-MM-dd'))
        self.sessions.blockSignals(True);self.sessions.clear();self.sessions.addItem('Add missed time',None)
        for r in self.rows:self.sessions.addItem(r['started_at'].replace('T',' ')+' → '+(r['ended_at'].replace('T',' ') if r['ended_at'] else 'Running'),r['id'])
        self.sessions.blockSignals(False);self.select();self.update_quick()
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
            self.subtract.interpretText();end=datetime.fromisoformat(r['ended_at'])-timedelta(seconds=round(self.subtract.value()*3600))
            self.window.storage.correct_session(r['kind'],r['started_at'],end.isoformat(),r['id'],remove=end==datetime.fromisoformat(r['started_at']));self.changed('Time deducted. Undo is available below.')
        except ValueError as e:self.message.setText(str(e)+' To remove the whole session, use Remove selected session.')
    def remove_session(self):
        r=self.selected()
        if not r:return
        try:self.window.storage.correct_session(r['kind'],session_id=r['id'],remove=True);self.changed('Session removed. Undo is available below.')
        except ValueError as e:self.message.setText(str(e))
    def undo(self):
        try:self.window.storage.undo_time_edit();self.changed('Last correction undone.')
        except ValueError as e:self.message.setText(str(e))
