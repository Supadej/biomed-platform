"""Deterministic fictional test fixtures. Refuses to replace an existing database."""
from pathlib import Path
import json, copy, importlib.util, random
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('server',ROOT/'serve.py');server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
rng=random.Random(20261022)
def load(n):return json.loads((ROOT/n).read_text())
def months(base):return [round(base*(1+(i%4)*.07),2) for i in range(12)]
def make():
 if server.DB.exists():raise SystemExit('Existing database retained. Extract a fresh copy of the ZIP to start a new test workspace.')
 portal=load('portal-seed-base.json');schema=load('schema-seed-base.json')['documents'];budget=load('budget-seed-base.json')
 for u in portal['users']:
  u['name']='TEST '+u['name'];u['email']=u['id']+'@example.invalid';u['managerId']='' if u['id']=='u1' else 'u1' if u['id'] in ['u2','u-accounting'] else 'u2' if u['id'] in ['u3','u4'] else 'u4'
 portal['isPermissionsSeeded']=True;portal['budgetPermissionsSeeded']=True
 portal['productLines']=['Allergy & Immunology','Respiratory','Life Science Research','Microbiology','Infectious Disease']
 db=dict(users=[dict(id='admin',name='TEST System Administrator',role='admin'),dict(id='sales',name='TEST Sales Representative',role='sales'),dict(id='smgr',name='TEST Sales Manager',role='sales_manager'),dict(id='pmgr',name='TEST Purchasing Manager',role='purchasing'),dict(id='wh',name='TEST Warehouse Officer',role='warehouse'),dict(id='acct',name='TEST Accounting Officer',role='accounting'),dict(id='dir',name='TEST Director',role='director')],customers=[],suppliers=[],products=[],warehouses=['TEST Main Warehouse','TEST Cold Chain','TEST Demo Store'],documents=[],movements=[],lots=[],quarantines=[],stockChecks=[],warehouseMoves=[],kits=[],audit=[],settings=dict(defaultVat=7,allowSelfApproval=True))
 for category,count,prefix in [('customers',30,'C'),('suppliers',12,'S')]:
  for i in range(1,count+1):
   db[category].append(dict(id=f'TEST-{prefix}{i:03}',name=f'TEST {"Hospital" if prefix=="C" else "Supplier"} {i:02}',active=i!=count,address=f'{100+i} Sample Road, Bangkok 10800 — fictional',taxId=f'TEST-TAX-{i:03}',contact=f'TEST Contact {i:02}',email=f'{prefix.lower()}{i}@example.invalid',phone='000-000-0000',creditDays=30,creditLimit=250000,currency='THB',paymentTerm='30 days',department='Diagnostics'))
 for i in range(1,41):
  db['products'].append(dict(id=f'TEST-P{i:03}',sku=f'TEST-CAT-{i:03}',catalogueNo=f'TEST-CAT-{i:03}',name=f'TEST {portal["productLines"][(i-1)%5]} Product {i:02}',brand=f'TEST Brand {(i-1)%4+1}',barcode=f'TESTBAR{i:05}',unit='kit' if i%3 else 'unit',saleUnitEn='kit' if i%3 else 'unit',saleUnitTh='ชุด' if i%3 else 'เครื่อง',size='24 tests' if i%3 else '1 unit',storage='2–8°C' if i%2 else 'Room temperature',line=portal['productLines'][(i-1)%5],vat=7,price=500+i*125,cost=250+i*60,active=i!=40))
 def line(i,qty=2):
  p=db['products'][i-1];return dict(productId=p['id'],qty=qty,price=p['price'],unit=p['unit'],description=p['name'],catalogueNo=p['sku'],lot=f'TEST-LOT-{i:03}',expiry='2027-12-31',sourceFields={})
 counter=0
 def document(kind,status='Draft',source=None,idx=1,month=10,qty=2):
  nonlocal counter
  counter+=1;date=f'2026-{month:02}-15';ref=f'TEST-{kind.upper()}-{counter:04}';ls=[line(idx,qty),line(idx+1,qty)]
  supplier=kind in ['purchase-request','purchase-order','supplier-confirm','delivery-in','check-in'];party=db['suppliers' if supplier else 'customers'][(idx-1)%(12 if supplier else 30)]
  f={}
  for field in schema.get(kind,{}).get('header',[]):
   k=field['id'];label=field.get('label','').lower()
   if field.get('type') in ['checkbox','radiobutton']:v=False
   elif field.get('options'):v=field['options'][0]['value']
   elif 'date' in label or 'date' in k.lower():v=date
   elif 'currency' in label:v='THB'
   elif 'customer' in label or 'supplier' in label:v=party['name']
   elif 'address' in label:v=party['address']
   elif 'email' in label:v=party['email']
   elif 'tel' in label or 'phone' in label:v=party['phone']
   elif any(x in label for x in ['amount','vat','discount','total']):v='0'
   else:v='TEST sample' if field.get('required') else ''
   f[k]=v
  f.update(txtdiscountSP='0',txtdiscountC='0',txtvatC='7',RBvat=False,RBnotvat=True,txtcustomernamec=party['name'],txtAddressc=party['address'],txtaddressd=party['address'],txtattentionto='TEST Receiving Department',ddcustomerid=party['id'],ddlsale='u6',txtremarkC='FICTIONAL TEST DATA — not a real transaction.')
  gross=round(sum(l['qty']*l['price'] for l in ls),2);tax=round(gross*.07,2)
  fin=dict(gross=gross,amount=gross,sales=0,cash=0,net=gross,vat=7,tax=tax,grand=round(gross+tax,2),inclusive=False)
  f.update(txtamountC=str(gross),txttotalamountC=str(gross),txttotalvatC=str(tax),txtgrandtotalC=str(fin['grand']))
  d=dict(id=f'TEST-D{counter:04}',ref=ref,kind=kind,status=status,date=date,due='2026-11-15',party=party['id'],warehouse=db['warehouses'][0],toWarehouse=db['warehouses'][2],currency='THB',externalRef=f'TEST-EXT-{counter:04}',portalRep='u6',portalLine=db['products'][idx-1]['line'],owner='sales' if not supplier else 'pmgr',created=date+'T09:00:00Z',sourceId=source['id'] if source else '',lines=ls,sourceFields=f,financials=fin,sourceVersion=1,sourcePage=schema.get(kind,{}).get('source',''),history=[dict(action='Seeded fictional test record',by='admin',at=date+'T09:00:00Z')])
  db['documents'].append(d);return d
 kinds=['quotation','customer-order','sales-order','purchase-request','purchase-order','supplier-confirm','delivery-in','check-in','withdrawal','borrowing','return-product','delivery-out','check-out','invoice','credit-note','debit-note','payment-receipt','stock-adjust','stock-transfer','stock-count']
 for kind in kinds:
  for status in ['Draft','Pending','Rejected']:document(kind,status,idx=1+(counter%15))
 # Approved purchasing and sales chains; shipment is only a child of check-out.
 for n,month in enumerate([8,9,10]):
  idx=1+n*5;prev=None
  for kind in ['purchase-request','purchase-order','supplier-confirm','delivery-in','check-in']:prev=document(kind,'Approved',prev,idx,month,50)
  q=document('quotation','Approved',idx=idx,month=month);o=document('sales-order','Approved',q,idx,month);inv=document('invoice','Approved',o,idx,month)
  do=document('delivery-out','Approved',inv,idx,month);co=document('check-out','Approved',do,idx,month)
  sh=document('shipment','Generated',co,idx,month);sh['autoGenerated']=True
  document('payment-receipt','Approved',inv,idx,month)
  if n==2:document('credit-note','Approved',inv,idx,month,1);document('debit-note','Approved',inv,idx,month,1)
 borrow=None
 for kind in ['withdrawal','borrowing','return-product','stock-adjust','stock-transfer','stock-count']:
  d=document(kind,'Approved',borrow if kind=='return-product' else None,idx=21)
  if kind=='borrowing':borrow=d
 # Ledger is the source of inventory. Each opening movement is linked to an explicit approved opening adjustment.
 opening=document('stock-adjust','Approved',idx=1,month=7);opening['ref']='TEST-OPENING-BALANCES';opening['lines']=[line(i,100) for i in range(1,40)]
 for i in range(1,40):
  for w in db['warehouses'][:2]:
   for lot,qty,expiry in [(f'TEST-LOT-{i:03}',100,'2027-12-31'),(f'TEST-OLD-{i:03}',5,'2026-09-01')]:
    db['movements'].append(dict(id=f'TEST-M{len(db["movements"])+1:04}',sourceId=opening['id'],at='2026-07-01T09:00:00Z',productId=f'TEST-P{i:03}',warehouse=w,lot=lot,expiry=expiry,change=qty))
 # Add postings for approved receiving / issuing / returns / transfers, leaving Draft/Pending unposted.
 for d in db['documents']:
  if d['status']!='Approved' or d is opening:continue
  if d['kind'] not in ['check-in','check-out','return-product','stock-adjust','stock-transfer']:continue
  for l in d['lines']:
   sign=1 if d['kind'] in ['check-in','return-product'] else -1
   pairs=[(d['warehouse'],sign*l['qty'])]
   if d['kind']=='stock-transfer':pairs.append((d['toWarehouse'],l['qty']))
   for w,change in pairs:db['movements'].append(dict(id=f'TEST-M{len(db["movements"])+1:04}',sourceId=d['id'],at=d['date']+'T10:00:00Z',productId=l['productId'],warehouse=w,lot=l['lot'],expiry=l['expiry'],change=change))
 db['quarantines']=[dict(id='TEST-QC1',productId='TEST-P003',warehouse=db['warehouses'][0],lot='TEST-LOT-003',status='Held',at='2026-10-20T09:00:00Z',by='wh',reason='TEST packaging review — held lot scenario')]
 db['stockChecks']=[dict(id='TEST-COUNT1',ref='TEST-COUNT-001',at='2026-10-22T09:00:00Z',productId='TEST-P030',warehouse=db['warehouses'][0],lot='TEST-LOT-030',system=100,count=98,status='Pending',comment='TEST two units missing')]
 db['warehouseMoves']=[dict(id='TEST-MOVE1',at='2026-10-22T09:00:00Z',productId='TEST-P030',lot='TEST-LOT-030',**{'from':db['warehouses'][0],'to':db['warehouses'][2]},qty=5,status='Pending',reason='TEST demo stock replenishment')]
 db['kits']=[dict(id='TEST-KIT1',name='TEST Diagnostic Starter Panel',parent='TEST-P039',components=[dict(id='TEST-P001',qty=2),dict(id='TEST-P002',qty=1)])]
 db['audit']=[dict(id='TEST-AUDIT1',at='2026-10-22T09:00:00Z',by='admin',action='Test dataset generated',reference='TEST-DATA',detail='All records fictional. Imported fixtures do not certify workflow behavior.')]
 document('quotation','Approved',idx=26,month=10)
 document('quotation','Approved',idx=31,month=10)
 opening['lines']=[dict(productId=m['productId'],qty=m['change'],price=0,lot=m['lot'],expiry=m['expiry'],warehouse=m['warehouse'],sourceFields={}) for m in db['movements'] if m['sourceId']==opening['id']]
 portal['isCRM']={}
 for i,q in enumerate(d for d in db['documents'] if d['kind']=='quotation'):
  outcome=['Monitoring','Follow-up','Lost','Won','Won','Won'][i%6]
  if q['lines'][0]['productId']=='TEST-P031':outcome='Won'
  if q['lines'][0]['productId']=='TEST-P026':outcome='Follow-up'
  crm=dict(outcome=outcome,reason='TEST customer selected another offer' if outcome=='Lost' else 'TEST customer accepted quotation' if outcome=='Won' else '',lead=True,followup='TEST follow-up on 2026-11-05',updatedBy='u6',updatedAt='2026-10-22T09:00:00Z')
  portal['isCRM'][q['id']]=crm;q['portalCRM']=copy.deepcopy(crm)
 portal['salesActuals']=[] # Achievements must continue to come from approved IS invoices.
 portal['salesTargets']=[dict(id=f'TEST-TARGET-{i}',rep='u6',line=line,period='2026-10',amount=50000,**{'from':'2026-10','to':'2026-10'},enteredBy='u4') for i,line in enumerate(portal['productLines'])]
 for k in ['tasks','tickets','expenses','objectives','visits','demos','appraisals','hrprofiles','leavebalance','onboarding','training','trainerRequests','incentiveSchemes','incentiveClaims','payments','pipeline','tenders']:portal[k]=[]
 for i,u in enumerate(portal['users']):
  uid=u['id'];portal['hrprofiles'].append(dict(id=f'TEST-HR{i}',employee=uid,position=u['role'],start='2024-05-01',dob='1990-06-15',sex='Not specified',education='TEST degree',email=u['email'],address='TEST fictional address',phone='000-000-0000',emergency='TEST contact',employment='Active',owner='u1'))
  for leave in ['Annual leave','Sick leave','Personal leave']:portal['leavebalance'].append(dict(id=f'TEST-LV{i}-{leave}',employee=uid,year=2026,leaveType=leave,entitlement=12 if leave=='Annual leave' else 30 if leave=='Sick leave' else 6,carried=2,adjustment=0,remark='TEST entitlement',owner='u1'))
 for i in range(6):
  status=['Pending','Approved','Rejected'][i%3];owner='u6' if i%2 else 'u5'
  portal['tasks'].append(dict(id=f'TEST-TASK{i}',title=f'TEST follow-up task {i+1}',owner='u4',assignee=owner,due='2026-11-05',priority='High' if i%2 else 'Normal',details='TEST workflow exploration',status=['Not started','In progress','Completed'][i%3],history=[]))
  portal['tickets'].append(dict(id=f'TEST-TICKET{i}',title=f'TEST support case {i+1}',owner=owner,category='IT & software',priority='Normal',details='TEST support example',created='2026-10-20T09:00:00Z',status=['Open','In progress','Resolved'][i%3],history=[]))
  portal['expenses'].append(dict(id=f'TEST-EXP{i}',owner=owner,category='Local',title=f'TEST customer visit expenses {i+1}',project='TEST-DEMO',destination='Bangkok',method='Bank transfer',purpose='TEST training visit',items=[dict(date='2026-10-15',type='Transport',amount=800,rate=1,vat=0,currency='THB',detail='TEST transport',receipt=None)],amount=800,advance=0,status=status,created='2026-10-15T09:00:00Z'))
  portal['objectives'].append(dict(id=f'TEST-OBJ{i}',owner=owner,title=f'TEST quarterly objective {i+1}',period='Quarterly',start='2026-10-01',end='2026-12-31',measure='Complete 10 customer visits',progress=i*15,status=status,submittedAt='2026-10-01T09:00:00Z'))
  portal['visits'].append(dict(id=f'TEST-VISIT{i}',employee=owner,customer=db['customers'][i]['name'],visitdate='2026-10-15',contact='TEST laboratory manager',product=portal['productLines'][i%5],discussion='TEST product discussion',next='Arrange demonstration',due='2026-11-05',status='Follow-up',owner=owner))
  portal['demos'].append(dict(id=f'TEST-DEMO{i}',employee=owner,customer=db['customers'][i]['name'],product=portal['productLines'][i%5],equipment=f'TEST-EQUIP-{i:03}',start='2026-10-15',end='2026-11-15',status=['Planned','In progress','Completed'][i%3],feedback='TEST evaluation feedback',next='Review results',owner=owner))
  portal['appraisals'].append(dict(id=f'TEST-APP{i}',employee=owner,period='2026 Q3',reviewdate='2026-10-10',objectives=80+i,competency=4,strengths='TEST communication',development='TEST application training',status='Reviewed',owner='u4'))
  portal['training'].append(dict(id=f'TEST-TR{i}',topic=f'TEST product competency {i+1}',employee=owner,trainer='u4',category='Product / application',due='2026-11-15',materialId='',materialName='',status='Assigned' if i%2 else 'Completed',assignedBy='u4',history=[]))
 portal['trainerRequests']=[dict(id='TEST-TRAINER1',topic='TEST refresher training',requester='u6',trainer='u4',date='2026-11-10',reason='TEST competency refresher',status='Pending',history=[])]
 for i,typ in enumerate(['Onboarding','Offboarding','RoleChange']):portal['onboarding'].append(dict(id=f'TEST-LIFE{i}',employee='u5',owner='u1',type=typ,start='2026-10-01',due='2026-11-01',status='In progress',joinDate='2026-11-01',joiningDepartment='Diagnostics',mentor='u4',lastDay='2026-11-01',leavingReason='Contract end',handoverTo='u6',changeType='Promotion',effectiveDate='2026-11-01',oldPosition='Specialist',newPosition='Senior Specialist',oldDepartment='Diagnostics',newDepartment='Diagnostics',newManager='u4'))
 portal['requests']=[]
 for i,typ in enumerate(['travel','budget','leave','car','room','general']):portal['requests'].append(dict(id=f'TEST-REQ{i}',type=typ,title=f'TEST {typ} request',owner='u6',department='Diagnostics',details='TEST request details',start='2026-11-02T09:00' if typ in ['car','room'] else '2026-11-02',end='2026-11-02T11:00' if typ in ['car','room'] else '2026-11-03',amount=2500 if typ in ['travel','budget'] else 0,asset=portal['assets']['cars'][0] if typ=='car' else portal['assets']['rooms'][0] if typ=='room' else '',status='Pending',stage=0,history=[],date='2026-10-22',leaveType='Annual leave'))
 portal['incentiveSchemes']=[dict(id='TEST-SCHEME1',rep='u6',line='Allergy & Immunology',**{'from':'2026-08','to':'2026-10'},threshold=0,rate=2,createdBy='u4',createdAt='2026-10-01T09:00:00Z')]
 portal['incentiveClaims']=[dict(id='TEST-INC1',schemeId='TEST-SCHEME1',rep='u6',target=50000,actual=0,attainment=0,rate=2,amount=0,status='Withdrawn',submittedAt='2026-10-15T09:00:00Z',submittedBy='u6',reviewNote='TEST withdrawn claim — calculate a new claim from invoice actuals')]
 approved=next(x for x in portal['expenses'] if x['status']=='Approved')
 portal['payments']=[dict(id='TEST-PAY1',sourceType='expense',sourceId=approved['id'],owner=approved['owner'],title='TEST approved expense payment',amount=800,status='Awaiting accounting',requestedAt='2026-10-20T09:00:00Z',requestedBy='u4',history=[])]
 for kind in ['sops','jobdescriptions','kpis']:
  portal[kind]=[dict(id=f'TEST-{kind}1',number=f'TEST-{kind.upper()}-001',title=f'TEST {kind} example',department='Diagnostics',revision='1.0',effective='2026-10-01',review='2027-10-01',description='TEST downloadable sample document',sharedWith=['u5','u6'],owner='u1',fileName='TEST-sample.txt',fileType='text/plain',updatedAt='2026-10-22T09:00:00Z',history=[])]
 for category in ['forms','resources']:
  for i,r in enumerate(portal[category]):r.update(title='TEST '+r['title'],fileId=f'TEST-ATTACH-{category}-{i}',filename='TEST-sample.txt',sharedWith=['u1','u4','u5','u6'])
 for r in portal['announcements']:r['title']='TEST '+r['title'];r['body']='FICTIONAL TEST CONTENT. Explore acknowledgements and attachments.'
 # Budget: two fiscal years, non-zero plans, actuals, commitments and staffing assumptions.
 years={}
 for fy in [2026,2027]:
  state=dict(fy=fy,products=[],expenses=[],workforce=[],ledger=[],approvals=[],versions=[],settings=dict(divisionSplit=False),ocosNames=budget['ocosCategories'])
  for i,p in enumerate(budget['products']):
   p=copy.deepcopy(p);base=20000+(i%10)*5000;p.update(budget=months(base),cogsBudget=months(base*.45),revenueActual=[round(v*.75,2) if j<6 else 0 for j,v in enumerate(months(base))],cogsActual=[round(v*.34,2) if j<6 else 0 for j,v in enumerate(months(base))],costCenter=p.get('division','Diagnostics'),active=True);state['products'].append(p)
  for i,x in enumerate(budget['expenses']):
   x=copy.deepcopy(x);base=500+(i%12)*250;x.update(budget=months(base),actual=[round(base*.7,2) if j<6 else 0 for j in range(12)],commitment=[base if j==6 else 0 for j in range(12)],costCenter=x.get('division','Diagnostics'),active=True)
   if x.get('category')=='Other Cost of Sales':x['componentRows']=[dict(id=f'TEST-COMP{j}',name=name,active=True,budget=[round(v/len(budget['ocosCategories']),2) for v in x['budget']],actual=[round(v/len(budget['ocosCategories']),2) for v in x['actual']],commitment=[round(v/len(budget['ocosCategories']),2) for v in x['commitment']]) for j,name in enumerate(budget['ocosCategories'])]
   state['expenses'].append(x)
  for i,div in enumerate(['Diagnostics','LSR']):state['workforce'].append(dict(id=f'TEST-WF{i}',role='TEST Product Specialist',division=div,headcount=2,salary=35000,start=0,end=11,increment=5,bonus=1,benefits=8))
  # Detailed ledger explains every seeded actual and commitment without double-counting the summaries.
  for record in state['products']+state['expenses']:
   fields=['revenueActual','cogsActual'] if 'revenueActual' in record else ['actual','commitment']
   for field in fields:
    for month,amount in enumerate(record[field]):
     if amount:state['ledger'].append(dict(id=f'TEST-BL{len(state["ledger"]):05}',date=f'{fy-1 if month<8 else fy}-{month+5 if month<8 else month-7:02}-15',line=('cogs:'+record['id']) if field=='cogsActual' else record['id'],label=record['name'],type='Commitment' if field=='commitment' else 'Actual',month=month,amount=amount,reference='TEST-BUDGET-FIXTURE',note='TEST opening actual / commitment',division=record.get('division','Diagnostics'),costCenter=record['costCenter']))
  state['approvals']=[dict(id='TEST-BA1',date='2026-10-22',scope='All',division='Diagnostics',revision=1,note='TEST review submission',status='Submitted',history=[dict(action='Submitted',role='Department Manager',date='2026-10-22T09:00:00Z')])]
  state['versions']=[dict(id='TEST-VER1',date='2026-10-22',name='TEST baseline scenario',note='Fictional budget assumptions')]
  years[str(fy)]=state
 fixtures={server.IS_KEY:db,'biomed_portal_v33_clean':portal,'biomed_budget_v60_years':dict(active=2027,years=years),'biomed_budget_v65_zeroed_once':'yes','biomed_portal_active_demo_user':'u1'}
 server.initialize()
 with server.connect() as c:
  server.project(c,json.dumps(db))
  for key,value in fixtures.items():c.execute('INSERT INTO workspace VALUES(?,?,1)',(key,value if isinstance(value,str) else json.dumps(value,ensure_ascii=False)))
 counts={k:len(db[k]) for k in ['customers','suppliers','products','warehouses','documents','movements','quarantines','stockChecks','warehouseMoves','kits']}
 counts.update(portal_users=len(portal['users']),budget_years=list(years),budget_products_per_year=len(years['2027']['products']),budget_expenses_per_year=len(years['2027']['expenses']))
 (ROOT/'Test_Data_Summary.json').write_text(json.dumps(counts,indent=2))
 print(json.dumps(counts,indent=2))
if __name__=='__main__':make()
