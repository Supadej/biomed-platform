"""Approved engineer custody transfers and transaction-bound job consumption."""
import json,uuid,datetime,math,sqlite3
from collections import defaultdict
import permissions_policy as policy
KEY='biomed_is_v50_transactions'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def initialize(c):
 c.executescript('''CREATE TABLE IF NOT EXISTS service_inventory_requests(id TEXT PRIMARY KEY,payload TEXT NOT NULL,version INTEGER NOT NULL);
 CREATE TABLE IF NOT EXISTS service_inventory_ledger(id TEXT PRIMARY KEY,at TEXT NOT NULL,engineer TEXT NOT NULL,product_id TEXT NOT NULL,lot TEXT NOT NULL,expiry TEXT NOT NULL,qty REAL NOT NULL,action TEXT NOT NULL,reference TEXT NOT NULL,actor TEXT NOT NULL);
 CREATE TABLE IF NOT EXISTS service_inventory_allocations(job_id TEXT PRIMARY KEY,payload TEXT NOT NULL);
 CREATE TABLE IF NOT EXISTS service_inventory_baseline(job_id TEXT PRIMARY KEY,payload TEXT NOT NULL);
 CREATE TABLE IF NOT EXISTS service_inventory_checks(id TEXT PRIMARY KEY,payload TEXT NOT NULL,version INTEGER NOT NULL);
 CREATE TABLE IF NOT EXISTS service_inventory_billing(job_id TEXT PRIMARY KEY,invoice_id TEXT NOT NULL,created_at TEXT NOT NULL);
 CREATE TABLE IF NOT EXISTS service_inventory_workflow_audit(id INTEGER PRIMARY KEY,at TEXT,actor TEXT,action TEXT,payload TEXT);''')
 part_products={i:json.loads(p).get('productId') for i,p in c.execute("SELECT id,payload FROM fse_records WHERE kind='parts'")}
 # Pre-existing job history must never create a retroactive stock deduction or phantom return.
 for ident,payload in c.execute("SELECT id,payload FROM fse_records WHERE kind='jobs'").fetchall():
  if not c.execute('SELECT 1 FROM service_inventory_allocations WHERE job_id=?',(ident,)).fetchone():
   r=json.loads(payload);total=defaultdict(float)
   for p in r.get('partsUsed',[]):
    product=p.get('productId') or part_products.get(p.get('partId'))
    if product:total[product]+=float(p.get('qty') or 0)
   c.execute('INSERT OR IGNORE INTO service_inventory_baseline VALUES(?,?)',(ident,json.dumps(total)))
def need(perms,action='view'):
 policy.need(perms,'is_view');policy.need(perms,'is.service-inventory.view')
 if action!='view':policy.need(perms,'is.service-inventory.'+action)
def warehouse_state(c):
 row=c.execute('SELECT value FROM workspace WHERE key=?',(KEY,)).fetchone();return json.loads(row[0]) if row else {}
def entries(c):return [dict(zip(['id','at','engineer','productId','lot','expiry','qty','action','reference','actor'],r)) for r in c.execute('SELECT * FROM service_inventory_ledger ORDER BY at DESC,id')]
def balances(c):
 return [dict(engineer=e,productId=p,lot=l,expiry=x,qty=q) for e,p,l,x,q in c.execute('SELECT engineer,product_id,lot,expiry,SUM(qty) FROM service_inventory_ledger GROUP BY engineer,product_id,lot,expiry HAVING ABS(SUM(qty))>0.00000001')]
def post(c,actor,engineer,product,lot,expiry,qty,action,ref):
 c.execute('INSERT INTO service_inventory_ledger VALUES(?,?,?,?,?,?,?,?,?,?)',(str(uuid.uuid4()),now(),engineer,product,lot,expiry,float(qty),action,ref,str(actor[4])))
def stock_post(c,actor,request,line,change):
 data=warehouse_state(c);movement={'id':'SI-'+request['id']+'-'+str(line['index']),'at':now(),'productId':line['productId'],'warehouse':line['warehouse'],'lot':line['lot'],'expiry':line.get('expiry',''),'change':change,'source':request['ref'],'docId':request['id'],'serviceInventory':True,'by':actor[4]}
 if any(m.get('id')==movement['id'] for m in data.get('movements',[])):raise ValueError('This transfer has already been posted')
 data.setdefault('movements',[]).append(movement)
 c.execute('UPDATE workspace SET value=?,revision=revision+1 WHERE key=?',(json.dumps(data,ensure_ascii=False),KEY))
 pos=c.execute("SELECT COALESCE(MAX(position),-1)+1 FROM stock_records WHERE category='movements'").fetchone()[0];c.execute("INSERT INTO stock_records VALUES('movements',?,?)",(pos,json.dumps(movement)))
