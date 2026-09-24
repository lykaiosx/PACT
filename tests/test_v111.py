import os,sys,tempfile,unittest
from pathlib import Path
temp=tempfile.TemporaryDirectory();os.environ['PACT_DATA_DIR']=temp.name;os.environ['PACT_TOKEN_DIR']=temp.name+'/tokens';os.environ['QT_QPA_PLATFORM']='offscreen'
sys.path.insert(0,str(Path('app').resolve()))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPoint,QEventLoop,QTimer
from PySide6.QtGui import QFontDatabase
from app import PACT,ASSETS
app=QApplication([]);QFontDatabase.addApplicationFont(str(ASSETS/'fonts/Newsreader.ttf'))
def wait(ms):loop=QEventLoop();QTimer.singleShot(ms,loop.quit);loop.exec()
class VisualFixes(unittest.TestCase):
 def setUp(self):self.w=PACT(testing=True);self.w.show();app.processEvents()
 def tearDown(self):
  self.w.timer.stop();self.w.hover.stop();self.w.sync_timer.stop();self.w.hide();self.w.storage.conn.close();self.w.deleteLater();app.processEvents()
 def test_long_sync_message_wraps_inside_sidebar(self):
  d=self.w.canvas.details;message='Cloud checked 14:39 · data through 24 Sep 08:37\nWatch data is stale. Sync your watch in Garmin Connect, then click Sync now.'
  for width in (320,420,520,693):
   self.w.resize(width,1100);app.processEvents();d.offer(message,self.w.mapToGlobal(QPoint(width-10,40)));d.present()
   self.assertTrue(self.w.rect().contains(d.geometry()));self.assertLessEqual(d.width(),width-16);self.assertGreaterEqual(d.height(),d.heightForWidth(d.width()));self.assertEqual(d.text(),message);self.assertTrue(d.wordWrap())
 def test_visible_hover_reflows_when_sidebar_narrows(self):
  self.w.resize(693,1100);app.processEvents();d=self.w.canvas.details;d.offer('Watch data is stale. Sync your watch in Garmin Connect, then click Sync now.',self.w.mapToGlobal(QPoint(650,40)));d.present();self.w.resize(320,1000);app.processEvents();self.w.size_canvas();self.assertTrue(self.w.rect().contains(d.geometry()))
 def test_divider_is_single_stationary_line_both_directions(self):
  c=self.w.canvas
  for width in (320,520,693):
   self.w.resize(width,2200);app.processEvents();self.w.size_canvas()
   y=round(3744*c.width()/3000)
   def band():
    im=c.grab().toImage();ratio=im.devicePixelRatio();x=round(20*ratio)
    return [im.pixelColor(x,row).rgba() for row in range(round((y-3)*ratio),round((y+3)*ratio))]
   reference=band()
   for kind in ('learning','work'):
    c.toggle_analytics();c.anim.pause()
    for ms in (0,105,210,315):c.anim.setCurrentTime(ms);app.processEvents();self.assertEqual(band(),reference)
    c.anim.resume();wait(150);self.assertEqual(c.kind,kind);self.assertEqual(band(),reference)
if __name__=='__main__':unittest.main(verbosity=2)
