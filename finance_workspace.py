"""Finance planning registers; never posts a bank payment or replaces the general ledger."""
import json,uuid,datetime,math
from zoneinfo import ZoneInfo
import permissions_policy as policy
import budget_governance as bg
import integration_engine as engine
TASKS=['Bank reconciliation','Receivables and receipts reconciliation','Payables and supplier statement reconciliation','Revenue and expense cutoff','Inventory and service-parts reconciliation','Accruals and prepayments','Tax and withholding supporting schedules','Management variance review']
def today():return datetime.datetime.now(ZoneInfo('Asia/Bangkok')).date()
def day(v):return datetime.date.fromisoformat(str(v))
def amount(v):
 n=float(v)
 if not math.isfinite(n) or n<0 or n>1e15:raise ValueError('Enter a valid nonnegative amount')
 return n
def initialize(c):c.execute('CREATE TABLE IF NOT EXISTS finance_workspace(year TEXT PRIMARY KEY,payload TEXT NOT NULL,version INTEGER NOT NULL)')
def load(c,year):
 initialize(c);r=c.execute('select payload,version from finance_workspace where year=?',('company',)).fetchone()
 return (json.loads(r[0]),r[1]) if r else ({'manual':[],'settlements':[],'cash':[],'opening':{},'maps':{},'close':{},'history':[]},0)
def warehouse(c):
 row=c.execute("select value from workspace where key='biomed_is_v50_transactions'").fetchone();return json.loads(row[0]) if row else {}
def source_rows(c,f):
 w=warehouse(c);customers={str(x['id']):x.get('name',x['id']) for x in w.get('customers',[])};rows=[];exceptions=[]
 live=[d for d in w.get('documents',[]) if d.get('status') in ['Approved','Confirmed','Received','Paid']]
 for d in live:
  if d.get('kind')!='invoice':continue
  credit=sum(engine.document_amount(x,'grand') for x in live if x.get('kind')=='credit-note' and x.get('sourceId')==d['id'] and (x.get('currency') or 'THB')==(d.get('currency') or 'THB'))
  total=max(0,engine.document_amount(d,'grand')-credit);due=d.get('due') or d.get('dueDate') or d.get('paymentDue') or d.get('sourceFields',{}).get('txtduedate')
  try:due=day(str(due)[:10]).isoformat()
  except ValueError:due=str(d.get('date') or today().isoformat())[:10];exceptions.append(d.get('ref',d['id'])+': due date missing; document date used')
  rows.append({'id':'IS:'+d['id'],'type':'Receivable','reference':d.get('ref') or d['id'],'party':customers.get(str(d.get('party')),str(d.get('party') or 'Unassigned')),'currency':d.get('currency') or 'THB','date':d.get('date'),'due':due,'amount':total,'sourceId':d['id'],'origin':'Approved IS invoice, net of linked credits'})
 rows+= [r for r in f['manual'] if not r.get('void')]
 for r in rows:
  snapshot=f.get('expressBalances',{}).get(r['id']);asof=snapshot['asOf'] if snapshot else r.get('asOf')
  basepaid=max(0,r['amount']-snapshot['outstanding']) if snapshot else 0
  paid=basepaid+sum(s['amount'] for s in f['settlements'] if s['sourceId']==r['id'] and not s.get('void') and (not asof or s['date']>asof))
  if snapshot:r['origin']+=' · Express reconciled snapshot '+asof;r['expressAsOf']=asof
  r['settled']=paid;r['outstanding']=round(max(0,r['amount']-paid),2);r['daysOverdue']=max(0,(today()-day(r['due'])).days);r['bucket']='Current' if day(r['due'])>=today() else '1–30' if r['daysOverdue']<=30 else '31–60' if r['daysOverdue']<=60 else '61–90' if r['daysOverdue']<=90 else 'Over 90'
  if paid>r['amount']+.005:exceptions.append(r['reference']+': settlements exceed revised source amount; investigate credits or void incorrect settlements')
 live_ids={x['id'] for x in rows}
 for settlement in f['settlements']:
  if not settlement.get('void') and settlement['sourceId'] not in live_ids:exceptions.append(settlement['reference']+': source no longer live; reconcile cancellation/refund. Recorded cash remains in forecast history.')
 return rows,exceptions

