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
NAMES={'Events':'Title','Leads':'LeadName','HelpDeskTickets':'Title','Logs':'LogValue','CRMPipelines':'PipelineName'}
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
   lead=crm.insert(c,'Leads',{'LeadName':snap['customer']+' · '+snap['reference'],'MainUserId':uid,'Creation':crm.now(),'LastUpdated':crm.now(),'Expected':d.get('date'),'ExpectedRevenue':snap['amount'],'AchivedRevenue':snap['amount'] if d['kind']=='invoice' else 0,'Currency':snap['currency'],'ProductLine':snap['line'],'CRMPipelineId':next(iter(crm.rows(c,'CRMPipelines')),{}).get('Id'),'LinkedCustomerId':d.get('party'),'SourceDocuments':source_docs})
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

def incentive_actuals(c,p):
 src=workspace(c,IS);docs=src.get('documents',[]);credits=[x for x in docs if x.get('kind')=='credit-note' and x.get('status')=='Approved'];actuals=[]
 if p.get('integrationIS') is not None:actuals=p['integrationIS'].get('salesActuals',[])
 else:
  # Same approved-invoice, THB and net-credit basis as Staff Portal incentives.
  for d in docs:
   if d.get('kind')!='invoice' or d.get('status')!='Approved' or d.get('currency') not in [None,'','THB']:continue
   net=max(0,amount(d)-sum(amount(x) for x in credits if x.get('sourceId')==d['id'] and x.get('currency')==d.get('currency')))
   actuals.append({'rep':str(d.get('portalRep') or d.get('owner') or ''),'line':d.get('portalLine') or 'Diagnostics','period':str(d.get('date',''))[:7],'amount':net})
 return actuals

def schemes(c,actor,perms):
 policy.need(perms,'incentives');policy.need(perms,'sales')
 p=workspace(c,PORTAL);src=workspace(c,IS);scope={str(actor[4])}
 if 'manage_incentives' in perms or 'approve_all' in perms:
  while True:
   extra={str(u['id']) for u in p.get('users',[]) if str(u.get('manager') or u.get('managerId') or '') in scope}
   if extra<=scope:break
   scope|=extra
 if 'approve_all' in perms:scope={str(u['id']) for u in p.get('users',[])}
 actuals=incentive_actuals(c,p)
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
 if entity in ['CRMPipelines','HelpDeskPipelines','ProjectPipeline']:
  obj['StageType']=workflow_stage_type(entity,obj);obj['Color']=obj.get('Color') or '#087fa9'
 if entity=='Leads':obj['ProductLine']=lead_line(c,obj)
 if entity=='ProjectActivity' and not obj.get('ProjectId'):obj['ProjectId']=(crm.raw(c,'ProjectPipeline',obj.get('ProjectPipelineId')) or {}).get('ProjectId')
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

WORKFLOWS={'Leads':('CRMPipelines','CRMPipelineId'),'HelpDeskTickets':('HelpDeskPipelines','PipelineId'),'ProjectActivity':('ProjectPipeline','ProjectPipelineId')}
def stage_config(entity):
 for child,(stage,fk) in WORKFLOWS.items():
  if entity==stage:return child,fk
 raise ValueError('Unknown stage register')
def workflow_records(c,perms,uid,entity,q):
 if entity=='Leads':return selected_leads(c,perms,uid,q)
 result=[]
 for row,version in accessible(c,perms,uid,entity):
  if q.get('search') and q['search'].casefold() not in ' '.join(str(v) for v in row.values()).casefold():continue
  owners=[row.get(k) for k in ['MainUserId','MainUserID','AssignedToUserId','CreatedByUserId']]+(row.get('UserIds') or [])
  if q.get('owner') and str(q['owner']) not in set(map(str,owners)):continue
  if entity=='ProjectActivity':
   stage=crm.raw(c,'ProjectPipeline',row.get('ProjectPipelineId')) or {};pid=row.get('ProjectId') or stage.get('ProjectId');row={**row,'ProjectId':pid}
   if q.get('project') and str(pid)!=str(q['project']):continue
  date=str(row.get('ActivityDate') or row.get('CreatedDate') or '')[:10]
  if q.get('from') and date<q['from'] or q.get('to') and date>q['to']:continue
  result.append({**row,'_version':version})
 return result

