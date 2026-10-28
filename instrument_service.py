"""Authenticated FSE register, optimistic locking, source import and audit."""
import json,uuid,datetime,sqlite3,math
from pathlib import Path
import permissions_policy as policy
KINDS={'instruments','jobs','movements','parts','replacements','contracts'}
def initialize(c):
 c.execute('CREATE TABLE IF NOT EXISTS service_column_preferences(account_id TEXT NOT NULL,kind TEXT NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(account_id,kind))')
 c.executescript('CREATE TABLE IF NOT EXISTS fse_records(id TEXT PRIMARY KEY,kind TEXT NOT NULL,payload TEXT NOT NULL,version INTEGER NOT NULL); CREATE TABLE IF NOT EXISTS fse_audit(id INTEGER PRIMARY KEY,at TEXT,actor TEXT,action TEXT,record_id TEXT,detail TEXT);')
def rows(c):return [dict(json.loads(p),version=v) for p,v in c.execute('SELECT payload,version FROM fse_records')]
def audit(c,actor,action,r):c.execute('INSERT INTO fse_audit(at,actor,action,record_id,detail) VALUES(?,?,?,?,?)',(datetime.datetime.now(datetime.timezone.utc).isoformat(),str(actor[4]),action,r.get('id'),json.dumps(r,ensure_ascii=False)))
def save(c,actor,perms,r,importing=False):
 policy.need(perms,'service.edit');r=dict(r);kind=r.get('kind')
 if kind not in KINDS:raise ValueError('Unknown service record type')
 for key,v in r.items():
  if key in ('date','scheduledDate','followUpDate','lastMaintenance','maintenanceDue','lastVisit','installationDate','warrantyEnd','startDate','endDate','nextMaintenance') and v:
   try:datetime.date.fromisoformat(v)
   except (ValueError,TypeError):
    if not importing:raise ValueError('Use YYYY-MM-DD for '+key)
  if key in ('qty','unitCost','laborHours','serviceAmount','amount','pmVisits','pmIntervalMonths') and v not in ('',None):
   try:n=float(v)
   except (ValueError,TypeError):n=float('nan')
   if (not math.isfinite(n) or n<0) and not importing:raise ValueError('Invalid nonnegative number: '+key)
 old=c.execute('SELECT payload,version FROM fse_records WHERE id=?',(r.get('id',''),)).fetchone()
 if not importing:
  policy.need(perms,'service.'+kind+'.view');policy.need(perms,'service.'+kind+('.edit' if old else '.create'))
 if old and json.loads(old[0]).get('kind')!=kind:raise ValueError('Record type cannot be changed')
 if old and r.get('version')!=old[1]:raise ValueError('Record changed; refresh before saving')
 if kind=='instruments':
  if not str(r.get('serial','')).strip():raise ValueError('Serial number required')
  if any(x['kind']=='instruments' and x['id']!=r.get('id') and x.get('serial','').strip().casefold()==r['serial'].strip().casefold() for x in rows(c)):raise ValueError('Serial number already exists')
 if kind in ('jobs','movements','replacements','contracts'):
  inst=c.execute("SELECT payload FROM fse_records WHERE id=? AND kind='instruments'",(r.get('instrumentId',''),)).fetchone()
  if not inst and not importing:raise ValueError('Select an instrument')
 if kind=='replacements':
  try:q=float(r.get('qty',0))
  except (TypeError,ValueError):q=0
  if not 0<q<1e9 and not importing:raise ValueError('Positive replacement quantity required')
 if kind=='movements' and not importing and (not r.get('date') or not r.get('toLocation')):raise ValueError('Movement date and destination required')
 if kind=='jobs' and not importing and r.get('status')=='Completed' and (not r.get('date') or not r.get('description') or not r.get('engineer')):raise ValueError('Completion needs service date, engineer and report description')
 for key in ('customerId','productId','invoiceId'):
  if r.get(key):
   if not importing:policy.need(perms,'is.invoice.view' if key=='invoiceId' else 'is.master-customers.view' if key=='customerId' else 'is.master-products.view')
   category='customers' if key=='customerId' else 'products'
   found=c.execute('SELECT 1 FROM documents WHERE id=? AND kind=?',(r[key],'invoice')).fetchone() if key=='invoiceId' else c.execute('SELECT 1 FROM masters WHERE category=? AND id=?',(category,r[key])).fetchone()
   if not found:raise ValueError('Linked Biomed IS record does not exist: '+key)
 r['id']=r.get('id') or str(uuid.uuid4());r.pop('version',None)
 if kind=='jobs' and not importing:
  import job_numbers
  r['jobNo']=job_numbers.reserve(c,'service:'+r['id'],r.get('jobNo'))
 c.execute('INSERT OR REPLACE INTO fse_records VALUES(?,?,?,?)',(r['id'],kind,json.dumps(r,ensure_ascii=False),(old[1]+1) if old else 1));audit(c,actor,'edit' if old else 'create',r)
 if not importing and kind in ('movements','jobs'):
  raw=c.execute("SELECT payload,version FROM fse_records WHERE id=?",(r['instrumentId'],)).fetchone();i=json.loads(raw[0])
  if kind=='movements':
   latest=sorted([x for x in rows(c) if x['kind']=='movements' and x.get('instrumentId')==i['id']],key=lambda x:x.get('date',''))[-1]
   i['location']=latest.get('toLocation',i.get('location',''))
  elif r.get('status')=='Completed':
   i['lastVisit']=max(i.get('lastVisit',''),r.get('date',''))
   if r.get('jobType') in ('Preventive Maintenance','Maintenance'):
    i['lastMaintenance']=max(i.get('lastMaintenance',''),r.get('date',''))
    if r.get('nextMaintenance'):i['maintenanceDue']=r['nextMaintenance']
  c.execute('UPDATE fse_records SET payload=?,version=version+1 WHERE id=?',(json.dumps(i,ensure_ascii=False),i['id']));audit(c,actor,'service-summary-update',i)
 return r['id']
