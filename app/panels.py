"""Design-derived dashboard and in-panel settings."""
import json, math
from pathlib import Path
from datetime import date,datetime,timedelta
from PySide6.QtCore import Qt,QRectF,QPoint,QPropertyAnimation,QEasingCurve,QParallelAnimationGroup,QSize,QTimer
from PySide6.QtGui import QColor,QPainter,QPen,QFont,QIcon,QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (QWidget,QPushButton,QInputDialog,QToolTip,QVBoxLayout,QFormLayout,QLabel,QComboBox,QDoubleSpinBox,QLineEdit,QScrollArea,QColorDialog,QHBoxLayout,QFileDialog)
ASSETS=Path(__file__).resolve().parent/'assets'
LIGHT='#FAFAFA';DARK='#100404'
SOFT_DARK='#24191D'
def luminance(value):
 c=QColor(value);v=[c.redF(),c.greenF(),c.blueF()];v=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in v];return sum(a*b for a,b in zip(v,[.2126,.7152,.0722]))
def ordered_colors(values):
 if len(values)!=4 or not all(QColor(v).isValid() for v in values):raise ValueError('Choose four valid colors')
 return sorted([QColor(v).name() for v in values],key=luminance,reverse=True)
def intensity_level(hours,target):
 if hours<=0:return -1
 return 3 if hours>=target else 2 if hours>=target*.75 else 1 if hours>=target*.5 else 0
def colors(window):
 s=window.storage;theme=s.get_setting('theme','light');bg,fg=(SOFT_DARK,'#F1E9E5') if theme=='dark' else (DARK,LIGHT) if theme=='high contrast' else (LIGHT,DARK)
 if theme=='custom':bg=s.get_setting('custom_background',LIGHT);fg=s.get_setting('custom_ink',DARK)
 for v in (bg,fg):
  if not QColor(v).isValid():return LIGHT,DARK
 return bg,fg
def intensity_colors(window):
 saved=window.storage.get_setting('intensity_colors')
 if saved:
  try:return ordered_colors(saved)
  except (ValueError,TypeError):pass
 bg,fg=map(QColor,colors(window));result=[]
 for a in (.25,.5,.75,1):result.append(QColor(*[round((1-a)*b+a*f) for b,f in zip(bg.getRgb()[:3],fg.getRgb()[:3])]).name())
 return ordered_colors(result)
def svg_colors(raw,window):
 import re
 bg,fg=colors(window);inks=intensity_colors(window)
 mapping={'#fafafa':bg,'#100404':fg,'black':fg,'white':bg,'#4b4242':inks[2],'#857f7f':inks[1]}
 return re.sub(r'(fill|stroke)="([^"]+)"',lambda m:f'{m[1]}="{mapping.get(m[2].lower(),m[2])}"',raw)
def gear_icon(ink):
 pix=QPixmap(64,64);pix.fill(Qt.transparent);p=QPainter(pix);p.setRenderHint(QPainter.Antialiasing);p.setPen(QPen(QColor(ink),4));p.setBrush(Qt.NoBrush);p.drawEllipse(15,15,34,34);p.drawEllipse(25,25,14,14)
 for i in range(8):
  a=i*math.pi/4;p.drawLine(QPoint(round(32+18*math.cos(a)),round(32+18*math.sin(a))),QPoint(round(32+26*math.cos(a)),round(32+26*math.sin(a))))
 p.end();return QIcon(pix)
class HoverDetails(QLabel):
 """One non-activating, mouse-transparent child; no native tooltip windows."""
 def __init__(self,window):
  super().__init__(window);self.window=window;self.setAttribute(Qt.WA_TransparentForMouseEvents);self.setTextFormat(Qt.PlainText);self.setWordWrap(False);self.hide();self.pending='';self.anchor=QPoint();self.delay=QTimer(self);self.delay.setSingleShot(True);self.delay.timeout.connect(self.present);self.dismiss=QTimer(self);self.dismiss.setSingleShot(True);self.dismiss.timeout.connect(self.clear_details)
 def offer(self,text,global_pos):
  if not text:
   self.delay.stop();self.pending=''
   if not self.dismiss.isActive():self.dismiss.start(120)
   return
  self.dismiss.stop()
  if text==self.pending and (self.isVisible() or self.delay.isActive()):return
  self.pending=text;self.anchor=self.window.mapFromGlobal(global_pos)
  if self.isVisible():self.present()
  else:self.delay.start(110)
 def present(self):
  if not self.pending or self.window.settings_panel or not self.window.isVisible():return
  bg,fg=colors(self.window);self.setStyleSheet(f'QLabel{{background:{bg};color:{fg};border:1px solid {fg};border-radius:0;padding:9px 12px;font-family:Newsreader;font-size:14px;}}');self.setText(self.pending);self.adjustSize()
  x=max(8,min(self.anchor.x()+14,self.window.width()-self.width()-8));y=self.anchor.y()+20
  if y+self.height()>self.window.height()-8:y=self.anchor.y()-self.height()-16
  self.move(x,max(8,y));self.raise_();self.show()
 def clear_details(self):self.delay.stop();self.dismiss.stop();self.pending='';self.hide()
