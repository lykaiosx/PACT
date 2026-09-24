import os,sys,tempfile,unittest,json,zipfile,hashlib
from pathlib import Path
from datetime import datetime,date,timedelta
from unittest.mock import patch
temp=tempfile.TemporaryDirectory();os.environ['PACT_DATA_DIR']=temp.name;os.environ['PACT_TOKEN_DIR']=temp.name+'/tokens';os.environ['QT_QPA_PLATFORM']='offscreen'
sys.path.insert(0,str(Path('app').resolve()))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QDate,QDateTime,QPointF,QEventLoop,QTimer
from app import PACT
from storage import Storage
from data_export import capture
from backup import create_backup,load_backup,restore_backup
from garmin_client import sync_state
from panels import colors
app=QApplication([])
def wait(ms):loop=QEventLoop();QTimer.singleShot(ms,loop.quit);loop.exec()

class V11(unittest.TestCase):
 def setUp(self):
  self.w=PACT(testing=True);self.s=self.w.storage
  for t in ('sessions','daily','kv','health_log','time_edits'):self.s.conn.execute('DELETE FROM '+t)
  self.s.conn.commit();self.w.history_at=0;self.w.refresh();self.day=(date.today()-timedelta(days=1)).isoformat()
 def tearDown(self):
  self.w.timer.stop();self.w.hover.stop();self.w.sync_timer.stop();self.w.hide();self.w.deleteLater();app.processEvents();self.s.conn.close()
 def add(self,kind='work',start='09:00:00',end='13:00:00'):
  return self.s.correct_session(kind,self.day+'T'+start,self.day+'T'+end)
 def test_add_deduct_undo_totals_exports_both_activities(self):
  for kind in ('work','learning'):
   sid=self.add(kind);self.s.correct_session(kind,self.day+'T09:00:00',self.day+'T11:00:00',sid)
   self.w.history_at=0;self.w.refresh();self.assertEqual(self.s.seconds_for_day(kind,self.day),7200)
   self.assertEqual(self.w.histories[kind][-2][1],2);self.assertEqual(self.w.annual[kind],2)
   row=next(r for r in capture(self.s)['daily'] if r['date']==self.day);self.assertEqual(row[kind+'_seconds'],7200)
   self.s.undo_time_edit();self.assertEqual(self.s.seconds_for_day(kind,self.day),14400)
   self.s.correct_session(kind,session_id=sid,remove=True);self.assertEqual(self.s.seconds_for_day(kind,self.day),0)
   self.s.undo_time_edit();self.assertEqual(self.s.seconds_for_day(kind,self.day),14400)
 def test_cross_midnight_and_overlap_validation(self):
  before=(date.fromisoformat(self.day)-timedelta(days=1)).isoformat()
  self.s.correct_session('work',before+'T23:30:00',self.day+'T00:30:00')
  self.assertEqual(self.s.seconds_for_day('work',before),1800);self.assertEqual(self.s.seconds_for_day('work',self.day),1800)
  with self.assertRaises(ValueError):self.s.correct_session('work',self.day+'T00:00:00',self.day+'T01:00:00')
  with self.assertRaises(ValueError):self.add(start='13:00:00',end='09:00:00')
  with self.assertRaises(ValueError):self.s.correct_session('work',datetime.now().isoformat(),(datetime.now()+timedelta(hours=1)).isoformat())
 def test_running_sessions_protected_and_undo_survives_restart(self):
  sid=self.s.start_session('work')
  with self.assertRaises(ValueError):self.s.correct_session('work',session_id=sid,remove=True)
  self.add('learning');other=Storage(self.s.db_path);other.undo_time_edit();other.conn.close();self.assertEqual(self.s.seconds_for_day('learning',self.day),0)
 def test_undo_refuses_new_conflicting_session(self):
  sid=self.add();self.s.correct_session('work',self.day+'T09:00:00',self.day+'T11:00:00',sid)
  self.s.conn.execute('INSERT INTO sessions(kind,started_at,ended_at) VALUES(?,?,?)',('work',self.day+'T11:00:00',self.day+'T12:00:00'));self.s.conn.commit()
  with self.assertRaises(ValueError):self.s.undo_time_edit()
 def test_backup_roundtrip_and_safety_copy_and_secret_exclusion(self):
  self.add();self.s.set_day_field('creatives',3,self.day);self.s.set_day_extra('hydration_ml',500, self.day);self.s.set_setting('theme','dark');self.s.set_setting('target_learning',3);self.s.set_setting('password','NEVER_INCLUDE')
  self.s.record_health({'steps':25},self.day,datetime.now().isoformat())
  path=Path(temp.name)/'migration.pact';create_backup(self.s,path)
  with zipfile.ZipFile(path) as z:self.assertNotIn(b'NEVER_INCLUDE',z.read('pact.json'))
  self.s.set_setting('target_learning',6);safety=restore_backup(self.s,path)
  self.assertEqual(self.s.target('learning'),3);self.assertEqual(self.s.seconds_for_day('work',self.day),14400);self.assertEqual(self.s.get_day(self.day)['creatives'],3);self.assertEqual(self.s.day_extra('hydration_ml',day=self.day),500);self.assertEqual(self.s.get_setting('theme'),'dark')
  self.assertEqual(self.s.conn.execute('SELECT COUNT(*) FROM health_log').fetchone()[0],1)
  restore_backup(self.s,safety);self.assertEqual(self.s.target('learning'),6)
 def test_backup_closes_copy_of_running_timer_only(self):
  self.s.start_session('work');path=Path(temp.name)/'running.pact';data=create_backup(self.s,path)
  self.assertIsNotNone(self.s.active_session('work'));self.assertEqual(data['running_timers_stopped'],1);restore_backup(self.s,path);self.assertIsNone(self.s.active_session('work'))
 def test_corrupt_backup_and_invalid_payload_do_not_modify_data(self):
  self.add();path=Path(temp.name)/'bad.pact';data=create_backup(self.s,path)
  for change in ('version','timestamp','goal','stages'):
   bad=json.loads(json.dumps(data))
   if change=='version':bad['version']=999
   if change=='timestamp':bad['tables']['sessions'][0]['ended_at']='invalid'
   if change=='goal':bad['tables']['kv'].append({'key':'target_work','value':'-1'})
   if change=='stages':bad['tables']['kv'].append({'key':self.day+':sleep_stages','value':'{"deep":-1}'})
   raw=json.dumps(bad).encode()
   with zipfile.ZipFile(path,'w') as z:z.writestr('pact.json',raw);z.writestr('sha256.txt',hashlib.sha256(raw).hexdigest())
   with self.assertRaises(ValueError):restore_backup(self.s,path)
   self.assertEqual(self.s.seconds_for_day('work',self.day),14400)
  path.write_bytes(b'broken')
  with self.assertRaises(ValueError):restore_backup(self.s,path)
 def test_sleep_survives_new_day_until_new_record(self):
  self.s.set_day_field('sleep_minutes',420,self.day);self.s.set_day_extra('sleep_score',85,self.day);self.s.set_day_extra('sleep_stages',{'light':18000,'deep':7200},self.day)
  self.s.set_day_field('sleep_minutes',0);self.s.set_day_extra('sleep_score',0)
  self.w.refresh();self.assertEqual(self.w.sleep['day'],self.day);self.assertEqual(self.w.sleep['sleep_score'],85)
  c=self.w.canvas;box,*_=c.stage_regions()[0];x,y,w,h=box;self.assertIn(date.fromisoformat(self.day).strftime('%B %Y'),c.tooltip_at(QPointF(x+w/2,y+h/2)))
  self.s.set_day_field('sleep_minutes',390);self.s.set_day_extra('sleep_score',90);self.w.refresh();self.assertEqual(self.w.sleep['day'],date.today().isoformat());self.assertEqual(self.w.sleep['sleep_score'],90)
 def test_freshness_conditions_and_future_day_boundary(self):
  now=datetime(2026,9,24,14,0)
  self.assertFalse(sync_state('2026-09-24T13:59:00','2026-09-24T13:55:00',now)[0])
  self.assertTrue(sync_state('2026-09-24T13:40:00',None,now)[0]);self.assertTrue(sync_state('2026-09-24T13:59:00','2026-09-24T10:00:00',now)[0])
  attention,text=sync_state('2026-09-24T13:59:00','2026-09-24T23:59:59',now);self.assertFalse(attention);self.assertIn('unavailable',text)
  self.assertTrue(sync_state(None,None,now)[0]);self.assertTrue(sync_state(None,None,now,error='Failed')[0]);self.assertFalse(sync_state(None,None,now,busy=True)[0])
 def test_editor_buttons_deduction_and_theme_indicator(self):
  self.add();self.w.canvas.time_buttons[0].click();p=self.w.settings_panel;p.day.setDate(QDate.fromString(self.day,'yyyy-MM-dd'));p.sessions.setCurrentIndex(1);p.subtract.setValue(2);p.deduct.click();self.assertEqual(self.s.seconds_for_day('work',self.day),7200);p.undo();self.assertEqual(self.s.seconds_for_day('work',self.day),14400)
  self.w.close_settings();wait(260);self.w.show();app.processEvents()
  for theme in ('light','dark','high contrast','custom'):
   self.s.set_setting('theme',theme);self.s.set_setting('custom_ink','#517242');self.s.set_setting('custom_background','#eee8dc');self.w.apply_theme();self.w.refresh();dot=self.w.canvas.sync_indicator;self.assertTrue(dot.attention);self.assertFalse(dot.toolTip());self.assertIn('Garmin status',dot.accessibleName());self.assertFalse(dot.grab().isNull())
  dot.click();self.assertIsNotNone(self.w.settings_panel)
 def test_restore_ui_does_not_overwrite_restored_settings(self):
  self.s.set_setting('target_work',6);path=Path(temp.name)/'ui.pact';create_backup(self.s,path);self.s.set_setting('target_work',12);self.w.settings();p=self.w.settings_panel;p.restore_path=str(path);p.restore();wait(350)
  self.assertEqual(self.s.target('work'),6);self.assertEqual(self.w.settings_panel.fields['work'].value(),6);self.assertIn('restored',self.w.settings_panel.saved_note.text())

if __name__=='__main__':unittest.main(verbosity=2)
