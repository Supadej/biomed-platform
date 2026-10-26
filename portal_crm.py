"""Flat, paginated Staff Portal modules over the existing CRM records.
No recursive serialization or separate CRM application is used by these pages.
"""
import json, math, datetime
from urllib.parse import urlsplit, parse_qs
import crm_api as crm
import permissions_policy as policy
PORTAL='biomed_portal_v33_clean'
IS='biomed_is_v50_transactions'
ENTITIES={'Events','Leads','Projects','ProjectPipeline','ProjectActivity','HelpDeskTickets','HelpDeskItems','CRMPipelines','HelpDeskPipelines','Logs','Targets','Contacts','Departments','Organizations','Products','SaleAreas','InventoryProducts','Users'}
KINDS=['quotation','customer-order','sales-order','invoice']
NAMES={'Events':'Title','Leads':'LeadName','HelpDeskTickets':'Title','Logs':'LogValue'}
def initialize(c):
 c.execute('CREATE TABLE IF NOT EXISTS portal_crm_binding(id INTEGER PRIMARY KEY CHECK(id=1),payload TEXT NOT NULL,revision INTEGER NOT NULL DEFAULT 1)')
 c.execute('CREATE TABLE IF NOT EXISTS portal_crm_targets(scheme_id TEXT PRIMARY KEY,record_id INTEGER NOT NULL,snapshot TEXT NOT NULL)')
def workspace(c,key):
 r=c.execute('SELECT value FROM workspace WHERE key=?',(key,)).fetchone();return json.loads(r[0]) if r and r[0] else {}
def config(c):
 r=c.execute('SELECT payload,revision FROM portal_crm_binding WHERE id=1').fetchone()
 return {'config':json.loads(r[0]),'revision':r[1]} if r else {'config':{'enabled':False,'kinds':KINDS,'ownerMap':{}},'revision':0}
def binding_need(perms,kinds):
 crm.need(perms,'leads','import');crm.need(perms,'leads','create');crm.need(perms,'leads','assign');crm.need(perms,'leads','view_all');policy.need(perms,'is_view')
 for k in kinds:policy.need(perms,'is.'+k+'.view')
def amount(d):
 v=d.get('financials',{}).get('net') if d.get('sourceVersion') and d.get('financials') else sum(float(x.get('qty') or 0)*float(x.get('price') or 0) for x in d.get('lines',[]))
 v=float(v or 0)
 if not math.isfinite(v):raise ValueError('Invalid document amount')
 return v

