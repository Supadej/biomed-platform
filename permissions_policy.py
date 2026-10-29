"""Shared catalog migration and server-side authorization of workspace changes."""
import json
from pathlib import Path
CATALOG=json.loads((Path(__file__).parent/'permissions-catalog.json').read_text())
OBSOLETE={'is_edit','is_approve','is_manage','budget_edit','budget_approve','budget_manage'}
def migrate_portal(data):
    if data.get('permissionCatalogVersion')==CATALOG['version'] and data.get('serviceInventoryBillingV1') and data.get('financeControlsV1') and data.get('expressImportV2') and data.get('financialRolesV3') and data.get('visitCalendarV1') and data.get('applicationServiceV1') and data.get('applicationServiceV2') and data.get('staffDirectoryV1'):return False
    roles=data.setdefault('roles',{})
    if not data.get('applicationServiceV2'):
        for name in ['Application Specialist','Application Service Manager']:
            if name in roles:
                additions=['application_service.perform','application_service.calendar','crm_view','crm.events.view','crm.events.create','crm.events.edit']
                if name=='Application Service Manager':additions+=['application_service.manage_references','crm.events.assign']
                roles[name]=sorted(set(roles[name]+additions))
        data['applicationServiceV2']=True
    if not data.get('applicationServiceV1'):
        base=['dashboard','application_service.perform','application_service.calendar','crm.events.view','crm.events.create','crm.events.edit','application_service.view','application_service.create','application_service.edit','application_service.export','crm_view','crm.tickets.view','crm.tickets.create','service.view','service.instruments.view']
        roles.setdefault('Application Specialist',base)
        roles.setdefault('Application Service Manager',base+['application_service.manage_references','crm.events.assign','application_service.view_all','application_service.assign','application_service.delete','application_service.audit','crm.tickets.view_all'])
        data['applicationServiceV1']=True
    if not data.get('visitCalendarV1'):
        for grants in roles.values():
            if 'portal.visits.create' in grants or 'portal.visits.edit' in grants:
                grants.extend(k for k in ['portal.visits.calendar','crm_view','crm.events.view'] if k not in grants)
        data['visitCalendarV1']=True
    if not data.get('financialRolesV3'):
        assignments={
          'Department Manager':['budget_view','budget.approvals.view','budget.approvals.submit','budget.approvals.department_approve','budget.approvals.return'],
          'Accounting':['budget_view','budget.approvals.view','budget.approvals.submit','budget.approvals.finance_approve','budget.approvals.return','budget.finance.view','budget.finance.edit','budget.finance.review','budget.finance.import','budget.express.view'],
          'Managing Director':['budget_view','budget.approvals.view','budget.approvals.director_approve','budget.approvals.return','budget.finance.view','budget.finance.review','budget.express.view','budget.periods.configure','budget.periods.unlock'],
          'Operations Director':['budget_view','budget.approvals.view','budget.approvals.director_approve','budget.approvals.return','budget.finance.view','budget.finance.review','budget.express.view','budget.periods.configure','budget.periods.unlock']}
        for name,grants in assignments.items():
            if name in roles:roles[name]=sorted(set(roles[name])|set(grants))
        data['financialRolesV3']=True
    if not data.get('expressImportV2'):
        for name,grants in roles.items():
            if name in ['Accounting','Managing Director','Operations Director']:
                grants.extend(k for k in ['budget.finance.import','budget.express.view'] if k not in grants)
        data['expressImportV2']=True
    if not data.get('financeControlsV1'):
        for name,grants in roles.items():
            if name in ['Accounting','Managing Director','Operations Director']:
                grants.extend(k for k in ['budget.finance.view','budget.finance.edit','budget.finance.review'] if k not in grants)
            if name in ['Managing Director','Operations Director']:
                grants.extend(k for k in ['budget.periods.configure','budget.periods.unlock'] if k not in grants)
        data['financeControlsV1']=True
    if not data.get('serviceInventoryBillingV1'):
        if 'Accounting' in roles:
            roles['Accounting']=sorted(set(roles['Accounting'])|{'is_view','is.service-inventory.view','service.view','service.jobs.view'})
        data['serviceInventoryBillingV1']=True
    if not data.get('minutesAccessV1'):
        if data.get('permissionCatalogVersion',0)<14:
            for grants in roles.values():
                grants.extend(p for p in ['minutes','portal.minutes.view','portal.minutes.acknowledge'] if p not in grants)
            roles.setdefault('Minutes Coordinator',['minutes']+['portal.minutes.'+a for a in ['view','create','edit','publish','manage','acknowledge','export','delete']])
        data['minutesAccessV1']=True
    if not data.get('serviceReferencesV1'):
        for name,grants in roles.items():
            if 'service.edit' in grants:grants.append('service.references.view')
        data['serviceReferencesV1']=True
    if not data.get('serviceRolePresetsV2'):
        base=['service.view']+[f'service.{k}.view' for k in ['instruments','jobs','movements','parts','replacements','contracts']]
        engineer=base+['service.edit','service.references.view']+[f'service.{k}.{a}' for k in ['jobs','movements','replacements'] for a in ['create','edit','print']]+['service.instruments.print']
        manager=base+['service.edit','service.references.view','service.manage','service.import','service.audit','service.export']+[f'service.{k}.{a}' for k in ['instruments','jobs','movements','parts','replacements','contracts'] for a in ['create','edit','print','export']]
        for name,grants in [('Service Viewer',base),('Service Engineer',engineer),('Service Manager',manager)]:
            if name not in roles:roles[name]=sorted(set(grants))
        data['serviceRolePresetsV2']=True

    if not data.get('serviceInventoryV1'):
        for grants in roles.values():
            if 'service.edit' in grants:
                grants.extend(k for k in ['is_view','is.service-inventory.view','is.service-inventory.request','is.service-inventory.return','is.service-inventory.consume','crm_view','crm.events.view','crm.events.create','crm.events.edit'] if k not in grants)
            if 'service.manage' in grants or 'is.stock-transfer.approve' in grants:
                grants.extend(k for k in ['is_view','is.service-inventory.view','is.service-inventory.approve','is.service-inventory.export'] if k not in grants)
            if 'service.manage' in grants:
                grants.extend(k for k in ['crm.events.assign'] if k not in grants)
        data['serviceInventoryV1']=True


    if not data.get('isPermissionsSeeded'):
        presets={'System Admin':['is_view','is_edit','is_approve','is_manage'],'Managing Director':['is_view','is_edit','is_approve','is_manage'],'Operations Director':['is_view','is_approve'],'Business Director':['is_view','is_approve'],'Department Manager':['is_view','is_edit'],'Accounting':['is_view','is_edit']}
        for role,perms in presets.items():
            if role in roles:roles[role]=list(set(roles[role]+perms))
        data['isPermissionsSeeded']=True
    if not data.get('budgetPermissionsSeeded'):
        for role in roles:
            ps=['budget_view','budget_edit','budget_approve','budget_manage'] if role in ['System Admin','Managing Director'] else ['budget_view','budget_approve'] if role in ['Operations Director','Business Director'] else ['budget_view','budget_edit'] if role in ['Department Manager','Accounting'] else []
            roles[role]=list(set(roles[role]+ps))
        data['budgetPermissionsSeeded']=True
    if not data.get('staffDirectoryV1'):
        for grants in roles.values():
            grants.extend(k for k in ['user_profile','portal.user_profile.view','portal.user_profile.edit','portal.user_profile.password','user_library','portal.user_library.view'] if k not in grants)
            if 'users' in grants:
                grants.extend(k for k in ['portal.users.view','portal.users.edit','portal.users.deactivate','portal.users.reset_password','portal.users.manage_departments'] if k not in grants)
        data['staffDirectoryV1']=True
    for role,perms in roles.items():
        old=set(perms);new=set(perms)
        for p in CATALOG['permissions']:
            if role!='System Admin' and data.get('permissionCatalogVersion',0)>=1 and p.get('introduced',1)<=data['permissionCatalogVersion']:continue
            if role=='System Admin' or p.get('legacy') in old or p['key'].startswith('portal.') and p['action'] in ['approve','reject'] and 'approve_all' in old or p['key'].startswith('is.') and 'is_manage' in old or p['key'].startswith('budget.') and 'budget_manage' in old:new.add(p['key'])
        roles[role]=sorted(new-OBSOLETE)
    data['permissionCatalogVersion']=CATALOG['version'];return True
