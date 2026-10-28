"""Count approval and invoice referral workflows for engineer custody."""
import json,uuid,datetime,math
from collections import defaultdict
import permissions_policy as policy
import service_inventory as si

def billing_reader(perms):return 'is.invoice.view' in perms and bool({'is.invoice.create','is.invoice.edit'} & set(perms))
def load_job(c,ident,perms,actor):
 policy.need(perms,'service.view');policy.need(perms,'service.jobs.view')
 row=c.execute("select payload,version from fse_records where id=? and kind='jobs'",(ident,)).fetchone()
 if not row:raise ValueError('Service job not found')
 job=dict(json.loads(row[0]),version=row[1]);alloc=c.execute('select payload from service_inventory_allocations where job_id=?',(ident,)).fetchone();alloc=json.loads(alloc[0]) if alloc else []
 if 'is.service-inventory.approve' not in perms and not billing_reader(perms) and (not alloc or any(str(x['engineer'])!=str(actor[4]) for x in alloc)):raise policy.PermissionDenied('This job uses another engineer’s custody')
 return job,alloc

def invoice_for(c,job_id,data=None):
 row=c.execute('select invoice_id from service_inventory_billing where job_id=?',(job_id,)).fetchone()
 return next((d for d in (data or si.warehouse_state(c)).get('documents',[]) if row and d['id']==row[0] and d.get('status')!='Cancelled'),None)
def read(c,actor,perms):
 pid=str(actor[4]);manager='is.service-inventory.approve' in perms;data=si.warehouse_state(c);customers={str(x['id']):x for x in data.get('customers',[])};instruments={i:json.loads(p) for i,p in c.execute("select id,payload from fse_records where kind='instruments'")};jobs=[]
 if 'service.jobs.view' in perms and 'service.view' in perms:
  visible_refs={r['reference'] for r in si.entries(c) if manager or billing_reader(perms) or r['engineer']==pid}
  for ident,payload in c.execute("select id,payload from fse_records where kind='jobs'"):
   if ident not in visible_refs:continue
   j=json.loads(payload);i=instruments.get(j.get('instrumentId'),{});customer_id=j.get('customerId') or i.get('customerId');invoice=invoice_for(c,ident,data);customer_id=customer_id or (invoice.get('party') if invoice else None);customer=customers.get(str(customer_id),{})
   jobs.append({'id':ident,'jobNo':j.get('jobNo') or ident,'customerId':customer_id,'customer':customer.get('name') or j.get('customer') or i.get('customer') or 'Customer not linked','serial':i.get('serial',''),'brand':i.get('brand',''),'model':i.get('model',''),'location':j.get('location') or i.get('location',''),'jobType':j.get('jobType',''),'date':j.get('date',''),'status':j.get('status',''),'engineer':j.get('engineer',''),'engineerName':j.get('engineerName',''),'description':j.get('description',''),'diagnosis':j.get('diagnosis',''),'actionTaken':j.get('actionTaken',''),'result':j.get('result',''),'currency':j.get('currency') or 'THB','billingStatus':'Invoiced' if invoice else 'Open','invoiceId':invoice['id'] if invoice else None,'invoiceNo':invoice.get('ref') if invoice else None,'invoiceStatus':invoice.get('status') if invoice else None})
 checks=[dict(json.loads(p),version=v) for p,v in c.execute('select payload,version from service_inventory_checks order by rowid desc')]
 return {'checks':[r for r in checks if manager or r['engineer']==pid],'jobDetails':jobs,'invoiceCustomers':[{'id':x['id'],'name':x.get('name') or x['id']} for x in data.get('customers',[])] if 'is.master-customers.view' in perms else [],'draftInvoices':[{'id':d['id'],'ref':d.get('ref'),'party':d.get('party'),'currency':d.get('currency') or 'THB'} for d in data.get('documents',[]) if d.get('kind')=='invoice' and d.get('status')=='Draft'] if 'is.invoice.view' in perms else []}

