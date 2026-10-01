import os,sys,tempfile,unittest
from pathlib import Path
from datetime import date,timedelta
temp=tempfile.TemporaryDirectory();os.environ['PACT_DATA_DIR']=temp.name;os.environ['PACT_TOKEN_DIR']=temp.name+'/tokens';os.environ['QT_QPA_PLATFORM']='offscreen';sys.path.insert(0,str(Path('app').resolve()))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QDate,QTime,QEvent
from app import PACT
app=QApplication([])
class SessionGuidance(unittest.TestCase):
 def setUp(self):
  self.w=PACT(testing=True);self.s=self.w.storage;self.w.timer.stop();self.w.hover.stop()
  for table in ('sessions','daily','kv','edit_history','time_edits','imported_totals'):self.s.conn.execute('DELETE FROM '+table)
  self.s.conn.commit();self.day=(date.today()-timedelta(days=3)).isoformat()
 def tearDown(self):
  self.w.hide();app.processEvents();self.w.deleteLater();app.sendPostedEvents(None,QEvent.DeferredDelete);self.s.conn.close()
 def add(self,a,b,kind='learning'):return self.s.correct_session(kind,self.day+'T'+a,self.day+'T'+b)
 def panel(self):
  self.w.edit_time('learning');p=self.w.settings_panel;p.day.setDate(QDate.fromString(self.day,'yyyy-MM-dd'));return p
 def test_use_last_end_preserves_seconds_and_adds_adjacent_time(self):
  self.add('21:00:00','22:30:47');p=self.panel();self.assertIn('10:30:47 PM',p.last_session_note.text());p.use_last_end.click();self.assertEqual(p.quick_start.time(),QTime(22,30,47));p.hours.setValue(0);p.minutes.setValue(30);p.quick_apply.click();rows=self.s.sessions_for_day('learning',self.day);self.assertEqual(rows[-1]['started_at'],self.day+'T22:30:47');self.assertEqual(rows[-1]['ended_at'],self.day+'T23:00:47');self.assertIn('11:00:47 PM',p.last_session_note.text())
 def test_overlap_names_exact_conflict_without_changing_data(self):
  self.add('21:00:00','22:30:47');p=self.panel();p.quick_start.setTime(QTime(22,30));p.minutes.setValue(30);before=self.s.conn.total_changes;p.quick_apply.click();self.assertIn('9:00:00 PM',p.message.text());self.assertIn('10:30:47 PM',p.message.text());self.assertIn('Learning',p.message.text());self.assertEqual(before,self.s.conn.total_changes)
 def test_activity_and_date_changes_refresh_reference(self):
  self.add('09:00:00','10:00:15');self.add('14:00:00','15:00:30','work');p=self.panel();p.kind.setCurrentText('Work');self.assertIn('3:00:30 PM',p.last_session_note.text());p.day.setDate(p.day.date().addDays(-1));self.assertIn('No Work sessions',p.last_session_note.text());self.assertFalse(p.use_last_end.isEnabled())
 def test_overnight_end_sets_correct_date(self):
  following=(date.fromisoformat(self.day)+timedelta(days=1)).isoformat();self.s.correct_session('learning',self.day+'T23:00:00',following+'T00:15:23');p=self.panel();p.use_last_end.click();self.assertEqual(p.day.date().toString('yyyy-MM-dd'),following);self.assertEqual(p.quick_start.time(),QTime(0,15,23))
 def test_running_session_has_no_invented_end(self):
  self.s.conn.execute('INSERT INTO sessions(kind,started_at) VALUES(?,?)',('learning',self.day+'T09:00:12'));self.s.conn.commit();p=self.panel();self.assertIn('still running',p.last_session_note.text());self.assertFalse(p.use_last_end.isEnabled());p.quick_start.setTime(QTime(10,0));p.quick_apply.click();self.assertIn('running Learning session',p.message.text());self.assertIn('9:00:12 AM',p.message.text())
 def test_imported_only_data_cannot_supply_session_end(self):
  self.s.conn.execute('INSERT INTO imported_totals VALUES(?,?,?)',(self.day,'learning',3600));self.s.conn.commit();p=self.panel();self.assertIn('imported daily total',p.last_session_note.text());self.assertFalse(p.use_last_end.isEnabled())
 def test_fractional_legacy_end_never_rounds_back_into_session(self):
  self.s.conn.execute('INSERT INTO sessions(kind,started_at,ended_at) VALUES(?,?,?)',('learning',self.day+'T09:00:00',self.day+'T10:00:12.500000'));self.s.conn.commit();p=self.panel();p.use_last_end.click();self.assertEqual(p.quick_start.time(),QTime(10,0,13));p.quick_apply.click();self.assertIn('Time added',p.message.text())
if __name__=='__main__':unittest.main()
