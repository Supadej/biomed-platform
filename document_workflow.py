"""Approval labels and distinct, permission-controlled operational progress."""
import json,datetime,uuid
import permissions_policy as policy
KEY='biomed_is_v50_transactions'
POSTED={'Approved','Confirmed','Received','Completed','Shipped','Paid','Generated'}
LABEL={'Pending':'Pending approval','Rejected':'Returned for correction','Generated':'Approved','Waiting':'Draft','Confirmed':'Approved','Received':'Approved','Completed':'Approved','Shipped':'Approved','Paid':'Approved'}
MANUAL={'quotation':['Not sent','Sent','Accepted','Lost','Expired'],'shipment':['Ready to ship','Shipped','Delivered']}
TARGET={'customer-order':('check-out','fulfilled'),'sales-order':('check-out','fulfilled'),'withdrawal':('check-out','issued'),'purchase-order':('check-in','received'),'delivery-in':('check-in','checked in'),'delivery-out':('check-out','checked out'),'purchase-request':('purchase-order','ordered'),'waiting-purchase':('purchase-request','requisitioned')}
def linked(d,parent):return d.get('sourceId')==parent or parent in d.get('sourceIds',[])
def descendants(d,docs):
 ids={d['id']};result=[]
 while True:
  found=[x for x in docs if x['id'] not in ids and any(linked(x,i) for i in ids)]
  if not found:return result
  result+=found;ids.update(x['id'] for x in found)
def amount(d):
 return float(d.get('financials',{}).get('grand',sum(float(l.get('qty',0))*float(l.get('price',0)) for l in d.get('lines',[]))))
def progress(d,docs):
 status=d.get('status');kind=d.get('kind');approved=status in POSTED
 if status in ['Cancelled','Voided']:return status
 if not approved:return 'Not posted'
 if kind=='quotation' and d.get('portalCRM',{}).get('outcome'):
  outcome=d['portalCRM']['outcome'];return 'Expired' if outcome=='Lost' and d.get('operationalProgress')=='Expired' else {'Won':'Accepted','Lost':'Lost','Follow-up':'Sent','Monitoring':'Not sent'}.get(outcome,d.get('operationalProgress','Not sent'))
 if kind in MANUAL:return d.get('operationalProgress') or ('Shipped' if status=='Shipped' else MANUAL[kind][0])
 trail=[x for x in descendants(d,docs) if x.get('status') in POSTED]
 if kind=='invoice':
  receipts=[x for x in trail if x['kind']=='payment-receipt' and x.get('currency','THB')==d.get('currency','THB')];credits=[x for x in trail if x['kind']=='credit-note' and x.get('currency','THB')==d.get('currency','THB')]
  due=max(0,amount(d)-sum(amount(x) for x in credits));paid=sum(amount(x) for x in receipts)
  if due<=.005 and credits and amount(d)>0:return 'Settled by credit'
  return 'Paid' if paid>=due-.005 else 'Partially paid' if paid>0 else 'Unpaid'
 if kind in ['customer-order','sales-order'] and d.get('lines') and all(l.get('borrowMode')=='settlement' for l in d['lines']):return 'Borrowing settlement recorded'
 if kind in TARGET:
  target,verb=TARGET[kind];source={};done={}
  for l in d.get('lines',[]):source[l.get('productId')]=source.get(l.get('productId'),0)+float(l.get('qty',0))
  for x in trail:
   if x['kind']!=target:continue
   # Combined PR allocations belong to specific request lines, not every source request.
   lines=[{'productId':a['productId'],'qty':a['qty']} for a in x.get('sourceAllocations',[]) if a.get('requestId')==d['id']] if x.get('sourceAllocations') else x.get('lines',[])
   for l in lines:done[l.get('productId')]=done.get(l.get('productId'),0)+float(l.get('qty',0))
  if source and all(done.get(k,0)>=v-.00001 for k,v in source.items()):return 'Fully '+verb
  return 'Partially '+verb if any(done.values()) else 'Not '+verb
 if kind=='borrowing':
  import borrowing
  try:rows=[v for (ident,index),v in borrowing.ledger({'documents':docs}).items() if ident==d['id']]
  except ValueError:return 'Review borrowing links'
  issued=sum(r['issued'] for r in rows);cleared=sum(r['purchased']+r['returned'] for r in rows)
  if not issued:return 'Not issued'
  if cleared>=issued-.00001:return 'Closed'
  due=d.get('due','')
  if due and due[:10]<datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).date().isoformat():return 'Overdue'
  return 'Partial' if cleared>0 else 'Open'
 if kind=='return-product':return 'Return authorized; awaiting receiving'
 if kind=='supplier-confirm':return 'Confirmation recorded'
 if kind=='credit-note':return 'Credit posted'
 return 'Posted'