def report(c,year,f):
 _,state=bg.workspace(c,year);g,_=bg.load(c,year);sources,exceptions=source_rows(c,json.loads(json.dumps(f)));w=warehouse(c);commitments=[]
 for l in (g.get('approved') or {}).get('lines',[]):
  if l['kind'] not in ['Expense','COGS']:continue
  rows=[r for r in state.get('expenses' if l['kind']=='Expense' else 'products',[]) if bg.identity(r,l['kind'])==[l['kind'],l['costCenter'],l['source']]]
  actual=sum(sum(r.get('actual' if l['kind']=='Expense' else 'cogsActual',[])) for r in rows);book=sum(sum(r.get('commitment',[])) for r in rows);key=json.dumps([l['kind'],l['costCenter'],l['source']],ensure_ascii=False);extra=0
  for d in w.get('documents',[]):
   mapping=f['maps'].get(d['id'],{})
   if d.get('kind')=='purchase-order' and d.get('status') in ['Approved','Confirmed','Received'] and mapping.get('key')==key and not mapping.get('included') and (d.get('currency') or 'THB')=='THB':
    total=engine.document_amount(d,'grand');billed=sum(x['amount'] for x in sources if x['type']=='Payable' and x.get('purchaseOrderId')==d['id']);extra+=max(0,total-billed)
  target=sum(l['target']);commitments.append({'key':key,'kind':l['kind'],'source':l['source'],'costCenter':l['costCenter'],'target':target,'actual':actual,'bookCommitment':book,'additionalPO':extra,'remaining':round(target-actual-book-extra,2)})
 pos=[{'id':d['id'],'reference':d.get('ref') or d['id'],'currency':d.get('currency') or 'THB','amount':engine.document_amount(d,'grand'),'mapping':f['maps'].get(d['id'])} for d in w.get('documents',[]) if d.get('kind')=='purchase-order' and d.get('status') in ['Approved','Confirmed','Received']]
 monday=today()-datetime.timedelta(days=today().weekday());currencies=sorted({'THB'}|{x['currency'] for x in sources+f['cash']}|set(f['opening']));forecast={}
 for currency in currencies:
  opening=f['opening'].get(currency,{});start=max(day(opening['date']),monday) if opening else monday;balance=opening.get('amount',0);weeks=[]
  for i in range(13):
   first=start+datetime.timedelta(days=i*7);last=first+datetime.timedelta(days=6);inc=out=0
   for r in sources:
    due=day(f['maps'].get(r['id'],{}).get('plannedDate') or r['due']);due=max(due,start)
    if r['currency']==currency and first<=due<=last:
     if r['type']=='Receivable':inc+=r['outstanding']
     else:out+=r['outstanding']
   for settlement in f['settlements']:
    if not settlement.get('void') and settlement['currency']==currency and first<=day(settlement['date'])<=last:
     source=next((x for x in sources if x['id']==settlement['sourceId']),None)
     typ=source['type'] if source else settlement.get('sourceType')
     if typ=='Receivable':inc+=settlement['amount']
     elif typ=='Payable':out+=settlement['amount']
   for r in f['cash']:
    if not r.get('void') and r['currency']==currency and first<=day(r['date'])<=last:
     if r['direction']=='Inflow':inc+=r['amount']
     else:out+=r['amount']
   weeks.append({'from':first.isoformat(),'to':last.isoformat(),'opening':round(balance,2),'inflow':round(inc,2),'outflow':round(out,2),'closing':round(balance+inc-out,2)});balance+=inc-out
  forecast[currency]={'openingVerified':bool(opening) and day(opening['date'])>=monday,'asOf':start.isoformat(),'weeks':weeks}
 return {'aging':sources,'exceptions':exceptions,'commitments':commitments,'purchaseOrders':pos,'forecast':forecast,'approvedBudget':bool(g.get('approved'))}

