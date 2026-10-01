"""Optional, independent PACT desktop summary using the existing local data."""
from datetime import date
from PySide6.QtCore import Qt,QPoint,QRectF
from PySide6.QtGui import QColor,QPainter,QPen,QFont,QCursor
from PySide6.QtWidgets import QWidget,QApplication,QMenu

STATS=('work','learning','sleep','steps','meals','creatives')
DEFAULT_STATS=list(STATS[:4])

def snapshot(window):
    s=window.storage;today=date.today().isoformat();day=s.existing_day(today);sleep=s.latest_sleep();rows=[]
    selected=s.get_setting('widget_stats',DEFAULT_STATS)
    for kind in STATS:
        if kind not in selected:continue
        if kind in ('work','learning'):
            seconds=window.seconds[kind];hours,rest=divmod(int(seconds),3600);minutes,seconds=divmod(rest,60)
            rows.append((kind.title(),f'{hours:02}:{minutes:02}:{seconds:02}',f'{s.target(kind):g}h goal'+(' · Running' if s.active_session(kind) else ''),window.seconds[kind]/(s.target(kind)*3600)))
        elif kind=='sleep':
            score=sleep.get('sleep_score');minutes=sleep.get('sleep_minutes');label='Sleep'
            if sleep.get('day') and sleep['day']!=today:label+=' · '+date.fromisoformat(sleep['day']).strftime('%d %b')
            detail='Not available' if minutes is None else f'{minutes//60}h {minutes%60:02}m slept'
            rows.append((label,'—' if score is None else str(score),detail+(' · score' if score is not None else ''),None))
        elif kind=='steps':rows.append(('Steps','—' if day.get('steps') is None else f'{day["steps"]:,}','Today',None))
        elif kind=='meals':
            values=[s.manual_value(k,today) for k in ('breakfast','lunch','dinner')];known=sum(v is not None for v in values)
            rows.append(('Meals','—' if not known else f'{sum(v or 0 for v in values)} eaten',f'{3-known} unrecorded' if known<3 else 'All three entered',None))
        else:
            value=s.manual_value('creatives',today);rows.append(('Creatives','—' if value is None else str(value),'Today',None))
    return rows

class FloatingWidget(QWidget):
    def __init__(self,window):
        super().__init__(None,Qt.Tool|Qt.FramelessWindowHint)
        self.window=window;self.drag_origin=None;self.dragged=False;self.rows=[];self.scale=1
        self.setWindowTitle('PACT Widget');self.setWindowIcon(window.windowIcon());self.setAttribute(Qt.WA_ShowWithoutActivating);self.setFocusPolicy(Qt.StrongFocus)
        self.setAccessibleName('PACT desktop stats. Enter opens PACT. Right-click for widget options.')
        self.refresh(restore_position=True)
    def refresh(self,restore_position=False):
        self.rows=snapshot(self.window);s=self.window.storage
        if self.drag_origin is not None:self.update();return
        point=QPoint(*s.get_setting('widget_position',[self.x(),self.y()])) if restore_position else self.pos()
        screen=QApplication.screenAt(point) or QApplication.primaryScreen();bounds=screen.availableGeometry();base_height=92+len(self.rows)*62
        self.scale=min(s.get_setting('widget_scale',100)/100,bounds.width()/320,bounds.height()/base_height)
        self.resize(round(320*self.scale),round(base_height*self.scale));self.setWindowOpacity(s.get_setting('widget_opacity',100)/100)
        if restore_position and s.get_setting('widget_position') is None:point=bounds.topLeft()+QPoint(24,24)
        self.move(max(bounds.left(),min(point.x(),bounds.right()-self.width()+1)),max(bounds.top(),min(point.y(),bounds.bottom()-self.height()+1)))
        self.update()
    def paintEvent(self,event):
        from panels import colors
        bg,ink=colors(self.window);p=QPainter(self);p.setRenderHint(QPainter.Antialiasing);p.fillRect(self.rect(),QColor(bg));p.scale(self.scale,self.scale);height=self.height()/self.scale;p.setPen(QPen(QColor(ink),1));p.drawRect(QRectF(.5,.5,319,height-1))
        def text(x,y,w,h,value,size=16,bold=False,align=Qt.AlignLeft):
            font=QFont('Newsreader');font.setPixelSize(size);font.setBold(bold);p.setFont(font);p.setPen(QColor(ink));p.drawText(QRectF(x,y,w,h),align|Qt.AlignVCenter,value)
        text(16,10,150,30,'Pact',27,True);text(180,14,124,24,'Locked' if self.window.storage.get_setting('widget_locked',False) else 'Drag to move',12,align=Qt.AlignRight)
        p.drawLine(16,48,304,48)
        for i,(label,value,detail,ratio) in enumerate(self.rows):
            y=58+i*62;text(16,y,163,24,label,18);text(179,y,125,24,value,19,True,Qt.AlignRight);text(16,y+24,288,17,detail,12)
            if ratio is not None:
                p.setPen(QPen(QColor(ink),1));p.drawRect(QRectF(16,y+45,288,6));p.fillRect(QRectF(17,y+46,286*max(0,min(1,ratio)),4),QColor(ink))
        text(16,height-27,288,19,'Open PACT  ›',13,align=Qt.AlignCenter);p.end()
    def mousePressEvent(self,event):
        if event.button()==Qt.LeftButton:
            self.dragged=False
            if event.position().y()<50*self.scale and not self.window.storage.get_setting('widget_locked',False):self.drag_origin=event.globalPosition().toPoint()-self.pos()
    def mouseMoveEvent(self,event):
        if self.drag_origin is not None and event.buttons()&Qt.LeftButton:
            point=event.globalPosition().toPoint()-self.drag_origin
            if (point-self.pos()).manhattanLength()>2:self.dragged=True
            self.move(point)
    def mouseReleaseEvent(self,event):
        if event.button()!=Qt.LeftButton:return
        dragged=self.dragged;self.drag_origin=None
        if dragged:
            self.refresh();self.window.storage.set_setting('widget_position',[self.x(),self.y()])
        else:self.window.reveal()
    def keyPressEvent(self,event):
        if event.key() in (Qt.Key_Return,Qt.Key_Enter):self.window.reveal()
        else:super().keyPressEvent(event)
    def contextMenuEvent(self,event):
        menu=QMenu(self);menu.addAction('Open PACT',self.window.reveal);menu.addAction('Widget settings',self.window.return_to_settings)
        locked=menu.addAction('Lock position');locked.setCheckable(True);locked.setChecked(self.window.storage.get_setting('widget_locked',False));locked.toggled.connect(self.set_locked)
        menu.addAction('Hide widget',lambda:self.window.set_widget_enabled(False));menu.exec(event.globalPos())
    def set_locked(self,value):
        self.window.storage.set_setting('widget_locked',bool(value));self.update()
        panel=self.window.settings_panel
        if panel and hasattr(panel,'widget_locked'):
            panel.widget_locked.blockSignals(True);panel.widget_locked.setChecked(bool(value));panel.widget_locked.blockSignals(False)
    def closeEvent(self,event):
        event.ignore();self.window.set_widget_enabled(False)