def projection(d,docs):
 p=progress(d,docs);overdue=d.get('kind')=='invoice' and p not in ['Paid','Settled by credit','Not posted','Cancelled','Voided'] and bool(d.get('paymentDue') or d.get('due')) and str(d.get('paymentDue') or d.get('due'))[:10]<datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).date().isoformat()
 return {'origin':'Automatic' if d.get('kind')=='shipment' and d.get('sourceId') else 'Manual / linked','approval':LABEL.get(d.get('status'),d.get('status','Draft')),'progress':p,'overdue':overdue,'options':MANUAL.get(d.get('kind'),[]) if d.get('status') in POSTED else [],'revision':len(d.get('history',[]))}
def guard(old,new):
 previous={x['id']:x for x in old.get('documents',[])}
 documents={x['id']:x for x in new.get('documents',[])};prior_moves={x.get('id') for x in old.get('movements',[])}
 for move in new.get('movements',[]):
  if move.get('id') is not None and move.get('id') in prior_moves:continue
  source=documents.get(move.get('sourceId'),{})
  if source.get('kind')=='return-product':raise ValueError('Product Return authorizes the return. Receive stock through Delivery In and Check In.')
  if source.get('kind')=='check-in':
   seen=set();parent=source
   while parent and parent.get('id') not in seen:
    seen.add(parent.get('id'))
    if parent.get('kind')=='return-product' and any(m.get('sourceId')==parent['id'] for m in old.get('movements',[])):raise ValueError('This legacy Product Return already posted stock. Review its ledger before receiving it again.')
    parent=documents.get(parent.get('sourceId'))
 for d in new.get('documents',[]):
  p=previous.get(d['id'],{})
  if p.get('status')=='Voided' and p!=d:raise policy.PermissionDenied('Voided documents are locked')
  if d.get('status')=='Voided' and p.get('status')!='Voided':raise policy.PermissionDenied('Use the controlled Void / Reverse action')
  if any(d.get(k)!=p.get(k) for k in ['operationalProgress','workflowHistory','voidReason','voidedAt']):raise policy.PermissionDenied('Use document workflow actions to change progress')