class PermissionDenied(Exception):pass
def need(perms,*keys):
    selected=next((k for k in keys if k in perms),None)
    if not selected:raise PermissionDenied('Permission required: '+' or '.join(keys))
    if '.' in selected:
        module,action=selected.rsplit('.',1);view=module+'.view'
        if action!='view' and view in {p['key'] for p in CATALOG['permissions']} and view not in perms:raise PermissionDenied('Permission required: '+view)
        if module.startswith('portal.') and module.split('.')[1] not in perms:raise PermissionDenied('Portal module access required: '+module.split('.')[1])
def changes(old,new):
    def keyed(rows):return {str(x.get('id',x.get('name',i))) if isinstance(x,dict) else str(x):x for i,x in enumerate(rows or [])}
    a,b=keyed(old),keyed(new)
    for key in set(a)|set(b):
        if a.get(key)!=b.get(key):yield a.get(key),b.get(key)
def authorize_is(perms,old,new,admin_test=False):
    need(perms,'is_view')
    import service_inventory
    service_inventory.protect(old,new)
    # Purchasing queue invariants apply to every API write, including forged clients.
    olddocs={d['id']:d for d in old.get('documents',[])}
    newdocs={d['id']:d for d in new.get('documents',[])}
    active_sources=set()
    for q in newdocs.values():
        if q.get('kind')!='waiting-purchase':continue
        prior=olddocs.get(q['id'])
        import math
        if q.get('status') not in ['Draft','Pending','Approved','Rejected','Cancelled','Waiting']:raise PermissionDenied('Invalid purchasing request status')
        parent=olddocs.get(q.get('sourceId'),{})
        if not prior:
            if q.get('status')!='Draft':raise PermissionDenied('Purchasing requests must start as drafts')
            if q.get('sourceId') and (parent.get('kind')!='customer-order' or parent.get('status')!='Approved'):raise PermissionDenied('Linked Customer Order must be approved')
        elif prior!=q:
            before,after=prior.get('status'),q.get('status')
            if prior.get('sourceId')!=q.get('sourceId'):raise PermissionDenied('Request source cannot be changed')
            if before==after:
                if before not in ['Draft','Rejected']:raise PermissionDenied('Only draft or rejected requests may be edited')
            else:
                allowed={'Draft':['Pending','Cancelled'],'Rejected':['Pending','Cancelled'],'Pending':['Approved','Rejected'],'Waiting':['Draft','Pending','Cancelled']}
                if after not in allowed.get(before,[]):raise PermissionDenied('Invalid purchasing approval transition')
                if any(prior.get(k)!=q.get(k) for k in set(prior)|set(q) if k not in ['status','history']):raise PermissionDenied('Status changes cannot alter request details')
                if after=='Approved' and not admin_test and not old.get('settings',{}).get('allowSelfApproval',True) and q.get('owner')==(q.get('history') or [{}])[-1].get('by'):raise PermissionDenied('Self approval disabled')
                if after=='Cancelled' and any((d.get('sourceId')==q['id'] or q['id'] in d.get('sourceIds',[])) and d.get('status')!='Cancelled' for d in newdocs.values()):raise PermissionDenied('Cancel linked requisition first')
            if q.get('sourceId') and q.get('status') in ['Pending','Approved'] and parent.get('status')!='Approved':raise PermissionDenied('Linked Customer Order must remain approved')
        if not prior or prior!=q:
            if not q.get('lines'):raise PermissionDenied('Purchasing request needs at least one item')
            for line in q['lines']:
                try:qty=float(line.get('qty',0));price=float(line.get('price',0))
                except (ValueError,TypeError):raise PermissionDenied('Invalid request quantity or price')
                if not line.get('productId') or not math.isfinite(qty) or qty<=0 or not math.isfinite(price) or price<0:raise PermissionDenied('Invalid request quantity or price')
        if q.get('status')!='Cancelled':
            if q.get('sourceId') and q.get('sourceId') in active_sources:raise PermissionDenied('Duplicate active purchasing queue entry')
            active_sources.add(q.get('sourceId'))
    for d in newdocs.values():
        if d.get('kind')=='purchase-request' and not d.get('sourceAllocations') and d['id'] not in olddocs and newdocs.get(d.get('sourceId'),{}).get('kind')=='waiting-purchase':
            queue=olddocs.get(d.get('sourceId'),{})
            parent=olddocs.get(queue.get('sourceId'),{})
            if queue.get('status')!='Approved' or queue.get('sourceId') and parent.get('status')!='Approved':raise PermissionDenied('Purchasing source is no longer approved')
            if any(x['id']!=d['id'] and not x.get('sourceAllocations') and x.get('sourceId')==queue.get('id') and x.get('kind')=='purchase-request' and x.get('status')!='Cancelled' for x in newdocs.values()):raise PermissionDenied('Queue already has a requisition')
    for previous in olddocs.values():
        if previous.get('sourceAllocations'):
            current=newdocs.get(previous['id'],{})
            if any(previous.get(k)!=current.get(k) for k in ['sourceId','sourceIds','sourceAllocations','purchasingBrand']):raise PermissionDenied('Combined PR source allocations cannot be changed')
    # Validate all allocation reservations against the complete stored workspace.
    allocated={}
    for pr in newdocs.values():
        if pr.get('kind')!='purchase-request' or pr.get('status') in ['Cancelled','Rejected']:continue
        allocations=pr.get('sourceAllocations',[])
        if allocations:
            import math
            if set(pr.get('sourceIds',[]))!={a.get('requestId') for a in allocations} or pr.get('sourceId') not in pr.get('sourceIds',[]):raise PermissionDenied('Invalid combined PR source links')
            expected={};actual={}
            for a in allocations:
                q=newdocs.get(a.get('requestId'),{});idx=a.get('requestLine');qty=a.get('qty')
                if q.get('kind')!='waiting-purchase' or q.get('status')!='Approved':raise PermissionDenied('Combined PR needs approved purchasing requests')
                if q.get('sourceId') and newdocs.get(q['sourceId'],{}).get('status')!='Approved':raise PermissionDenied('Source Customer Order is no longer approved')
                if isinstance(idx,bool) or not isinstance(idx,int) or idx<0 or idx>=len(q.get('lines',[])):raise PermissionDenied('Invalid source request line')
                try:qty=float(qty)
                except (ValueError,TypeError):raise PermissionDenied('Invalid allocation quantity')
                if not math.isfinite(qty) or qty<=0:raise PermissionDenied('Invalid allocation quantity')
                line=q['lines'][idx];product=next((x for x in new.get('products',[]) if x.get('id')==line.get('productId')),{});unit=(line.get('unit') or product.get('unit') or '') if pr['id'] not in olddocs else a.get('unit','')
                brand=str(product.get('brand') or line.get('brand') or 'Unspecified brand')
                if a.get('productId')!=line.get('productId') or a.get('unit','')!=unit or pr['id'] not in olddocs and brand!=pr.get('purchasingBrand') or (q.get('currency') or 'THB')!=(pr.get('currency') or 'THB'):raise PermissionDenied('Mixed brand, currency or product in combined PR')
                key=(q['id'],idx);allocated[key]=allocated.get(key,0)+qty
                item=(line.get('productId'),unit);expected[item]=expected.get(item,0)+qty
                if pr['id'] not in olddocs:need(perms,'is.waiting-purchase.derive')
            for line in pr.get('lines',[]):
                try:qty=float(line.get('qty',0))
                except (ValueError,TypeError):raise PermissionDenied('Invalid PR quantity')
                if not math.isfinite(qty) or qty<=0:raise PermissionDenied('Invalid PR quantity')
                key=(line.get('productId'),line.get('unit') or '');actual[key]=actual.get(key,0)+qty
            if set(expected)!=set(actual) or any(abs(expected[k]-actual[k])>1e-6 for k in expected):raise PermissionDenied('PR quantities must match request allocations')
        elif newdocs.get(pr.get('sourceId'),{}).get('kind')=='waiting-purchase':
            q=newdocs[pr['sourceId']]
            for idx,line in enumerate(q.get('lines',[])):allocated[(q['id'],idx)]=allocated.get((q['id'],idx),0)+float(line.get('qty',0))
    for (qid,idx),qty in allocated.items():
        if qty>float(newdocs[qid]['lines'][idx].get('qty',0))+1e-6:raise PermissionDenied('Purchasing quantity already allocated to another PR')
    approved=False
    for before,after in changes(old.get('documents'),new.get('documents')):
        d=after or before;module='is.'+d.get('kind','')
        if not after:raise PermissionDenied('Transaction deletion requires backup restore permission')
        if not before:
            if d.get('kind')=='shipment' and d.get('sourceId'):
                source=next((x for x in new.get('documents',[]) if x.get('id')==d['sourceId']),{})
                need(perms,'is.'+source.get('kind','')+'.approve');approved=True
            else:
                need(perms,module+'.create')
                if d.get('status') not in ['Draft','Rejected']:raise PermissionDenied('New transactions must start as drafts')
                if d.get('sourceId'):
                    source=next((x for x in old.get('documents',[]) if x.get('id')==d['sourceId']),{})
                    need(perms,'is.'+source.get('kind','')+'.derive')
        elif before.get('status')!=after.get('status'):
            action={'Pending':'submit','Approved':'approve','Rejected':'reject','Cancelled':'cancel'}.get(after.get('status'),'edit');need(perms,module+'.'+action);approved|=action=='approve'
            if action in ['approve','reject'] and before.get('status')!='Pending':raise PermissionDenied('Only pending transactions can be decided')
            if action in ['approve','reject'] and any(before.get(k)!=after.get(k) for k in ['kind','lines','party','warehouse','sourceId']):raise PermissionDenied('Approval cannot change transaction details')
        elif before.get('portalCRM')!=after.get('portalCRM') and all(before.get(k)==after.get(k) for k in set(before)|set(after) if k!='portalCRM'):need(perms,'portal.pipeline.edit')
        else:need(perms,module+'.edit')
    for category in ['customers','suppliers','products','warehouses']:
        for a,b in changes(old.get(category),new.get(category)):
            action='create' if a is None else 'delete' if b is None else 'deactivate' if isinstance(a,dict) and isinstance(b,dict) and a.get('active',True)!=b.get('active',True) else 'edit'
            need(perms,'is.master-'+category+'.'+action,'is.master-'+category+'.import')
    for field,module in [('stockChecks','cycle-count'),('warehouseMoves','warehouse-move'),('kits','kits'),('quarantines','lot-control')]:
        for a,b in changes(old.get(field),new.get(field)):
            if field=='quarantines':action='release' if (b or {}).get('status')=='Released' else 'hold'
            else:action='create' if a is None else 'delete' if b is None else 'approve' if b.get('status')=='Approved' else 'reject' if b.get('status')=='Rejected' else 'edit'
            need(perms,'is.'+module+'.'+action);approved|=action=='approve'
    if old.get('movements',[])!=new.get('movements',[]) and not approved:raise PermissionDenied('Stock movements require an authorized approval')
    if old.get('settings',{})!=new.get('settings',{}):need(perms,'is.rules.edit')
    if old.get('users',[])!=new.get('users',[]):raise PermissionDenied('IS actor definitions cannot be edited directly')
    known={'documents','customers','suppliers','products','warehouses','stockChecks','warehouseMoves','kits','quarantines','movements','audit','settings','users','lots'}
    if old.get('lots',[])!=new.get('lots',[]) and not approved:need(perms,'is.lot-control.hold','is.lot-control.release')
    for k in set(old)|set(new):
        if k not in known and old.get(k)!=new.get(k):need(perms,'is.rules.edit')
