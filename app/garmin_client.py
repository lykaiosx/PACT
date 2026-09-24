from __future__ import annotations
from datetime import date,datetime,timedelta
from pathlib import Path
import os
TOKENSTORE=os.environ.get('PACT_TOKEN_DIR',str(Path.home()/'.garminconnect'))
class GarminBridge:
    def __init__(self): self.client=None
    def resume(self):
        from garminconnect import Garmin
        g=Garmin(); g.login(TOKENSTORE); self.client=g; return True
    def login(self,email:str,password:str,prompt_mfa=None):
        from garminconnect import Garmin
        g=Garmin(email,password,prompt_mfa=prompt_mfa); g.login(TOKENSTORE); self.client=g; return True
    def today(self):
        return self.for_day(date.today().isoformat())
    def for_day(self, day):
        if self.client is None: self.resume()
        sleep=self.client.get_sleep_data(day) or {}; stats=self.client.get_stats(day) or {}; dto=sleep.get('dailySleepDTO') or {}
        if stats.get('calendarDate') not in (None,day):raise ValueError('Garmin returned a different date')
        seconds=dto.get('sleepTimeSeconds'); seconds=dto.get('duration') if seconds is None else seconds
        mins=int(seconds/60) if isinstance(seconds,(int,float)) else None
        steps=stats.get('totalSteps',stats.get('steps')); resting=stats.get('restingHeartRate',stats.get('restingHeartRateValue'))
        scores=dto.get('sleepScores') or {}
        overall=scores.get('overall') or {}
        score=overall.get('value') if isinstance(overall,dict) else overall
        stages={k:dto.get(f) for k,f in [('deep','deepSleepSeconds'),('light','lightSleepSeconds'),('rem','remSleepSeconds'),('awake','awakeSleepSeconds')]}
        stages={k:v for k,v in stages.items() if isinstance(v,(int,float)) and v>=0}
        hydration={};hydration_error=False
        try:
            hydration=self.client.get_hydration_data(day) or {}
            if hydration.get('calendarDate') not in (None,day):raise ValueError('Hydration date mismatch')
        except Exception:hydration={};hydration_error=True
        def amount(key):
            v=hydration.get(key);return v if isinstance(v,(int,float)) and v>=0 else None
        return {'_day':day,'_data_through':stats.get('wellnessEndTimeLocal'),'_hydration_error':hydration_error,'hydration_ml':amount('valueInML'),'hydration_goal_ml':amount('goalInML'),'sleep_minutes':mins,'steps':int(steps) if isinstance(steps,(int,float)) else None,'resting_hr':int(resting) if isinstance(resting,(int,float)) else None,'sleep_score':score,'sleep_stages':stages or None,'body_battery':stats.get('bodyBatteryMostRecentValue'),'calories':stats.get('totalKilocalories') if isinstance(stats.get('totalKilocalories'),(int,float)) else None}

def freshness_text(checked_at,data_through,now=None):
    now=now or datetime.now()
    try:checked=datetime.fromisoformat(checked_at).strftime('%H:%M')
    except (TypeError,ValueError):return 'Not checked yet'
    text='Cloud checked '+checked
    try:
        through=datetime.fromisoformat(data_through)
        if through.tzinfo:through=through.astimezone().replace(tzinfo=None)
        # Some Garmin summaries use a future day-end boundary, not an upload timestamp.
        if through>now+timedelta(minutes=5):return text+' · watch data freshness unavailable'
        text+=' · data through '+through.strftime('%d %b %H:%M')
        if now-through>timedelta(hours=1):text+='\nWatch data is stale. Sync your watch in Garmin Connect, then click Sync now.'
        return text
    except (TypeError,ValueError):return text+' · watch data freshness unavailable'

def sync_state(checked_at,data_through,now=None,error=None,busy=False):
    now=now or datetime.now()
    if busy:return False,'Checking Garmin cloud…'
    text=freshness_text(checked_at,data_through,now)
    if error:return True,error+'\n'+text
    try:
        checked=datetime.fromisoformat(checked_at)
        if checked.tzinfo:checked=checked.astimezone().replace(tzinfo=None)
        if now-checked>timedelta(minutes=10):return True,text+'\nCloud check overdue. Select Sync now.'
    except (TypeError,ValueError):return True,'Not checked yet. Connect Garmin or select Sync now.'
    try:
        through=datetime.fromisoformat(data_through)
        if through.tzinfo:through=through.astimezone().replace(tzinfo=None)
        if through<=now and now-through>timedelta(hours=1):return True,text
    except (TypeError,ValueError):pass
    return False,text