class Settings(QWidget):
 def __init__(self,window):
  super().__init__(window);self.window=window;self.fields={};self.setAttribute(Qt.WA_OpaquePaintEvent);self.setAutoFillBackground(True);root=QVBoxLayout(self);root.setContentsMargins(16,18,16,36);self.setStyleSheet('QWidget{font-size:14px;}')
  head=QHBoxLayout();back=QPushButton('‹');back.setAccessibleName('Back to dashboard');back.clicked.connect(window.close_settings);head.addWidget(back);head.addWidget(QLabel('Settings'),1);root.addLayout(head)
  self.saved_note=QLabel('Changes save automatically.');self.saved_note.setWordWrap(True);root.addWidget(self.saved_note)
  scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setFrameShape(QScrollArea.NoFrame);body=QWidget();form=QFormLayout(body);form.setVerticalSpacing(8);scroll.setWidget(body);root.addWidget(scroll)
  def section(title):
   label=QLabel(title);label.setStyleSheet('font-weight:bold;font-size:20px;padding-top:10px;');form.addRow(label)
  section('Garmin connection');self.state=QLabel(window.garmin_status);self.state.setWordWrap(True);form.addRow(self.state)
  self.email=QLineEdit();self.email.setPlaceholderText('Email');self.password=QLineEdit();self.password.setPlaceholderText('Password');self.password.setEchoMode(QLineEdit.Password);form.addRow(self.email);form.addRow(self.password)
  connect=QPushButton('Connect Garmin');connect.clicked.connect(self.connect);sync=QPushButton('Sync now');sync.clicked.connect(window.sync);form.addRow(connect,sync)
  schedule=QLabel('Checks Garmin every 5 minutes. Hydration and its goal come from Garmin; update them on your watch or in Garmin Connect.');schedule.setWordWrap(True);form.addRow(schedule)
  self.code=QLineEdit();self.code.setPlaceholderText('Verification code');self.code.hide();self.verify=QPushButton('Verify');self.verify.clicked.connect(self.submit_code);self.verify.hide();form.addRow(self.code,self.verify)
  section('Appearance');self.theme=QComboBox();self.theme.addItems(['Light','Dark','High Contrast','Custom']);self.theme.setCurrentText(window.storage.get_setting('theme','light').title());form.addRow('Theme',self.theme)
  self.color_values={};self.color_buttons={}
  for key,label,default in [('custom_background','Background',LIGHT),('custom_ink','Text and lines',DARK)]:
   self.add_color(form,key,label,window.storage.get_setting(key,default))
  self.use_custom=QComboBox();self.use_custom.addItems(['Theme default','Custom colors']);self.use_custom.setCurrentIndex(int(bool(window.storage.get_setting('intensity_colors'))));form.addRow('Chart palette',self.use_custom)
  for i,c in enumerate(intensity_colors(window)):self.add_color(form,f'level{i}',f'Intensity {i+1}',c)
  hint=QLabel('Custom intensity colors are ordered from lightest to darkest. Darker means more progress.');hint.setWordWrap(True);form.addRow(hint)
  section('Customization')
  for key,label,default,maximum,suffix in [('target_work','Work target',8,24,' h'),('target_learning','Learning target',2,24,' h'),('target_sleep','Sleep target',8,24,' h'),('annual_work_goal','Annual work',2000,8784,' h'),('annual_learning_goal','Annual learning',730,8784,' h')]:
   f=QDoubleSpinBox();f.setRange(.25 if key.startswith('target') else 1,maximum);f.setSingleStep(.25 if key.startswith('target') else 1);f.setDecimals(2 if key.startswith('target') else 0);f.setSuffix(suffix);f.setValue(window.storage.get_setting(key,default));self.fields[key.replace('target_','')]=f;form.addRow(label,f)
  section('Data export');export=QPushButton('Export daily totals (.csv)');export.clicked.connect(lambda:self.export(False));form.addRow(export);all_data=QPushButton('Export all records (.zip)');all_data.clicked.connect(lambda:self.export(True));form.addRow(all_data)
  description=QLabel('CSV opens in Excel or Google Sheets. Daily totals cover midnight to midnight. All records also includes hourly timers, sessions and Garmin observations.');description.setWordWrap(True);form.addRow(description);self.export_status=QLabel('');self.export_status.setWordWrap(True);form.addRow(self.export_status)
  self.theme.currentIndexChanged.connect(self.save);self.use_custom.currentIndexChanged.connect(self.save)
  for field in self.fields.values():field.setKeyboardTracking(False);field.valueChanged.connect(self.save);field.editingFinished.connect(self.save)
 def paintEvent(self,event):
  p=QPainter(self);p.fillRect(self.rect(),QColor(colors(self.window)[0]));p.end()
 def export(self,full):
  from data_export import export_data
  suffix='zip' if full else 'csv';path,_=QFileDialog.getSaveFileName(self,'Export PACT data',str(Path.home()/'Documents'/f'PACT_{date.today().isoformat()}.{suffix}'),'ZIP archive (*.zip)' if full else 'CSV spreadsheet (*.csv)')
  if not path:return
  if not path.lower().endswith('.'+suffix):path+='.'+suffix
  try:
   count=export_data(self.window.storage,path,full);self.export_status.setText(f'Exported {count} days to {Path(path).name}.')
  except (OSError,ValueError):self.export_status.setText('Could not save this file. Choose a writable folder and close the file in Excel, then retry.')
 def add_color(self,form,key,label,value):
  self.color_values[key]=value;b=QPushButton(value);self.color_buttons[key]=b;b.clicked.connect(lambda:self.choose(key));form.addRow(label,b)
 def choose(self,key):
  c=QColorDialog.getColor(QColor(self.color_values[key]),self,'Choose color')
  if c.isValid():self.color_values[key]=c.name();self.color_buttons[key].setText(c.name());self.theme.setCurrentText('Custom') if key.startswith('custom_') else self.use_custom.setCurrentIndex(1);self.save()
 def connect(self):
  if self.email.text().strip() and self.password.text():self.window.sync(self.email.text().strip(),self.password.text());self.password.clear()
 def submit_code(self):
  if self.window.job:self.window.job.answer=self.code.text().strip();self.window.job.event.set();self.code.clear();self.code.hide();self.verify.hide()
 def save(self,*args):
  s=self.window.storage
  for key,f in self.fields.items():s.set_setting('target_'+key if key in ('work','learning','sleep') else key,f.value())
  s.set_setting('theme',self.theme.currentText().lower())
  for key in ('custom_background','custom_ink'):s.set_setting(key,self.color_values[key])
  s.set_setting('intensity_colors',ordered_colors([self.color_values[f'level{i}'] for i in range(4)]) if self.use_custom.currentIndex() else None)
  self.window.apply_theme();self.window.refresh();self.saved_note.setText('All changes saved automatically.')
 def flush(self):
  for field in self.fields.values():field.interpretText()
  self.save()
