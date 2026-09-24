"""Versioned, credential-free migration snapshots; restores are transactional."""
import hashlib,json,math,os,tempfile,zipfile,sqlite3
from pathlib import Path
from datetime import datetime,date

TABLES={'sessions':['id','kind','started_at','ended_at'], 'daily':['day','creatives','breakfast','lunch','dinner','sleep_minutes','steps','resting_hr'], 'kv':['key','value'], 'health_log':['id','observed_at','day','data_through','payload']}
SETTINGS={'theme','custom_background','custom_ink','intensity_colors','target_work','target_learning','target_sleep','annual_work_goal','annual_learning_goal','water_goal','last_sync','last_data_through'}
EXTRAS={'sleep_score','sleep_stages','body_battery','calories','hydration_ml','hydration_goal_ml','water','garmin_data_through','garmin_checked_at'}
LIMIT=100*1024*1024

def allowed_key(key):
    if key in SETTINGS:return True
    try:return isinstance(key,str) and len(key)>11 and date.fromisoformat(key[:10]).isoformat()==key[:10] and key[10]==':' and key[11:] in EXTRAS
    except ValueError:return False

def create_backup(storage,path):
    now=datetime.now().isoformat(timespec='seconds');data={}
    for table,cols in TABLES.items():data[table]=[dict(r) for r in storage.conn.execute('SELECT '+','.join(cols)+' FROM '+table)]
    data['kv']=[r for r in data['kv'] if allowed_key(r['key'])]
    # A timer restored on another device must not count the journey between devices.
    running=sum(r['ended_at'] is None for r in data['sessions'])
    for r in data['sessions']:
        if r['ended_at'] is None:r['ended_at']=now
    raw=json.dumps({'format':'PACT backup','version':1,'app_version':'1.1.1','created_at':now,'running_timers_stopped':running,'tables':data},allow_nan=False).encode()
    path=Path(path);fd,tmp=tempfile.mkstemp(prefix='.pact-backup-',dir=path.parent);os.close(fd)
    try:
        with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('pact.json',raw);z.writestr('sha256.txt',hashlib.sha256(raw).hexdigest())
        os.replace(tmp,path)
    finally:
        if Path(tmp).exists():Path(tmp).unlink()
    return load_backup(path)

def load_backup(path):
    try:
        with zipfile.ZipFile(path) as z:
            if sorted(z.namelist())!=['pact.json','sha256.txt'] or any(i.file_size>LIMIT for i in z.infolist()):raise ValueError('This is not a supported PACT backup.')
            raw=z.read('pact.json')
            if hashlib.sha256(raw).hexdigest()!=z.read('sha256.txt').decode().strip():raise ValueError('The backup checksum does not match.')
        data=json.loads(raw)
        if data.get('format')!='PACT backup' or data.get('version')!=1:raise ValueError('Unsupported backup version.')
        datetime.fromisoformat(data['created_at'])
        tables=data['tables']
        if set(tables)!=set(TABLES):raise ValueError('Backup is missing required data.')
        for table,cols in TABLES.items():
            if not isinstance(tables[table],list):raise ValueError('Invalid backup table.')
            keys=set()
            for r in tables[table]:
                if set(r)!=set(cols):raise ValueError('Invalid backup columns.')
                key=r[cols[0]]
                if key in keys:raise ValueError('Duplicate backup records.')
                keys.add(key)
                if table in ('sessions','health_log') and (type(key)!=int or not 1<=key<2**63):raise ValueError('Invalid record identifier.')
                if table=='sessions':
                    a=datetime.fromisoformat(r['started_at']);b=datetime.fromisoformat(r['ended_at'])
                    if r['kind'] not in ('work','learning') or a.tzinfo or b.tzinfo or b<a or a.year<2000 or b>datetime.now():raise ValueError('Invalid session times.')
                if table=='daily':
                    date.fromisoformat(r['day'])
                    for k,v in r.items():
                        if k!='day' and v is not None and (type(v)!=int or not 0<=v<2**63):raise ValueError('Invalid daily value.')
                    if any(r[k] is None for k in ('creatives','breakfast','lunch','dinner')):raise ValueError('Missing daily value.')
                if table=='health_log':
                    date.fromisoformat(r['day']);datetime.fromisoformat(r['observed_at']);payload=json.loads(r['payload'])
                    if not isinstance(payload,dict):raise ValueError('Invalid health record.')
                if table=='kv':
                    if not allowed_key(r['key']):raise ValueError('Unsupported setting in backup.')
                    v=json.loads(r['value']);key=r['key']
                    if key.startswith(('target_','annual_')) and (not isinstance(v,(int,float)) or not math.isfinite(v) or v<=0 or v>(24 if key.startswith('target_') else 8784)):raise ValueError('Invalid goal.')
                    if key=='theme' and v not in ('light','dark','high contrast','custom'):raise ValueError('Invalid theme.')
                    if key in ('custom_background','custom_ink'):
                        from PySide6.QtGui import QColor
                        if not isinstance(v,str) or not QColor(v).isValid():raise ValueError('Invalid color.')
                    if key=='intensity_colors' and v is not None:
                        from PySide6.QtGui import QColor
                        if not isinstance(v,list) or len(v)!=4 or not all(isinstance(c,str) and QColor(c).isValid() for c in v):raise ValueError('Invalid chart colors.')
        # Validate date-specific extras before they reach the painter.
        for r in tables['kv']:
            if ':' not in r['key']:continue
            key=r['key'][11:];v=json.loads(r['value'])
            if key=='sleep_stages':
                if v is not None and (not isinstance(v,dict) or not set(v)<= {'deep','light','rem','awake'} or not all(isinstance(n,(int,float)) and math.isfinite(n) and n>=0 for n in v.values())):raise ValueError('Invalid sleep stages.')
            elif key not in ('garmin_data_through','garmin_checked_at') and v is not None and (not isinstance(v,(int,float)) or not math.isfinite(v) or v<0):raise ValueError('Invalid health value.')
        return data
    except (KeyError,TypeError,UnicodeError,zipfile.BadZipFile,json.JSONDecodeError,OverflowError) as e:raise ValueError('The file is not a valid PACT backup.') from e

def restore_backup(storage,path):
    data=load_backup(path)
    # A regular backup can be restored through this same UI if replacement was a mistake.
    safety=storage.db_path.with_name('pact-before-restore-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.pact')
    create_backup(storage,safety)
    with storage.conn:
        for table in ('time_edits',*TABLES):storage.conn.execute('DELETE FROM '+table)
        for table,cols in TABLES.items():
            storage.conn.executemany('INSERT INTO '+table+' ('+','.join(cols)+') VALUES('+','.join('?' for _ in cols)+')',[[r[c] for c in cols] for r in data['tables'][table]])
    return safety