def product_lines(c):
 p=workspace(c,PORTAL)
 return sorted({str(x) for x in p.get('productLines',[]) if x}|{str(x['line']) for x in p.get('incentiveSchemes',[]) if x.get('line')})
def stage_kind(stage):
 if stage.get('StageType') in ['open','won','lost']:return stage['StageType']
 return {'won':'won','lost':'lost','lost/cancel':'lost','lost/cancelled':'lost'}.get(str(stage.get('PipelineName','')).strip().lower(),'open')
def workflow_stage_type(entity,stage):
 if entity=='CRMPipelines':return stage_kind(stage)
 if stage.get('StageType'):return stage['StageType']
 name=str(stage.get('Name','')).strip().lower()
 defaults={'HelpDeskPipelines':{'in progress':'in_progress','waiting':'waiting','resolved':'resolved','closed':'closed'},'ProjectPipeline':{'in progress':'in_progress','completed':'done','done':'done','cancelled':'cancelled'}}
 return defaults.get(entity,{}).get(name,'open')

def stages_list(c,entity='CRMPipelines',project=None):
 out=[]
 for payload,ver in c.execute('SELECT payload,version FROM crm_records WHERE entity=? AND deleted=0',(entity,)):
  r=json.loads(payload)
  if entity=='ProjectPipeline' and project and str(r.get('ProjectId'))!=str(project):continue
  out.append({**r,'StageType':workflow_stage_type(entity,r),'Color':r.get('Color') or '#087fa9','_version':ver})
 return sorted(out,key=lambda r:(float(r['Order'] if r.get('Order') is not None else r['Id']),r['Id']))
def lead_line(c,lead,cache=None):
 if lead.get('ProductLine'):return str(lead['ProductLine'])
 lines={str(x['line']) for x in (lead.get('SourceDocuments') or {}).values() if x.get('line')}
 if len(lines)==1:return next(iter(lines))
 if lead.get('ProductId'):
  if cache is None:cache={}
  products=cache.setdefault('products',{});pid=lead['ProductId']
  if pid not in products:products[pid]=(crm.raw(c,'Products',pid) or {}).get('Name')
  if 'lines' not in cache:cache['lines']=set(product_lines(c))
  name=products[pid]
  if name and name in cache['lines']:return name
 return ''
def selected_leads(c,perms,uid,q):
 out=[];line_cache={}
 for row,ver in accessible(c,perms,uid,'Leads'):
  if q.get('search') and q['search'].casefold() not in ' '.join(str(v) for k,v in row.items() if k!='SourceDocuments').casefold():continue
  if q.get('owner') and str(q['owner']) not in {str(row.get('MainUserId')),*map(str,row.get('UserIds') or [])}:continue
  day=str(row.get('Expected') or '')[:10]
  if q.get('from') and day<q['from'] or q.get('to') and day>q['to']:continue
  if q.get('line') and lead_line(c,row,line_cache)!=q['line']:continue
  out.append({**row,'ProductLine':lead_line(c,row,line_cache),'_version':ver})
 return out

def currency_totals(leads):
 out={}
 for r in leads:
  cur=str(r.get('Currency') or 'THB');x=out.setdefault(cur,{'expected':0,'leadAchieved':0})
  x['expected']+=float(r.get('ExpectedRevenue') or 0);x['leadAchieved']+=float(r.get('AchivedRevenue') or 0)
 return out

