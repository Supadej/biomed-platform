"""Role-aware online manual: authenticate and filter content before returning it."""
import json,re,hashlib,datetime
from pathlib import Path
from html.parser import HTMLParser
import permissions_policy as policy
ROOT=Path(__file__).parent
class Table(HTMLParser):
 def __init__(self):super().__init__();self.rows=[];self.row=None;self.cell=None
 def handle_starttag(self,t,a):
  if t=='tr':self.row=[]
  if t in ['td','th']:self.cell=''
 def handle_data(self,d):
  if self.cell is not None:self.cell+=d
 def handle_endtag(self,t):
  if t in ['td','th'] and self.cell is not None:self.row.append(self.cell);self.cell=None
  if t=='tr' and self.row:self.rows.append(self.row);self.row=None
p=Table();p.feed((ROOT/'document-flow-guide.html').read_text());DOCUMENTS={r[0].lower():r[1:] for r in p.rows if len(r)==4}
# Purpose, fields to review, lifecycle and a module-specific operational note.
DETAILS={
'portal.announcements':('Read company notices and acknowledge those addressed to you.','Title|Publication date|Audience|Attachments|Acknowledgement','Find the current notice|Read the content and supporting files|Check your acknowledgement state','Acknowledgement is a separate action from opening a notice.'),
'portal.requests':('Track an internal request through the configured reporting workflow.','Request type|Title|Dates|Reason|Attachments|Approval stage','Choose the correct request type|Review the request and evidence|Follow the current decision stage|Read returned comments','Use the matching request type; travel and leave are different processes.'),
'portal.expenses':('Record supported expenses and follow reimbursement review.','Category|Expense dates|Line amounts and currency|Receipts|Decision','Review each expense line|Check receipt evidence and totals|Follow the decision and processing state','Do not submit the same receipt twice.'),
'portal.payments':('Review authorized requests awaiting accounting processing.','Employee|Request type|Approval|Amount|Payment reference and date','Filter the queue|Expand the source request|Verify authorization and amount|Review the processing state','An approved request and a completed payment are different stages.'),
'portal.cars':('Book a company vehicle without conflicting reservations.','Vehicle|Start / end|Driver|Purpose|Approval','Review availability|Choose the correct vehicle and period|Review the booking decision|Check the confirmed reservation','Check the vehicle and time before travel.'),
'portal.rooms':('Reserve a suitable room for a meeting.','Room|Start / end|Purpose|Responsible employee','Review availability|Choose the room and time|Review authorization|Check the confirmed booking','Check existing reservations before creating a duplicate.'),
'portal.visits':('Plan customer visits and record outcomes with clear follow-up.','Representative|Visit date & time|Duration: 1–24 hours|Collaborators|Customer type/status|Products|Discussion and follow-up','Review the customer and schedule|Record the discussion and outcome|Assign a specific next action and due date|Use Analysis and the multi-select filters to review activity','Calendar linkage is optional. Select real list entries; typing a search value alone does not establish a link.'),
'portal.demos':('Track demonstration instruments and customer evaluation.','Owner|Customer|Product|Instrument / ID|Start / end|Evaluation and next action','Review the instrument and placement period|Check authorization|Record the evaluation result|Review the next action','Use the same demonstration reference when recording progress.'),
'portal.tenders':('Track manual and linked quotation/tender activity together.','Manual / Linked source|Reference|Customer|Owner|Product|Value|Status|Follow-up','Locate the quotation or tender|Check its source|Review next action and due date|Use Analysis to investigate status and value','Manual and Linked entries share the register and follow-up controls.'),
'portal.pipeline':('Track opportunities, expected outcome and next action.','Manual / Linked source|Customer|Owner|Product|Value|Stage|Expected close|Follow-up','Review the opportunity|Check its source and stage|Review follow-up and due date|Use Analysis for value and outcome trends','A stage change does not approve a source commercial transaction.'),
'portal.sales':('Review sales performance and underlying invoice references.','Employee|Period|Customer|Product|Linked invoice value','Set the reporting scope|Review the summary|Trace values to source invoices|Use Analysis to compare periods','Compare like-for-like periods and currency scopes.'),
'portal.incentives':('Review incentive rules, performance basis and authorization.','Scheme|Period|Eligible employees|Target|Calculation|Decision','Choose the scheme and period|Review the calculation basis|Check entitlement evidence|Review approval and processing','Read the scheme rules before interpreting a calculated entitlement.'),
'portal.user_profile':('Keep your own contact details and password current.','Picture|Mobile|Email|DOB|LINE ID','Open your profile|Review the information visible to colleagues|Review the saved result','Use your current password when the password-change controls request it.'),
'portal.user_library':('Find basic information for active colleagues.','Picture and name|Mobile|Email|DOB|LINE ID','Search the active employee|Review the basic contact information|Use the relevant contact method','Ask the colleague to update outdated information in their own profile.'),
'portal.users':('Manage staff accounts and reporting assignments.','Name and email|Department|Role|Reports to|Active state','Find the correct employee|Review department, role and manager|Check the resulting account state','Initial password and confirmation must match. Editing opens beneath the selected row.'),
'portal.roles':('Maintain role responsibilities and individual function/action grants.','Role|Responsibility description|Application access|Module and action permissions','Select the role|Review its responsibility description|Review the precise action grants|Verify the affected user experience','This manual reads these saved settings. Role names alone do not grant access.'),
'portal.hierarchy':('Review reporting relationships used by internal workflows.','Employee|Department|Reports to|Reporting chain','Locate the employee|Review their manager|Check the reporting chain','Resolve missing or circular reporting relationships with the authorized administrator.'),
'portal.hrprofiles':('Review permitted employee employment information.','Employee|Employment dates|Education|Contact details|Appraisal','Find the permitted profile|Check employment and personal details|Review supporting information','Employee records remain subject to your permitted scope.'),
'portal.leavebalance':('Review entitlement and apply for leave.','Category|Start / end|Weekdays|Reason|Balance','Review entitlement|Choose the category and dates|Check weekdays and evidence|Follow the decision','Apply for leave and Leave entitlement are separate tabs.'),
'portal.onboarding':('Track onboarding, offboarding and internal role changes.','Employee|Process|Effective date|Checklist|Responsible people','Choose the employee process|Review the assigned checklist|Check evidence and completion|Review the final state','Promotion or transfer does not necessarily end employment.'),
'portal.training':('Review training material, attendance and competency evidence.','Topic|Trainer|Date|Participants|Material|Assessment','Find the training|Read the material and schedule|Check participation requirements|Review completion evidence','Attendance and demonstrated competency are different evidence types.'),
'portal.appraisals':('Review performance against the appraisal criteria.','Employee|Period|Criteria and weight|Score|Comments','Choose employee and period|Review criteria|Review scores and evidence|Review feedback and decision','Use the configured criteria, not an unrelated period’s assessment.'),
'portal.minutes':('Read meeting minutes and track acknowledgements.','Meeting/date|Attendees|Minutes|Attachments|Actions|Audience','Locate the meeting|Read minutes and attachments|Review assigned actions|Check acknowledgement','Read the current revision before acknowledging.'),
'portal.tasks':('Track assigned work and due dates.','Task|Owner / assignee|Due date|Status','Review open work|Prioritize by due date|Read the required action|Review completion','Keep the next responsible action clear.'),
'portal.objectives':('Review assigned targets and progress.','Objective|Owner|Target|Due date|Progress','Read the objective|Check its measure|Review progress|Discuss variances','A target needs a defined measure and period.'),
'portal.helpdesk':('Track an internal support issue.','Issue|Requester|Priority|Status|Response','Describe the problem|Provide reproducible details|Review the response|Check resolution','Include expected and observed results without passwords.'),
'portal.content':('Maintain public website content.','Page|English / Thai content|Images|Links|Publication','Locate the section|Review both language versions|Check links and files|Review the resulting website','Preview public content before considering the change complete.'),
'portal.brands':('Maintain brand information and public presentation.','Brand|Product grouping|Logo|Description|More information HTML','Locate the brand|Review identity and logo|Check formatted information|Review the website presentation','Use consistent shared brand names.'),
'portal.catalogue':('Maintain catalogue records and publication.','Catalogue number|Name|Brand|Description|Publication','Find the item|Review its information|Check publication state|Review the public result','Publication is distinct from an internal catalogue record.'),
'portal.catalogue.enquiries':('Review customer enquiry baskets and linked follow-up.','Customer contact|Requested items|Received date|Linked lead','Open Received Enquiries|Read the request|Review the linked follow-up|Check next-action ownership','Do not create duplicate follow-up solely because a card is outside a filter.'),
'application_service':('Schedule specialist support and retain work, feedback and follow-up.','Application job ID|Optional topic|Type and specialist|Customer and products|Start / end|Optional instrument|Work, result and follow-up','Review the customer and product scope|Record actual work and result|Check follow-up and due date|Review feedback and related records','Job IDs use BMDASDD-MM-YY/# and are assigned on save. Completed jobs require Work performed and Result. Signature is optional.'),
'service.jobs':('Record engineering work with instrument and customer traceability.','Instrument / serial|Job ID|Type, engineer and dates|Description and diagnosis|Action taken and result|Parts|Feedback and optional signature','Find the job and instrument|Review diagnosis|Review actions and parts|Review outcome and next maintenance','Select an actual instrument from search results. Job IDs are assigned on save; do not invent a duplicate reference.'),
'service.instruments':('Keep instrument serial identity, placement and maintenance traceable.','Serial / alias|Brand/model|Customer/location|Warranty|Maintenance dates','Find the serial|Review placement|Review service and movement history|Check upcoming maintenance','Search by serial alias when the primary serial is not recognized.'),
'service.movements':('Record an instrument relocation.','Instrument|From / to|Date|Engineer|Reason','Identify the serial|Review origin and destination|Check the movement date|Review the history','A movement retains the same instrument identity.'),
'service.parts':('Declare product-backed service spare parts.','Biomed IS product|Catalogue number|Unit|Brand/model compatibility','Locate the part|Review catalogue number and unit|Check compatibility|Use the declared part','If a part is missing, check its product-backed declaration first.'),
'service.replacements':('Trace parts used on service jobs.','Job|Instrument|Part|Quantity|Date|Stock reference','Find the replacement|Check job and instrument|Review consumed quantity|Review stock and billing references','Avoid recording the same part usage twice.'),
'service.contracts':('Review instrument warranty and contract coverage.','Instrument|Contract|Status|Start / end|Coverage|Visits','Find the instrument coverage|Review dates|Review obligations|Review the contract state','Check coverage before interpreting a job as chargeable.'),
'is.service-inventory':('Control engineer-held parts, usage and discrepancies.','Engineer|Part|Quantity|Request/return|Service job|Count variance','Review engineer balance|Review requests, returns and usage|Match the physical count|Investigate discrepancies and billing references','Check the exact engineer and part when stock is insufficient. Counts consolidate holdings; discrepancies need justification.'),
'is.outstanding':('Track remaining customer obligations on original borrowings.','Customer|Borrowing|Product|Issued|Returned / purchased|Remaining|Age','Filter the borrowing|Expand details|Review clearing links|Follow up the remaining balance','Returns and purchase settlements must link to the original borrowing.'),
'crm.events':('Plan visits and meetings with responsible employees.','Title|Start / end|Responsible employee|Collaborators|Products|Notes and attachments','Choose dates; initial From/To use today|Review events and the colour legend|Open an event|Review follow-up','Each user has a distinct calendar colour. Review the responsible person as well as the date.'),
'crm.tickets':('Track customer support work and related jobs.','Title/customer|Priority|Owner|Stage|Problem / solution|Linked jobs','Find the ticket|Review priority and owner|Review related work|Check solution and remaining action','One support ticket can refer to several jobs. Ticket stage is not commercial authorization.'),
'crm.projects':('Organize activities within project folders.','Folder|Stages|Activity|Owner|Due date','Choose the project folder|Review stages|Open the activity|Review next action','Select the right folder before assuming an activity is missing.'),
'crm.activities':('Track assigned activity within a project.','Project/stage|Activity|Owner|Due date|Outcome','Locate the project|Review the activity|Review the stage|Check next action','Use the same project context when reviewing progress.'),
'crm.leads':('Track sales actions through configured opportunity stages.','Customer/product|Owner/territory|Source|Stage/value|Target|Next action','Review the board|Check owner and source|Review next action|Compare activity with target','Review source links before adding a duplicate lead.'),
'budget.products':('Set annual and monthly revenue targets.','Fiscal year|Plan/source type|Brand or service|Cost center|Annual target|12 monthly values','Choose year and cost center|Review the target line|Compare annual and monthly distribution|Review plan and performance','Always review the fiscal year before changing amounts.'),
'budget.ledger':('Record actuals and commitments against the correct plan.','Actual / commitment|Cost center|Budget line|Month|Reference|Amount','Choose entry type|Review budget line and period|Check reference and amount|Review the resulting variance','A commitment is not a payment. Keep the correct entry type.'),
'budget.approvals':('Follow the configured planning review stages.','Year/scope|Submission|Reviewer|Stage|Comments','Review scope and validation|Check the current stage|Review the decision|Read returned comments','Only the granted review stage is available to your account.'),
'budget.express':('Stage and review Express accounting exports.','Report/company|As-of date|Encoding/separator/sheet|Mapping|Staged rows','Choose the file and mapping|Preview file|Map columns and inspect errors|Review the batch and reconciliation','Do not apply an unreviewed batch simply to clear a preview error.'),
'budget.finance':('Review aging, cash forecast and monthly close controls.','Currency|As-of date|Balances|Cash assumptions|Close checklist','Choose the view|Review date and currency|Check source balances|Review exceptions','Forecast assumptions and verified opening balances are different inputs.'),
'budget.periods':('Review period locks and allowed changes.','Year|Period|Lock|Reason','Locate the period|Review its lock state|Check the requested change|Review the resulting history','Do not unlock a period simply to bypass a validation issue.'),
'system.database':('Back up and recover data through controlled administration.','Backup/date|Scope|Validation|Restore/reset|Audit','Identify the operation|Review scope and recovery point|Read the confirmation|Verify the result','A project source ZIP is not a database backup. Keep a verified recovery copy before destructive work.')}
FAMILY={
'budget':('Review the selected financial planning function.','Fiscal year|Cost center|Category or source|Monthly and annual values|Actual / commitment|Variance','Choose fiscal year and scope|Review underlying lines|Compare monthly/annual totals|Investigate differences in source records','Check period locks and approval stage before changing a value.'),
'crm':('Review the customer relationship reference and its linked activity.','Record identity|Owner|Customer relationship|Source reference|Status','Locate the reference|Review ownership and relationships|Check linked records|Review the next action','Reference modules may be reached through parent records and selectors, rather than a separate menu.'),
'is':('Review the operational reference and its source records.','Reference|Product or party|Warehouse / lot where applicable|Status|Linked records','Select the relevant scope|Review the record|Trace the source|Review downstream effects','Use the exact reference, product and location when investigating a discrepancy.'),
'portal':('Review work and information shared within your permitted scope.','Record title|Owner|Period/date|Sharing|Evidence and status','Locate the record|Review current information|Check supporting evidence|Review the resulting state','If information is missing, check filters, assignment and sharing before creating a duplicate.'),
'service':('Coordinate permitted instrument service records and configuration.','Instrument|Service reference|Responsible employee|Date|History','Choose an available service tab|Review the record|Check linked history|Review the next responsible action','Your function-level action grants control the available buttons.'),
'ai':('Use or configure the assistant within your permitted scope.','Provider|Configuration state|Question|Response','Check provider availability|Ask a focused question|Review the response against the actual record|Validate before acting','Never include secret keys or passwords in a question; AI output still needs verification.')}
LABELS={'create':'Create','edit':'Edit','view':'Read records','submit':'Submit for review','approve':'Approve','reject':'Return / reject','derive':'Create linked document','print':'Print / Email report','export':'Export','delete':'Remove','view_all':'Legacy broad-view action (record visibility still applies)','calendar':'Link Calendar','manage_references':'Manage reference list','request':'Request stock','return':'Return / correction','consume':'Record parts usage','password':'Change password','reset_password':'Reset staff password','deactivate':'Change active state','assign':'Assign responsibility','audit':'Read audit history','progress':'Update progress','reverse':'Void / reverse','department_approve':'Department review','finance_approve':'Finance review','director_approve':'Director review'}
MODULES={}
for permission in policy.CATALOG['permissions']:
 if not permission['module'].startswith('access.'):MODULES.setdefault(permission['module'],[]).append(permission)