CATEGORY={'Promotional Expenses':'expense_promo','Administrative Expenses':'expense_admin','Financial Expenses':'expense_finance','Other Expenses':'expense_other','Salary and Bonus':'person_salary','Commission and Incentive':'person_incentive','Social Security and Provident Fund':'person_social','Healthcare Coverage':'person_health','Local Traveling and Expenses':'person_local','Overseas Traveling and Expenses':'person_overseas','Trainings and KOM':'person_training','Other Cost of Sales':'ocos'}
def authorize_budget(perms,old,new):
    need(perms,'budget_view')
    if old.get('active')!=new.get('active'):need(perms,'budget.fiscal-year.switch')
    oldyears,newyears=old.get('years',{}),new.get('years',{})
    for year in set(oldyears)|set(newyears):
        a,b=oldyears.get(year),newyears.get(year)
        if a==b:continue
        if a is None:need(perms,'budget.fiscal-year.create');continue
        if b is None:need(perms,'budget.settings.reset_all');continue
        for kind,master in [('products','manage_products'),('expenses','manage_items')]:
            for prev,nxt in changes(a.get(kind),b.get(kind)):
                rec=nxt or prev;tab=CATEGORY.get(rec.get('category'),'manage_items') if kind=='expenses' else 'products'
                if prev is None or nxt is None:
                    action='create' if prev is None else 'delete';need(perms,'budget.'+master+'.'+action,'budget.ocos.'+action if tab=='ocos' else 'budget.workforce.edit' if rec.get('workforceId') else 'budget.'+master+'.'+action);continue
                for field in set(prev)|set(nxt):
                    if prev.get(field)==nxt.get(field):continue
                    numeric={'budget':'edit','cogsBudget':'edit','revenueActual':'actual','cogsActual':'actual','actual':'actual','commitment':'commitment','componentRows':'edit'}
                    if field in numeric:
                        target='cogs' if field in ['cogsBudget','cogsActual'] else tab
                        if field=='componentRows':
                            for ca,cb in changes(prev.get(field),nxt.get(field)):
                                if ca is None or cb is None:need(perms,'budget.ocos.create' if ca is None else 'budget.ocos.delete')
                                else:
                                    for ck in set(ca)|set(cb):
                                        if ca.get(ck)!=cb.get(ck):need(perms,'budget.ocos.'+('delete' if ck=='active' and cb.get(ck)==False else 'edit' if ck not in ['actual','commitment'] else ck))
                            continue
                        need(perms,'budget.'+target+'.'+numeric[field],*(['budget.is_bridge.reconcile'] if field=='revenueActual' else []))
                    else:need(perms,'budget.'+master+'.edit',*(['budget.masters.edit'] if field in ['costCenter','division'] else []),*(['budget.'+master+'.delete'] if field=='active' else []))
        for field,module in [('costCenters','masters'),('workforce','workforce'),('ledger','ledger')]:
            for prev,nxt in changes(a.get(field),b.get(field)):
                action='create' if prev is None else 'delete' if nxt is None else 'edit';need(perms,'budget.'+module+'.'+action,*(['budget.is_bridge.reconcile'] if field=='ledger' else []))
        for prev,nxt in changes(a.get('approvals'),b.get('approvals')):
            if prev is None:need(perms,'budget.approvals.submit')
            elif nxt is None:need(perms,'budget.settings.reset_current','budget.settings.reset_all')
            else:
                expected={'Submitted':'Department Approved','Department Approved':'Finance Approved','Finance Approved':'Approved'}.get(prev.get('status'))
                if nxt.get('status') not in ['Returned',expected]:raise PermissionDenied('Invalid budget approval transition')
                action='return' if nxt.get('status')=='Returned' else {'Submitted':'department_approve','Department Approved':'finance_approve','Finance Approved':'director_approve'}.get(prev.get('status'),'edit');need(perms,'budget.approvals.'+action)
        if a.get('ocosNames')!=b.get('ocosNames'):need(perms,'budget.ocos.create','budget.ocos.delete','budget.ocos.edit')
        if a.get('isMappings')!=b.get('isMappings'):need(perms,'budget.is_bridge.edit')
        if a.get('settings')!=b.get('settings'):need(perms,'budget.settings.restore')
        if a.get('versions')!=b.get('versions') and a.get('approvals')==b.get('approvals'):need(perms,'budget.settings.reset_current','budget.settings.reset_all')
