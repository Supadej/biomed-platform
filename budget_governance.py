"""Versioned budget targets and independently reviewed period closure snapshots."""
import json,uuid,datetime,math,hashlib
import permissions_policy as policy
import budget_categories as refs
KEY='biomed_budget_v60_years'
def initialize(c):
 c.execute('CREATE TABLE IF NOT EXISTS budget_governance(year TEXT PRIMARY KEY,payload TEXT NOT NULL,version INTEGER NOT NULL)')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def workspace(c,year):
 row=c.execute('select value from workspace where key=?',(KEY,)).fetchone();data=json.loads(row[0]) if row else {};return data,data.get('years',{}).get(str(year),{})
def identity(r,kind):
 return [kind,str(r.get('costCenter') or r.get('division') or 'Unassigned'),str(r.get('financialSource') or ((r.get('category') or 'Other expenses')+' · '+(r.get('name') or r.get('id','')))) if kind=='Expense' else str(r.get('brand') or r.get('revenueSource') or r.get('name') or 'Other revenue')]
def expense_group(category):
 if category=='Other Cost of Sales':return refs.GROUPS[2]
 if category in ['Salary and Bonus','Commission and Incentive','Social Security and Provident Fund','Social Security & PVF','Healthcare Coverage']:return refs.GROUPS[3]
 if category in ['Local Traveling and Expenses','Overseas Traveling and Expenses','Trainings and KOM']:return refs.GROUPS[4]
 return refs.GROUPS[5]
def current_references(c,year):
 data,state=workspace(c,year)
 return {'costCenters':state.get('costCenters',[]),'sources':[{'id':x['id'],'name':identity(x,'Expense')[2],'group':expense_group(x.get('category')),'active':x.get('active') is not False} for x in state.get('expenses',[])]}
def mapped_lines(lines,state):
 out=[]
 for line in lines:
  matches=[x for x in state.get('expenses',[]) if x.get('active') is not False and (x.get('costCenter') or x.get('division'))==line.get('costCenter') and (x.get('id')==line.get('lineId') or identity(x,'Expense')[2]==line.get('source') or x.get('category')==line.get('source'))] if line.get('kind')=='Expense' else []
  if not matches:out.append(line);continue
  amounts=[[float((x.get('budget') or [0]*12)[i] or 0) for x in matches] for i in range(12)]
  allocations=[[0]*12 for x in matches]
  for i,total in enumerate(line['target']):
   den=sum(amounts[i]);used=0
   for j in range(len(matches)):
    n=float(total)-used if j==len(matches)-1 else float(total)*(amounts[i][j]/den if den else 1/len(matches));allocations[j][i]=n;used+=n
  for j,item in enumerate(matches):out.append({**line,'id':str(item['id']),'lineId':item['id'],'category':item.get('category'),'source':identity(item,'Expense')[2],'group':expense_group(item.get('category')),'target':allocations[j]})
 return out
def grouped(state):
 out={}
 for collection,kind,budget,actual in [('products','Revenue','budget','revenueActual'),('products','COGS','cogsBudget','cogsActual'),('expenses','Expense','budget','actual')]:
  for r in state.get(collection,[]):
   if r.get('active')==False:continue
   key=identity(r,kind);k=json.dumps(key);g=out.setdefault(k,{'id':str(uuid.uuid5(uuid.NAMESPACE_URL,k)),'kind':kind,'costCenter':key[1],'source':key[2],'revenueType':'Brand' if r.get('brand') else 'Other','target':[0]*12,'actual':[0]*12,'commitment':[0]*12,'expenseMenu':policy.CATEGORY.get(r.get('category'),'manage_items') if kind=='Expense' else None,'category':r.get('category') if kind=='Expense' else None,'lineId':r.get('id') if kind=='Expense' else None,'group':expense_group(r.get('category')) if kind=='Expense' else refs.GROUPS[0 if kind=='Revenue' else 1]})
   for i in range(12):
    for field,name in [(budget,'target'),(actual,'actual')]+([('commitment','commitment')] if kind=='Expense' else []):g[name][i]+=float((r.get(field) or [0]*12)[i] or 0)
 return list(out.values())
