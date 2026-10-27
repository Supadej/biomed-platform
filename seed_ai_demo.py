"""Add fictional demo records without replacing existing records or permissions."""
import argparse,json,sqlite3,os,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PREFIX='AI-DEMO-'
def add(c,email):
 actor=c.execute('SELECT user_id FROM accounts WHERE lower(email)=lower(?) AND disabled=0',(email,)).fetchone()
 if not actor:raise ValueError('Select an existing active account with --email')
 owner=actor[0];today=datetime.date.today();day=today.isoformat();future=(today+datetime.timedelta(days=7)).isoformat()
 def load(key,default):
  row=c.execute('SELECT value FROM workspace WHERE key=?',(key,)).fetchone();return json.loads(row[0]) if row else default
 def put(key,data):c.execute('INSERT INTO workspace(key,value,revision) VALUES(?,?,1) ON CONFLICT(key) DO UPDATE SET value=excluded.value,revision=workspace.revision+1',(key,json.dumps(data,ensure_ascii=False)))
 def append(data,field,record):
  existing=data.setdefault(field,[])
  if not any(isinstance(r,dict) and r.get('id')==record['id'] for r in existing):existing.append(record)
 portal=load('biomed_portal_v33_clean',json.loads((ROOT/'portal-seed-base.json').read_text()))
 for field,title,extra in [('announcements','DEMO: AI testing week',{'body':'Fictional content for testing Copilot. Demo stock and amounts are not real company records.','date':day,'by':'Demo administrator'}),('forms','DEMO: Travel checklist',{'description':'Fictional travel preparation checklist','category':'Travel','url':''}),('resources','DEMO: Product training guide',{'description':'Fictional training reference','category':'Training','url':''}),('tasks','DEMO: Prepare customer product demonstration',{'due':future,'priority':'High','status':'Not started','history':[]}),('objectives','DEMO: Complete three training sessions',{'period':'Monthly','start':day,'end':future,'measure':'3 training sessions','progress':33,'status':'Pending'}),('requests','DEMO: Training visit travel request',{'type':'travel','start':day,'end':future,'department':'Diagnostics','details':'Fictional training trip','amount':4800,'asset':'','status':'Pending','stage':0,'history':[],'date':day}),('tickets','DEMO: Product setup support',{'created':day,'description':'Fictional support case','status':'Open','history':[]}),('expenses','DEMO: Local training travel claim',{'category':'Local','created':day,'amount':1200,'advance':0,'status':'Pending','items':[{'date':day,'type':'Travel','amount':1200,'rate':1,'vat':0,'currency':'THB','detail':'Fictional taxi expense','receipt':None}]}),('sops','DEMO: Equipment demonstration SOP',{'description':'Fictional training document. No attachment.','category':'Training','url':''})]:
  append(portal,field,dict(id=PREFIX+field+'-'+owner,owner=owner,title=title,**extra))
 put('biomed_portal_v33_clean',portal)
 db=load('biomed_is_v50_transactions',{'users':[],'customers':[],'suppliers':[],'products':[],'warehouses':[],'lots':[],'documents':[],'movements':[],'audit':[],'settings':{'defaultVat':7,'allowSelfApproval':True}})
 for field,record in [('customers',{'id':PREFIX+'CUSTOMER','name':'DEMO Research Centre','category':'Demo customer','creditDays':30}),('suppliers',{'id':PREFIX+'SUPPLIER','name':'DEMO Diagnostic Supplier','country':'Thailand','currency':'THB'}),('products',{'id':PREFIX+'PRODUCT','name':'DEMO Training Reagent Kit','sku':'DEMO-KIT-001','brand':'DEMO','supplierId':PREFIX+'SUPPLIER','category':'Training','line':'Diagnostics','unit':'kit','vat':7,'cost':2000,'price':3500,'storage':'2–8°C'}),('warehouses',{'id':PREFIX+'WAREHOUSE','name':'DEMO Warehouse','active':True}),('lots',{'id':PREFIX+'LOT','productId':PREFIX+'PRODUCT','warehouse':'DEMO Warehouse','lot':'DEMO-LOT-001','expiry':(today+datetime.timedelta(days=365)).isoformat(),'qty':50,'held':False})]:append(db,field,record)
 previous=None
 for i,kind in enumerate(['quotation','customer-order','invoice']):
  ident=PREFIX+kind;record={'id':ident,'kind':kind,'ref':PREFIX+kind.upper(),'date':day,'party':'DEMO Research Centre','status':'Draft','owner':owner,'created':day+'T09:00:00','history':[],'lines':[{'productId':PREFIX+'PRODUCT','qty':5,'price':3500}],'warehouse':'DEMO Warehouse','currency':'THB','notes':'Fictional AI test record; unposted. No real stock movement or financial posting.'}
  if previous:record['sourceId']=previous
  append(db,'documents',record);previous=ident
 put('biomed_is_v50_transactions',db)
 # Keep normalized IS tables in sync with the workspace projection.
 import serve
 serve.project(c,json.dumps(db))
 budget=load('biomed_budget_v60_years',{'active':2027,'years':{}})
 fy=int(budget.get('active',2027));year=budget.setdefault('years',{}).setdefault(str(fy),{'fy':fy,'products':[],'expenses':[],'workforce':[],'ledger':[],'approvals':[],'versions':[],'settings':{'divisionSplit':False}})
 m=(today.month-5)%12;actual=[0]*12;actual[m]=17500;cogs=[0]*12;cogs[m]=10000;expense=[0]*12;expense[m]=1200;commit=[0]*12;commit[m]=4800
 append(year,'products',{'id':PREFIX+'BUDGET-PRODUCT','name':'DEMO Training Reagent Kit','division':'Diagnostics','costCenter':'DEMO Diagnostics','active':True,'source':'Fictional AI test','budget':[25000]*12,'cogsBudget':[14000]*12,'revenueActual':actual,'cogsActual':cogs})
 append(year,'expenses',{'id':PREFIX+'BUDGET-EXPENSE','name':'DEMO Training travel','category':'Promotional Expenses','division':'Diagnostics','costCenter':'DEMO Diagnostics','active':True,'source':'Fictional AI test','budget':[5000]*12,'actual':expense,'commitment':commit})
 append(year,'costCenters',{'id':PREFIX+'CC','name':'DEMO Diagnostics','active':True})
 for suffix,line,amount,typ in [('REVENUE',PREFIX+'BUDGET-PRODUCT',17500,'Actual'),('TRAVEL',PREFIX+'BUDGET-EXPENSE',1200,'Actual'),('COMMIT',PREFIX+'BUDGET-EXPENSE',4800,'Commitment')]:
  append(year,'ledger',{'id':PREFIX+suffix,'date':day,'line':line,'label':'DEMO AI testing','type':typ,'month':m,'amount':amount,'reference':PREFIX+suffix,'note':'Fictional AI test','division':'Diagnostics','costCenter':'DEMO Diagnostics'})
 put('biomed_budget_v60_years',budget)
 return owner
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--database',default=os.environ.get('BIOMED_DATABASE_PATH',str(ROOT/'data/biomed.sqlite3')));p.add_argument('--email',default='testadmin@example.invalid');args=p.parse_args();path=Path(args.database).resolve()
 if not path.is_file():p.error('Database does not exist; refusing to create a new installation')
 backup=path.with_name(path.name+'.before-ai-demo-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.bak')
 with sqlite3.connect(path) as c:
  with sqlite3.connect(backup) as target:c.backup(target)
  os.chmod(backup,0o600)
  c.execute('BEGIN IMMEDIATE')
  owner=add(c,args.email)
 print('Fictional demo data ready for '+args.email+'. Existing records and role permissions retained. Backup: '+str(backup))
