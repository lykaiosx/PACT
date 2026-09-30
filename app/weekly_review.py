"""Weekly recap calculated from recorded local data; no inferred missing values."""
from datetime import date,timedelta
from html import escape

def last_week(today=None):
    today=today or date.today();return today-timedelta(days=today.weekday()+7)

def duration(seconds):
    minutes=round(seconds/60);return f'{minutes//60} h {minutes%60:02} min'

def summary(storage,start=None,today=None,end=None):
    today=today or date.today();start=start or last_week(today)
    if end is None:
        start-=timedelta(days=start.weekday());end=start+timedelta(days=6)
        if end>=today:raise ValueError('Choose a completed week.')
    if end>today or end<start:raise ValueError('Choose a valid recorded period.')
    days=[start+timedelta(days=i) for i in range((end-start).days+1)];result={'start':start,'end':days[-1],'activities':{},'has_data':False,'edited_days':0}
    for kind in ('work','learning'):
        values=[storage.seconds_for_day(kind,d.isoformat()) for d in days];known=[storage.has_activity_record(kind,d.isoformat()) for d in days];target=storage.target(kind)*3600
        hits=[k and v>=target for k,v in zip(known,values)];longest=run=0
        for hit in hits:run=run+1 if hit else 0;longest=max(longest,run)
        previous_days=[d-timedelta(days=len(days)) for d in days];previous_known=sum(storage.has_activity_record(kind,d.isoformat()) for d in previous_days)
        previous=sum(storage.seconds_for_day(kind,d.isoformat()) for d in previous_days)
        best=max(range(len(days)),key=lambda i:values[i]) if any(v>0 for v in values) else None
        result['activities'][kind]={'values':values,'known':known,'total':sum(values),'recorded':sum(known),'goal_days':sum(hits),'streak':longest,'best':None if best is None else (days[best],values[best]),'previous':previous if previous_known else None,'previous_recorded':previous_known}
        result['has_data']|=any(known)
    creatives=[];meal_values=[];complete_meals=0;sleep=[];creative_values=[];sleep_values=[];meal_types=[0,0,0];covered=0
    for day in days:
        key=day.isoformat();value=storage.manual_value('creatives',key)
        creative_values.append(value)
        if value is not None:creatives.append(value)
        meals=[storage.manual_value(k,key) for k in ('breakfast','lunch','dinner')];meal_values.extend(v for v in meals if v is not None);complete_meals+=all(v==1 for v in meals)
        for i,v in enumerate(meals):meal_types[i]+=v or 0
        minutes=storage.existing_day(key).get('sleep_minutes');sleep_values.append(minutes)
        covered+=bool(value is not None or any(v is not None for v in meals) or minutes is not None or any(storage.has_activity_record(k,key) for k in ('work','learning')))
        if minutes is not None:sleep.append(minutes)
        result['edited_days']+=bool(storage.conn.execute('SELECT 1 FROM edit_history WHERE day=? LIMIT 1',(key,)).fetchone())
    result.update(creatives=sum(creatives),creative_days=len(creatives),meals=sum(meal_values),meal_entries=len(meal_values),complete_meal_days=complete_meals,sleep_average=sum(sleep)/len(sleep) if sleep else None,sleep_nights=len(sleep))
    result.update(days=days,creative_values=creative_values,sleep_values=sleep_values,meal_types=meal_types,covered_days=covered)
    result['has_data']|=bool(creatives or meal_values or sleep)
    return result

from wrapped import WrappedReview as WeeklyReview