def load(c,year):
 initialize(c);row=c.execute('select payload,version from budget_governance where year=?',(str(year),)).fetchone()
 return (json.loads(row[0]),row[1]) if row else ({'draft':None,'approved':None,'reviews':[],'history':[]},0)
def numbers(values,negative=False):
 if not isinstance(values,list) or len(values)!=12:raise ValueError('Enter all twelve fiscal months')
 v=[float(x) for x in values]
 if any(not math.isfinite(x) or (x<0 and not negative) or abs(x)>1e15 for x in v):raise ValueError('Targets must be finite nonnegative amounts')
 return v
STAGES={'Submitted':('Department Approved','department_approve'),'Department Approved':('Finance Approved','finance_approve'),'Finance Approved':('Approved','director_approve')}
def decide(record,body,actor,perms,c=None):
 if record.get('status') not in STAGES:raise ValueError('This submission is not awaiting approval')
 if str(actor[4])==record['submittedBy'] and not policy.admin_self_approval(actor,c):raise policy.PermissionDenied('Another authorized employee must approve this submission')
 action=body['action'];reason=str(body.get('reason') or '').strip()
 stage,permission=STAGES[record['status']]
 if record['status']=='Submitted' and c is not None and not policy.is_system_admin(actor):
  row=c.execute("select value from workspace where key='biomed_portal_v33_clean'").fetchone();users=json.loads(row[0]).get('users',[]) if row else []
  owners={str(l.get('owner') or record['submittedBy']) for l in record.get('lines',[])} or {record['submittedBy']}
  managers={str(u.get('managerId') or '') for u in users if str(u.get('id')) in owners}
  if not managers or '' in managers or str(actor[4]) not in managers:raise policy.PermissionDenied('Department review requires the reporting manager of a budget owner; assign reporting managers before submission.')
  if action=='approve':
   approvals=set(record.get('departmentApprovals',[]));approvals.add(str(actor[4]));record['departmentApprovals']=sorted(approvals)
   if not managers.issubset(approvals):stage='Submitted'
 policy.need(perms,'budget.approvals.'+('return' if action in ['return','reject'] else permission))
 if action in ['return','reject'] and not reason:raise ValueError('A return reason is required')
 if c is not None and str(actor[4])==record['submittedBy']:policy.self_approval_audit(c,actor,'Budget/performance',record.get('id','target'))
 record['status']=('Rejected' if action=='reject' else 'Returned') if action in ['return','reject'] else stage
 record.setdefault('history',[]).append({'at':now(),'by':actor[4],'name':actor[2],'action':record['status'],'reason':reason})
def actual_snapshot(state,start,end):
 return [{'key':identity(r,k),'id':r.get('id'),'actual':[(r.get(field) or [0]*12)[i] for i in range(start,end+1)]} for coll,k,field in [('products','Revenue','revenueActual'),('products','COGS','cogsActual'),('expenses','Expense','actual')] for r in state.get(coll,[])]
def guard(c,old,new):
 initialize(c)
 for year,b in new.get('years',{}).items():
  a=old.get('years',{}).get(year,{})
  before={str(r.get('id')):r for coll in ['products','expenses'] for r in a.get(coll,[])}
  for coll in ['products','expenses']:
   for r in b.get(coll,[]):
    prior=before.get(str(r.get('id')),{} )
    for field in ['budget','cogsBudget']:
     if numbers(r.get(field,[0]*12))!=numbers(prior.get(field,[0]*12)):raise ValueError('Set budgets only in Annual & Monthly Budget; use other menus for actuals.')
    components={x.get('id'):x for x in prior.get('componentRows',[])}
    for item in r.get('componentRows',[]):
     if numbers(item.get('budget',[0]*12))!=numbers(components.get(item.get('id'),{}).get('budget',[0]*12)):raise ValueError('Set component budgets only in Annual & Monthly Budget.')
 for year,payload in c.execute('select year,payload from budget_governance'):
  g=json.loads(payload);a=old.get('years',{}).get(year,{});b=new.get('years',{}).get(year,{})
  for r in g['reviews']:
   if g.get('settings',{}).get('periodLockEnabled',True) and r.get('locked',True) and r['status']=='Approved' and actual_snapshot(a,r['start'],r['end'])!=actual_snapshot(b,r['start'],r['end']):raise ValueError('Performance period is finalized. Reopen it with Director authorization and a reason before changing actuals.')
  if g.get('approved'):
   def budgets(s):return [(r.get('id'),r.get('budget'),r.get('cogsBudget'),[(x.get('id'),x.get('budget')) for x in r.get('componentRows',[])] ) for coll in ['products','expenses'] for r in s.get(coll,[])]
   old_budget={str(x[0]):x for x in budgets(a)};new_budget={str(x[0]):x for x in budgets(b)}
   if any(new_budget.get(k)!=v for k,v in old_budget.items()) or any(any(float(n or 0)!=0 for values in [v[1] or [],v[2] or []]+[row[1] or [] for row in v[3]] for n in values) for k,v in new_budget.items() if k not in old_budget):raise ValueError('An approved budget exists. Submit a revised target plan through Budget setting and approvals.')