MODULES['portal.dashboard']=[{'key':'dashboard','label':'Overview','action':'view'}]
def visible(module,perms):
 if module.startswith('is.') and 'is_view' not in perms:return False
 if module.startswith('budget.') and 'budget_view' not in perms:return False
 if module.startswith('crm.') and 'crm_view' not in perms:return False
 if module.startswith('service.') and 'service.view' not in perms:return False
 if module.startswith('portal.'):
  key=module.split('.')[1]
  if key=='catalogue':
   if not {'catalogue_manager','portal.catalogue.view'}&perms:return False
  elif key not in perms:return False
 if module=='service.references' and 'service.instruments.view' not in perms:return False
 rows=MODULES[module];view=module+'.view'
 if any(p['key']==view for p in rows):return view in perms
 return module.startswith('portal.') or any(p['key'] in perms for p in rows)
def action_steps(module,action,title):
 texts={
'view':['Open '+title+' and check the date, owner and search filters.','Use Details to expand a record and review its identity, source and state.','Clear filters before assuming an older record is missing.'],
'create':['Choose New / Create in this function. Select actual entries from reference-list search results.','Complete required fields, review dates, quantities/amounts and ownership, then Save once.','Wait for confirmation and note the assigned reference. Check the saved record before retrying after a connection problem.'],
'edit':['Locate the exact record and choose Edit.','Change the permitted fields and Save. Resolve displayed validation errors without discarding entered values.','If someone else changed the record, refresh and review that version before retrying.'],
'submit':['Review the draft/scope and supporting evidence.','Use Submit / Submit for approval.','Confirm the next review stage and monitor returned comments.'],
'approve':['Expand the full record and review the request, sources and supporting values.','Choose Approve only within your decision authority.','Check the resulting authorization and audit trail; controlled downstream effects may follow.'],
'reject':['Read the record and identify the correction needed.','Choose Return / Reject and enter the required reason.','Confirm the recorded decision for the owner to correct and resubmit.'],
'print':['Open the saved record and choose Print report or Email report. Select PDF or HTML.','For printing, review the prepared report. For email, use Email with attachment and choose an available email app.','If sharing is unavailable, download the report and attach it manually. Open email app does not attach automatically. Check recipient and attachment before sending.'],
'export':['Set the intended filters and review the displayed scope.','Choose Export / Export CSV and inspect the downloaded file.','Handle exported personal and business information according to company policy.'],
'derive':['Open the approved source and choose the offered linked-document action.','Review inherited party, source and remaining eligible quantities.','Save the new draft and review its own authorization; creating a draft is not a stock posting.'],
'progress':['Open the record’s workflow panel. Read authorization and operational progress separately.','Select an available value and Save progress, with a reason where required.','For calculated progress, inspect the linked transactions instead of overwriting a summary.'],
'reverse':['Review downstream documents and the original posting effect.','Use Void / Reverse, enter a reason and resolve blocked dependencies first.','Verify the reversing effect and audit trail; do not create an unrelated opposite record to hide the error.'],
'calendar':['Enable Add / update in Staff Portal calendar where your form offers it.','Review the Calendar date and responsible person. The date defaults to today and remains selectable.','Save the job and check its linked event; changing the job start date does not overwrite a separately selected Calendar date.'],
'password':['Open User Profile password controls.','Enter current password, new password and matching confirmation.','Save and sign in again if requested. Keep the password private.'],
'reset_password':['Find the correct staff row and choose Reset password.','Enter and confirm the replacement using the displayed requirements.','Complete reset and communicate securely using company procedure. Existing sessions may require sign-in again.'],
'manage_references':['Open Customer reference list in Application Service.','Add the institution or remove an inactive choice. Historical jobs retain their reference.','Select an active customer in the job form before saving.'],
'request':['Open Service Inventory → New Request. Choose the engineer and product-backed part.','Enter the quantity/source details and submit for the configured decision.','Review the approved engineer balance before consuming stock.'],
'consume':['Open the service job parts controls and select the supplying engineer.','Choose the exact product-backed part, available holding and quantity.','Save and review Track Record; do not record the same consumption twice.'],
'acknowledge':['Read the current notice/minutes and its attachments.','Use Acknowledge when your account is in the required audience.','Check the recorded acknowledgement. Opening the title alone is not acknowledgement.'],
'view_all':['Record visibility in Roles & permissions is the authoritative record limit; this legacy grant does not override it.','Use owner/date filters to review the intended scope.','It does not grant editing or access to another function.']}
 if action in ['create','edit'] and module in ['application_service','service.jobs']:
  app=module=='application_service'
  return ['Open '+('Application Service → Records → New application job' if app else 'Instrument Service → Service jobs → Create')+' or the correct row’s Edit action.','Choose '+('Service type, eligible specialist, status and Start date & time.' if app else 'Instrument / serial from search results, job type, engineer, dates and status.'),'Select the customer reference and review products / location. '+('Topic and instrument are optional.' if app else 'Review the instrument’s serial and linked customer.'),'Record '+('Purpose, Work performed, Result / outcome, follow-up and due date. Completed jobs need Work performed and Result.' if app else 'Description, diagnosis, action taken, result, parts used and follow-up.'),'Expand optional report feedback/signature information when needed. A captured signature needs the actual customer name and acknowledgement; a changed signed report may require a new signature.','Review optional Calendar/ticket controls offered to your role. Save once, read the confirmation and note the generated reference. Clear date filters if it saved outside the visible range.']
 if action=='configure' and module=='system.database':return ['Open Database administration and the administrator test self-approval control.','Change this testing option only for an intentional test; it applies to System Admin self-approval.','Disable the test option before ordinary live operation and review the audit record.']
 if action=='restore' and module=='system.database':return ['Choose a full-system Biomed database backup ZIP, not the project source ZIP.','Run validation preview and review the backup date, table counts and affected systems.','Enter the required reason and RESTORE ALL DATA confirmation only after retaining a recovery copy. Verify accounts, records and balances after restore.']
 if action=='reset' and module=='system.database':return ['Retain a verified recovery copy and identify the exact affected data scope.','Choose Archive & reset and read the confirmation carefully. Enter a reason and ARCHIVE AND RESET only when intended.','Verify the archive and resulting record scope before resuming entry.']
 if action=='create' and module=='portal.users':return ['Open User directory → Add staff account.','Enter name and unique company email; choose department, role and Reports to.','Enter Initial password and Confirm initial password; they must match.','Create the account and verify its active state and reporting line.']
 if action=='visibility' and module=='portal.roles':return ['Open Staff Portal → Roles & permissions and select a role.','In Record visibility choose a limit for each function, then Save record visibility. Existing action grants are still required.','Own includes the responsible employee; Own + assigned adds explicitly assigned records. Reporting team includes all levels of Reports to. Department uses the employee department. All includes unassigned legacy records.','Verify Reports to and departments in User directory. Use separate settings for shared reference lists. New requests use the updated limit immediately.','If an older unassigned record disappears, ask System Admin to review responsibility or the applicable All setting. Do not recreate the transaction.']
 if action=='edit' and module=='portal.roles':return ['Select the role in Roles & responsibilities.','To change its name, enter Role name and select Rename role. Permissions, responsibilities and user assignments are preserved.','To remove it, choose a Replacement role if users are assigned, then select Delete role and confirm. Reassignment also requires staff role assignment permission; affected users sign in again.','System Admin and the default Employee role cannot be renamed or deleted. Clone a built-in role to create a custom one.','Maintain the responsibility description and precise application/module/action grants using the offered controls.','Refresh access in this manual to see the resulting responsibilities and function instructions.']
 if action in ['department_approve','finance_approve','director_approve','review']:return ['Open the submission/batch in your review stage.','Review scope, validation, values and comments.','Record the offered decision and verify the resulting stage.']
 return texts.get(action,['Locate the '+LABELS.get(action,action.replace('_',' '))+' control in '+title+'.','Review the exact record, scope, validation and confirmation before applying the action.','Verify the result and history. Ownership, linked-record and approval rules still apply.'])
