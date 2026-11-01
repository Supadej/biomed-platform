"""Central inventory of Copilot data connectors and required existing permissions."""
import permissions_policy as policy
def catalog():
 p=policy.CATALOG;out=[]
 labels={v['key']:v['label'] for v in p['permissions'] if v.get('action')=='access'}
 own={'tasks','requests','expenses','objectives'}
 for key in p['portalModules']:
  out.append({'id':'portal.'+key,'system':'portal','label':labels.get(key,key.replace('_',' ').title()),'permission':key,'mode':'Own record counts' if key in own else 'Read-only scoped summary','connected':True})
 out.append({'id':'portal.calendar','system':'portal','label':'Calendar','permission':'crm.events.view','mode':'Read events / confirmed drafts','connected':True})
 for key,label,entity in [('leads','Sales Plan','Leads'),('activities','Project & Activity','ProjectActivity'),('tickets','External Helpdesk','HelpDeskTickets')]:
  out.append({'id':'crm.'+key,'system':'portal','label':label,'permission':'crm.'+key+'.view','entity':entity,'mode':'Permission-filtered counts','connected':True})
 seen=set()
 for r in p['permissions']:
  if r.get('action')!='view' or not r['key'].startswith(('is.','budget.')):continue
  ident=r['key'][:-5]
  if ident in seen:continue
  seen.add(ident);system=ident.split('.')[0];key=ident.split('.')[1]
  connected=(key in p['transactions'] or key=='stock-inventory') if system=='is' else key in ['products','cogs','ocos','expense_promo','expense_admin','expense_finance','expense_other','person_salary','person_incentive','person_social','person_health','person_local','person_overseas','person_training','manage_items','manage_products']
  label=p['transactions'].get(key,key.replace('-',' ').title()) if system=='is' else p['budgetTabs'].get(key,key.replace('_',' ').title())
  out.append({'id':ident,'system':system,'label':label,'permission':r['key'],'mode':'Permission-filtered counts' if connected and system=='is' else 'Masked financial totals' if connected else 'Read-only scoped summary','connected':True})
 return out
def permitted(item,perms):
 if item['permission'] not in perms:return False
 if item['system']=='is':return 'is_view' in perms
 if item['system']=='budget':return 'budget_view' in perms
 if item['id'].startswith('crm.') or item['id']=='portal.calendar':return 'crm_view' in perms
 return True
