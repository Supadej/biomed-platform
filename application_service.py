"""Application specialist work orders with scoped Helpdesk referrals and audit."""
import datetime,json,uuid,sqlite3,csv,io
from urllib.parse import urlparse,parse_qs
import permissions_policy as policy
import service_referrals
import application_references as references
import application_job_extras as extras
STATUSES={'Scheduled','In progress','Follow-up','Completed','Cancelled'}
TYPES={'Installation support','Application training','Method validation','Troubleshooting','Optimization','Demonstration','Customer follow-up','Others'}
def initialize(c):
 c.executescript('CREATE TABLE IF NOT EXISTS application_service_records(id TEXT PRIMARY KEY,payload TEXT NOT NULL,version INTEGER NOT NULL,deleted INTEGER NOT NULL DEFAULT 0);CREATE TABLE IF NOT EXISTS application_service_audit(id INTEGER PRIMARY KEY,at TEXT NOT NULL,actor TEXT NOT NULL,action TEXT NOT NULL,record_id TEXT NOT NULL,payload TEXT NOT NULL);')
def migrate(c):
 references.initialize(c);choices=references.customers(c)
 if c.execute("SELECT 1 FROM application_reference_migrations WHERE name='application-jobs-v2'").fetchone():return
 import document_numbers
 for ident,payload in c.execute('SELECT id,payload FROM application_service_records').fetchall():
  r=json.loads(payload);r['topic']=r.get('title','');person=c.execute('SELECT name FROM accounts WHERE user_id=?',(r.get('specialist'),)).fetchone();r['specialistName']=person[0] if person else r.get('specialist','');r['legacyReference']=r.get('reference','');r['customerId']=next((x['id'] for x in choices if x['name'].casefold()==r.get('customer','').casefold()),'');r['products']=[r['productLine']] if r.get('productLine') else []
  day=document_numbers.bangkok_day()
  try:day=datetime.datetime.fromisoformat(r['createdAt']).astimezone(datetime.timezone(datetime.timedelta(hours=7))).date()
  except (KeyError,ValueError,TypeError):pass
  r['reference']=document_numbers.allocate(c,'application-service',ident,'BMDAS',day=day,year_digits=2)
  c.execute('UPDATE application_service_records SET payload=?,version=version+1 WHERE id=?',(json.dumps(r,ensure_ascii=False),ident))
 c.execute("INSERT INTO application_reference_migrations VALUES('application-jobs-v2')")
def uid(actor):return str(actor[4])
def visible(r,actor,perms):
 if policy.visibility.contextual(perms):return policy.visibility.visible(perms,'application_service',r)
 return 'application_service.view_all' in perms or str(r.get('specialist'))==uid(actor) or r.get('createdBy')==uid(actor)
def records(c,actor,perms,from_date="",to_date="",record_id=""):
 policy.need(perms,'application_service.view')
 if from_date and to_date and from_date>to_date:raise ValueError('From date cannot be after To date')
 clauses=[];args=[]
 for key,value,op in [('from',from_date,'>='),('to',to_date,'<=')]:
  if value:
   try:datetime.date.fromisoformat(value)
   except (ValueError,TypeError):raise ValueError('Invalid filter date')
   clauses.append("substr(json_extract(payload,'$.start'),1,10)"+op+'?');args.append(value)
 where=' AND '.join(clauses) or '1'
 if record_id:where='('+where+') OR id=?';args.append(record_id)
 return [dict(json.loads(p),version=v) for p,v in c.execute('SELECT payload,version FROM application_service_records WHERE deleted=0 AND ('+where+')',args) if visible(json.loads(p),actor,perms)]