def active_engineers(c):
 import service_catalog
 return service_catalog.engineers(c)
def dispatch(c,actor,perms,body=None):
 need(perms);pid=str(actor[4]);manager='is.service-inventory.approve' in perms
 import service_inventory_workflows as workflows
 if body and body.get('action') in ['stock-check','stock-check-approve','stock-check-reject','stock-check-cancel','add-to-invoice','unlink-invoice']:return workflows.dispatch(c,actor,perms,body)
 if body is None:
  workflow=workflows.read(c,actor,perms);read_all=manager or workflows.billing_reader(perms)
  data=warehouse_state(c);products={str(x['id']):x for x in data.get('products',[])};central=defaultdict(float);exp={}
  for m in data.get('movements',[]):
   key=(m.get('productId',''),m.get('warehouse',''),m.get('lot',''));central[key]+=float(m.get('change') or 0);exp[key]=m.get('expiry') or exp.get(key,'')
  catalogue={json.loads(p).get('productId') for p, in c.execute("SELECT payload FROM fse_records WHERE kind='parts'")}
  requests=[dict(json.loads(p),version=v) for p,v in c.execute('SELECT payload,version FROM service_inventory_requests ORDER BY rowid DESC')]
  names={str(i):n for i,n in c.execute('SELECT user_id,name FROM accounts')};return {**workflow,'people':[{'id':i,'name':n} for i,n in names.items()],'warehouses':[str(x.get('id') or x.get('name')) if isinstance(x,dict) else str(x) for x in data.get('warehouses',[])],'userId':pid,'permissions':sorted(perms),'engineers':active_engineers(c),'products':[{field:x.get(field,'') for field in ['id','name','sku','catalogueNo','unit']} for k,x in products.items() if k in catalogue],'central':[dict(productId=p,warehouse=w,lot=l,expiry=exp[(p,w,l)],qty=q) for (p,w,l),q in central.items() if p in catalogue and q>0],'balances':[r for r in balances(c) if read_all or r['engineer']==pid],'requests':[r for r in requests if manager or r['engineer']==pid],'jobs':[{'id':i,'jobNo':json.loads(p).get('jobNo')} for i,p in c.execute("SELECT id,payload FROM fse_records WHERE kind='jobs'")] if 'service.jobs.view' in perms else [],'ledger':[r for r in entries(c) if read_all or r['engineer']==pid]}
 action=body.get('action')
 if action=='request':
  kind=body.get('kind');need(perms,'return' if kind=='Return' else 'request')
  if kind not in ['Request','Return']:raise ValueError('Choose Request or Return')
  engineer=str(body.get('engineer') or pid)
  if engineer!=pid and not manager:raise policy.PermissionDenied('Request only your own service inventory')
  if engineer not in {x['id'] for x in active_engineers(c)}:raise ValueError('Choose an active service engineer')
  lines=body.get('lines',[])
  if not isinstance(lines,list) or not 1<=len(lines)<=100:raise ValueError('Add 1–100 part lines')
  data=warehouse_state(c);products={str(x['id']) for x in data.get('products',[])};warehouses={str(v) for x in data.get('warehouses',[]) for v in ([x.get('id'),x.get('name')] if isinstance(x,dict) else [x]) if v};catalogue={json.loads(p).get('productId') for p, in c.execute("SELECT payload FROM fse_records WHERE kind='parts'")};clean=[]
  for index,line in enumerate(lines):
   qty=float(line.get('qty',0))
   if not math.isfinite(qty) or qty<=0:raise ValueError('Quantity must be positive')
   if line.get('productId') not in products or line.get('productId') not in catalogue:raise ValueError('Select a declared service spare part')
   if line.get('warehouse') not in warehouses:raise ValueError('Select an existing warehouse')
   if not isinstance(line.get('lot'),str) or not line['lot'].strip():raise ValueError('A traceable lot is required')
   expiry=line.get('expiry') or ''
   if expiry:
    try:datetime.date.fromisoformat(expiry)
    except (TypeError,ValueError):raise ValueError('Invalid expiry')
   clean.append({'index':index,'productId':line['productId'],'warehouse':line['warehouse'],'lot':line['lot'].strip(),'expiry':expiry,'qty':qty})
  ident=str(uuid.uuid4());date=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime('%d-%m-%y');seq=c.execute('SELECT COUNT(*) FROM service_inventory_requests WHERE json_extract(payload,\'$.day\')=?',(date,)).fetchone()[0]+1
  r={'id':ident,'ref':('SIR' if kind=='Request' else 'SIRT')+date+'/'+str(seq),'day':date,'kind':kind,'engineer':engineer,'requester':pid,'createdAt':now(),'status':'Pending','note':str(body.get('note') or '')[:4000],'lines':clean,'history':[{'at':now(),'by':pid,'action':'Submitted'}]};c.execute('INSERT INTO service_inventory_requests VALUES(?,?,1)',(ident,json.dumps(r,ensure_ascii=False)));return {'id':ident}
 if action not in ['approve','reject','cancel']:raise ValueError('Unknown inventory operation')
 row=c.execute('SELECT payload,version FROM service_inventory_requests WHERE id=?',(body.get('id'),)).fetchone()
 if not row:raise ValueError('Request not found')
 r=json.loads(row[0])
 if row[1]!=body.get('version'):raise ValueError('Request changed; refresh before deciding')
 if r['status']!='Pending':raise ValueError('Request has already been decided')
 if action=='cancel':
  if r['requester']!=pid and not manager:raise policy.PermissionDenied('Only the requester or approver can cancel')
 else:
  need(perms,'approve')
  if pid in [r['requester'],r['engineer']]:raise policy.PermissionDenied('A different approver must approve or reject this request')
 if action=='reject' and not str(body.get('reason') or '').strip():raise ValueError('A rejection reason is required')
 if action=='approve':
  for line in r['lines']:
   if r['kind']=='Request':
    data=warehouse_state(c);matches=[m for m in data.get('movements',[]) if m.get('productId')==line['productId'] and m.get('warehouse')==line['warehouse'] and m.get('lot')==line['lot']];available=sum(float(m.get('change') or 0) for m in matches);expiry=next((m.get('expiry') for m in reversed(matches) if m.get('expiry')),'')
    if not matches or line['qty']>available+1e-8:raise ValueError('Insufficient warehouse stock for '+line['lot'])
    if line['expiry']!=expiry:raise ValueError('Expiry must match the warehouse lot')
    if expiry and expiry<datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).date().isoformat():raise ValueError('Expired stock cannot be issued')
    if any(q.get('productId')==line['productId'] and q.get('lot')==line['lot'] and q.get('status') not in ['Released','Closed','Cancelled'] for q in data.get('quarantines',[])):raise ValueError('Quarantined stock cannot be issued')
    stock_post(c,actor,r,line,-line['qty']);post(c,actor,r['engineer'],line['productId'],line['lot'],line['expiry'],line['qty'],'Approved issue',r['ref'])
   else:
    available=sum(x['qty'] for x in balances(c) if x['engineer']==r['engineer'] and x['productId']==line['productId'] and x['lot']==line['lot'] and x['expiry']==line['expiry'])
    if line['qty']>available+1e-8:raise ValueError('Parts were already used or returned; insufficient engineer balance')
    # Return only into an existing warehouse; expired stock remains visible by its original expiry.
    data=warehouse_state(c);wh={str(v) for x in data.get('warehouses',[]) for v in ([x.get('id'),x.get('name')] if isinstance(x,dict) else [x]) if v}
    if line['warehouse'] not in wh:raise ValueError('Return warehouse no longer exists')
    known={m.get('expiry') or '' for m in data.get('movements',[]) if m.get('productId')==line['productId'] and m.get('warehouse')==line['warehouse'] and m.get('lot')==line['lot']}
    if known and known!={line['expiry']}:raise ValueError('Return lot expiry conflicts with existing warehouse stock')
    stock_post(c,actor,r,line,line['qty']);post(c,actor,r['engineer'],line['productId'],line['lot'],line['expiry'],-line['qty'],'Approved return',r['ref'])
 r['status']={'approve':'Approved','reject':'Rejected','cancel':'Cancelled'}[action];r['history'].append({'at':now(),'by':pid,'action':r['status'],'reason':str(body.get('reason') or '')[:4000]});c.execute('UPDATE service_inventory_requests SET payload=?,version=version+1 WHERE id=?',(json.dumps(r,ensure_ascii=False),r['id']));return {'saved':True}