def handle(h,method,connect,session,permissions,origin):
 actor=session(h)
 if not actor:return h.reply(401,{'error':'Sign in through Staff Portal'})
 try:
  perms=permissions(actor);policy.need(perms,'service.view')
  with connect() as c:
   if method=='GET':
    data=[r for r in rows(c) if 'service.'+r['kind']+'.view' in perms];masters={}
    for category,key in [('customers','is.master-customers.view'),('products','is.master-products.view')]:
     masters[category]=[dict(json.loads(p),id=i) for i,p in c.execute('SELECT id,payload FROM masters WHERE category=?',(category,))] if key in perms else []
    masters['invoices']=[dict(id=i,ref=ref) for i,ref in c.execute("SELECT id,reference FROM documents WHERE kind='invoice'")] if 'is.invoice.view' in perms else []
    return h.reply(200,{'columnPreferences':{k:json.loads(p) for k,p in c.execute('SELECT kind,payload FROM service_column_preferences WHERE account_id=?',(str(actor[0]),))},'records':data,'masters':masters,'helpdesk':linked_tickets(c,actor,perms) if 'service.instruments.view' in perms else [],'permissions':sorted(perms),'audit':[dict(id=i,at=at,actor=a,action=act,recordId=r) for i,at,a,act,r in c.execute('SELECT id,at,actor,action,record_id FROM fse_audit ORDER BY id DESC LIMIT 100')] if 'service.audit' in perms else []})
   if not origin(h):return h.reply(403,{'error':'Invalid origin'})
   n=int(h.headers.get('Content-Length','0'))
   if not 0<n<10_000_000:raise ValueError('Invalid request size')
   body=json.loads(h.rfile.read(n));action=body.get('action');c.execute('BEGIN IMMEDIATE')
   if action=='columns':
    kind=body.get('kind');columns=body.get('columns')
    if kind not in KINDS:raise ValueError('Unknown service tab')
    policy.need(perms,'service.'+kind+'.view')
    allowed={'brand','model','location','customer','serial','brandModel','serialBrandModel','customerLocation','partDescription','daysDue','jobNo','jobType','status','fromLocation','toLocation','date','catalogueNo','name','qty','startDate','endDate','maintenanceDue','type','assetType','lastMaintenance','lastVisit','instrumentSoftware','computerSoftware','engineer','description','warrantyEnd','installationDate','scheduledDate','followUpDate','nextMaintenance','laborHours','serviceAmount','currency','contractNo','coverage','amount','comment','changeNo','unitCost','invoiceRef','diagnosis','actionTaken','result','customerAcceptance','pmIntervalMonths','pmVisits','partChangeRef','stockDocumentId','serialAlias'}
    if not isinstance(columns,list) or not 1<=len(columns)<=50:raise ValueError('Select at least one column')
    keys=set()
    for col in columns:
     if not isinstance(col,dict) or col.get('key') not in allowed or col['key'] in keys:raise ValueError('Invalid or repeated column')
     if not isinstance(col.get('label'),str) or not 1<=len(col['label'].strip())<=100:raise ValueError('Column headings must have 1–100 characters')
     keys.add(col['key'])
    c.execute('INSERT OR REPLACE INTO service_column_preferences VALUES(?,?,?)',(str(actor[0]),kind,json.dumps(columns,ensure_ascii=False)))
    result={'saved':True}
   elif action in ('preview','import'):

    policy.need(perms,'service.manage');policy.need(perms,'service.import');seed=json.loads((Path(__file__).parent/'reference'/'service-import.json').read_text());existing={r['id'] for r in rows(c)};pending=[r for r in seed['records'] if r['id'] not in existing]
    if action=='preview':return h.reply(200,{'counts':{k:sum(r['kind']==k for r in pending) for k in KINDS},'warnings':seed['warnings'],'existing':len(existing)})
    policy.need(perms,'service.edit')
    for r in pending:save(c,actor,perms,r,True)
    result={'imported':len(pending),'warnings':seed['warnings']}
   elif action=='export':
    kind=body.get('kind')
    if kind not in KINDS:raise ValueError('Unknown record type')
    policy.need(perms,'service.export');policy.need(perms,'service.'+kind+'.view');policy.need(perms,'service.'+kind+'.export')
    result={'records':[r for r in rows(c) if r['kind']==kind]};audit(c,actor,'export',{'kind':kind})
   elif action=='save':result={'id':save(c,actor,perms,body['record'])}
   else:raise ValueError('Unknown service operation')
  return h.reply(200,result)
 except policy.PermissionDenied as e:return h.reply(403,{'error':str(e)})
 except (ValueError,KeyError,TypeError,sqlite3.IntegrityError) as e:return h.reply(400,{'error':str(e)})

