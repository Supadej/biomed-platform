"""Functional default grants for the supplied company staff roster.

Supervisor and manager titles use the same functional management tier.
No shared director/manager template grants system administration.
"""
import permissions_policy as policy

VALID={p['key'] for p in policy.CATALOG['permissions']}

def grants(role):
 if role=='System Admin':return sorted(VALID)
 g=set()
 def add(*keys):g.update(k for k in keys if k in VALID)
 def module(name,actions):
  if name.startswith('portal.'):add(name.split('.')[1])
  elif name.startswith('crm.'):add('crm_view')
  elif name.startswith('is.'):add('is_view')
  elif name.startswith('budget.'):add('budget_view')
  elif name.startswith('service.'):add('service.view')
  add(*(name+'.'+a for a in actions.split()))
 def self_service():
  add('dashboard','announcements','requests','cars','rooms','expenses','tasks','helpdesk','training','objectives','hrprofiles','leavebalance','sops','jobdescriptions','kpis','forms','resources','minutes','user_profile','user_library','ai.internal.use')
  for name,actions in {'announcements':'download acknowledge','requests':'create edit submit cancel','cars':'create edit submit cancel','rooms':'create edit submit cancel','expenses':'create submit cancel export','tasks':'create edit','helpdesk':'create edit','training':'download submit','objectives':'create edit submit','sops':'download','jobdescriptions':'download','kpis':'download','forms':'download','resources':'download','minutes':'view acknowledge','user_profile':'view edit password','user_library':'view'}.items():module('portal.'+name,actions)
  module('crm.events','view create edit');module('crm.files','view upload');module('crm.shortcuts','view create edit delete')
 def documents(kinds,manager=False,edit=True):
  for k in kinds.split():module('is.'+k,'view print export'+(' create edit submit derive' if edit else '')+(' approve reject cancel' if manager else ''))
  module('is.dashboard','view');module('is.trace','view')
 def customers(edit=False):module('is.master-customers','view'+(' create edit' if edit else ''))
 def projects(manager=False):
  for k in ['projects','project_stages','activities']:module('crm.'+k,'view create edit export'+(' assign view_all' if manager else ''))
 def tickets(manager=False):module('crm.tickets','view create edit export'+(' assign view_all' if manager else ''))
 def sales(manager=False):
  add('sales','incentives','visits','demos','tenders','pipeline','objectives')
  for k,a in {'visits':'create edit calendar','demos':'create edit submit cancel','tenders':'create edit','pipeline':'create edit','incentives':'create edit submit cancel'}.items():module('portal.'+k,a)
  module('crm.leads','view create edit export'+(' view_all assign' if manager else ''));projects(manager);tickets(manager);customers(True)
  documents('quotation customer-order sales-order borrowing return-product',manager)
  documents('invoice',False,False)
  module('is.stocks','view');module('is.outstanding','view')
  if manager:
   add('manage_sales','manage_incentives','approve_incentives');module('portal.sales','edit');module('portal.incentives','approve reject');module('portal.demos','approve reject');module('portal.objectives','approve reject');module('crm.targets','view create edit export');module('crm.events','view_all assign')
 def financial(manager=False):
  add('payments','process_payments');module('portal.payments','create edit submit'+(' approve reject' if manager else ''))
  for k in ['dashboard','pnl','products_summary','budget_summary','reports','quality']:module('budget.'+k,'view export')
  for k in ['products','cogs','ocos','expense_promo','expense_admin','expense_finance','expense_other','person_salary','person_incentive','person_social','person_health','person_local','person_overseas','person_training']:module('budget.'+k,'view export edit actual commitment')
  for k in ['ledger','masters','manage_products','manage_items','workforce']:module('budget.'+k,'view export create edit')
  module('budget.finance','view edit import'+(' review' if manager else ''));module('budget.express','view');module('budget.approvals','view export submit return'+(' finance_approve' if manager else ''))
  for k in ['is_bridge','portal_bridge']:module('budget.'+k,'view edit reconcile')
  if manager:module('budget.periods','configure unlock')
  documents('invoice credit-note debit-note payment-receipt',manager);documents('quotation customer-order sales-order purchase-request purchase-order supplier-confirm delivery-in delivery-out',False,False)
  module('is.service-inventory','view export');module('service.jobs','view');customers();module('is.master-suppliers','view');module('is.reports','view print export')
 def logistics(manager=False):
  documents('delivery-in check-in delivery-out check-out stock-transfer stock-count withdrawal borrowing return-product',manager)
  for k in ['stocks','stock-inventory','expiry','outstanding']:module('is.'+k,'view export')
  module('is.shipment','view print export progress')
  for k in ['cycle-count','warehouse-move']:module('is.'+k,'view create export print'+(' approve reject' if manager else ''))
  module('is.service-inventory','view export'+(' approve' if manager else ''))
  for k in ['master-products','master-warehouses']:module('is.'+k,'view'+(' create edit import export deactivate' if manager else ''))
  if manager:module('is.lot-control','view hold release export')
 def purchasing(manager=False):
  documents('purchase-request purchase-order supplier-confirm',manager);documents('delivery-in check-in',False,False)
  module('is.waiting-purchase','view create edit derive submit print'+(' approve reject cancel' if manager else ''))
  module('is.master-suppliers','view create edit'+(' import export deactivate' if manager else ''));module('is.master-products','view');module('is.stocks','view');projects(manager)
 def service(manager=False):
  add('service.view','service.edit')
  for k in ['instruments','jobs','movements','parts','replacements','contracts']:module('service.'+k,'view print'+(' create edit export' if manager or k in ['jobs','movements','replacements'] else ''))
  add('service.references.view');tickets(manager)
  module('is.service-inventory','view request return consume'+(' approve export' if manager else ''))
  if manager:add('service.manage','service.export','service.import','service.audit');module('crm.events','view_all assign')
 def application(manager=False):
  add(*('application_service.'+a for a in ('view create edit export perform calendar print'+(' view_all assign audit manage_references' if manager else '')).split()))
  module('service.instruments','view');module('service.references','view');customers();tickets(manager)
  if manager:module('crm.events','view_all assign')
 def management():
  add('hierarchy','manage_tasks','approve_travel','approve_budget','approve_leave','approve_general','approve_expense')
  module('portal.requests','approve reject');module('portal.expenses','approve reject');module('portal.training','approve reject');module('portal.objectives','approve reject')
 def commercial_budget():
  for k in ['dashboard','products_summary','budget_summary','products','cogs','ocos','expense_promo','reports']:module('budget.'+k,'view export'+(' edit commitment' if k in ['products','cogs','ocos','expense_promo'] else ''))
  module('budget.approvals','view submit department_approve return')

 self_service()
 if role in ['Sales Representative','Sales Manager','Sales Supervisor','Product Manager','Product Specialist','Business Director','Marketing Communication Specialist']:
  sales(role in ['Sales Manager','Sales Supervisor','Product Manager','Business Director'])
 if role in ['Sales Manager','Sales Supervisor','Product Manager','Business Director']:management();commercial_budget()
 if role in ['Service Engineer','Service Engineer Supervisor','Service Manager']:
  service(role!='Service Engineer')
  if role!='Service Engineer':management()
 if role in ['Application Specialist','Application Specialist Manager','Application Service Manager']:
  application(role!='Application Specialist');add('visits','demos');module('portal.visits','create edit calendar');module('portal.demos','create edit submit cancel')
  if role!='Application Specialist':management();module('portal.demos','approve reject')
 if role in ['Inventory Officer','Operation Manager','Messenger & Delivery Supervisor','Delivery Manager']:logistics(role!='Inventory Officer')
 if role in ['Purchasing Officer','Procurement & Regulatory Supervisor','Procurement & Regulatory Manager','Operation Manager']:purchasing(role!='Purchasing Officer')
 if role in ['Operation Manager','Messenger & Delivery Supervisor','Delivery Manager','Procurement & Regulatory Supervisor','Procurement & Regulatory Manager']:management()
 if role in ['Accounting','Accounting Manager']:financial(role=='Accounting Manager')
 if role=='Accounting Manager':management()
 if role=='Bill Collector':documents('invoice payment-receipt');customers();module('portal.payments','edit');add('payments');module('crm.billing','view edit');module('is.outstanding','view')
 if role in ['Administration Officer','Director Secretary']:
  add('announcements','forms','resources');tickets();projects();module('crm.contacts','view create edit');module('portal.forms','create edit upload share');module('portal.resources','create edit upload share')
 if role=='Administration Officer':documents('customer-order sales-order delivery-out',False,False)
 if role=='Messenger & Delivery':module('is.shipment','view print progress');documents('delivery-out check-out',False,False)
 if role in ['IT & Infrastructure Manager','IT & Infrastructure Officer']:
  tickets(role.endswith('Manager'));projects(role.endswith('Manager'));module('portal.helpdesk','create edit');add('manage_helpdesk')
  if role.endswith('Manager'):
   management();add('users');module('portal.users','view edit reset_password deactivate manage_departments')
 if role=='QMR':
  for k in ['sops','jobdescriptions','kpis']:module('portal.'+k,'create edit upload download share')
  add('manage_sops','manage_jobdescriptions','manage_kpis','manage_training');module('portal.training','create edit upload download approve reject');module('portal.minutes','create edit publish manage acknowledge export');module('is.history','view export');module('is.reports','view print export')
 if role=='Marketing Communication Specialist':
  add('content','brands','catalogue_manager');module('portal.content','create edit publish upload');module('portal.brands','create edit');module('portal.catalogue','view create edit import sync');add('portal.catalogue.enquiries');module('crm.brands','view create edit');module('crm.products','view create edit')
 if role in ['Managing Director','Operations Director']:
  management();sales(True);logistics(True);purchasing(True);financial(True)
  for k in ['instruments','jobs','movements','parts','replacements','contracts']:module('service.'+k,'view print export')
  add('service.export','application_service.view','application_service.view_all','application_service.export','application_service.print','application_service.audit')
  module('budget.approvals','director_approve');add('manage_leave_entitlement','approve_car','approve_room','booking_approvals','approve_incentives','manage_incentives');module('portal.cars','approve reject');module('portal.rooms','approve reject');module('portal.leavebalance','create edit');module('portal.appraisals','create edit');module('portal.onboarding','create edit');module('portal.hrprofiles','create edit');module('portal.demos','approve reject');module('portal.minutes','create edit publish manage acknowledge export');module('portal.users','view');module('is.approval','view export')
 return sorted(g)