def publish(c,year,lines,actual=False):
 data,state=workspace(c,year)
 for kind,coll,field in ([('Revenue','products','revenueActual'),('COGS','products','cogsActual'),('Expense','expenses','actual')] if actual else [('Revenue','products','budget'),('COGS','products','cogsBudget'),('Expense','expenses','budget')]):
  targets={json.dumps([l['kind'],l['costCenter'],l['source']]):l for l in lines if l['kind']==kind}
  for key,line in targets.items():
   rows=[r for r in state.get(coll,[]) if ((kind=='Expense' and line.get('lineId') and r.get('id')==line['lineId']) or json.dumps(identity(r,kind))==key) and r.get('active')!=False]
   if not rows:
    row={'id':'PLAN-'+str(uuid.uuid4()),'name':line.get('expenseName') or line['source'],'costCenter':line['costCenter'],'division':line['costCenter'],'active':True,'budget':[0]*12}
    if coll=='products':row.update(brand=line['source'] if line['revenueType']=='Brand' else '',revenueSource=line['source'],revenueType=line['revenueType'],cogsBudget=[0]*12,revenueActual=[0]*12,cogsActual=[0]*12)
    else:row.update(category=line.get('category') or {'Other Cost of Sales Budget':'Other Cost of Sales','Personnel & Benefits Budget':'Salary and Bonus','Travel & Training Budget':'Local Traveling and Expenses','Other Operating Expenses Budget':'Other Expenses'}.get(line.get('group'),line['source']),financialSource=line['source'],actual=[0]*12,commitment=[0]*12)
    state.setdefault(coll,[]).append(row);rows=[row]
   for row in rows:
    if kind in ['Revenue','COGS'] and line.get('associatedBrand'):row['associatedBrand']=line['associatedBrand']
    if kind=='Expense' and row.get('category')=='Other Cost of Sales' and not row.get('componentRows'):
     row['componentRows']=[{'id':'allocation-'+str(row['id']),'name':'Unallocated amount','active':True,**{k:list(row.get(k) or [0]*12) for k in ['budget','actual','commitment']}}]
   for i,total in enumerate(line['target']):
    weights=[float((r.get(field) or [0]*12)[i] or 0) for r in rows];den=sum(weights);used=0
    for j,r in enumerate(rows):
     value=total-used if j==len(rows)-1 else total*(weights[j]/den if den else 1/len(rows));r.setdefault(field,[0]*12)[i]=value;used+=value
     if kind=='Expense' and r.get('componentRows'):
      components=r['componentRows'];weights=[float((x.get(field) or [0]*12)[i] or 0) for x in components];den=sum(weights);allocated=0
      for j,component in enumerate(components):
       share=value-allocated if j==len(components)-1 else value*(weights[j]/den if den else 1/len(components));component.setdefault(field,[0]*12)[i]=share;allocated+=share
 data.setdefault('years',{})[str(year)]=state;c.execute('update workspace set value=?,revision=revision+1 where key=?',(json.dumps(data,ensure_ascii=False),KEY))
def monthly_effective(g):
 """Only approved monthly snapshots authorize budget; never infer from annual plan."""
 records=g.get('monthlyBudgets',[]);result=[]
 for month in range(12):
  approved=[r for r in records if r['month']==month and r['status']=='Approved']
  record=approved[-1] if approved else None
  result.append({'month':month,'approved':bool(record),'revision':record.get('revision') if record else None,'lines':record['lines'] if record else []})
 return result

