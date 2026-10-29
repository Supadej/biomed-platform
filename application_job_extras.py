"""Optional application report acknowledgement and owned calendar event."""
import json,datetime,hashlib,math
import permissions_policy as policy
REPORT_FIELDS='reference topic customerId customer contact products instrumentId specialist serviceType status start end purpose workPerformed result followUp followUpDate customerFeedback areaCode department instrumentWarranty instrumentOwnership feedbackSolved feedbackSpeed feedbackPreparedness feedbackCourtesy feedbackSatisfaction feedbackComment customerSignatory'.split()
def digest(r):return hashlib.sha256(json.dumps({k:r.get(k) for k in REPORT_FIELDS},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def validate(r,raw,prior):
 for key,choices in [('feedbackSolved',['','Yes','No'])]+[(k,['','Excellent','Fair','Needs improvement']) for k in ['feedbackSpeed','feedbackPreparedness','feedbackCourtesy','feedbackSatisfaction']]+[('instrumentWarranty',['','In Warranty','Out of Warranty','Service Contract']),('instrumentOwnership',['','Reagent Rental','Company Property','Customer Property'])]:
  r[key]=raw.get(key,prior.get(key,''))
  if r[key] not in choices:raise ValueError('Choose a valid '+key)
 for key in ['areaCode','department','feedbackComment','customerSignatory']:
  r[key]=raw.get(key,prior.get(key,''))
  if not isinstance(r[key],str) or len(r[key])>10000:raise ValueError('Invalid '+key)
 enabled=raw.get('calendarEnabled',prior.get('calendarEnabled',False))
 if not isinstance(enabled,bool):raise ValueError('Choose whether to link the calendar')
 r['calendarEnabled']=enabled;r['calendarDate']=r['start'][:10]
def signature(actor,r,raw,prior):
 sig=raw.get('customerSignature',prior.get('customerSignature'));old=prior.get('customerSignature')
 if sig is None:return
 if not isinstance(sig,dict):raise ValueError('Invalid customer signature')
 if sig==old:
  if sig.get('reportHash')!=digest(r):raise ValueError('The report changed after signing. Clear the signature or ask the customer to sign the revised report.')
  r['customerSignature']=sig;return
 name=str(sig.get('name') or '').strip();strokes=sig.get('strokes')
 if not name or len(name)>200 or sig.get('consent') is not True:raise ValueError('Enter customer name and confirm acknowledgement')
 if not isinstance(strokes,list) or not 1<=len(strokes)<=100:raise ValueError('Draw a customer signature')
 clean=[];count=0
 for stroke in strokes:
  if not isinstance(stroke,list) or len(stroke)<2:raise ValueError('Draw a complete signature stroke')
  points=[]
  for point in stroke:
   if not isinstance(point,list) or len(point)!=2 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=1 for v in point):raise ValueError('Invalid signature coordinates')
   count+=1
   if count>5000:raise ValueError('Signature too complex; clear and sign again')
   points.append([round(v,5) for v in point])
  clean.append(points)
 if old and clean==old.get('strokes'):raise ValueError('Ask the customer to draw a new signature for the revised report')
 r['customerSignatory']=name;r['customerSignature']={'name':name,'strokes':clean,'consent':True,'signedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'capturedBy':str(actor[4]),'reportHash':digest(r)}
def calendar(c,actor,perms,r,prior):
 import crm_api as crm
 previous=prior.get('calendarEventId');existing=None
 if previous:
  row=c.execute("SELECT payload FROM crm_records WHERE entity='Events' AND id=?",(previous,)).fetchone();existing=json.loads(row[0]) if row else None
  if not existing or existing.get('ApplicationServiceId')!=r['id']:raise ValueError('Calendar link changed; contact the administrator')
 if not r.get('calendarEnabled'):
  if previous:
   for key in ['application_service.calendar','crm_view','crm.events.view','crm.events.edit']:policy.need(perms,key)
   c.execute("UPDATE crm_records SET deleted=1,version=version+1 WHERE entity='Events' AND id=?",(previous,));crm.audit(c,actor,'Events',previous,'unlink application service calendar',{'applicationJobId':r['id']})
  return
 crm.bind_users(c);user=crm.user_id(c,actor);owner=c.execute('SELECT crm_user_id FROM crm_identity WHERE portal_user_id=?',(r['specialist'],)).fetchone()
 if not owner:raise ValueError('Specialist has no calendar identity')
 owner=owner[0];date=r['calendarDate'];event={'Title':r['customer'],'StartDate':date+'T00:00:00','EndDate':date+'T23:59:00','IsAllDay':True,'MainUserID':owner,'UserIds':[] if owner==user else [user],'Location':r['customer'],'ApplicationServiceId':r['id'],'_bridgeSource':'application-service','Description':r['reference']+(' · '+r['topic'] if r.get('topic') else ''),'ConferenceURL':'/?portal=1&module=application_service&applicationRecord='+r['id']}
 if existing and all(existing.get(k)==v for k,v in event.items()):r['calendarEventId']=previous;return
 for key in ['application_service.calendar','crm_view','crm.events.view','crm.events.edit' if previous else 'crm.events.create']:policy.need(perms,key)
 if owner!=user:crm.need(perms,'events','assign')
 if previous:
  c.execute("UPDATE crm_records SET deleted=0 WHERE entity='Events' AND id=?",(previous,));crm.update(c,'Events',previous,event);ident=previous
 else:ident=crm.insert(c,'Events',event)['Id']
 r['calendarEventId']=ident;crm.audit(c,actor,'Events',ident,'update application service calendar' if previous else 'create application service calendar',{'applicationJobId':r['id']})
