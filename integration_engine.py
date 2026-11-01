"""Deterministic projections and bridge-only ledger reconciliation."""
import copy,datetime,math,json
IS_DEFAULT={'quotations':True,'sales':True,'quotationStatuses':['Approved'],'amountBasis':'net','credits':True,'dateField':'date','staffField':'portalRep','staffMap':{},'productMap':{},'rates':{'THB':1}}
BUDGET_DEFAULT={'enabled':False,'expenses':True,'incentives':True,'requests':False,'commitments':True,'actuals':True,'dateBasis':'statusDate','expenseAmount':'claimTotal','rules':[]}
def number(v):
 try:n=float(v or 0)
 except (TypeError,ValueError):raise ValueError('Invalid financial amount')
 if not math.isfinite(n):raise ValueError('Invalid financial amount')
 return n
def day(v):
 try:return datetime.date.fromisoformat(str(v or '')[:10]).isoformat()
 except ValueError:return ''
def document_amount(d,basis):
 gross=sum(number(l.get('qty'))*number(l.get('price')) for l in d.get('lines',[]));f=d.get('financials') or {};sf=d.get('sourceFields') or {}
 if basis=='gross':return gross
 net=number(f['net']) if 'net' in f else gross-number(sf.get('txtdiscountSP'))-number(sf.get('txtdiscountC'))
 if basis=='grand':return number(f['grand']) if 'grand' in f else net+net*number(sf.get('txtvatC'))/100
 return net
def is_projection(source,portal,config):
 c={**IS_DEFAULT,**config};quotes=[];sales=[];issues=[];users={str(x['id']) for x in portal.get('users',[])};lines=set(portal.get('productLines',[]));docs=source.get('documents',[])
 for d in docs:
  kind=d.get('kind');isquote=kind=='quotation' and c['quotations'] and d.get('status') in c['quotationStatuses'];isinvoice=kind=='invoice' and c['sales'] and d.get('status')=='Approved'
  if not(isquote or isinvoice):continue
  ref=d.get('ref',d['id']);currency=d.get('currency') or 'THB';rate=c['rates'].get(currency)
  if rate is None:issues.append(ref+': currency rate not configured');continue
  rep=str(d.get(c['staffField']) or '');rep=str(c['staffMap'].get(rep,rep))
  if rep not in users:issues.append(ref+': employee mapping missing');continue
  date=day(d.get(c['dateField']))
  if not date:issues.append(ref+': valid date missing');continue
  grouped={};invalid=False
  for l in d.get('lines',[]):
   target=c['productMap'].get(str(l.get('productId'))) or d.get('portalLine')
   if target not in lines:invalid=True;break
   grouped[target]=grouped.get(target,0)+number(l.get('qty'))*number(l.get('price'))
  if invalid or not grouped:issues.append(ref+': product-line mapping missing');continue
  amount=document_amount(d,c['amountBasis']);gross=sum(grouped.values());credit_totals={k:0 for k in grouped}
  if isinvoice and c['credits']:
   for cr in docs:
    if cr.get('kind')!='credit-note' or cr.get('status')!='Approved' or cr.get('sourceId')!=d['id']:continue
    if (cr.get('currency') or 'THB')!=currency:invalid=True;break
    credit_amount=document_amount(cr,c['amountBasis']);cg={}
    for l in cr.get('lines',[]):
     target=c['productMap'].get(str(l.get('productId'))) or cr.get('portalLine') or d.get('portalLine')
     if target not in grouped:invalid=True;break
     cg[target]=cg.get(target,0)+number(l.get('qty'))*number(l.get('price'))
    cgross=sum(cg.values())
    if invalid or not cgross:invalid=True;break
    for k,v in cg.items():credit_totals[k]+=credit_amount*v/cgross
  if invalid:issues.append(ref+': linked credit-note mapping/currency needs review');continue
  if isquote:quotes.append({'id':str(d['id']),'ref':ref,'date':date,'sourceStatus':d['status'],'customer':next((x.get('name','') for x in source.get('customers',[]) if x['id']==d.get('party')),d.get('party','')),'owner':rep,'line':' / '.join(grouped),'value':round(amount*number(rate),2),'currency':'THB'})
  else:
   for line,value in grouped.items():sales.append({'id':'invoice:'+str(d['id'])+':'+line,'sourceId':d['id'],'reference':ref,'rep':rep,'line':line,'period':date[:7],'amount':round(max(0,amount*(value/gross if gross else 0)-credit_totals[line])*number(rate),2),'note':'Configured Biomed IS bridge'})
 return {'quotations':quotes,'salesActuals':sales,'exceptions':issues}
def status_day(record):
 for key in ['decidedAt','reviewedAt','approvedAt','updatedAt']:
  if day(record.get(key)):return day(record[key])
 for event in reversed(record.get('history',[])):
  if event.get('status') in ['Approved','Paid'] or any(v in str(event.get('action','')) for v in ['Approved','Paid']):
   if day(event.get('at') or event.get('date')):return day(event.get('at') or event.get('date'))
 return ''