def project(actor,permissions,portal):
 perms=set(permissions);chapters=[]
 for module,rows in MODULES.items():
  if not visible(module,perms):continue
  family=module.split('.')[0];key=module.split('.',1)[-1];title=rows[0]['label'].split(' — ')[0]
  if family=='budget':title=policy.CATALOG['budgetTabs'].get(key,title)
  if family=='is':title=policy.CATALOG['transactions'].get(key,title)
  if family=='crm':title=policy.CATALOG['crmModules'].get(key,{}).get('label',title)
  detail=DETAILS.get(module,FAMILY.get(family,FAMILY['portal']));purpose,fields,flow,note=detail
  if family=='is':
   aliases={'waiting-purchase':'waiting to be purchased','stock-count':'stock count','cycle-count':'stock count','warehouse-move':'warehouse transfer'};doc=DOCUMENTS.get(aliases.get(key,title.lower().rstrip('s')) ) or DOCUMENTS.get(title.lower())
   if doc:purpose,document_flow,effect=doc;flow='Review the source and authorization|Review quantities and values|Review the linked transaction history';note=effect
   else:document_flow=''
  else:document_flow=''
  system={'is':'Biomed IS','budget':'Financial','crm':'CRM','service':'Instrument Service','system':'Administration','ai':'Assistant'}.get(family,'Application Service' if module=='application_service' else 'Staff Portal')
  actions=[]
  for item in rows:
   if item['key'] not in perms:continue
   if family=='service' and item['action'] in ['create','edit','delete'] and 'service.edit' not in perms:continue
   if family=='service' and item['action']=='export' and 'service.export' not in perms:continue
   if item['key']=='service.import' and 'service.manage' not in perms:continue
   if item['key']=='application_service.calendar' and not {'crm_view','crm.events.view'}<=perms:continue
   actions.append({'key':item['key'],'label':LABELS.get(item['action'],item['action'].replace('_',' ').capitalize()),'steps':action_steps(module,item['action'],title)})
  if not any(a['key'].endswith('.view') for a in actions):actions.insert(0,{'key':None,'label':'Read the available reference','steps':action_steps(module,'view',title)})
  href=''
  if family=='is':href='/biomed-is.html?function='+key
  elif family=='budget':href='/biomed-budget.html'+('?tab='+key if key in ['is_bridge','approvals','finance','express'] else '')
  elif family=='portal' and (key in policy.CATALOG['portalModules'] or key=='dashboard'):href='/?portal=1&module='+key
  elif module=='application_service':href='/?portal=1&module=application_service'
  elif family=='service':href='/?portal=1&module=instrument_service'
  elif module=='system.database':href='/database-admin.html'
  elif family=='crm' and key in ['events','tickets','projects','activities','leads']:href='/?portal=1&module='+{'events':'calendar','tickets':'external_helpdesk','projects':'projects','activities':'projects','leads':'sales_plan'}[key]
  if module in policy.visibility.modules() and policy.visibility.contextual(permissions):note+=' Record visibility: '+policy.visibility.SCOPES[policy.visibility.scope(permissions,module)]+'. Action permissions remain required.'
  chapters.append(dict(id=module,title=title,system=system,purpose=purpose,fields=fields.split('|'),workflow=flow.split('|'),documentFlow=document_flow,note=note,actions=actions,href=href))
 profile=next((u for u in portal.get('users',[]) if str(u.get('id'))==str(actor[4])),{});description=portal.get('roleDescriptions',{}).get(actor[3],'');types=[];keys=[a['key'] or '' for c in chapters for a in c['actions']]
 if any(k.endswith(('.create','.edit','.consume','.perform')) for k in keys):types.append('Operational contributor')
 if any(k.endswith(('.approve','_approve','.review','.reject')) for k in keys):types.append('Reviewer / approver')
 if any(k.endswith(('.assign','.manage','.configure','.deactivate')) for k in keys):types.append('Coordinator / administrator')
 revision=hashlib.sha256(json.dumps([actor[0],actor[2],actor[3],sorted(perms),description,profile.get('department',''),portal.get('roleRecordScopes',{}).get(actor[3],{}),'73.1'],sort_keys=True).encode()).hexdigest()[:20]
 return {'version':'73.1','revision':revision,'user':{'id':str(actor[0]),'name':actor[2],'role':actor[3],'department':profile.get('department',''),'responsibility':description,'types':types or ['Reader']},'chapters':chapters,'systems':list(dict.fromkeys(c['system'] for c in chapters))}
def handle(h,connect,session,permissions):
 actor=session(h)
 if not actor:return h.reply(401,{'error':'Sign in to open your manual.'})
 with connect() as c:
  row=c.execute("SELECT value FROM workspace WHERE key='biomed_portal_v33_clean'").fetchone();portal=json.loads(row[0]) if row else {}
 return h.reply(200,project(actor,permissions(actor),portal))