def dispatch(c,actor,perms,body):
 pid=str(actor[4]);manager='is.service-inventory.approve' in perms;action=body['action']
 if action=='stock-check':
  si.need(perms,'request');engineer=str(body.get('engineer') or pid)
  if engineer!=pid and not manager:raise policy.PermissionDenied('Count your own custody only')
  if engineer not in {str(e['id']) for e in si.active_engineers(c)}:raise ValueError('Select an active stock holder')
  lines=body.get('lines');catalogue={json.loads(p).get('productId') for p, in c.execute("select payload from fse_records where kind='parts'")}
  if not isinstance(lines,list) or not 1<=len(lines)<=100:raise ValueError('Add 1–100 count lines')
  clean=[];seen=set();balances=si.balances(c)
  for line in lines:
   product=line.get('productId');lot=str(line.get('lot') or '').strip();expiry=line.get('expiry') or '';key=(product,lot,expiry)
   if product not in catalogue or not lot or key in seen:raise ValueError('Select a declared part and unique lot/expiry per count')
   if expiry:datetime.date.fromisoformat(expiry)
   seen.add(key);counted=float(line.get('counted',-1));book=sum(r['qty'] for r in balances if (r['engineer'],r['productId'],r['lot'],r['expiry'])==(engineer,product,lot,expiry))
   if not math.isfinite(counted) or counted<0 or counted>1e9:raise ValueError('Counted quantity must be a finite nonnegative value')
   if abs(float(line.get('book',-1))-book)>1e-8:raise ValueError('Stock changed since the count form loaded; refresh and recount')
   reason=str(line.get('reason') or '').strip()
   if abs(counted-book)>1e-8 and not reason:raise ValueError('Justify every stock discrepancy')
   if len(reason)>4000:raise ValueError('Justification is too long')
   clean.append({'productId':product,'lot':lot,'expiry':expiry,'book':book,'counted':counted,'delta':counted-book,'reason':reason})
  ident=str(uuid.uuid4());import document_numbers
  ref=document_numbers.allocate(c,'service-count',ident,'SIC',year_digits=2);different=any(abs(x['delta'])>1e-8 for x in clean);r={'id':ident,'ref':ref,'engineer':engineer,'requester':pid,'createdAt':si.now(),'status':'Pending' if different else 'Completed','lines':clean,'history':[{'at':si.now(),'by':pid,'action':'Submitted' if different else 'Count matched'}]}
  c.execute('insert into service_inventory_checks values(?,?,1)',(ident,json.dumps(r)));return {'id':ident}
 if action.startswith('stock-check-'):
  decision=action[len('stock-check-'):];row=c.execute('select payload,version from service_inventory_checks where id=?',(body.get('id'),)).fetchone()
  if not row or row[1]!=body.get('version'):raise ValueError('Count changed; refresh before deciding')
  r=json.loads(row[0])
  if r['status']!='Pending':raise ValueError('Count has already been decided')
  if decision=='cancel':
   if pid!=r['requester'] and not manager:raise policy.PermissionDenied('Only requester or approver may cancel')
  elif decision in ['approve','reject']:
   si.need(perms,'approve')
   if pid in [r['engineer'],r['requester']]:raise policy.PermissionDenied('A different approver must decide this count')
  else:raise ValueError('Unknown count decision')
  reason=str(body.get('reason') or '').strip()
  if decision=='reject' and not reason:raise ValueError('A rejection reason is required')
  if decision=='approve':
   balance=si.balances(c)
   for l in r['lines']:
    current=sum(x['qty'] for x in balance if (x['engineer'],x['productId'],x['lot'],x['expiry'])==(r['engineer'],l['productId'],l['lot'],l['expiry']))
    if abs(current-l['book'])>1e-8:raise ValueError('Stock moved after counting. Cancel this check and recount before approval.')
   for l in r['lines']:
    if abs(l['delta'])>1e-8:si.post(c,actor,r['engineer'],l['productId'],l['lot'],l['expiry'],l['delta'],'Approved stock adjustment',r['ref'])
  r['status']={'approve':'Approved','reject':'Rejected','cancel':'Cancelled'}[decision];r['history'].append({'at':si.now(),'by':pid,'action':r['status'],'reason':reason});c.execute('update service_inventory_checks set payload=?,version=version+1 where id=?',(json.dumps(r),r['id']));return {'id':r['id']}
 if action=='add-to-invoice':
  policy.need(perms,'is.invoice.view');job,alloc=load_job(c,body.get('jobId'),perms,actor);data=si.warehouse_state(c)
  if invoice_for(c,job['id'],data):raise ValueError('This service job is already included in an invoice')
  if not alloc:raise ValueError('No currently allocated service parts to invoice')
  customer_id=body.get('customerId');inst=c.execute('select payload from fse_records where id=?',(job.get('instrumentId'),)).fetchone();inst=json.loads(inst[0]) if inst else {};bound=job.get('customerId') or inst.get('customerId')
  if bound and customer_id and customer_id!=bound:raise ValueError('Invoice customer must match the service job')
  customer_id=bound or customer_id
  if not any(x['id']==customer_id for x in data.get('customers',[])):raise ValueError('Link an existing Biomed IS customer before invoicing')
  currency=job.get('currency') or 'THB';invoice_id=body.get('invoiceId');invoice=next((d for d in data.get('documents',[]) if d['id']==invoice_id),None)
  if invoice_id:
   policy.need(perms,'is.invoice.edit')
   if not invoice or invoice.get('kind')!='invoice' or invoice.get('status')!='Draft' or invoice.get('party')!=customer_id or (invoice.get('currency') or 'THB')!=currency:raise ValueError('Select a Draft invoice for the same customer and currency')
  else:
   policy.need(perms,'is.invoice.create');invoice_id=str(uuid.uuid4());import document_numbers
   invoice={'id':invoice_id,'kind':'invoice','ref':document_numbers.allocate(c,'is',invoice_id,'IV',year_digits=2),'date':document_numbers.bangkok_day().isoformat(),'party':customer_id,'currency':currency,'status':'Draft','owner':pid,'created':si.now(),'lines':[],'history':[],'notes':'Service Inventory parts · draft pending normal invoice approval'};data.setdefault('documents',[]).append(invoice)
  totals=defaultdict(float)
  for l in alloc:totals[l['productId']]+=l['qty']
  products={p['id']:p for p in data.get('products',[])}
  for product,qty in totals.items():
   p=products.get(product,{})
   if not p:raise ValueError('Service product is missing from Biomed IS')
   price=float(p.get('price') or 0)
   if not math.isfinite(price) or price<0:raise ValueError('Invalid selling price in product master')
   invoice['lines'].append({'productId':product,'qty':qty,'price':price,'vat':float(p.get('vat') or 0),'description':p.get('name',''),'serviceJobId':job['id'],'serviceJobNo':job.get('jobNo'),'serviceInventoryBilled':True})
  invoice.setdefault('history',[]).append({'at':si.now(),'by':pid,'status':'Draft','reason':'Added parts from '+str(job.get('jobNo'))});c.execute('insert or replace into service_inventory_billing values(?,?,?)',(job['id'],invoice_id,si.now()));job.pop('version',None);job['invoiceId']=invoice_id;c.execute('update fse_records set payload=?,version=version+1 where id=?',(json.dumps(job,ensure_ascii=False),job['id']));c.execute('update workspace set value=?,revision=revision+1 where key=?',(json.dumps(data,ensure_ascii=False),si.KEY));import serve
  serve.project(c,json.dumps(data));audit(c,pid,'add-to-invoice',{'jobId':job['id'],'invoiceId':invoice_id});return {'invoiceId':invoice_id,'invoiceNo':invoice['ref']}
 if action=='unlink-invoice':
  policy.need(perms,'is.invoice.edit');job,alloc=load_job(c,body.get('jobId'),perms,actor);data=si.warehouse_state(c);invoice=invoice_for(c,job['id'],data)
  if not invoice or invoice.get('status')!='Draft':raise ValueError('Only Draft invoice referrals can be removed')
  invoice['lines']=[l for l in invoice['lines'] if l.get('serviceJobId')!=job['id']];invoice.setdefault('history',[]).append({'at':si.now(),'by':pid,'status':'Draft','reason':'Removed service job '+str(job.get('jobNo'))});c.execute('delete from service_inventory_billing where job_id=?',(job['id'],));job.pop('version',None);job.pop('invoiceId',None);c.execute('update fse_records set payload=?,version=version+1 where id=?',(json.dumps(job,ensure_ascii=False),job['id']));c.execute('update workspace set value=?,revision=revision+1 where key=?',(json.dumps(data),si.KEY));import serve
  serve.project(c,json.dumps(data));audit(c,pid,'unlink-invoice',{'jobId':job['id'],'invoiceId':invoice['id']});return {'jobId':job['id']}
 raise ValueError('Unknown Service Inventory workflow')
def audit(c,pid,action,data):c.execute('insert into service_inventory_workflow_audit(at,actor,action,payload) values(?,?,?,?)',(si.now(),pid,action,json.dumps(data)))
def protect_usage(c,r,previous,desired):
 invoice=invoice_for(c,r['id'])
 if not invoice:return
 old=defaultdict(float)
 for p in previous:old[p['productId']]+=p['qty']
 if dict(old)!=desired or any(p['engineer']!=(r.get('inventoryEngineer') or r.get('engineer')) for p in previous):raise ValueError('Parts are linked to invoice '+str(invoice.get('ref'))+'. Remove the job from its Draft invoice, or cancel that invoice through the normal workflow before changing usage.')
def protect_invoices(old,new):
 def refs(data):return sorted((str(d['id']),str(l.get('serviceJobId')),str(l.get('productId')),float(l.get('qty') or 0)) for d in data.get('documents',[]) if d.get('kind')=='invoice' for l in d.get('lines',[]) if l.get('serviceInventoryBilled'))
 if refs(old)!=refs(new):raise policy.PermissionDenied('Use Service Inventory to add or remove linked service parts on invoices')