def validate_demo_change(perms,old,new,a,b,actor_id):
    """Enforce demo routing even when the workspace API is called directly."""
    before=(a or {}).get('approvalStatus','Not submitted');after=(b or {}).get('approvalStatus','Not submitted')
    admin='approve_all' in perms
    owner=(a or b or {}).get('employee') or (a or b or {}).get('owner')
    manager=next((u.get('managerId') for u in old.get('users',[]) if u.get('id')==owner),None)
    if not a:
        if after!='Draft':raise PermissionDenied('New demos must start as drafts')
        if b.get('history'):raise PermissionDenied('New demos cannot contain approval history')
        if actor_id and not admin and b.get('owner')!=actor_id:raise PermissionDenied('Invalid demo creator')
        if actor_id and owner!=actor_id and not admin and manager!=actor_id:raise PermissionDenied('Demo employee must be in your reporting team')
        return 'create'
    if not b:
        if before not in ['Draft','Rejected','Not submitted']:raise PermissionDenied('Submitted demos must be retained')
        if actor_id and not admin and actor_id not in [owner,manager]:raise PermissionDenied('Cannot remove another employee demo')
        return 'delete'
    if before!=after:
        transitions={'Draft':['Pending'],'Not submitted':['Pending'],'Rejected':['Pending'],'Pending':['Approved','Rejected','Cancelled']}
        if after not in transitions.get(before,[]):raise PermissionDenied('Invalid demo approval transition')
        action={'Pending':'submit','Approved':'approve','Rejected':'reject','Cancelled':'cancel'}[after]
        if actor_id and not admin and (actor_id!=manager or actor_id==owner) and action in ['approve','reject']:raise PermissionDenied('Only the reporting manager or administrator may decide this demo')
        if actor_id and not admin and actor_id!=owner and action in ['submit','cancel']:raise PermissionDenied('Only the employee may submit or withdraw this demo')
        if any(a.get(k)!=b.get(k) for k in set(a)|set(b) if k not in ['approvalStatus','history']):raise PermissionDenied('Approval cannot alter demo details')
        history=b.get('history',[]);previous=a.get('history',[])
        if not isinstance(history,list) or len(history)!=len(previous)+1 or history[:-1]!=previous or history[-1].get('action')!=after or actor_id and history[-1].get('by')!=actor_id:raise PermissionDenied('Append an approval history entry for this action')
        if after=='Rejected' and not str(history[-1].get('reason','')).strip():raise PermissionDenied('Rejection reason required')
        if after=='Pending' and (not b.get('customer') or not b.get('start') or not b.get('end') or b['end']<b['start'] or not manager and not admin):raise PermissionDenied('Demo needs a customer, valid dates and a reporting manager')
        return action
    if actor_id and not admin and actor_id not in [owner,manager]:raise PermissionDenied('Cannot edit another employee demo')
    if before in ['Pending','Cancelled']:raise PermissionDenied('Pending or withdrawn demos cannot be edited')
    if a.get('history',[])!=b.get('history',[]):raise PermissionDenied('Approval history cannot be rewritten')
    if before=='Approved' and any(a.get(k)!=b.get(k) for k in set(a)|set(b) if k not in ['status','feedback','next','updated']):raise PermissionDenied('Approved demo details are locked; update only evaluation progress')
    return 'edit'

