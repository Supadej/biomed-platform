"""Authenticated, revision-checked integration operations, separate from general workspace writes."""
import json,hashlib,datetime,uuid,copy
import integration_engine as engine
import permissions_policy as policy
PKEY='biomed_portal_v33_clean';IKEY='biomed_is_v50_transactions';BKEY='biomed_budget_v60_years'
def initialize(c):
 c.executescript('CREATE TABLE IF NOT EXISTS integration_config(id TEXT PRIMARY KEY,value TEXT NOT NULL,revision INTEGER NOT NULL);CREATE TABLE IF NOT EXISTS integration_runs(id TEXT PRIMARY KEY,bridge TEXT NOT NULL,at TEXT NOT NULL,actor TEXT NOT NULL,summary TEXT NOT NULL);')
def workspace(c,key):
 r=c.execute('SELECT value,revision FROM workspace WHERE key=?',(key,)).fetchone();return (json.loads(r[0]) if r and r[0] else {}),r[1] if r else 0
def put(c,key,value,revision):
 if key==BKEY:
  import budget_governance
  budget_governance.guard(c,workspace(c,key)[0],value)
 c.execute('INSERT OR REPLACE INTO workspace VALUES(?,?,?)',(key,json.dumps(value,ensure_ascii=False),revision+1))
def settings(c,id,default):
 r=c.execute('SELECT value,revision FROM integration_config WHERE id=?',(id,)).fetchone();return ({**copy.deepcopy(default),**json.loads(r[0])} if r else copy.deepcopy(default),r[1] if r else 0)
def clean(direction,data,portal,store,year):
 if not isinstance(data,dict):raise ValueError('Invalid settings')
 default=engine.IS_DEFAULT if direction=='is-portal' else engine.BUDGET_DEFAULT
 c={k:data.get(k,copy.deepcopy(v)) for k,v in default.items()}
 for k,v in default.items():
  if isinstance(v,bool) and not isinstance(c[k],bool):raise ValueError('Invalid switch: '+k)
 if direction=='is-portal':
  if c['amountBasis'] not in ['net','gross','grand'] or c['dateField'] not in ['date','due'] or c['staffField'] not in ['portalRep','owner']:raise ValueError('Invalid document rule')
  if not isinstance(c['quotationStatuses'],list) or not set(c['quotationStatuses'])<=set(['Draft','Pending','Approved','Rejected','Cancelled']):raise ValueError('Invalid quotation statuses')
  for k in ['staffMap','productMap','rates']:
   if not isinstance(c[k],dict):raise ValueError('Invalid mapping')
  if len(c['productMap'])>10000:raise ValueError('Too many mappings')
  for code,rate in c['rates'].items():
   if not isinstance(code,str) or len(code)>6 or engine.number(rate)<=0:raise ValueError('Currency rates must be positive THB conversion rates')
  if engine.number(c['rates'].get('THB'))!=1:raise ValueError('THB rate must remain 1')
  if any(v not in {u['id'] for u in portal.get('users',[])} for v in c['staffMap'].values()):raise ValueError('Choose existing Portal users')
  if any(v not in portal.get('productLines',[]) for v in c['productMap'].values()):raise ValueError('Choose existing Portal product lines')
 else:
  if str(year) not in store.get('years',{}):raise ValueError('Fiscal year does not exist')
  if c['dateBasis'] not in ['statusDate','sourceDate'] or c['expenseAmount'] not in ['claimTotal','paymentAmount']:raise ValueError('Invalid financial rule')
  if not isinstance(c['rules'],list) or len(c['rules'])>1000:raise ValueError('Invalid mapping rules')
  targets={r['id'] for r in store['years'][str(year)].get('expenses',[]) if r.get('active',True) and r.get('category')!='Other Cost of Sales'}
  for r in c['rules']:
   if r.get('module') not in ['expenses','incentives','requests'] or r.get('target') not in targets:raise ValueError('Map each rule to an active expense line')
 return c