def sync_documents(c,data,actor):
 """Run in the IS save transaction, only after an administrator enables binding.
 Exact source IDs + ancestry prevent repeated saves and later invoices duplicating leads.
 """
 cfg=config(c)['config']
 if not cfg.get('enabled'):return {'created':0,'updated':0,'skipped':0}
 docs={str(d['id']):d for d in data.get('documents',[]) if d.get('id')};counts={'created':0,'updated':0,'skipped':0}
 identity={str(a):b for a,b in c.execute('SELECT portal_user_id,crm_user_id FROM crm_identity')}
 customers={str(x['id']):x.get('name',x['id']) for x in data.get('customers',[])}
 def chain(d):
  seq=[d];seen={str(d['id'])}
  while d.get('sourceId') and str(d['sourceId']) in docs:
   d=docs[str(d['sourceId'])]
   if str(d['id']) in seen:break
   seen.add(str(d['id']));seq.append(d)
  return seq
 for d in sorted(docs.values(),key=lambda x:(KINDS.index(x['kind']) if x.get('kind') in KINDS else 99,str(x.get('date','')))):
  if d.get('kind') not in cfg['kinds']:continue
  seq=chain(d);links=[]
  for x in seq:
   linked=c.execute("SELECT record_id FROM crm_links WHERE source='native-is' AND source_id=? AND entity='Leads'",(str(x['id']),)).fetchone()
   if linked:links.append(linked[0])
  if len(set(links))>1:counts['skipped']+=1;continue
  if d.get('status')!='Approved' and not links:continue
  lead=crm.raw(c,'Leads',links[0]) if links else None
  if links and not lead:counts['skipped']+=1;continue # deletion remains deliberate
  owner=str(d.get('portalRep') or d.get('owner') or '');owner=cfg.get('ownerMap',{}).get(owner,owner);uid=identity.get(owner)
  if not uid:counts['skipped']+=1;continue
  if lead and lead.get('_bridgeSource'):counts['skipped']+=1;continue
  snap={'id':str(d['id']),'kind':d['kind'],'reference':d.get('ref') or str(d['id']),'status':d.get('status','Draft'),'amount':amount(d),'currency':d.get('currency') or 'THB','customer':customers.get(str(d.get('party')),str(d.get('party') or '')),'date':d.get('date'),'line':d.get('portalLine','Diagnostics')}
  if lead and lead.get('Currency')!=snap['currency']:counts['skipped']+=1;continue
  source_docs=dict((lead or {}).get('SourceDocuments') or {});old=source_docs.get(str(d['id']));source_docs[str(d['id'])]=snap
  if not lead:
   lead=crm.insert(c,'Leads',{'LeadName':snap['customer']+' · '+snap['reference'],'MainUserId':uid,'Creation':crm.now(),'LastUpdated':crm.now(),'Expected':d.get('date'),'ExpectedRevenue':snap['amount'],'AchivedRevenue':snap['amount'] if d['kind']=='invoice' else 0,'Currency':snap['currency'],'CRMPipelineId':next(iter(crm.rows(c,'CRMPipelines')),{}).get('Id'),'LinkedCustomerId':d.get('party'),'SourceDocuments':source_docs})
   counts['created']+=1;crm.audit(c,actor,'Leads',lead['Id'],'generate from IS',snap)
  elif old!=snap:
   updates={'SourceDocuments':source_docs,'LastUpdated':crm.now()}
   invoices=[x for x in source_docs.values() if x['kind']=='invoice' and x.get('status')=='Approved']
   if any(x['kind']=='invoice' for x in source_docs.values()):updates['AchivedRevenue']=sum(x['amount'] for x in invoices)
   crm.update(c,'Leads',lead['Id'],updates);counts['updated']+=1;crm.audit(c,actor,'Leads',lead['Id'],'refresh source binding',snap)
  for x in seq:c.execute("INSERT OR IGNORE INTO crm_links VALUES('native-is',?,'Leads',?)",(str(x['id']),lead['Id']))
 for payload, in c.execute("SELECT payload FROM crm_records WHERE entity='Leads' AND deleted=0"):
  lead=json.loads(payload);snapshots=lead.get('SourceDocuments')
  if not snapshots:continue
  changed=False
  for sid,snap in snapshots.items():
   if sid not in docs and snap.get('status')!='Removed':snap['status']='Removed';changed=True
  if changed:
   invoices=[s for s in snapshots.values() if s.get('kind')=='invoice' and s.get('status')=='Approved']
   updates={'SourceDocuments':snapshots,'LastUpdated':crm.now()}
   if any(s.get('kind')=='invoice' for s in snapshots.values()):updates['AchivedRevenue']=sum(s['amount'] for s in invoices)
   crm.update(c,'Leads',lead['Id'],updates);counts['updated']+=1;crm.audit(c,actor,'Leads',lead['Id'],'source removed',{})
 return counts

def schemes(c,actor,perms):
 policy.need(perms,'incentives');policy.need(perms,'sales')
 p=workspace(c,PORTAL);src=workspace(c,IS);scope={str(actor[4])}
 if 'manage_incentives' in perms or 'approve_all' in perms:
  while True:
   extra={str(u['id']) for u in p.get('users',[]) if str(u.get('manager') or u.get('managerId') or '') in scope}
   if extra<=scope:break
   scope|=extra
 if 'approve_all' in perms:scope={str(u['id']) for u in p.get('users',[])}
 docs=src.get('documents',[]);credits=[x for x in docs if x.get('kind')=='credit-note' and x.get('status')=='Approved'];actuals=[]
 if p.get('integrationIS') is not None:actuals=p['integrationIS'].get('salesActuals',[])
 else:
  # Same approved-invoice, THB and net-credit basis as Staff Portal incentives.
  for d in docs:
   if d.get('kind')!='invoice' or d.get('status')!='Approved' or d.get('currency') not in [None,'','THB']:continue
   net=max(0,amount(d)-sum(amount(x) for x in credits if x.get('sourceId')==d['id'] and x.get('currency')==d.get('currency')))
   actuals.append({'rep':str(d.get('portalRep') or d.get('owner') or ''),'line':d.get('portalLine') or 'Diagnostics','period':str(d.get('date',''))[:7],'amount':net})
 out=[]
 for s in p.get('incentiveSchemes',[]):
  if str(s.get('rep')) not in scope:continue
  def matches(x):return str(x.get('rep'))==str(s['rep']) and x.get('line')==s.get('line') and s['from']<=str(x.get('period',''))<=s['to']
  target=sum(float(x.get('amount') or 0) for x in p.get('salesTargets',[]) if matches(x));actual=sum(float(x.get('amount') or 0) for x in actuals if matches(x));attainment=actual/target*100 if target>0 else 0
  link=c.execute('SELECT record_id FROM portal_crm_targets WHERE scheme_id=?',(str(s['id']),)).fetchone()
  out.append({**s,'target':target,'actual':actual,'attainment':attainment,'eligible':target>0 and actual>=target,'linkedId':link[0] if link else None})
 return out

