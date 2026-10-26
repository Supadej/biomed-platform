"""Explicit preview/run bridges into CRM. Snapshots never post stock or finance back."""
import json,hashlib,re,datetime
from urllib.parse import urlsplit,parse_qs
import crm_api as crm
import permissions_policy as policy
DIRECTIONS={
 'is-crm':{'title':'Biomed IS → CRM','source':'biomed_is_v50_transactions','sections':{'customers':['id','name','contact','email','phone','address','taxId','department'],'products':['id','name','catalogueNo','sku','brand','unit','barcode','storage'],'documents':['id','ref','kind','date','party','status','currency','sourceId','lines'],'stock':['productId','warehouse','lot','expiry','qty','held']},'defaults':['customers','products','documents']},
 'portal-crm':{'title':'Staff Portal → CRM','source':'biomed_portal_v33_clean','sections':{'people':['id','name','email','department','managerId'],'opportunities':['id','title','customer','customerId','product','value','amount','status','owner','employee','opportunity','reference','closing','deadline','stage','date'],'visits':['id','title','customer','customerId','date','visitdate','start','end','owner','employee','notes','discussion','next'],'helpdesk':['id','title','description','details','status','priority','owner','date','created']},'defaults':['people','opportunities','visits']},
 'budget-crm':{'title':'Budgeting → CRM','source':'biomed_budget_v60_years','sections':{'targets':['id','name','costCenter','budget','revenueActual'],'budgets':['id','name','category','costCenter','budget','actual','commitment']},'defaults':['targets','budgets']}}

def default(direction):
 spec=DIRECTIONS[direction];return {'enabled':True,'sections':spec['defaults'],'fields':{k:list(v) for k,v in spec['sections'].items()},'statuses':['Approved'],'documentKinds':['quotation','customer-order','sales-order','purchase-order','invoice','credit-note','debit-note','payment-receipt'],'fy':2027,'userMap':{},'productMap':{},'customerMap':{},'costCenterMap':{},'pipelineMap':{},'ticketPipelineMap':{},'allowPartial':False}

def config(c,direction):
 row=c.execute('SELECT payload,revision FROM crm_bridge_config WHERE direction=?',(direction,)).fetchone();return (json.loads(row[0]),row[1]) if row else (default(direction),0)

def validate(direction,value):
 if not isinstance(value,dict):raise ValueError('Bridge rules must be an object')
 spec=DIRECTIONS[direction];out=default(direction);out.update({k:v for k,v in value.items() if k in out})
 if not isinstance(out['sections'],list) or set(out['sections'])-set(spec['sections']):raise ValueError('Unknown bridge section')
 if not isinstance(out['fields'],dict):raise ValueError('Field selections must be an object')
 for section,fields in out['fields'].items():
  if section not in spec['sections'] or not isinstance(fields,list) or set(fields)-set(spec['sections'][section]):raise ValueError('Invalid selected attributes')
 for key in ['userMap','productMap','customerMap','costCenterMap','pipelineMap','ticketPipelineMap']:
  if not isinstance(out[key],dict) or any(not isinstance(k,str) or not isinstance(v,(str,int)) for k,v in out[key].items()):raise ValueError('Mappings must contain source ID to destination ID pairs')
 if not isinstance(out['statuses'],list) or set(out['statuses'])-{'Approved','Draft','Pending','Rejected','Cancelled'}:raise ValueError('Invalid document statuses')
 if not isinstance(out['documentKinds'],list) or len(out['documentKinds'])>30:raise ValueError('Invalid document kinds')
 out['fy']=int(out['fy'])
 if not 2020<=out['fy']<=2100:raise ValueError('Select a valid fiscal year')
 out['enabled']=bool(out['enabled']);out['allowPartial']=bool(out['allowPartial']);return out

def source(c,perms,direction):
 spec=DIRECTIONS[direction];key=spec['source'];row=c.execute('SELECT value,revision FROM workspace WHERE key=?',(key,)).fetchone()
 raw=row[0] if row and row[0] else '{}';filtered=policy.read_filter(perms,key,raw)
 return json.loads(filtered or '{}'),row[1] if row else 0

