"""Portable CSV exports: local calendar days, exact timer seconds, no credentials."""
import csv,io,json,zipfile,os,tempfile
from pathlib import Path
from datetime import date,datetime,timedelta

DAILY_FIELDS=['date','work_seconds','work_hours','learning_seconds','learning_hours','creatives','breakfast','lunch','dinner','water_cups','hydration_ml','hydration_goal_ml','legacy_manual_water_cups','sleep_minutes','sleep_score','deep_sleep_seconds','light_sleep_seconds','rem_sleep_seconds','awake_seconds','steps','resting_hr_bpm','body_battery','calories_kcal','garmin_data_through','garmin_checked_at']
def capture(storage,now=None):
 now=now or datetime.now();sessions=[dict(r) for r in storage.conn.execute('SELECT * FROM sessions ORDER BY started_at,id')]
 daily={r['day']:dict(r) for r in storage.conn.execute('SELECT * FROM daily')};extras={}
 for r in storage.conn.execute('SELECT key,value FROM kv'):
  key=r['key']
  if len(key)>11 and key[10]==':':
   try:date.fromisoformat(key[:10]);extras.setdefault(key[:10],{})[key[11:]]=json.loads(r['value'])
   except (ValueError,TypeError):pass
 imported=[dict(r) for r in storage.conn.execute('SELECT * FROM imported_totals ORDER BY day,kind')];imported_map={(r['day'],r['kind']):r['seconds'] for r in imported}
 hours={};days=set(daily)|set(extras)|{r['day'] for r in imported}
 for row in sessions:
  start=datetime.fromisoformat(row['started_at']);end=min(now,datetime.fromisoformat(row['ended_at']) if row['ended_at'] else now)
  if row['kind'] not in ('work','learning'):continue
  while start<end:
   boundary=start.replace(minute=0,second=0,microsecond=0)+timedelta(hours=1);stop=min(end,boundary);key=(start.date().isoformat(),start.hour,row['kind']);hours[key]=hours.get(key,0)+(stop-start).total_seconds();days.add(key[0]);start=stop
 days.add(now.date().isoformat());first=min(date.fromisoformat(d) for d in days);rows=[];hourly=[];d=first
 while d<=now.date():
  key=d.isoformat();base=daily.get(key,{});extra=extras.get(key,{});stages=extra.get('sleep_stages') or {};totals={k:sum(hours.get((key,h,k),0) for h in range(24))+imported_map.get((key,k),0) for k in ('work','learning')}
  row={'date':key,'work_seconds':int(totals['work']),'work_hours':round(totals['work']/3600,6),'learning_seconds':int(totals['learning']),'learning_hours':round(totals['learning']/3600,6),'creatives':base.get('creatives',0),'breakfast':base.get('breakfast'),'lunch':base.get('lunch'),'dinner':base.get('dinner'),'water_cups':round(extra['hydration_ml']/236.588,6) if extra.get('hydration_ml') is not None else None,'hydration_ml':extra.get('hydration_ml'),'hydration_goal_ml':extra.get('hydration_goal_ml'),'legacy_manual_water_cups':extra.get('water'),'sleep_minutes':base.get('sleep_minutes'),'sleep_score':extra.get('sleep_score'),'steps':base.get('steps'),'resting_hr_bpm':base.get('resting_hr'),'body_battery':extra.get('body_battery'),'calories_kcal':extra.get('calories'),'garmin_data_through':extra.get('garmin_data_through'),'garmin_checked_at':extra.get('garmin_checked_at')}
  for field,stage in [('deep_sleep_seconds','deep'),('light_sleep_seconds','light'),('rem_sleep_seconds','rem'),('awake_seconds','awake')]:row[field]=stages.get(stage)
  rows.append(row)
  for h in range(24):
   if d==now.date() and h>now.hour:break
   hourly.append({'date':key,'hour_start_local':f'{key}T{h:02}:00:00','work_seconds':None if (key,'work') in imported_map else int(hours.get((key,h,'work'),0)),'learning_seconds':None if (key,'learning') in imported_map else int(hours.get((key,h,'learning'),0))})
  d+=timedelta(days=1)
 logs=[dict(r) for r in storage.conn.execute('SELECT observed_at,day,data_through,payload FROM health_log ORDER BY id')]
 snapshots=[]
 for log in logs:
  payload=json.loads(log.pop('payload'));stages=payload.pop('sleep_stages',{}) or {};log.update(payload)
  log.update({k+'_seconds':v for k,v in stages.items()});snapshots.append(log)
 return {'captured_at':now.isoformat(timespec='seconds'),'daily':rows,'hourly':hourly,'sessions':sessions,'health':snapshots,'imported_totals':imported}
def csv_bytes(rows,fields):
 out=io.StringIO(newline='');writer=csv.DictWriter(out,fieldnames=fields,extrasaction='ignore');writer.writeheader()
 for row in rows:
  # Keep user-derived text from being evaluated as spreadsheet formulas.
  writer.writerow({k:("'"+v if isinstance(v,str) and v.startswith(('=','+','-','@')) else v) for k,v in row.items() if k in fields})
 return out.getvalue().encode('utf-8-sig')
def export_data(storage,path,full=False):
 snapshot=capture(storage);path=Path(path);fd,tmp=tempfile.mkstemp(prefix='.pact-export-',dir=path.parent);os.close(fd)
 try:
  if full:
   with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
    if snapshot['imported_totals']:z.writestr('imported_daily_totals.csv',csv_bytes(snapshot['imported_totals'],['day','kind','seconds']))
    z.writestr('daily.csv',csv_bytes(snapshot['daily'],DAILY_FIELDS));z.writestr('hourly.csv',csv_bytes(snapshot['hourly'],['date','hour_start_local','work_seconds','learning_seconds']));z.writestr('sessions.csv',csv_bytes(snapshot['sessions'],['id','kind','started_at','ended_at']))
    z.writestr('garmin_observations.csv',csv_bytes(snapshot['health'],['observed_at','day','data_through','sleep_minutes','sleep_score','steps','resting_hr','body_battery','calories','hydration_ml','hydration_goal_ml','deep_seconds','light_seconds','rem_seconds','awake_seconds']))
    z.writestr('README.txt','PACT export captured at '+snapshot['captured_at']+' local time.\nCSV files open in Excel and import into Google Sheets.\nDaily rows use local calendar days (midnight to midnight). Hourly timer rows split sessions at each hour and midnight. Health values are daily Garmin totals, not hourly measurements. Blank health fields mean unavailable. Observations are logged starting with PACT 1.2; earlier snapshots cannot be reconstructed. Open sessions have a blank end, and totals stop at the export time. Today is partial. Historical gaps are retained; missing daily checkboxes/water remain blank. Hydration is stored in Garmin milliliters and converted to US cups (236.588 mL per cup). Older manual water entries are preserved separately in legacy_manual_water_cups. Imported daily totals have no known hourly distribution; affected hourly values are blank, and imported_daily_totals.csv preserves these totals separately. Daily CSV totals include both imported totals and any timed sessions. No credentials or Garmin tokens are exported.\n')
  else:Path(tmp).write_bytes(csv_bytes(snapshot['daily'],DAILY_FIELDS))
  os.replace(tmp,path)
 finally:
  if Path(tmp).exists():Path(tmp).unlink()
 return len(snapshot['daily'])