def display_record(entity,obj):
 # Original CRM dates sometimes use locale strings. Present deterministic ISO values.
 obj=dict(obj)
 for field,typ in crm.SCHEMA.get(entity,{}).get('fields',{}).items():
  value=obj.get(field)
  if not value or '[datetime' not in typ:continue
  value=str(value)
  try:obj[field]=datetime.datetime.fromisoformat(value.replace('Z','+00:00')).isoformat();continue
  except ValueError:pass
  for fmt in ['%m/%d/%Y, %H:%M','%m/%d/%Y, %H:%M:%S','%m/%d/%Y','%d/%m/%Y, %H:%M','%d/%m/%Y']:
   try:obj[field]=datetime.datetime.strptime(value,fmt).isoformat();break
   except ValueError:continue
 return obj

def record(c,perms,uid,entity,id):
 r=c.execute('SELECT payload,version FROM crm_records WHERE entity=? AND id=? AND deleted=0',(entity,id)).fetchone()
 if not r:raise ValueError('Record not found')
 obj=json.loads(r[0])
 if not crm.visible(c,perms,entity,obj,uid) or not target_visible(c,perms,uid,entity,obj):raise policy.PermissionDenied('Record is outside your scope')
 return {k:v for k,v in display_record(entity,obj).items() if k.lower() not in ['password','passwordhash','salt','token','username']},r[1]
def target_visible(c,perms,uid,entity,obj):
 if entity!='Targets' or not obj.get('PortalRep') or 'approve_all' in perms:return True
 identity=c.execute('SELECT portal_user_id FROM crm_identity WHERE crm_user_id=?',(uid,)).fetchone()
 scope={str(identity[0])} if identity else set()
 if 'manage_incentives' in perms:
  users=workspace(c,PORTAL).get('users',[])
  while True:
   extra={str(x['id']) for x in users if str(x.get('managerId','')) in scope}
   if extra<=scope:break
   scope|=extra
 return str(obj['PortalRep']) in scope

def accessible(c,perms,uid,entity):
 crm.need(perms,crm.MODULES[entity])
 for payload,version in c.execute('SELECT payload,version FROM crm_records WHERE entity=? AND deleted=0 ORDER BY id DESC',(entity,)):
  obj=display_record(entity,json.loads(payload))
  if crm.visible(c,perms,entity,obj,uid) and target_visible(c,perms,uid,entity,obj):yield obj,version

