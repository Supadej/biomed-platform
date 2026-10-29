"""Service job report fields and an optional linked Staff Portal calendar event."""
import json,datetime
import permissions_policy as policy

def validate(r):
 for key in ['description','diagnosis','actionTaken','result','comment']:
  if key in r and (not isinstance(r[key],str) or len(r[key])>100000):raise ValueError('Report text must be at most 100000 characters: '+key)
 for key in ['feedbackComment','customerSignatory']:
  if key in r and (not isinstance(r[key],str) or len(r[key])>10000):raise ValueError('Invalid '+key)
 for key,choices in [('feedbackSolved',['','Yes','No'])]+[(k,['','Excellent','Fair','Needs improvement']) for k in ['feedbackSpeed','feedbackPreparedness','feedbackCourtesy','feedbackSatisfaction']]:
  if r.get(key,'') not in choices:raise ValueError('Choose an available '+key)
 if r.get('calendarEnabled') not in [None,True,False]:raise ValueError('Choose whether to link the calendar')
 if r.get('calendarEnabled'):
  date=r.get('scheduledDate') or r.get('date') or datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).date().isoformat()
  try:datetime.date.fromisoformat(date)
  except (TypeError,ValueError):raise ValueError('Choose a calendar date')
  r['calendarDate']=date

def calendar(c,actor,perms,r,old):
 import crm_api as crm
 prior=(old or {}).get('calendarEventId')
 if not r.get('calendarEnabled'):
  if prior:
   crm.need(perms,'events','edit');c.execute("UPDATE crm_records SET deleted=1,version=version+1 WHERE entity='Events' AND id=? AND json_extract(payload,'$.ServiceJobId')=?",(prior,r['id']));crm.audit(c,actor,'Events',prior,'unlink service job calendar',{'jobId':r['id']})
  r.pop('calendarEventId',None);return
 crm.bind_users(c);uid=crm.user_id(c,actor)
 user=c.execute('SELECT crm_user_id FROM crm_identity WHERE portal_user_id=?',(r.get('engineer'),)).fetchone()
 owner=user[0] if user else uid
 inst=c.execute("SELECT payload FROM fse_records WHERE id=? AND kind='instruments'",(r.get('instrumentId'),)).fetchone();i=json.loads(inst[0]) if inst else {};loc=r.get('location') or i.get('location') or 'Location not set';date=r['calendarDate']
 data={'Title':r['jobNo']+' · '+loc+' · '+date,'StartDate':date+'T00:00:00','EndDate':date+'T23:59:00','IsAllDay':True,'MainUserID':owner,'UserIds':[] if owner==uid else [uid],'Location':loc,'ServiceJobId':r['id'],'_bridgeSource':'service-job','Description':'Service job '+r['jobNo']+' · '+r.get('jobType',''),'ConferenceURL':'/?portal=1&module=instrument_service&record='+r['id']}
 if prior:
  existing=crm.raw(c,'Events',prior)
  if not existing:
   row=c.execute("SELECT payload FROM crm_records WHERE entity='Events' AND id=?",(prior,)).fetchone();existing=json.loads(row[0]) if row else None
  if not existing or existing.get('ServiceJobId')!=r['id']:raise ValueError('Calendar referral changed; contact the administrator')
  if all(existing.get(k)==v for k,v in data.items()):r['calendarEventId']=prior;return
  crm.need(perms,'events','edit')
  if owner!=uid:crm.need(perms,'events','assign')
  c.execute("UPDATE crm_records SET deleted=0 WHERE entity='Events' AND id=?",(prior,));crm.update(c,'Events',prior,data);event_id=prior
 else:
  crm.need(perms,'events','create')
  if owner!=uid:crm.need(perms,'events','assign')
  event_id=crm.insert(c,'Events',data)['Id']
 r['calendarEventId']=event_id;crm.audit(c,actor,'Events',event_id,'update service job calendar' if prior else 'create service job calendar',{'jobId':r['id']})
