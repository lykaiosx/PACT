import os,sys,tempfile,unittest,csv,json,zipfile,hashlib
from pathlib import Path
from datetime import datetime,date,timedelta
from unittest.mock import patch
temp=tempfile.TemporaryDirectory();os.environ['PACT_DATA_DIR']=temp.name;os.environ['PACT_TOKEN_DIR']=temp.name+'/tokens';os.environ['QT_QPA_PLATFORM']='offscreen'
sys.path.insert(0,str(Path('app').resolve()))
from PySide6.QtWidgets import QApplication,QMessageBox
from app import PACT
from data_export import export_data,capture
from progress import load_csv,import_csv,reset_progress
from backup import create_backup,restore_backup,load_backup
app=QApplication([])
class ProgressTests(unittest.TestCase):
 def setUp(self):
  self.w=PACT(testing=True);self.s=self.w.storage
  for t in ('sessions','daily','kv','health_log','time_edits','imported_totals'):self.s.conn.execute('DELETE FROM '+t)
  self.s.conn.commit();self.day=(date.today()-timedelta(days=2)).isoformat();self.path=Path(temp.name)/'daily.csv'
 def tearDown(self):
  self.w.timer.stop();self.w.hover.stop();self.w.sync_timer.stop();self.w.hide();self.w.deleteLater();app.processEvents();self.s.conn.close()
 def csv(self,rows):
  with self.path.open('w',encoding='utf-8-sig',newline='') as f:
   writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
 def row(self,**kwargs):return {'date':self.day,'work_seconds':'7200','learning_seconds':'1800','creatives':'3','sleep_minutes':'420','steps':'500',**kwargs}
 def test_csv_roundtrip_keeps_daily_totals_without_invented_sessions(self):
  self.s.correct_session('work',self.day+'T09:00:00',self.day+'T11:00:00');self.s.set_day_field('creatives',3,self.day);self.s.set_day_extra('sleep_stages',{'deep':1800},self.day);export_data(self.s,self.path)
  reset_progress(self.s);count,_,_=import_csv(self.s,self.path);self.assertGreater(count,0);self.assertEqual(self.s.seconds_for_day('work',self.day),7200);self.assertEqual(self.s.get_day(self.day)['creatives'],3);self.assertEqual(self.s.day_extra('sleep_stages',day=self.day),{'deep':1800})
  data=capture(self.s);self.assertFalse(data['sessions']);self.assertEqual(next(r for r in data['daily'] if r['date']==self.day)['work_seconds'],7200);self.assertTrue(all(r['work_seconds'] is None for r in data['hourly']))
  full=Path(temp.name)/'full.zip';export_data(self.s,full,True)
  with zipfile.ZipFile(full) as z:self.assertIn('imported_daily_totals.csv',z.namelist())
 def test_repeat_import_and_existing_dates_are_skipped(self):
  self.csv([self.row()]);self.assertEqual(import_csv(self.s,self.path)[:2],(1,0));self.assertEqual(import_csv(self.s,self.path)[:2],(0,1));self.assertEqual(self.s.seconds_for_day('work',self.day),7200)
  reset_progress(self.s);self.s.set_day_field('steps',0,self.day);self.assertEqual(import_csv(self.s,self.path)[:2],(0,1))
 def test_bad_csv_is_rejected_before_any_import(self):
  for values in ({'work_seconds':'-1'},{'work_seconds':'NaN'},{'work_seconds':'90000'},{'date':'3000-01-01'},{'steps':'1.5'},{'breakfast':'2'}):
   self.csv([self.row(**values)])
   with self.assertRaises(ValueError):import_csv(self.s,self.path)
   self.assertEqual(self.s.conn.execute('SELECT COUNT(*) FROM imported_totals').fetchone()[0],0)
  self.csv([self.row(),self.row()])
  with self.assertRaises(ValueError):import_csv(self.s,self.path)
  self.path.write_text('started_at,ended_at\nx,y\n')
  with self.assertRaises(ValueError):load_csv(self.path)
 def test_import_totals_survive_backup_and_restore(self):
  self.csv([self.row()]);import_csv(self.s,self.path);path=Path(temp.name)/'with-imports.pact';create_backup(self.s,path);reset_progress(self.s);restore_backup(self.s,path);self.assertEqual(self.s.seconds_for_day('work',self.day),7200);self.assertTrue(self.s.has_activity_record('work',self.day))
 def test_old_pact_backup_still_loads(self):
  path=Path(temp.name)/'old.pact';data=create_backup(self.s,path);data['tables'].pop('imported_totals');raw=json.dumps(data).encode()
  with zipfile.ZipFile(path,'w') as z:z.writestr('pact.json',raw);z.writestr('sha256.txt',hashlib.sha256(raw).hexdigest())
  self.assertEqual(load_backup(path)['tables']['imported_totals'],[]);restore_backup(self.s,path)
 def test_reset_preserves_settings_and_can_recover_progress(self):
  self.csv([self.row()]);import_csv(self.s,self.path);self.s.start_session('learning');self.s.set_setting('theme','dark');self.s.set_setting('target_work',6)
  safety=reset_progress(self.s);self.assertIsNone(self.s.active_session('learning'));self.assertEqual(self.s.seconds_for_day('work',self.day),0);self.assertEqual(self.s.target('work'),6);self.assertEqual(self.s.get_setting('theme'),'dark');self.assertTrue(safety.exists());restore_backup(self.s,safety);self.assertEqual(self.s.seconds_for_day('work',self.day),7200)
 def test_reset_cancel_and_confirmation(self):
  self.s.correct_session('work',self.day+'T09:00:00',self.day+'T11:00:00');self.w.settings();p=self.w.settings_panel
  with patch('panels.QMessageBox.warning',return_value=QMessageBox.Cancel) as dialog:p.reset_progress();self.assertEqual(dialog.call_args.args[-1],QMessageBox.Cancel)
  self.assertEqual(self.s.seconds_for_day('work',self.day),7200)
  with patch('panels.QMessageBox.warning',return_value=QMessageBox.Yes):p.reset_progress()
  self.assertEqual(self.s.seconds_for_day('work',self.day),0)
 def test_reset_does_not_automatically_repopulate_old_garmin_days(self):
  reset_progress(self.s);self.w.synced({'_day':date.today().isoformat(),'steps':4,'_history':[{'_day':self.day,'steps':100}]});self.assertFalse(self.s.existing_day(self.day));self.assertEqual(self.s.get_day()['steps'],4)
 def test_csv_preview_and_confirmation(self):
  self.csv([self.row()]);self.w.settings();p=self.w.settings_panel
  with patch('panels.QFileDialog.getOpenFileName',return_value=(str(self.path),'')):p.preview_csv()
  self.assertIn('1 new dates',p.csv_note.text());self.assertEqual(self.s.seconds_for_day('work',self.day),0);p.import_csv();self.assertEqual(self.s.seconds_for_day('work',self.day),7200)
 def test_backup_failure_prevents_reset_or_import(self):
  self.s.correct_session('work',self.day+'T09:00:00',self.day+'T11:00:00');self.csv([self.row(date=(date.today()-timedelta(days=1)).isoformat())])
  with patch('progress.create_backup',side_effect=OSError('disk unavailable')):
   with self.assertRaises(OSError):reset_progress(self.s)
   with self.assertRaises(OSError):import_csv(self.s,self.path)
  self.assertEqual(self.s.seconds_for_day('work',self.day),7200);self.assertEqual(self.s.conn.execute('SELECT COUNT(*) FROM imported_totals').fetchone()[0],0)
if __name__=='__main__':unittest.main(verbosity=2)