def match_instruments(c,serial):
 """Exact serial/explicit alias matching; leading zeros and punctuation are significant."""
 key=str(serial or '').strip().casefold()
 if not key:return []
 return [r for r in rows(c) if r['kind']=='instruments' and key in {str(r.get(f,'')).strip().casefold() for f in ['serial','serialAlias']}]

def linked_tickets(c,actor,perms):
 import crm_api as crm
 if not {'crm_view','crm.tickets.view'}.issubset(perms):return []
 try:uid=crm.user_id(c,actor)
 except policy.PermissionDenied:return []
 result=[]
 for r in crm.rows(c,'HelpDeskTickets'):
  if not crm.visible(c,perms,'HelpDeskTickets',r,uid):continue
  matches=match_instruments(c,r.get('SerialNumber'))
  if len(matches)==1:result.append(dict(instrumentId=matches[0]['id'],id=r['Id'],title=r.get('Title'),serial=r.get('SerialNumber'),problem=r.get('Problem'),solution=r.get('Solution'),status=r.get('Status'),jobNo=r.get('JobNumber'),due=r.get('DueDate')))
 return result

def seed_workbook(c):
 """One-time additive workbook migration; never overwrite operational edits."""
 c.execute('CREATE TABLE IF NOT EXISTS fse_migrations(name TEXT PRIMARY KEY,applied_at TEXT,detail TEXT)')
 name='fse-jul2026-v1'
 if c.execute('SELECT 1 FROM fse_migrations WHERE name=?',(name,)).fetchone():return
 seed=json.loads((Path(__file__).parent/'reference'/'service-import.json').read_text());current=rows(c);existing={r['id'] for r in current};remap={};count=0
 actor=('migration','','Workbook migration','System Admin','system:workbook');perms={'service.edit','service.view'}
 for original in sorted(seed['records'],key=lambda r:0 if r['kind']=='instruments' else 1):
  r=dict(original)
  if r['id'] in existing:continue
  if r['kind']=='instruments':
   matches=[x for x in current if x['kind']=='instruments' and str(x.get('serial','')).strip().casefold()==r['serial'].strip().casefold()]
   if matches:remap[r['id']]=matches[0]['id'];continue
  if r.get('instrumentId') in remap:r['instrumentId']=remap[r['instrumentId']]
  save(c,actor,perms,r,True);existing.add(r['id']);current.append(r);count+=1
 c.execute('INSERT INTO fse_migrations VALUES(?,?,?)',(name,datetime.datetime.now(datetime.timezone.utc).isoformat(),json.dumps({'inserted':count,'reusedInstruments':len(remap),'warnings':seed['warnings']})))
