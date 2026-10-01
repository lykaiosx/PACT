"""PACT. The supplied SVG remains the layout source; live fields use its coordinates."""
from __future__ import annotations
import sys, os, json, time, threading, hashlib
from pathlib import Path
from datetime import date, datetime, timedelta
from PySide6.QtCore import Qt, QTimer, QRectF, Signal, QThread, QPoint, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QFontDatabase, QCursor, QIcon, QAction
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import (QApplication,QWidget,QScrollArea,QVBoxLayout,QPushButton,QDialog,QFormLayout,
 QDoubleSpinBox,QComboBox,QDialogButtonBox,QLabel,QLineEdit,QInputDialog,QSystemTrayIcon,QMenu,QMessageBox,QToolTip)
if '--self-test' in sys.argv:
 import tempfile,atexit
 _test_dir=tempfile.TemporaryDirectory(prefix='pact-check-')
 os.environ['PACT_DATA_DIR']=_test_dir.name
 os.environ['PACT_TOKEN_DIR']=str(Path(_test_dir.name)/'tokens')
 atexit.register(_test_dir.cleanup)
from storage import Storage,APP_DIR
from garmin_client import GarminBridge,TOKENSTORE,freshness_text,sync_state
BASE=Path(__file__).resolve().parent
ASSETS=BASE/'assets'
LIGHT='#FAFAFA'; DARK='#100404'
def hms(seconds):
 h,r=divmod(max(0,int(seconds)),3600);m,s=divmod(r,60);return f'{h:02}:{m:02}:{s:02}'
def palette(dark):return (DARK,LIGHT) if dark else (LIGHT,DARK)
def themed_svg(data,dark):
 if not dark:return data
 # Exchange semantic ink/paper roles, including the original black/white icons.
 import re
 mapping={'#fafafa':DARK,'#100404':LIGHT,'black':LIGHT,'white':DARK,'#4b4242':'#bfbcbc','#857f7f':'#857f7f'}
 return re.sub(r'(fill|stroke)="([^"]+)"',lambda m:f'{m[1]}="{mapping.get(m[2].lower(),m[2])}"',data)
class GarminJob(QThread):
 result=Signal(dict);failed=Signal(str);mfa=Signal()
 def __init__(self,bridge,email=None,password=None,backfill=False):
  super().__init__();self.bridge=bridge;self.email=email;self.password=password;self.backfill=backfill;self.answer='';self.event=threading.Event()
 def prompt(self):
  self.mfa.emit()
  if not self.event.wait(120) or not self.answer:raise RuntimeError('Verification cancelled')
  return self.answer
 def run(self):
  try:
   if self.email:self.bridge.login(self.email,self.password,self.prompt)
   elif self.bridge.client is None:self.bridge.resume()
   data=self.bridge.today();data['_history']=[]
   if self.backfill:
    for days in (1,2):
     try:data['_history'].append(self.bridge.for_day((date.today()-timedelta(days=days)).isoformat()))
     except Exception:pass
   self.result.emit(data)
  except Exception:
   # Do not expose authentication response bodies or credentials in logs/UI.
   self.failed.emit('Garmin could not sync. Check your connection or sign in again.')
  finally:self.password=None
