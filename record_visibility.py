"""Record visibility is an intersection with action permissions, never an action grant.
Context travels with each authenticated permission set; there is no process-global actor.
"""
import copy,json
PKEY='biomed_portal_v33_clean'
IKEY='biomed_is_v50_transactions'
SCOPES={'own':'Own records','assigned':'Own + assigned','team':'Reporting team','department':'Department','all':'All records'}
PORTAL={'tasks':'tasks','requests':'requests','expenses':'expenses','payments':'payments','objectives':'objectives','tickets':'helpdesk','salesTargets':'sales','salesActuals':'sales','incentiveSchemes':'incentives','incentiveClaims':'incentives','trainerRequests':'training','visits':'visits','tenders':'tenders','pipeline':'pipeline','demos':'demos','appraisals':'appraisals','onboarding':'onboarding','hrprofiles':'hrprofiles','leavebalance':'leavebalance'}
CRM={'Leads':'leads','Events':'events','Projects':'projects','ProjectActivity':'activities','HelpDeskTickets':'tickets','Targets':'targets','ExternalSnapshots':'finance'}
SHARED={'is.master-customers','is.master-suppliers','is.master-products','is.master-warehouses','is.kits','service.instruments','service.parts','service.contracts'}
def modules():
 import permissions_policy as policy
 result={}
 for r in policy.CATALOG['permissions']:
  m=r['module']
  if m in {'is.'+k for k in policy.CATALOG['transactions']}|{'is.shipment','is.waiting-purchase','is.cycle-count','is.warehouse-move'} or m.startswith('is.master-') or m in {'portal.'+v for v in PORTAL.values()} or m in {'crm.'+v for v in CRM.values()} or m in SHARED or m in {'service.jobs','service.movements','service.replacements','application_service','portal.minutes','is.service-inventory'}:
   result.setdefault(m,r['label'])
 return result
class Permissions(set):
 def __init__(self,values,actor,portal,documents=None,identities=None):
  super().__init__(values);self.actor=actor;self.portal=portal;self.documents=documents or [];self.identities=identities or {};self._team=None
 def copy(self):return Permissions(self,self.actor,self.portal,self.documents,self.identities)
def contextual(perms):return isinstance(perms,Permissions)
def subset(perms,values):
 out=perms.copy() if contextual(perms) else set(perms)
 out.intersection_update(values);return out
def admin(perms):return contextual(perms) and str(perms.actor[3]).strip().lower().replace('_',' ').replace('-',' ') in {'system admin','administrator'}
def default(role,module):
 role=role.casefold()
 if role in {'system admin','administrator','managing director','operations director'}:return 'all'
 if module in SHARED or module.startswith('is.master-') or module.startswith('crm.') and module not in {'crm.'+x for x in CRM.values()}:return 'all'
 if role=='business director':return 'department'
 # Central operations must process authorized transactions across sales teams.
 if module.startswith('is.') and any(s in role for s in ['accounting','inventory','warehouse','purchas','procurement','messenger','operation manager','bill collector']):return 'all'
 if module in {'portal.payments','portal.expenses','portal.incentives'} and 'accounting' in role:return 'all'
 if 'manager' in role or 'supervisor' in role or role=='department manager':return 'team'
 if module.startswith('service.') or module in {'application_service','portal.minutes'}:return 'assigned'
 return 'own'
def scope(perms,module):
 if not contextual(perms) or admin(perms):return 'all'
 value=perms.portal.get('roleRecordScopes',{}).get(perms.actor[3],{}).get(module)
 return value if value in SCOPES else default(perms.actor[3],module)
def team(perms):
 if perms._team is None:
  found={str(perms.actor[4])}
  while True:
   more={str(u['id']) for u in perms.portal.get('users',[]) if str(u.get('managerId','')) in found}
   if more<=found:break
   found|=more
  perms._team=found
 return perms._team
def values(record,keys):
 out=set()
 for k in keys:
  v=record.get(k)
  for x in v if isinstance(v,list) else [v]:
   if isinstance(x,(str,int)) and str(x):out.add(str(x))
 return out
def principals(perms,module,r):
 if module=='is.service-inventory':own=values(r,['owner','engineer','requester','actor'])
 elif module.startswith('is.') and (r.get('portalRep') or r.get('owner')):
  own={str(r.get('portalRep') or r.get('owner'))}
 elif module.startswith('crm.'):
  own=values(r,['MainUserId','MainUserID','CreatedByUserId','OwnerId','PortalRep','UserId'])
  own={str(perms.identities.get(x,x)) for x in own}
 else:own=values(r,['owner','ownerId','userId','employeeId','employee','rep','createdBy','specialist'])
 assigned=values(r,['assignedTo','assignedToId','assignedUsers','collaborators','engineer','specialist','approvalBy','assignee','UserIds','AssignedToUserId','sharedWith','employees','internalAttendees'])
 if module.startswith('crm.'):assigned={str(perms.identities.get(x,x)) for x in assigned}
 return own,assigned