def portal_sources(portal,config):
 c={**BUDGET_DEFAULT,**config};records=[];issues=[];users={x['id']:x for x in portal.get('users',[])}
 for module,field in [('expenses','expenses'),('incentives','incentiveClaims'),('requests','requests')]:
  if not c[module]:continue
  for r in portal.get(field,[]):
   if r.get('status')!='Approved':continue
   if module=='requests' and r.get('type') not in ['travel','budget']:continue
   key=module+':'+str(r['id']);owner=r.get('owner') or r.get('rep') or r.get('employee');department=users.get(owner,{}).get('department','');category=r.get('category','') if module=='expenses' else 'Incentives' if module=='incentives' else r.get('type','')
   paid=[p for p in portal.get('payments',[]) if p.get('sourceId')==r['id'] and p.get('sourceType')==('expense' if module=='expenses' else 'incentive') and p.get('status')=='Paid'] if module!='requests' else []
   if len(paid)>1:issues.append(key+': multiple paid records; review before import');continue
   payment=paid[0] if paid else None;kind='Actual' if payment else 'Commitment'
   if kind=='Actual' and not c['actuals'] or kind=='Commitment' and not c['commitments']:continue
   if payment and payment.get('owner')!=owner:issues.append(key+': payment owner mismatch');continue
   if module=='requests' and any(x.get('requestId')==r['id'] or x.get('sourceRequestId')==r['id'] for x in portal.get('expenses',[]) if x.get('status')=='Approved'):continue
   amount=number(payment.get('amount')) if payment and c['expenseAmount']=='paymentAmount' else number(r.get('amount'))
   date=status_day(payment) if payment and c['dateBasis']=='statusDate' else status_day(r) if c['dateBasis']=='statusDate' else day(r.get('date') or r.get('created') or r.get('submittedAt') or r.get('start'))
   if amount<0 or not date:issues.append(key+': amount/date needs review');continue
   records.append({'key':key,'module':module,'category':category,'department':department,'owner':owner,'date':date,'type':kind,'amount':round(amount,2),'reference':r.get('title') or r['id']})
 return records,issues
def budget_plan(portal,store,configs):
 postings=[];issues=[]
 for year,config in configs.items():
  c={**BUDGET_DEFAULT,**config}
  if not c['enabled']:continue
  y=store.get('years',{}).get(str(year))
  if not y:continue
  sources,warnings=portal_sources(portal,c);issues.extend('FY'+str(year)+' '+x for x in warnings)
  for r in sources:
   date=datetime.date.fromisoformat(r['date']);fy=date.year+(1 if date.month>=5 else 0)
   if str(fy)!=str(year):
    if not configs.get(str(fy),{}).get('enabled'):issues.append(r['key']+': posting date falls in FY'+str(fy)+'; enable and map that fiscal year')
    continue
   candidates=[rule for rule in c['rules'] if rule.get('module')==r['module'] and rule.get('category','') in ['',r['category']] and rule.get('department','') in ['',r['department']]]
   candidates.sort(key=lambda rule:bool(rule.get('category'))+bool(rule.get('department')),reverse=True)
   if not candidates or len(candidates)>1 and (bool(candidates[0].get('category'))+bool(candidates[0].get('department')))==(bool(candidates[1].get('category'))+bool(candidates[1].get('department'))):issues.append(r['key']+': missing or ambiguous expense mapping');continue
   target=next((x for x in y.get('expenses',[]) if x['id']==candidates[0].get('target') and x.get('active',True)),None)
   if not target or target.get('category')=='Other Cost of Sales':issues.append(r['key']+': active expense line required (Other COGS excluded)');continue
   postings.append({**r,'year':str(year),'line':target['id'],'label':target.get('name',''),'costCenter':target.get('costCenter',''),'month':(date.month-5)%12})
 counts={}
 for row in postings:counts[row['key']]=counts.get(row['key'],0)+1
 duplicates={key for key,count in counts.items() if count>1}
 for key in duplicates:issues.append(key+': source matches multiple fiscal-year rules; align the date basis before posting')
 postings=[row for row in postings if row['key'] not in duplicates]
 return {'postings':postings,'exceptions':list(dict.fromkeys(issues))}
def reconcile_budget(store,plan):
 out=copy.deepcopy(store)
 for year,y in out.get('years',{}).items():
  targets={r['id']:r for r in y.get('expenses',[])}
  for old in y.get('ledger',[]):
   if old.get('bridge')!='portal-budget':continue
   target=targets.get(old.get('line'));field='actual' if old['type']=='Actual' else 'commitment'
   if target is None:raise ValueError('Previous bridge target is missing; restore the expense line before reconciling')
   target.setdefault(field,[0]*12)[old['month']]=round(number(target.setdefault(field,[0]*12)[old['month']])-number(old['amount']),2)
  y['ledger']=[r for r in y.get('ledger',[]) if r.get('bridge')!='portal-budget']
 for p in plan['postings']:
  y=out['years'][p['year']];target=next(x for x in y['expenses'] if x['id']==p['line']);field='actual' if p['type']=='Actual' else 'commitment';target.setdefault(field,[0]*12)[p['month']]=round(number(target[field][p['month']])+p['amount'],2)
  y.setdefault('ledger',[]).append({'id':'portal:'+p['key']+':'+p['year'],'bridge':'portal-budget','portalSourceId':p['key'],'line':p['line'],'label':p['label'],'costCenter':p['costCenter'],'month':p['month'],'type':p['type'],'amount':p['amount'],'date':p['date'],'reference':p['reference'],'note':'Staff Portal reconciliation'})
 return out
