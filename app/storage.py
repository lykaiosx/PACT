from __future__ import annotations
import sqlite3
import os
import json
from datetime import date, datetime, timedelta
from pathlib import Path
APP_DIR = Path(os.environ.get('PACT_DATA_DIR', str(Path.home() / 'AppData' / 'Local' / 'PersonalOS')))
DB_PATH = APP_DIR / "personalos.sqlite3"
class Storage:
    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        # One-time SQLite backup before PACT first opens an existing PersonalOS DB.
        backup=self.db_path.with_name('personalos-before-pact.sqlite3')
        if self.db_path.stat().st_size and not backup.exists():
            dest=sqlite3.connect(backup)
            try:self.conn.backup(dest)
            finally:dest.close()
        self._init()
    def _init(self):
        self.conn.executescript('''
        CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, started_at TEXT NOT NULL, ended_at TEXT);
        CREATE TABLE IF NOT EXISTS daily (day TEXT PRIMARY KEY, creatives INTEGER NOT NULL DEFAULT 0, breakfast INTEGER NOT NULL DEFAULT 0, lunch INTEGER NOT NULL DEFAULT 0, dinner INTEGER NOT NULL DEFAULT 0, sleep_minutes INTEGER, steps INTEGER, resting_hr INTEGER);
        CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE IF NOT EXISTS health_log (id INTEGER PRIMARY KEY AUTOINCREMENT, observed_at TEXT NOT NULL, day TEXT NOT NULL, data_through TEXT, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS time_edits (id INTEGER PRIMARY KEY AUTOINCREMENT, edited_at TEXT NOT NULL, before_json TEXT, after_json TEXT, undone INTEGER NOT NULL DEFAULT 0);
        ''')
        self.conn.commit()
    def _ensure_day(self, day: str):
        self.conn.execute("INSERT OR IGNORE INTO daily(day) VALUES(?)", (day,)); self.conn.commit()
    def get_day(self, day: str | None = None):
        day = day or date.today().isoformat(); self._ensure_day(day)
        return dict(self.conn.execute("SELECT * FROM daily WHERE day=?", (day,)).fetchone())
    def set_day_field(self, field: str, value, day: str | None = None):
        if field not in {"creatives","breakfast","lunch","dinner","sleep_minutes","steps","resting_hr"}: raise ValueError(field)
        day = day or date.today().isoformat(); self._ensure_day(day)
        self.conn.execute(f"UPDATE daily SET {field}=? WHERE day=?", (value, day)); self.conn.commit()
    def start_session(self, kind: str):
        active=self.active_session(kind)
        if active: return active["id"]
        cur=self.conn.execute("INSERT INTO sessions(kind,started_at) VALUES(?,?)",(kind,datetime.now().isoformat(timespec='seconds'))); self.conn.commit(); return cur.lastrowid
    def stop_session(self, kind: str):
        active=self.active_session(kind)
        if active: self.conn.execute("UPDATE sessions SET ended_at=? WHERE id=?",(datetime.now().isoformat(timespec='seconds'),active["id"])); self.conn.commit()
    def active_session(self, kind: str):
        row=self.conn.execute("SELECT * FROM sessions WHERE kind=? AND ended_at IS NULL ORDER BY id DESC LIMIT 1",(kind,)).fetchone(); return dict(row) if row else None
    def seconds_for_day(self, kind: str, day: str | None = None):
        target=date.fromisoformat(day) if day else date.today(); start=datetime.combine(target,datetime.min.time()); end=start+timedelta(days=1); now=datetime.now()
        rows=self.conn.execute("SELECT * FROM sessions WHERE kind=? AND started_at < ? AND COALESCE(ended_at, ?) > ?",(kind,end.isoformat(),now.isoformat(),start.isoformat())).fetchall(); total=0.0
        for row in rows:
            s=max(datetime.fromisoformat(row['started_at']),start); e=min(datetime.fromisoformat(row['ended_at']) if row['ended_at'] else now,end)
            if e>s: total+=(e-s).total_seconds()
        return int(total)
    def history(self, kind, days=366):
        return [(d:=date.today()-timedelta(days=i), self.seconds_for_day(kind,d.isoformat())/3600) for i in range(days-1,-1,-1)]
    def has_activity_record(self, kind, day):
        start=datetime.combine(date.fromisoformat(day),datetime.min.time());end=start+timedelta(days=1)
        return self.conn.execute('SELECT 1 FROM sessions WHERE kind=? AND started_at<? AND (started_at>=? OR COALESCE(ended_at,?)>?) LIMIT 1',(kind,end.isoformat(),start.isoformat(),datetime.now().isoformat(),start.isoformat())).fetchone() is not None
    def work_history(self, days: int = 84):
        return [(d:=date.today()-timedelta(days=i), self.seconds_for_day('work',d.isoformat())/3600) for i in range(days-1,-1,-1)]
    def get_setting(self, key, default=None):
        row = self.conn.execute('SELECT value FROM kv WHERE key=?', (key,)).fetchone()
        if row is None: return default
        try: return json.loads(row['value'])
        except (ValueError, TypeError): return default
    def set_setting(self, key, value):
        self.conn.execute('INSERT OR REPLACE INTO kv(key,value) VALUES(?,?)', (key,json.dumps(value)))
        self.conn.commit()
    def target(self, kind):
        value = self.get_setting('target_'+kind, {'work':8,'learning':2,'sleep':8}[kind])
        try: return min(24,max(.25,float(value)))
        except (ValueError,TypeError): return {'work':8,'learning':2,'sleep':8}[kind]
    def day_extra(self, key, default=None, day=None):
        return self.get_setting((day or date.today().isoformat())+':'+key,default)
    def set_day_extra(self, key, value, day=None):
        self.set_setting((day or date.today().isoformat())+':'+key,value)
    def existing_day(self, day):
        row=self.conn.execute('SELECT * FROM daily WHERE day=?',(day,)).fetchone()
        return dict(row) if row else {}
    def record_health(self, data, day, observed_at):
        keys=('sleep_minutes','steps','resting_hr','sleep_score','sleep_stages','body_battery','calories','hydration_ml','hydration_goal_ml')
        payload={k:data[k] for k in keys if data.get(k) is not None}
        self.conn.execute('INSERT INTO health_log(observed_at,day,data_through,payload) VALUES(?,?,?,?)',(observed_at,day,data.get('_data_through'),json.dumps(payload)))
        self.conn.commit()

    def sessions_for_day(self, kind, day):
        start=datetime.combine(date.fromisoformat(day),datetime.min.time());end=start+timedelta(days=1)
        return [dict(r) for r in self.conn.execute('SELECT * FROM sessions WHERE kind=? AND started_at<? AND COALESCE(ended_at,?)>? ORDER BY started_at', (kind,end.isoformat(),datetime.now().isoformat(),start.isoformat()))]

    def correct_session(self, kind, start=None, end=None, session_id=None, remove=False):
        if kind not in ('work','learning'):raise ValueError('Choose Work or Learning.')
        before=None
        if session_id is not None:
            row=self.conn.execute('SELECT * FROM sessions WHERE id=?',(session_id,)).fetchone()
            if not row or row['kind']!=kind:raise ValueError('This session no longer exists.')
            before=dict(row)
            if before['ended_at'] is None:raise ValueError('Stop this timer before correcting its session.')
        if remove and before is None:raise ValueError('Select a session first.')
        if not remove:
            start=datetime.fromisoformat(start);end=datetime.fromisoformat(end)
            if start.tzinfo or end.tzinfo or start>=end or end>datetime.now():raise ValueError('Use local times with the end after the start and no later than now.')
            if start.year<2000:raise ValueError('Choose a date from 2000 onward.')
            start=start.isoformat(timespec='seconds');end=end.isoformat(timespec='seconds')
            overlap=self.conn.execute('SELECT 1 FROM sessions WHERE kind=? AND id!=? AND started_at<? AND COALESCE(ended_at,?)>?',(kind,session_id or -1,end,datetime.now().isoformat(),start)).fetchone()
            if overlap:raise ValueError('This overlaps another session of the same activity. Adjust the times first.')
        with self.conn:
            after=None
            if remove:self.conn.execute('DELETE FROM sessions WHERE id=?',(session_id,))
            elif before:
                self.conn.execute('UPDATE sessions SET started_at=?,ended_at=? WHERE id=?',(start,end,session_id));after={'id':session_id,'kind':kind,'started_at':start,'ended_at':end}
            else:
                session_id=self.conn.execute('INSERT INTO sessions(kind,started_at,ended_at) VALUES(?,?,?)',(kind,start,end)).lastrowid;after={'id':session_id,'kind':kind,'started_at':start,'ended_at':end}
            self.conn.execute('INSERT INTO time_edits(edited_at,before_json,after_json) VALUES(?,?,?)',(datetime.now().isoformat(),json.dumps(before),json.dumps(after)))
        return session_id

    def undo_time_edit(self):
        row=self.conn.execute('SELECT * FROM time_edits WHERE undone=0 ORDER BY id DESC LIMIT 1').fetchone()
        if row is None:raise ValueError('There are no corrections to undo.')
        before=json.loads(row['before_json']);after=json.loads(row['after_json']);sid=(after or before)['id']
        current=self.conn.execute('SELECT * FROM sessions WHERE id=?',(sid,)).fetchone()
        if (dict(current) if current else None)!=after:raise ValueError('This session changed again; it cannot be safely undone.')
        if before:
            collision=self.conn.execute('SELECT 1 FROM sessions WHERE kind=? AND id!=? AND started_at<? AND COALESCE(ended_at,?)>?',(before['kind'],sid,before['ended_at'],datetime.now().isoformat(),before['started_at'])).fetchone()
            if collision:raise ValueError('Undo would overlap another session. Correct that session first.')
        with self.conn:
            self.conn.execute('DELETE FROM sessions WHERE id=?',(sid,))
            if before:self.conn.execute('INSERT INTO sessions(id,kind,started_at,ended_at) VALUES(:id,:kind,:started_at,:ended_at)',before)
            self.conn.execute('UPDATE time_edits SET undone=1 WHERE id=?',(row['id'],))

    def latest_sleep(self):
        row=self.conn.execute('SELECT day,sleep_minutes FROM daily WHERE day<=? AND sleep_minutes>0 ORDER BY day DESC LIMIT 1',(date.today().isoformat(),)).fetchone()
        if not row:return {'day':date.today().isoformat(),'sleep_minutes':None,'sleep_score':None,'sleep_stages':{}}
        result=dict(row)
        for key in ('sleep_score','sleep_stages'):result[key]=self.day_extra(key,day=result['day'])
        return result