def visible(perms,module,r,seen=None):
 if not contextual(perms):return True
 s=scope(perms,module)
 if s=='all':return True
 if not isinstance(r,dict):return False
 me=str(perms.actor[4]);own,assigned=principals(perms,module,r)
 # Legacy generated records inherit responsibility only from their source.
 if not own and not assigned and module.startswith('is.') and r.get('sourceId'):
  seen=set(seen or ())
  if str(r.get('id')) in seen:return False
  seen.add(str(r.get('id')))
  source=next((d for d in perms.documents if str(d.get('id'))==str(r['sourceId'])),None)
  if source:
   a,b=principals(perms,'is.'+source.get('kind',''),source)
   if not a and not b:return visible(perms,module,source,seen)
   own,assigned=a,b
 if me in own:return True
 if s=='own':return False
 if me in assigned:return True
 if s=='assigned':return False
 if s=='team':return bool((own|assigned)&team(perms))
 users={str(u['id']):u for u in perms.portal.get('users',[])};dept=users.get(me,{}).get('department')
 if not dept:return False
 return any(users.get(x,{}).get('department')==dept for x in own|assigned) or not own and not assigned and r.get('department')==dept

def need(perms,module,record):
 if not visible(perms,module,record):
  import permissions_policy as policy
  raise policy.PermissionDenied('Record is outside your configured visibility: '+module)
def is_visible(perms,d):
 return ('is.'+d.get('kind','')+'.view' in perms or 'is.outstanding.view' in perms and d.get('kind') in ['invoice','credit-note','debit-note','payment-receipt']) and visible(perms,'is.'+d.get('kind',''),d)
def document(perms,ident):
 return next((d for d in perms.documents if str(d.get('id'))==str(ident)),None) if contextual(perms) else None
def linked(perms,r):
 if not contextual(perms):return True
 for ident,snap in (r.get('SourceDocuments') or {}).items():
  d=document(perms,ident)
  if d and not is_visible(perms,d):return False
 for field in ['ISDocumentId','SourceDocumentId']:
  if r.get(field) and not is_visible(perms,document(perms,r[field]) or {}):return False
 return True

def filter_data(perms,key,data):
 if not contextual(perms):return data
 if key==IKEY:
  data['documents']=[d for d in data.get('documents',[]) if is_visible(perms,d)]
  for f,m in [('stockChecks','is.cycle-count'),('warehouseMoves','is.warehouse-move'),('customers','is.master-customers'),('suppliers','is.master-suppliers'),('products','is.master-products'),('warehouses','is.master-warehouses'),('kits','is.kits')]:
   data[f]=[r for r in data.get(f,[]) if (m+'.view' in perms or m in {'is.master-customers','is.master-products'} and 'service.references.view' in perms) and visible(perms,m,r)]
  shown={str(d['id']) for d in data['documents']}
  # Stock balances remain shared operational data; movements and audit retain scope.
  data['audit']=[r for r in data.get('audit',[]) if str(r.get('sourceId',r.get('documentId',r.get('docId','')))) in shown or str(r.get('by',r.get('actor','')))==str(perms.actor[4]) or admin(perms)]
  data['movements']=[r if admin(perms) or str(r.get('sourceId',r.get('docId',''))) in shown else stock_balance(r) for r in data.get('movements',[])]
 elif key==PKEY:
  for f,m in PORTAL.items():
   if isinstance(data.get(f),list):data[f]=[r for r in data[f] if module_view(perms,'portal.'+request_module(r,m)) and visible(perms,'portal.'+request_module(r,m),r)]
  allowed={str(d['id']) for d in perms.documents if is_visible(perms,d)}
  if 'isCRM' in data:data['isCRM']={i:r for i,r in data['isCRM'].items() if str(i) in allowed}
  bridge=data.get('integrationIS') or {}
  bridge['quotations']=[r for r in bridge.get('quotations',[]) if str(r.get('sourceId',r.get('id',''))) in allowed and visible(perms,'portal.tenders',r)]
  bridge['salesActuals']=[r for r in bridge.get('salesActuals',[]) if visible(perms,'portal.sales',r)]
  if not admin(perms) and scope(perms,'portal.sales')!='all':bridge['exceptions']=[]
  if 'integrationIS' in data:data['integrationIS']=bridge
 return data

def request_module(r,m):return ('cars' if r.get('type')=='car' else 'rooms' if r.get('type')=='room' else 'requests') if m=='requests' else m

