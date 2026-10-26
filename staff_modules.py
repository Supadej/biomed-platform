"""Native Staff Portal CRM functions. Persisted in the SAME configured SQLite database.
Independent of the legacy CRM API; legacy rows stay untouched and are displayed via migration.
"""
import json,uuid,datetime,sqlite3
MODULES={'calendar':'Events','sales-plan':'Leads','project-activity':'Projects','external-helpdesk':'HelpDeskTickets'}
EXTRA={'project-activity':'ProjectActivity'}
OLD_FIELDS={
 'calendar':{'title':['Title','EventName','Name','Subject'],'details':['Description','Note','Detail'],'start':['StartDate','Start','StartTime','Date'],'end':['EndDate','End','EndTime'],'customer':['OrganizationName','Customer','Organization'],'owner':['Owner','UserId'],'status':['Status']},
 'sales-plan':{'title':['LeadName','Name','Title','Subject'],'customer':['OrganizationName','Customer','Organization'],'value':['Amount','Value','ExpectedRevenue'],'status':['Status','PipelineName'],'owner':['Owner','UserId'],'details':['Description','Note']},
 'project-activity':{'title':['ProjectName','Name','Title'],'customer':['OrganizationName','Customer','Organization'],'status':['Status'],'owner':['Owner','UserId'],'details':['Description','Detail'],'start':['StartDate'],'end':['EndDate']},
 'external-helpdesk':{'title':['Subject','Title','Name'],'customer':['OrganizationName','Customer','Organization'],'status':['Status'],'owner':['Owner','UserId'],'details':['Description','Detail','Problem']}
}
FIELDS={'calendar':['title','details','start','end','customer','location','owner','status','priority','participants','source'], 'sales-plan':['title','customer','contact','owner','status','priority','value','target','actual','forecastDate','details','source','sourceId','incentiveScheme','incentiveEligible'], 'project-activity':['title','customer','owner','start','end','status','priority','details','progress','members','activities'], 'external-helpdesk':['title','customer','contact','owner','status','priority','category','product','details','resolution','dueDate','activities']}
STATUS={'calendar':['Scheduled','Completed','Cancelled'],'sales-plan':['New','Qualified','Proposal','Negotiation','Won','Lost'],'project-activity':['Planning','In progress','On hold','Completed','Cancelled'],'external-helpdesk':['Open','In progress','Waiting','Resolved','Closed']}
PERM={'calendar':'dashboard','sales-plan':'pipeline','project-activity':'tasks','external-helpdesk':'helpdesk'}
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def init(c):
 c.execute('''CREATE TABLE IF NOT EXISTS staff_crm_items(module TEXT NOT NULL,id TEXT NOT NULL PRIMARY KEY,payload TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,created_by TEXT NOT NULL,deleted INTEGER NOT NULL DEFAULT 0,UNIQUE(module,id))''')
 c.execute('CREATE INDEX IF NOT EXISTS staff_crm_module_idx ON staff_crm_items(module,deleted,updated_at)')
 c.execute('''CREATE TABLE IF NOT EXISTS staff_crm_audit(id INTEGER PRIMARY KEY AUTOINCREMENT,module TEXT NOT NULL,record_id TEXT NOT NULL,actor TEXT NOT NULL,action TEXT NOT NULL,at TEXT NOT NULL,details TEXT NOT NULL)''')
 c.execute('''CREATE TABLE IF NOT EXISTS staff_crm_import(module TEXT NOT NULL,legacy_id INTEGER NOT NULL,record_id TEXT NOT NULL,PRIMARY KEY(module,legacy_id))''')
 # Idempotent import; does not remove or modify a single legacy record.
 if not c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='crm_records'").fetchone():return
 for module,entity in MODULES.items():
  for lid,payload in c.execute('SELECT id,payload FROM crm_records WHERE entity=? AND deleted=0',(entity,)).fetchall():
   if c.execute('SELECT 1 FROM staff_crm_import WHERE module=? AND legacy_id=?',(module,lid)).fetchone():continue
   try:old=json.loads(payload)
   except (ValueError,TypeError):continue
   result={}
   for field,choices in OLD_FIELDS[module].items():
    for key in choices:
     if old.get(key) not in (None,''):
      result[field]=old[key];break
   result.setdefault('title',f'{entity} #{lid}')
   result['legacyId']=lid;result['legacyEntity']=entity;result['legacyData']=old
   rid=str(uuid.uuid4());t=now()
   c.execute('INSERT INTO staff_crm_items VALUES(?,?,?,?,?,?,0)',(module,rid,json.dumps(result,ensure_ascii=False),t,t,'legacy-import'))
   c.execute('INSERT INTO staff_crm_import VALUES(?,?,?)',(module,lid,rid))

def authorize(module,perms,write=False):
 if module not in MODULES:raise ValueError('Unknown Staff Portal function')
 old=PERM[module]
 allow={'calendar':{'dashboard','portal.dashboard.view','crm.events.view'},'sales-plan':{'pipeline','portal.pipeline.view','crm.leads.view'},'project-activity':{'tasks','portal.tasks.view','crm.projects.view'},'external-helpdesk':{'helpdesk','portal.helpdesk.view','crm.tickets.view'}}
 if not (perms & allow[module] or 'System Admin' in perms):raise PermissionError('Access to this Staff Portal function is not enabled for your role')
 if write:
  # First-stage access follows existing Staff Portal module permission. The original
  # module is not required, and role-specific restrictions can be added in Staff Portal.
  pass