def require_sources(perms,direction,rules):
 sections=rules['sections']
 if direction=='is-crm':
  policy.need(perms,'is_view')
  for section,key in [('customers','is.master-customers.view'),('products','is.master-products.view'),('stock','is.stock-inventory.view')]:
   if section in sections:policy.need(perms,key)
  if 'documents' in sections:
   for k in rules['documentKinds']:policy.need(perms,'is.'+k+'.view')
 if direction=='portal-crm':
  for section,modules in [('people',['users']),('opportunities',['pipeline','tenders']),('visits',['visits']),('helpdesk',['helpdesk'])]:
   if section in sections:
    for m in modules:policy.need(perms,m)
 if direction=='budget-crm':
  policy.need(perms,'budget_view')
  if 'targets' in sections:policy.need(perms,'budget.products.view')
  if 'budgets' in sections:
   # Expense information is read through the existing schedule-scope filter.
   if not any(p.startswith('budget.expense_') and p.endswith('.view') or p.startswith('budget.person_') and p.endswith('.view') or p=='budget.ocos.view' for p in perms):raise policy.PermissionDenied('Budget expense schedule view permission required')

def preview(c,actor,perms,direction):
 crm.need(perms,'bridges');rules,revision=config(c,direction);require_sources(perms,direction,rules);data,source_revision=source(c,perms,direction);crm.bind_users(c);items=[];exceptions=[]
 def select(section,row):return {k:row[k] for k in rules['fields'].get(section,[]) if k in row}
 def add(section,source_id,entity,record):
  module=crm.MODULES.get(entity,'finance');crm.need(perms,module,'import')
  items.append({'section':section,'sourceId':str(source_id),'entity':entity,'record':record})
 def mapped(key,id):
  target=rules[key].get(str(id));return int(target) if str(target).isdigit() else None
 if not rules['enabled']:exceptions.append('Bridge is disabled')
 elif direction=='is-crm':
  if 'customers' in rules['sections']:
   for row in data.get('customers',[]):
    if row.get('active') is False:continue
    x=select('customers',row);add('customers',row['id'],'Organizations',{'Name':x.get('name',row['id']),'ExternalId':row['id'],'CustomerAttributes':x})
    add('customers',row['id'],'Departments',{'Name':x.get('department') or 'Customer contacts','_organizationSource':str(row['id'])})
    add('customers',row['id'],'Contacts',{'Name':x.get('contact') or x.get('name') or str(row['id']),'Email':x.get('email'),'Phone':x.get('phone'),'Address':x.get('address'),'_departmentSource':str(row['id'])})
    if 'address' in x or 'taxId' in x:add('customers',row['id'],'BillingInformations',{'Name':x.get('name') or str(row['id']),'Address':x.get('address'),'TaxID':x.get('taxId'),'Email':x.get('email'),'Phone':x.get('phone'),'_contactSource':str(row['id'])})
  if 'products' in rules['sections']:
   for row in data.get('products',[]):
    if row.get('active') is False:continue
    x=select('products',row)
    if x.get('brand') and not any(i['entity']=='InventoryBrands' and i['sourceId']==str(x['brand']) for i in items):add('products',x['brand'],'InventoryBrands',{'Name':x['brand'],'InventoryBrandType':'Linked IS brand','InventoryBrandDistriutor':'Biomed Diagnostics'})
    add('products',row['id'],'InventoryProducts',{'Name':x.get('name',row['id']),'CategoryNumber':x.get('catalogueNo') or x.get('sku'),'Description':x.get('name'),'Unit':x.get('unit'),'Type':0,'StockCount':0,'ISProductId':row['id'],'CatalogAttributes':x,'_brandSource':str(x['brand']) if x.get('brand') else None})
  if 'documents' in rules['sections']:
   for row in data.get('documents',[]):
    if row.get('kind') not in rules['documentKinds'] or row.get('status') not in rules['statuses']:continue
    x=select('documents',row);amount=sum(float(l.get('qty') or 0)*float(l.get('price') or 0) for l in row.get('lines',[]))
    add('documents',row['id'],'ExternalSnapshots',{'Name':row.get('ref',row['id']),'Kind':row['kind'],'Date':row.get('date'),'Status':row.get('status'),'Currency':row.get('currency','THB'),'Amount':round(amount,2),'AmountBasis':'Line quantity × unit price before document discounts/VAT','Attributes':x,'SourceUrl':'/biomed-is.html?record='+str(row['id'])})
  if 'stock' in rules['sections']:
   lots={}
   for m in data.get('movements',[]):
    key=(m.get('productId'),m.get('warehouse'),m.get('lot'));x=lots.setdefault(key,{'productId':key[0],'warehouse':key[1],'lot':key[2],'qty':0,'expiry':''});x['qty']+=float(m.get('change') or 0)
    if m.get('expiry'):x['expiry']=m['expiry']
   for key,row in lots.items():
    row['held']=next((q.get('status')=='Held' for q in reversed(data.get('quarantines',[])) if (q.get('productId'),q.get('warehouse'),q.get('lot'))==key),False)
    add('stock','|'.join(str(v) for v in key),'ExternalSnapshots',{'Name':' / '.join(str(v) for v in key),'Kind':'Stock snapshot','Attributes':select('stock',row),'SourceUrl':'/biomed-is.html'})
 elif direction=='portal-crm':
  if 'people' in rules['sections']:
   for row in data.get('users',[]):
    id=c.execute('SELECT crm_user_id FROM crm_identity WHERE portal_user_id=?',(str(row['id']),)).fetchone()
    if id:add('people',row['id'],'Users',{'BoundCRMUserId':id[0],'StaffAttributes':select('people',row)})
  if 'opportunities' in rules['sections']:
   for module in ['pipeline','tenders']:
    for row in data.get(module,[]):
     owner=row.get('owner') or row.get('employee') or row.get('userId');uid=mapped('userMap',owner)
     if uid is None:
      identity=c.execute('SELECT crm_user_id FROM crm_identity WHERE portal_user_id=?',(str(owner),)).fetchone();uid=identity[0] if identity else None
     if uid is None:exceptions.append(module+'/'+str(row.get('id'))+': map owner '+str(owner));continue
     x=select('opportunities',row);pipeline=mapped('pipelineMap',row.get('stage') or row.get('status')) or rows_first(c,'CRMPipelines')
     if not crm.raw(c,'CRMPipelines',pipeline):exceptions.append('Map opportunity stage '+str(row.get('stage') or row.get('status')));continue
     value=x.get('value',x.get('amount',0))
     try:value=float(value or 0)
     except (TypeError,ValueError):exceptions.append(module+'/'+str(row.get('id'))+': numeric expected value required');continue
     add('opportunities',module+':'+str(row['id']),'Leads',{'LeadName':x.get('title') or x.get('opportunity') or x.get('reference') or row.get('name') or 'Portal '+str(row['id']),'MainUserId':uid,'ExpectedRevenue':value,'Currency':row.get('currency','THB'),'CRMPipelineId':pipeline,'AdditionalInfo':json.dumps(x,ensure_ascii=False),'Creation':row.get('date'),'Expected':x.get('closing') or x.get('deadline'),'ExternalStatus':row.get('status') or row.get('stage')})
  for section,table,entity in [('visits','visits','Events'),('helpdesk','tickets','HelpDeskTickets')]:
   if section not in rules['sections']:continue
   for row in data.get(table,[]):
    owner=row.get('owner') or row.get('employee') or row.get('userId');uid=mapped('userMap',owner);bound=c.execute('SELECT crm_user_id FROM crm_identity WHERE portal_user_id=?',(str(owner),)).fetchone();uid=uid or (bound[0] if bound else None)
    if uid is None:exceptions.append(section+'/'+str(row.get('id'))+': map owner '+str(owner));continue
    x=select(section,row);record={'Title':x.get('title') or x.get('customer') or row.get('subject') or section+' '+str(row['id']),'Description':x.get('notes') or x.get('discussion') or x.get('description') or x.get('details'),'SourceAttributes':x}
    if entity=='Events':record.update(MainUserID=uid,StartDate=x.get('start') or x.get('date') or x.get('visitdate'),EndDate=x.get('end') or x.get('date') or x.get('visitdate'))
    else:record.update(CreatedByUserId=uid,AssignedToUserId=uid,PipelineId=mapped('ticketPipelineMap',row.get('status')) or rows_first(c,'HelpDeskPipelines'),Status=row.get('status'),Problem=x.get('description') or x.get('details'),CreatedDate=x.get('date') or x.get('created'))
    add(section,row['id'],entity,record)
 elif direction=='budget-crm':
  year=data.get('years',{}).get(str(rules['fy']))
  if not year:exceptions.append('Fiscal year '+str(rules['fy'])+' is not available')
  else:
   if 'targets' in rules['sections']:
    for row in year.get('products',[]):
     id=mapped('productMap',row['id'])
     if id is None or not crm.raw(c,'Products',id):exceptions.append('Map budget product '+str(row['id'])+' to a CRM portfolio product');continue
     x=select('targets',row);fy=rules['fy'];add('targets',str(fy)+':'+str(row['id']),'Targets',{'Name':'FY'+str(fy)+' · '+str(x.get('name',row['id'])),'ProductID':id,'TargetValue':round(sum(float(v or 0) for v in x.get('budget',[])),2),'StartDate':f'{fy-1}-05-01','EndDate':f'{fy}-04-30','FinancialYear':fy,'CostCenter':rules['costCenterMap'].get(str(x.get('costCenter')),x.get('costCenter')),'ActualValue':round(sum(float(v or 0) for v in x.get('revenueActual',[])),2),'MonthlyBudget':x.get('budget',[]),'MonthlyActual':x.get('revenueActual',[])})
   if 'budgets' in rules['sections']:
    for row in year.get('expenses',[]):
     x=select('budgets',row);add('budgets',str(rules['fy'])+':'+str(row['id']),'ExternalSnapshots',{'Name':x.get('name',row['id']),'Kind':'Budget expense snapshot','FinancialYear':rules['fy'],'CostCenter':rules['costCenterMap'].get(str(x.get('costCenter')),x.get('costCenter')),'Currency':'THB','Budget':round(sum(float(v or 0) for v in x.get('budget',[])),2),'ActualValue':round(sum(float(v or 0) for v in x.get('actual',[])),2),'CommitmentValue':round(sum(float(v or 0) for v in x.get('commitment',[])),2),'Attributes':x,'SourceUrl':'/biomed-budget.html?tab=reports'})
 # Snapshot only data authorised by current source and CRM grants. No fuzzy matching or writeback.
 payload={'direction':direction,'rules':rules,'configRevision':revision,'sourceRevision':source_revision,'actor':actor[0],'grants':sorted(perms),'items':items,'exceptions':exceptions}
 digest=hashlib.sha256(crm.dump(payload).encode()).hexdigest();return {'direction':direction,'config':rules,'revision':revision,'sourceRevision':source_revision,'token':digest,'items':items,'exceptions':exceptions,'summary':{'records':len(items),'exceptions':len(exceptions)}}