def responsibility(role):
 if role=='System Admin':return 'Maintain accounts, roles, integrations, backups and application configuration. Full system administration. Review audit records and separate operational approvals from administration.'
 tier='Manager / supervisor' if any(w in role for w in ['Manager','Supervisor']) else 'Director' if role in ['Managing Director','Operations Director','Business Director'] else 'Contributor'
 area=('engineering service, instrument records, service stock and customer service reports' if role.startswith('Service') else 'application jobs, customer training, application reports and feedback' if role.startswith('Application') else 'accounting, invoices, receipts, payment processing, financial entries and reconciliation' if role.startswith('Accounting') else 'purchasing, suppliers and procurement documentation' if 'Purchas' in role or 'Procurement' in role else 'inventory, delivery, stock verification and logistics' if role in ['Inventory Officer','Messenger & Delivery','Messenger & Delivery Supervisor','Operation Manager'] else 'quality documents, SOPs, training evidence and acknowledgements' if role=='QMR' else 'user support and infrastructure coordination' if role.startswith('IT &') else 'sales, customer visits, quotations, pipeline, product activity and follow-up' if role.startswith(('Sales','Product','Business')) else 'marketing content, brands, catalogue and commercial activity' if role.startswith('Marketing') else 'company operational oversight and authorized financial review' if role in ['Managing Director','Operations Director'] else 'billing follow-up, customer receipts and outstanding balances' if role=='Bill Collector' else 'administrative coordination, schedules, documents and assigned work')
 return tier+' responsibility for '+area+'. '+('Review and coordinate the functional team using the same authorization tier for supervisors and managers. ' if tier=='Manager / supervisor' else '')+'All users retain personal requests, profile, calendar and shared employee resources. Record-level ownership, assigned reporting lines and workflow checks still apply. No authority to approve one’s own work is added by this preset.'