from panels import Canvas,Settings,colors
class PACT(QWidget):
 def __init__(self,testing=False):
  super().__init__();self.testing=testing;self.storage=Storage();self.garmin=GarminBridge();self.job=None;self.sync_error=None;self.sync_busy=False;self.garmin_status='Not synced';self.corner_since=None;self.corner_latched=False
  self.dark=self.storage.get_setting('theme','light')=='dark';self.setWindowTitle('PACT');self.setWindowFlags(Qt.Window|Qt.FramelessWindowHint)
  self.floating_widget=None;self.settings_panel=None;self.panel_animation=None;self.display_hint=None;self.quitting=False;self.last_backfill=0;self.setWindowIcon(QIcon(str(ASSETS/'pact.ico')));self.canvas=Canvas(self)
  root=QVBoxLayout(self);root.setContentsMargins(0,0,0,0);self.scroll=QScrollArea();self.scroll.setFrameShape(QScrollArea.NoFrame);self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff);self.scroll.setWidget(self.canvas);root.addWidget(self.scroll)
  self.scroll.verticalScrollBar().valueChanged.connect(self.canvas.details.clear_details)
  self.apply_theme();self.refresh();self.fit_screen();self.timer=QTimer(self);self.timer.timeout.connect(self.refresh);self.timer.start(1000)
  self.hover=QTimer(self);self.hover.timeout.connect(self.check_corner);self.hover.start(75)
  self.sync_timer=QTimer(self);self.sync_timer.setInterval(300000);self.sync_timer.timeout.connect(self.auto_sync)
  self.tray=None
  self.garmin_status=freshness_text(self.storage.day_extra('garmin_checked_at'),self.storage.day_extra('garmin_data_through'))
  for screen in QApplication.screens():self.watch_screen(screen)
  QApplication.instance().screenAdded.connect(self.watch_screen);QApplication.instance().screenRemoved.connect(self.on_display_changed)
  if not testing:
   self.tray=QSystemTrayIcon(self.windowIcon(),self);self.tray.setToolTip('PACT');menu=QMenu(self)
   for title,fn in [('Show / hide',self.toggle_visible),('Settings',self.settings),('Show / hide widget',self.toggle_widget),('PACT Wrapped',self.open_weekly_review),('Sync Garmin',self.sync),('Quit PACT',self.quit)]:
    act=menu.addAction(title);act.triggered.connect(fn)
   self.tray.setContextMenu(menu);self.tray.activated.connect(lambda reason:self.toggle_visible() if reason==QSystemTrayIcon.Trigger else None);self.tray.show()
   if Path(TOKENSTORE).exists():QTimer.singleShot(1500,self.sync)
   self.sync_timer.start()
   self.weekly_timer=QTimer(self);self.weekly_timer.setInterval(3600000);self.weekly_timer.timeout.connect(self.check_weekly_review);self.weekly_timer.start();QTimer.singleShot(15000,self.check_weekly_review)
   self.tray.messageClicked.connect(self.open_review_notice)
  if not testing:self.update_widget()
 def set_widget_enabled(self,enabled):
  self.storage.set_setting('widget_enabled',bool(enabled));self.update_widget()
  if self.settings_panel and hasattr(self.settings_panel,'widget_enabled'):
   field=self.settings_panel.widget_enabled;field.blockSignals(True);field.setChecked(bool(enabled));field.blockSignals(False)
 def toggle_widget(self):self.set_widget_enabled(not self.storage.get_setting('widget_enabled',False))
 def update_widget(self):
  if self.storage.get_setting('widget_enabled',False):
   if self.floating_widget is None:
    from floating_widget import FloatingWidget
    self.floating_widget=FloatingWidget(self);self.destroyed.connect(self.floating_widget.deleteLater)
   self.floating_widget.refresh();self.floating_widget.show()
  elif self.floating_widget:self.floating_widget.hide()
 def open_review_notice(self):
  notice=getattr(self,'last_notice',None)
  if notice in ('weekly','monthly'):self.open_weekly_review('Weekly' if notice=='weekly' else 'Monthly',completed=True)
  else:self.settings()
 def check_weekly_review(self):
  if self.quitting or not self.tray:return
  month_end=date.today().replace(day=1)-timedelta(days=1);month=month_end.replace(day=1)
  if self.storage.get_setting('monthly_notifications',True) and self.storage.get_setting('monthly_notified')!=month.isoformat():
   from weekly_review import summary
   if summary(self.storage,month,end=month_end)['has_data']:
    self.last_notice='monthly';self.tray.showMessage('PACT · Your monthly Wrapped','Eight stories from your completed month are ready. Click to play.',QSystemTrayIcon.Information,10000);self.storage.set_setting('monthly_notified',month.isoformat());return
  if not self.storage.get_setting('weekly_notifications',True):return
  from weekly_review import last_week,summary
  week=last_week().isoformat()
  if self.storage.get_setting('weekly_notified')==week:return
  report=summary(self.storage)
  if not report['has_data']:return
  self.last_notice='weekly';self.tray.showMessage('PACT · Your weekly review','Your completed week is ready. Click to review your time, habits and highlights.',QSystemTrayIcon.Information,10000);self.storage.set_setting('weekly_notified',week)
 def open_weekly_review(self,mode=None,completed=False):
  from weekly_review import WeeklyReview
  if self.settings_panel:self.settings_panel.flush();self.settings_panel.hide();self.settings_panel.deleteLater();self.settings_panel=None
  if self.panel_animation:self.panel_animation.stop()
  if not self.isVisible():self.reveal()
  self.canvas.details.clear_details();self.settings_panel=WeeklyReview(self);self.settings_panel.setGeometry(self.rect());self.settings_panel.show();self.settings_panel.raise_()
  if mode=='Weekly':self.settings_panel.mode.setCurrentIndex(1)
  elif completed:
   from PySide6.QtCore import QDate
   self.settings_panel.date.setDate(QDate((date.today().replace(day=1)-timedelta(days=1)).replace(day=1)))
 def return_to_settings(self):
  if self.settings_panel:self.settings_panel.hide();self.settings_panel.deleteLater();self.settings_panel=None
  self.settings()
 def auto_sync(self):
  if self.garmin.client is not None or Path(TOKENSTORE).exists():self.sync()
 def apply_theme(self):
  self.dark=self.storage.get_setting('theme','light')=='dark';bg,fg=colors(self)
  QApplication.instance().setStyleSheet(f'QWidget{{background:{bg};color:{fg};font-family:Newsreader;font-size:16px;}} QPushButton,QLineEdit,QDoubleSpinBox,QSpinBox,QDateEdit,QDateTimeEdit,QTimeEdit,QComboBox{{border:1px solid {fg};padding:5px;border-radius:0;}} QTabWidget::pane{{border:1px solid {fg};}} QTabBar::tab{{background:{bg};color:{fg};border:1px solid {fg};padding:6px;}} QTabBar::tab:selected{{font-weight:bold;border-bottom:2px solid {fg};}} QScrollBar:vertical{{width:6px;background:{bg};}} QScrollBar::handle:vertical{{background:{fg};min-height:20px;}} QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}')
  self.canvas.retheme()
 def resizeEvent(self,e):
  super().resizeEvent(e);QTimer.singleShot(0,self.size_canvas)
 def size_canvas(self):
  w=self.scroll.viewport().width();self.canvas.setFixedSize(w,round(w*9314/self.canvas.geo['width']))
  if self.settings_panel:self.settings_panel.setGeometry(self.rect())
  if self.canvas.details.isVisible():self.canvas.details.present()
 def fit_screen(self,screen=None):
  screen=screen or QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen();g=screen.availableGeometry();h=g.height()
  if self.storage.get_setting('display_auto_adjust',False):
   # Qt supplies logical pixels: Windows DPI scaling is already accounted for.
   # Enlarge the complete design together rather than shrinking text to fit.
   default_width=min(520,g.width(),max(320,int(h*3000/9314)))
   largest=min(g.width(),max(560,round(default_width*1.6)));amount=max(0,min(100,int(self.storage.get_setting('display_width',100))))
   w=round(default_width+(largest-default_width)*amount/100)
   scrolling=Qt.ScrollBarAsNeeded
  else:w=min(520,g.width(),max(320,int(h*3000/9314)));scrolling=Qt.ScrollBarAsNeeded if h<994 else Qt.ScrollBarAlwaysOff
  self.scroll.setVerticalScrollBarPolicy(scrolling);self.setGeometry(g.right()-w+1,g.bottom()-h+1,w,h);self.size_canvas()
 def watch_screen(self,screen):
  screen.availableGeometryChanged.connect(self.on_display_changed);screen.logicalDotsPerInchChanged.connect(self.on_display_changed)
 def on_display_changed(self,*args):
  QTimer.singleShot(0,self.refit_current_screen)
 def refit_current_screen(self):
  self.fit_screen(QApplication.screenAt(self.geometry().center()) or QApplication.primaryScreen())
  if self.floating_widget:self.floating_widget.refresh()
  if hasattr(self,'timer') and self.storage.get_setting('widget_enabled',False)!=(self.floating_widget is not None and self.floating_widget.isVisible()):self.update_widget()
 def reveal(self):
  self.fit_screen();self.show();self.raise_();self.activateWindow()
  if not self.testing:QTimer.singleShot(350,self.show_display_hint)
 def show_display_hint(self):
  if self.quitting or not self.isVisible() or self.display_hint or self.storage.get_setting('display_hint_seen',False):return
  box=QMessageBox(self);box.setWindowTitle('PACT display options');box.setText('This is PACT’s default layout. For larger text and controls, turn on Auto-adjust for readability in the Appearance section of Settings. It adapts to your monitor and allows scrolling when needed. You can turn it off at any time.')
  settings_button=box.addButton('Open Settings',QMessageBox.ActionRole);done=box.addButton('Got it',QMessageBox.AcceptRole);box.setDefaultButton(done);box.setEscapeButton(done);self.display_hint=box
  def finished(*args):
   self.storage.set_setting('display_hint_seen',True);self.display_hint=None
   if not self.quitting and box.clickedButton()==settings_button:self.settings()
   box.deleteLater()
  box.finished.connect(finished);box.open()
 def toggle_visible(self):self.hide() if self.isVisible() else self.reveal()
 def check_corner(self):
  pos=QCursor.pos();screen=QApplication.screenAt(pos)
  if not screen:return
  g=screen.geometry();inside=g.right()-pos.x()<9 and pos.y()-g.top()<9
  if not inside:self.corner_since=None;self.corner_latched=False;return
  if self.corner_latched:return
  if self.corner_since is None:self.corner_since=time.monotonic()
  if time.monotonic()-self.corner_since>=.35:
   self.corner_latched=True
   if not self.isVisible():self.reveal()
 def keyPressEvent(self,e):
  if e.key()==Qt.Key_Escape:self.close_settings() if self.settings_panel else self.hide()
  elif e.key()==Qt.Key_Comma and e.modifiers()&Qt.ControlModifier:self.settings()
  else:super().keyPressEvent(e)
 def closeEvent(self,e):e.ignore();self.hide()
 def settings(self):
  if not self.isVisible():self.reveal()
  if self.settings_panel:return
  self.canvas.details.clear_details()
  self.settings_panel=Settings(self);self.settings_panel.setGeometry(self.width(),0,self.width(),self.height());self.settings_panel.show()
  self.settings_panel.raise_();self.panel_animation=QPropertyAnimation(self.settings_panel,b'pos',self);self.panel_animation.setDuration(320);self.panel_animation.setStartValue(QPoint(self.width(),0));self.panel_animation.setEndValue(QPoint(0,0));self.panel_animation.setEasingCurve(QEasingCurve.InOutCubic);self.panel_animation.start()
 def close_settings(self):
  if not self.settings_panel:return
  self.settings_panel.flush()
  panel=self.settings_panel;self.settings_panel=None
  self.panel_animation=QPropertyAnimation(panel,b'pos',self);self.panel_animation.setDuration(240);self.panel_animation.setStartValue(panel.pos());self.panel_animation.setEndValue(QPoint(self.width(),0));self.panel_animation.finished.connect(panel.deleteLater);self.panel_animation.start()
 def edit_time(self,kind):
  if self.settings_panel:return
  from time_editor import TimeEditor
  self.canvas.details.clear_details();self.settings_panel=TimeEditor(self,kind);self.settings_panel.setGeometry(self.rect());self.settings_panel.show();self.settings_panel.raise_()
 def toggle_timer(self,kind):
  (self.storage.stop_session if self.storage.active_session(kind) else self.storage.start_session)(kind);self.history_at=0;self.refresh()
 def refresh(self):
  self.day=self.storage.get_day();self.sleep=self.storage.latest_sleep();self.seconds={k:self.storage.seconds_for_day(k) for k in ('work','learning')}
  self.sync_attention,self.garmin_status=sync_state(self.storage.get_setting('last_sync'),self.storage.get_setting('last_data_through',self.storage.day_extra('garmin_data_through')),error=self.sync_error,busy=self.sync_busy)
  self.canvas.sync_indicator.set_attention(self.sync_attention)
  # Queries for history are bounded and need not run on every timer tick.
  if not hasattr(self,'history') or time.monotonic()-getattr(self,'history_at',0)>30:
   self.histories={k:self.storage.history(k,366) for k in ('work','learning')};self.history=self.histories['work'];self.annual={k:sum(v for d,v in hist if d.year==date.today().year) for k,hist in self.histories.items()};self.history_at=time.monotonic()
  for i,k in enumerate(('work','learning')):self.canvas.controls[i][0].setText('Stop' if self.storage.active_session(k) else 'Start')
  self.canvas.update()
  if self.floating_widget:self.floating_widget.refresh()
  if not self.quitting and hasattr(self,'timer') and self.storage.get_setting('widget_enabled',False)!=(self.floating_widget is not None and self.floating_widget.isVisible()):self.update_widget()
  if self.settings_panel and hasattr(self.settings_panel,'state'):self.settings_panel.state.setText(self.garmin_status)
 def connect_garmin(self):self.settings()
 def sync(self,email=None,password=None):
  if self.testing or (self.job and self.job.isRunning()):return
  self.sync_busy=True;self.garmin_status='Checking Garmin cloud…';backfill=time.monotonic()-self.last_backfill>3600;self.job=GarminJob(self.garmin,email if isinstance(email,str) else None,password,backfill);self.job.result.connect(self.synced);self.job.failed.connect(self.sync_failed);self.job.mfa.connect(self.ask_mfa);self.job.start();self.refresh()
 def ask_mfa(self):
  if self.settings_panel and not isinstance(self.settings_panel,Settings):self.close_settings()
  self.settings();self.settings_panel.code.show();self.settings_panel.verify.show();self.settings_panel.code.setFocus()
 def synced(self,data):
  self.sync_busy=False;self.sync_error='Hydration could not be refreshed. Select Sync now.' if data.get('_hydration_error') else None
  checked=datetime.now().isoformat(timespec='seconds')
  for record in [data]+data.get('_history',[]):
   day=record.get('_day',date.today().isoformat())
   cutoff=self.storage.get_setting('progress_reset_at')
   if cutoff and day<cutoff[:10]:continue
   for k in ('sleep_minutes','steps','resting_hr','sleep_score','sleep_stages','body_battery','calories','hydration_ml','hydration_goal_ml'):
    v=record.get(k)
    if v is None:continue
    if k in ('sleep_minutes','steps','resting_hr'):self.storage.set_day_field(k,v,day)
    else:self.storage.set_day_extra(k,v,day)
   self.storage.set_day_extra('garmin_data_through',record.get('_data_through'),day);self.storage.set_day_extra('garmin_checked_at',checked,day);self.storage.record_health(record,day,checked)
  if data.get('_history'):self.last_backfill=time.monotonic()
  self.garmin_status=freshness_text(checked,data.get('_data_through'))
  if data.get('_hydration_error'):self.garmin_status+='\nHydration could not be refreshed. Retry Sync now.'
  self.storage.set_setting('last_sync',checked);self.storage.set_setting('last_data_through',data.get('_data_through'));self.history_at=0;self.refresh()
 def sync_failed(self,message):
  self.sync_busy=False;self.sync_error=message
  self.garmin.client=None
  self.garmin_status=message
  self.refresh()
  if self.tray:self.last_notice='garmin';self.tray.showMessage('PACT · Garmin',message,QSystemTrayIcon.Information,5000)
 def quit(self):
  self.quitting=True
  if self.floating_widget:self.floating_widget.hide()
  if self.display_hint:self.display_hint.reject()
  if self.settings_panel:self.settings_panel.flush()
  self.sync_timer.stop()
  if self.job and self.job.isRunning():
   self.job.event.set();self.hide();QTimer.singleShot(250,self.quit);return
  self.storage.conn.close();QApplication.quit()
 def hideEvent(self,event):
  self.canvas.details.clear_details()
  if self.settings_panel:self.settings_panel.flush()
  super().hideEvent(event)