def consume(c,actor,perms,r,old):
 """Release and reallocate atomically. Saving unchanged lines never deducts twice."""
 row=c.execute('SELECT payload FROM service_inventory_allocations WHERE job_id=?',(r['id'],)).fetchone();previous=json.loads(row[0]) if row else []
 baseline_row=c.execute('SELECT payload FROM service_inventory_baseline WHERE job_id=?',(r['id'],)).fetchone();baseline=json.loads(baseline_row[0]) if baseline_row else {};desired=defaultdict(float)
 for p in r.get('partsUsed',[]):desired[p['productId']]+=float(p['qty'])
 desired={p:max(0,q-float(baseline.get(p,0))) for p,q in desired.items()};desired={p:q for p,q in desired.items() if q>1e-8}
 old_totals=defaultdict(float)
 for p in previous:old_totals[p['productId']]+=p['qty']
 import service_inventory_workflows
 service_inventory_workflows.protect_usage(c,r,previous,desired)
 if dict(old_totals)==desired and all(p['engineer']==(r.get('inventoryEngineer') or r.get('engineer')) for p in previous):return
 if not desired and not previous:return
 need(perms,'consume');engineer=str(r.get('inventoryEngineer') or r.get('engineer') or '')
 if desired and not engineer:raise ValueError('Select the engineer whose Service Inventory supplies these parts')
 if (engineer!=str(actor[4]) or any(p['engineer']!=str(actor[4]) for p in previous)) and 'is.service-inventory.approve' not in perms:raise policy.PermissionDenied('Only an inventory approver may post parts against another engineer')
 pool=defaultdict(float)
 for p in balances(c):pool[(p['engineer'],p['productId'],p['lot'],p['expiry'])]+=p['qty']
 for p in previous:pool[(p['engineer'],p['productId'],p['lot'],p['expiry'])]+=p['qty']
 allocation=[];today=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).date().isoformat()
 for product,qty in desired.items():
  for (eng,prod,lot,expiry),available in sorted(pool.items(),key=lambda kv:(kv[0][3] or '9999',kv[0][2])):
   if eng!=engineer or prod!=product or available<=0:continue
   if expiry and expiry<today:available=min(available,sum(p['qty'] for p in previous if (p['engineer'],p['productId'],p['lot'],p['expiry'])==(eng,prod,lot,expiry)))
   if available<=0:continue
   take=min(qty,available);allocation.append({'engineer':eng,'productId':prod,'lot':lot,'expiry':expiry,'qty':take});qty-=take
   if qty<1e-8:break
  if qty>1e-8:
   owner=next((e['name'] for e in active_engineers(c) if str(e['id'])==engineer),engineer or 'unselected engineer');available=max(0,desired[product]-qty)
   raise ValueError('Insufficient Service Inventory for '+product+' in '+owner+' custody: '+str(available)+' usable; '+str(desired[product])+' required. Choose the correct Parts supplied by engineer, or approve a stock request for that person. Consolidated stock held by other engineers is not this person’s balance.')
 if allocation==previous:return
 for p in previous:post(c,actor,p['engineer'],p['productId'],p['lot'],p['expiry'],p['qty'],'Job usage reversed',r['id'])
 for p in allocation:post(c,actor,p['engineer'],p['productId'],p['lot'],p['expiry'],-p['qty'],'Service job usage',r['id'])
 c.execute('INSERT OR REPLACE INTO service_inventory_allocations VALUES(?,?)',(r['id'],json.dumps(allocation)))