class Canvas(QWidget):
 def __init__(self,window):
  super().__init__();self.window=window;self.kind='work';self.setMouseTracking(True);self.renderer=QSvgRenderer();self.controls=[];self.anim=None;self.slide_image=None;self.load_design()
  for text,box,callback,name in [('Start',self.box(53),lambda:window.toggle_timer('work'),'Work timer'),('Start',self.box(56),lambda:window.toggle_timer('learning'),'Learning timer'),('',self.box(54),window.hide,'Hide PACT'),('',(2530,125,150,122),window.settings,'Settings'),('',self.box(401),self.creatives,'Creatives'),('',(900,2660,289,122),self.water,'Cups of water'),('',self.box(55),self.toggle_analytics,'Show Learning Analytics')]:
   b=QPushButton(text,self);b.setAccessibleName(name);b.clicked.connect(callback);b.setCursor(Qt.PointingHandCursor);self.controls.append((b,box))
  self.controls[5][0].hide();self.controls[5][0].setEnabled(False)
  for i,box in enumerate(self.geo['meals']):
   b=QPushButton('',self);b.setAccessibleName(['Breakfast','Lunch','Dinner'][i]);b.clicked.connect(lambda checked=False,n=i:self.meal(n));self.controls.append((b,box))
  self.details=HoverDetails(window);self.retheme()
 def box(self,i):return self.geo['boxes'][str(i)]
 def load_design(self):
  self.geo=json.loads((ASSETS/f'{self.kind}-geometry.json').read_text());self.raw=(ASSETS/f'{self.kind}-static.svg').read_text()
 def toggle_analytics(self):
  if self.anim and self.anim.state()==QPropertyAnimation.Running:return
  self.details.clear_details()
  top=round(3739*self.width()/self.geo['width']);old=self.grab();self.kind='learning' if self.kind=='work' else 'work';self.load_design();self.retheme();self.window.refresh();new=self.grab()
  self.controls[6][0].setAccessibleName('Show Work Analytics' if self.kind=='learning' else 'Show Learning Analytics')
  direction=1 if self.kind=='learning' else -1;self.anim=QParallelAnimationGroup(self);self.slide_layers=[]
  for pix,start,end in [(old,0,-direction*self.width()),(new,direction*self.width(),0)]:
   layer=QLabel(self);layer.setAttribute(Qt.WA_OpaquePaintEvent);ratio=pix.devicePixelRatio();crop=pix.copy(0,round(top*ratio),pix.width(),pix.height()-round(top*ratio));layer.setPixmap(crop);layer.setGeometry(start,top,self.width(),self.height()-top);layer.show();layer.raise_();self.slide_layers.append(layer)
   animation=QPropertyAnimation(layer,b'pos',self.anim);animation.setDuration(420);animation.setStartValue(QPoint(start,top));animation.setEndValue(QPoint(end,top));animation.setEasingCurve(QEasingCurve.InOutCubic);self.anim.addAnimation(animation)
  self.anim.finished.connect(self.finish_slide);self.anim.start()
 def finish_slide(self):
  for layer in self.slide_layers:layer.deleteLater()
  self.slide_layers=[];self.update()
 def retheme(self):
  self.renderer.load(svg_colors(self.raw,self.window).encode());self.resize_controls();self.update()
  if hasattr(self,'details'):self.details.clear_details()
 def resize_controls(self):
  scale=self.width()/self.geo['width'];bg,fg=colors(self.window)
  for i,(b,box) in enumerate(self.controls):
   if i in (0,1,2,4,6):box=self.box({0:53,1:56,2:54,4:401,6:55}[i])
   elif i>=7:box=self.geo['meals'][i-7]
   b.setGeometry(*(round(v*scale) for v in box));b.setStyleSheet(f'background:{fg if i<2 else "transparent"};color:{bg if i<2 else fg};border:0;padding:0;font-family:Newsreader;font-size:{max(9,round(75*scale))}px;')
   if i==3:b.setIcon(gear_icon(fg));b.setIconSize(b.size())
   if i==6:
    # Cover the original right arrow and draw the actual navigation direction.
    b.setStyleSheet(f'background:{fg};border:0;padding:0;');pix=QPixmap(64,64);pix.fill(Qt.transparent);p=QPainter(pix);p.setPen(QPen(QColor(bg),3));p.setRenderHint(QPainter.Antialiasing);points=[QPoint(38,16),QPoint(23,32),QPoint(38,48)] if self.kind=='learning' else [QPoint(26,16),QPoint(41,32),QPoint(26,48)];p.drawPolyline(points);p.end();b.setIcon(QIcon(pix));b.setIconSize(b.size())
 def resizeEvent(self,e):self.resize_controls();super().resizeEvent(e)
 def creatives(self):
  s=self.window.storage;v,ok=QInputDialog.getInt(self,'Creatives','Completed today',s.get_day()['creatives'],0,999)
  if ok:s.set_day_field('creatives',v);self.window.refresh()
 def water(self):
  pass # Hydration is read-only Garmin data; retained callback slot for control indexing.
 def meal(self,n):
  s=self.window.storage;k=('breakfast','lunch','dinner')[n];s.set_day_field(k,not s.get_day()[k]);self.window.refresh()
 def stage_regions(self):
  stages=self.window.storage.day_extra('sleep_stages',{}) or {};total=sum(stages.values());x,y,_,_=self.box(547);size=547;gap=12;regions=[]
  if not total:return regions
  left=stages.get('light',0)+stages.get('deep',0);split=size*left/total
  for cx,cw,a,b,la,lb in [(x,split,'light','deep',2,3),(x+split,size-split,'rem','awake',1,0)]:
   subtotal=stages.get(a,0)+stages.get(b,0)
   if not subtotal:continue
   top=size*stages.get(a,0)/subtotal
   for cy,ch,stage,level in [(y,top,a,la),(y+top,size-top,b,lb)]:
    if cw>gap and ch>gap:regions.append(((cx+gap/2,cy+gap/2,cw-gap,ch-gap),stage,stages.get(stage,0),level))
  return regions
 @staticmethod
 def duration(seconds):
  h,r=divmod(max(0,int(seconds)),3600);m,s=divmod(r,60);return f'{h}h {m:02}m {s:02}s'
 def day_tip(self,d,kind,value):
  s=self.window.storage;creatives=s.existing_day(d.isoformat()).get('creatives',0);duration='Not available' if value is None else self.duration(value*3600)
  return f'{d.day} {d:%B %Y}\n{kind.title()}: {duration}\nCreatives: {creatives}'
 def tooltip_at(self,pos):
  s=self.window.storage;vals=self.window.histories[self.kind]
  for key,count in [('annual',360),('workweek',7),('monthly',30)]:
   for idx,box in enumerate(self.geo[key]):
    d,v=vals[-count:][idx]
    if key=='monthly':
     if v<=0:continue
     x,_,w,_=box;h=970*min(1,v/s.target(self.kind));box=(x,self.box(533)[1]-9-h,w,h)
    if QRectF(*box).contains(pos):
     if not s.has_activity_record(self.kind,d.isoformat()):return '' if key=='monthly' else f'{d.day} {d:%B %Y}\nNot available'
     return self.day_tip(d,self.kind,v)
  for i,box in enumerate(self.geo['sleepweek']):
   if QRectF(*box).contains(pos):
    d=date.today()-timedelta(days=6-i);mins=s.existing_day(d.isoformat()).get('sleep_minutes');return f'{d.day} {d:%B %Y}\nNot available' if mins is None else self.day_tip(d,'sleep',mins/60)
  for box,stage,seconds,level in self.stage_regions():
   if QRectF(*box).contains(pos):return self.day_tip(date.today(),{'light':'Light sleep','deep':'Deep sleep','rem':'REM sleep','awake':'Awake'}[stage],seconds/3600)
  if QRectF(1928,2455,1000,125).contains(pos):
   score=s.day_extra('sleep_score');mins=self.window.day.get('sleep_minutes');return '' if score is None and mins is None else self.day_tip(date.today(),'sleep',None if mins is None else mins/60)+f'\nSleep score: {score if score is not None else "Not available"}'
  return ''
 def paintEvent(self,event):
  p=QPainter(self);p.setRenderHint(QPainter.Antialiasing);p.scale(self.width()/self.geo['width'],self.width()/self.geo['width']);p.fillRect(QRectF(0,0,self.geo['width'],9314),QColor(colors(self.window)[0]));self.renderer.render(p,QRectF(0,0,self.geo['width'],9314));s=self.window.storage;day=self.window.day;bg,fg=colors(self.window);inks=intensity_colors(self.window)
  def text(x,y,w,h,value,size=75,bold=False,right=False,center=False,italic=False):
   p.setPen(QColor(fg));f=QFont('Newsreader');f.setPixelSize(round(size));f.setBold(bold);f.setItalic(italic);p.setFont(f);p.drawText(QRectF(x,y,w,h),Qt.AlignVCenter|(Qt.AlignHCenter if center else Qt.AlignRight if right else Qt.AlignLeft),str(value))
  def field(i,value,size=75,bold=False,width=None):
   x,y,w,h=self.box(i)
   if width:x=x+w-width;w=width
   text(x,y-24,w,h+48,value,size,bold,right=True)
  def fill(box,level,border=True):
   p.fillRect(QRectF(*box),QColor(bg if level<0 else inks[min(3,level)]))
   if border:p.setPen(QPen(QColor(fg),3));p.setBrush(Qt.NoBrush);p.drawRect(QRectF(*box))
  def bar(box,ratio):
   x,y,w,h=box;p.fillRect(QRectF(x,y,w*max(0,min(1,ratio)),h),QColor(inks[max(0,intensity_level(ratio,1))]))
  now=datetime.now();text(52,339,1900,120,now.strftime('%A, %d %B'));text(2300,339,640,120,now.strftime('%I:%M %p').lstrip('0'),right=True)
  for kind,i,j in [('work',31,527),('learning',32,528)]:
   seconds=self.window.seconds[kind];h,r=divmod(max(0,int(seconds)),3600);m,sec=divmod(r,60);x,y,_,_=self.box(i);text(x,y-26,1400,132,f'{h:02}:{m:02}:{sec:02}',100,True);text(1700,y-10,890,100,f'{seconds/3600:.1f} / {s.target(kind):g}h',65,right=True);bar(self.box(j),seconds/3600/s.target(kind))
  mins=day.get('sleep_minutes');text(54,1910,600,132,'—' if mins is None else f'{mins//60:02}:{mins%60:02}',100,True);text(650,1920,540,100,f'/ {s.target("sleep"):g}h',65,right=True);bar(self.box(529),(mins or 0)/60/s.target('sleep'))
  for i,value in [(34,'—' if day.get('resting_hr') is None else f'{day["resting_hr"]}BPM'),(35,'—' if day.get('steps') is None else f'{day["steps"]:,}'),(45,self.hydration_text()),(46,s.day_extra('body_battery')),(47,None if s.day_extra('calories') is None else f'{s.day_extra("calories"):,.0f}'),(36,s.day_extra('sleep_score'))]:field(i,'—' if value is None else value,75,True,width=425 if i!=36 else 235)
  x,y,w,h=self.box(401);text(x,y,w,h,day['creatives'],75,center=True)
  for i,box in enumerate(self.geo['meals']):fill(box,3 if day[('breakfast','lunch','dinner')[i]] else -1)
  vals=self.window.histories[self.kind];week=[v for _,v in vals[-7:]];target=s.target(self.kind)
  for i,v in [(49,sum(week)/7),(51,max(week)),(50,min(week))]:field(i,f'{v:.1f}h'+('/day' if i==49 else ''),75,width=500)
  for i,box in enumerate(self.geo['sleepweek']):
   d=(date.today()-timedelta(days=6-i)).isoformat();m=s.existing_day(d).get('sleep_minutes');fill(box,intensity_level((m or 0)/60,s.target('sleep')))
  for (_,v),box in zip(vals[-7:],self.geo['workweek']):fill(box,intensity_level(v,target))
  baseline=self.box(533)[1]-9
  for (_,v),box in zip(vals[-30:],self.geo['monthly']):
   x,_,w,_=box;h=970*min(1,v/target)
   if h:fill((x,baseline-h,w,h),intensity_level(v,target),False)
  for (_,v),box in zip(vals[-360:],self.geo['annual']):fill(box,intensity_level(v,target))
  for n,(i,j) in enumerate([(38,546),(40,549),(42,552),(44,555)]):
   fill(self.box(j),3-n,False);x,y,_,_=self.box(j);x=self.box(546)[0];text(x+130,y-7,90,89,'≥' if n<3 else '<',70,italic=True);text(x+220,y-7,220,89,f'{target*(1 if n==0 else .75 if n==1 else .5):g}hr',70,True,italic=True)
  regions=self.stage_regions()
  if regions:
   for box,stage,seconds,level in regions:fill(box,level,False)
  else:
   x,y,_,_=self.box(547);text(x,y,547,547,'—',90,center=True)
  for i,l in [(545,3),(548,2),(551,1),(554,0)]:fill(self.box(i),l,False)
  annual=self.window.annual[self.kind];goal=s.get_setting('annual_'+self.kind+'_goal',2000 if self.kind=='work' else 730);bar(self.box(84),annual/max(1,goal));x,y,w,h=self.box(84);text(x+1000,y-110,w-1000,100,f'{annual:,.1f} / {goal:,.0f}h',65,right=True)
  start=datetime(now.year,1,1);end=datetime(now.year+1,1,1);progress=(now-start).total_seconds()/(end-start).total_seconds();bar(self.box(85),progress);x,y,w,h=self.box(85);text(x+1000,y-110,w-1000,100,f'{progress:.1%}',65,right=True);p.end()
 def mouseMoveEvent(self,e):
  pos=e.position()*(self.geo['width']/self.width());tip=self.tooltip_at(pos)
  self.details.offer(tip,e.globalPosition().toPoint())
  super().mouseMoveEvent(e)
 def leaveEvent(self,e):self.details.offer('',QPoint());super().leaveEvent(e)
 def hydration_text(self):
  s=self.window.storage;ml=s.day_extra('hydration_ml');goal=s.day_extra('hydration_goal_ml')
  if ml is None:return '—'
  cups=round(ml/236.588,2)
  return f'{cups:g} / {round(goal/236.588,2):g}' if goal else f'{cups:g}'