def audit(c,actor,action,r):c.execute('INSERT INTO application_service_audit(at,actor,action,record_id,payload) VALUES(?,?,?,?,?)',(datetime.datetime.now(datetime.timezone.utc).isoformat(),str(actor[0]),action,r['id'],json.dumps(r,ensure_ascii=False)))
def save(c,actor,perms,record):
 policy.need(perms,'application_service.view');raw=dict(record)
 old=c.execute('SELECT payload,version,deleted FROM application_service_records WHERE id=?',(raw.get('id',''),)).fetchone()
 if raw.get('id') and (not old or old[2] or not visible(json.loads(old[0]),actor,perms)):raise policy.PermissionDenied('Application service record unavailable')
 policy.need(perms,'application_service.edit' if old else 'application_service.create')
 if old and raw.get('version')!=old[1]:raise ValueError('Record changed. Refresh before saving.')
 prior=json.loads(old[0]) if old else {};r={}
 for key in ['title','customer','contact','productLine','instrumentId','specialist','serviceType','status','start','end','purpose','workPerformed','result','followUp','followUpDate','customerFeedback','topic','customerId']:
  value=raw.get(key,'')
  if not isinstance(value,str) or len(value)>10000:raise ValueError('Invalid field: '+key)
  r[key]=value.strip()
 r['topic']=raw.get('topic',raw.get('title',prior.get('topic',''))).strip();r['title']=r['topic']
 customer=next((x for x in references.customers(c) if x['id']==r['customerId']),None)
 if not customer or not customer['active'] and r['customerId']!=prior.get('customerId'):raise ValueError('Select an active customer / institution from the reference list')
 r['customer']=customer['name']
 if not r['specialist'] or not r['start']:raise ValueError('Customer, specialist and start date & time are required')
 products=raw.get('products',prior.get('products',[]))
 if not isinstance(products,list) or len(products)>100 or any(not isinstance(x,str) or not x or len(x)>200 for x in products):raise ValueError('Select valid products')
 if any(x not in references.products(c) and x not in prior.get('products',[]) for x in products):raise ValueError('Select products from the available list')
 r['products']=list(dict.fromkeys(products));r['productLine']=', '.join(r['products'])
 if r['status'] not in STATUSES or r['serviceType'] not in TYPES:raise ValueError('Choose a valid status and service type')
 for k in ['start','end']:
  if r[k]:
   try:datetime.datetime.strptime(r[k],'%Y-%m-%dT%H:%M')
   except ValueError:raise ValueError('Use a valid date & time for '+k)
 if r['end'] and r['end']<r['start']:raise ValueError('End cannot precede start')
 if r['followUpDate']:
  try:datetime.date.fromisoformat(r['followUpDate'])
  except ValueError:raise ValueError('Use a valid follow-up date')
 if r['status']=='Completed' and (not r['workPerformed'] or not r['result']):raise ValueError('Completed work requires work performed and result')
 if not any(u['id']==r['specialist'] for u in references.specialists(c)):
  if r['specialist']!=prior.get('specialist') or not prior:raise ValueError('Select an active employee with Application Service job responsibilities')
 r['specialistName']=next((u['name'] for u in references.specialists(c) if u['id']==r['specialist']),prior.get('specialistName',r['specialist']))
 if r['specialist']!=uid(actor) and r['specialist']!=prior.get('specialist'):policy.need(perms,'application_service.assign')
 ticket=raw.get('ticketId') or None
 if raw.get('newTicket'):
  if ticket:raise ValueError('Choose an existing ticket or create a new ticket')
  if not isinstance(raw['newTicket'],dict):raise ValueError('Invalid new ticket')
  ticket=service_referrals.create_ticket(c,actor,perms,r,raw['newTicket'])
 if ticket is not None:
  try:ticket=int(ticket)
  except (ValueError,TypeError):raise ValueError('Invalid Helpdesk ticket')
 if str(ticket or '')!=str(prior.get('ticketId') or ''):
  if prior.get('ticketId'):service_referrals.ticket(c,actor,perms,prior['ticketId'])
  if ticket:service_referrals.ticket(c,actor,perms,ticket)
 r['ticketId']=ticket
 if r['instrumentId'] and r['instrumentId']!=prior.get('instrumentId'):
  policy.need(perms,'service.view');policy.need(perms,'service.instruments.view')
  if not c.execute("SELECT 1 FROM fse_records WHERE id=? AND kind='instruments'",(r['instrumentId'],)).fetchone():raise ValueError('Instrument unavailable')
 now=datetime.datetime.now(datetime.timezone.utc).isoformat();r.update(id=prior.get('id') or str(uuid.uuid4()),createdBy=prior.get('createdBy',uid(actor)),createdAt=prior.get('createdAt',now),updatedAt=now,updatedBy=uid(actor))
 import document_numbers
 r['reference']=prior.get('reference') or document_numbers.allocate(c,'application-service',r['id'],'BMDAS',year_digits=2)
 if prior.get('legacyReference'):r['legacyReference']=prior['legacyReference']
 extras.validate(r,raw,prior);extras.signature(actor,r,raw,prior);extras.calendar(c,actor,perms,r,prior)
 version=old[1]+1 if old else 1
 c.execute('INSERT INTO application_service_records VALUES(?,?,?,0) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload,version=excluded.version',(r['id'],json.dumps(r,ensure_ascii=False),version));audit(c,actor,'updated' if old else 'created',r)
 if ticket!=prior.get('ticketId'):
  import crm_api
  for ident,action in [(prior.get('ticketId'),'unlink application service'),(ticket,'link application service')]:
   if ident:crm_api.audit(c,actor,'HelpDeskTickets',ident,action,{'applicationServiceId':r['id'],'reference':r['reference']})
 return dict(r,version=version)