def server_name():return 'PACT-'+hashlib.sha256(str(APP_DIR).lower().encode()).hexdigest()[:16]
def main():
 app=QApplication(sys.argv);app.setApplicationName('PACT');app.setQuitOnLastWindowClosed(False)
 QFontDatabase.addApplicationFont(str(ASSETS/'fonts'/'Newsreader.ttf'));app.setFont(QFont('Newsreader'))
 sock=QLocalSocket();sock.connectToServer(server_name())
 if sock.waitForConnected(400):
  sock.write(b'quit' if '--shutdown' in sys.argv else b'show');sock.waitForBytesWritten(1000);sock.disconnectFromServer();return 0
 if '--shutdown' in sys.argv:return 0
 server=QLocalServer();QLocalServer.removeServer(server_name())
 if not server.listen(server_name()):return 1
 win=PACT(testing='--self-test' in sys.argv)
 def incoming():
  client=server.nextPendingConnection()
  def read():
   command=bytes(client.readAll());client.disconnectFromServer();win.quit() if command==b'quit' else win.reveal()
  if client.bytesAvailable():read()
  else:client.readyRead.connect(read)
 server.newConnection.connect(incoming)
 if '--self-test' in sys.argv:
  win.reveal();QTimer.singleShot(300,win.quit)
 elif '--hidden' not in sys.argv:win.reveal()
 return app.exec()
if __name__=='__main__':
 try:sys.exit(main())
 except Exception:
  import traceback
  APP_DIR.mkdir(parents=True,exist_ok=True)
  (APP_DIR/'pact-crash.log').write_text(traceback.format_exc())
  sys.exit(1)

