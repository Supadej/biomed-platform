"""Shared operational brands. Website brand catalogue is intentionally independent."""
import json,uuid,datetime,sqlite3
import permissions_policy as policy
KEYS=['biomed_is_v50_transactions','biomed_portal_v33_clean','biomed_budget_v60_years']
def initialize(c):
 c.executescript('CREATE TABLE IF NOT EXISTS operational_brands(id TEXT PRIMARY KEY,name TEXT NOT NULL COLLATE NOCASE UNIQUE,active INTEGER NOT NULL DEFAULT 1,version INTEGER NOT NULL DEFAULT 1);CREATE TABLE IF NOT EXISTS operational_brand_audit(id INTEGER PRIMARY KEY,at TEXT,actor TEXT,action TEXT,payload TEXT);')
 if c.execute('select count(*) from operational_brands').fetchone()[0]:
  normalize(c);return
 names=set()
 row=c.execute('select value from workspace where key=?',(KEYS[0],)).fetchone()
 if row:names|={str(x.get('brand','')).strip() for x in json.loads(row[0]).get('products',[])}
 for p, in c.execute('select payload from fse_records'):
  names.add(str(json.loads(p).get('brand') or '').strip())
 row=c.execute('select value from workspace where key=?',(KEYS[1],)).fetchone()
 if row:names|=set(json.loads(row[0]).get('productLines',[]))
 for name in sorted(names):
  if name:c.execute('insert or ignore into operational_brands(id,name) values(?,?)',(str(uuid.uuid4()),name))
 sync(c);normalize(c)
def normalize(c):
 canonical={r['name'].strip().casefold():r['name'] for r in rows(c)};names=set()
 def scan(v):
  if isinstance(v,dict):
   for k,x in v.items():
    if k in ['brand','Brand'] and isinstance(x,str):names.add(x)
    elif k!='brands':scan(x)
  elif isinstance(v,list):
   for x in v:scan(x)
 for key in KEYS:
  row=c.execute('select value from workspace where key=?',(key,)).fetchone()
  if row:scan(json.loads(row[0]))
 for table in ['fse_records','crm_records']:
  for p, in c.execute('select payload from '+table):scan(json.loads(p))
 for name in names:
  target=canonical.get(name.strip().casefold())
  if target and target!=name:sync(c,name,target)
def rows(c):return [dict(id=i,name=n,active=bool(a),version=v) for i,n,a,v in c.execute('select * from operational_brands order by name collate nocase')]
def sync(c,old=None,new=None):
 names=[r['name'] for r in rows(c) if r['active']]
 def walk(v):
  if isinstance(v,dict):
   for k,x in v.items():
    if old and isinstance(x,str) and k in ['brand','Brand','line','ProductLine'] and x==old:v[k]=new
    elif old and k=='BrandNames' and isinstance(x,list):v[k]=[new if t==old else t for t in x]
    elif k!='customerSignature':walk(x)
  elif isinstance(v,list):
   for x in v:walk(x)
 for key in KEYS:
  row=c.execute('select value from workspace where key=?',(key,)).fetchone()
  if not row:continue
  data=json.loads(row[0]);website=data.pop('brands',None) if key==KEYS[1] else None;walk(data)
  if key==KEYS[1]:
   if website is not None:data['brands']=website
   data['productLines']=names
  data['operationalBrands']=rows(c)
  c.execute('update workspace set value=?,revision=revision+1 where key=?',(json.dumps(data,ensure_ascii=False),key))
 for table,idcols in [('fse_records','id'),('crm_records','entity,id')]:
  for row in c.execute('select '+idcols+',payload from '+table).fetchall():
   data=json.loads(row[-1]);before=json.dumps(data,ensure_ascii=False);walk(data);after=json.dumps(data,ensure_ascii=False)
   if before!=after:c.execute('update '+table+' set payload=?,version=version+1 where '+' and '.join(k+'=?' for k in idcols.split(',')),(after,*row[:-1]))
 row=c.execute('select payload from service_setup where id=1').fetchone()
 if row:
  data=json.loads(row[0]);walk(data);data['brands']=names;c.execute('update service_setup set payload=?,version=version+1 where id=1',(json.dumps(data,ensure_ascii=False),))
 # Regenerate product master projection after a rename.
 if old:
  import serve
  row=c.execute('select value from workspace where key=?',(KEYS[0],)).fetchone()
  if row:serve.project(c,row[0])
