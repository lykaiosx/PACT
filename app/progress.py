"""Non-destructive CSV merge and explicit progress reset."""
import csv,json,math
from datetime import date,datetime
from pathlib import Path
from backup import create_backup,SETTINGS

def safety_backup(storage,reason):
    path=storage.db_path.with_name('pact-before-'+reason+'-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.pact')
    create_backup(storage,path);return path

def reset_progress(storage):
    safety=safety_backup(storage,'reset')
    with storage.conn:
        for table in ('sessions','daily','health_log','time_edits','imported_totals'):storage.conn.execute('DELETE FROM '+table)
        keep=SETTINGS-{'last_sync','last_data_through','progress_reset_at'}
        storage.conn.execute('DELETE FROM kv WHERE key NOT IN ('+','.join('?' for _ in keep)+')',tuple(keep))
        storage.conn.execute('INSERT INTO kv(key,value) VALUES(?,?)',('progress_reset_at',json.dumps(datetime.now().isoformat())))
    return safety

def load_csv(path):
    try:return _load_csv(path)
    except (csv.Error,UnicodeError) as e:raise ValueError('The CSV cannot be read. Save it as UTF-8 CSV and retry.') from e

def _load_csv(path):
    path=Path(path)
    if path.stat().st_size>25*1024*1024:raise ValueError('CSV exceeds the 25 MB limit.')
    rows=[];seen=set()
    with path.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f);headers=reader.fieldnames or []
        if len(set(headers))!=len(headers) or not {'date','work_seconds','learning_seconds'}<=set(headers):raise ValueError('Choose a PACT daily totals CSV (or daily.csv from an exported ZIP).')
        for index,row in enumerate(reader,2):
            try:
                if None in row or any(v is None for v in row.values()):raise ValueError('Missing or extra columns.')
                d=date.fromisoformat(row['date'])
                if d.year<2000 or d>date.today() or d.isoformat()!=row['date']:raise ValueError('Invalid date.')
                if row['date'] in seen:raise ValueError('Duplicate date.')
                seen.add(row['date'])
                def number(key,maximum=1e12,integer=False,required=False):
                    raw=row.get(key,'').strip()
                    if not raw:
                        if required:raise ValueError('Missing '+key)
                        return None
                    n=float(raw)
                    if not math.isfinite(n) or not 0<=n<=maximum or (integer and n!=int(n)):raise ValueError('Invalid '+key)
                    return int(n) if integer else n
                record={'day':row['date'],'totals':{k:number(k+'_seconds',86400,True,True) for k in ('work','learning')}}
                record['daily']={k:number(k,1 if k in ('breakfast','lunch','dinner') else 1e9,True) for k in ('creatives','breakfast','lunch','dinner','sleep_minutes','steps')}
                record['daily']['resting_hr']=number('resting_hr_bpm',1000,True)
                record['extras']={k:number(src,100 if k=='sleep_score' else 1e12) for k,src in [('sleep_score','sleep_score'),('body_battery','body_battery'),('calories','calories_kcal'),('hydration_ml','hydration_ml'),('hydration_goal_ml','hydration_goal_ml'),('water','legacy_manual_water_cups')]}
                stages={key:number(src,86400) for key,src in [('deep','deep_sleep_seconds'),('light','light_sleep_seconds'),('rem','rem_sleep_seconds'),('awake','awake_seconds')]}
                record['extras']['sleep_stages']={k:v for k,v in stages.items() if v is not None} or None
                for key in ('garmin_data_through','garmin_checked_at'):
                    value=row.get(key,'').strip()
                    if value:datetime.fromisoformat(value)
                    record['extras'][key]=value or None
                rows.append(record)
            except (ValueError,TypeError,OverflowError) as e:raise ValueError(f'Row {index}: {e}') from e
    if not rows:raise ValueError('This CSV has no daily records.')
    return sorted(rows,key=lambda r:r['day'])

def existing_dates(storage):
    from data_export import capture
    dates={r['day'] for r in storage.conn.execute('SELECT DISTINCT day FROM imported_totals')}
    for r in capture(storage)['daily']:
        if r['work_seconds'] or r['learning_seconds'] or r['creatives'] or any(r.get(k) for k in ('breakfast','lunch','dinner')) or any(r.get(k) is not None for k in ('sleep_minutes','steps','resting_hr_bpm','hydration_ml','calories_kcal','sleep_score','body_battery')):dates.add(r['date'])
    for r in storage.conn.execute('SELECT started_at FROM sessions WHERE ended_at IS NULL'):dates.add(r[0][:10])
    return dates

def import_csv(storage,path):
    rows=load_csv(path);existing=existing_dates(storage);selected=[r for r in rows if r['day'] not in existing]
    if not selected:return 0,len(rows),None
    safety=safety_backup(storage,'csv-import')
    with storage.conn:
        for r in selected:
            day=r['day'];base=r['daily']
            storage.conn.execute('INSERT OR REPLACE INTO daily(day,creatives,breakfast,lunch,dinner,sleep_minutes,steps,resting_hr) VALUES(?,?,?,?,?,?,?,?)',(day,base['creatives'] or 0,base['breakfast'] or 0,base['lunch'] or 0,base['dinner'] or 0,base['sleep_minutes'],base['steps'],base['resting_hr']))
            for kind,seconds in r['totals'].items():storage.conn.execute('INSERT INTO imported_totals(day,kind,seconds) VALUES(?,?,?)',(day,kind,seconds))
            for key,value in r['extras'].items():
                if value is not None:storage.conn.execute('INSERT OR REPLACE INTO kv(key,value) VALUES(?,?)',(day+':'+key,json.dumps(value)))
    return len(selected),len(rows)-len(selected),safety
