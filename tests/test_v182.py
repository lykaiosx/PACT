import os,sys,unittest
from pathlib import Path
from types import SimpleNamespace
os.environ['QT_QPA_PLATFORM']='offscreen';sys.path.insert(0,str(Path('app').resolve()))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage,QPainter,QColor
from wrapped import StoryCanvas
app=QApplication([])
class PageTurnContinuity(unittest.TestCase):
 def render(self,t,bg,ink):
  canvas=StoryCanvas(SimpleNamespace(content_elapsed=3.4));image=QImage(720,1200,QImage.Format_RGB32);image.fill(QColor(bg));painter=QPainter(image);painter.setRenderHint(QPainter.Antialiasing);painter.scale(2,2)
  slide=dict(tag='ROOM TO GROW',title='You kept\nyour curiosity.',metric='2h 41m',number=9660,duration=True,unit='of recorded learning',graphic='book',values=[9660],note='1 day recorded',detail='One page, one session, one thing learned.')
  canvas.draw(painter,slide,t,bg,ink);painter.end();return image.copy(40,584,640,380)
 def test_final_frame_has_no_graphic_swap_in_all_themes(self):
  for bg,ink in [('#fafafa','#100404'),('#24191d','#fafafa'),('#e2f1e5','#183527')]:
   # OutCubic progress for the frame 1/30 second before a 3.4-second finish.
   before=self.render(1-((1/30)/3.4)**3,bg,ink);after=self.render(1,bg,ink)
   changed=sum(a!=b for a,b in zip(bytes(before.constBits()),bytes(after.constBits())))
   self.assertLess(changed,100,'The final frame must not replace the page or its writing.')
 def test_page_still_moves_during_the_animation(self):
  first=self.render(.2,'#fafafa','#100404');middle=self.render(.6,'#fafafa','#100404');last=self.render(1,'#fafafa','#100404')
  self.assertNotEqual(bytes(first.constBits()),bytes(middle.constBits()));self.assertNotEqual(bytes(middle.constBits()),bytes(last.constBits()))
if __name__=='__main__':unittest.main()
