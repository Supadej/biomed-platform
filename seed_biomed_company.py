"""Additive company-relevant TEST fixtures. Never a production stock import."""
import json,sqlite3,datetime,hashlib,secrets
from pathlib import Path
ROOT=Path(__file__).resolve().parent
P='BMD-TEST-'
def add(c):
 def load(k):return json.loads(c.execute('select value from workspace where key=?',(k,)).fetchone()[0])
 def put(k,v):c.execute('update workspace set value=?,revision=revision+1 where key=?',(json.dumps(v,ensure_ascii=False),k))
 def push(d,k,v):
  if not any(x.get('id')==v['id'] for x in d.setdefault(k,[]) if isinstance(x,dict)):d[k].append(v)
 portal=load('biomed_portal_v33_clean');db=load('biomed_is_v50_transactions');now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)));day=now.date().isoformat();credentials=[]
 positions=[]
 def pos(title,department,role='Employee',manager='Managing Director'):
  positions.append((title,department,role,manager))
 pos('Managing Director','Management','Managing Director','')
 for title in ['Operations Director','Life Science Research Business Director','Diagnostics Business Director']:pos(title,'Operations' if title=='Operations Director' else 'Life Science Research' if title.startswith('Life') else 'Diagnostics','Operations Director' if title=='Operations Director' else 'Business Director')
 for title,dept in [('Accounting Manager','Accounting & Finance'),('Finance Manager','Accounting & Finance'),('Human Resource Manager','Human Resources'),('Operation Manager','Operations'),('Procurement & Regulatory Manager','Procurement & Regulatory'),('IT & Infrastructure Manager','IT')]:pos(title,dept,'Department Manager','Operations Director')
 for title in ['QMR','Document Control','Internal Control 1','Internal Control 2']:pos(title,'Quality Assurance','Employee','Managing Director' if title=='QMR' else 'QMR')
 for title,dept,manager,role in [('Accountant','Accounting & Finance','Accounting Manager','Accounting'),('Bill Collector','Accounting & Finance','Finance Manager','Accounting'),('Administration Officer','Administration','Operation Manager','Employee'),('Inventory Officer','Warehouse & Logistics','Operation Manager','Employee'),('Customer Service (Documentation)','Operations','Operation Manager','Employee'),('General Support Officer','Administration','Operation Manager','Employee'),('Housekeeping 1','Administration','Operation Manager','Employee'),('Housekeeping 2','Administration','Operation Manager','Employee'),('Messenger & Delivery Supervisor','Warehouse & Logistics','Operation Manager','Employee'),('Procurement & Regulatory Supervisor','Procurement & Regulatory','Procurement & Regulatory Manager','Employee'),('IT & Infrastructure Officer','IT','IT & Infrastructure Manager','Employee')]:pos(title,dept,role,manager)
 for i in range(1,3):pos('Messenger & Delivery '+str(i),'Warehouse & Logistics','Employee','Messenger & Delivery Supervisor')
 for i in range(1,4):pos('Purchasing Officer '+str(i),'Procurement & Regulatory','Employee','Procurement & Regulatory Supervisor')
 pos('Director Secretary','Management')
 for title in ['LSR Sales Manager','LSR Product Manager']:pos(title,'Life Science Research','Department Manager','Life Science Research Business Director')
 pos('LSR Sales Supervisor','Life Science Research','Employee','LSR Sales Manager')
 for i in range(1,4):pos('LSR Sales Rep. '+str(i),'Life Science Research','Employee','LSR Sales Supervisor')
 for i in range(1,3):pos('LSR Product Specialist '+str(i),'Life Science Research','Employee','LSR Product Manager')
 for team in (1,2):
  mgr=f'DIAG Team {team} Sales Manager';sup=f'DIAG Team {team} Sales Supervisor';pos(mgr,'Diagnostics','Department Manager','Diagnostics Business Director');pos(sup,'Diagnostics','Employee',mgr)
  for i in range(1,2 if team==1 else 5):pos(f'DIAG Team {team} Sales Rep. {i}','Diagnostics','Employee',sup)
 pos('DIAG Senior Sales Rep. Team 2','Diagnostics','Employee','DIAG Team 2 Sales Supervisor')
 for i in range(1,4):pos('DIAG Product Manager '+str(i),'Diagnostics','Department Manager','Diagnostics Business Director');pos('DIAG Product Specialist '+str(i),'Diagnostics','Employee','DIAG Product Manager '+str(i))
 pos('Marketing Communication Specialist','Marketing','Employee','Diagnostics Business Director');pos('DIAG Application Specialist Manager','Diagnostics','Department Manager','Diagnostics Business Director')
 for i in range(1,4):pos('DIAG Application Specialist '+str(i),'Diagnostics','Employee','DIAG Application Specialist Manager')
 pos('Service Engineer Manager','Service','Service Manager','Diagnostics Business Director');pos('Service Engineer Supervisor','Service','Service Manager','Service Engineer Manager');pos('Senior Service Engineer','Service','Service Engineer','Service Engineer Supervisor')
 for i in range(1,4):pos('Service Engineer '+str(i),'Service','Service Engineer','Service Engineer Supervisor')
 ids={title:P+'USER-'+str(i+1) for i,(title,*_) in enumerate(positions)}
 # Tailored roles start with employee self-service, then only relevant functional grants.
 allperms=set(portal['roles']['System Admin']);base=set(portal['roles']['Employee'])
 for title,dept,role,manager in positions:
  if role=='Employee' and dept in ('Diagnostics','Life Science Research','Marketing','Warehouse & Logistics','Procurement & Regulatory','Quality Assurance'):
   custom='TEST '+dept+' Staff';grants=set(base)
   if dept in ('Diagnostics','Life Science Research','Marketing'):grants|={x for x in allperms if x.startswith(('crm.customers.','crm.events.','crm.activities.')) and x.endswith(('.view','.create','.edit'))};grants|={'crm_view','is_view'};grants|={x for x in allperms if x.startswith(('is.quotation.','is.customer-order.')) and x.endswith(('.view','.create','.edit'))}
   if dept=='Warehouse & Logistics':grants|={'is_view'};grants|={x for x in allperms if x.startswith(('is.inventory.','is.delivery-in.','is.delivery-out.','is.withdrawal.','is.return.')) and x.endswith(('.view','.create','.edit'))}
   if dept=='Procurement & Regulatory':grants|={'is_view'};grants|={x for x in allperms if x.startswith(('is.purchase-request.','is.purchase-order.')) and x.endswith(('.view','.create','.edit'))}
   if dept=='Quality Assurance':grants|={'sops','minutes.view','minutes.acknowledge'} & allperms
   portal['roles'].setdefault(custom,sorted(grants & allperms));role=custom
  uid=ids[title];email=uid.lower()+'@example.invalid';push(portal,'users',{'id':uid,'name':'TEST · '+title,'email':email,'role':role,'department':dept,'position':title,'managerId':ids.get(manager,''),'active':True,'testData':True})
  push(portal,'hrprofiles',{'id':uid+'-HR','owner':uid,'employee':uid,'position':title,'employment':'Active','start':day,'email':email,'notes':'Position placeholder from supplied chart; not a verified employee identity.'})
  if not c.execute('select 1 from accounts where user_id=?',(uid,)).fetchone():
   password=secrets.token_urlsafe(15);salt=secrets.token_bytes(16);iterations=310000;digest=hashlib.pbkdf2_hmac('sha256',password.encode(),salt,iterations,dklen=32)
   c.execute('insert into accounts(id,email,name,role,user_id,password_hash,salt,iterations,created_at) values(?,?,?,?,?,?,?,?,?)',(uid,email,'TEST · '+title,role,uid,digest,salt,iterations,now.isoformat()));credentials.append({'position':title,'email':email,'password':password,'role':role})
 source='https://www.biomedthai.com/products/research.html'
 catalogue=[('Abcam','Antibody research pack'),('Abcam','ELISA research kit'),('Standard BioTools','CyTOF XT'),('Standard BioTools','Hyperion XTi'),('Standard BioTools','Maxpar panel kit'),('STEMCELL Technologies','Cell isolation research pack'),('STEMCELL Technologies','Cell culture research pack'),('JPT Peptide Technologies','Peptide pool research pack'),('System Biosciences','Exosome research pack'),('System Biosciences','CRISPR research pack'),('C.T.L.','ImmunoSpot analyzer'),('C.T.L.','ELISpot research kit'),('Mabtech','FluoroSpot research kit'),('Mabtech','ELISA research kit'),('PromoCell','Primary cell research pack'),('PromoCell','Cell culture medium'),('Minerva Biolabs','Mycoplasma detection kit'),('Minerva Biolabs','DNA decontamination reagent'),('Minerva Biolabs','PCR reagent pack')]
 for brand in sorted({x[0] for x in catalogue}):
  push(portal,'brands',{'id':P+'BRAND-'+brand.replace(' ','-'),'name':brand,'category':'Research','field':'Life Science Research','description':'Published research portfolio · test catalogue','url':source,'active':True,'sourceUrl':source,'testData':True})
  if brand not in portal.setdefault('productLines',[]):portal['productLines'].append(brand)
 push(db,'warehouses',{'id':P+'WH','name':'TEST Biomed Training Warehouse','active':True,'testData':True})
 for i,(brand,name) in enumerate(catalogue):
  pid=P+'PRODUCT-'+str(i+1);push(db,'products',{'id':pid,'name':'TEST · '+name,'brand':brand,'sku':P+'SKU-'+str(i+1),'category':'Testing only','line':'Life Science Research','unit':'unit' if 'analyzer' in name or name in ('CyTOF XT','Hyperion XTi') else 'pack','price':5000+i*500,'cost':2500+i*200,'vat':7,'active':True,'sourceUrl':source,'notes':'Published brand/product family; fictional SKU, price and quantity. Not a saleable catalogue item.','testData':True})
  for j in range(3):push(db,'lots',{'id':pid+'-LOT-'+str(j),'productId':pid,'warehouse':'TEST Biomed Training Warehouse','lot':P+'LOT-'+str(i+1)+'-'+str(j),'expiry':(now.date()+datetime.timedelta(days=365+j*180)).isoformat(),'qty':1000,'held':False,'testData':True})
 put('biomed_portal_v33_clean',portal);put('biomed_is_v50_transactions',db)
 import seed_testing_data,serve
 seed_testing_data.add(c,ids['Managing Director'])
 # Link new company test documents to the company-specific masters and users.
 db=load('biomed_is_v50_transactions')
 import permissions_policy
 for i,kind in enumerate(permissions_policy.CATALOG['transactions']):
  for j in range(3):
   push(db,'documents',{'id':P+kind+'-'+str(j),'kind':kind,'ref':P+kind.upper()+'-'+str(j),'date':day,'party':'TEST-DEMO-V2-'+('SUP-' if kind in ('purchase-request','purchase-order','delivery-in') else 'CUST-')+str(j),'status':'Draft','owner':ids['Managing Director'],'created':now.isoformat(),'history':[],'lines':[{'productId':P+'PRODUCT-'+str((i+j)%len(catalogue)+1),'qty':5+j,'price':5000}],'warehouse':'TEST Biomed Training Warehouse','currency':'THB','notes':'TEST ONLY · fictional unposted workflow document','testData':True})
 put('biomed_is_v50_transactions',db);serve.project(c,json.dumps(db))
 return {'positions':len(positions),'products':len(catalogue),'openingQty':len(catalogue)*3000,'credentials':credentials}
if __name__=='__main__':
 path=ROOT/'data/biomed.sqlite3'
 with sqlite3.connect(path) as c:
  with sqlite3.connect(path.with_suffix('.before-company-test.bak')) as backup:c.backup(backup)
  c.execute('begin immediate');result=add(c)
  if result['credentials']:(ROOT/'TEST_ACCOUNT_ACCESS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
 print({k:v for k,v in result.items() if k!='credentials'})