def guard_and_merge(perms,key,old,new):
 """Reject forged hidden writes; retain omitted hidden rows before normal validation."""
 if not contextual(perms):return new
 import permissions_policy as policy
 fields=({'documents':None,'stockChecks':'is.cycle-count','warehouseMoves':'is.warehouse-move','customers':'is.master-customers','suppliers':'is.master-suppliers','products':'is.master-products','warehouses':'is.master-warehouses','kits':'is.kits'} if key==IKEY else {k:'portal.'+v for k,v in PORTAL.items()} if key==PKEY else {})
 for f,m in fields.items():
  prior={str(x.get('id',i) if isinstance(x,dict) else x):x for i,x in enumerate(old.get(f,[]))};incoming={str(x.get('id',i) if isinstance(x,dict) else x):x for i,x in enumerate(new.get(f,[]))}
  for ident in prior.keys()|incoming.keys():
   a,b=prior.get(ident),incoming.get(ident);r=a or b
   module=m or 'is.'+r.get('kind','')
   if module=='portal.requests':module='portal.'+request_module(r,'requests')
   if a is not None and a==b:continue
   if a is not None and not (module_view(perms,module) and visible(perms,module,a)):
    if b is not None:raise policy.PermissionDenied('Cannot change a hidden record')
    new.setdefault(f,[]).append(a);continue
   if b is not None:
    need(perms,module,b)
    if f=='documents':
     refs=values(b,['sourceId','sourceIds'])
     for line in b.get('lines',[]):
      ref=line.get('borrowRef')
      if isinstance(ref,dict):refs|=values(ref,['documentId','borrowingId','id'])
     for ref in refs:
      d=document(perms,ref)
      if d is not None and not is_visible(perms,d):raise policy.PermissionDenied('Linked source is outside your visibility')
 if key==IKEY:
  shown=filter_data(perms,key,copy.deepcopy(old))
  for field in ['movements','audit']:
   present={str(x.get('id',i)):x for i,x in enumerate(new.get(field,[]))}
   masks={str(x.get('id',i)):x for i,x in enumerate(shown.get(field,[]))}
   for i,a in enumerate(old.get(field,[])):
    ident=str(a.get('id',i));mask=masks.get(ident)
    if mask==a:continue
    b=present.get(ident)
    if b is not None and b not in [mask,a]:raise policy.PermissionDenied('Hidden stock/audit source cannot be changed')
    if b is not None:new[field]=[a if str(x.get('id',j))==ident else x for j,x in enumerate(new[field])]
    else:new.setdefault(field,[]).append(a)
 if key==PKEY:
  if old.get('roleRecordScopes')!=new.get('roleRecordScopes'):
   policy.need(perms,'portal.roles.visibility')
   validate_config(new.get('roleRecordScopes'),new.get('roles',{}))
  prior=old.get('isCRM',{});incoming=new.get('isCRM',{})
  for ident in prior.keys()|incoming.keys():
   if prior.get(ident)==incoming.get(ident):continue
   d=document(perms,ident)
   if not d or not is_visible(perms,d):
    if ident in incoming:raise policy.PermissionDenied('Quotation follow-up is outside your visibility')
    incoming[ident]=prior[ident]
  if 'isCRM' in old or 'isCRM' in new:new['isCRM']=incoming
 return new

def validate_config(config,roles):
 if not isinstance(config,dict) or set(config)-set(roles):raise ValueError('Choose existing roles')
 known=modules()
 for role,settings in config.items():
  if not isinstance(settings,dict) or set(settings)-set(known) or any(v not in SCOPES for v in settings.values()):raise ValueError('Invalid record visibility settings')
  if role.casefold() in {'system admin','administrator'} and any(v!='all' for v in settings.values()):raise ValueError('System Admin retains all records')

def migrate(data):
 if data.get('recordVisibilityV1'):return False
 data.setdefault('roleRecordScopes',{})
 for role in data.get('roles',{}):data['roleRecordScopes'].setdefault(role,{m:default(role,m) for m in modules()})
 data['recordVisibilityV1']=True;return True

def stock_balance(r):
 return {k:v for k,v in r.items() if k in {'id','at','productId','warehouse','lot','expiry','change','qty','held','serviceInventory'}}


def module_view(perms,module):
 import permissions_policy as policy
 key=module+'.view'
 known={p['key'] for p in policy.CATALOG['permissions']}
 if module.startswith('portal.'):
  return module.split('.',1)[1] in perms and (key not in known or key in perms)
 if module in {'is.master-customers','is.master-products'} and 'service.references.view' in perms:return True
 return key not in known or key in perms
