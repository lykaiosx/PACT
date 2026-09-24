import os,sys,tempfile,unittest
from pathlib import Path
from datetime import datetime,date,timedelta
temp=tempfile.TemporaryDirectory();os.environ['PACT_DATA_DIR']=temp.name;os.environ['PACT_TOKEN_DIR']=temp.name+'/tokens';os.environ['QT_QPA_PLATFORM']='offscreen'
sys.path.insert(0,str(Path('app').resolve()))
from PySide6.QtWidgets import QApplication,QDialog
from PySide6.QtGui import QFontDatabase,QColor
from PySide6.QtCore import QRect,Qt
from app import PACT,ASSETS
from panels import Settings,intensity_level,ordered_colors,luminance,colors
from garmin_client import GarminBridge
app=QApplication([]);QFontDatabase.addApplicationFont(str(ASSETS/'fonts/Newsreader.ttf'))
class Revision(unittest.TestCase):
 def setUp(self):
  self.w=PACT(testing=True);self.s=self.w.storage
  for table in ('sessions','daily','kv'):self.s.conn.execute('DELETE FROM '+table)
  self.s.conn.commit();self.w.apply_theme();self.w.history_at=0;self.w.refresh()
 def tearDown(self):self.w.timer.stop();self.w.hover.stop();self.w.hide();self.w.deleteLater();app.processEvents();self.s.conn.close()
 def session(self,kind,start,hours):
  self.s.conn.execute('INSERT INTO sessions(kind,started_at,ended_at) VALUES(?,?,?)',(kind,start.isoformat(),(start+timedelta(hours=hours)).isoformat()));self.s.conn.commit()
 def test_learning_target_history_and_annual(self):
  self.session('learning',datetime.combine(date.today(),datetime.min.time()),2)
  self.session('work',datetime.combine(date.today(),datetime.min.time()),2)
  self.session('work',datetime(date.today().year-1,12,31,23),2)
  self.w.history_at=0;self.w.refresh()
  self.assertEqual(self.w.histories['learning'][-1][1],2);self.assertEqual(self.w.annual['work'],3)
  self.assertEqual(intensity_level(2,self.s.target('learning')),3);self.assertEqual(intensity_level(2,self.s.target('work')),0)
  self.s.set_setting('target_learning',4);self.assertEqual(intensity_level(2,self.s.target('learning')),1)
  self.w.canvas.toggle_analytics();self.assertEqual(self.w.canvas.kind,'learning');self.assertEqual(len(self.w.canvas.geo['monthly']),30)
 def test_settings_embedded_persistent_palette(self):
  self.w.settings();p=self.w.settings_panel;self.assertFalse(isinstance(p,QDialog));self.assertEqual(p.parent(),self.w)
  p.theme.setCurrentText('Custom');p.color_values['custom_background']='#f6f2e9';p.fields['learning'].setValue(3);p.fields['annual_work_goal'].setValue(1800);p.use_custom.setCurrentIndex(1)
  values=['#000000','#ffffff','#777777','#bbbbbb']
  for i,c in enumerate(values):p.color_values[f'level{i}']=c
  p.save();self.assertEqual(self.s.target('learning'),3);self.assertEqual(self.s.get_setting('annual_work_goal'),1800);self.assertEqual(colors(self.w)[0],'#f6f2e9')
  result=self.s.get_setting('intensity_colors');self.assertEqual(result,ordered_colors(values));self.assertEqual(result[0],'#ffffff');self.assertEqual(result[-1],'#000000');self.assertIsNotNone(self.w.settings_panel)
 def test_calories_zero_missing_and_persistence(self):
  class Client:
   calories=0
   def get_sleep_data(self,d):return {}
   def get_stats(self,d):return {'totalKilocalories':self.calories}
  bridge=GarminBridge();bridge.client=Client();self.assertEqual(bridge.today()['calories'],0);bridge.client.calories=2530;self.w.synced(bridge.today());self.assertEqual(self.s.day_extra('calories'),2530);bridge.client.calories=None;self.assertIsNone(bridge.today()['calories'])
 def test_responsive_docking(self):
  class Screen:
   def __init__(self,w,h):self.g=QRect(100,20,w,h)
   def availableGeometry(self):return self.g
  for width,height in [(1920,1040),(2560,1400),(1280,720)]:
   screen=Screen(width,height);self.w.fit_screen(screen);self.w.show();app.processEvents();self.w.size_canvas()
   self.assertEqual(self.w.geometry().right(),screen.g.right());self.assertEqual(self.w.geometry().bottom(),screen.g.bottom())
   if height>=994:self.assertLessEqual(self.w.canvas.height(),self.w.scroll.viewport().height());self.assertEqual(self.w.scroll.verticalScrollBarPolicy(),Qt.ScrollBarAlwaysOff)
   else:self.assertGreater(self.w.canvas.height(),height);self.assertEqual(self.w.scroll.verticalScrollBarPolicy(),Qt.ScrollBarAsNeeded)
 def test_sleep_mosaic_visible_gap(self):
  self.s.set_day_field('sleep_minutes',420)
  self.s.set_day_extra('sleep_stages',{'light':4,'deep':2,'rem':3,'awake':1});self.w.refresh();self.w.canvas.setFixedSize(3000,9314);im=self.w.canvas.grab().toImage();bg=QColor(colors(self.w)[0]);x=1928+round(547*.6)
  self.assertEqual(im.pixelColor(x,2700),bg);self.assertNotEqual(im.pixelColor(x-20,2700),bg);self.assertNotEqual(im.pixelColor(x+20,2700),bg)
if __name__=='__main__':unittest.main(verbosity=2)

