import xml.etree.ElementTree as E,json,hashlib
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QImage
app=QApplication([])
root=E.parse('app/assets/layout.svg').getroot()
for i,e in enumerate(root): e.set('id',f'e{i}')
r=QSvgRenderer(E.tostring(root));dynamic=set([4,5,28,29,30,31,32,33,42,43,44,45,46,47,48,49,51,52,53,526,527,538,541,544,547])
shapes={'annual':[],'monthly':[],'sleepweek':[],'workweek':[],'meals':[]}
for i,e in enumerate(list(root)):
 b=r.boundsOnElement(f'e{i}');x,y,w,h=b.x(),b.y(),b.width(),b.height()
 key=None
 if 5900<y<8550 and w<130 and h<130:key='annual'
 elif 4670<y<5650 and 70<w<80 and x<2500:key='monthly'
 elif 2050<y<2060 and x>1900:key='sleepweek'
 elif 4130<y<4140 and x>1800:key='workweek'
 elif 3380<y<3390:key='meals'
 if key:
  shapes[key].append([round(v,2) for v in (x,y,w,h)]);dynamic.add(i)
 if i in dynamic:root.remove(e)
for k in shapes:shapes[k]=sorted([list(v) for v in set(tuple(v) for v in shapes[k])],key=lambda v:(v[1],v[0]) if k=='annual' else (v[0],v[1]))
Path('app/assets/static.svg').write_bytes(E.tostring(root))
Path('app/assets/geometry.json').write_text(json.dumps(shapes,indent=2))
records=[]
for p in Path('design-assets').rglob('*'):
 if not p.is_file():continue
 entry={'path':str(p.relative_to('design-assets')),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 if p.suffix=='.png':
  im=QImage(str(p));entry.update(width=im.width(),height=im.height(),valid=not im.isNull())
 elif p.suffix=='.svg':
  sr=QSvgRenderer(str(p));entry.update(valid=sr.isValid(),width=sr.defaultSize().width(),height=sr.defaultSize().height())
 records.append(entry)
Path('asset-inventory.json').write_text(json.dumps(records,indent=2))
print({k:len(v) for k,v in shapes.items()});print('Inspected',len(records),'assets; invalid:',[r['path'] for r in records if not r['valid']])

