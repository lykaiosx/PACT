import os,sys,tempfile,unittest
from pathlib import Path
from datetime import date,timedelta
from unittest.mock import patch,Mock
temp=tempfile.TemporaryDirectory();os.environ['PACT_DATA_DIR']=temp.name;os.environ['PACT_TOKEN_DIR']=temp.name+'/tokens';os.environ['QT_QPA_PLATFORM']='offscreen';sys.path.insert(0,str(Path('app').resolve()))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QRect,QEvent
from app import PACT
from weekly_review import summary,last_week,WeeklyReview
from backup import create_backup,restore_backup
app=QApplication([])
class Screen:
 def availableGeometry(self):return QRect(0,0,3840,2120)
class ReviewTests(unittest.TestCase):
 def setUp(self):
  self.w=PACT(testing=True);self.s=self.w.storage;self.w.timer.stop();self.w.hover.stop()
  for table in ('sessions','daily','kv','edit_history','time_edits','imported_totals'):self.s.conn.execute('DELETE FROM '+table)
  self.s.conn.commit();self.start=last_week()
 def tearDown(self):
  self.w.tray=None;self.w.hide();self.w.deleteLater();app.sendPostedEvents(None,QEvent.DeferredDelete);self.s.conn.close()
 def add(self,offset,hours,kind='work'):
  day=(self.start+timedelta(days=offset)).isoformat();self.s.conn.execute('INSERT INTO imported_totals VALUES(?,?,?)',(day,kind,int(hours*3600)));self.s.conn.commit()
 def test_slider_live_endpoints_midpoint_and_backup(self):
  self.w.settings();p=self.w.settings_panel
  with patch.object(self.w,'refit_current_screen',side_effect=lambda:self.w.fit_screen(Screen())):
   p.width_slider.setValue(100);largest=self.w.width();p.width_slider.setValue(0);original=self.w.width();p.width_slider.setValue(50);self.assertEqual(self.w.width(),round((largest+original)/2));self.assertEqual(original,520);self.assertEqual(largest,832)
  path=Path(temp.name)/'width.pact';create_backup(self.s,path);self.s.set_setting('display_width',1);restore_backup(self.s,path);self.assertEqual(self.s.get_setting('display_width'),50)
 def test_week_boundaries_and_empty(self):
  self.assertEqual(last_week(date(2026,1,1)),date(2025,12,22));self.assertEqual(last_week(date(2026,1,5)),date(2025,12,29));r=summary(self.s);self.assertFalse(r['has_data']);self.assertIsNone(r['sleep_average']);self.assertEqual(r['meal_entries'],0)
  with self.assertRaises(ValueError):summary(self.s,date.today())
 def test_totals_goals_streaks_best_and_comparison(self):
  for i,hours in enumerate([8,9,8,0,10]):self.add(i,hours)
  self.add(-7,2);self.add(2,2,'learning');r=summary(self.s);a=r['activities']['work'];self.assertEqual(a['total'],35*3600);self.assertEqual(a['streak'],3);self.assertEqual(a['goal_days'],4);self.assertEqual(a['best'][0],self.start+timedelta(days=4));self.assertEqual(a['previous'],7200);self.assertEqual(a['recorded'],5)
 def test_missing_habits_are_not_zero_and_edits_recompute(self):
  day=self.start.isoformat();self.s.edit_manual('creatives',3,day);self.s.edit_manual('breakfast',0,day);self.s.set_day_field('sleep_minutes',420,day);r=summary(self.s);self.assertEqual(r['creative_days'],1);self.assertEqual(r['meal_entries'],1);self.assertEqual(r['complete_meal_days'],0);self.assertEqual(r['sleep_average'],420);self.assertEqual(r['edited_days'],1);self.s.edit_manual('creatives',5,day);self.assertEqual(summary(self.s)['creatives'],5)
 def test_notification_once_and_opt_out(self):
  self.add(0,1);self.w.tray=Mock();self.s.set_setting('monthly_notifications',False);self.s.set_setting('weekly_notifications',False);self.w.check_weekly_review();self.w.tray.showMessage.assert_not_called();self.s.set_setting('weekly_notifications',True);self.w.check_weekly_review();self.w.check_weekly_review();self.w.tray.showMessage.assert_called_once()
 def test_review_navigation_and_return_to_settings(self):
  self.w.settings();self.w.open_weekly_review();self.assertIsInstance(self.w.settings_panel,WeeklyReview);self.assertIn('No recorded data',self.w.settings_panel.slides[0]['detail']);self.w.return_to_settings();self.assertTrue(hasattr(self.w.settings_panel,'width_slider'))
if __name__=='__main__':unittest.main()
