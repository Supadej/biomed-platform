"""Expanded, deterministic fictional workflow fixtures; additive and repeatable."""
import json,datetime,math
PREFIX='TEST-DEMO-V2-'
def add(c,owner):
 today=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).date()
 def day(n=0):return (today+datetime.timedelta(days=n)).isoformat()
 def load(key):return json.loads(c.execute('SELECT value FROM workspace WHERE key=?',(key,)).fetchone()[0])
 def put(key,d):c.execute('UPDATE workspace SET value=?,revision=revision+1 WHERE key=?',(json.dumps(d,ensure_ascii=False),key))
 def push(d,field,record):
  if not any(isinstance(r,dict) and r.get('id')==record['id'] for r in d.setdefault(field,[])):d[field].append(record)
 portal=load('biomed_portal_v33_clean')
 for i in range(6):
  push(portal,'users',{'id':PREFIX+'EMP-'+str(i),'name':'DEMO Employee '+str(i+1),'email':'demo.employee'+str(i+1)+'@example.invalid','role':'Employee','department':['Diagnostics','Life Science Research','Service'][i%3],'managerId':owner,'active':True})
 people=[owner]+[PREFIX+'EMP-'+str(i) for i in range(6)]
 for i in range(36):
  who=people[i%7];status=['Pending','Approved','Rejected','Cancelled'][(i//6)%4];typ=['travel','budget','leave','car','room','general'][i%6]
  date=day(i-18);ident=PREFIX+'REQUEST-'+str(i)
  record={'id':ident,'owner':who,'title':f'DEMO {typ.title()} request {i+1:02}','type':typ,'department':['Diagnostics','Life Science Research','Service'][i%3],'details':'Fictional workflow test. No real booking or expense.','start':date,'end':date,'date':date,'amount':(i+1)*350 if typ in ('travel','budget') else 0,'asset':'Company Car 1' if typ=='car' else 'Meeting Room A' if typ=='room' else '', 'status':status,'stage':0,'history':[]}
  if typ=='leave':record.update(leaveType='Annual leave',days=1,reason='DEMO personal leave',attachments=[])
  push(portal,'requests',record)
 for field,statuses,size in [('tasks',['Not started','In progress','Completed'],30),('tickets',['Open','In progress','Resolved','Closed'],20),('objectives',['Pending','Approved','Rejected'],18),('expenses',['Pending','Approved','Rejected','Cancelled'],24),('visits',['Open','Follow-up','Completed'],18),('demos',['Draft','Pending','Approved','Rejected','Cancelled'],20),('tenders',['Preparing','Submitted','Clarification','Won','Lost','Cancelled'],18),('pipeline',['Lead','Qualified','Proposal','Negotiation','Won','Lost'],18),('appraisals',['Draft','Submitted','Reviewed'],12),('onboarding',['Open','In progress','Completed'],12)]:
  for i in range(size):
   who=owner if i%2==0 else people[1+i%6];date=day(i-size//2);st=statuses[i%len(statuses)]
   r={'id':PREFIX+field.upper()+'-'+str(i),'owner':who,'employee':who,'title':f'DEMO {field} scenario {i+1:02}','status':st,'created':date+'T09:00:00+07:00','date':date,'history':[],'details':'Fictional testing example','department':'Diagnostics'}
   if field=='tasks':r.update(due=day(i-10),priority=['Normal','High','Critical'][i%3])
   if field=='tickets':r.update(category=['IT & software','Office & facility','Logistics & warehouse'][i%3],priority=['Normal','High','Critical'][i%3])
   if field=='objectives':r.update(period=['Weekly','Monthly','Quarterly','Annual'][i%4],start=day(-15),end=day(15),measure='Complete '+str(i+2)+' DEMO activities',progress=(i*13)%101,submittedAt=date,reviewedBy=owner if st!='Pending' else '')
   if field=='expenses':r.update(category=['Local','Upcountry','Overseas','Other'][i%4],amount=800+i*250,advance=0,project='DEMO Testing',destination='DEMO Centre',method='Reimbursement',purpose='Fictional travel expense',items=[{'date':date,'type':'Travel','amount':800+i*250,'rate':1,'vat':0,'currency':'THB','detail':'DEMO expense','receipt':None}])
   if field in ('visits','demos','tenders','pipeline'):r.update(customer='DEMO Research Centre '+str(i%8+1),product='Diagnostics',contact='DEMO Contact',next='Review DEMO follow-up',start=date,end=day(i-size//2+3))
   if field=='visits':r.update(visitdate=date,discussion='DEMO instrument training and reagent discussion',due=day(i-4))
   if field=='demos':r.update(equipment='DEMO Analyzer '+str(i%4+1),feedback='Fictional evaluation',approvalBy=owner,submittedAt=date,history=[])
   if field=='tenders':r.update(reference=PREFIX+'TENDER-'+str(i),amount=50000+i*7500,deadline=day(i),submitted=date,remarks='Fictional tender outcome')
   if field=='pipeline':r.update(opportunity='DEMO laboratory placement '+str(i+1),value=75000+i*12000,probability=[10,25,50,75,100,0][i%6],closing=day(i+5),stage=st)
   if field=='appraisals':r.update(period='DEMO Q4',reviewdate=date,objectives=55+i*4,competency=1+i%5,strengths='DEMO learning progress',development='DEMO training plan')
   if field=='onboarding':r.update(type=['Onboarding','Offboarding','Role change'][i%3],start=date,due=day(i+4),checklist=[],notes='Fictional lifecycle scenario')
   push(portal,field,r)
 for field in ('announcements','forms','resources','sops','jobdescriptions','kpis','training'):
  for i in range(6):
   push(portal,field,{'id':PREFIX+field+'-'+str(i),'owner':owner,'title':f'DEMO {field} reference {i+1}','body':'Fictional testing content only.','description':'Fictional example; no attachment.','category':'Training','date':day(i-4),'by':'Demo administrator','url':'','sharedWith':[owner],'department':'Diagnostics','version':'1.0','status':(['Assigned','In progress','Completed'][i%3] if field=='training' else 'Active'),'attendees':[],'employee':owner,'trainer':owner,'assignedBy':owner,'due':day(i+5),'history':[]})
 for i,who in enumerate(people):
  push(portal,'leavebalance',{'id':PREFIX+'LEAVE-'+who,'owner':who,'employee':who,'year':today.year,'leaveType':'Annual leave','entitlement':15,'carried':2,'adjustment':0,'remark':'DEMO entitlement'})
  # Fictional profiles for fictional employees only, preserving real employee profiles.
  if who!=owner:push(portal,'hrprofiles',{'id':PREFIX+'HR-'+who,'owner':who,'employee':who,'position':'DEMO Specialist','start':day(-365-i*30),'employment':['Active','Probation','On leave'][i%3],'email':'demo.employee'+str(i)+'@example.invalid','education':'Fictional testing profile','sex':'Not specified'})
 for i in range(6):
  status=['Awaiting accounting','Processing','Paid','Returned'][i%4]
  push(portal,'payments',{'id':PREFIX+'PAY-'+str(i),'owner':owner,'title':'DEMO reimbursement '+str(i+1),'amount':800+(1+4*i)*250,'status':status,'requestedAt':day(i-6),'requestedBy':owner,'sourceType':'expense','sourceId':PREFIX+'EXPENSES-'+str(1+4*i),'history':[]})
 for i in range(12):
  line=(portal.get('productLines') or ['Diagnostics'])[i%len(portal.get('productLines') or ['Diagnostics'])];period=day(-30*(i//4))[:7]
  for field in ('salesTargets','salesActuals'):
   push(portal,field,{'id':PREFIX+field+str(i),'rep':owner,'line':line,'period':period,'amount':100000+i*12000 if field=='salesTargets' else 65000+i*9000,'note':'DEMO performance example','enteredBy':owner})
 for i in range(4):
  line=(portal.get('productLines') or ['Diagnostics'])[i%len(portal.get('productLines') or ['Diagnostics'])]
  scheme={'id':PREFIX+'SCHEME-'+str(i),'rep':owner,'line':line,'from':day()[:7],'to':day()[:7],'rate':1.5+i*.5,'threshold':70,'revision':1,'createdBy':owner,'createdAt':day()}
  push(portal,'incentiveSchemes',scheme)
  push(portal,'incentiveClaims',{'id':PREFIX+'CLAIM-'+str(i),'schemeId':scheme['id'],'schemeSnapshot':scheme,'rep':owner,'target':100000,'actual':120000,'attainment':120,'rate':scheme['rate'],'amount':120000*scheme['rate']/100,'status':['Pending','Approved','Rejected','Withdrawn'][i],'submittedBy':owner,'submittedAt':day(i-4),'reviewedBy':owner if i else ''})
 put('biomed_portal_v33_clean',portal)
 db=load('biomed_is_v50_transactions')
 for i in range(8):
  push(db,'customers',{'id':PREFIX+'CUST-'+str(i),'name':'DEMO Research Centre '+str(i+1),'category':'DEMO customer','creditDays':[0,30,60][i%3],'active':True})
  push(db,'suppliers',{'id':PREFIX+'SUP-'+str(i),'name':'DEMO Supplier '+str(i+1),'currency':'THB','country':'Thailand','active':True})
  push(db,'products',{'id':PREFIX+'PROD-'+str(i),'name':'DEMO '+['Allergy Kit','PCR Reagent','Control Material','Training Analyzer','Culture Medium','Antibody Set','ELISpot Kit','Consumable Pack'][i],'brand':'DEMO Brand '+str(i%3+1),'sku':'DEMO-SKU-'+str(i),'category':'DEMO training','line':'Diagnostics' if i%2==0 else 'Life Science Research','unit':'kit','vat':7,'price':2500+i*500,'cost':1200+i*250,'active':True,'storage':'2–8°C'})
 for i in range(3):push(db,'warehouses',{'id':PREFIX+'WH-'+str(i),'name':'DEMO Warehouse '+str(i+1),'active':True})
 # Opening fictional balances, not posted transaction movements.
 for i in range(24):push(db,'lots',{'id':PREFIX+'LOT-'+str(i),'productId':PREFIX+'PROD-'+str(i%8),'warehouse':'DEMO Warehouse '+str(i%3+1),'lot':'DEMO-LOT-'+str(i),'expiry':day([-30,20,90,365][i%4]),'qty':[0,10,25,60][i%4],'held':i%5==0})
 import permissions_policy as policy
 for kind in policy.CATALOG['transactions']:
  for i,st in enumerate(['Draft','Pending','Rejected','Cancelled']):
   push(db,'documents',{'id':PREFIX+kind+'-'+str(i),'kind':kind,'ref':PREFIX+kind.upper()+'-'+str(i),'date':day(i*4-8),'party':PREFIX+('SUP-' if kind in ('purchase-request','purchase-order','supplier-confirm','delivery-in','check-in') else 'CUST-')+str(i),'status':st,'owner':owner,'created':day(i*4-8)+'T09:00:00+07:00','history':[],'lines':[{'productId':PREFIX+'PROD-'+str(i),'qty':i+2,'price':2500+i*500}],'warehouse':'DEMO Warehouse 1','currency':'THB','portalRep':owner,'portalLine':'Diagnostics','notes':'Fictional DEMO fixture, no real goods moved. Use normal workflow to post Draft/Pending stock documents.'})
 for i in range(12):
  quote=PREFIX+'APPROVED-QUOTE-'+str(i)
  push(db,'documents',{'id':quote,'kind':'quotation','ref':quote,'date':day(i-6),'party':PREFIX+'CUST-'+str(i%8),'status':'Approved','owner':owner,'created':day(i-6)+'T09:00:00+07:00','history':[],'lines':[{'productId':PREFIX+'PROD-'+str(i%8),'qty':3+i,'price':2500+(i%8)*500}],'currency':'THB','portalRep':owner,'portalLine':'Diagnostics','notes':'Fictional approved offer for testing conversion.'})
  portal.setdefault('isCRM',{}).setdefault(quote,{'outcome':['Monitoring','Follow-up','Won','Lost'][i%4],'reason':'DEMO outcome justification','lead':i%3!=0,'followup':'DEMO next step','updatedBy':owner,'updatedAt':day(i-6)})
  if i%4==2:
   q=next(d for d in db['documents'] if d['id']==quote)
   push(db,'documents',{**q,'id':PREFIX+'ORDER-'+str(i),'ref':PREFIX+'ORDER-'+str(i),'kind':'sales-order','status':'Approved','sourceId':quote})
   push(db,'documents',{**q,'id':PREFIX+'INVOICE-'+str(i),'ref':PREFIX+'INVOICE-'+str(i),'kind':'invoice','status':'Approved','sourceId':PREFIX+'ORDER-'+str(i),'notes':'Fictional invoice for testing sales summaries; affects demo totals.'})
 put('biomed_portal_v33_clean',portal);put('biomed_is_v50_transactions',db)
 import serve
 serve.project(c,json.dumps(db))
 budget=load('biomed_budget_v60_years');fy=today.year+(today.month>=5)
 categories=['Promotional Expenses','Administrative Expenses','Financial Expenses','Other Expenses','Salary and Bonus','Commission and Incentive','Social Security and Provident Fund','Healthcare Coverage','Local Traveling and Expenses','Overseas Traveling and Expenses','Trainings and KOM','Other Cost of Sales']
 for year in (fy-1,fy,fy+1):
  y=budget.setdefault('years',{}).setdefault(str(year),{'fy':year,'products':[],'expenses':[],'workforce':[],'ledger':[],'approvals':[],'versions':[],'settings':{'divisionSplit':False}})
  months=12 if year<fy else (today.month-5)%12+1 if year==fy else 0
  for i in range(8):
   ident=PREFIX+'BP-'+str(i);plan=[round((20000+i*5000)*(1+.15*math.sin((m+i)*math.pi/6))) for m in range(12)];actual=[round(v*(.7+(i%4)*.15)) if m<months else 0 for m,v in enumerate(plan)];cost=[round(v*.55) for v in actual]
   push(y,'products',{'id':ident,'name':'DEMO Product line '+str(i+1),'division':'Diagnostics','costCenter':'DEMO Diagnostics','active':True,'source':'Fictional testing','budget':plan,'cogsBudget':[round(v*.55) for v in plan],'revenueActual':actual,'cogsActual':cost})
   for field,line,amounts in [('revenueActual',ident,actual),('cogsActual','cogs:'+ident,cost)]:
    for m,amount in enumerate(amounts):
     if amount:push(y,'ledger',{'id':PREFIX+str(year)+field+str(i)+'-'+str(m),'date':f'{year-1 if m<8 else year}-{m+5 if m<8 else m-7:02}-15','line':line,'label':'DEMO Product line '+str(i+1),'month':m,'type':'Actual','amount':amount,'reference':PREFIX+'BUDGET','note':'Fictional testing','division':'Diagnostics','costCenter':'DEMO Diagnostics'})
  for i,category in enumerate(categories):
   ident=PREFIX+'BE-'+str(i);plan=[2500+i*750]*12;actual=[round(v*(.65+(i%5)*.12)) if m<months else 0 for m,v in enumerate(plan)];commit=[round(v*.3) if months<=m<min(months+3,12) else 0 for m,v in enumerate(plan)]
   push(y,'expenses',{'id':ident,'name':'DEMO '+category,'category':category,'division':'Diagnostics','costCenter':'DEMO Diagnostics','active':True,'source':'Fictional testing','budget':plan,'actual':actual,'commitment':commit})
   for typ,values in [('Actual',actual),('Commitment',commit)]:
    for m,amount in enumerate(values):
     if amount:push(y,'ledger',{'id':PREFIX+str(year)+typ+str(i)+'-'+str(m),'date':f'{year-1 if m<8 else year}-{m+5 if m<8 else m-7:02}-15','line':ident,'label':'DEMO '+category,'month':m,'type':typ,'amount':amount,'reference':PREFIX+'BUDGET','note':'Fictional testing','division':'Diagnostics','costCenter':'DEMO Diagnostics'})
  for i,st in enumerate(['Submitted','Department Approved','Finance Approved','Approved','Returned']):
   push(y,'approvals',{'id':PREFIX+'APP-'+str(i),'date':day(i-5),'scope':['Product & COGS plan','Promotional Expenses','Administrative Expenses','Local Traveling and Expenses','Other Expenses'][i],'division':'DEMO Diagnostics','costCenter':'DEMO Diagnostics','revision':1,'note':'Fictional approval scenario','status':st,'history':[{'action':'Submitted','role':'DEMO','date':day(i-5)}]})
  for i in range(3):
   push(y,'workforce',{'id':PREFIX+'WF-'+str(i),'role':'DEMO Specialist '+str(i+1),'division':'DEMO Diagnostics','costCenter':'DEMO Diagnostics','headcount':i+1,'salary':25000+i*10000,'start':0,'end':11,'increment':5,'bonus':1,'benefits':8})
  push(y,'versions',{'id':PREFIX+'VERSION','date':day(),'scope':'Local Traveling and Expenses','division':'DEMO Diagnostics','costCenter':'DEMO Diagnostics','revision':1,'budgetTotal':sum(sum(p['budget']) for p in y['products'] if p.get('id','').startswith(PREFIX)),'versionType':'DEMO approved scope snapshot'})
  push(y,'costCenters',{'id':PREFIX+'CC','name':'DEMO Diagnostics','active':True})
 put('biomed_budget_v60_years',budget)
 if c.execute("SELECT 1 FROM sqlite_master WHERE name='crm_records'").fetchone():
  import crm_api as crm
  identity=c.execute('SELECT crm_user_id FROM crm_identity WHERE portal_user_id=?',(owner,)).fetchone()
  uid=identity[0] if identity else crm.insert(c,'Users',{'FirstName':'DEMO','LastName':'Test owner','PortalUserId':owner,'Enabled':True})['Id']
  if not identity:c.execute('INSERT INTO crm_identity VALUES(?,?)',(owner,uid))
  def record(entity,tag,data):
   key=PREFIX+tag;row=c.execute("SELECT record_id FROM crm_links WHERE source='demo-v2' AND source_id=? AND entity=?",(key,entity)).fetchone()
   if row:return row[0]
   ident=crm.insert(c,entity,data)['Id'];c.execute('INSERT INTO crm_links VALUES(?,?,?,?)',('demo-v2',key,entity,ident));return ident
  project=record('Projects','PROJECT',{'Name':'DEMO Diagnostic training programme','Description':'Fictional project for workflow testing'})
  stages=[record('ProjectPipeline','STAGE-'+str(i),{'Name':'DEMO '+name,'ProjectId':project,'Order':i+1,'StageType':['open','in_progress','done'][i],'Color':'#087e79'}) for i,name in enumerate(['Planning','In progress','Completed'])]
  pipelines=crm.rows(c,'CRMPipelines');tickets=crm.rows(c,'HelpDeskPipelines')
  for i in range(24):
   record('Leads','LEAD-'+str(i),{'LeadName':'DEMO Sales Plan '+str(i+1),'MainUserId':uid,'Creation':day(i-12),'LastUpdated':day(i-12),'Expected':day(i),'ExpectedRevenue':75000+i*8500,'Budget':100000+i*10000,'CRMPipelineId':pipelines[i%len(pipelines)]['Id'] if pipelines else None,'WinOrLost':[None,None,None,None,True,False][i%6],'ProductLine':'Diagnostics','AdditionalInfo':'Fictional customer opportunity'})
   record('Events','EVENT-'+str(i),{'Title':'DEMO '+['Customer visit','Training','Team review'][i%3]+' '+str(i+1),'Description':'Fictional test event','StartDate':day(i-12)+'T10:00:00','EndDate':day(i-12)+'T11:00:00','IsAllDay':False,'MainUserID':uid,'Plan':'DEMO testing session'})
   record('ProjectActivity','ACTIVITY-'+str(i),{'Name':'DEMO Project activity '+str(i+1),'Description':'Fictional project task','MainUserId':uid,'ProjectId':project,'ProjectPipelineId':stages[i%3],'ActivityDate':day(i-12),'Creation':day(i-12),'Done':i%3==2,'Budget':5000+i*300,'NextStep':'Review DEMO result'})
   record('HelpDeskTickets','TICKET-'+str(i),{'Title':'DEMO External support '+str(i+1),'Problem':'Fictional instrument support request','Solution':'DEMO resolved example' if i%4==3 else '', 'Status':['Open','In progress','Waiting','Resolved'][i%4],'Priority':i%3,'CreatedByUserId':uid,'AssignedToUserId':uid,'CreatedDate':day(i-12),'DueDate':day(i-8),'PipelineId':tickets[i%len(tickets)]['Id'] if tickets else None,'PipelineStatus':['open','in_progress','waiting','resolved'][i%4]})
