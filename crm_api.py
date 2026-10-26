"""Cookie-authenticated compatibility API for the supplied Biomed ERP browser client.
Original schema names are retained; password/permission authority stays in Staff Portal.
"""
import json,re,math,secrets,datetime,hashlib,html
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
import permissions_policy as policy
SCHEMA=json.loads((Path(__file__).parent/'crm-schema.json').read_text())
MODULES={'Users':'users','Groups':'groups','SaleAreas':'territories','Products':'products','InventoryBrands':'brands','InventoryProducts':'inventory','Stocks':'stock','Contacts':'contacts','Organizations':'organizations','Departments':'departments','BillingInformations':'billing','CRMPipelines':'pipelines','Leads':'leads','Events':'events','Projects':'projects','ProjectPipeline':'project_stages','ProjectActivity':'activities','HelpDeskTickets':'tickets','HelpDeskItems':'ticket_items','HelpDeskPipelines':'ticket_stages','Targets':'targets','Logs':'logs','Shortcuts':'shortcuts'}
JOINS={'LeadUsers':('Leads','LeadId','Users','UserId'),'LeadContacts':('Leads','LeadId','Contacts','ContactId'),'EventUsers':('Events','EventId','Users','UserId'),'EventContacts':('Events','EventId','Contacts','ContactId'),'EventProducts':('Events','EventId','Products','ProductId'),'ProjectActivityUsers':('ProjectActivity','ProjectActivityId','Users','UserId'),'ProjectActivityContacts':('ProjectActivity','ProjectActivityId','Contacts','ContactId'),'UserHelpdesks':('HelpDeskTickets','HelpdeskTicketId','Users','UserId'),'ContactHelpdesks':('HelpDeskTickets','HelpdeskTicketId','Contacts','ContactId'),'ProductUsers':('Users','UserId','Products','ProductId'),'SaleAreaUsers':('Users','UserId','SaleAreas','SaleAreaId'),'GroupUsers':('Groups','GroupId','Users','UserId')}
ALIASES={'users':'Users','groups':'Groups','saleareas':'SaleAreas','products':'Products','contacts':'Contacts','organizations':'Organizations','departments':'Departments','billinginformations':'BillingInformations','targets':'Targets','log':'Logs','logs':'Logs','shortcuts':'Shortcuts','v2/crm/pipelines':'CRMPipelines','v2/crm/leads':'Leads','v2/event':'Events','events':'Events','v2/project/activities':'ProjectActivity','v2/project/pipelines':'ProjectPipeline','v2/project':'Projects','v2/helpdesk/pipeline':'HelpDeskPipelines','v2/helpdesk/tickets':'HelpDeskTickets','v2/helpdesk/ticket':'HelpDeskTickets','v2/helpdesk/item':'HelpDeskItems','v2/product/brands':'InventoryBrands','v2/product/inventory':'InventoryProducts','v2/product/stock':'Stocks','v2/product':'Products'}
LEGACY_PERMS={1:('user_manage','users','edit'),2:('user_permission_manage','roles','edit'),3:('lead_creation','leads','create'),4:('lead_manage','leads','edit'),5:('contact_manage','contacts','edit'),6:('event_manage','events','edit'),7:('project_manage','projects','edit'),8:('log_manage','logs','edit'),9:('helpdesk_manage','tickets','edit'),10:('crm_access','dashboard','view'),11:('project_access','projects','create'),12:('event_access','events','create'),13:('contact_access','contacts','export'),18:('helpdesk_access','tickets','view'),19:('inventory_access','inventory','view'),20:('brand_manage','brands','edit'),21:('product_manage','inventory','edit'),22:('stock_manage','stock','edit')}
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def dump(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'),allow_nan=False)
def initialize(c):
 c.executescript('''CREATE TABLE IF NOT EXISTS crm_records(entity TEXT NOT NULL,id INTEGER NOT NULL,payload TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1,deleted INTEGER NOT NULL DEFAULT 0,PRIMARY KEY(entity,id));
 CREATE TABLE IF NOT EXISTS crm_identity(portal_user_id TEXT PRIMARY KEY,crm_user_id INTEGER NOT NULL UNIQUE);
 CREATE TABLE IF NOT EXISTS crm_audit(id INTEGER PRIMARY KEY AUTOINCREMENT,at TEXT NOT NULL,actor TEXT NOT NULL,entity TEXT NOT NULL,record_id INTEGER,action TEXT NOT NULL,detail TEXT NOT NULL);
 CREATE TABLE IF NOT EXISTS crm_files(id TEXT PRIMARY KEY,name TEXT NOT NULL,mime TEXT NOT NULL,content BLOB NOT NULL,owner TEXT NOT NULL);
 CREATE TABLE IF NOT EXISTS crm_links(source TEXT NOT NULL,source_id TEXT NOT NULL,entity TEXT NOT NULL,record_id INTEGER NOT NULL,PRIMARY KEY(source,source_id,entity));
 CREATE TABLE IF NOT EXISTS crm_bridge_config(direction TEXT PRIMARY KEY,payload TEXT NOT NULL,revision INTEGER NOT NULL DEFAULT 1);
 CREATE TABLE IF NOT EXISTS crm_bridge_runs(id INTEGER PRIMARY KEY AUTOINCREMENT,direction TEXT NOT NULL,at TEXT NOT NULL,actor TEXT NOT NULL,digest TEXT NOT NULL,result TEXT NOT NULL);''')
 # Seed only workflow labels, never fictional customer, lead or finance records.
 for entity,labels,name in [('CRMPipelines',['New lead','Qualified','Proposal','Negotiation','Won','Lost'],'PipelineName'),('HelpDeskPipelines',['Open','In progress','Waiting','Resolved'],'Name')]:
  if not c.execute('SELECT 1 FROM crm_records WHERE entity=? LIMIT 1',(entity,)).fetchone():
   for i,label in enumerate(labels):insert(c,entity,{name:label,'Order':i+1})
def raw(c,entity,id):
 r=c.execute('SELECT payload FROM crm_records WHERE entity=? AND id=? AND deleted=0',(entity,id)).fetchone();return json.loads(r[0]) if r else None
def rows(c,entity):return [json.loads(r[0]) for r in c.execute('SELECT payload FROM crm_records WHERE entity=? AND deleted=0 ORDER BY id',(entity,))]
def next_id(c,entity):return c.execute('SELECT COALESCE(MAX(id),0)+1 FROM crm_records WHERE entity=?',(entity,)).fetchone()[0]
def insert(c,entity,data):
 id=next_id(c,entity);record={k:None for k in SCHEMA.get(entity,{}).get('fields',{}) if k.lower() not in ['password','username']};record.update(data);record['Id']=id
 c.execute('INSERT INTO crm_records(entity,id,payload) VALUES(?,?,?)',(entity,id,dump(record)));return record

def update(c,entity,id,data):
 prior=raw(c,entity,id)
 if not prior:raise ValueError('Record not found')
 prior.update(data);prior['Id']=id;c.execute('UPDATE crm_records SET payload=?,version=version+1 WHERE entity=? AND id=?',(dump(prior),entity,id));return prior

def bind_users(c):
 row=c.execute("SELECT value FROM workspace WHERE key='biomed_portal_v33_clean'").fetchone();portal=json.loads(row[0]) if row and row[0] else {};profiles=portal.get('users',[])
 for u in profiles:
  pid=str(u.get('id',''))
  if not pid:continue
  r=c.execute('SELECT crm_user_id FROM crm_identity WHERE portal_user_id=?',(pid,)).fetchone();account=c.execute('SELECT name,email,disabled FROM accounts WHERE user_id=? ORDER BY created_at LIMIT 1',(pid,)).fetchone();names=str(account[0] if account else u.get('name','')).split(' ',1);email=account[1] if account else u.get('email','');data={'PortalUserId':pid,'FirstName':names[0],'LastName':names[1] if len(names)>1 else '', 'Email':email,'username':email,'Role':u.get('role',''),'Enabled':not bool(account[2]) if account else u.get('active',True) is not False}
  if r:
   current=raw(c,'Users',r[0])
   if any(current.get(k)!=v for k,v in data.items()):update(c,'Users',r[0],data)
  else:
   crm=insert(c,'Users',data);c.execute('INSERT INTO crm_identity VALUES(?,?)',(pid,crm['Id']))
 return portal

def need(perms,module,action='view'):
 policy.need(perms,'crm_view');policy.need(perms,'crm.'+module+'.view')
 if action!='view':policy.need(perms,'crm.'+module+'.'+action)

def user_id(c,actor):
 r=c.execute('SELECT crm_user_id FROM crm_identity WHERE portal_user_id=?',(str(actor[4]),)).fetchone()
 if not r:raise policy.PermissionDenied('Staff Portal user profile is required')
 return r[0]

def audit(c,actor,entity,id,action,data):c.execute('INSERT INTO crm_audit(at,actor,entity,record_id,action,detail) VALUES(?,?,?,?,?,?)',(now(),str(actor[0]),entity,id,action,dump(data)))

def permission_rows(perms):return [{'Id':i,'Type':name,'PermissionKey':name,'Value':3} for i,(name,module,action) in LEGACY_PERMS.items() if 'crm.'+module+'.'+action in perms]

def scoped(perms,entity,record,uid):
 # Entity visibility is grant-controlled. Optional own/team restrictions are enabled per role by withholding view_all.
 module=MODULES.get(entity)
 if entity=='Shortcuts':return record.get('UserId')==uid and 'crm.shortcuts.view' in perms
 if not module or 'crm.'+module+'.view' not in perms:return False
 if module not in ['leads','events','activities','tickets','shortcuts']:return True
 if 'crm.'+module+'.view_all' in perms:return True
 owners=[record.get(k) for k in ['MainUserId','MainUserID','CreatedByUserId','AssignedToUserId','UserId','OwnerId']];owners.extend(record.get('UserIds',[]));return uid in owners

def visible(c,perms,entity,record,uid):
 if not record or not scoped(perms,entity,record,uid):return False
 if entity=='HelpDeskItems':return visible(c,perms,'HelpDeskTickets',raw(c,'HelpDeskTickets',record.get('TicketId')),uid)
 if entity=='Logs':
  for field,target in [('LeadId','Leads'),('EventId','Events'),('ActivityId','ProjectActivity'),('HelpdeskTicketId','HelpDeskTickets')]:
   if record.get(field) and not visible(c,perms,target,raw(c,target,record[field]),uid):return False
 return True

def related_allowed(perms,table):return 'crm.'+MODULES.get(table,'_')+'.view' in perms

def serialize(c,entity,record,perms,uid,depth=0):
 if record is None:return None
 r={k:v for k,v in record.items() if k.lower() not in ['password','passwordhash','salt','permissions','token']}
 if entity=='Stocks':r['Type']='Incoming' if r.get('Type') in [0,'0','Incoming'] else 'Outgoing'
 if entity=='Logs':r['LogId']=r['Id']
 if entity=='Users':
  r['Permissions']=permission_rows(perms) if r['Id']==uid else []
  for key in ['GroupUsers','ProductUsers','SaleAreaUsers']:r[key]=[]
 for fk in SCHEMA.get(entity,{}).get('foreignKeys',[]):
  field,target=fk['field'],fk['table'];id=r.get(field)
  name=re.sub(r'(ID|Id)$','',field)
  if id is not None and depth<2 and related_allowed(perms,target):
   child=raw(c,target,id);r[name]=serialize(c,target,child,perms,uid,depth+1) if child and visible(c,perms,target,child,uid) else None
  else:r.setdefault(name,None)
 # Stable aliases expected by the original browser scripts.
 for src,dst in [('MainCustomer','MainContact'),('CRMPipeline','Pipeline'),('Department','MainDepartment')]:
  if src in r:r.setdefault(dst,r[src])
 if entity=='HelpDeskTickets':r['Description']=r.get('Problem') or r.get('Description') or '';r['CreatedBy']=r.get('CreatedByUser');r['AssignedTo']=r.get('AssignedToUser');r['Product']=r.get('Product');r['UserHelpdesks']=[]
 if depth>=2:return r
 for join,(parent,pfield,target,tfield) in JOINS.items():
  if entity!=parent:continue
  ids=record.get({'Users':'UserIds','Contacts':'ContactIds','Products':'ProductIds','SaleAreas':'SaleAreaIds'}.get(target,'RelatedIds'),[])
  entries=[]
  if related_allowed(perms,target):
   for id in ids:
    rec=raw(c,target,id)
    if rec and visible(c,perms,target,rec,uid):entries.append({pfield:r['Id'],tfield:id,target[:-1] if target!='SaleAreas' else 'SaleArea':serialize(c,target,rec,perms,uid,depth+1)})
  r[join]=entries
  if target in ['Users','Contacts','Products']:r[target]=[next(v for k,v in e.items() if isinstance(v,dict)) for e in entries]
 defaults={'Leads':['Users','Contacts','LeadUsers','LeadContacts','Logs','Events'],'Events':['Users','Contacts','Products','EventUsers','EventContacts','EventProducts','Logs'],'ProjectActivity':['Users','Contacts','ProjectActivityUsers','ProjectActivityContacts','Logs'],'HelpDeskTickets':['Users','Contacts','UserHelpdesks','ContactHelpdesks','HelpDeskItems','Logs']}
 for key in defaults.get(entity,[]):r.setdefault(key,[])
 children={'Projects':[('ProjectPipeline','ProjectId','ProjectPipelines')],'ProjectPipeline':[('ProjectActivity','ProjectPipelineId','ProjectActivities')],'InventoryBrands':[('InventoryProducts','BrandId','InventoryProducts')],'InventoryProducts':[('Stocks','ProductId','Stocks')],'Organizations':[('Departments','OrganizationID','Departments')],'Departments':[('Contacts','DepartmentID','Contacts')],'Contacts':[('BillingInformations','ContactId','BillingInformations')],'HelpDeskTickets':[('HelpDeskItems','TicketId','HelpDeskItems')],'CRMPipelines':[('Leads','CRMPipelineId','Leads')]}
 for child,field,key in children.get(entity,[]):
  r[key]=[serialize(c,child,x,perms,uid,depth+1) for x in rows(c,child) if x.get(field)==r['Id'] and visible(c,perms,child,x,uid)] if related_allowed(perms,child) else []
 if entity=='InventoryProducts':r['StockCount']=sum(float(x.get('Quantity') or 0) for x in rows(c,'Stocks') if x.get('ProductId')==r['Id']) if related_allowed(perms,'Stocks') else r.get('StockCount',0)
 if entity=='ProjectPipeline':r['Activities']=r.get('ProjectActivities',[])
 if entity=='Projects':r['Pipelines']=r.get('ProjectPipelines',[])
 if entity=='Users':
  for key,target,field in [('ProductUsers','Products','ProductId'),('SaleAreaUsers','SaleAreas','SaleAreaId')]:
   ids=record.get('ProductIds' if target=='Products' else 'SaleAreaIds',[])
   r[key]=[{'UserId':r['Id'],field:id,'Product' if target=='Products' else 'SaleArea':serialize(c,target,raw(c,target,id),perms,uid,2)} for id in ids if related_allowed(perms,target) and raw(c,target,id)]
 return r

def number(v):
 if v in [None,'','NaN']:return None
 f=float(v)
 if not math.isfinite(f):raise ValueError('Amounts and quantities must be finite')
 return int(f) if f.is_integer() else f

def normalized(entity,data):
 if not isinstance(data,dict):raise ValueError('A record object is required')
 fields=SCHEMA[entity]['fields'];keys={k.lower():k for k in fields};extra=['UserIds','ContactIds','ProductIds','SaleAreaIds','LinkedCustomerId','Currency','SourceDocumentId','SourceDocumentKind','PortalUserId','ExternalId','LinkedLeadId','OrganizationId','MainUserId','Version','FinancialYear','CostCenter','ActualValue','CommitmentValue','Location']
 keys.update({k.lower():k for k in extra});aliases={'pipelineid':'CRMPipelineId' if entity=='Leads' else 'ProjectPipelineId' if entity=='ProjectActivity' else 'PipelineId','description':'Problem' if entity=='HelpDeskTickets' else 'Description','mainuserid':'MainUserID' if entity=='Events' else 'MainUserId','maincontactid':'MainContactID' if entity=='Events' else 'MainCustomerId' if entity=='Leads' else 'MainContactId','productids':'ProductIds','userids':'UserIds','subuserids':'UserIds','subcontactids':'ContactIds','saleareaids':'SaleAreaIds'};keys.update(aliases)
 out={}
 for k,v in data.items():
  key=keys.get(k.lower())
  if not key or key.lower() in ['password','username','permissions','token','id','enabled','role','portaluserid']:continue
  if key.endswith('Ids'):
   if not isinstance(v,list):raise ValueError(key+' must be an ID list')
   out[key]=list(dict.fromkeys(int(number(i)) for i in v if number(i) is not None));continue
  typ=fields.get(key,'')
  if any(x in typ for x in ['[int]','[float]']):
   try:v=number(v)
   except ValueError:
    if key not in ['JobType','InstumentalStatus']:raise
   if isinstance(v,float) and '[int]' in typ:raise ValueError(key+' requires an integer')
  if '[bit]' in typ:v=v in [True,1,'1','true','True']
  if isinstance(v,str) and len(v)>100000:raise ValueError('Field too long')
  if isinstance(v,str) and '<' in v and '>' in v:raise ValueError('CRM fields accept text, not HTML markup')
  out[key]=v
 return out

def validate_relations(c,entity,record):
 for fk in SCHEMA[entity]['foreignKeys']:
  val=record.get(fk['field'])
  if val is not None and not raw(c,fk['table'],val):raise ValueError('Unknown '+fk['field'])
 for key,target in [('UserIds','Users'),('ContactIds','Contacts'),('ProductIds','Products'),('SaleAreaIds','SaleAreas')]:
  if any(not raw(c,target,x) for x in record.get(key,[])):raise ValueError('Unknown record in '+key)

def date_key(value):
 if not value:return None
 text=str(value)
 if re.match(r'^\d{4}-\d{2}-\d{2}',text):return text[:10]
 for fmt in ['%m/%d/%Y','%d/%m/%Y','%m-%d-%Y']:
  try:return datetime.datetime.strptime(text.split(',')[0].strip(),fmt).date().isoformat()
  except ValueError:pass
 return None

def filter_rows(records,query,entity=None,c=None):
 if not isinstance(query,dict):return records
 q={str(k).lower():(v[0] if isinstance(v,list) and len(v)==1 and not str(k).lower().endswith('ids') else v) for k,v in query.items()};out=[]
 for r in records:
  ok=True
  for key,fields in [('productids',['ProductId','ProductID','ProductIds']),('saleareaids',['SaleAreaId','SaleAreaID','SaleAreaIds']),('userids',['MainUserId','MainUserID','UserIds','AssignedToUserId']),('contactids',['MainCustomerId','MainContactID','ContactId','ContactIds'])]:
   wanted=q.get(key)
   if key=='userids' and q.get('onlymainresponsible'):fields=['MainUserId','MainUserID','CreatedByUserId']
   if wanted:
    vals=[]
    for f in fields:
     v=r.get(f);vals.extend(v if isinstance(v,list) else [v])
    if not set(map(str,wanted)).intersection(map(str,vals)):ok=False
  for label,field in [('expected','Expected'),('creation','Creation'),('start','StartDate'),('end','EndDate'),('update','LastUpdated')]:
   for suffix,sign in [('start',-1),('end',1)]:
    bound=q.get(label+suffix)
    if bound:
     b=date_key(bound);a=date_key(r.get(field))
     if entity=='Targets' and label=='expected':a=date_key(r.get('EndDate' if sign==-1 else 'StartDate'))
     if not b:raise ValueError('Invalid date filter: '+str(bound))
     if not a or sign==-1 and a<b or sign==1 and a>b:ok=False
  for key,val in q.items():
   if key.endswith('id') and val not in [None,'']:
    field=next((f for f in r if f.lower()==key),None)
    if field and str(r.get(field))!=str(val):ok=False
  text=q.get('search') or q.get('title')
  if text and str(text).lower() not in ' '.join(str(r.get(k) or '') for k in ['Name','LeadName','Title','Description','CategoryNumber','Problem','Model','SerialNumber']).lower():ok=False
  if q.get('anyint') is not None and str(r.get('Priority'))!=str(q['anyint']):ok=False
  if q.get('extendedids') and str(r.get('AssignedToUserId')) not in set(map(str,q['extendedids'])):ok=False
  for k,sign in [('startdate',-1),('enddate',1)]:
   if q.get(k):
    bound=date_key(q[k]);value=date_key(r.get('CreatedDate') or r.get('Creation') or r.get('StartDate'))
    if not bound:raise ValueError('Invalid date filter')
    if not value or sign==-1 and value<bound or sign==1 and value>bound:ok=False
  if entity=='InventoryProducts':
   brand=raw(c,'InventoryBrands',r.get('BrandId')) or {}
   for key,field in [('producttype','Type')]:
    if q.get(key) not in [None,''] and str(r.get(field))!=str(q[key]):ok=False
   if q.get('brandtype') not in [None,''] and str(brand.get('InventoryBrandType'))!=str(q['brandtype']):ok=False
   if q.get('distributor') not in [None,''] and str(q['distributor']).lower() not in str(brand.get('InventoryBrandDistriutor','')).lower():ok=False
   stock=sum(float(x.get('Quantity') or 0) for x in rows(c,'Stocks') if x.get('ProductId')==r['Id'])
   if q.get('min') is not None and stock<float(q['min']) or q.get('max') is not None and stock>float(q['max']):ok=False
  for key in ['ispо','ispo','iscollected','winorlost']:
   if q.get(key) is not None:
    field=next((k for k in r if k.lower()==key),None)
    if field and str(r[field]).lower()!=str(q[key]).lower():ok=False
  if ok:out.append(r)
 return out

def stock_action(c,actor,perms,uid,action,data):
 need(perms,'stock','edit' if action in ['add','remove'] else 'delete')
 if action=='delete':return mutate(c,actor,perms,uid,'Stocks','delete',data)
 product=int(data.get('ProductId',0));rec=raw(c,'InventoryProducts',product)
 if not rec:raise ValueError('Choose an inventory product')
 qty=number(data.get('Quantity'))
 if action in ['add','remove'] and (qty is None or qty<=0):raise ValueError('Quantity must be positive')
 lot=str(data.get('LotNumber','')).strip()
 if action in ['add','remove'] and not lot:raise ValueError('Lot number is required')
 existing=[x for x in rows(c,'Stocks') if x.get('ProductId')==product and x.get('LotNumber')==lot]
 if action=='remove' and sum(float(x.get('Quantity') or 0) for x in existing)<qty:raise ValueError('Insufficient CRM stock in this lot')
 if action=='delete':return mutate(c,actor,perms,uid,'Stocks','delete',data)
 record=normalized('Stocks',data);record.update(Quantity=qty if action=='add' else -qty,IncomingDate=now(),UserId=uid,Type=0 if action=='add' else 1)
 result=insert(c,'Stocks',record);audit(c,actor,'Stocks',result['Id'],action,record);return result

def mutate(c,actor,perms,uid,entity,action,data):
 module=MODULES[entity];need(perms,module,action)
 id=int(number(data.get('Id',data.get('id',data.get('LogId',0)))) or 0);prior=raw(c,entity,id) if id else None
 if action in ['edit','delete'] and not prior:raise ValueError('Record not found')
 if prior and not visible(c,perms,entity,prior,uid):raise policy.PermissionDenied('Record is outside your CRM scope')
 if prior and prior.get('_bridgeSource'):raise policy.PermissionDenied('This record is a linked source snapshot. Edit its source system or bridge mapping.')
 if entity=='Users' and action!='edit':raise policy.PermissionDenied('Create or disable sign-in users in Staff Portal → User directory')
 if action=='delete':
  if entity=='Stocks':
   remaining=sum(float(x.get('Quantity') or 0) for x in rows(c,'Stocks') if x.get('ProductId')==prior.get('ProductId') and x.get('LotNumber')==prior.get('LotNumber') and x['Id']!=id)
   if remaining<0:raise ValueError('Deleting this receipt would make the lot negative. Reverse dependent issues first.')
  for table,spec in SCHEMA.items():
   for fk in spec['foreignKeys']:
    if fk['table']==entity and any(x.get(fk['field'])==id for x in rows(c,table)):raise ValueError('Record has linked '+table+'; remove or reassign links first')
  c.execute('UPDATE crm_records SET deleted=1,version=version+1 WHERE entity=? AND id=?',(entity,id));audit(c,actor,entity,id,'delete',{});return {'Id':id,'deleted':True}
 clean=normalized(entity,data)
 if module in ['leads','events','activities','tickets']:
  owner_fields=['MainUserId','MainUserID','AssignedToUserId','CreatedByUserId','UserIds']
  if any(k in clean and clean[k]!=(prior or {}).get(k) and clean[k] not in [uid,[uid],None,[]] for k in owner_fields):need(perms,module,'assign')
 if entity=='Users':
  # Shared account name/email/role cannot be changed by a legacy CRM user form.
  for k in ['Email','FirstName','LastName','Role']:clean.pop(k,None)
 if entity=='Leads':clean.setdefault('Currency',(prior or {}).get('Currency','THB'))
 if not prior:
  if entity in ['Leads','ProjectActivity']:clean.setdefault('MainUserId',uid)
  if entity=='Events':clean.setdefault('MainUserID',uid)
  if entity=='HelpDeskTickets':clean.setdefault('CreatedByUserId',uid);clean.setdefault('AssignedToUserId',uid);clean.setdefault('CreatedDate',now())
  if entity=='Shortcuts':clean['UserId']=uid
  if entity=='Logs':clean['UserId']=uid;clean.setdefault('DateTime',now())
  if entity=='Leads':clean.setdefault('Creation',now());clean.setdefault('LastUpdated',now());clean.setdefault('CRMPipelineId',next(iter(rows(c,'CRMPipelines')),{}).get('Id'))
 if entity=='Shortcuts':
  clean['UserId']=uid
  dest=clean.get('UrlParams',(prior or {}).get('UrlParams',''))
  if not re.fullmatch(r'(?:\./)?[a-zA-Z0-9_-]+\.html(?:\?[a-zA-Z0-9_%=&.,+:-]*)?',dest):raise ValueError('Shortcuts must link to a local CRM page')
 if entity=='HelpDeskTickets':clean['LastUpdate']=now()
 validate_relations(c,entity,{**(prior or {}),**clean})
 if entity=='HelpDeskItems':
  parent=raw(c,'HelpDeskTickets',clean.get('TicketId',(prior or {}).get('TicketId')))
  if not parent or not visible(c,perms,'HelpDeskTickets',parent,uid):raise policy.PermissionDenied('Ticket is outside your CRM scope')
 if entity=='Stocks' and action=='edit':raise ValueError('Use stock add/remove actions to adjust balances')
 result=update(c,entity,id,clean) if prior else insert(c,entity,clean)
 if entity=='HelpDeskTickets' and 'HelpDeskItems' in data:
  need(perms,'ticket_items','edit' if prior else 'create')
  for line in data['HelpDeskItems']:
   payload=normalized('HelpDeskItems',line);payload['TicketId']=result['Id'];validate_relations(c,'HelpDeskItems',payload)
   if line.get('Id'):
    old=raw(c,'HelpDeskItems',int(line['Id']))
    if not old or old.get('TicketId')!=result['Id']:raise ValueError('Ticket item does not belong to this ticket')
    update(c,'HelpDeskItems',int(line['Id']),payload)
   else:insert(c,'HelpDeskItems',payload)
 audit(c,actor,entity,result['Id'],action,clean);return result

def handle(c,actor,perms,path,method,data):
 policy.need(perms,'crm_view');bind_users(c);uid=user_id(c,actor);route=urlsplit(path).path.removeprefix('/biomedapi/').strip('/');query=parse_qs(urlsplit(path).query)
 if route=='login':raise policy.PermissionDenied('Use the shared Staff Portal sign-in')
 if route=='myuser':
  record=raw(c,'Users',uid);r=serialize(c,'Users',record,perms,uid);r['Permissions']=permission_rows(perms);return r
 if route.lower()=='v2/user/summary':
  need(perms,'dashboard');u=serialize(c,'Users',raw(c,'Users',uid),perms,uid)
  events=[serialize(c,'Events',x,perms,uid) for x in rows(c,'Events') if visible(c,perms,'Events',x,uid)]
  return {'user':u,'myEvent':[x for x in events if x.get('MainUserID')==uid],'myCoopEvent':[x for x in events if x.get('MainUserID')!=uid],'myTarget':[serialize(c,'Targets',x,perms,uid) for x in rows(c,'Targets') if related_allowed(perms,'Targets')],'userProduct':[x.get('Product') for x in u['ProductUsers']],'userSaleArea':[x.get('SaleArea') for x in u['SaleAreaUsers']]}
 if route=='visualization':
  need(perms,'relationships');return {name:[serialize(c,entity,r,perms,uid) for r in rows(c,entity) if visible(c,perms,entity,r,uid)] for name,entity in [('Users','Users'),('Contacts','Contacts'),('Events','Events'),('Leads','Leads'),('Activities','ProjectActivity'),('Tickets','HelpDeskTickets')]}
 if route.startswith('v2/helpdesk/public/'):raise policy.PermissionDenied('CRM tickets require the shared authenticated session')
 if route.startswith('v2/product/stock/') and route.rsplit('/',1)[1] in ['add','remove','delete']:
  if method not in ['POST','PUT','DELETE']:raise ValueError('Stock writes require POST')
  return stock_action(c,actor,perms,uid,route.rsplit('/',1)[1],data)
 # Multipart files are handled by the authenticated server handler, not this JSON router.
 action='view';id=None;base=route
 suffix=route.rsplit('/',1)[-1]
 if suffix in ['create','update','delete','get']:base=route.rsplit('/',1)[0];action={'create':'create','update':'edit','delete':'delete','get':'view'}[suffix]
 elif suffix.isdigit():base=route.rsplit('/',1)[0];id=int(suffix)
 if base=='log/get':base='log'
 entity=ALIASES.get(base)
 if not entity:raise ValueError('Unsupported CRM route: '+route)
 module=MODULES[entity]
 if action!='view' and method not in ['POST','PUT','DELETE']:raise ValueError('CRM writes require POST, PUT or DELETE')
 if method in ['PUT','DELETE'] and action=='view':
  action='edit' if method=='PUT' else 'delete';data={**data,'Id':id or data.get('Id')}
 if action!='view':return mutate(c,actor,perms,uid,entity,action,data)
 need(perms,module)
 if id:
  record=raw(c,entity,id)
  if not record:raise ValueError('Record not found')
  if not visible(c,perms,entity,record,uid):raise policy.PermissionDenied('Record is outside your CRM scope')
  return serialize(c,entity,record,perms,uid)
 selected=filter_rows([r for r in rows(c,entity) if visible(c,perms,entity,r,uid)],data if method=='POST' else query,entity,c)
 result=[serialize(c,entity,r,perms,uid) for r in selected]
 return result

# Router additions for the quick-navigation API used by the supplied source.
_original_handle=handle
def handle(c,actor,perms,path,method,data):
 route=urlsplit(path).path.removeprefix('/biomedapi/').strip('/');lower=route.lower()
 if lower.startswith('v2/user/getshortcuts/'):
  policy.need(perms,'crm_view');bind_users(c);uid=user_id(c,actor);need(perms,'shortcuts');requested=int(route.rsplit('/',1)[1])
  if requested!=uid:raise policy.PermissionDenied('Shortcuts belong to the signed-in user')
  return [{**x,'id':x['Id']} for x in rows(c,'Shortcuts') if x.get('UserId')==uid]
 if lower=='v2/user/createshortcut':
  if method!='POST':raise ValueError('Shortcut creation requires POST')
  return _original_handle(c,actor,perms,'/biomedapi/shortcuts/create','POST',data)
 if lower.startswith('v2/user/deleteshortcut/'):
  if method not in ['POST','DELETE']:raise ValueError('Shortcut deletion requires DELETE or POST')
  return _original_handle(c,actor,perms,'/biomedapi/shortcuts/delete','POST',{'Id':int(route.rsplit('/',1)[1])})
 match=re.fullmatch(r'(.+)/(delete|update)/(\d+)',route)
 if match:return _original_handle(c,actor,perms,'/biomedapi/'+match[1]+'/'+match[2],method,{**data,'Id':int(match[3])})
 return _original_handle(c,actor,perms,path,method,data)
