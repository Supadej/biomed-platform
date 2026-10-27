"""Bounded read-only summaries. Never expose credentials, attachments or HR details."""
import json
import permissions_policy as policy
import copilot_functions
PORTAL_MAP={'helpdesk':['tickets'],'incentives':['incentiveSchemes','incentiveClaims'],'training':['training','trainerRequests'],'sales':['salesTargets','salesActuals'],'cars':['requests'],'rooms':['requests'],'hierarchy':['departments'],'integration_is':['integrationIS'],'integration_crm':[]}
SHARED={'announcements','forms','resources','content','brands'}
SAFE=('id','title','name','ref','date','start','end','status','category','type')
def rows(value):
 return value if isinstance(value,list) else list(value.values()) if isinstance(value,dict) else []
def summary(records,details=False):
 records=[r for r in records if isinstance(r,dict)]
 result={'record_count':len(records),'status_counts':{}}
 for r in records:
  s=str(r.get('status','Unspecified'))[:60]
  if s not in result['status_counts'] and len(result['status_counts'])>=20:s='Other'
  result['status_counts'][s]=result['status_counts'].get(s,0)+1
 if details:result['sample_records']=[{k:str(r[k])[:180] for k in SAFE if k in r and isinstance(r[k],(str,int,float))} for r in records[:12]]
 return result
def augment(c,actor,perms,module,functions):
 key={'portal':'biomed_portal_v33_clean','is':'biomed_is_v50_transactions','budget':'biomed_budget_v60_years'}.get(module)
 if not key:return {}
 row=c.execute('SELECT value FROM workspace WHERE key=?',(key,)).fetchone()
 if not row:return {}
 # Export rights must not remove financial masks or function restrictions.
 perms=set(perms)-{'is.backup.export','budget.settings.backup'}
 for item in copilot_functions.catalog():
  if item['system']==module and functions is not None and not functions.get(item['id'],False):perms.discard(item['permission'])
 data=json.loads(policy.read_filter(perms,key,row[0]));out={}
 for item in copilot_functions.catalog():
  if item['system']!=module or not copilot_functions.permitted(item,perms):continue
  if functions is not None and not functions.get(item['id'],False):continue
  ident=item['id'];name=ident.split('.',1)[1]
  if module=='portal':
   if ident.startswith('crm.') or name=='calendar':continue
   fields=PORTAL_MAP.get(name,[name]);records=[]
   for field in fields:records+=rows(data.get(field,[]))
   if name in ('cars','rooms'):records=[r for r in records if isinstance(r,dict) and r.get('type')==('car' if name=='cars' else 'room')]
   if name in SHARED:
    records=[r for r in records if isinstance(r,dict) and (not r.get('sharedWith') or actor[4] in r.get('sharedWith',[]) or 'all' in r.get('sharedWith',[]) or r.get('owner')==actor[4])]
   if name not in SHARED:
    records=[r for r in records if isinstance(r,dict) and any(str(r.get(k,''))==str(actor[4]) for k in ('owner','userId','employeeId','ownerId','assignedTo'))]
   out[ident]={**summary(records,functions is not None and (name in SHARED or name in ('tasks','requests','objectives','visits','demos','pipeline','tenders','helpdesk'))),'scope':'shared permitted catalogue' if name in SHARED else 'explicitly owned records only; private details omitted'}
  elif module=='is':
   field={'master-customers':'customers','master-suppliers':'suppliers','master-products':'products','master-warehouses':'warehouses','cycle-count':'stockChecks','warehouse-move':'warehouseMoves','lot-control':'quarantines','kits':'kits','history':'audit','rules':'rules','legacy-map':'legacyMap'}.get(name)
   records=rows(data.get(field,[])) if field else [d for d in data.get('documents',[]) if d.get('kind')==name]
   if name in ('stocks','stock-inventory','expiry'):records=data.get('lots',[])
   if name in ('dashboard','reports','trace','reconcile'):records=data.get('documents',[])
   if name=='approval':records=[d for d in data.get('documents',[]) if d.get('status')=='Pending']
   if name=='outstanding':records=[d for d in data.get('documents',[]) if d.get('kind') in ('invoice','credit-note','debit-note','payment-receipt')]
   out[ident]={**summary(records,True),'scope':'existing view permissions; no attachments or contact details'}
  else:
   years=[]
   for year,y in list(data.get('years',{}).items())[-10:]:
    field={'ledger':'ledger','workforce':'workforce','approvals':'approvals','settings':'versions','manage_products':'products','manage_items':'expenses','masters':'costCenters'}.get(name)
    records=rows(y.get(field,[])) if field else y.get('products',[])+y.get('expenses',[])
    years.append({'year':year,**summary(records,False)})
   out[ident]={'years':years,'scope':'existing financial masks; counts only; permitted monetary totals appear separately'}
 return out