def sales_summary(c,actor,perms,leads,q):
 stages={x['Id']:x for x in crm.rows(c,'CRMPipelines')}
 def is_lost(row):
  stage=stages.get(row.get('CRMPipelineId'),{})
  return stage_kind(stage)=='lost'
 active=[r for r in leads if not is_lost(r)];resolved_cache={'lines':set(product_lines(c))}
 out={'leadCount':len(leads),'activeCount':len(active),'lostCount':len(leads)-len(active),'currencies':currency_totals(active),'targets':[],'targetsAvailable':False,'unmappedCount':sum(lead_line(c,r,resolved_cache) not in resolved_cache['lines'] for r in active),'missingClosingCount':sum(not r.get('Expected') for r in active)}
 if not {'incentives','sales','crm.targets.view'}<=set(perms):return out
 available=[s for s in schemes(c,actor,perms) if float(s.get('threshold') or 0)==100]
 p=workspace(c,PORTAL);actuals=incentive_actuals(c,p);identity={int(uid):str(pid) for pid,uid in c.execute('SELECT portal_user_id,crm_user_id FROM crm_identity')}
 people={str(u['id']):u.get('name',str(u['id'])) for u in p.get('users',[])}
 slices=set();plan_index={};line_cache=resolved_cache
 for r in active:
  if (r.get('Currency') or 'THB')!='THB':continue
  key=(identity.get(r.get('MainUserId')),lead_line(c,r,line_cache),str(r.get('Expected') or '')[:7]);item=plan_index.setdefault(key,{'expected':0,'count':0});item['expected']+=float(r.get('ExpectedRevenue') or 0);item['count']+=1
 def matches(row,rep,line,lo,hi):return str(row.get('rep'))==str(rep) and row.get('line')==line and lo<=str(row.get('period',''))<=hi
 def months(lo,hi):
  year,month=map(int,lo.split('-'));endyear,endmonth=map(int,hi.split('-'))
  for count in range(1200):
   if (year,month)>(endyear,endmonth):break
   yield f'{year:04d}-{month:02d}'
   month+=1
   if month>12:year+=1;month=1
 for s in available:
  if q.get('owner') and str(s['rep'])!=identity.get(int(q['owner'])):continue
  if q.get('line') and s['line']!=q['line']:continue
  lo=max(str(s['from']),str(q.get('from') or s['from'])[:7]);hi=min(str(s['to']),str(q.get('to') or s['to'])[:7])
  if lo>hi:continue
  target=sum(float(r.get('amount') or 0) for r in p.get('salesTargets',[]) if matches(r,s['rep'],s['line'],lo,hi));actual=sum(float(r.get('amount') or 0) for r in actuals if matches(r,s['rep'],s['line'],lo,hi))
  planned=[v for (rep,line,month),v in plan_index.items() if rep==str(s['rep']) and line==s['line'] and lo<=month<=hi]
  expected=sum(v['expected'] for v in planned);planned_count=sum(v['count'] for v in planned)
  out['targets'].append({'id':s['id'],'rep':s['rep'],'representative':people.get(str(s['rep']),str(s['rep'])),'line':s['line'],'from':lo,'to':hi,'target':target,'expected':expected,'actual':actual,'attainment':actual/target*100 if target>0 else 0,'coverage':expected/target*100 if target>0 else 0,'gap':max(0,target-actual),'leadCount':planned_count,'linkedId':s['linkedId'],'eligible':target>0 and actual>=target})
  slices|={(str(s['rep']),s['line'],month) for month in months(lo,hi)}
 def included(r):return (str(r.get('rep')),r.get('line'),str(r.get('period',''))) in slices
 total_target=sum(float(r.get('amount') or 0) for r in p.get('salesTargets',[]) if included(r));total_actual=sum(float(r.get('amount') or 0) for r in actuals if included(r))
 expected=sum(v['expected'] for key,v in plan_index.items() if key in slices)
 out.update(targetsAvailable=True,totalTarget=total_target,totalActual=total_actual,totalExpected=expected,attainment=total_actual/total_target*100 if total_target>0 else 0,coverage=expected/total_target*100 if total_target>0 else 0)
 return out