def protect(old,new):
 import service_inventory_workflows
 service_inventory_workflows.protect_invoices(old,new)
 before={m['id']:m for m in old.get('movements',[]) if m.get('serviceInventory')};after={m['id']:m for m in new.get('movements',[]) if m.get('serviceInventory')}
 if {m['productId'] for m in before.values()}-{str(p['id']) for p in new.get('products',[])}:raise policy.PermissionDenied('Products with Service Inventory history cannot be deleted; deactivate them instead')
 if before!=after:raise policy.PermissionDenied('Service Inventory warehouse postings are controlled by approved transfers and cannot be edited in a workspace save')
def handle(h,method,connect,session,permissions,origin):
 actor=session(h)
 if not actor:return h.reply(401,{'error':'Sign in through Staff Portal'})
 try:
  body=None
  if method=='POST':
   if not origin(h):raise policy.PermissionDenied('Invalid origin')
   n=int(h.headers.get('Content-Length','0'))
   if not 0<n<=100000:raise ValueError('Invalid request size')
   body=json.loads(h.rfile.read(n))
  with connect() as c:
   if method=='POST':c.execute('BEGIN IMMEDIATE')
   result=dispatch(c,actor,permissions(actor),body)
  return h.reply(200,result)
 except policy.PermissionDenied as e:return h.reply(403,{'error':str(e)})
 except (ValueError,TypeError,KeyError,sqlite3.IntegrityError) as e:return h.reply(400,{'error':str(e)})