def validate_scheme(b,new,old_id):
    import math,re
    try:rate=float(b['rate']);threshold=float(b['threshold'])
    except (ValueError,TypeError,KeyError):raise PermissionDenied('Invalid incentive rate or target attainment')
    if not math.isfinite(rate) or not 0<=rate<=100 or not math.isfinite(threshold) or threshold<0:raise PermissionDenied('Invalid incentive rate or target attainment')
    if not all(re.fullmatch(r'20\d{2}-(0[1-9]|1[0-2])',str(b.get(k,''))) for k in ['from','to']) or b['from']>b['to']:raise PermissionDenied('Invalid incentive period')
    if b.get('line') not in new.get('productLines',[]) or not any(u.get('id')==b.get('rep') for u in new.get('users',[])):raise PermissionDenied('Choose an existing representative and product line')
    if any(s.get('id')!=old_id and all(s.get(k)==b.get(k) for k in ['rep','line','from','to']) for s in new.get('incentiveSchemes',[])):raise PermissionDenied('Duplicate incentive scheme')

def authorize_portal(perms,old,new,actor_id=None):
    mapping={'tickets':'helpdesk','salesTargets':'sales','salesActuals':'sales','departments':'hierarchy','productLines':'sales','incentiveSchemes':'incentives','incentiveClaims':'incentives','trainerRequests':'training','siteSections':'content','assets':'settings','roleDescriptions':'roles'}
    for field in set(old)|set(new):
        if old.get(field)==new.get(field):continue
        if field=='integrationIS':raise PermissionDenied('Use integration reconciliation to change bridge projections')
        if field=='isCRM':
            before=old.get(field,{}) or {};after=new.get(field,{}) or {}
            if not isinstance(before,dict) or not isinstance(after,dict):raise PermissionDenied('Invalid quotation follow-up register')
            for ident in set(before)|set(after):
                a=before.get(ident);b=after.get(ident)
                if a==b:continue
                if b is not None:
                    if not isinstance(b,dict) or set(b)-{'outcome','reason','lead','followup','updatedBy','updatedAt'}:raise PermissionDenied('Invalid quotation follow-up fields')
                    if b.get('outcome','Monitoring') not in ['Monitoring','Follow-up','Won','Lost']:raise PermissionDenied('Invalid quotation outcome')
                    if type(b.get('lead',False)) is not bool:raise PermissionDenied('Invalid pipeline flag')
                    if b.get('outcome') in ['Won','Lost'] and not str(b.get('reason','')).strip():raise PermissionDenied('Won/Lost requires justification')
                action='delete' if b is None else 'edit'
                candidates=['portal.'+m+'.'+action for m in ['tenders','pipeline'] if m in perms and (m=='tenders' or (a or b or {}).get('lead'))]
                if not candidates:raise PermissionDenied('Quotation & Tender or Sales Pipeline access required')
                need(perms,*candidates)
                if b is not None and bool((a or {}).get('lead'))!=bool(b.get('lead')):need(perms,'portal.pipeline.edit')
            continue

        if field in ['permissionCatalogVersion','isPermissionsSeeded','budgetPermissionsSeeded']:
            raise PermissionDenied('Permission migration metadata cannot be edited')
        if field in ['initialBrandsSeeded'] and old.get(field) is None:continue
        if old.get(field) is None and new.get(field) in [[],{},None]:continue
        module=mapping.get(field,field)
        if field=='roles':
            need(perms,'roles')
            for name in set(old.get(field,{}))|set(new.get(field,{})):
                if old.get(field,{}).get(name)!=new.get(field,{}).get(name):need(perms,'portal.roles.create' if name not in old.get(field,{}) else 'portal.roles.edit')
        elif isinstance(old.get(field,[]),list) and isinstance(new.get(field),list):
            for a,b in changes(old.get(field),new.get(field)):
                action='create' if a is None else 'delete' if b is None else 'edit'
                if field in ['salesTargets','salesActuals','productLines','departments']:action='edit'
                if field in ['requests','expenses','objectives','incentiveClaims','payments','trainerRequests'] and a and b and a.get('status')!=b.get('status'):action='approve' if b.get('status') in ['Approved','Paid','Completed'] else 'reject' if b.get('status') in ['Rejected','Returned'] else 'cancel' if b.get('status') in ['Cancelled','Withdrawn'] else 'submit'
                if field=='demos':action=validate_demo_change(perms,old,new,a,b,actor_id)
                if field=='incentiveSchemes' and b:
                    validate_scheme(b,new,(a or b).get('id'))
                    if a:
                        for claim in old.get('incentiveClaims',[]):
                            if claim.get('schemeId')==a.get('id') and not claim.get('schemeSnapshot'):
                                updated=next((x for x in new.get('incentiveClaims',[]) if x.get('id')==claim.get('id')),{})
                                if updated.get('schemeSnapshot')!=a:raise PermissionDenied('Preserve the original scheme snapshot on existing incentive claims before editing')
                if field=='incentiveClaims' and a and b and a.get('schemeSnapshot')!=b.get('schemeSnapshot'):
                    scheme=next((x for x in old.get('incentiveSchemes',[]) if x.get('id')==a.get('schemeId')),None)
                    if a.get('schemeSnapshot') or b.get('schemeSnapshot')!=scheme or any(a.get(k)!=b.get(k) for k in set(a)|set(b) if k!='schemeSnapshot'):raise PermissionDenied('Submitted incentive snapshot cannot be changed')
                    need(perms,'portal.incentives.edit');continue
                if field=='trainerRequests' and a is None:action='submit'
                if field=='users' and a and b and a.get('role')!=b.get('role'):action='assign'
                if field=='announcements' and a and b and a.get('acks')!=b.get('acks') and all(a.get(k)==b.get(k) for k in set(a)|set(b) if k!='acks'):action='acknowledge'
                if field=='requests':module='cars' if (b or a).get('type')=='car' else 'rooms' if (b or a).get('type')=='room' else 'requests'
                if field=='requests' and action in ['approve','reject']:
                    t=(b or a).get('type');need(perms,'approve_'+('car' if t=='car' else 'room' if t=='room' else t),'approve_all')
                need(perms,'portal.'+module+'.'+action)
                if module=='content' and b:
                    for field in ['photos','attachments']:
                        if b.get(field,[])!=(a or {}).get(field,[]):need(perms,'portal.content.upload')
                if module=='content' and b and b.get('status')=='published' and a!=b:need(perms,'portal.content.publish')
                if module in ['pipeline','tenders'] and b:
                    if 'outcome' in b:
                        if b['outcome'] not in ['Monitoring','Follow-up','Lead','Qualified','Proposal','Negotiation','Preparing','Submitted','Clarification','Cancelled','Won','Lost']:raise PermissionDenied('Invalid follow-up outcome')
                        for key,limit in [('reason',4000),('followup',10000)]:
                            if not isinstance(b.get(key,''),str) or len(b.get(key,''))>limit:raise PermissionDenied('Invalid follow-up text')
                        if b['outcome'] in ['Won','Lost'] and not b.get('reason','').strip():raise PermissionDenied('A justification is required for Won or Lost')
                    if 'lead' in b and type(b['lead']) is not bool:raise PermissionDenied('Invalid pipeline flag')
                    if module=='tenders' and bool((a or {}).get('lead'))!=bool(b.get('lead')):need(perms,'portal.pipeline.edit')
                    import math
                    try:
                        amount=float(b.get('value' if module=='pipeline' else 'amount',0) or 0)
                        probability=float(b.get('probability',0) or 0)
                    except (ValueError,TypeError):raise PermissionDenied('Invalid opportunity value')
                    if not math.isfinite(amount) or amount<0 or module=='pipeline' and (not math.isfinite(probability) or not 0<=probability<=100):raise PermissionDenied('Invalid opportunity value or probability')
                if module in ['forms','resources','sops','jobdescriptions','kpis','training','announcements'] and b:
                    for fk in ['fileId','materialId','attachments']:
                        if b.get(fk) and (a or {}).get(fk)!=b.get(fk):need(perms,'portal.'+module+'.upload')
                    if module in ['forms','resources','sops','jobdescriptions','kpis'] and (a or {}).get('sharedWith',[])!=b.get('sharedWith',[]):need(perms,'portal.'+module+'.share')
        else:need(perms,'portal.'+module+'.'+('publish' if field=='siteSections' else 'edit'))