def handle(handler,direction,action,year,body,connection,actor,perms,project):
 if direction not in ['is-portal','portal-budget']:raise ValueError('Unknown bridge')
 module='portal.integration_is' if direction=='is-portal' else 'budget.portal_bridge'
 policy.need(perms,module+'.view')
 if policy.visibility.contextual(perms) and not policy.visibility.admin(perms):
  relevant=[m for m in policy.visibility.modules() if m.startswith('is.') or m.startswith('portal.')]
  if any(policy.visibility.scope(perms,m)!='all' for m in relevant):raise policy.PermissionDenied('Company-wide reconciliation requires System Admin; normal document access follows your record visibility')
 if direction=='portal-budget':policy.need(perms,'budget_view')
 key=direction if direction=='is-portal' else direction+':'+str(year)
 default=engine.IS_DEFAULT if direction=='is-portal' else engine.BUDGET_DEFAULT
 config,revision=settings(connection,key,default);portal,pr=workspace(connection,PKEY);source,ir=workspace(connection,IKEY);budget,br=workspace(connection,BKEY)
 if action=='save':
  policy.need(perms,module+'.edit')
  if body.get('revision')!=revision:raise ValueError('Settings changed in another session. Reload before saving.')
  config=clean(direction,body.get('config'),portal,budget,year)
  connection.execute('INSERT OR REPLACE INTO integration_config VALUES(?,?,?)',(key,json.dumps(config),revision+1));return {'saved':True,'revision':revision+1}
 history=[dict(id=r[0],at=r[1],actor=r[2],summary=json.loads(r[3])) for r in connection.execute('SELECT id,at,actor,summary FROM integration_runs WHERE bridge=? ORDER BY at DESC LIMIT 15',(direction,))]
 if action=='config':
  if direction=='is-portal':
   used={str(l.get('productId')) for d in source.get('documents',[]) for l in d.get('lines',[])}
   options={'users':[{'id':u['id'],'name':u.get('name',u['id'])} for u in portal.get('users',[])],'productLines':portal.get('productLines',[]),'staffIds':sorted({str(d.get(field) or '') for d in source.get('documents',[]) for field in ['portalRep','owner'] if d.get(field)}),'products':[{'id':p['id'],'name':p.get('name',p['id'])} for p in source.get('products',[]) if str(p['id']) in used][:1500]}
  else:
   options={'years':sorted(budget.get('years',{})),'targets':[{'id':x['id'],'name':x.get('name',''),'category':x.get('category',''),'costCenter':x.get('costCenter','')} for x in budget.get('years',{}).get(str(year),{}).get('expenses',[]) if x.get('active',True) and x.get('category')!='Other Cost of Sales' and policy.financial_view(perms,x,'actual')],'categories':{'expenses':sorted({x.get('category','') for x in portal.get('expenses',[])}),'incentives':['Incentives'],'requests':['travel','budget']},'departments':portal.get('departments',[])}
  return {'config':config,'revision':revision,'options':options,'history':history,'canEdit':module+'.edit' in perms,'canRun':module+'.reconcile' in perms,'year':year}
 policy.need(perms,module+'.reconcile')
 if direction=='is-portal':
  policy.need(perms,'is_view');plan=engine.is_projection(source,portal,config)
  if config['quotations']:policy.need(perms,'is.quotation.view')
  if config['sales']:policy.need(perms,'is.invoice.view');policy.need(perms,'is.credit-note.view')
  proposed=None
 else:
  configs={str(r[0]).split(':',1)[1]:json.loads(r[1]) for r in connection.execute("SELECT id,value FROM integration_config WHERE id LIKE 'portal-budget:%'")}
  configs.setdefault(str(year),config);plan=engine.budget_plan(portal,budget,configs);proposed=engine.reconcile_budget(budget,plan)
  for cfg in configs.values():
   if cfg.get('enabled') and cfg.get('actuals'):policy.need(perms,'payments')
   for enabled,view in [('expenses','expenses'),('incentives','incentives'),('requests','requests')]:
    if cfg.get('enabled') and cfg.get(enabled):policy.need(perms,view)
  # A reconciliation can release prior-year commitments; require access to every affected schedule.
  for ykey,y in proposed.get('years',{}).items():
   before=budget.get('years',{}).get(ykey,{})
   for row in y.get('expenses',[]):
    old=next((r for r in before.get('expenses',[]) if r['id']==row['id']),{})
    category=policy.CATEGORY.get(row.get('category'),'manage_items')
    if any(l.get('bridge')=='portal-budget' and l.get('line')==row['id'] for l in y.get('ledger',[])+before.get('ledger',[])):policy.need(perms,'budget.'+category+'.view')
    for field,grant in [('actual','actual'),('commitment','commitment')]:
     if row.get(field)!=old.get(field):policy.need(perms,'budget.'+category+'.'+grant)
 token=hashlib.sha256(json.dumps({'plan':plan,'revisions':[pr,ir,br],'config':config,'configs':configs if direction=='portal-budget' else None},sort_keys=True).encode()).hexdigest()
 if action=='preview':return {'previousPostings':[dict(row,year=fy) for fy,y in budget.get('years',{}).items() for row in y.get('ledger',[]) if row.get('bridge')=='portal-budget'] if direction=='portal-budget' else [],'plan':plan,'token':token,'message':'Preview only; no records have been changed. Portal-to-Financial reconciliation refreshes bridge postings across all configured fiscal years to release old commitments.'}
 if action!='run':raise ValueError('Unknown operation')
 if body.get('token')!=token:raise ValueError('Source records or settings changed. Preview again before syncing.')
 if plan['exceptions'] and not body.get('allowPartial'):raise ValueError('Resolve exceptions, or explicitly allow posting eligible records only.')
 now=datetime.datetime.now(datetime.timezone.utc).isoformat()
 if direction=='is-portal':
  for field in ['pipeline','salesActuals']:
   portal[field]=[r for r in portal.get(field,[]) if not str(r.get('sourceId','')).startswith('biomed-is-v50:')]
  portal['integrationIS']={**plan,'syncedAt':now,'configRevision':revision};put(connection,PKEY,portal,pr)
  summary={'quotations':len(plan['quotations']),'salesRows':len(plan['salesActuals']),'exceptions':len(plan['exceptions'])}
 else:put(connection,BKEY,proposed,br);summary={'postings':len(plan['postings']),'exceptions':len(plan['exceptions']),'fiscalYears':sorted({p['year'] for p in plan['postings']})}
 summary['rulesUsed']=configs if direction=='portal-budget' else config
 connection.execute('INSERT INTO integration_runs VALUES(?,?,?,?,?)',(uuid.uuid4().hex,direction,now,actor[2],json.dumps(summary)))
 return {'synced':True,'summary':summary}
