import os,sys,tempfile,unittest,csv,io,zipfile,json
from pathlib import Path
from datetime import datetime,date,timedelta
temp=tempfile.TemporaryDirectory();os.environ['PACT_DATA_DIR']=temp.name;os.environ['PACT_TOKEN_DIR']=temp.name+'/tokens';os.environ['QT_QPA_PLATFORM']='offscreen'
sys.path.insert(0,str(Path('app').resolve()))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase,QColor
from PySide6.QtCore import QPointF,QAbstractAnimation
from PySide6.QtCore import QEventLoop,QTimer
class QTest:
 @staticmethod
 def qWait(ms):
  loop=QEventLoop();QTimer.singleShot(ms,loop.quit);loop.exec()
from app import PACT,ASSETS
from panels import colors,SOFT_DARK,DARK
from garmin_client import freshness_text,GarminBridge
from data_export import capture,export_data
app=QApplication([]);QFontDatabase.addApplicationFont(str(ASSETS/'fonts/Newsreader.ttf'))
class Polish(unittest.TestCase):
 def setUp(self):
  self.w=PACT(testing=True);self.s=self.w.storage
  for table in ('sessions','daily','kv','health_log'):self.s.conn.execute('DELETE FROM '+table)
  self.s.conn.commit();self.w.apply_theme();self.w.history_at=0;self.w.refresh()
 def tearDown(self):self.w.timer.stop();self.w.hover.stop();self.w.sync_timer.stop();self.w.hide();self.w.deleteLater();app.processEvents();self.s.conn.close()
 def test_export_midnight_hourly_and_health(self):
  start=datetime(2026,1,1,23,30);end=datetime(2026,1,2,1,15)
  self.s.conn.execute('INSERT INTO sessions(kind,started_at,ended_at) VALUES(?,?,?)',('work',start.isoformat(),end.isoformat()));self.s.conn.commit();self.s.set_day_field('creatives',3,'2026-01-01');self.s.set_day_field('sleep_minutes',420,'2026-01-01');self.s.set_day_extra('sleep_stages',{'light':18000,'deep':7200},'2026-01-01');self.s.set_setting('private_sentinel','DO_NOT_EXPORT')
  data=capture(self.s,datetime(2026,1,2,2));first,second=data['daily'];self.assertEqual(first['work_seconds'],1800);self.assertEqual(second['work_seconds'],4500);self.assertEqual(first['creatives'],3);self.assertEqual(first['light_sleep_seconds'],18000);self.assertEqual(sum(r['work_seconds'] for r in data['hourly']),6300);self.assertIsNone(second['sleep_minutes'])
  path=Path(temp.name)/'daily.csv';export_data(self.s,path);rows=list(csv.DictReader(io.StringIO(path.read_text(encoding='utf-8-sig'))));self.assertEqual(rows[0]['work_seconds'],'1800');self.assertNotIn('DO_NOT_EXPORT',path.read_text())
  zpath=Path(temp.name)/'all.zip';export_data(self.s,zpath,True)
  with zipfile.ZipFile(zpath) as z:self.assertEqual(set(z.namelist()),{'daily.csv','hourly.csv','sessions.csv','garmin_observations.csv','README.txt'});self.assertIsNone(z.testzip())
 def test_live_session_export_stops_at_capture(self):
  self.s.conn.execute('INSERT INTO sessions(kind,started_at) VALUES(?,?)',('learning','2026-01-01T23:45:00'));self.s.conn.commit();data=capture(self.s,datetime(2026,1,2,0,15));self.assertEqual([r['learning_seconds'] for r in data['daily']],[900,900]);self.assertIsNone(data['sessions'][0]['ended_at'])
 def test_tooltips_all_views_and_creatives(self):
  
  for kind in ('work','learning'):
   start=datetime.combine(date.today(),datetime.min.time());self.s.conn.execute('INSERT INTO sessions(kind,started_at,ended_at) VALUES(?,?,?)',(kind,start.isoformat(),(start+timedelta(hours=1)).isoformat()))
  self.s.conn.commit();self.w.history_at=0;self.s.set_day_field('creatives',3);self.s.set_day_field('sleep_minutes',420);self.s.set_day_extra('sleep_score',81);self.s.set_day_extra('sleep_stages',{'light':18000,'deep':3600,'rem':3600});self.w.refresh()
  for kind in ('work','learning'):
   c=self.w.canvas;c.kind=kind;c.load_design()
   for key in ('annual','monthly','workweek','sleepweek'):
    x,y,w,h=c.geo[key][-1]
    if key=='monthly':y=c.box(533)[1]-15;h=2
    tip=c.tooltip_at(QPointF(x+w/2,y+h/2));self.assertIn('Creatives: 3',tip);self.assertIn(date.today().strftime('%B %Y'),tip);self.assertIn('Sleep: 7h' if key=='sleepweek' else kind.title()+':',tip)
   box,stage,seconds,level=next(r for r in c.stage_regions() if r[1]=='light');x,y,w,h=box;tip=c.tooltip_at(QPointF(x+w/2,y+h/2));self.assertIn('Light Sleep: 5h 00m',tip);self.assertIn('Sleep score: 81',c.tooltip_at(QPointF(2800,2500)))
 def test_settings_opaque_top_save_and_themes(self):
  self.w.show();self.w.resize(420,1050);app.processEvents();self.w.settings();QTest.qWait(370);p=self.w.settings_panel;im=self.w.grab().toImage();self.assertEqual(im.pixelColor(3,100),QColor(colors(self.w)[0]));self.assertEqual(im.pixelColor(30,38),QColor(colors(self.w)[0]));self.assertFalse(hasattr(p,'save_button'));self.assertEqual(p.geometry(),self.w.rect())
  p.theme.setCurrentText('Dark');self.assertEqual(colors(self.w)[0],SOFT_DARK);p.theme.setCurrentText('High Contrast');self.assertEqual(colors(self.w)[0],DARK)
 def test_synchronized_slide_finishes_cleanly(self):
  c=self.w.canvas;c.setFixedSize(600,1863);c.toggle_analytics();self.assertEqual(len(c.slide_layers),2);c.anim.setCurrentTime(210);self.assertLess(c.slide_layers[0].x(),0);self.assertGreater(c.slide_layers[1].x(),0);self.assertEqual(c.slide_layers[1].x()-c.slide_layers[0].x(),600);QTest.qWait(450);self.assertEqual(c.slide_layers,[])
 def test_freshness_and_dated_history_logging(self):
  now=datetime(2026,9,23,15,7);msg=freshness_text(now.isoformat(),'2026-09-23T05:20:00.0',now);self.assertIn('stale',msg);self.assertIn('05:20',msg);self.assertNotIn('stale',freshness_text(now.isoformat(),'2026-09-23T15:00:00',now));self.assertIn('unavailable',freshness_text(now.isoformat(),'2026-09-23T23:59:59',now))
  self.w.synced({'_day':'2026-09-22','_data_through':'2026-09-22T23:40:00','steps':400,'sleep_stages':{'light':18000},'_history':[{'_day':'2026-09-21','steps':123}]});self.assertEqual(self.s.existing_day('2026-09-22')['steps'],400);self.assertEqual(self.s.existing_day('2026-09-21')['steps'],123);self.assertEqual(self.s.conn.execute('SELECT COUNT(*) FROM health_log').fetchone()[0],2)
 def test_reject_mismatched_garmin_date(self):
  class Client:
   def get_sleep_data(self,d):return {}
   def get_stats(self,d):return {'calendarDate':'2000-01-01','totalSteps':19}
  b=GarminBridge();b.client=Client()
  with self.assertRaises(ValueError):b.today()
if __name__=='__main__':unittest.main(verbosity=2)
