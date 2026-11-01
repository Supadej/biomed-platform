"""Repair additive TEST opening balances and seed approved test engineer custody."""
import sqlite3,json,datetime
from pathlib import Path
ROOT=Path(__file__).parent
P='BMD-TEST-'
def add(c):
 import serve,service_inventory,service_catalog,operational_brands
 service_inventory.initialize(c)
 d=json.loads(c.execute("select value from workspace where key='biomed_is_v50_transactions'").fetchone()[0]);today=datetime.date.today();at=datetime.datetime.now(datetime.timezone.utc).isoformat()
 def push(field,row):
  if not any(x.get('id')==row['id'] for x in d.setdefault(field,[])):d[field].append(row)
 # Every seeded lot becomes an explicit test opening movement, as used by Stock Inventory.
 for lot in d.get('lots',[]):
  if not (str(lot.get('id','')).startswith(('BMD-TEST-','TEST-DEMO-','AI-DEMO-'))):continue
  push('movements',{'id':'TEST-OPEN-'+lot['id'],'at':at,'productId':lot['productId'],'warehouse':lot['warehouse'],'lot':lot['lot'],'expiry':lot.get('expiry',''),'change':float(lot.get('qty') or 0),'sourceId':'TEST-OPENING','testData':True})
 for p in d['products']:
  qty=sum(float(m.get('change') or 0) for m in d['movements'] if m.get('productId')==p['id'] and (not m.get('expiry') or m['expiry']>=today.isoformat()))
  if qty<=0:push('movements',{'id':'TEST-USABLE-'+p['id'],'at':at,'productId':p['id'],'warehouse':'TEST Biomed Training Warehouse','lot':'TEST-USABLE-'+p['id'],'expiry':(today+datetime.timedelta(days=730)).isoformat(),'change':1000,'sourceId':'TEST-OPENING','testData':True})
 instruments=[json.loads(p) for p, in c.execute("select payload from fse_records where kind='instruments'")];selected=[];pairs=set()
 for ins in instruments:
  pair=(ins.get('brand'),ins.get('model'))
  if pair not in pairs and pair[0]:selected.append(ins);pairs.add(pair)
  if len(selected)==8:break
 for i,ins in enumerate(selected):
  pid=P+'SPARE-'+str(i+1);partid=P+'CAT-'+str(i+1);lot=P+'SPARE-LOT-'+str(i+1)
  push('products',{'id':pid,'name':'TEST · Service consumable '+str(i+1)+' · '+ins.get('model',''),'sku':pid,'brand':ins['brand'],'category':'TEST spare part','line':'Diagnostics','unit':'piece','price':500,'cost':250,'vat':7,'active':True,'testData':True,'notes':'Fictional service inventory test item; not an actual manufacturer catalogue code'})
  part={'id':partid,'kind':'parts','productId':pid,'catalogueNo':pid,'name':'TEST service consumable '+str(i+1),'brand':ins['brand'],'model':ins.get('model',''),'testData':True}
  c.execute('insert or ignore into fse_records(id,kind,payload,version) values(?,?,?,1)',(partid,'parts',json.dumps(part)))
  push('movements',{'id':'TEST-OPEN-'+pid,'at':at,'productId':pid,'warehouse':'TEST Biomed Training Warehouse','lot':lot,'expiry':'2030-12-31','change':2000,'sourceId':'TEST-OPENING','testData':True})
 for i in range(3):push('kits',{'id':P+'KIT-'+str(i+1),'name':'TEST · Research workflow kit '+str(i+1),'parent':'','components':[{'id':P+'PRODUCT-'+str(i*2+1),'qty':2},{'id':P+'PRODUCT-'+str(i*2+2),'qty':1}],'testData':True})
 c.execute("update workspace set value=?,revision=revision+1 where key='biomed_is_v50_transactions'",(json.dumps(d,ensure_ascii=False),));serve.project(c,json.dumps(d))
 portal=json.loads(c.execute("select value from workspace where key='biomed_portal_v33_clean'").fetchone()[0]);perms=set(portal['roles']['System Admin']);approver=(None,None,None,None,'u1')
 engineers=[e for e in service_catalog.engineers(c) if str(e['id']).startswith('BMD-TEST-')]
 for e in engineers:
  ref='TEST initial custody '+str(e['id'])
  if c.execute("select 1 from service_inventory_requests where json_extract(payload,'$.note')=?",(ref,)).fetchone():continue
  lines=[{'productId':P+'SPARE-'+str(i+1),'warehouse':'TEST Biomed Training Warehouse','lot':P+'SPARE-LOT-'+str(i+1),'expiry':'2030-12-31','qty':25} for i in range(len(selected))]
  result=service_inventory.dispatch(c,(None,None,None,None,e['id']),perms,{'action':'request','kind':'Request','engineer':e['id'],'lines':lines,'note':ref})
  service_inventory.dispatch(c,approver,perms,{'action':'approve','id':result['id'],'version':1})
 import instrument_service
 for index,e in enumerate(engineers):
  ident=P+'SERVICE-JOB-'+str(index+1)
  if c.execute('select 1 from fse_records where id=?',(ident,)).fetchone():continue
  ins=selected[index%len(selected)];partid=P+'CAT-'+str(index%len(selected)+1)
  instrument_service.save(c,(None,None,None,None,e['id']),perms,{'id':ident,'kind':'jobs','instrumentId':ins['id'],'engineer':e['id'],'date':today.isoformat(),'status':'Completed','jobType':'Repair','description':'TEST ONLY · repair workflow and inventory consumption demonstration','diagnosis':'TEST simulated component issue','actionTaken':'TEST consumable replacement and function check','result':'TEST check complete','partsUsed':[{'partId':partid,'qty':2,'unitCost':250}],'testData':True})
 budget=json.loads(c.execute("select value from workspace where key='biomed_budget_v60_years'").fetchone()[0])
 for fy,y in budget.get('years',{}).items():
  if not any(x.get('name')=='TEST Research' for x in y.setdefault('costCenters',[])):y['costCenters'].append({'id':P+'BUDGET-CC','name':'TEST Research','active':True})
  for product in d['products']:
   if not product['id'].startswith(P+'PRODUCT-'):continue
   ident=P+'BUDGET-'+product['id']
   if any(x.get('id')==ident for x in y.setdefault('products',[])):continue
   closed=12 if int(fy)<int(budget['active']) else 6 if int(fy)==int(budget['active']) else 0
   plan=[float(product['price'])*10]*12;cost=[float(product['cost'])*10]*12
   y['products'].append({'id':ident,'name':product['name'],'brand':product['brand'],'productId':product['id'],'division':'Life Science Research','costCenter':'TEST Research','source':'Fictional Biomed testing','active':True,'budget':plan,'cogsBudget':cost,'revenueActual':[v*.8 if i<closed else 0 for i,v in enumerate(plan)],'cogsActual':[v*.8 if i<closed else 0 for i,v in enumerate(cost)],'testData':True})
 c.execute("update workspace set value=?,revision=revision+1 where key='biomed_budget_v60_years'",(json.dumps(budget,ensure_ascii=False),))
 operational_brands.initialize(c);operational_brands.sync(c)
 return {'engineers':len(engineers),'spareProducts':len(selected),'balances':len(service_inventory.balances(c))}
if __name__=='__main__':
 with sqlite3.connect(ROOT/'data/biomed.sqlite3') as c:
  with sqlite3.connect(ROOT/'data/biomed.before-stock-v27.bak') as backup:c.backup(backup)
  c.execute('begin immediate');print(add(c))