def mutate(c,actor,perms,body):
 policy.need(perms,'is_view');row=c.execute('SELECT value,revision FROM workspace WHERE key=?',(KEY,)).fetchone();data=json.loads(row[0]);docs=data.get('documents',[]);d=next((x for x in docs if x['id']==body.get('id')),None)
 if not d:raise ValueError('Document unavailable')
 kind=d['kind'];policy.need(perms,'is.'+kind+'.view')
 if body.get('revision')!=len(d.get('history',[])):raise ValueError('Document changed; refresh before continuing')
 if d.get('status') not in POSTED:raise ValueError('Only approved documents can use this action')
 now=datetime.datetime.now(datetime.timezone.utc).isoformat();reason=str(body.get('reason','')).strip();action=body.get('action')
 if action=='progress':
  policy.need(perms,'is.'+kind+'.progress');value=body.get('value');options=MANUAL.get(kind,[])
  if value not in options:raise ValueError('Progress is calculated from linked documents for this document type')
  old=progress(d,docs)
  if kind=='shipment' and options.index(value)<options.index(old):raise ValueError('Shipment progress cannot move backwards')
  if value==old:return {'saved':True}
  if kind=='quotation' and value=='Lost' and not reason:raise ValueError('Enter the reason the quotation was lost')
  d['operationalProgress']=value
  if kind=='quotation':d['portalCRM']={**d.get('portalCRM',{}),'outcome':{'Not sent':'Monitoring','Sent':'Follow-up','Accepted':'Won','Lost':'Lost','Expired':'Lost'}[value],'reason':reason or ('Quotation expired' if value=='Expired' else 'Customer accepted' if value=='Accepted' else ''),'updatedBy':actor[4],'updatedAt':now}
 elif action=='void':
  policy.need(perms,'is.'+kind+'.reverse')
  if len(reason)<3:raise ValueError('Enter a meaningful reason for voiding / reversing')
  if any(x.get('status') not in ['Cancelled','Voided'] for x in descendants(d,docs)):raise ValueError('Cancel or reverse downstream documents first')
  if any(x.get('status') in POSTED and any(isinstance(l.get('borrowRef'),dict) and l['borrowRef'].get('id')==d['id'] for l in x.get('lines',[])) for x in docs):raise ValueError('Clear linked borrowing settlements and returns before reversal')
  if any(l.get('borrowRef') for l in d.get('lines',[])):raise ValueError('Borrowing-linked postings require borrowing settlement review before reversal')
  if kind=='shipment' and progress(d,docs) in ['Shipped','Delivered']:raise ValueError('Shipped or delivered goods require a Product Return and receiving workflow, not a dispatch reversal')
  moves=[m for m in data.get('movements',[]) if m.get('sourceId')==d['id']]
  balances={}
  for m in data.get('movements',[]):
   key=(m.get('productId'),m.get('warehouse'),m.get('lot'));balances[key]=balances.get(key,0)+float(m.get('change',0))
  reversal={}
  for m in moves:
   key=(m.get('productId'),m.get('warehouse'),m.get('lot'));reversal[key]=reversal.get(key,0)-float(m.get('change',0))
  if any(balances.get(k,0)+v<-.00001 for k,v in reversal.items()):raise ValueError('Reversal would make stock negative; resolve dependent stock transactions first')
  for m in moves:data['movements'].append({**m,'id':str(uuid.uuid4()),'at':now,'change':-float(m.get('change',0)),'reversalOf':m.get('id'),'reason':reason})
  if c.execute('SELECT 1 FROM service_inventory_billing WHERE invoice_id=?',(d['id'],)).fetchone():raise ValueError('Service inventory billing is linked; review and unlink the billing workflow before reversal')
  d.update(status='Voided',voidReason=reason,voidedAt=now)
 else:raise ValueError('Unknown workflow action')
 event={'status':d['status'],'action':action,'progress':d.get('operationalProgress'),'by':actor[4],'at':now,'reason':reason};d.setdefault('history',[]).append(event);d.setdefault('workflowHistory',[]).append(event)
 data.setdefault('audit',[]).insert(0,{'id':str(uuid.uuid4()),'at':now,'by':actor[4],'action':action,'reference':d.get('ref'),'detail':reason})
 import serve
 serve.project(c,json.dumps(data))
 c.execute('UPDATE workspace SET value=?,revision=revision+1 WHERE key=?',(json.dumps(data,ensure_ascii=False),KEY));return {'saved':True,'reconcileRequired':action=='void'}
def handle(h,method,connect,session,permissions,origin):
 actor=session(h)
 if not actor:return h.reply(401,{'error':'Sign in required'})
 if method=='POST' and not origin(h):return h.reply(403,{'error':'Invalid origin'})
 try:
  perms=permissions(actor);policy.need(perms,'is_view')
  with connect() as c:
   c.execute('BEGIN IMMEDIATE' if method=='POST' else 'BEGIN')
   if method=='POST':
    length=int(h.headers.get('Content-Length','0'))
    if not 0<length<10000:raise ValueError('Invalid request size')
    body=json.loads(h.rfile.read(length))
    if not isinstance(body,dict):raise ValueError('Invalid workflow request')
    result=mutate(c,actor,perms,body)
   else:
    row=c.execute('SELECT value FROM workspace WHERE key=?',(KEY,)).fetchone();data=json.loads(row[0]) if row else {};docs=data.get('documents',[]);result={d['id']:projection(d,docs) for d in docs if 'is.'+d['kind']+'.view' in perms}
  return h.reply(200,result)
 except policy.PermissionDenied as e:return h.reply(403,{'error':str(e)})
 except (ValueError,KeyError,TypeError) as e:return h.reply(400,{'error':str(e)})
