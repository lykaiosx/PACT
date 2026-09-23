import xml.etree.ElementTree as E,json,hashlib,shutil
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QImage
app=QApplication([]);out=Path('app/assets')
for kind,title in [('work','Working'),('learning','Learning')]:
 source=Path(f'app/assets/{kind}-layout.svg')
 root=E.parse(source).getroot()
 for i,e in enumerate(root):e.set('id',f'e{i}')
 r=QSvgRenderer(E.tostring(root));boxes={};shapes={k:[] for k in ['annual','monthly','sleepweek','workweek','meals']}
 dynamic={4,5,31,32,33,34,35,36,38,40,42,44,45,46,47,48,49,50,51,52,57,58,86,87,535,536,547,550,553,556,546,549,552,555}
 for i,e in enumerate(list(root)):
  b=r.boundsOnElement(f'e{i}');x,y,w,h=[round(v,2) for v in (b.x(),b.y(),b.width(),b.height())];boxes[str(i)]=[x,y,w,h];key=None
  if e.tag.endswith('rect') or i==399:
   if 6000<y<8700 and 120<w<125 and 120<h<125:key='annual'
   elif 4780<y<5800 and 70<w<80 and x<2500:key='monthly'
   elif 2050<y<2060 and x>1900:key='sleepweek'
   elif 4240<y<4280 and x>1800:key='workweek'
   elif 3500<y<3660 and 120<w<125:key='meals'
  if key:shapes[key].append([x,y,w,h]);dynamic.add(i)
  if i in dynamic:root.remove(e)
 for k in shapes:shapes[k]=sorted([list(v) for v in set(tuple(v) for v in shapes[k])],key=lambda v:(v[1],v[0]) if k=='annual' else (v[0],v[1]))
 shapes['boxes']=boxes;shapes['width']=r.defaultSize().width();shapes['height']=9314
 (out/f'{kind}-static.svg').write_bytes(E.tostring(root));(out/f'{kind}-geometry.json').write_text(json.dumps(shapes))
 print(kind,{k:len(v) for k,v in shapes.items() if isinstance(v,list)})
records=[]
for p in Path('design-assets/learning').rglob('*'):
 if not p.is_file():continue
 row={'path':str(p.relative_to('design-assets/learning')),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
 if p.suffix.lower()=='.png':im=QImage(str(p));row.update(valid=not im.isNull(),width=im.width(),height=im.height())
 elif p.suffix.lower()=='.svg':r=QSvgRenderer(str(p));row.update(valid=r.isValid(),width=r.defaultSize().width(),height=r.defaultSize().height())
 records.append(row)
Path('new-asset-inventory.json').write_text(json.dumps(records,indent=2));print('Learning assets:',len(records),'invalid:',sum(not r.get('valid',True) for r in records))