def handle(c,actor,perms,path,method,data):
 crm.bind_users(c);uid=crm.user_id(c,actor);parts=urlsplit(path);action=parts.path.rsplit('/',1)[-1];q={k:v[0] for k,v in parse_qs(parts.query).items()}
 def get_entity():
  e=q.get('entity') or data.get('entity')
  if e not in ENTITIES:raise ValueError('Unknown portal feature')
  return e
 if action=='meta' and method=='GET':
  enabled={e:s for e,s in crm.SCHEMA.items() if e in ENTITIES and 'crm.'+crm.MODULES[e]+'.view' in perms}
  return {'schema':enabled,'permissions':sorted(perms),'uid':uid}
 if action=='binding':
  if method=='GET':
   binding_need(perms,config(c)['config']['kinds']);src=workspace(c,IS);p=workspace(c,PORTAL)
   return {**config(c),'sourceOwners':sorted({str(d.get('portalRep') or d.get('owner') or '') for d in src.get('documents',[]) if d.get('kind') in KINDS}), 'staff':[{'id':str(u['id']),'name':u.get('name',str(u['id']))} for u in p.get('users',[])]}
  if method!='POST':raise ValueError('Use POST')
  cfg=data.get('config',{});kinds=cfg.get('kinds',[])
  if not kinds or set(kinds)-set(KINDS):raise ValueError('Choose sales document types')
  binding_need(perms,kinds);old=config(c)
  if data.get('revision')!=old['revision']:raise ValueError('Binding changed; reload settings')
  users={str(x['id']) for x in workspace(c,PORTAL).get('users',[])};mapping=cfg.get('ownerMap',{})
  if not isinstance(mapping,dict) or any(str(v) not in users for v in mapping.values()):raise ValueError('Map owners to valid Staff Portal user IDs')
  cfg={'enabled':bool(cfg.get('enabled')),'kinds':kinds,'ownerMap':mapping}
  c.execute('INSERT OR REPLACE INTO portal_crm_binding VALUES(1,?,?)',(crm.dump(cfg),old['revision']+1));crm.audit(c,actor,'binding',None,'configure',cfg)
  return {**config(c),'result':sync_documents(c,workspace(c,IS),actor)}
 if action=='sync' and method=='POST':
  binding_need(perms,config(c)['config']['kinds']);return sync_documents(c,workspace(c,IS),actor)
 if action=='schemes' and method=='GET':crm.need(perms,'targets');return schemes(c,actor,perms)
 if action=='link-target' and method=='POST':
  crm.need(perms,'targets','create');s=next((s for s in schemes(c,actor,perms) if str(s['id'])==str(data.get('schemeId'))),None)
  if not s or not s['eligible']:raise ValueError('Link requires a positive target and at least 100% actual attainment')
  if s['linkedId']:
   target=crm.raw(c,'Targets',s['linkedId'])
   if not target:raise ValueError('Linked target was deleted; ask an administrator to review')
   crm.need(perms,'targets','edit')
  else:target=None
  snapshot={k:s[k] for k in ['id','rep','line','from','to','target','actual','attainment']}
  last=datetime.date.fromisoformat(s['to']+'-01');end=(last.replace(day=28)+datetime.timedelta(days=4)).replace(day=1)-datetime.timedelta(days=1)
  values={'Name':s['line']+' · '+s['from']+' – '+s['to'],'TargetValue':s['target'],'StartDate':s['from']+'-01','EndDate':end.isoformat(),'ActualValue':s['actual'],'IncentiveSchemeId':s['id'],'AttainmentAtLink':s['attainment'],'LinkedAt':crm.now(),'PortalRep':s['rep']}
  result=crm.update(c,'Targets',target['Id'],values) if target else crm.insert(c,'Targets',values)
  c.execute('INSERT OR REPLACE INTO portal_crm_targets VALUES(?,?,?)',(str(s['id']),result['Id'],crm.dump(snapshot)));crm.audit(c,actor,'Targets',result['Id'],'link incentive target',snapshot);return result
 entity=get_entity();module=crm.MODULES[entity];crm.need(perms,module)
 if action=='options' and method=='GET':
  search=q.get('search','').casefold();selected=set(q.get('selected','').split(','));out=[]
  for obj,ver in accessible(c,perms,uid,entity):
   label=(str(obj.get('FirstName') or '')+' '+str(obj.get('LastName') or '')).strip() if entity=='Users' else obj.get(NAMES.get(entity,'Name')) or obj.get('PipelineName') or obj.get('Description') or '#'+str(obj['Id'])
   if (search in str(label).casefold() and len(out)<100) or str(obj['Id']) in selected:out.append({'id':obj['Id'],'label':str(label)})
  return out
 if action=='list' and method=='GET':
  page=max(1,int(q.get('page',1)));size=min(1000 if entity=='Events' else 100,max(1,int(q.get('size',30))));items=[];total=0;search=q.get('search','').casefold()
  for obj,ver in accessible(c,perms,uid,entity):
   if search and search not in ' '.join(str(v) for k,v in obj.items() if k not in ['SourceDocuments']).casefold():continue
   if q.get('field') and str(obj.get(q['field']) or '')!=q.get('value',''):continue
   if q.get('owner'):
    owners=[obj.get(k) for k in ['MainUserId','MainUserID','AssignedToUserId','CreatedByUserId']]+(obj.get('UserIds') or [])
    if str(q['owner']) not in set(map(str,owners)):continue
   if q.get('project'):
    if entity=='Projects' and str(obj['Id'])!=q['project']:continue
    if entity=='ProjectPipeline' and str(obj.get('ProjectId'))!=q['project']:continue
    if entity=='ProjectActivity':
     stage=crm.raw(c,'ProjectPipeline',obj.get('ProjectPipelineId')) or {}
     if str(stage.get('ProjectId'))!=q['project']:continue
   date=str(obj.get('StartDate') or obj.get('ActivityDate') or obj.get('CreatedDate') or obj.get('Expected') or '')
   end=str(obj.get('EndDate') or date)
   if q.get('from') and end[:10]<q['from'] or q.get('to') and date[:10]>q['to']:continue
   if (page-1)*size<=total<page*size:items.append({**obj,'_version':ver})
   total+=1
  return {'items':items,'total':total,'page':page,'size':size}
 if action=='history' and method=='GET':
  record(c,perms,uid,entity,int(q['id']))
  return [dict(zip(['at','actor','action','detail'],r)) for r in c.execute('SELECT at,actor,action,detail FROM crm_audit WHERE entity=? AND record_id=? ORDER BY id DESC LIMIT 100',(entity,int(q['id'])))]
 if action=='record' and method=='GET':
  obj,ver=record(c,perms,uid,entity,int(q['id']));return {**obj,'_version':ver}
 if action not in ['save','delete'] or method!='POST':raise ValueError('Unsupported portal operation')
 values=data.get('record',{});id=values.get('Id');prior=None
 if id:
  prior,ver=record(c,perms,uid,entity,int(id))
  if data.get('version')!=ver:raise ValueError('This record changed in another session. Reload before saving.')
 if action=='delete':return crm.mutate(c,actor,perms,uid,entity,'delete',{'Id':id})
 if entity=='Targets' and (prior or {}).get('IncentiveSchemeId'):raise ValueError('Refresh this linked target from Incentive schemes')
 name=NAMES.get(entity,'Name')
 if name in crm.SCHEMA[entity]['fields'] and not str(values.get(name,(prior or {}).get(name)) or '').strip():raise ValueError('A title or name is required')
 if not prior:
  for owner_key in {'Events':['MainUserID'],'Leads':['MainUserId'],'ProjectActivity':['MainUserId'],'HelpDeskTickets':['AssignedToUserId','CreatedByUserId']}.get(entity,[]):
   if not values.get(owner_key):values[owner_key]=uid
 merged={**(prior or {}),**values}
 if entity=='Events':
  try:a=datetime.datetime.fromisoformat(str(merged.get('StartDate')));b=datetime.datetime.fromisoformat(str(merged.get('EndDate')))
  except (TypeError,ValueError):raise ValueError('Choose valid start and end dates')
  if b<a:raise ValueError('End must be after start')
 for k in ['ExpectedRevenue','AchivedRevenue','Budget','Expense','Quantity','TargetValue','ActivityBudget','MaterialBudget']:
  if k in values and values[k] not in [None,''] and float(values[k])<0:raise ValueError(k+' cannot be negative')
 # Parent scope must also hold when activities/stages/items/logs reference a record.
 for field,parent in [('ProjectId','Projects'),('ProjectPipelineId','ProjectPipeline'),('TicketId','HelpDeskTickets'),('LeadId','Leads'),('EventId','Events'),('ActivityId','ProjectActivity'),('HelpdeskTicketId','HelpDeskTickets')]:
  if merged.get(field):record(c,perms,uid,parent,int(merged[field]))
 if entity=='Logs' and not any(merged.get(k) for k in ['LeadId','EventId','ActivityId','HelpdeskTicketId']):raise ValueError('Choose a record for the note')
 for k in ['MainUserID','MainUserId','AssignedToUserId','CreatedByUserId']:
  if merged.get(k) and not crm.raw(c,'Users',int(merged[k])):raise ValueError('Unknown responsible employee')
 # Explicit null relation selections must stay null, never empty strings.
 values={k:(None if v=='' and (k.endswith('Id') or k.endswith('ID')) else v) for k,v in values.items()}
 result=crm.mutate(c,actor,perms,uid,entity,'edit' if prior else 'create',values)
 return {**result,'_version':c.execute('SELECT version FROM crm_records WHERE entity=? AND id=?',(entity,result['Id'])).fetchone()[0]}
