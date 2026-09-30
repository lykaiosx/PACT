import os,sys,tempfile,unittest
from pathlib import Path
from datetime import date,timedelta
from unittest.mock import Mock
temp=tempfile.TemporaryDirectory();os.environ['PACT_DATA_DIR']=temp.name;os.environ['PACT_TOKEN_DIR']=temp.name+'/tokens';os.environ['QT_QPA_PLATFORM']='offscreen';sys.path.insert(0,str(Path('app').resolve()))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QDate,QEvent,QEventLoop,QTimer
from app import PACT
from wrapped import make_slides
app=QApplication([])
class WrappedTests(unittest.TestCase):
 def setUp(self):
  self.w=PACT(testing=True);self.s=self.w.storage;self.w.timer.stop();self.w.hover.stop()
  for table in ('sessions','daily','kv','edit_history','time_edits','imported_totals'):self.s.conn.execute('DELETE FROM '+table)
  self.s.conn.commit()
 def tearDown(self):
  self.w.tray=None;self.w.hide();self.w.deleteLater();app.sendPostedEvents(None,QEvent.DeferredDelete);self.s.conn.close()
 def test_eight_monthly_slides_and_leap_month(self):
  self.s.conn.execute("INSERT INTO imported_totals VALUES('2024-02-29','work',7200)");self.s.conn.commit();slides,period,r=make_slides(self.s,'Monthly',date(2024,2,1),date(2024,3,1));self.assertEqual(len(slides),8);self.assertEqual(len(r['days']),29);self.assertEqual(slides[1]['metric'],'2h');self.assertEqual(len({s['graphic'] for s in slides}),8);self.assertNotIn('so far',period)
 def test_current_month_partial_and_missing_data(self):
  slides,period,r=make_slides(self.s,'Monthly',date(2024,2,1),date(2024,2,10));self.assertIn('so far',period);self.assertEqual(len(r['days']),10);self.assertEqual(slides[7]['metric'],'—');self.assertEqual(slides[5]['metric'],'—')
 def test_navigation_animation_and_pause_on_hide(self):
  self.w.show();self.w.open_weekly_review();p=self.w.settings_panel;p.animation.stop();p.progress=1;p.go(1);self.assertEqual(p.index,1);self.assertEqual(p.previous,0);p.animation.setCurrentTime(325);self.assertGreater(p.progress,0);self.assertLess(p.progress,1);p.animation.setCurrentTime(650);self.assertEqual(p.progress,1);p.play.setChecked(True);self.assertTrue(p.timer.isActive());p.hide();self.assertFalse(p.timer.isActive());self.assertFalse(p.play.isChecked())
 def test_weekly_mode_and_period_switch_resets(self):
  self.w.open_weekly_review();p=self.w.settings_panel;p.go(5);p.mode.setCurrentIndex(1);self.assertEqual(p.index,0);self.assertEqual(len(p.report['days']),7);self.assertLess(p.report['end'],date.today());p.mode.setCurrentIndex(0);self.assertEqual(p.report['start'].day,1)
 def test_monthly_notification_once_and_opens_completed_month(self):
  last=date.today().replace(day=1)-timedelta(days=1);self.s.conn.execute('INSERT INTO imported_totals VALUES(?,?,?)',(last.isoformat(),'work',3600));self.s.conn.commit();self.s.set_setting('weekly_notifications',False);self.w.tray=Mock();self.w.check_weekly_review();self.w.check_weekly_review();self.w.tray.showMessage.assert_called_once();self.w.open_review_notice();self.assertEqual(self.w.settings_panel.report['end'],last)
if __name__=='__main__':unittest.main()
