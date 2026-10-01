import os,sys,tempfile,unittest
from pathlib import Path
from datetime import date
temp=tempfile.TemporaryDirectory();os.environ['PACT_DATA_DIR']=temp.name;os.environ['PACT_TOKEN_DIR']=temp.name+'/tokens';os.environ['QT_QPA_PLATFORM']='offscreen';sys.path.insert(0,str(Path('app').resolve()))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt,QEvent,QPoint,QPointF
from PySide6.QtGui import QMouseEvent
from app import PACT
from backup import create_backup,restore_backup
from floating_widget import snapshot
app=QApplication([])
class WidgetTests(unittest.TestCase):
 def setUp(self):
  self.w=PACT(testing=True);self.s=self.w.storage;self.w.timer.stop();self.w.hover.stop()
  for table in ('sessions','daily','kv','edit_history','time_edits','imported_totals'):self.s.conn.execute('DELETE FROM '+table)
  self.s.conn.commit();self.w.refresh()
 def tearDown(self):
  if self.w.floating_widget:self.w.floating_widget.hide()
  self.w.hide();app.processEvents();self.w.deleteLater();app.sendPostedEvents(None,QEvent.DeferredDelete);self.s.conn.close()
 def test_widget_independent_of_sidebar_and_not_topmost(self):
  self.w.set_widget_enabled(True);widget=self.w.floating_widget;self.w.show();self.w.hide();self.assertTrue(widget.isVisible());self.assertFalse(widget.windowFlags()&Qt.WindowStaysOnTopHint);self.w.set_widget_enabled(False);self.assertFalse(widget.isVisible());self.assertFalse(self.s.get_setting('widget_enabled'))
 def test_live_totals_and_missing_manual_values(self):
  self.s.set_setting('widget_stats',['work','steps','meals','creatives']);self.s.conn.execute('INSERT INTO imported_totals VALUES(?,?,?)',(date.today().isoformat(),'work',9660));self.s.conn.commit();self.w.refresh();rows=snapshot(self.w);self.assertEqual(rows[0][1],'02:41:00');self.assertEqual(rows[1][1],'—');self.assertEqual(rows[2][1],'—');self.assertEqual(rows[3][1],'—')
  self.s.edit_manual('breakfast',1);self.s.edit_manual('lunch',0);self.s.edit_manual('creatives',3);self.s.set_day_field('steps',506);self.w.refresh();rows=snapshot(self.w);self.assertEqual(rows[1][1],'506');self.assertEqual(rows[2][1],'1 eaten');self.assertEqual(rows[2][2],'1 unrecorded');self.assertEqual(rows[3][1],'3')
 def test_drag_saves_position_and_lock_prevents_movement(self):
  self.w.set_widget_enabled(True);widget=self.w.floating_widget;widget.move(50,50)
  def event(kind,x,y,buttons):return QMouseEvent(kind,QPointF(20,20),QPointF(x,y),Qt.LeftButton,buttons,Qt.NoModifier)
  widget.mousePressEvent(event(QEvent.MouseButtonPress,70,70,Qt.LeftButton));widget.mouseMoveEvent(event(QEvent.MouseMove,110,110,Qt.LeftButton));widget.mouseReleaseEvent(event(QEvent.MouseButtonRelease,110,110,Qt.NoButton));self.assertEqual(self.s.get_setting('widget_position'),[90,90]);widget.set_locked(True);widget.mousePressEvent(event(QEvent.MouseButtonPress,110,110,Qt.LeftButton));widget.mouseMoveEvent(event(QEvent.MouseMove,150,150,Qt.LeftButton));self.assertEqual(widget.pos(),QPoint(90,90))
 def test_backup_restores_widget_preferences(self):
  prefs={'widget_enabled':True,'widget_locked':True,'widget_stats':['work','learning','meals'],'widget_scale':125,'widget_opacity':65,'widget_position':[90,120]}
  for key,value in prefs.items():self.s.set_setting(key,value)
  target=Path(temp.name)/'widget.pact';create_backup(self.s,target);self.s.set_setting('widget_stats',[]);self.s.set_setting('widget_enabled',False);restore_backup(self.s,target)
  for key,value in prefs.items():self.assertEqual(self.s.get_setting(key),value)
  self.w.update_widget();self.assertTrue(self.w.floating_widget.isVisible());self.assertAlmostEqual(self.w.floating_widget.windowOpacity(),.65,places=2)
 def test_offscreen_position_and_all_stats_fit_screen(self):
  self.s.set_setting('widget_position',[-90000,90000]);self.s.set_setting('widget_scale',150);self.s.set_setting('widget_stats',['work','learning','sleep','steps','meals','creatives']);self.w.set_widget_enabled(True);widget=self.w.floating_widget;self.assertTrue(app.primaryScreen().availableGeometry().contains(widget.geometry()));self.assertEqual(len(widget.rows),6)
 def test_settings_options_are_live_and_theme_applies(self):
  self.w.settings();panel=self.w.settings_panel;panel.widget_enabled.setChecked(True);widget=self.w.floating_widget;old_width=widget.width();panel.widget_size.setValue(130);self.assertGreater(widget.width(),old_width);panel.widget_opacity.setValue(70);self.assertAlmostEqual(widget.windowOpacity(),.7,places=2);panel.widget_options['meals'].setChecked(True);self.assertTrue(any(row[0]=='Meals' for row in widget.rows));panel.theme.setCurrentText('Dark');self.assertEqual(widget.grab().toImage().pixelColor(5,5).name(),'#24191d')
if __name__=='__main__':unittest.main()
