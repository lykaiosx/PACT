"""One highlight per animated, theme-native PACT story slide."""
import calendar,math,os,tempfile,zipfile
from pathlib import Path
from datetime import date,timedelta
from PySide6.QtCore import Qt,QDate,QRectF,QPointF,QTimer,QVariantAnimation,QEasingCurve
from PySide6.QtGui import QPainter,QColor,QPen,QFont,QFontMetricsF,QImage,QPdfWriter,QPageSize,QPainterPath
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QComboBox,QDateEdit,QLabel,QGridLayout,QFileDialog

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
      dict(tag='ROOM TO GROW',title='You kept\nyour curiosity.',metric=compact(learning['total']) if learning['recorded'] else '—',unit='of recorded learning',graphic='book',values=learning['values'],note=f'{learning["recorded"]} of {n} days recorded',detail='One page, one session, one thing learned.' if learning['total'] else 'Your next learning session starts the story.'),
      dict(tag='SHOWING UP',title='Consistency\nhas a rhythm.',metric=str(work['streak']) if work['recorded'] else '—',unit='days in your longest work-goal streak',graphic='grid',values=[int(k and v>=s.target('work')*3600) for k,v in zip(work['known'],work['values'])],note=f'{work["goal_days"]} work-goal days in total',detail=f'Filled squares met your current {s.target("work"):g}h work target. Missing days do not extend a streak.'),
      dict(tag='THINGS YOU CREATED',title='Ideas became\nsomething real.',metric=str(r['creatives']) if r['creative_days'] else '—',unit='creatives recorded',graphic='tiles',values=r['creative_values'],note=f'{r["creative_days"]} of {n} days with entries',detail='An idea, a mark, something made.'),
      dict(tag='THE EVERYDAY BASICS',title='You made room\nfor yourself.',metric=str(r['meals']) if r['meal_entries'] else '—',unit='meals marked as eaten',graphic='meals',values=r['meal_types'],note=f'{r["complete_meal_days"]} days with all three meals eaten',detail=f'{r["meals"]} eaten · {r["meal_skipped"]} marked as skipped\n{r["meal_unknown"]} unrecorded. Unrecorded does not mean skipped.'),
      dict(tag='TIME TO RECHARGE',title='Rest was part\nof the picture.',metric=compact(r['sleep_average']*60) if r['sleep_average'] is not None else '—',unit='average recorded sleep',graphic='moon',values=r['sleep_values'],note=f'{r["sleep_nights"]} recorded nights',detail='From Garmin sleep records. Here’s to your next chapter.' if r['sleep_nights'] else 'No sleep records for this period yet.')]
    for slide,value in zip(slides,[r['covered_days'],work['total'],best[1] if best else 0,learning['total'],work['streak'],r['creatives'],r['meals'],(r['sleep_average'] or 0)*60]):
        slide['number']=value;slide['duration']=slide['graphic'] in ('bars','peak','book','moon')
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
        self.draw(p,self.owner.slides[self.owner.index],self.owner.content_progress,bg,ink);p.restore();p.end()
    def draw(self,p,s,t,bg,ink):
        fg=QColor(ink);paper=QColor(bg)
        def text(y,h,value,size=18,bold=False,italic=False,fit=True,reference=None):
            font=QFont('Newsreader');font.setPixelSize(size);font.setBold(bold);font.setItalic(italic)
            while fit and size>10 and max(QFontMetricsF(font).horizontalAdvance(line) for line in (reference or value).split('\n'))>320:size-=1;font.setPixelSize(size)
            p.setFont(font);p.setPen(fg);p.drawText(QRectF(20,y,320,h),Qt.AlignHCenter|Qt.AlignVCenter|Qt.TextWordWrap,value)
        p.setPen(QPen(fg,1));p.drawLine(QPointF(20,36),QPointF(340,36));text(9,20,s['tag'],11)
        reference=(str(round(s['number']/60)//60)+'h 59m') if s['duration'] and s['metric']!='—' else s['metric']
        text(52,92,s['title'],39,False,True);text(149,89,animated_metric(s,t),78,True,reference=reference);text(242,36,s['unit'],17)
        p.save();p.setClipRect(QRectF(20,292,320,190));p.setPen(QPen(fg,1.2));p.setBrush(fg);kind=s['graphic'];values=s['values'];grow=t
        if kind=='orbit':
            p.setBrush(Qt.NoBrush)
            for i in range(5):
                w=170-i*28;p.drawEllipse(QRectF(180-w/2,385-w/2,w,w))
            angle=-math.pi/2+(t-1)*math.pi*4;p.setBrush(fg);p.drawEllipse(QPointF(180+72*math.cos(angle),385+72*math.sin(angle)),11,11)
        elif kind=='bars':
            vals=[v or 0 for v in values];maximum=max(vals,default=0) or 1;slot=300/max(1,len(vals));bar=max(2,slot*.65)
            p.drawLine(QPointF(30,460),QPointF(330,460))
            for i,v in enumerate(vals):
                height=140*v/maximum*grow
                if height<1.5:continue
                if v:p.fillRect(QRectF(30+i*slot,460-height,bar,height),fg)
        elif kind=='book':
            # A stationary book fills with writing: no turning sheet or final swap.
            def book_page(side,reveal):
                p.setBrush(paper)
                edge=180+side*107
                page=QPainterPath(QPointF(180,334));page.cubicTo(180+side*30,312,edge-side*25,320,edge,331)
                page.lineTo(edge,439);page.cubicTo(edge-side*25,428,180+side*30,425,180,447);page.closeSubpath();p.drawPath(page)
                for row in range(4):
                    index=row+(4 if side==1 else 0);amount=max(0,min(1,reveal*8-index));y=354+row*18
                    line=QPainterPath(QPointF(180+side*18,y))
                    for step in range(1,33):
                        u=amount*step/32;line.lineTo(180+side*(18+56*u+9*u*u),y-20*u+17*u*u)
                    if amount:p.setBrush(Qt.NoBrush);p.drawPath(line)
            for side in (-1,1):book_page(side,grow)
            p.drawLine(QPointF(180,334),QPointF(180,447))
        elif kind=='peak':
            if any(values):
                for i in range(18):
                    a=2*math.pi*i/18;inner=40+12*grow;outer=40+50*grow;p.drawLine(QPointF(180+inner*math.cos(a),385+inner*math.sin(a)),QPointF(180+outer*math.cos(a),385+outer*math.sin(a)))
                p.drawEllipse(QRectF(140,345,80,80))
            else:p.setBrush(Qt.NoBrush);p.drawEllipse(QRectF(140,345,80,80))
        elif kind=='tiles':
            # A full-size drawing motif stays balanced even with a single creative.
            p.setBrush(Qt.NoBrush);p.drawRect(QRectF(116,305,128,152))
            p.drawLine(QPointF(130,322),QPointF(210,322))
            path=QPainterPath(QPointF(136,412))
            for j in range(1,101):
                f=j/100
                if f>grow:break
                path.lineTo(136+86*f,390+22*math.cos(f*math.pi*3))
            p.setPen(QPen(fg,2));p.drawPath(path)
            x=136+86*grow;y=390+22*math.cos(grow*math.pi*3)
            p.save();p.translate(x,y);p.rotate(30);p.setBrush(paper)
            nib=QPainterPath(QPointF(0,0));nib.lineTo(-7,-17);nib.lineTo(-4,-54);nib.lineTo(4,-54);nib.lineTo(7,-17);nib.closeSubpath();p.drawPath(nib);p.restore()
        elif kind=='grid':
            for i,(value,rect) in enumerate(zip(values,consistency_cells(len(values)))):
                p.setOpacity(1 if t>=1 else .65+.35*math.cos((self.owner.content_elapsed*2+i*.07)*math.pi));p.setBrush(fg if value else Qt.NoBrush);p.drawRect(rect)
        elif kind=='meals':
            # Plate and cutlery: a meal symbol, not a pie chart of unknown days.
            p.setBrush(Qt.NoBrush)
            for radius in (64,48):p.drawEllipse(QPointF(180,378),radius,radius)
            p.drawArc(QRectF(121,319,118,118),90*16,-round(360*16*grow))
            reach=65*grow
            p.drawLine(QPointF(95,420),QPointF(95,420-reach))
            for x in (87,95,103):p.drawLine(QPointF(x,332),QPointF(x,356))
            p.drawArc(QRectF(87,348,16,16),180*16,180*16)
            p.drawLine(QPointF(265,420),QPointF(265,420-reach));p.drawEllipse(QRectF(256,327,18,31))
            font=QFont('Newsreader');font.setPixelSize(12);p.setFont(font)
            for i,value in enumerate(values):p.drawText(QRectF(20+105*i,451,110,24),Qt.AlignCenter,f'{("Breakfast","Lunch","Dinner")[i]} {value}')
        elif kind=='moon':
            if any(v is not None for v in values):
                p.save();p.translate(180,385);p.rotate(-12*(1-grow));p.scale(.85+.15*grow,.85+.15*grow);p.translate(-180,-385);p.setPen(Qt.NoPen);p.setBrush(fg);p.drawEllipse(QRectF(101,310,156,156));p.setBrush(paper);p.drawEllipse(QRectF(138+10*grow,292,143,143));p.setBrush(fg)
                p.restore();p.setPen(Qt.NoPen);p.setBrush(fg)
                for i,(x,y,r) in enumerate([(88,331,3),(264,419,4),(285,333,2),(75,418,1.5),(270,370,1.5)]):
                    p.setOpacity(1 if t>=1 else max(0,t)*(.55+.45*math.sin(self.owner.content_elapsed*math.pi+i)));p.drawEllipse(QPointF(x,y),r,r)
            else:p.setBrush(Qt.NoBrush);p.drawEllipse(QRectF(101,310,156,156))
        p.restore();text(490,36,s['note'],18,True);text(532,56,s['detail'],14,fit=False)
    def keyPressEvent(self,event):self.owner.keyPressEvent(event)

class WrappedReview(QWidget):
    def __init__(self,window):
        super().__init__(window);self.window=window;self.index=0;self.previous=None;self.progress=1.;self.content_progress=0.;self.content_elapsed=0.;self.direction=1;self.slides=[];root=QVBoxLayout(self);root.setContentsMargins(12,14,12,22);root.setSpacing(8)
        header=QGridLayout();header.setColumnStretch(1,1);header.setHorizontalSpacing(8);header.setVerticalSpacing(8)
        back=QPushButton('‹');back.setAccessibleName('Back to Settings');back.clicked.connect(window.return_to_settings)
        self.mode=QComboBox();self.mode.addItems(['Monthly','Weekly'])
        self.play=QPushButton('Play');self.play.setCheckable(True);self.play.toggled.connect(self.toggle_play)
        prev=QPushButton('‹');prev.setAccessibleName('Previous period');prev.clicked.connect(lambda:self.move_period(-1))
        self.date=QDateEdit(QDate.currentDate());self.date.setCalendarPopup(True);self.date.setMinimumDate(QDate(2000,1,3));self.date.setMaximumDate(QDate.currentDate());self.date.setDisplayFormat('MMM yyyy')
        self.next_period=QPushButton('›');self.next_period.setAccessibleName('Next period');self.next_period.clicked.connect(lambda:self.move_period(1))
        self.header_controls=[back,self.mode,self.play,prev,self.date,self.next_period]
        for i,control in enumerate(self.header_controls):
            control.setFixedHeight(max(34,self.fontMetrics().height()+14));header.addWidget(control,i//3,i%3)
        root.addLayout(header)
        export_row=QHBoxLayout();self.export_format=QComboBox();self.export_format.addItems(['One PDF report','PNG slides (ZIP)']);self.export_format.setAccessibleName('Report export format');export_row.addWidget(self.export_format,1)
        self.export_button=QPushButton('Export');self.export_button.clicked.connect(self.choose_export);export_row.addWidget(self.export_button);root.addLayout(export_row)
        for control in (self.export_format,self.export_button):control.setFixedHeight(self.mode.height())
        self.period_note=QLabel();self.period_note.setAlignment(Qt.AlignCenter);root.addWidget(self.period_note)
        self.canvas=StoryCanvas(self);root.addWidget(self.canvas,1);dots=QHBoxLayout();dots.setSpacing(4);self.dots=[]
        for i in range(8):
            b=QPushButton();b.setFixedHeight(9);b.setAccessibleName(f'Go to slide {i+1}');b.clicked.connect(lambda _,n=i:self.go(n));dots.addWidget(b);self.dots.append(b)
        root.addLayout(dots);bottom=QHBoxLayout();self.back_slide=QPushButton('Previous');self.back_slide.clicked.connect(lambda:self.go(self.index-1));bottom.addWidget(self.back_slide);self.counter=QLabel();self.counter.setAlignment(Qt.AlignCenter);bottom.addWidget(self.counter,1);self.next_slide=QPushButton('Next');self.next_slide.clicked.connect(lambda:self.go(self.index+1));bottom.addWidget(self.next_slide);root.addLayout(bottom)
        self.animation=QVariantAnimation(self);self.animation.setDuration(650);self.animation.setStartValue(0.);self.animation.setEndValue(1.);self.animation.setEasingCurve(QEasingCurve.InOutCubic);self.animation.valueChanged.connect(self.animate);self.content_animation=QVariantAnimation(self);self.content_animation.setDuration(3400);self.content_animation.setStartValue(0.);self.content_animation.setEndValue(1.);self.content_animation.setEasingCurve(QEasingCurve.OutCubic);self.content_animation.valueChanged.connect(self.animate_content);self.animation.finished.connect(self.content_animation.start);self.timer=QTimer(self);self.timer.setInterval(5500);self.timer.timeout.connect(self.advance);self.mode.currentIndexChanged.connect(self.change_mode);self.date.dateChanged.connect(self.reload);self.reload()
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
        self.animation.stop();self.content_animation.stop();self.content_progress=0.;self.content_elapsed=0.;self.play.setChecked(False);self.slides,self.period,self.report=make_slides(self.window.storage,self.mode.currentText(),self.date.date().toPython());self.index=0;self.previous=None;self.progress=0.
        self.period_note.setText(self.period);self.date.blockSignals(True);self.date.setDate(QDate(self.report['start']));self.date.blockSignals(False);self.next_period.setEnabled(self.report['start']<(date.today().replace(day=1) if self.mode.currentIndex()==0 else last_week()));self.controls();self.animation.start()
    def controls(self):
        from panels import colors
        bg,ink=colors(self.window);self.counter.setText(f'{self.index+1} / 8');self.back_slide.setEnabled(self.index>0);self.next_slide.setEnabled(self.index<7)
        for i,b in enumerate(self.dots):b.setStyleSheet(f'padding:0;border:1px solid {ink};background:{ink if i<=self.index else bg};')
        self.canvas.setAccessibleName(self.slides[self.index]['title'].replace('\n',' ')+' '+self.slides[self.index]['metric']+' '+self.slides[self.index]['unit'])
    def animate(self,value):self.progress=float(value);self.canvas.update()
    def animate_content(self,value):
        self.content_progress=float(value);self.content_elapsed=self.content_animation.currentTime()/1000;self.canvas.update()
    def go(self,index):
        if not 0<=index<8 or index==self.index:return
        self.animation.stop();self.content_animation.stop();self.content_progress=0.;self.content_elapsed=0.;self.previous=self.index;self.direction=1 if index>self.index else -1;self.index=index;self.progress=0.;self.controls();self.animation.start()
    def keyPressEvent(self,event):
        if event.key()==Qt.Key_Right:self.go(self.index+1)
        elif event.key()==Qt.Key_Left:self.go(self.index-1)
        elif event.key()==Qt.Key_Space:self.play.toggle()
        else:super().keyPressEvent(event)
    def hideEvent(self,event):
        self.play.setChecked(False);self.animation.stop();self.content_animation.stop();self.content_progress=1.;self.progress=1.;self.previous=None;self.canvas.update();super().hideEvent(event)

    def export_report(self,filename):
        """Render the selected report at rest, without touching its data or playback."""
        from panels import colors
        target=Path(filename);bg,ink=colors(self.window)
        if target.suffix.lower() not in ('.pdf','.zip'):raise ValueError('Choose PDF or ZIP.')
        handle,temp=tempfile.mkstemp(prefix='.pact-report-',suffix=target.suffix,dir=target.parent);os.close(handle)
        def page(p,width,height,slide,index):
            p.fillRect(QRectF(0,0,width,height),QColor(bg));p.save();scale=min(width/360,height/650);p.translate((width-360*scale)/2,(height-650*scale)/2);p.scale(scale,scale)
            p.setPen(QColor(ink));font=QFont('Newsreader');font.setPixelSize(11);p.setFont(font);p.drawText(QRectF(20,0,320,24),Qt.AlignCenter,'PACT · '+self.period)
            p.translate(0,25);self.canvas.draw(p,slide,1,bg,ink);p.translate(0,-25)
            p.setFont(font);p.drawText(QRectF(20,625,320,20),Qt.AlignCenter,f'{index+1} / 8 · '+('Includes edited/imported entries' if self.report['edited_days'] else 'Recorded entries'));p.restore()
        try:
            if target.suffix.lower()=='.pdf':
                writer=QPdfWriter(temp);writer.setPageSize(QPageSize(QPageSize.A4));writer.setTitle('PACT Wrapped · '+self.period);writer.setCreator('PACT');painter=QPainter(writer)
                if not painter.isActive():raise OSError('Could not create the report.')
                try:
                    for i,slide in enumerate(self.slides):
                        if i and not writer.newPage():raise OSError('Could not write a report page.')
                        page(painter,writer.width(),writer.height(),slide,i)
                finally:painter.end()
                del writer
            else:
                from PySide6.QtCore import QBuffer,QIODevice
                with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as archive:
                    for i,slide in enumerate(self.slides):
                        image=QImage(1080,1950,QImage.Format_ARGB32);painter=QPainter(image);painter.setRenderHint(QPainter.Antialiasing);page(painter,1080,1950,slide,i);painter.end();buffer=QBuffer();buffer.open(QIODevice.WriteOnly)
                        if not image.save(buffer,'PNG'):raise OSError('Could not create a slide image.')
                        title=('Overview','Work','Busiest work day','Learning','Consistency','Creatives','Meals','Sleep')[i]
                        archive.writestr(f'PACT-Wrapped-{self.report["start"]}/Slide {i+1:02} - {title}.png',bytes(buffer.data()))
            os.replace(temp,target)
        finally:
            if os.path.exists(temp):os.unlink(temp)
    def choose_export(self):
        images=self.export_format.currentIndex()==1;extension='.zip' if images else '.pdf'
        filename,chosen=QFileDialog.getSaveFileName(self,'Export PNG slides' if images else 'Export PDF report',f'PACT-Wrapped-{self.report["start"]}{extension}','PNG slides (*.zip)' if images else 'PDF report (*.pdf)')
        if not filename:return
        if Path(filename).suffix.lower()!=extension:filename+=extension
        try:self.export_report(filename);self.period_note.setText('Report exported · '+self.period)
        except Exception:self.period_note.setText('Could not export. Choose a writable location and try again.')

def animated_metric(slide,progress):
    if slide['metric']=='—' or progress>=1:return slide['metric']
    number=slide['number']*max(0,progress)
    return compact(number) if slide['duration'] else str(int(number))

def consistency_cells(count):
    """Balanced rows without introducing boxes for dates outside the report."""
    if not count:return []
    columns=count if count<=7 else 7 if count==28 else 8 if count==31 else 6
    rows=math.ceil(count/columns);gap=7;size=min(32,(150-gap*(rows-1))/rows)
    top=385-(rows*(size+gap)-gap)/2;cells=[]
    for row in range(rows):
        length=min(columns,count-row*columns);left=180-(length*(size+gap)-gap)/2
        cells.extend(QRectF(left+col*(size+gap),top+row*(size+gap),size,size) for col in range(length))
    return cells