def validate_workspace(c,key,before,after):
 if key not in KEYS:return
 old=json.loads(before or '{}');new=json.loads(after or '{}')
 if new.get('operationalBrands')!=old.get('operationalBrands'):raise ValueError('Manage operational brands through Biomed IS → Master Data → Brands')
 if key==KEYS[1] and new.get('productLines')!=old.get('productLines'):raise ValueError('Manage product brands through Biomed IS → Master Data → Brands')
 allowed={x['name'] for x in rows(c) if x['active']}
 def check(a,b):
  if isinstance(b,dict):
   for k,v in b.items():
    prior=a.get(k) if isinstance(a,dict) else None
    if k in ['brand','Brand'] and v and v!=prior and v not in allowed:raise ValueError('Select an active operational brand')
    if k!='brands':check(prior,v)
  elif isinstance(b,list):
   previous={str(x.get('id')):x for x in (a or []) if isinstance(x,dict)} if isinstance(a,list) else {}
   for x in b:
    if isinstance(x,dict):check(previous.get(str(x.get('id')),{}),x)
 check(old,new)
def dispatch(c,actor,perms,body=None):
 if not {'is_view','crm_view','budget_view','service.view'}&set(perms):raise policy.PermissionDenied('Module access required')
 if body is None:return {'brands':rows(c),'canManage':'is.master-products.edit' in perms and 'is_view' in perms}
 policy.need(perms,'is_view');policy.need(perms,'is.master-products.edit')
 action=body.get('action');ident=body.get('id');prior=c.execute('select name,version from operational_brands where id=?',(ident,)).fetchone()
 if action=='create':
  name=str(body.get('name') or '').strip()
  if not name or len(name)>200:raise ValueError('Enter a brand name, maximum 200 characters')
  c.execute('insert into operational_brands(id,name) values(?,?)',(str(uuid.uuid4()),name));sync(c)
 else:
  if not prior or prior[1]!=body.get('version'):raise ValueError('Brand changed; refresh before saving')
  if action=='rename':
   name=str(body.get('name') or '').strip()
   if not name or len(name)>200:raise ValueError('Enter a brand name, maximum 200 characters')
   c.execute('update operational_brands set name=?,version=version+1 where id=?',(name,ident));sync(c,prior[0],name)
  elif action in ['remove','restore']:
   # Referenced brands are archived so historical documents remain intelligible.
   c.execute('update operational_brands set active=?,version=version+1 where id=?',(int(action=='restore'),ident));sync(c)
  else:raise ValueError('Unknown brand action')
 c.execute('insert into operational_brand_audit(at,actor,action,payload) values(?,?,?,?)',(datetime.datetime.now(datetime.timezone.utc).isoformat(),str(actor[4]),action,json.dumps(body)))
 return {'brands':rows(c),'canManage':True}
def handle(h,method,connect,session,permissions,origin):
 actor=session(h)
 if not actor:return h.reply(401,{'error':'Sign in required'})
 try:
  body=None
  if method=='POST':
   if not origin(h):raise policy.PermissionDenied('Invalid origin')
   n=int(h.headers.get('Content-Length','0'))
   if not 0<n<=10000:raise ValueError('Invalid request size')
   body=json.loads(h.rfile.read(n))
  with connect() as c:
   if method=='POST':c.execute('begin immediate')
   result=dispatch(c,actor,permissions(actor),body)
  return h.reply(200,result)
 except policy.PermissionDenied as e:return h.reply(403,{'error':str(e)})
 except (ValueError,TypeError,KeyError,sqlite3.IntegrityError) as e:return h.reply(400,{'error':str(e)})