def handle(c,actor,perms,path,method,data):
 crm.bind_users(c);uid=crm.user_id(c,actor);parts=urlsplit(path);action=parts.path.rsplit('/',1)[-1];q={k:v[0] for k,v in parse_qs(parts.query).items()}
 def get_entity():
  e=q.get('entity') or data.get('entity')
  if e not in ENTITIES:raise ValueError('Unknown portal feature')
  return e
 if action=='meta' and method=='GET':
  enabled={e:s for e,s in crm.SCHEMA.items() if e in ENTITIES and 'crm.'+crm.MODULES[e]+'.view' in perms}
  return {'schema':enabled,'permissions':sorted(perms),'uid':uid,'productLines':product_lines(c)}
 if action in ['sales-board','sales-summary','workflow-board'] and method=='GET':
  entity=q.get('entity','Leads')
  if entity not in WORKFLOWS:raise ValueError('Unknown workflow')
  crm.need(perms,crm.MODULES[entity]);leads=workflow_records(c,perms,uid,entity,q)
  summary=sales_summary(c,actor,perms,leads,q) if entity=='Leads' else None
  if action=='sales-summary':
   if entity!='Leads':raise ValueError('Sales summary is for Sales Plan')
   return summary
  stage_entity,fk=WORKFLOWS[entity];crm.need(perms,crm.MODULES[stage_entity]);stages=stages_list(c,stage_entity,q.get('project') if stage_entity=='ProjectPipeline' else None);groups=[];ids={x['Id'] for x in stages}
  if stage_entity=='ProjectPipeline' and 'crm.projects.view' in perms:
   for stage in stages:stage['ProjectName']=(crm.raw(c,'Projects',stage.get('ProjectId')) or {}).get('Name') or '#'+str(stage.get('ProjectId'))
  for stage in [None]+stages:
   matched=[r for r in leads if (r.get(fk)==stage['Id'] if stage else r.get(fk) not in ids)]
   groups.append({'stage':stage,'count':len(matched),'totals':currency_totals(matched) if entity=='Leads' else {},'budget':sum(float(r.get('Budget') or 0) for r in matched) if entity=='ProjectActivity' else 0,'items':matched[:30],'page':1})
  return {'columns':groups,'summary':summary,'total':len(leads)}
 if action=='stage-list' and method=='GET':
  entity=q.get('entity','CRMPipelines');child,fk=stage_config(entity);crm.need(perms,crm.MODULES[entity]);stages=stages_list(c,entity,q.get('project'))
  if {'crm.'+crm.MODULES[child]+'.view','crm.'+crm.MODULES[child]+'.view_all'}<=set(perms):
   leads=crm.rows(c,child)
   for stage in stages:stage['usage']=sum(r.get(fk)==stage['Id'] for r in leads)
  return stages
 if action=='save-stages' and method=='POST':
  entity=data.get('entity','CRMPipelines');stage_config(entity);crm.need(perms,crm.MODULES[entity]);changes=data.get('stages',[])
  if not isinstance(changes,list) or len(changes)>100:raise ValueError('Save up to 100 stage changes at a time')
  c.execute('SAVEPOINT stage_changes')
  try:
   for row in changes:
    if not isinstance(row,dict):raise ValueError('Invalid stage changes')
    handle(c,actor,perms,'/api/crm/native/save','POST',{'entity':entity,'record':row.get('record',{}),'version':row.get('version')})
   c.execute('RELEASE SAVEPOINT stage_changes');return stages_list(c,entity,data.get('project'))
  except Exception:
   c.execute('ROLLBACK TO SAVEPOINT stage_changes');c.execute('RELEASE SAVEPOINT stage_changes');raise
 if action=='stage-reorder' and method=='POST':
  crm.need(perms,'pipelines','edit');stages=stages_list(c);ids=data.get('ids',[]);versions=data.get('versions',{})
  if not isinstance(ids,list) or len(ids)!=len(set(ids)) or set(ids)!={r['Id'] for r in stages}:raise ValueError('Stages changed; reload before reordering')
  for stage in stages:
   if versions.get(str(stage['Id']))!=stage['_version']:raise ValueError('A stage changed; reload before reordering')
  for position,id in enumerate(ids,1):
   crm.update(c,'CRMPipelines',id,{'Order':position});crm.audit(c,actor,'CRMPipelines',id,'reorder',{'Order':position})
  return {'saved':True}
 if action=='stage-delete' and method=='POST':
  entity=data.get('entity','CRMPipelines');child,fk=stage_config(entity);crm.need(perms,crm.MODULES[entity],'delete');id=int(data.get('id',0));stage,version=record(c,perms,uid,entity,id)
  if data.get('version')!=version:raise ValueError('Stage changed; reload before removing')
  linked=[r for r in crm.rows(c,child) if r.get(fk)==id];replacement=data.get('replacementId')
  c.execute('SAVEPOINT remove_stage')
  try:
   if linked:
    crm.need(perms,crm.MODULES[child],'edit');crm.need(perms,crm.MODULES[child],'view_all')
    if not replacement or str(replacement)==str(id):raise ValueError('Choose a replacement stage or Unassigned for existing records')
    replacement=None if replacement=='unassigned' else int(replacement)
    if replacement is not None:
     target,_=record(c,perms,uid,entity,replacement)
     if entity=='ProjectPipeline' and target.get('ProjectId')!=stage.get('ProjectId'):raise ValueError('Choose a replacement stage in the same project')
    for lead in linked:
     handle(c,actor,perms,'/api/crm/native/save','POST',{'entity':child,'record':{'Id':lead['Id'],fk:replacement},'version':c.execute('SELECT version FROM crm_records WHERE entity=? AND id=?',(child,lead['Id'])).fetchone()[0]})
   result=crm.mutate(c,actor,perms,uid,entity,'delete',{'Id':id});c.execute('RELEASE SAVEPOINT remove_stage');return {**result,'moved':len(linked)}
  except Exception:
   c.execute('ROLLBACK TO SAVEPOINT remove_stage');c.execute('RELEASE SAVEPOINT remove_stage');raise
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
 if action=='save-form' and method=='POST':
  entity=get_entity();allowed={'HelpDeskTickets':('HelpDeskItems','TicketId'),'Projects':('ProjectPipeline','ProjectId'),'ProjectPipeline':('ProjectActivity','ProjectPipelineId')}
  children=data.get('children',[])
  if not isinstance(children,list) or len(children)>100:raise ValueError('A form supports up to 100 changed lines per save')
  if children and entity not in allowed:raise ValueError('This form has no editable item lines')
  c.execute('SAVEPOINT portal_form')
  try:
   saved=handle(c,actor,perms,'/api/crm/native/save','POST',{'entity':entity,'record':data.get('record',{}),'version':data.get('version')})
   for line in children:
    child,fk=allowed[entity]
    if not isinstance(line,dict) or line.get('entity')!=child or line.get('action','save') not in ['save','delete']:raise ValueError('Invalid item line')
    values=dict(line.get('record',{}));old=None
    if values.get('Id'):
     old,_=record(c,perms,uid,child,int(values['Id']))
     if old.get(fk)!=saved['Id']:raise policy.PermissionDenied('Item does not belong to this record')
    if values.get(fk) not in [None,saved['Id']]:raise ValueError('Cannot move an item to a different parent')
    values[fk]=saved['Id'];operation=line.get('action','save')
    if operation=='delete' and not old:raise ValueError('Cannot delete an unsaved item')
    if operation=='save':
     required='Description' if child=='HelpDeskItems' else 'Name'
     if not str(values.get(required,(old or {}).get(required)) or '').strip():raise ValueError('Every item line needs a '+required.lower())
    handle(c,actor,perms,'/api/crm/native/'+operation,'POST',{'entity':child,'record':values,'version':line.get('version')})
   c.execute('RELEASE SAVEPOINT portal_form');return saved
  except Exception:
   c.execute('ROLLBACK TO SAVEPOINT portal_form');c.execute('RELEASE SAVEPOINT portal_form');raise
 entity=get_entity();module=crm.MODULES[entity];crm.need(perms,module)
 if action=='options' and method=='GET':
  search=q.get('search','').casefold();selected=set(q.get('selected','').split(','));out=[]
  for obj,ver in accessible(c,perms,uid,entity):
   label=(str(obj.get('FirstName') or '')+' '+str(obj.get('LastName') or '')).strip() if entity=='Users' else obj.get(NAMES.get(entity,'Name')) or obj.get('PipelineName') or obj.get('Description') or '#'+str(obj['Id'])
   if (search in str(label).casefold() and len(out)<100) or str(obj['Id']) in selected:out.append({'id':obj['Id'],'label':str(label),**({'order':obj.get('Order')} if entity in ['CRMPipelines','HelpDeskPipelines','ProjectPipeline'] else {}),**({'projectId':obj.get('ProjectId')} if entity=='ProjectPipeline' else {})})
  return out
 if action=='list' and method=='GET':
  line_cache={};page=max(1,int(q.get('page',1)));size=min(1000 if entity=='Events' else 100,max(1,int(q.get('size',30))));items=[];total=0;search=q.get('search','').casefold()
  for obj,ver in accessible(c,perms,uid,entity):
   if entity=='Leads':obj['ProductLine']=lead_line(c,obj,line_cache)
   if entity=='Leads' and q.get('line') and lead_line(c,obj)!=q['line']:continue
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
     if str(obj.get('ProjectId') or stage.get('ProjectId'))!=q['project']:continue
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
 if entity in ['CRMPipelines','HelpDeskPipelines','ProjectPipeline']:
  allowed={'CRMPipelines':['open','won','lost'],'HelpDeskPipelines':['open','in_progress','waiting','resolved','closed'],'ProjectPipeline':['open','in_progress','done','cancelled']}[entity]
  if 'StageType' in values and values['StageType'] not in allowed+[None,'']:raise ValueError('Choose a valid stage outcome')
  if values.get('Color') and not __import__('re').fullmatch(r'#[0-9a-fA-F]{6}',str(values['Color'])):raise ValueError('Choose a valid stage colour')
 if entity=='HelpDeskTickets' and 'PipelineId' in values and (not prior or values['PipelineId']!=prior.get('PipelineId')):
  stage=crm.raw(c,'HelpDeskPipelines',values['PipelineId']) or {};values['Status']=stage.get('Name') or 'Unassigned';values['PipelineStatus']=workflow_stage_type('HelpDeskPipelines',stage)
 if entity=='ProjectActivity':
  merged_stage=values.get('ProjectPipelineId',(prior or {}).get('ProjectPipelineId'));stage=crm.raw(c,'ProjectPipeline',merged_stage) or {}
  old_stage=crm.raw(c,'ProjectPipeline',(prior or {}).get('ProjectPipelineId')) or {}
  if merged_stage:
   if values.get('ProjectId') and values['ProjectId']!=stage.get('ProjectId'):raise ValueError('Choose a stage belonging to the selected project')
   values['ProjectId']=stage.get('ProjectId')
  else:values.setdefault('ProjectId',(prior or {}).get('ProjectId') or old_stage.get('ProjectId'))
  if 'ProjectPipelineId' in values and (not prior or values['ProjectPipelineId']!=prior.get('ProjectPipelineId')):
   values['Done']={'done':'Completed','cancelled':'Cancelled','in_progress':'In progress'}.get(workflow_stage_type('ProjectPipeline',stage),'Planned')
 if entity=='Leads':
  if values.get('ProductLine') and len(str(values['ProductLine']))>250:raise ValueError('Product line is too long')
  if 'CRMPipelineId' in values and (not prior or values['CRMPipelineId']!=prior.get('CRMPipelineId')):
   stage=crm.raw(c,'CRMPipelines',values['CRMPipelineId']) or {};kind=stage_kind(stage)
   values['WinOrLost']=True if kind=='won' else False if kind=='lost' else None
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
