import os,sys,tempfile,unittest
from pathlib import Path
from datetime import date,timedelta
temp=tempfile.TemporaryDirectory();os.environ['PACT_DATA_DIR']=temp.name;os.environ['PACT_TOKEN_DIR']=temp.name+'/tokens';os.environ['QT_QPA_PLATFORM']='offscreen'
sys.path.insert(0,str(Path('app').resolve()))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QDate,QTime,QEvent
from app import PACT
from backup import create_backup,restore_backup
app=QApplication([])
class Corrections(unittest.TestCase):
 def setUp(self):
  self.w=PACT(testing=True);self.s=self.w.storage;self.w.timer.stop();self.w.hover.stop()
  for t in ('sessions','time_edits','imported_totals','kv'):self.s.conn.execute('DELETE FROM '+t)
  self.s.conn.commit();self.day=(date.today()-timedelta(days=3)).isoformat()
 def tearDown(self):
  self.w.hide();self.w.deleteLater();app.sendPostedEvents(None,QEvent.DeferredDelete);self.s.conn.close()
 def add(self,start,end,kind='work'):return self.s.correct_session(kind,self.day+'T'+start,self.day+'T'+end)
 def test_simple_add_and_deduct_without_selecting_session(self):
  self.w.edit_time('work');p=self.w.settings_panel;p.day.setDate(QDate.fromString(self.day,'yyyy-MM-dd'));p.quick_start.setTime(QTime(17,0));p.hours.setValue(0);p.minutes.setValue(30);p.quick_apply.click()
  self.assertEqual(self.s.seconds_for_day('work',self.day),1800);self.assertEqual(self.s.sessions_for_day('work',self.day)[0]['ended_at'],self.day+'T17:30:00')
  p.mode.setCurrentIndex(1);p.minutes.setValue(10);p.quick_apply.click();self.assertEqual(self.s.seconds_for_day('work',self.day),1200);p.undo();self.assertEqual(self.s.seconds_for_day('work',self.day),1800)
 def test_deduction_spans_sessions_and_undo_is_one_action(self):
  self.add('09:00:00','10:00:00');self.add('14:00:00','15:00:00');self.s.deduct_day('work',self.day,5400)
  self.assertEqual(self.s.seconds_for_day('work',self.day),1800);self.s.undo_time_edit();self.assertEqual(self.s.seconds_for_day('work',self.day),7200)
 def test_imported_only_and_mixed_deduction_backup(self):
  self.s.conn.execute('INSERT INTO imported_totals VALUES(?,?,?)',(self.day,'learning',3600));self.s.conn.commit();self.s.deduct_day('learning',self.day,1800);self.assertEqual(self.s.seconds_for_day('learning',self.day),1800);self.s.undo_time_edit()
  self.add('10:00:00','11:00:00','learning');self.s.deduct_day('learning',self.day,5400);self.assertEqual(self.s.seconds_for_day('learning',self.day),1800)
  path=Path(temp.name)/'corrected.pact';create_backup(self.s,path);restore_backup(self.s,path);self.assertEqual(self.s.seconds_for_day('learning',self.day),1800)
 def test_full_deduction_and_excess_rejected_without_changes(self):
  self.add('09:00:00','10:00:00')
  with self.assertRaises(ValueError):self.s.deduct_day('work',self.day,3601)
  self.assertEqual(self.s.seconds_for_day('work',self.day),3600);self.s.deduct_day('work',self.day,3600);self.assertEqual(self.s.seconds_for_day('work',self.day),0);self.s.undo_time_edit();self.assertEqual(self.s.seconds_for_day('work',self.day),3600)
 def test_cross_midnight_keeps_adjacent_days_and_undo(self):
  a=date.fromisoformat(self.day);previous=(a-timedelta(days=1)).isoformat();following=(a+timedelta(days=1)).isoformat();self.s.correct_session('work',previous+'T23:00:00',following+'T01:00:00')
  self.s.deduct_day('work',self.day,1800);self.assertEqual(self.s.seconds_for_day('work',self.day),84600)
  for d in (previous,following):self.assertEqual(self.s.seconds_for_day('work',d),3600)
  self.s.undo_time_edit();self.assertEqual(self.s.seconds_for_day('work',self.day),86400)
 def test_running_timer_is_not_modified(self):
  self.s.start_session('work')
  with self.assertRaises(ValueError):self.s.deduct_day('work',date.today().isoformat(),60)
  self.assertIsNotNone(self.s.active_session('work'))
 def test_undo_rejects_new_overlap(self):
  self.add('09:00:00','10:00:00');self.s.deduct_day('work',self.day,1800)
  self.s.conn.execute('INSERT INTO sessions(kind,started_at,ended_at) VALUES(?,?,?)',('work',self.day+'T09:45:00',self.day+'T10:00:00'));self.s.conn.commit()
  with self.assertRaises(ValueError):self.s.undo_time_edit()
 def test_advanced_full_session_deduction(self):
  self.add('09:00:00','10:00:00');self.w.edit_time('work');p=self.w.settings_panel;p.day.setDate(QDate.fromString(self.day,'yyyy-MM-dd'));p.mode.setCurrentIndex(2);p.sessions.setCurrentIndex(1);p.subtract.setValue(1);p.deduct.click();self.assertEqual(self.s.seconds_for_day('work',self.day),0)
if __name__=='__main__':unittest.main()