def authorize_change(perms,key,before,after,operation=None,actor_id=None,admin_test=False):
    old=json.loads(before or '{}');new=json.loads(after or '{}')
    if not isinstance(old,dict) or not isinstance(new,dict):raise PermissionDenied('Workspace must be an object')
    if key=='biomed_is_v50_transactions' and operation=='restore':need(perms,'is.backup.restore');return
    if key=='biomed_budget_v60_years' and operation in ['restore','reset_current','reset_all']:
        need(perms,'budget.settings.'+operation)
        if operation=='reset_current' and any(old.get('years',{}).get(y)!=new.get('years',{}).get(y) for y in set(old.get('years',{}))|set(new.get('years',{})) if str(y)!=str(old.get('active'))):raise PermissionDenied('Only the active fiscal year can be reset')
        return
    if key=='biomed_is_v50_transactions':authorize_is(perms,old,new,admin_test)
    elif key=='biomed_budget_v60_years':authorize_budget(perms,old,new)
    elif key=='biomed_portal_v33_clean':
        if not old:
            need(perms,'portal.roles.edit');return
        authorize_portal(perms,old,new,actor_id)

PORTAL_FIELDS={'tickets':'helpdesk','salesTargets':'sales','salesActuals':'sales','productLines':'sales','incentiveSchemes':'incentives','incentiveClaims':'incentives','trainerRequests':'training','siteSections':'content'}
FINANCE_FIELDS=['budget','cogsBudget','revenueActual','cogsActual','actual','commitment','componentRows']
def financial_view(perms,record,field,product=False):
    module='cogs' if product and field in ['cogsBudget','cogsActual'] else 'products' if product else CATEGORY.get(record.get('category'),'manage_items')
    return 'budget.'+module+'.view' in perms