def rows_first(c,entity):return next(iter(crm.rows(c,entity)),{}).get('Id')

def handle(c,actor,perms,path,method,data):
 chunks=urlsplit(path).path.strip('/').split('/')
 if len(chunks)!=5:raise ValueError('Invalid CRM bridge route')
 direction,action=chunks[3:]
 if direction not in DIRECTIONS:raise ValueError('Unknown CRM bridge')
 crm.need(perms,'bridges')
 if action=='config' and method=='GET':
  rules,revision=config(c,direction);return {'direction':direction,'title':DIRECTIONS[direction]['title'],'config':rules,'revision':revision,'attributes':DIRECTIONS[direction]['sections'],'destinations':{'users':[{'id':r['Id'],'name':str(r.get('FirstName',''))+' '+str(r.get('LastName',''))} for r in crm.rows(c,'Users') if crm.related_allowed(perms,'Users')],'products':[{'id':r['Id'],'name':r.get('Name')} for r in crm.rows(c,'Products') if crm.related_allowed(perms,'Products')]},'history':[dict(zip(['id','at','actor','summary'],r)) for r in c.execute('SELECT id,at,actor,result FROM crm_bridge_runs WHERE direction=? ORDER BY id DESC LIMIT 20',(direction,))]}
 if action=='save' and method=='POST':
  crm.need(perms,'bridges','edit');rules=validate(direction,data.get('config'));prior,revision=config(c,direction)
  if data.get('revision')!=revision:raise ValueError('Bridge configuration changed; reload before saving')
  c.execute('INSERT OR REPLACE INTO crm_bridge_config VALUES(?,?,?)',(direction,crm.dump(rules),revision+1));crm.audit(c,actor,'bridge',None,'configure',{'direction':direction,'config':rules});return {'saved':True,'revision':revision+1}
 if action=='preview' and method=='GET':return preview(c,actor,perms,direction)
 if action=='run' and method=='POST':
  crm.need(perms,'bridges','reconcile');p=preview(c,actor,perms,direction)
  if data.get('token')!=p['token']:raise ValueError('Source data or rules changed; preview again')
  if p['exceptions'] and not p['config']['allowPartial']:raise ValueError('Resolve mapping exceptions or explicitly enable partial reconciliation in the saved rules')
  if not p['config']['enabled']:raise ValueError('Bridge is disabled')
  counts={'created':0,'updated':0,'exceptions':len(p['exceptions'])}
  for row in p['items']:
   entity,source_id=row['entity'],row['sourceId'];record=row['record'];record={**record,'_bridgeSource':direction,'_bridgeSourceId':source_id,'_bridgeAt':crm.now()}
   for placeholder,target,field in [('_organizationSource','Organizations','OrganizationID'),('_departmentSource','Departments','DepartmentID'),('_contactSource','Contacts','ContactId'),('_brandSource','InventoryBrands','BrandId')]:
    if record.get(placeholder) is not None:
     parent=c.execute('SELECT record_id FROM crm_links WHERE source=? AND source_id=? AND entity=?',(direction,record[placeholder],target)).fetchone()
     if not parent:raise ValueError('Required source mapping is missing for '+target)
     record[field]=parent[0]
    record.pop(placeholder,None)
   crm.validate_relations(c,entity,record) if entity in crm.SCHEMA else None
   existing=c.execute('SELECT record_id FROM crm_links WHERE source=? AND source_id=? AND entity=?',(direction,source_id,entity)).fetchone()
   if entity=='Organizations' and str(source_id) in p['config']['customerMap']:
    mapped=int(p['config']['customerMap'][str(source_id)])
    if not crm.raw(c,'Organizations',mapped):raise ValueError('Customer destination organization does not exist')
    if existing and existing[0]!=mapped:raise ValueError('This customer already has a different CRM mapping')
    if not existing:c.execute('INSERT INTO crm_links VALUES(?,?,?,?)',(direction,source_id,entity,mapped));existing=(mapped,)
   if entity=='Users':
    # Bound people remain editable CRM profiles; only the explicitly selected staff attributes are copied.
    id=record.pop('BoundCRMUserId');record.pop('_bridgeSource',None);record.pop('_bridgeSourceId',None);crm.update(c,entity,id,record);counts['updated']+=1
   elif existing:
    current=crm.raw(c,entity,existing[0])
    if not current:raise ValueError('Previously linked CRM record is missing')
    crm.update(c,entity,existing[0],record);id=existing[0];counts['updated']+=1
   else:
    result=crm.insert(c,entity,record);id=result['Id'];c.execute('INSERT INTO crm_links VALUES(?,?,?,?)',(direction,source_id,entity,id));counts['created']+=1
  c.execute('INSERT INTO crm_bridge_runs(direction,at,actor,digest,result) VALUES(?,?,?,?,?)',(direction,crm.now(),str(actor[0]),p['token'],crm.dump(counts)));crm.audit(c,actor,'bridge',None,'reconcile',{'direction':direction,**counts});return {'summary':counts}
 raise ValueError('Unsupported CRM bridge action')
