"""Shared, versioned cost centers and financial source reference records."""
import json,uuid
import permissions_policy as policy
GROUPS=['Revenue Target Budget','Product Cost of Sales Budget','Other Cost of Sales Budget','Personnel & Benefits Budget','Travel & Training Budget','Other Operating Expenses Budget']
def load(c):
 c.execute('CREATE TABLE IF NOT EXISTS financial_references(id INTEGER PRIMARY KEY CHECK(id=1),payload TEXT NOT NULL,version INTEGER NOT NULL)')
 r=c.execute('select payload,version from financial_references where id=1').fetchone()
 if r:return json.loads(r[0]),r[1]
 data={'costCenters':[],'sources':[]};names=set()
 for raw, in c.execute('select value from workspace'):
  try:value=json.loads(raw)
  except (ValueError,TypeError):continue
  def walk(v):
   if isinstance(v,dict):
    if isinstance(v.get('costCenter'),str) and v['costCenter'].strip():names.add(v['costCenter'].strip())
    for r in v.get('costCenters',[]):
     if isinstance(r,dict) and r.get('name'):names.add(r['name'])
    for x in v.values():walk(x)
   elif isinstance(v,list):
    for x in v:walk(x)
  walk(value)
 data['costCenters']=[{'id':str(uuid.uuid4()),'name':n,'active':True} for n in sorted(names)]
 c.execute('insert into financial_references values(1,?,1)',(json.dumps(data),));return data,1
def handle(h,method,connect,session,permissions,origin):
 actor=session(h)
 if not actor:return h.reply(401,{'error':'Sign in required'})
 try:
  perms=permissions(actor)
  if not any(p in perms for p in ['budget_view','is_view','dashboard']):raise policy.PermissionDenied('Application access required')
  with connect() as c:
   c.execute('BEGIN IMMEDIATE');data,v=load(c)
   if method=='POST':
    if not origin(h):return h.reply(403,{'error':'Invalid origin'})
    size=int(h.headers.get('Content-Length',0))
    if not 0<size<100000:raise ValueError('Invalid request size')
    b=json.loads(h.rfile.read(size));collection=b.get('collection')
    if collection not in ['costCenters','sources']:raise ValueError('Invalid reference list')
    policy.need(perms,'budget.masters.edit' if collection=='costCenters' else 'budget.manage_items.edit')
    if b.get('version')!=v:return h.reply(409,{'error':'References changed. Refresh before saving.'})
    name=str(b.get('name','')).strip();group=b.get('group')
    if not name or len(name)>200:raise ValueError('Enter a name within 200 characters')
    if collection=='sources' and group not in GROUPS:raise ValueError('Choose a budget category')
    record=next((x for x in data[collection] if x['id']==b.get('id')),None)
    if any(x['name'].casefold()==name.casefold() and x is not record for x in data[collection]):raise ValueError('Reference name already exists')
    # Name is the legacy linkage key: do not rename linked entries silently.
    if record and record['name']!=name:
     if any(record['name'] in raw for raw, in c.execute('select value from workspace')):raise ValueError('This reference is in use. Deactivate it and create a replacement to preserve history.')
     if c.execute("select 1 from sqlite_master where name='budget_governance'").fetchone() and any(record['name'] in raw for raw, in c.execute('select payload from budget_governance')):raise ValueError('Reference is linked to budget history. Deactivate instead of renaming.')
    if not record:record={'id':str(uuid.uuid4())};data[collection].append(record)
    record.update(name=name,active=b.get('active') is not False)
    if collection=='sources':record['group']=group
    c.execute('update financial_references set payload=?,version=? where id=1',(json.dumps(data,ensure_ascii=False),v+1));v+=1
   return h.reply(200,{'references':data,'version':v,'groups':GROUPS,'canCenters':'budget.masters.edit' in perms,'canSources':'budget.manage_items.edit' in perms})
 except policy.PermissionDenied as ex:return h.reply(403,{'error':str(ex)})
 except (ValueError,TypeError,KeyError) as ex:return h.reply(400,{'error':str(ex)})
