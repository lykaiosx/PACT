import os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
temp=tempfile.TemporaryDirectory();os.environ['PACT_DATA_DIR']=temp.name;os.environ['PACT_TOKEN_DIR']=temp.name+'/tokens';os.environ['QT_QPA_PLATFORM']='offscreen'
sys.path.insert(0,str(Path('app').resolve()))
from PySide6.QtCore import QRect,Qt,QEvent
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QEventLoop,QTimer
from app import PACT
from panels import Settings
from backup import create_backup,restore_backup
from progress import reset_progress
app=QApplication([])
class Screen:
 def __init__(self,w,h,x=0):self.rect=QRect(x,0,w,h)
 def availableGeometry(self):return self.rect
class DisplayTests(unittest.TestCase):
 def setUp(self):
  self.w=PACT(testing=True);self.s=self.w.storage
  self.s.conn.execute('DELETE FROM kv');self.s.conn.commit();self.w.timer.stop();self.w.hover.stop()
 def tearDown(self):
  if self.w.display_hint:self.w.display_hint.reject()
  self.w.hide();self.w.deleteLater();app.sendPostedEvents(None,QEvent.DeferredDelete);self.s.conn.close()
 def test_default_geometry_unchanged(self):
  for width,height in [(1280,720),(1920,1040),(2560,1400),(3840,2120)]:
   screen=Screen(width,height,1920);self.w.fit_screen(screen)
   self.assertEqual(self.w.width(),min(520,width,max(320,int(height*3000/9314))))
   self.assertEqual(self.w.geometry().right(),screen.rect.right());self.assertEqual(self.w.geometry().bottom(),screen.rect.bottom())
 def test_adjusted_geometry_scales_and_stays_on_screen(self):
  self.s.set_setting('display_auto_adjust',True)
  for width,height in [(600,600),(1280,720),(1920,1040),(2560,1400),(3840,2120)]:
   screen=Screen(width,height,-width);self.w.fit_screen(screen)
   self.assertGreaterEqual(self.w.width(),min(520,width,max(320,int(height*3000/9314))))
   self.assertLessEqual(self.w.width(),width);self.assertEqual(self.w.geometry().right(),-1)
   self.assertEqual(self.w.height(),height);self.assertEqual(self.w.scroll.verticalScrollBarPolicy(),Qt.ScrollBarAsNeeded)
 def test_toggle_persists_and_reverts(self):
  self.w.show();p=Settings(self.w)
  with patch.object(self.w,'refit_current_screen',side_effect=lambda:self.w.fit_screen(Screen(1920,1040))):
   p.auto_adjust.setChecked(True);self.assertTrue(self.s.get_setting('display_auto_adjust'));self.assertEqual(self.w.width(),480)
   reopened=Settings(self.w);self.assertTrue(reopened.auto_adjust.isChecked());self.assertIn('16px',reopened.styleSheet());reopened.deleteLater()
   p.auto_adjust.setChecked(False);self.assertEqual(self.w.width(),334);self.assertIn('14px',p.styleSheet())
  p.deleteLater()
 def test_monitor_change_refits(self):
  with patch.object(self.w,'refit_current_screen') as refit:
   self.w.on_display_changed();app.processEvents();refit.assert_called_once()
 def test_backup_and_reset_preserve_preference(self):
  self.s.set_setting('display_auto_adjust',True);self.s.set_setting('display_hint_seen',True)
  path=Path(temp.name)/'display.pact';create_backup(self.s,path);reset_progress(self.s)
  self.assertTrue(self.s.get_setting('display_auto_adjust'));self.s.set_setting('display_auto_adjust',False);restore_backup(self.s,path)
  self.assertTrue(self.s.get_setting('display_auto_adjust'));self.assertTrue(self.s.get_setting('display_hint_seen'))
 def test_welcome_once_and_never_hidden(self):
  self.w.show_display_hint();self.assertIsNone(self.w.display_hint)
  self.w.show();self.w.show_display_hint();box=self.w.display_hint;self.assertIsNotNone(box)
  self.w.show_display_hint();self.assertIs(self.w.display_hint,box)
  next(b for b in box.buttons() if b.text()=='Got it').click();self.assertTrue(self.s.get_setting('display_hint_seen'))
  self.w.show_display_hint();self.assertIsNone(self.w.display_hint)
 def test_welcome_settings_shortcut(self):
  self.w.show();self.w.show_display_hint()
  next(b for b in self.w.display_hint.buttons() if b.text()=='Open Settings').click()
  self.assertIsInstance(self.w.settings_panel,Settings);self.assertFalse(self.w.settings_panel.auto_adjust.isChecked())
 def test_testing_reveal_does_not_show_welcome(self):
  self.w.reveal();loop=QEventLoop();QTimer.singleShot(400,loop.quit);loop.exec();self.assertIsNone(self.w.display_hint)
if __name__=='__main__':unittest.main()
