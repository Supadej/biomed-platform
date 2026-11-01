"""Managed Application Service customer references and eligible specialists."""
import json,uuid,unicodedata
import permissions_policy as policy
PORTAL='biomed_portal_v33_clean'
def portal(c):
 row=c.execute('SELECT value FROM workspace WHERE key=?',(PORTAL,)).fetchone();return json.loads(row[0]) if row else {}
def specialists(c):
 p=portal(c);roles=p.get('roles',{});profiles={str(u['id']):u for u in p.get('users',[]) if u.get('id')}
 result=[]
 for ident,name,role,disabled in c.execute('SELECT user_id,name,role,disabled FROM accounts'):
  u=profiles.get(str(ident),{});grants=roles.get(role,[])
  if disabled or u.get('active') is False:continue
  if policy.is_system_admin(('','','',role,str(ident))) or 'application_service.perform' in grants:result.append({'id':str(ident),'name':name,'role':role})
 return sorted(result,key=lambda r:r['name'].casefold())
def products(c):
 p=portal(c);names={str(x).strip() for x in p.get('productLines',[]) if isinstance(x,str) and x.strip()}
 if c.execute("SELECT 1 FROM sqlite_master WHERE name='operational_brands'").fetchone():names.update(n for n, in c.execute('SELECT name FROM operational_brands WHERE active=1'))
 return sorted(names,key=str.casefold)
def initialize(c):
 c.execute('CREATE TABLE IF NOT EXISTS application_customers(id TEXT PRIMARY KEY,name TEXT NOT NULL,active INTEGER NOT NULL DEFAULT 1,source_id TEXT)');c.execute('CREATE TABLE IF NOT EXISTS application_reference_migrations(name TEXT PRIMARY KEY)')
def customers(c):
 initialize(c)
 if not c.execute("SELECT 1 FROM application_reference_migrations WHERE name='customer-seed-v1'").fetchone():
  names={}
  for ident,payload in c.execute("SELECT id,payload FROM masters WHERE category='customers'"):
   name=str(json.loads(payload).get('name') or '').strip()
   if name:names.setdefault(name.casefold(),(name,ident))
  for payload, in c.execute('SELECT payload FROM application_service_records'):
   name=str(json.loads(payload).get('customer') or '').strip()
   if name:names.setdefault(name.casefold(),(name,None))
  for name,source in names.values():c.execute('INSERT INTO application_customers VALUES(?,?,1,?)',(str(uuid.uuid4()),name,source))
  c.execute("INSERT INTO application_reference_migrations VALUES('customer-seed-v1')")
 return [dict(id=i,name=n,active=bool(a),sourceId=s) for i,n,a,s in c.execute('SELECT id,name,active,source_id FROM application_customers ORDER BY name COLLATE NOCASE')]
def change(c,actor,perms,values):
 policy.need(perms,'application_service.manage_references');customers(c)
 if values.get('operation')=='add':
  name=unicodedata.normalize('NFKC',str(values.get('name') or '')).strip()
  if not 1<=len(name)<=200:raise ValueError('Customer name must contain 1–200 characters')
  old=next((x for x in customers(c) if x['name'].casefold()==name.casefold()),None)
  if old:c.execute('UPDATE application_customers SET active=1 WHERE id=?',(old['id'],))
  else:c.execute('INSERT INTO application_customers VALUES(?,?,1,NULL)',(str(uuid.uuid4()),name))
 elif values.get('operation')=='remove':
  if not c.execute('SELECT 1 FROM application_customers WHERE id=?',(values.get('id'),)).fetchone():raise ValueError('Customer reference not found')
  c.execute('UPDATE application_customers SET active=0 WHERE id=?',(values['id'],))
 else:raise ValueError('Unknown customer reference action')
 import application_service
 application_service.audit(c,actor,'customer reference '+values['operation'],{'id':'customer-references','name':values.get('name'),'customerId':values.get('id')})
 return customers(c)
