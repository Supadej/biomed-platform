"""Versioned budget targets and independently reviewed period closure snapshots."""
import json,uuid,datetime,math,hashlib
import permissions_policy as policy
KEY='biomed_budget_v60_years'
def initialize(c):
 c.execute('CREATE TABLE IF NOT EXISTS budget_governance(year TEXT PRIMARY KEY,payload TEXT NOT NULL,version INTEGER NOT NULL)')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def workspace(c,year):
 row=c.execute('select value from workspace where key=?',(KEY,)).fetchone();data=json.loads(row[0]) if row else {};return data,data.get('years',{}).get(str(year),{})
def identity(r,kind):
 return [kind,str(r.get('costCenter') or r.get('division') or 'Unassigned'),str(r.get('category') or 'Other expenses') if kind=='Expense' else str(r.get('brand') or r.get('revenueSource') or 'Other revenue')]
def grouped(state):
 out={}
 for collection,kind,budget,actual in [('products','Revenue','budget','revenueActual'),('products','COGS','cogsBudget','cogsActual'),('expenses','Expense','budget','actual')]:
  for r in state.get(collection,[]):
   if r.get('active')==False:continue
   key=identity(r,kind);k=json.dumps(key);g=out.setdefault(k,{'id':str(uuid.uuid5(uuid.NAMESPACE_URL,k)),'kind':kind,'costCenter':key[1],'source':key[2],'revenueType':'Brand' if r.get('brand') else 'Other','target':[0]*12,'actual':[0]*12})
   for i in range(12):
    for field,name in [(budget,'target'),(actual,'actual')]:g[name][i]+=float((r.get(field) or [0]*12)[i] or 0)
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
def decide(record,body,actor,perms):
 if record.get('status') not in STAGES:raise ValueError('This submission is not awaiting approval')
 if str(actor[4])==record['submittedBy']:raise policy.PermissionDenied('Another authorized employee must approve this submission')
 action=body['action'];reason=str(body.get('reason') or '').strip()
 stage,permission=STAGES[record['status']]
 policy.need(perms,'budget.approvals.'+('return' if action=='return' else permission))
 if action=='return' and not reason:raise ValueError('A return reason is required')
 record['status']='Returned' if action=='return' else stage
 record.setdefault('history',[]).append({'at':now(),'by':actor[4],'name':actor[2],'action':record['status'],'reason':reason})
def actual_snapshot(state,start,end):
 return [{'key':identity(r,k),'id':r.get('id'),'actual':[(r.get(field) or [0]*12)[i] for i in range(start,end+1)]} for coll,k,field in [('products','Revenue','revenueActual'),('products','COGS','cogsActual'),('expenses','Expense','actual')] for r in state.get(coll,[])]
def guard(c,old,new):
 initialize(c)
 for year,payload in c.execute('select year,payload from budget_governance'):
  g=json.loads(payload);a=old.get('years',{}).get(year,{});b=new.get('years',{}).get(year,{})
  for r in g['reviews']:
   if r['status']=='Approved' and actual_snapshot(a,r['start'],r['end'])!=actual_snapshot(b,r['start'],r['end']):raise ValueError('Performance period is finalized. Reopen it with Director authorization and a reason before changing actuals.')
  if g.get('approved'):
   def budgets(s):return [(r.get('id'),r.get('budget'),r.get('cogsBudget'),[(x.get('id'),x.get('budget')) for x in r.get('componentRows',[])] ) for coll in ['products','expenses'] for r in s.get(coll,[])]
   if budgets(a)!=budgets(b):raise ValueError('An approved budget exists. Submit a revised target plan through Budget setting and approvals.')
def publish(c,year,lines,actual=False):
 data,state=workspace(c,year)
 for kind,coll,field in ([('Revenue','products','revenueActual'),('COGS','products','cogsActual'),('Expense','expenses','actual')] if actual else [('Revenue','products','budget'),('COGS','products','cogsBudget'),('Expense','expenses','budget')]):
  targets={json.dumps([l['kind'],l['costCenter'],l['source']]):l for l in lines if l['kind']==kind}
  for key,line in targets.items():
   rows=[r for r in state.get(coll,[]) if json.dumps(identity(r,kind))==key and r.get('active')!=False]
   if not rows:
    row={'id':'PLAN-'+str(uuid.uuid4()),'name':line['source'],'costCenter':line['costCenter'],'division':line['costCenter'],'active':True,'budget':[0]*12}
    if coll=='products':row.update(brand=line['source'] if line['revenueType']=='Brand' else '',revenueSource=line['source'],revenueType=line['revenueType'],cogsBudget=[0]*12,revenueActual=[0]*12,cogsActual=[0]*12)
    else:row.update(category=line['source'],actual=[0]*12,commitment=[0]*12)
    state.setdefault(coll,[]).append(row);rows=[row]
   for i,total in enumerate(line['target']):
    weights=[float((r.get(field) or [0]*12)[i] or 0) for r in rows];den=sum(weights);used=0
    for j,r in enumerate(rows):
     value=total-used if j==len(rows)-1 else total*(weights[j]/den if den else 1/len(rows));r.setdefault(field,[0]*12)[i]=value;used+=value
     if kind=='Expense' and r.get('componentRows'):
      components=r['componentRows'];components[0].setdefault(field,[0]*12)[i]=value
      for component in components[1:]:component.setdefault(field,[0]*12)[i]=0
 data.setdefault('years',{})[str(year)]=state;c.execute('update workspace set value=?,revision=revision+1 where key=?',(json.dumps(data,ensure_ascii=False),KEY))