def clean(module,data,prior=None):
 if not isinstance(data,dict):raise ValueError('Record must be an object')
 old=dict(prior or {});allowed=set(FIELDS[module]);special={'legacyId','legacyEntity','legacyData','generated','linkedAt','incentiveLinked'}
 for k,v in data.items():
  if k not in allowed:continue
  if isinstance(v,(dict,list)):
   if k not in ('activities','members','participants'):raise ValueError('Invalid field: '+k)
   if len(json.dumps(v))>30000:raise ValueError('Field too large: '+k)
  elif v is not None and not isinstance(v,(str,int,float,bool)):raise ValueError('Invalid field: '+k)
  elif isinstance(v,str) and len(v)>15000:raise ValueError('Field too long: '+k)
  old[k]=v
 if not str(old.get('title') or '').strip():raise ValueError('Title is required')
 if module=='sales-plan':
  target=float(old.get('target') or 0);actual=float(old.get('actual') or 0)
  if target<0 or actual<0:raise ValueError('Target and actual must not be negative')
  old['attainment']=round(actual/target*100,2) if target else 0
  # Server-enforced; not merely a disabled button.
  if old.get('incentiveScheme') and old['attainment']<100:raise ValueError('Incentive scheme requires at least 100% target attainment')
  old['incentiveEligible']=bool(target>0 and old['attainment']>=100)
 old.setdefault('status',STATUS[module][0]);return old

def audit(c,module,rid,actor,action,detail):
 c.execute('INSERT INTO staff_crm_audit(module,record_id,actor,action,at,details) VALUES(?,?,?,?,?,?)',(module,rid,str(actor[0]),action,now(),json.dumps(detail,ensure_ascii=False)))

def list_items(c,module):
 return [dict(json.loads(payload),id=rid,createdAt=created,updatedAt=updated) for rid,payload,created,updated in c.execute('SELECT id,payload,created_at,updated_at FROM staff_crm_items WHERE module=? AND deleted=0 ORDER BY updated_at DESC LIMIT 2000',(module,))]

def source_documents(c):
 kinds={'quotation','customer-order','order','sales-order','invoice'}
 results=[]
 for (ident,kind,ref,status,payload) in c.execute('SELECT id,kind,reference,status,payload FROM documents WHERE kind IN (?,?,?,?,?) ORDER BY rowid DESC LIMIT 1000',tuple(kinds)):
  try:d=json.loads(payload)
  except (TypeError,ValueError):d={}
  results.append({'id':str(ident),'kind':kind,'reference':ref or d.get('ref') or ident,'status':status,'customer':d.get('customerName') or d.get('customer') or d.get('customerId') or '', 'value':d.get('total') or d.get('grandTotal') or d.get('amount') or 0})
 return results

def handle(c,module,action,method,data,perms,actor,query):
 authorize(module,perms,method!='GET')
 if method=='GET':
  if action=='list':return {'records':list_items(c,module),'statuses':STATUS[module]}
  if action=='sources' and module=='sales-plan':return {'documents':source_documents(c)}
  if action=='audit':return {'audit':[dict(zip(['action','at','details'],r)) for r in c.execute('SELECT action,at,details FROM staff_crm_audit WHERE module=? ORDER BY id DESC LIMIT 200',(module,))]}
  raise ValueError('Invalid read operation')
 if action=='create':
  record=clean(module,data);rid=str(uuid.uuid4());t=now();c.execute('INSERT INTO staff_crm_items VALUES(?,?,?,?,?,?,0)',(module,rid,json.dumps(record,ensure_ascii=False),t,t,str(actor[0])));audit(c,module,rid,actor,'create',record);return {'id':rid,'record':record}
 if action=='generate' and module=='sales-plan':
  docs=source_documents(c);requested=set(str(i) for i in data.get('ids',[]));created=0;skipped=0
  for doc in docs:
   if doc['id'] not in requested:continue
   if any(str(r.get('sourceId'))==doc['id'] and r.get('source')==doc['kind'] for r in list_items(c,module)):skipped+=1;continue
   new={'title':str(doc['reference']),'customer':doc['customer'],'status':'New','value':doc['value'],'source':doc['kind'],'sourceId':doc['id'],'generated':True}
   handle(c,module,'create','POST',new,perms,actor,{})
   created+=1
  return {'created':created,'skipped':skipped}
 rid=str(data.get('id',''))
 row=c.execute('SELECT payload FROM staff_crm_items WHERE module=? AND id=? AND deleted=0',(module,rid)).fetchone()
 if not row:raise ValueError('Record not found')
 old=json.loads(row[0])
 if action=='update':
  new=clean(module,data,old);c.execute('UPDATE staff_crm_items SET payload=?,updated_at=? WHERE module=? AND id=?',(json.dumps(new,ensure_ascii=False),now(),module,rid));audit(c,module,rid,actor,'update',data);return {'id':rid,'record':new}
 if action=='delete':
  c.execute('UPDATE staff_crm_items SET deleted=1,updated_at=? WHERE module=? AND id=?',(now(),module,rid));audit(c,module,rid,actor,'delete',{});return {'deleted':True}
 raise ValueError('Invalid action')