def budget_row_visible(perms,row,product=False):
    return ('budget.manage_products.view' in perms or 'budget.products.view' in perms or 'budget.cogs.view' in perms) if product else ('budget.manage_items.view' in perms or 'budget.'+CATEGORY.get(row.get('category'),'manage_items')+'.view' in perms)
def read_filter(perms,key,value):
    if not value:return value
    if key not in ['biomed_is_v50_transactions','biomed_budget_v60_years','biomed_portal_v33_clean']:return value
    data=json.loads(value)
    if key=='biomed_is_v50_transactions':
        if 'is.backup.export' in perms:return value
        data['documents']=[d for d in data.get('documents',[]) if 'is.'+d.get('kind','')+'.view' in perms or 'is.outstanding.view' in perms and d.get('kind') in ['invoice','credit-note','debit-note','payment-receipt']]
        for field,module in [('stockChecks','cycle-count'),('warehouseMoves','warehouse-move'),('quarantines','lot-control'),('kits','kits'),('audit','history')]:
            if 'is.'+module+'.view' not in perms:data[field]=[]
        if not any('is.'+k+'.view' in perms for k in ['stocks','stock-inventory','expiry','lot-control','cycle-count','warehouse-move']):data['movements']=[];data['lots']=[]
    elif key=='biomed_budget_v60_years':
        if 'budget.settings.backup' in perms:return value
        for y in data.get('years',{}).values():
            for field,product in [('products',True),('expenses',False)]:
                y[field]=[row for row in y.get(field,[]) if budget_row_visible(perms,row,product)]
                for row in y[field]:
                    for f in FINANCE_FIELDS:
                        if f in row and not financial_view(perms,row,f,product):row[f]=[] if f=='componentRows' else [0]*12
            for field,module in [('workforce','workforce'),('approvals','approvals'),('versions','settings')]:
                if 'budget.'+module+'.view' not in perms:y[field]=[]
            if 'budget.ledger.view' not in perms:y['ledger']=[]
            else:
                ids={x['id'] for x in y['products']+y['expenses']};y['ledger']=[x for x in y.get('ledger',[]) if x.get('line','').removeprefix('cogs:') in ids]
    else:
        if 'isCRM' in data:
            data['isCRM']={k:v for k,v in data['isCRM'].items() if 'tenders' in perms or 'pipeline' in perms and isinstance(v,dict) and v.get('lead')}
        if 'integrationIS' in data:
            if not any(m in perms for m in ['pipeline','tenders']):data['integrationIS']['quotations']=[]
            if 'sales' not in perms:data['integrationIS']['salesActuals']=[]
            if 'portal.integration_is.view' not in perms:data['integrationIS']['exceptions']=[]
        for field in list(data):
            module=PORTAL_FIELDS.get(field,field)
            if field=='operationalBrands':continue
            if (isinstance(data[field],list) or field=='siteSections') and field not in ['users','departments'] and module not in perms:data[field]={} if field=='siteSections' else []
    return json.dumps(data,ensure_ascii=False,separators=(',',':'))
