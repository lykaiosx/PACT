import os,sys,tempfile,unittest,json
from pathlib import Path
from datetime import date,timedelta
temp=tempfile.TemporaryDirectory();os.environ['PACT_DATA_DIR']=temp.name;os.environ['PACT_TOKEN_DIR']=temp.name+'/tokens';os.environ['QT_QPA_PLATFORM']='offscreen'
sys.path.insert(0,str(Path('app').resolve()))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QDate,QEvent
from app import PACT
from backup import create_backup,restore_backup
from progress import reset_progress,import_csv
from data_export import export_data,capture
app=QApplication([])
class Editing(unittest.TestCase):
 def setUp(self):
  self.w=PACT(testing=True);self.s=self.w.storage;self.w.timer.stop();self.w.hover.stop()
  for t in ('sessions','daily','time_edits','imported_totals','kv','edit_history'):self.s.conn.execute('DELETE FROM '+t)
  self.s.conn.commit();self.day=(date.today()-timedelta(days=1)).isoformat()
 def tearDown(self):
  self.w.hide();self.w.deleteLater();app.sendPostedEvents(None,QEvent.DeferredDelete);self.s.conn.close()
 def test_settings_dated_daily_editor(self):
  self.w.settings();p=self.w.settings_panel;self.assertEqual(p.tabs.count(),3);d=p.edit_data.daily;d.day.setDate(QDate.fromString(self.day,'yyyy-MM-dd'))
  for box in d.meals.values():box.setCurrentIndex(2)
  d.creatives.setValue(3);self.assertEqual(self.s.existing_day(self.day)['creatives'],3)
  self.assertTrue(all(self.s.existing_day(self.day)[k]==1 for k in d.meals));self.assertEqual(self.s.existing_day(date.today().isoformat())['creatives'],0)
  p.edit_history.reload();self.assertIn('Creatives',p.edit_history.text.toPlainText());self.assertIn('After: 3',p.edit_history.text.toPlainText())
 def test_unknown_zero_and_undo_are_distinct(self):
  self.assertIsNone(self.s.manual_value('creatives',self.day));self.s.edit_manual('creatives',0,self.day);self.assertEqual(self.s.manual_value('creatives',self.day),0);self.s.undo_manual();self.assertIsNone(self.s.manual_value('creatives',self.day));self.assertEqual(self.s.conn.execute('SELECT COUNT(*) FROM edit_history').fetchone()[0],2)
 def test_time_add_deduct_undo_leave_audit(self):
  self.s.correct_session('work',self.day+'T10:00:00',self.day+'T11:00:00');self.s.deduct_day('work',self.day,1800);self.s.undo_time_edit()
  actions=[r[0] for r in self.s.conn.execute('SELECT action FROM edit_history ORDER BY id')];self.assertEqual(actions,['Add time','Deduct time','Undo time correction'])
 def test_backup_reset_restore_preserves_history(self):
  self.s.edit_manual('breakfast',0,self.day);path=Path(temp.name)/'history.pact';create_backup(self.s,path);reset_progress(self.s);self.assertEqual(self.s.conn.execute('SELECT COUNT(*) FROM edit_history').fetchone()[0],0);restore_backup(self.s,path);self.assertEqual(self.s.manual_value('breakfast',self.day),0);self.assertEqual(self.s.conn.execute('SELECT COUNT(*) FROM edit_history').fetchone()[0],1)
 def test_exports_and_import_provenance(self):
  self.s.edit_manual('creatives',0,self.day);path=Path(temp.name)/'daily.csv';export_data(self.s,path);row=next(r for r in capture(self.s)['daily'] if r['date']==self.day);self.assertEqual(row['edited'],1);self.assertIsNone(row['breakfast']);reset_progress(self.s);import_csv(self.s,path);self.assertEqual(self.s.manual_value('creatives',self.day),0);self.assertIsNone(self.s.manual_value('breakfast',self.day));self.assertIn('CSV import',[r[0] for r in self.s.conn.execute('SELECT action FROM edit_history')])
 def test_health_and_future_dates_rejected(self):
  for field,day in [('steps',self.day),('creatives',(date.today()+timedelta(days=1)).isoformat())]:
   with self.assertRaises(ValueError):self.s.edit_manual(field,1,day)
 def test_earlier_time_corrections_migrate_once(self):
  self.s.correct_session('learning',self.day+'T10:00:00',self.day+'T11:00:00');self.s.conn.execute('DELETE FROM edit_history');self.s.conn.commit();self.s._init()
  self.assertEqual(self.s.conn.execute('SELECT action FROM edit_history').fetchone()[0],'Earlier correction');self.s._init();self.assertEqual(self.s.conn.execute('SELECT COUNT(*) FROM edit_history').fetchone()[0],1)
if __name__=='__main__':unittest.main()
