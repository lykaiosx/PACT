import os,sys,tempfile,unittest
from pathlib import Path
from datetime import date,datetime,timedelta
temp=tempfile.TemporaryDirectory();os.environ['PACT_DATA_DIR']=temp.name;os.environ['PACT_TOKEN_DIR']=temp.name+'/tokens';os.environ['QT_QPA_PLATFORM']='offscreen'
sys.path.insert(0,str(Path('app').resolve()))
from PySide6.QtWidgets import QApplication,QPushButton
from PySide6.QtGui import QFontDatabase,QColor
from PySide6.QtCore import Qt,QPoint,QPointF,QEventLoop,QTimer
from app import PACT,ASSETS
from panels import colors
from garmin_client import GarminBridge
from storage import Storage
from data_export import capture
app=QApplication([]);QFontDatabase.addApplicationFont(str(ASSETS/'fonts/Newsreader.ttf'))
def wait(ms):loop=QEventLoop();QTimer.singleShot(ms,loop.quit);loop.exec()
class HoverHydration(unittest.TestCase):
 def setUp(self):
  self.w=PACT(testing=True);self.s=self.w.storage
  for table in ('sessions','daily','kv','health_log'):self.s.conn.execute('DELETE FROM '+table)
  self.s.conn.commit();self.w.apply_theme();self.w.history_at=0;self.w.refresh()
 def tearDown(self):self.w.timer.stop();self.w.hover.stop();self.w.sync_timer.stop();self.w.hide();self.w.deleteLater();app.processEvents();self.s.conn.close()
 def test_stable_hover_through_moves_and_gaps(self):
  self.w.show();app.processEvents();detail=self.w.canvas.details;anchor=self.w.mapToGlobal(QPoint(100,200));text='23 September 2026\nWork: 1h 00m\nCreatives: 3'
  for i in range(50):detail.offer(text,anchor+QPoint(i,0))
  wait(140);self.assertTrue(detail.isVisible());position=detail.pos()
  for i in range(50):detail.offer(text,anchor+QPoint(i,20))
  self.assertEqual(detail.pos(),position);self.assertTrue(detail.testAttribute(Qt.WA_TransparentForMouseEvents));self.assertFalse(detail.isWindow())
  detail.offer('',anchor);wait(50);self.assertTrue(detail.isVisible());detail.offer('Different day\nWork: 2h',anchor);wait(100);self.assertTrue(detail.isVisible());self.assertIn('Different day',detail.text());self.assertIn(colors(self.w)[0],detail.styleSheet());detail.offer('',anchor);wait(150);self.assertFalse(detail.isVisible())
 def test_blank_columns_legends_and_control_tips(self):
  c=self.w.canvas
  for kind in ('work','learning'):
   c.kind=kind;c.load_design();c.retheme();x,y,w,h=c.geo['monthly'][0];self.assertEqual(c.tooltip_at(QPointF(x+w/2,c.box(533)[1]-15)),'');x,y,w,h=c.geo['annual'][0];tip=c.tooltip_at(QPointF(x+w/2,y+h/2));self.assertIn('Not available',tip);self.assertNotIn('Creatives:',tip)
   for i in (545,548,551,554):x,y,w,h=c.box(i);self.assertEqual(c.tooltip_at(QPointF(x+w/2,y+h/2)),'')
  self.assertTrue(all(not b.toolTip() for b in c.findChildren(QPushButton)));self.assertFalse(c.controls[5][0].isEnabled())
 def test_only_painted_monthly_bar_has_details(self):
  start=datetime.combine(date.today(),datetime.min.time());self.s.conn.execute('INSERT INTO sessions(kind,started_at,ended_at) VALUES(?,?,?)',('work',start.isoformat(),(start+timedelta(hours=1)).isoformat()));self.s.conn.commit();self.w.history_at=0;self.w.refresh();c=self.w.canvas;x,y,w,h=c.geo['monthly'][-1];baseline=c.box(533)[1]-9
  self.assertIn('Work: 1h',c.tooltip_at(QPointF(x+w/2,baseline-20)));self.assertEqual(c.tooltip_at(QPointF(x+w/2,baseline-900)),'')
 def test_autosave_without_closing_and_flush_typed_values(self):
  self.w.settings();p=self.w.settings_panel;p.theme.setCurrentText('Dark');self.assertEqual(self.s.get_setting('theme'),'dark');p.fields['learning'].setValue(3);self.assertEqual(self.s.target('learning'),3);self.assertIs(self.w.settings_panel,p);self.assertFalse(any(b.text()=='Save' for b in p.findChildren(QPushButton)));self.assertNotIn('water_goal',p.fields)
  p.fields['work'].lineEdit().setText('10.25 h');self.w.close_settings();self.assertEqual(self.s.target('work'),10.25);other=Storage(self.s.db_path);self.assertEqual(other.target('work'),10.25);other.conn.close()
 def test_hydration_mapping_zero_goal_and_export(self):
  class Client:
   value=473.176
   def get_sleep_data(self,d):return {}
   def get_stats(self,d):return {'calendarDate':d,'totalSteps':506}
   def get_hydration_data(self,d):return {'calendarDate':d,'valueInML':self.value,'goalInML':2839.056}
  b=GarminBridge();b.client=Client();data=b.today();self.assertEqual(data['hydration_ml'],473.176);self.w.synced(data);self.assertEqual(self.w.canvas.hydration_text(),'2 / 12');row=capture(self.s)['daily'][-1];self.assertEqual(row['water_cups'],2);self.assertEqual(row['hydration_goal_ml'],2839.056);b.client.value=0;self.w.synced(b.today());self.assertEqual(self.w.canvas.hydration_text(),'0 / 12')
 def test_hydration_failure_keeps_other_metrics_and_five_minute_timer(self):
  class Client:
   def get_sleep_data(self,d):return {}
   def get_stats(self,d):return {'totalSteps':506}
   def get_hydration_data(self,d):raise ConnectionError()
  b=GarminBridge();b.client=Client();data=b.today();self.assertEqual(data['steps'],506);self.assertIsNone(data['hydration_ml']);self.w.synced(data);self.assertIn('Hydration could not',self.w.garmin_status);self.assertEqual(self.w.sync_timer.interval(),300000)
if __name__=='__main__':unittest.main(verbosity=2)