def delete(c,actor,perms,ident,version):
 policy.need(perms,'application_service.delete');r=next((x for x in records(c,actor,perms) if x['id']==ident),None)
 if not r:raise policy.PermissionDenied('Application service record unavailable')
 if r['version']!=version:raise ValueError('Record changed. Refresh before deleting.')
 extras.calendar(c,actor,perms,dict(r,calendarEnabled=False),r)
 c.execute('UPDATE application_service_records SET deleted=1,version=version+1 WHERE id=?',(ident,));audit(c,actor,'deleted',r)
def handle(h,method,connect,session,permissions,origin):
 actor=session(h)
 if not actor:return h.reply(401,{'error':'Sign in through Staff Portal'})
 try:
  perms=permissions(actor);policy.need(perms,'application_service.view')
  with connect() as c:
   if method=='GET':
    q=parse_qs(urlparse(h.path).query);ticket=q.get('ticket',[''])[0]
    if ticket:service_referrals.ticket(c,actor,perms,ticket)
    rows=records(c,actor,perms,q.get('from',[''])[0],q.get('to',[''])[0],q.get('record',[''])[0])
    if ticket:rows=[r for r in rows if str(r.get('ticketId'))==ticket]
    staff=references.specialists(c)
    instruments=[dict(json.loads(p),id=i) for i,p in c.execute("SELECT id,payload FROM fse_records WHERE kind='instruments'")] if {'service.view','service.instruments.view'}<=set(perms) else []
    return h.reply(200,{'records':sorted(rows,key=lambda r:r['start'],reverse=True),'specialists':staff,'customers':references.customers(c),'products':references.products(c),'instruments':instruments,'tickets':service_referrals.visible_tickets(c,actor,perms),'permissions':sorted(perms),'userId':uid(actor),'audit':[dict(at=at,actor=a,action=act,recordId=i) for at,a,act,i in c.execute('SELECT at,actor,action,record_id FROM application_service_audit ORDER BY id DESC LIMIT 500') if i in {r['id'] for r in rows}] if 'application_service.audit' in perms else []})
   if not origin(h):return h.reply(403,{'error':'Invalid origin'})
   n=int(h.headers.get('Content-Length','0'))
   if not 0<n<1_000_000:raise ValueError('Invalid request size')
   body=json.loads(h.rfile.read(n))
   if not isinstance(body,dict):raise ValueError('Invalid request')
   c.execute('BEGIN IMMEDIATE')
   if body.get('action')=='save':result={'record':save(c,actor,perms,body.get('record',{}))}
   elif body.get('action')=='customers':result={'customers':references.change(c,actor,perms,body)}
   elif body.get('action')=='delete':delete(c,actor,perms,body.get('id'),body.get('version'));result={'deleted':True}
   elif body.get('action')=='export':
    policy.need(perms,'application_service.export');rows=records(c,actor,perms);ids=body.get('ids',[])
    if not isinstance(ids,list):raise ValueError('Invalid export selection')
    fields=['reference','topic','customer','productLine','specialist','serviceType','status','start','end','purpose','workPerformed','result','followUp','followUpDate','ticketId','createdAt','updatedAt'];f=io.StringIO();w=csv.writer(f);w.writerow(fields)
    for r in rows:
     if r['id'] in ids:w.writerow([("'"+str(r.get(k,''))) if str(r.get(k,'')).startswith(('=','+','-','@','\t','\r')) else r.get(k,'') for k in fields])
    result={'csv':f.getvalue()}
   else:raise ValueError('Unknown action')
   c.commit();return h.reply(200,result)
 except policy.PermissionDenied as e:return h.reply(403,{'error':str(e)})
 except (ValueError,KeyError,TypeError,sqlite3.IntegrityError) as e:return h.reply(400,{'error':str(e)})