def merge_scope(perms,key,old_value,new_value):
    """Preserve omitted records and masked amounts when a restricted user saves."""
    if not old_value or not new_value:return new_value
    old,new=json.loads(old_value),json.loads(new_value)
    if key=='biomed_is_v50_transactions':
        visible=json.loads(read_filter(perms,key,old_value))
        for field in ['documents','stockChecks','warehouseMoves','quarantines','kits','audit','movements','lots']:
            shown={str(x.get('id',i)) for i,x in enumerate(visible.get(field,[]))}
            incoming={str(x.get('id',i)) for i,x in enumerate(new.get(field,[]))}
            for i,row in enumerate(old.get(field,[])):
                ident=str(row.get('id',i))
                if ident not in shown and ident not in incoming:new.setdefault(field,[]).append(row)
    elif key=='biomed_budget_v60_years':
        for year,y in new.get('years',{}).items():
            previous=old.get('years',{}).get(year,{})
            if not previous and 'budget.fiscal-year.create' in perms:
                previous=json.loads(json.dumps(old.get('years',{}).get(str(old.get('active')),{})))
                for row in previous.get('products',[]):row['revenueActual']=[0]*12;row['cogsActual']=[0]*12
                for row in previous.get('expenses',[]):
                    row['actual']=[0]*12;row['commitment']=[0]*12
                    for component in row.get('componentRows',[]):component['actual']=[0]*12;component['commitment']=[0]*12
                for field in ['ledger','approvals','versions']:previous[field]=[]
            for field,product in [('products',True),('expenses',False)]:
                rows={x['id']:x for x in y.get(field,[])}
                for before in previous.get(field,[]):
                    current=rows.get(before['id'])
                    if current is None and not budget_row_visible(perms,before,product):y.setdefault(field,[]).append(before);continue
                    if current:
                        for f in FINANCE_FIELDS:
                            if f in before and not financial_view(perms,before,f,product):
                                mask=[] if f=='componentRows' else [0]*12
                                if current.get(f,mask) not in [mask,before[f]]:raise PermissionDenied('A hidden financial schedule cannot be changed')
                                current[f]=before[f]
            for field,module in [('workforce','workforce'),('approvals','approvals'),('versions','settings')]:
                if 'budget.'+module+'.view' not in perms and y.get(field,[])==[]:y[field]=previous.get(field,[])
            if 'budget.ledger.view' not in perms and y.get('ledger',[])==[]:y['ledger']=previous.get('ledger',[])
            elif 'budget.ledger.view' in perms:
                visible_ids={x['id'] for x in previous.get('products',[])+previous.get('expenses',[]) if budget_row_visible(perms,x,x in previous.get('products',[]))}
                present={x['id'] for x in y.get('ledger',[])}
                for x in previous.get('ledger',[]):
                    if x.get('line','').removeprefix('cogs:') not in visible_ids and x['id'] not in present:y.setdefault('ledger',[]).append(x)
    elif key=='biomed_portal_v33_clean':
        if 'integrationIS' in old:new['integrationIS']=old['integrationIS']
        if 'isCRM' in old:
            incoming=new.setdefault('isCRM',{})
            for ident,row in old['isCRM'].items():
                if not ('tenders' in perms or 'pipeline' in perms and isinstance(row,dict) and row.get('lead')):incoming[ident]=row
        for field in old:
            module=PORTAL_FIELDS.get(field,field)
            if field=='operationalBrands':continue
            if (isinstance(old[field],list) or field=='siteSections') and field not in ['users','departments'] and module not in perms and new.get(field) in [[],{},None]:new[field]=old[field]
    return json.dumps(new,ensure_ascii=False,separators=(',',':'))


def is_system_admin(actor):
    return str(actor[3]).strip().lower().replace('_',' ').replace('-',' ') in ('system admin','administrator')
def admin_self_approval(actor,c):
    if not is_system_admin(actor) or c is None:return False
    c.execute("CREATE TABLE IF NOT EXISTS system_controls(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
    r=c.execute("SELECT value FROM system_controls WHERE key='adminSelfApprovalTesting'").fetchone()
    return bool(r and r[0]=='true')
def self_approval_audit(c,actor,kind,reference):
    c.execute('CREATE TABLE IF NOT EXISTS system_admin_audit(id INTEGER PRIMARY KEY,at TEXT,actor TEXT,action TEXT,detail TEXT)')
    import datetime
    c.execute('INSERT INTO system_admin_audit(at,actor,action,detail) VALUES(?,?,?,?)',(datetime.datetime.now(datetime.timezone.utc).isoformat(),str(actor[4]),'TEST self-approval',json.dumps({'workflow':kind,'reference':reference})))