def handle(h,method,connect,session,permissions,origin):
 actor=session(h)
 if not actor:return h.reply(401,{'error':'Sign in required'})
 try:
  perms=permissions(actor);policy.need(perms,'budget_view','budget.approvals.view')
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
    if not 0<size<=2000000:raise ValueError('Invalid request size')
    body=json.loads(h.rfile.read(size));action=body.get('action')
    if body.get('version')!=version:return h.reply(409,{'error':'Plan changed; refresh before saving'})
    if action in ['save','submit']:
     policy.need(perms,'budget.approvals.submit')
     if g.get('draft',{} ) and g['draft']['status'] in STAGES:raise ValueError('Return the pending submission before changing its targets')
     lines=body.get('lines')
     if not isinstance(lines,list) or not 1<=len(lines)<=2000:raise ValueError('Add target lines')
     clean=[];seen=set();brands={r[0] for r in c.execute('select name from operational_brands where active=1')}
     for l in lines:
      kind=l.get('kind');source=str(l.get('source','')).strip();center=str(l.get('costCenter','')).strip();typ=l.get('revenueType','Other')
      if typ not in ['Brand','Service','Miscellaneous','Other'] or kind not in ['Revenue','COGS','Expense'] or not source or not center or len(source)>200 or len(center)>200:raise ValueError('Enter valid source and cost center')
      if kind in ['Revenue','COGS'] and typ=='Brand' and source not in brands:raise ValueError('Select an active shared brand')
      key=(kind,source.casefold(),center.casefold())
      if key in seen:raise ValueError('Consolidate duplicate source and cost-center lines')
      seen.add(key);clean.append({'id':l.get('id') or str(uuid.uuid4()),'kind':kind,'source':source,'costCenter':center,'revenueType':typ,'target':numbers(l.get('target'))})
     required={tuple(identity(r,k)) for coll,k in [('products','Revenue'),('products','COGS'),('expenses','Expense')] for r in state.get(coll,[]) if r.get('active')!=False}
     if not required.issubset({(l['kind'],l['costCenter'],l['source']) for l in clean}):raise ValueError('Retain all current source lines; set unwanted targets to zero instead of deleting them')
     g['draft']={'lines':clean,'status':'Submitted' if action=='submit' else 'Draft','submittedBy':str(actor[4]),'submittedName':actor[2],'at':now(),'revision':1+(g.get('approved') or {}).get('revision',0),'history':[]}
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
     if period!='Monthly' and any(not any(r['start']==i and r['end']==i and r['status']=='Approved' for r in g['reviews']) for i in range(start,end+1)):raise ValueError('Finalize each included monthly performance first')
     g['reviews'].append({'id':str(uuid.uuid4()),'period':period,'start':start,'end':end,'status':'Submitted','submittedBy':str(actor[4]),'submittedName':actor[2],'at':now(),'actualSnapshot':actual_snapshot(state,start,end),'budgetSnapshot':g['approved'],'history':[]})
    elif action=='reopen':
     policy.need(perms,'budget.approvals.director_approve');reason=str(body.get('reason') or '').strip()
     if not reason:raise ValueError('Explain why the finalized period must be reopened')
     record=next(r for r in g['reviews'] if r['id']==body.get('id'))
     if record['status']!='Approved':raise ValueError('Only finalized periods can be reopened')
     for r in g['reviews']:
      if r['status']=='Approved' and r['start']<=record['start'] and r['end']>=record['end']:r['status']='Reopened';r['history'].append({'at':now(),'by':actor[4],'name':actor[2],'action':'Reopened','reason':reason})
    elif action in ['approve','return']:
     record=next((r for r in g['reviews'] if r['id']==body.get('id')),None) if body.get('id') else g.get('draft')
     if not record:raise ValueError('Submission not found')
     if action=='approve' and 'actualSnapshot' in record and record['actualSnapshot']!=actual_snapshot(state,record['start'],record['end']):raise ValueError('Actuals changed after submission; return and resubmit this review')
     decide(record,body,actor,perms)
     if record['status']=='Approved' and 'lines' in record:publish(c,year,record['lines']);g['approved']=json.loads(json.dumps(record));g.setdefault('approvedVersions',[]).append(json.loads(json.dumps(record)))
    else:raise ValueError('Unknown action')
    g['history'].append({'at':now(),'by':actor[4],'name':actor[2],'action':action});c.execute('insert or replace into budget_governance values(?,?,?)',(year,json.dumps(g,ensure_ascii=False),version+1));version+=1
   _,state=workspace(c,year);return h.reply(200,{'governance':g,'workspaceRevision':c.execute('select revision from workspace where key=?',(KEY,)).fetchone()[0],'version':version,'current':grouped(state),'brands':[r[0] for r in c.execute('select name from operational_brands where active=1')],'userId':str(actor[4]),'permissions':sorted(perms)})
 except policy.PermissionDenied as ex:return h.reply(403,{'error':str(ex)})
 except (ValueError,TypeError,KeyError,StopIteration) as ex:return h.reply(400,{'error':str(ex) or 'Record not found'})