def handle(h,method,connect,session,permissions,origin):
 actor=session(h)
 if not actor:return h.reply(401,{'error':'Sign in required'})
 try:
  perms=permissions(actor)
  for permission in ['budget_view','budget.finance.view','is.invoice.view','is.purchase-order.view']:policy.need(perms,permission)
  from urllib.parse import parse_qs,urlsplit
  year=parse_qs(urlsplit(h.path).query).get('year',[''])[0]
  if not year.isdigit() or not 2000<=int(year)<=2200:raise ValueError('Select a fiscal year')
  with connect() as c:
   c.execute('BEGIN IMMEDIATE');f,version=load(c,year);_,state=bg.workspace(c,year)
   if not state:raise ValueError('Fiscal year not found')
   if any(not policy.budget_row_visible(perms,r,coll=='products') for coll in ['products','expenses'] for r in state.get(coll,[])):raise policy.PermissionDenied('Finance requires view access to every included budget schedule')
   if method=='POST':
    if not origin(h):return h.reply(403,{'error':'Invalid origin'})
    length=int(h.headers.get('Content-Length',0))
    if not 0<length<=500000:raise ValueError('Invalid request size')
    body=json.loads(h.rfile.read(length));action=body.get('action');policy.need(perms,'budget.finance.review' if action=='close-review' else 'budget.finance.edit')
    if body.get('version')!=version:return h.reply(409,{'error':'Finance records changed; refresh and retry'})
    ident=str(uuid.uuid4());at=bg.now();name=actor[2];base={'id':ident,'at':at,'by':str(actor[4]),'name':name}
    if action in ['manual','cash']:
     r=body.get('record',{});currency=r.get('currency')
     if currency not in ['THB','USD','EUR','CNY']:raise ValueError('Choose THB, USD, EUR or CNY')
     value=amount(r.get('amount'));reference=str(r.get('reference') or '').strip()
     if value<=0 or not reference:raise ValueError('Enter a positive amount and a unique document reference')
     records=f['manual'] if action=='manual' else f['cash']
     if any(x['reference'].casefold()==reference.casefold() and not x.get('void') for x in records):raise ValueError('Duplicate reference')
     if action=='manual':
      typ=r.get('type')
      if typ not in ['Receivable','Payable'] or not str(r.get('party') or '').strip():raise ValueError('Choose a type and enter customer or supplier')
      if typ=='Receivable' and any(x['reference'].casefold()==reference.casefold() for x in source_rows(c,json.loads(json.dumps(f)))[0]):raise ValueError('An existing receivable already uses this reference')
      due=day(r.get('due')).isoformat();date=day(r.get('date')).isoformat();po=r.get('purchaseOrderId') or None
      if po and not any(x['id']==po and x.get('kind')=='purchase-order' and (x.get('currency') or 'THB')==currency for x in warehouse(c).get('documents',[])):raise ValueError('Choose a purchase order in the same currency')
      records.append({**base,'type':typ,'reference':reference,'party':str(r['party'])[:200],'currency':currency,'amount':value,'date':date,'due':due,'purchaseOrderId':po,'origin':'Finance-entered obligation; reconcile to accounting'})
     else:
      if r.get('direction') not in ['Inflow','Outflow']:raise ValueError('Choose cash direction')
      records.append({**base,'reference':reference,'currency':currency,'amount':value,'date':day(r.get('date')).isoformat(),'direction':r['direction'],'note':str(r.get('note') or '')[:1000]})
    elif action=='settle':
     rows,_=source_rows(c,json.loads(json.dumps(f)));r=next(x for x in rows if x['id']==body.get('sourceId'));value=amount(body.get('amount'));date=day(body.get('date'));ref=str(body.get('reference') or '').strip()
     if (r.get('expressAsOf') or r.get('asOf')) and date.isoformat()<=(r.get('expressAsOf') or r.get('asOf')):raise ValueError('This date is already included in the Express outstanding snapshot; reconcile it in Express or record a later settlement')
     if value<=0 or value>r['outstanding']+.005 or date>today() or not ref:raise ValueError('Enter a bank/reference-backed settlement up to the outstanding amount, dated today or earlier')
     if body.get('verified') is not True:raise ValueError('Verify the receipt/payment against supporting records')
     if any(s['reference'].casefold()==ref.casefold() and not s.get('void') for s in f['settlements']):raise ValueError('Duplicate settlement reference')
     f['settlements'].append({**base,'sourceId':r['id'],'sourceType':r['type'],'reference':ref,'amount':value,'currency':r['currency'],'date':date.isoformat()})
    elif action=='opening':
     currency=body.get('currency')
     if currency not in ['THB','USD','EUR','CNY']:raise ValueError('Invalid currency')
     date=day(body.get('date'))
     if date>today():raise ValueError('Opening balance must be dated today or earlier')
     value=float(body.get('amount'))
     if not math.isfinite(value) or abs(value)>1e15:raise ValueError('Invalid opening cash amount')
     f['opening'][currency]={'date':date.isoformat(),'amount':value,'by':actor[4],'at':at}
    elif action=='mapping':
     key=body.get('key');r=next(x for x in report(c,year,f)['purchaseOrders'] if x['id']==body.get('id'))
     if key not in {l['key'] for l in report(c,year,f)['commitments']}:raise ValueError('Choose an approved budget source')
     if r['currency']!='THB':raise ValueError('Foreign-currency PO requires an approved FX conversion; it is shown separately')
     f['maps'][r['id']]={'key':key,'included':body.get('included') is True}
    elif action=='planned-date':
     rows,_=source_rows(c,json.loads(json.dumps(f)));r=next(x for x in rows if x['id']==body.get('id'));f['maps'].setdefault(r['id'],{})['plannedDate']=day(body.get('date')).isoformat()
    elif action=='void':
     reason=str(body.get('reason') or '').strip()
     if not reason:raise ValueError('A reason is required')
     r=next(x for x in f['manual']+f['cash']+f['settlements'] if x['id']==body.get('id'))
     if r.get('void'):raise ValueError('Record already voided')
     if r in f['manual'] and any(x['sourceId']==r['id'] and not x.get('void') for x in f['settlements']):raise ValueError('Void linked settlements first')
     r['void']={'at':at,'by':actor[4],'reason':reason}
    elif action in ['close-save','close-submit','close-review','close-reopen']:
     month=int(body.get('month',-1))
     if not 0<=month<12:raise ValueError('Choose a fiscal month')
     key=str(year)+':'+str(month);close=f['close'].setdefault(key,{'status':'Draft','tasks':[{'title':t,'owner':'','done':False,'evidence':''} for t in TASKS],'history':[]})
     if action=='close-save':
      if close['status'] not in ['Draft','Returned']:raise ValueError('Reopen or return the checklist before editing')
      tasks=body.get('tasks');users={r[0] for r in c.execute('select user_id from accounts')}
      if not isinstance(tasks,list) or len(tasks)!=len(TASKS):raise ValueError('Complete the standard checklist')
      for i,t in enumerate(tasks):
       if t.get('owner') not in users or type(t.get('done')) is not bool:raise ValueError('Assign an existing employee to every task')
       if t['done'] and not str(t.get('evidence') or '').strip():raise ValueError('Completed tasks require a supporting reference')
      close['tasks']=[{'title':TASKS[i],'owner':t['owner'],'done':t['done'],'evidence':str(t.get('evidence') or '')[:2000]} for i,t in enumerate(tasks)]
     elif action=='close-submit':
      if close['status'] not in ['Draft','Returned'] or not all(t['done'] for t in close['tasks']):raise ValueError('Save and complete all close tasks before submission')
      next_month=(int(year)-1)*12+4+month+1
      if today()<datetime.date(next_month//12,next_month%12+1,1):raise ValueError('The fiscal month has not ended')
      if close.get('snapshot'):close.setdefault('versions',[]).append({'snapshot':close['snapshot'],'tasks':json.loads(json.dumps(close['tasks'])),'budgetActualSnapshot':close.get('budgetActualSnapshot'),'at':at})
      close.update(status='Submitted',submittedBy=str(actor[4]),snapshot=report(c,year,f),budgetActualSnapshot=bg.actual_snapshot(state,month,month))
     elif action=='close-review':
      if close['status']!='Submitted' or close['submittedBy']==str(actor[4]):raise policy.PermissionDenied('Another authorized reviewer must decide the submitted close')
      if close.get('budgetActualSnapshot')!=bg.actual_snapshot(state,month,month) and body.get('approve'):raise ValueError('Actuals changed; return this checklist and recheck the supporting records')
      if not body.get('approve') and not str(body.get('reason') or '').strip():raise ValueError('A return reason is required')
      close['status']='Reviewed' if body.get('approve') else 'Returned'
     else:
      policy.need(perms,'budget.periods.unlock')
      if not str(body.get('reason') or '').strip():raise ValueError('A reopening reason is required')
      close['status']='Draft'
     close['history'].append({**base,'action':action,'reason':str(body.get('reason') or '')})
    else:raise ValueError('Unknown finance action')
    f['history'].append({**base,'action':action,'details':{k:v for k,v in body.items() if k not in ['version']}});c.execute('insert or replace into finance_workspace values(?,?,?)',('company',json.dumps(f,ensure_ascii=False),version+1));version+=1
   return h.reply(200,{'finance':f,'version':version,'report':report(c,year,f),'permissions':sorted(perms),'userId':str(actor[4]),'people':[{'id':r[0],'name':r[1]} for r in c.execute('select user_id,name from accounts')]})
 except policy.PermissionDenied as ex:return h.reply(403,{'error':str(ex)})
 except (ValueError,TypeError,KeyError,StopIteration) as ex:return h.reply(400,{'error':str(ex) or 'Record not found'})
