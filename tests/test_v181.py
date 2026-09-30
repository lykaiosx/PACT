import os,sys,tempfile,unittest,zipfile
from pathlib import Path
from datetime import date,timedelta
from unittest.mock import patch
temp=tempfile.TemporaryDirectory();os.environ['PACT_DATA_DIR']=temp.name;os.environ['PACT_TOKEN_DIR']=temp.name+'/tokens';os.environ['QT_QPA_PLATFORM']='offscreen';sys.path.insert(0,str(Path('app').resolve()))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QEvent
from app import PACT
from wrapped import make_slides,consistency_cells,animated_metric
app=QApplication([])
class ReportClarityTests(unittest.TestCase):
 def setUp(self):
  self.w=PACT(testing=True);self.w.timer.stop();self.w.hover.stop();self.s=self.w.storage
  for table in ('sessions','daily','kv','edit_history','time_edits','imported_totals'):self.s.conn.execute('DELETE FROM '+table)
  self.s.conn.commit()
 def tearDown(self):
  self.w.tray=None;self.w.hide();app.processEvents();self.w.deleteLater();app.sendPostedEvents(None,QEvent.DeferredDelete);self.s.conn.close()
 def test_meals_yes_no_unknown_reconcile_and_edit(self):
  for i in range(14):self.s.edit_manual(('breakfast','lunch','dinner')[i%3],1 if i<13 else 0,(date(2024,4,1)+timedelta(days=i//3)).isoformat())
  slides,_,r=make_slides(self.s,'Monthly',date(2024,4,1));meal=slides[6]
  self.assertEqual((r['meals'],r['meal_skipped'],r['meal_unknown']),(13,1,76));self.assertEqual(sum(r['meal_types']),13);self.assertEqual(meal['metric'],'13');self.assertIn('13 eaten · 1 marked as skipped',meal['detail']);self.assertIn('76 unrecorded',meal['detail']);self.assertEqual(r['meals']+r['meal_skipped']+r['meal_unknown'],90)
  self.s.edit_manual('lunch',1,'2024-04-05');slides,_,r=make_slides(self.s,'Monthly',date(2024,4,1));self.assertEqual((r['meals'],r['meal_skipped']),(14,0));self.assertEqual(slides[6]['metric'],'14')
 def test_empty_and_all_eaten_meals(self):
  slides,_,r=make_slides(self.s,'Monthly',date(2024,4,1));self.assertEqual(slides[6]['metric'],'—');self.assertEqual(r['meal_unknown'],90)
  for day in range(1,11):
   for kind in ('breakfast','lunch','dinner'):self.s.edit_manual(kind,1,f'2024-04-{day:02}')
  slides,_,r=make_slides(self.s,'Monthly',date(2024,4,1));self.assertEqual(slides[6]['metric'],'30');self.assertEqual(r['meal_entries'],30);self.assertEqual(r['meal_unknown'],60);self.assertEqual(sum(r['meal_types']),30)
 def test_grid_preserves_dates_and_centers_every_row(self):
  for count in (1,7,14,28,29,30,31):
   cells=consistency_cells(count);self.assertEqual(len(cells),count)
   for y in {r.y() for r in cells}:
    row=[r for r in cells if r.y()==y];self.assertAlmostEqual((row[0].left()+row[-1].right())/2,180)
  cells=consistency_cells(30);self.assertEqual(len({r.y() for r in cells}),5);self.assertEqual(len({r.x() for r in cells}),6)
 def test_explicit_png_selection_and_descriptive_archive_names(self):
  self.w.open_weekly_review();p=self.w.settings_panel;p.export_format.setCurrentIndex(1)
  with tempfile.TemporaryDirectory() as directory:
   target=Path(directory)/'report'
   with patch('wrapped.QFileDialog.getSaveFileName',return_value=(str(target),'PNG slides (*.zip)')) as dialog:p.choose_export()
   self.assertIn('.zip',dialog.call_args.args[2]);self.assertEqual(dialog.call_args.args[3],'PNG slides (*.zip)')
   with zipfile.ZipFile(str(target)+'.zip') as z:
    names=z.namelist();self.assertEqual(len(names),8);self.assertTrue(names[0].endswith('/Slide 01 - Overview.png'));self.assertTrue(names[3].endswith('/Slide 04 - Learning.png'));self.assertTrue(names[6].endswith('/Slide 07 - Meals.png'));self.assertEqual(len({Path(n).parent for n in names}),1)
   p.export_format.setCurrentIndex(0)
   with patch('wrapped.QFileDialog.getSaveFileName',return_value=(str(target),'PDF report (*.pdf)')):p.choose_export()
   self.assertTrue(Path(str(target)+'.pdf').read_bytes().startswith(b'%PDF'))
 def test_learning_has_distinct_graphic_and_duration_counter(self):
  self.s.conn.execute("INSERT INTO imported_totals VALUES('2024-04-01','learning',9660)");self.s.conn.commit();slides,_,_=make_slides(self.s,'Monthly',date(2024,4,1));self.assertEqual(slides[3]['graphic'],'book');self.assertNotEqual(slides[1]['graphic'],slides[3]['graphic']);self.assertEqual(animated_metric(slides[3],1),'2h 41m');self.assertIn('h',animated_metric(slides[3],.5))
if __name__=='__main__':unittest.main()
