"""Controlled service reference lists and Biomed IS-backed spare parts."""
import json
import permissions_policy as policy

def setup(c):
 c.execute('CREATE TABLE IF NOT EXISTS service_setup(id INTEGER PRIMARY KEY CHECK(id=1),payload TEXT NOT NULL,version INTEGER NOT NULL)')
 row=c.execute('SELECT payload,version FROM service_setup WHERE id=1').fetchone()
 if row:return dict(json.loads(row[0]),version=row[1])
 records=[json.loads(p) for p, in c.execute('SELECT payload FROM fse_records')]
 pairs=sorted({(r.get('brand','').strip(),r.get('model','').strip()) for r in records if r.get('brand') and r.get('model')})
 def unique(values):
  result={}
  for value in sorted(values):result.setdefault(value.casefold(),value)
  return list(result.values())
 brands=unique({r['brand'].strip() for r in records if r.get('brand')});brand_map={b.casefold():b for b in brands}
 models={}
 for b,m in pairs:
  canonical=brand_map[b.casefold()];models.setdefault((canonical.casefold(),m.casefold()),{'brand':canonical,'name':m})
 data={'brands':brands,'models':list(models.values()),'locations':unique({str(r.get(k)).strip() for r in records for k in ['location','fromLocation','toLocation'] if r.get(k)})}
 c.execute('INSERT INTO service_setup VALUES(1,?,1)',(json.dumps(data,ensure_ascii=False),));return dict(data,version=1)
def save_setup(c,perms,data):
 policy.need(perms,'service.manage');prior=setup(c)
 if data.get('version')!=prior['version']:raise ValueError('Reference lists changed; refresh first')
 clean={}
 for key in ['brands','locations']:
  values=data.get(key)
  if not isinstance(values,list) or len(values)>10000:raise ValueError('Invalid '+key)
  if any(not isinstance(x,str) or not x.strip() or len(x)>200 for x in values):raise ValueError('List values must contain 1–200 characters')
  if len({x.strip().casefold() for x in values})!=len(values):raise ValueError('Duplicate '+key)
  clean[key]=sorted(x.strip() for x in values)
 models=data.get('models')
 if not isinstance(models,list) or len(models)>10000:raise ValueError('Invalid models')
 clean['models']=[];seen=set()
 for r in models:
  if not isinstance(r,dict) or r.get('brand') not in clean['brands'] or not str(r.get('name','')).strip():raise ValueError('Each model needs an available brand and model name')
  name=str(r['name']).strip()
  if len(name)>200 or (r['brand'].casefold(),name.casefold()) in seen:raise ValueError('Invalid or duplicate model')
  seen.add((r['brand'].casefold(),name.casefold()));clean['models'].append({'brand':r['brand'],'name':name})
 c.execute('UPDATE service_setup SET payload=?,version=version+1 WHERE id=1',(json.dumps(clean,ensure_ascii=False),))
 return setup(c)
def engineers(c):
 try:
  row=c.execute("SELECT value FROM workspace WHERE key='biomed_portal_v33_clean'").fetchone();portal=json.loads(row[0]) if row else {};roles=portal.get('roles',{})
  out=[];accounts={str(pid):{'name':name,'role':role,'disabled':disabled} for pid,name,role,disabled in c.execute('SELECT user_id,name,role,disabled FROM accounts')}
  people={str(u['id']):u for u in portal.get('users',[]) if u.get('id') is not None}
  for pid,account in accounts.items():people.setdefault(pid,dict(account,id=pid))
  for pid,u in people.items():
   account=accounts.get(pid,{});role=u.get('role') or account.get('role','');name=u.get('name') or account.get('name','');grants=set(roles.get(role,[]))
   if account.get('disabled') or u.get('active') is False:continue
   if role=='System Admin' or 'service.jobs.edit' in grants or 'service.jobs.create' in grants:
    crm=c.execute('SELECT crm_user_id FROM crm_identity WHERE portal_user_id=?',(pid,)).fetchone()
    out.append({'id':pid,'name':name,'role':role,'crmId':crm[0] if crm else None})
  return out
 except Exception as exc:
  # Some isolated import/test databases do not contain sign-in tables.
  import sqlite3
  if isinstance(exc,sqlite3.OperationalError):return []
  raise

def validate(c,r,old=None):
 config=setup(c);prior=old or {};kind=r['kind']
 for field,choices in [('brand',config['brands']),('location',config['locations']),('fromLocation',config['locations']),('toLocation',config['locations'])]:
  val=r.get(field,'')
  if val and val!=prior.get(field) and val not in choices:raise ValueError('Select '+field+' from service reference lists')
 if r.get('model') and (r.get('model'),r.get('brand'))!=(prior.get('model'),prior.get('brand')):
  if not any(x['name']==r['model'] and x['brand']==r.get('brand') for x in config['models']):raise ValueError('Select a model belonging to the selected brand')
 if kind in ('jobs','movements'):
  if r.get('engineer') and r.get('engineer')!=prior.get('engineer'):
   selected=next((x for x in engineers(c) if x['id']==r.get('engineer')),None)
   if not selected:raise ValueError('Select an active employee with service job responsibilities')
   r['engineerName']=selected['name']
 if kind=='parts':
  if not r.get('productId'):raise ValueError('Select a Biomed IS product to declare as a spare part')
  row=c.execute("SELECT payload FROM masters WHERE category='products' AND id=?",(r['productId'],)).fetchone()
  if not row:raise ValueError('Spare parts must be Biomed IS products')
  product=json.loads(row[0]);
  if prior.get('catalogueNo') and prior.get('catalogueNo')!=(product.get('catalogueNo') or product.get('sku') or r['productId']):r.setdefault('legacyCatalogueNo',prior['catalogueNo'])
  for ident,payload in c.execute("SELECT id,payload FROM fse_records WHERE kind='parts'"):
   other=json.loads(payload)
   if ident!=r.get('id') and (other.get('productId'),other.get('brand',''),other.get('model',''))==(r['productId'],r.get('brand',''),r.get('model','')):raise ValueError('This product is already declared for the selected brand / model')
  r['name']=product.get('name','');r['catalogueNo']=product.get('catalogueNo') or product.get('sku') or r['productId']
 if kind=='jobs':
  if 'partsUsed' not in r:return
  if not isinstance(r['partsUsed'],list) or len(r['partsUsed'])>200:raise ValueError('Invalid service parts')
  instrument=c.execute("SELECT payload FROM fse_records WHERE id=? AND kind='instruments'",(r.get('instrumentId'),)).fetchone();instrument=json.loads(instrument[0]) if instrument else {}
  parts={i:json.loads(p) for i,p in c.execute("SELECT id,payload FROM fse_records WHERE kind='parts'")}
  import math
  for line in r['partsUsed']:
   part=parts.get(line.get('partId'))
   if not part or not part.get('productId'):raise ValueError('Choose an IS-backed spare part from the catalogue')
   if any(part.get(k) and instrument.get(k) and part[k]!=instrument[k] for k in ['brand','model']):raise ValueError('Spare part is not declared for this instrument brand / model')
   try:qty=float(line.get('qty',0));cost=float(line.get('unitCost',0))
   except (ValueError,TypeError):raise ValueError('Invalid part quantity or cost')
   if not math.isfinite(qty) or qty<=0 or not math.isfinite(cost) or cost<0:raise ValueError('Parts need a positive quantity and nonnegative unit cost')
   line.update(productId=part['productId'],catalogueNo=part.get('catalogueNo'),name=part.get('name'),qty=qty,unitCost=cost)
