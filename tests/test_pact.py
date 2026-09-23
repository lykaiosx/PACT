import os,sys,tempfile,unittest,sqlite3,json,time
from pathlib import Path
from datetime import date,datetime,timedelta
TEST_DIR=tempfile.TemporaryDirectory(prefix='pact-tests-')
os.environ['PACT_DATA_DIR']=TEST_DIR.name
os.environ['PACT_TOKEN_DIR']=str(Path(TEST_DIR.name)/'tokens')
os.environ['QT_QPA_PLATFORM']='offscreen'
sys.path.insert(0,str(Path('app').resolve()))
from PySide6.QtWidgets import QApplication,QDialog
from PySide6.QtGui import QFontDatabase,QColor
from PySide6.QtCore import Qt
from app import PACT,Settings,ASSETS,themed_svg
from storage import Storage
from garmin_client import GarminBridge
app=QApplication([]);QFontDatabase.addApplicationFont(str(ASSETS/'fonts/Newsreader.ttf'))
class Tests(unittest.TestCase):
 def setUp(self):
  self.w=PACT(testing=True);self.s=self.w.storage
  self.s.conn.execute('DELETE FROM sessions');self.s.conn.execute('DELETE FROM daily');self.s.conn.execute('DELETE FROM kv');self.s.conn.commit();self.w.refresh()
 def tearDown(self):self.w.timer.stop();self.w.hover.stop();self.w.hide();self.w.deleteLater();app.processEvents();self.s.conn.close()
 def test_targets_persist_and_change_fill(self):
  start=datetime.combine(date.today(),datetime.min.time());end=start+timedelta(hours=2);self.s.conn.execute('INSERT INTO sessions(kind,started_at,ended_at) VALUES(?,?,?)',('work',start.isoformat(),end.isoformat()));self.s.conn.commit()
  self.w.refresh();self.w.canvas.setFixedSize(600,1800);self.w.apply_theme()
  first=self.w.canvas.grab().toImage();d=Settings(self.w);d.fields['work'].setValue(10);d.theme.setCurrentIndex(1);d.save()
  self.assertEqual(self.s.target('work'),10);self.assertTrue(self.w.dark)
  another=Storage(self.s.db_path);self.assertEqual(another.target('work'),10);self.assertEqual(another.get_setting('theme'),'dark');another.conn.close()
  self.s.set_setting('theme','light');self.w.apply_theme();second=self.w.canvas.grab().toImage()
  x=int(700/3000*first.width());y=int(950/9000*first.height())
  self.assertNotEqual(first.pixelColor(x,y),second.pixelColor(x,y))
 def test_timer_stop_resume_and_midnight(self):
  yesterday=date.today()-timedelta(days=1);start=datetime.combine(yesterday,datetime.min.time())+timedelta(hours=23)
  end=start+timedelta(hours=2)
  self.s.conn.execute('INSERT INTO sessions(kind,started_at,ended_at) VALUES(?,?,?)',('work',start.isoformat(),end.isoformat()));self.s.conn.commit()
  self.assertEqual(self.s.seconds_for_day('work',yesterday.isoformat()),3600);self.assertEqual(self.s.seconds_for_day('work',date.today().isoformat()),3600)
  self.w.toggle_timer('learning');self.assertIsNotNone(self.s.active_session('learning'));self.w.hide();self.assertIsNotNone(self.s.active_session('learning'));self.w.toggle_timer('learning');self.assertIsNone(self.s.active_session('learning'))
 def test_existing_database_backup_and_counts(self):
  self.s.set_day_field('creatives',9);self.s.set_setting('legacy_key',{'keep':True});self.s.set_day_extra('water',4)
  self.w.canvas.meal(0);self.assertTrue(self.s.get_day()['breakfast']);self.assertEqual(self.s.get_day()['creatives'],9)
  another=Storage(self.s.db_path);self.assertEqual(another.get_setting('legacy_key'),{'keep':True});self.assertEqual(another.day_extra('water'),4);another.conn.close()
  self.assertTrue(self.s.db_path.with_name('personalos-before-pact.sqlite3').exists())
 def test_window_hidden_bottom_and_not_topmost(self):
  self.w.reveal();app.processEvents();g=app.primaryScreen().availableGeometry();self.assertEqual(self.w.geometry().bottom(),g.bottom());self.assertFalse(bool(self.w.windowFlags()&Qt.WindowStaysOnTopHint))
  self.w.close();self.assertFalse(self.w.isVisible());self.w.reveal();self.assertTrue(self.w.isVisible())
 def test_corner_dwell_and_latch(self):
  import app as module
  original=module.QCursor
  class Cursor:
   @staticmethod
   def pos():return app.primaryScreen().geometry().topRight()
  module.QCursor=Cursor
  try:
   self.w.hide();self.w.check_corner();self.assertFalse(self.w.isVisible());self.w.corner_since=time.monotonic()-.5;self.w.check_corner();self.assertTrue(self.w.isVisible());self.w.hide();self.w.check_corner();self.assertFalse(self.w.isVisible())
  finally:module.QCursor=original
 def test_garmin_zero_and_sleep_mapping(self):
  class Client:
   def get_sleep_data(self,d):return {'dailySleepDTO':{'sleepTimeSeconds':28800,'sleepScores':{'overall':{'value':85}},'deepSleepSeconds':3600,'lightSleepSeconds':20000,'remSleepSeconds':5200,'awakeSleepSeconds':600}}
   def get_stats(self,d):return {'totalSteps':0,'restingHeartRate':55,'bodyBatteryMostRecentValue':75}
  bridge=GarminBridge();bridge.client=Client();data=bridge.today();self.assertEqual(data['steps'],0);self.assertEqual(data['sleep_minutes'],480);self.assertEqual(data['sleep_score'],85);self.w.synced(data);self.assertEqual(self.s.day_extra('body_battery'),75)
 def test_palette_and_asset_geometry(self):
  self.assertEqual(themed_svg('<rect fill="#FAFAFA"/><path fill="#100404"/>',True),'<rect fill="#100404"/><path fill="#FAFAFA"/>')
  self.assertEqual(len(self.w.canvas.geo['annual']),360);self.assertEqual(len(self.w.canvas.geo['monthly']),30)
  self.assertIn('Newsreader',QFontDatabase.families())
 def test_missing_data_is_not_fabricated(self):
  self.assertIsNone(self.s.get_day()['sleep_minutes']);self.assertIsNone(self.s.day_extra('sleep_score'));self.assertIsNone(self.s.day_extra('body_battery'))
if __name__=='__main__':unittest.main(verbosity=2)