def submit_month(g,body,actor,perms):
 policy.need(perms,'budget.approvals.submit')
 month=body.get('month')
 if type(month) is not int or not 0<=month<12:raise ValueError('Select a valid fiscal month')
 plan=g.get('approved')
 if not plan:raise ValueError('Approve the annual plan before submitting monthly allocations')
 records=g.setdefault('monthlyBudgets',[])
 if any(r['month']==month and r['status'] in STAGES for r in records):raise ValueError('This month already has a pending budget approval')
 snapshot=[{**l,'amount':l['target'][month]} for l in plan['lines']]
 prior=[r for r in records if r['month']==month and r['status']=='Approved']
 if prior and prior[-1]['lines']==snapshot:raise ValueError('This monthly allocation is already approved; revise the annual plan first')
 records.append({'id':str(uuid.uuid4()),'month':month,'lines':snapshot,'annualRevision':plan['revision'],'revision':1+max([r.get('revision',0) for r in records if r['month']==month] or [0]),'status':'Submitted','submittedBy':str(actor[4]),'submittedName':actor[2],'at':now(),'history':[]})

def handle(h,method,connect,session,permissions,origin):
 actor=session(h)
 if not actor:return h.reply(401,{'error':'Sign in required'})
 try:
  perms=permissions(actor)
  for permission in ['budget_view','budget.approvals.view']:policy.need(perms,permission)
  from urllib.parse import parse_qs,urlsplit
  year=str(parse_qs(urlsplit(h.path).query).get('year',[''])[0])
  if not year.isdigit() or not 2000<=int(year)<=2200:raise ValueError('Select a fiscal year')
  with connect() as c:
   c.execute('BEGIN IMMEDIATE');g,version=load(c,year);data,state=workspace(c,year)
   if not state:raise ValueError('Fiscal year not found')
   if any(not policy.budget_row_visible(perms,r,product=coll=='products') for coll in ['products','expenses'] for r in state.get(coll,[])):raise policy.PermissionDenied('Company-wide budget planning requires view access to every included revenue and expense schedule')
   if method=='POST':
    if not origin(h):return h.reply(403,{'error':'Invalid origin'})
    size=int(h.headers.get('Content-Length',0))
    if not 0<size<=8000000:raise ValueError('Invalid request size')
    body=json.loads(h.rfile.read(size));action=body.get('action')
    if body.get('version')!=version:return h.reply(409,{'error':'Plan changed; refresh before saving'})
    if action=='source-reference':
     policy.need(perms,'budget.approvals.submit')
     items=g.setdefault('sourceReferences',[]);ref=next((r for r in items if r['id']==body.get('id')),None)
     name=str(body.get('name') or '').strip()
     if not name or len(name)>200:raise ValueError('Enter a reference name (up to 200 characters)')
     if any(r['name'].casefold()==name.casefold() and r is not ref for r in items):raise ValueError('Reference names must be unique')
     if ref and ref['name']!=name:
      used=any(l.get('source')==ref['name'] for rec in [g.get('draft'),g.get('approved')]+g.get('approvedVersions',[]) for l in (rec or {}).get('lines',[]))
      used=used or any(identity(r,'Revenue')[2]==ref['name'] for r in state.get('products',[]))
      if used:raise ValueError('This source has budget history. Deactivate it and create a new name instead.')
     if ref:ref.update(name=name,active=body.get('active',True) is True)
     else:items.append({'id':str(uuid.uuid4()),'name':name,'active':True})
    elif action in ['save','submit']:
     policy.need(perms,'budget.approvals.submit')
     if g.get('draft',{} ) and g['draft']['status'] in STAGES:raise ValueError('Return the pending submission before changing its targets')
     lines=body.get('lines')
     if not isinstance(lines,list) or not 1<=len(lines)<=2000:raise ValueError('Add target lines')
     clean=[];seen=set();brands={r[0] for r in c.execute('select name from operational_brands where active=1')}
     for l in lines:
      kind=l.get('kind');source=str(l.get('source','')).strip();center=str(l.get('costCenter','')).strip();typ=l.get('revenueType','Other')
      item=None
      if kind=='Expense':
       item=next((x for x in state.get('expenses',[]) if x.get('id')==l.get('lineId') and x.get('active') is not False),None)
       legacy_source=any(identity(x,'Expense')[2]==source and identity(x,'Expense')[1]==center for x in state.get('expenses',[]))
       if not item and not legacy_source:raise ValueError('Select an Expense Item from Manage expense items')
       if item:
        if item.get('category')!=l.get('category') or (item.get('costCenter') or item.get('division'))!=center:raise ValueError('Expense item must match its menu category and cost center')
        source=identity(item,'Expense')[2]
      if kind in ['Revenue','COGS'] and typ!='Brand':
       old_sources={identity(x,k)[2] for x in state.get('products',[]) for k in ['Revenue','COGS']}
       old_sources|={x['source'] for x in (g.get('draft') or {}).get('lines',[])}
       if source not in old_sources and source not in {x['name'] for x in g.get('sourceReferences',[]) if x.get('active')}:raise ValueError('Select an active Service / other revenue source reference')
      associated_brand=str(l.get('associatedBrand') or '')
      if associated_brand and associated_brand not in brands:raise ValueError('Select an active shared brand')
      if typ not in ['Brand','Service','Miscellaneous','Other'] or kind not in ['Revenue','COGS','Expense'] or not source or not center or len(source)>200 or len(center)>200:raise ValueError('Enter valid source and cost center')
      if kind in ['Revenue','COGS'] and typ=='Brand' and source not in brands:raise ValueError('Select an active shared brand')
      key=(kind,source.casefold(),center.casefold())
      if key in seen:raise ValueError('Consolidate duplicate source and cost-center lines')
      reference_data=current_references(c,year)
      oldkeys={tuple(identity(r,k)) for coll,k in [('products','Revenue'),('products','COGS'),('expenses','Expense')] for r in state.get(coll,[])}
      oldkeys|={(r['kind'],r['costCenter'],r['source']) for r in (g.get('draft') or {}).get('lines',[])}
      legacy=(kind,center,source) in oldkeys
      if not legacy and center not in {r['name'] for r in reference_data['costCenters'] if r.get('active')}:raise ValueError('Select an active shared cost center')
      reference=next((r for r in reference_data['sources'] if r['name']==source and r.get('active')),None)
      category=str(l.get('category') or '').strip()
      if kind=='Expense' and not reference and not legacy and category not in policy.CATEGORY:raise ValueError('Choose the linked expense menu category')
      group=(expense_group(category) if kind=='Expense' and category else None) or l.get('group') or (reference or {}).get('group') or ('Revenue Target Budget' if kind=='Revenue' else 'Product Cost of Sales Budget' if kind=='COGS' else 'Other Cost of Sales Budget' if source=='Other Cost of Sales' else 'Other Operating Expenses Budget')
      if group not in refs.GROUPS:raise ValueError('Select a budget category')
      if (kind=='Revenue' and group!=refs.GROUPS[0]) or (kind=='COGS' and group!=refs.GROUPS[1]) or (kind=='Expense' and group not in refs.GROUPS[2:]):raise ValueError('Source category does not match the selected plan type')
      owner=str(l.get('owner') or actor[4]);people=json.loads(c.execute("select value from workspace where key='biomed_portal_v33_clean'").fetchone()[0]).get('users',[])
      if owner not in {str(u['id']) for u in people if u.get('active') is not False}:raise ValueError('Select an active budget owner')
      comment=str(l.get('comment') or '')[:4000];attachments=l.get('attachments') or []
      if not isinstance(attachments,list) or len(attachments)>3:raise ValueError('Maximum three supporting files per line')
      import base64
      for attachment in attachments:
       if not isinstance(attachment,dict) or not isinstance(attachment.get('name'),str) or len(attachment['name'])>200:raise ValueError('Invalid supporting file')
       value=attachment.get('data','')
       if not isinstance(value,str) or not value.startswith(('data:application/pdf;base64,','data:image/png;base64,','data:image/jpeg;base64,')):raise ValueError('Use PDF, PNG or JPEG supporting files')
       blob=base64.b64decode(value.split(',',1)[1],validate=True)
       if len(blob)>1000000 or not blob.startswith((b'%PDF',b'\x89PNG',b'\xff\xd8')):raise ValueError('Invalid file or file exceeds 1 MB')
      seen.add(key);clean.append({'id':l.get('id') or str(uuid.uuid4()),'kind':kind,'source':source,'costCenter':center,'revenueType':typ,'associatedBrand':associated_brand,'expenseName':item.get('name') if item else str(l.get('expenseName') or '')[:200],'category':category if kind=='Expense' else None,'target':numbers(l.get('target')),'lineId':item['id'] if item else l.get('lineId'),'owner':owner,'group':group,'comment':comment,'attachments':attachments})
     required={tuple(identity(r,k)) for coll,k in [('products','Revenue'),('products','COGS'),('expenses','Expense')] for r in state.get(coll,[]) if r.get('active')!=False}
     if not required.issubset({(l['kind'],l['costCenter'],l['source']) for l in clean}):raise ValueError('Retain all current source lines; set unwanted targets to zero instead of deleting them')
     if g.get('draft'):g.setdefault('submissionArchive',[]).append(json.loads(json.dumps(g['draft'])))
     g['draft']={'lines':clean,'status':'Submitted' if action=='submit' else 'Draft','submittedBy':str(actor[4]),'submittedName':actor[2],'at':now(),'revision':1+(g.get('approved') or {}).get('revision',0),'history':[]}
    elif action=='submit-month':
     submit_month(g,body,actor,perms)
    elif action=='actual':
     if body.get('workspaceRevision')!=c.execute('select revision from workspace where key=?',(KEY,)).fetchone()[0]:return h.reply(409,{'error':'Actuals changed in another view; refresh before recording totals'})
     lines=body.get('lines')
     if not isinstance(lines,list) or len(lines)>2000:raise ValueError('Invalid actual lines')
     existing={tuple(identity(r,k)) for coll,k in [('products','Revenue'),('products','COGS'),('expenses','Expense')] for r in state.get(coll,[]) if r.get('active')!=False}
     for l in lines:
      if (l.get('kind'),l.get('costCenter'),l.get('source')) not in existing:raise ValueError('Approve a target source before recording its actuals')
      numbers(l.get('target'),negative=True)
      if l['kind']=='Expense':policy.need(perms,'budget.'+policy.CATEGORY[l['source']]+'.actual' if l['source'] in policy.CATEGORY else 'budget.manage_items.edit')
      else:policy.need(perms,'budget.'+('products' if l['kind']=='Revenue' else 'cogs')+'.actual')
     before=json.loads(json.dumps(data));publish(c,year,lines,actual=True);after,_=workspace(c,year);guard(c,before,after)
    elif action=='review':
     policy.need(perms,'budget.approvals.submit')
     if not g.get('approved'):raise ValueError('Approve the annual target budget before performance review')
     if body.get('verified') is not True:raise ValueError('Verify actuals and supporting records before submission')
     period=body.get('period');index=int(body.get('index',0));start,end=(index,index) if period=='Monthly' and 0<=index<12 else (index*6,index*6+5) if period=='Half-year' and index in [0,1] else (0,11) if period=='Annual' else (-1,-1)
     if start<0:raise ValueError('Choose a valid performance period')
     from zoneinfo import ZoneInfo
     next_month=(int(year)-1)*12+4+end+1
     closing=datetime.date(next_month//12,next_month%12+1,1)
     if datetime.datetime.now(ZoneInfo('Asia/Bangkok')).date()<closing:raise ValueError('The selected fiscal period has not ended yet')
     if any(r['start']==start and r['end']==end and r['status'] not in ['Returned','Reopened'] for r in g['reviews']):raise ValueError('This period already has a review')
     if period!='Monthly' and any(not any(r['start']==i and r['end']==i and r['status']=='Approved' and r['actualSnapshot']==actual_snapshot(state,i,i) for r in g['reviews']) for i in range(start,end+1)):raise ValueError('Finalize each included monthly performance first')
     g['reviews'].append({'id':str(uuid.uuid4()),'period':period,'start':start,'end':end,'status':'Submitted','submittedBy':str(actor[4]),'submittedName':actor[2],'at':now(),'actualSnapshot':actual_snapshot(state,start,end),'budgetSnapshot':g['approved'],'history':[]})
    elif action in ['reopen','unlock']:
     policy.need(perms,'budget.periods.unlock');reason=str(body.get('reason') or '').strip()
     if not reason:raise ValueError('Explain why the finalized period must be reopened')
     record=next(r for r in g['reviews'] if r['id']==body.get('id'))
     if record['status']!='Approved':raise ValueError('Only finalized periods can be reopened')
     for r in g['reviews']:
      if r['status']=='Approved' and r['start']<=record['start'] and r['end']>=record['end']:r['status']='Reopened';r['locked']=False;r['history'].append({'at':now(),'by':actor[4],'name':actor[2],'action':'Reopened','reason':reason})
    elif action=='lock-settings':
     policy.need(perms,'budget.periods.configure')
     if type(body.get('enabled')) is not bool:raise ValueError('Choose whether period locking is enabled')
     reason=str(body.get('reason') or '').strip()
     if not reason:raise ValueError('A reason is required for lock policy changes')
     g.setdefault('settings',{})['periodLockEnabled']=body['enabled']
     if body['enabled']:
      for review in g['reviews']:
       if review['status']=='Approved' and review['actualSnapshot']!=actual_snapshot(state,review['start'],review['end']):
        review['status']='Reopened';review['locked']=False;review['history'].append({'at':now(),'by':actor[4],'name':actor[2],'action':'Reapproval required after unlocked actual changes','reason':reason})
     g['history'].append({'at':now(),'by':actor[4],'name':actor[2],'action':'Lock policy enabled' if body['enabled'] else 'Lock policy disabled','reason':reason})
    elif action in ['approve','return','reject']:
     record=next((r for r in g['reviews']+g.get('monthlyBudgets',[]) if r['id']==body.get('id')),None) if body.get('id') else g.get('draft')
     if not record:raise ValueError('Submission not found')
     if action=='approve' and 'actualSnapshot' in record and record['actualSnapshot']!=actual_snapshot(state,record['start'],record['end']):raise ValueError('Actuals changed after submission; return and resubmit this review')
     decide(record,body,actor,perms,c)
     if record['status']=='Approved' and 'actualSnapshot' in record:record['locked']=g.get('settings',{}).get('periodLockEnabled',True)
     if record['status']=='Approved' and 'lines' in record and 'month' not in record:publish(c,year,mapped_lines(record['lines'],state));g['approved']=json.loads(json.dumps(record));g.setdefault('approvedVersions',[]).append(json.loads(json.dumps(record)))
    else:raise ValueError('Unknown action')
    g['history'].append({'at':now(),'by':actor[4],'name':actor[2],'action':action});c.execute('insert or replace into budget_governance values(?,?,?)',(year,json.dumps(g,ensure_ascii=False),version+1));version+=1
   _,state=workspace(c,year);return h.reply(200,{'governance':g,'mappedPlanLines':mapped_lines(((g.get('draft') or g.get('approved') or {}).get('lines') or grouped(state)),state),'effectiveMonthly':monthly_effective(g),'workspaceRevision':c.execute('select revision from workspace where key=?',(KEY,)).fetchone()[0],'version':version,'current':grouped(state),'expenseItems':[{'id':r['id'],'name':r.get('name'),'category':r.get('category'),'costCenter':r.get('costCenter') or r.get('division'),'source':identity(r,'Expense')[2]} for r in state.get('expenses',[]) if r.get('active') is not False],'expenseCategories':list(policy.CATEGORY),'references':current_references(c,year),'people':[{'id':u['id'],'name':u['name']} for u in json.loads(c.execute("select value from workspace where key='biomed_portal_v33_clean'").fetchone()[0]).get('users',[]) if u.get('active') is not False],'brands':[r[0] for r in c.execute('select name from operational_brands where active=1')],'userId':str(actor[4]),'adminSelfApprovalTesting':policy.admin_self_approval(actor,c),'permissions':sorted(perms)})
 except policy.PermissionDenied as ex:return h.reply(403,{'error':str(ex)})
 except (ValueError,TypeError,KeyError,StopIteration) as ex:return h.reply(400,{'error':str(ex) or 'Record not found'})
