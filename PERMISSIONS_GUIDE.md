# Roles and permissions

Open Staff Portal → Website & Administration → Roles & responsibilities, using the System Administrator account.

There are 583 explicit grants across Staff Portal/application access (182), Biomed IS (273), and Financial (128). The editor groups them by application and function, with an individual checkbox for each action, a search box, group enable/clear controls, editable responsibilities, empty new roles, and role cloning.

## Configure a role

1. Choose an existing role or create/clone one.
2. Enable the relevant Application access or Staff Portal module access.
3. Enable each function's View permission where offered, then its permitted actions. An action grant does not automatically grant its View permission.
4. Assign the role through User directory. Refresh open application pages after changing access.

IS example: enable `is_view` and `is.quotation.view` to see the quotation register. Add quotation Create, Edit and Submit to prepare quotations; Approve and Reject are independent. Invoice, stock, purchasing and master data rights remain separate. Custom role names work with these permissions.

Budget example: enable `budget_view`, Target and revenue View/Edit, and Fiscal years Switch to plan revenue without granting COGS, personnel costs, actual postings or approvals. Department, Finance and Director approvals are separate grants. Approval stages still proceed in order.

Portal requests use both their function actions and existing request-type approval scope: travel, budget request, leave, car, room or general approval. Existing owner, reporting hierarchy and document-sharing rules still determine which records can be acted on. Management scope flags for training, documents and team workflows are also listed in the editor.

## Included sample roles

- IS Quotation Clerk: quotation drafts, submission, print and export.
- Budget Revenue Planner: revenue planning with other schedules restricted.
- Budget Finance Reviewer: financial schedule review and the Finance approval stage.

These are templates; existing sample account assignments are preserved. Administrators can assign any template or clone and customize it.

## Enforcement and persistence

The server validates changes to IS transactions/master data, financial schedules, approval transitions, and Portal workspace records. A crafted direct save cannot grant itself new roles or perform a denied action. Workspace reads omit hidden transaction types and schedules; hidden records and masked amounts are preserved when an authorized user saves a partial workspace. Budget reports therefore total only the schedules the role can view.

Full IS exports/backups and full Budget backups intentionally include all workspace records. Grant backup/restore access only to roles that should have that full data access. IS product/customer/supplier references needed by permitted transaction forms remain available as reference data; the Master Data view permission controls the maintenance screen. This is function-level access, not arbitrary field-level masking of every reference record. Existing detailed reporting-tree and document-sharing behavior is retained.

IS reconciliation also requires IS application access and Invoice view. Quotation follow-up and order generation require their Portal pipeline and corresponding IS quotation/order permissions.

On first start, old broad IS/Budget grants are expanded once into explicit actions. Saved removals are not re-added on page load or restart. Password hashes, accounts and operational records are retained when using an existing database file.

## Storage and deployment

The local app uses SQLite. The SQL2012_Migration folder contains the previously provided schema and transfer starter; it does not provide a SQL Server runtime adapter. Approval amount limits, immutable auditing and full production row/department isolation still require implementation and staging validation before operational use.

Uploaded document binaries retain the existing browser file storage. The workspace records, role matrix and responsibilities are in SQLite; this permissions update does not migrate existing browser attachment binaries.

## Permission catalog

| Group | Function | Action | Key |
| --- | --- | --- | --- |
| Application access | Biomed IS application access | access | `is_view` |
| Application access | Financial application access | access | `budget_view` |
| Staff Portal · Module access | Human Resources — manage leave entitlements | access | `manage_leave_entitlement` |
| Staff Portal · Module access | Finance — view payment processing | access | `payments` |
| Staff Portal · Module access | Finance — process payments | access | `process_payments` |
| Staff Portal · Module access | Sales — view incentive schemes | access | `incentives` |
| Staff Portal · Module access | Sales — manage incentive schemes | access | `manage_incentives` |
| Staff Portal · Module access | Sales — approve incentive claims | access | `approve_incentives` |
| Staff Portal · Module access | Finance — approve expense claims | access | `approve_expense` |
| Staff Portal · Module access | Sales — manage targets and actuals | access | `manage_sales` |
| Staff Portal · Module access | Sales — performance, visits, pipeline and quotations | access | `sales` |
| Staff Portal · Module access | People — objectives and progress | access | `objectives` |
| Staff Portal · Module access | Administration — reporting hierarchy | access | `hierarchy` |
| Staff Portal · Module access | Requests — travel, leave and general requests | access | `requests` |
| Staff Portal · Module access | Facilities — company vehicle bookings | access | `cars` |
| Staff Portal · Module access | Facilities — meeting room bookings | access | `rooms` |
| Staff Portal · Module access | Operations — tasks and action tracking | access | `tasks` |
| Staff Portal · Module access | Facilities — support tickets | access | `helpdesk` |
| Staff Portal · Module access | Human Resources — training and competency | access | `training` |
| Staff Portal · Module access | Human Resources — employee profiles | access | `hrprofiles` |
| Staff Portal · Module access | Human Resources — leave balances | access | `leavebalance` |
| Staff Portal · Module access | Human Resources — performance appraisals | access | `appraisals` |
| Staff Portal · Module access | Human Resources — onboarding, role changes and offboarding | access | `onboarding` |
| Staff Portal · Module access | Sales — quotation follow-up and pipeline | access | `pipeline` |
| Staff Portal · Module access | Sales — customer visits | access | `visits` |
| Staff Portal · Module access | Sales — product demonstrations | access | `demos` |
| Staff Portal · Module access | Sales — tender and quotation tracking | access | `tenders` |
| Staff Portal · Module access | Quality — SOP register | access | `sops` |
| Staff Portal · Module access | Human Resources — job descriptions | access | `jobdescriptions` |
| Staff Portal · Module access | Management — KPI register | access | `kpis` |
| Staff Portal · Module access | Website — content publishing | access | `content` |
| Staff Portal · Module access | Website — brand management | access | `brands` |
| Staff Portal · Module access | Administration — user directory | access | `users` |
| Staff Portal · Module access | Administration — roles and permissions | access | `roles` |
| Staff Portal · Module access | Administration — workspace settings | access | `settings` |
| Staff Portal · Module access | Company — announcements | access | `announcements` |
| Staff Portal · Module access | Company — forms library | access | `forms` |
| Staff Portal · Module access | Company — shared resources | access | `resources` |
| Staff Portal · Module access | Finance — expense claims | access | `expenses` |
| Staff Portal · Module access | Requests — approve travel | access | `approve_travel` |
| Staff Portal · Module access | Financial — approve requests | access | `approve_budget` |
| Staff Portal · Module access | Human Resources — approve leave | access | `approve_leave` |
| Staff Portal · Module access | Facilities — approve vehicle bookings | access | `approve_car` |
| Staff Portal · Module access | Facilities — approve meeting rooms | access | `approve_room` |
| Staff Portal · Module access | Requests — approve general requests | access | `approve_general` |
| Staff Portal · Module access | Administration — all approval queues | access | `approve_all` |
| Staff Portal · Module access | Operations — manage team tasks | access | `manage_tasks` |
| Staff Portal · Module access | Facilities — manage support tickets | access | `manage_helpdesk` |
| Staff Portal · Module access | Quality — manage SOPs | access | `manage_sops` |
| Staff Portal · Module access | Human Resources — assign training | access | `manage_training` |
| Staff Portal · Module access | Human Resources — manage job descriptions | access | `manage_jobdescriptions` |
| Staff Portal · Module access | Management — manage KPIs | access | `manage_kpis` |
| Staff Portal · Module access | Administration — manage departments | access | `manage_departments` |
| Staff Portal · Module access | Staff Portal dashboard | access | `dashboard` |
| Staff Portal · Module access | Booking approval queue | access | `booking_approvals` |
| Staff Portal · Function actions | Announcements | create | `portal.announcements.create` |
| Staff Portal · Function actions | Announcements | edit | `portal.announcements.edit` |
| Staff Portal · Function actions | Announcements | upload | `portal.announcements.upload` |
| Staff Portal · Function actions | Announcements | download | `portal.announcements.download` |
| Staff Portal · Function actions | Forms library | create | `portal.forms.create` |
| Staff Portal · Function actions | Forms library | edit | `portal.forms.edit` |
| Staff Portal · Function actions | Forms library | delete | `portal.forms.delete` |
| Staff Portal · Function actions | Forms library | upload | `portal.forms.upload` |
| Staff Portal · Function actions | Forms library | download | `portal.forms.download` |
| Staff Portal · Function actions | Forms library | share | `portal.forms.share` |
| Staff Portal · Function actions | Shared resources | create | `portal.resources.create` |
| Staff Portal · Function actions | Shared resources | edit | `portal.resources.edit` |
| Staff Portal · Function actions | Shared resources | delete | `portal.resources.delete` |
| Staff Portal · Function actions | Shared resources | upload | `portal.resources.upload` |
| Staff Portal · Function actions | Shared resources | download | `portal.resources.download` |
| Staff Portal · Function actions | Shared resources | share | `portal.resources.share` |
| Staff Portal · Function actions | Travel, leave and general requests | create | `portal.requests.create` |
| Staff Portal · Function actions | Travel, leave and general requests | edit | `portal.requests.edit` |
| Staff Portal · Function actions | Travel, leave and general requests | delete | `portal.requests.delete` |
| Staff Portal · Function actions | Travel, leave and general requests | submit | `portal.requests.submit` |
| Staff Portal · Function actions | Travel, leave and general requests | approve | `portal.requests.approve` |
| Staff Portal · Function actions | Travel, leave and general requests | reject | `portal.requests.reject` |
| Staff Portal · Function actions | Travel, leave and general requests | cancel | `portal.requests.cancel` |
| Staff Portal · Function actions | Company car bookings | create | `portal.cars.create` |
| Staff Portal · Function actions | Company car bookings | edit | `portal.cars.edit` |
| Staff Portal · Function actions | Company car bookings | submit | `portal.cars.submit` |
| Staff Portal · Function actions | Company car bookings | approve | `portal.cars.approve` |
| Staff Portal · Function actions | Company car bookings | reject | `portal.cars.reject` |
| Staff Portal · Function actions | Company car bookings | cancel | `portal.cars.cancel` |
| Staff Portal · Function actions | Meeting room bookings | create | `portal.rooms.create` |
| Staff Portal · Function actions | Meeting room bookings | edit | `portal.rooms.edit` |
| Staff Portal · Function actions | Meeting room bookings | submit | `portal.rooms.submit` |
| Staff Portal · Function actions | Meeting room bookings | approve | `portal.rooms.approve` |
| Staff Portal · Function actions | Meeting room bookings | reject | `portal.rooms.reject` |
| Staff Portal · Function actions | Meeting room bookings | cancel | `portal.rooms.cancel` |
| Staff Portal · Function actions | Expense claims | create | `portal.expenses.create` |
| Staff Portal · Function actions | Expense claims | delete | `portal.expenses.delete` |
| Staff Portal · Function actions | Expense claims | export | `portal.expenses.export` |
| Staff Portal · Function actions | Expense claims | submit | `portal.expenses.submit` |
| Staff Portal · Function actions | Expense claims | approve | `portal.expenses.approve` |
| Staff Portal · Function actions | Expense claims | reject | `portal.expenses.reject` |
| Staff Portal · Function actions | Expense claims | cancel | `portal.expenses.cancel` |
| Staff Portal · Function actions | Payment processing | create | `portal.payments.create` |
| Staff Portal · Function actions | Payment processing | edit | `portal.payments.edit` |
| Staff Portal · Function actions | Payment processing | submit | `portal.payments.submit` |
| Staff Portal · Function actions | Payment processing | approve | `portal.payments.approve` |
| Staff Portal · Function actions | Payment processing | reject | `portal.payments.reject` |
| Staff Portal · Function actions | Incentive schemes and claims | create | `portal.incentives.create` |
| Staff Portal · Function actions | Incentive schemes and claims | delete | `portal.incentives.delete` |
| Staff Portal · Function actions | Incentive schemes and claims | submit | `portal.incentives.submit` |
| Staff Portal · Function actions | Incentive schemes and claims | approve | `portal.incentives.approve` |
| Staff Portal · Function actions | Incentive schemes and claims | reject | `portal.incentives.reject` |
| Staff Portal · Function actions | Incentive schemes and claims | cancel | `portal.incentives.cancel` |
| Staff Portal · Function actions | Objectives and reviews | create | `portal.objectives.create` |
| Staff Portal · Function actions | Objectives and reviews | edit | `portal.objectives.edit` |
| Staff Portal · Function actions | Objectives and reviews | delete | `portal.objectives.delete` |
| Staff Portal · Function actions | Objectives and reviews | submit | `portal.objectives.submit` |
| Staff Portal · Function actions | Objectives and reviews | approve | `portal.objectives.approve` |
| Staff Portal · Function actions | Objectives and reviews | reject | `portal.objectives.reject` |
| Staff Portal · Function actions | Tasks and action board | create | `portal.tasks.create` |
| Staff Portal · Function actions | Tasks and action board | edit | `portal.tasks.edit` |
| Staff Portal · Function actions | Tasks and action board | delete | `portal.tasks.delete` |
| Staff Portal · Function actions | Helpdesk tickets | create | `portal.helpdesk.create` |
| Staff Portal · Function actions | Helpdesk tickets | edit | `portal.helpdesk.edit` |
| Staff Portal · Function actions | SOP register | create | `portal.sops.create` |
| Staff Portal · Function actions | SOP register | edit | `portal.sops.edit` |
| Staff Portal · Function actions | SOP register | delete | `portal.sops.delete` |
| Staff Portal · Function actions | SOP register | upload | `portal.sops.upload` |
| Staff Portal · Function actions | SOP register | download | `portal.sops.download` |
| Staff Portal · Function actions | SOP register | share | `portal.sops.share` |
| Staff Portal · Function actions | Job descriptions | create | `portal.jobdescriptions.create` |
| Staff Portal · Function actions | Job descriptions | edit | `portal.jobdescriptions.edit` |
| Staff Portal · Function actions | Job descriptions | delete | `portal.jobdescriptions.delete` |
| Staff Portal · Function actions | Job descriptions | upload | `portal.jobdescriptions.upload` |
| Staff Portal · Function actions | Job descriptions | download | `portal.jobdescriptions.download` |
| Staff Portal · Function actions | Job descriptions | share | `portal.jobdescriptions.share` |
| Staff Portal · Function actions | KPI documents | create | `portal.kpis.create` |
| Staff Portal · Function actions | KPI documents | edit | `portal.kpis.edit` |
| Staff Portal · Function actions | KPI documents | delete | `portal.kpis.delete` |
| Staff Portal · Function actions | KPI documents | upload | `portal.kpis.upload` |
| Staff Portal · Function actions | KPI documents | download | `portal.kpis.download` |
| Staff Portal · Function actions | KPI documents | share | `portal.kpis.share` |
| Staff Portal · Function actions | HR profiles | create | `portal.hrprofiles.create` |
| Staff Portal · Function actions | HR profiles | edit | `portal.hrprofiles.edit` |
| Staff Portal · Function actions | HR profiles | delete | `portal.hrprofiles.delete` |
| Staff Portal · Function actions | Leave entitlements | create | `portal.leavebalance.create` |
| Staff Portal · Function actions | Leave entitlements | edit | `portal.leavebalance.edit` |
| Staff Portal · Function actions | Leave entitlements | delete | `portal.leavebalance.delete` |
| Staff Portal · Function actions | Customer visits | create | `portal.visits.create` |
| Staff Portal · Function actions | Customer visits | edit | `portal.visits.edit` |
| Staff Portal · Function actions | Customer visits | delete | `portal.visits.delete` |
| Staff Portal · Function actions | Product demonstrations | create | `portal.demos.create` |
| Staff Portal · Function actions | Product demonstrations | edit | `portal.demos.edit` |
| Staff Portal · Function actions | Product demonstrations | delete | `portal.demos.delete` |
| Staff Portal · Function actions | Performance appraisals | create | `portal.appraisals.create` |
| Staff Portal · Function actions | Performance appraisals | edit | `portal.appraisals.edit` |
| Staff Portal · Function actions | Performance appraisals | delete | `portal.appraisals.delete` |
| Staff Portal · Function actions | Onboarding / promotion / offboarding | create | `portal.onboarding.create` |
| Staff Portal · Function actions | Onboarding / promotion / offboarding | edit | `portal.onboarding.edit` |
| Staff Portal · Function actions | Onboarding / promotion / offboarding | delete | `portal.onboarding.delete` |
| Staff Portal · Function actions | Training and competency | create | `portal.training.create` |
| Staff Portal · Function actions | Training and competency | edit | `portal.training.edit` |
| Staff Portal · Function actions | Training and competency | upload | `portal.training.upload` |
| Staff Portal · Function actions | Training and competency | download | `portal.training.download` |
| Staff Portal · Function actions | Training and competency | submit | `portal.training.submit` |
| Staff Portal · Function actions | Training and competency | approve | `portal.training.approve` |
| Staff Portal · Function actions | Training and competency | reject | `portal.training.reject` |
| Staff Portal · Function actions | Website content publishing | create | `portal.content.create` |
| Staff Portal · Function actions | Website content publishing | edit | `portal.content.edit` |
| Staff Portal · Function actions | Website content publishing | delete | `portal.content.delete` |
| Staff Portal · Function actions | Website content publishing | publish | `portal.content.publish` |
| Staff Portal · Function actions | Brand catalogue | create | `portal.brands.create` |
| Staff Portal · Function actions | Brand catalogue | edit | `portal.brands.edit` |
| Staff Portal · Function actions | Brand catalogue | delete | `portal.brands.delete` |
| Staff Portal · Function actions | Staff accounts and roles | create | `portal.users.create` |
| Staff Portal · Function actions | Staff accounts and roles | assign | `portal.users.assign` |
| Staff Portal · Function actions | Roles and responsibilities | create | `portal.roles.create` |
| Staff Portal · Function actions | Roles and responsibilities | edit | `portal.roles.edit` |
| Staff Portal · Function actions | Roles and responsibilities | clone | `portal.roles.clone` |
| Staff Portal · Function actions | Company settings and facilities | edit | `portal.settings.edit` |
| Staff Portal · Function actions | Reporting hierarchy / departments | edit | `portal.hierarchy.edit` |
| Staff Portal · Function actions | Sales targets and performance | edit | `portal.sales.edit` |
| Staff Portal · Function actions | Quotation follow-up and won/lost status | edit | `portal.pipeline.edit` |
| Staff Portal · Function actions | Tenders | create | `portal.tenders.create` |
| Staff Portal · Function actions | Tenders | edit | `portal.tenders.edit` |
| Staff Portal · Function actions | Tenders | delete | `portal.tenders.delete` |
| Biomed IS · Sales | Quotation | view | `is.quotation.view` |
| Biomed IS · Sales | Quotation | create | `is.quotation.create` |
| Biomed IS · Sales | Quotation | edit | `is.quotation.edit` |
| Biomed IS · Sales | Quotation | submit | `is.quotation.submit` |
| Biomed IS · Sales | Quotation | approve | `is.quotation.approve` |
| Biomed IS · Sales | Quotation | reject | `is.quotation.reject` |
| Biomed IS · Sales | Quotation | cancel | `is.quotation.cancel` |
| Biomed IS · Sales | Quotation | derive | `is.quotation.derive` |
| Biomed IS · Sales | Quotation | print | `is.quotation.print` |
| Biomed IS · Sales | Quotation | export | `is.quotation.export` |
| Biomed IS · Sales | Customer orders | view | `is.customer-order.view` |
| Biomed IS · Sales | Customer orders | create | `is.customer-order.create` |
| Biomed IS · Sales | Customer orders | edit | `is.customer-order.edit` |
| Biomed IS · Sales | Customer orders | submit | `is.customer-order.submit` |
| Biomed IS · Sales | Customer orders | approve | `is.customer-order.approve` |
| Biomed IS · Sales | Customer orders | reject | `is.customer-order.reject` |
| Biomed IS · Sales | Customer orders | cancel | `is.customer-order.cancel` |
| Biomed IS · Sales | Customer orders | derive | `is.customer-order.derive` |
| Biomed IS · Sales | Customer orders | print | `is.customer-order.print` |
| Biomed IS · Sales | Customer orders | export | `is.customer-order.export` |
| Biomed IS · Sales | Sales orders | view | `is.sales-order.view` |
| Biomed IS · Sales | Sales orders | create | `is.sales-order.create` |
| Biomed IS · Sales | Sales orders | edit | `is.sales-order.edit` |
| Biomed IS · Sales | Sales orders | submit | `is.sales-order.submit` |
| Biomed IS · Sales | Sales orders | approve | `is.sales-order.approve` |
| Biomed IS · Sales | Sales orders | reject | `is.sales-order.reject` |
| Biomed IS · Sales | Sales orders | cancel | `is.sales-order.cancel` |
| Biomed IS · Sales | Sales orders | derive | `is.sales-order.derive` |
| Biomed IS · Sales | Sales orders | print | `is.sales-order.print` |
| Biomed IS · Sales | Sales orders | export | `is.sales-order.export` |
| Biomed IS · Sales | Withdrawal | view | `is.withdrawal.view` |
| Biomed IS · Sales | Withdrawal | create | `is.withdrawal.create` |
| Biomed IS · Sales | Withdrawal | edit | `is.withdrawal.edit` |
| Biomed IS · Sales | Withdrawal | submit | `is.withdrawal.submit` |
| Biomed IS · Sales | Withdrawal | approve | `is.withdrawal.approve` |
| Biomed IS · Sales | Withdrawal | reject | `is.withdrawal.reject` |
| Biomed IS · Sales | Withdrawal | cancel | `is.withdrawal.cancel` |
| Biomed IS · Sales | Withdrawal | derive | `is.withdrawal.derive` |
| Biomed IS · Sales | Withdrawal | print | `is.withdrawal.print` |
| Biomed IS · Sales | Withdrawal | export | `is.withdrawal.export` |
| Biomed IS · Sales | Borrowing | view | `is.borrowing.view` |
| Biomed IS · Sales | Borrowing | create | `is.borrowing.create` |
| Biomed IS · Sales | Borrowing | edit | `is.borrowing.edit` |
| Biomed IS · Sales | Borrowing | submit | `is.borrowing.submit` |
| Biomed IS · Sales | Borrowing | approve | `is.borrowing.approve` |
| Biomed IS · Sales | Borrowing | reject | `is.borrowing.reject` |
| Biomed IS · Sales | Borrowing | cancel | `is.borrowing.cancel` |
| Biomed IS · Sales | Borrowing | derive | `is.borrowing.derive` |
| Biomed IS · Sales | Borrowing | print | `is.borrowing.print` |
| Biomed IS · Sales | Borrowing | export | `is.borrowing.export` |
| Biomed IS · Sales | Product return | view | `is.return-product.view` |
| Biomed IS · Sales | Product return | create | `is.return-product.create` |
| Biomed IS · Sales | Product return | edit | `is.return-product.edit` |
| Biomed IS · Sales | Product return | submit | `is.return-product.submit` |
| Biomed IS · Sales | Product return | approve | `is.return-product.approve` |
| Biomed IS · Sales | Product return | reject | `is.return-product.reject` |
| Biomed IS · Sales | Product return | cancel | `is.return-product.cancel` |
| Biomed IS · Sales | Product return | derive | `is.return-product.derive` |
| Biomed IS · Sales | Product return | print | `is.return-product.print` |
| Biomed IS · Sales | Product return | export | `is.return-product.export` |
| Biomed IS · Purchasing | Purchase requisition | view | `is.purchase-request.view` |
| Biomed IS · Purchasing | Purchase requisition | create | `is.purchase-request.create` |
| Biomed IS · Purchasing | Purchase requisition | edit | `is.purchase-request.edit` |
| Biomed IS · Purchasing | Purchase requisition | submit | `is.purchase-request.submit` |
| Biomed IS · Purchasing | Purchase requisition | approve | `is.purchase-request.approve` |
| Biomed IS · Purchasing | Purchase requisition | reject | `is.purchase-request.reject` |
| Biomed IS · Purchasing | Purchase requisition | cancel | `is.purchase-request.cancel` |
| Biomed IS · Purchasing | Purchase requisition | derive | `is.purchase-request.derive` |
| Biomed IS · Purchasing | Purchase requisition | print | `is.purchase-request.print` |
| Biomed IS · Purchasing | Purchase requisition | export | `is.purchase-request.export` |
| Biomed IS · Purchasing | Purchase order | view | `is.purchase-order.view` |
| Biomed IS · Purchasing | Purchase order | create | `is.purchase-order.create` |
| Biomed IS · Purchasing | Purchase order | edit | `is.purchase-order.edit` |
| Biomed IS · Purchasing | Purchase order | submit | `is.purchase-order.submit` |
| Biomed IS · Purchasing | Purchase order | approve | `is.purchase-order.approve` |
| Biomed IS · Purchasing | Purchase order | reject | `is.purchase-order.reject` |
| Biomed IS · Purchasing | Purchase order | cancel | `is.purchase-order.cancel` |
| Biomed IS · Purchasing | Purchase order | derive | `is.purchase-order.derive` |
| Biomed IS · Purchasing | Purchase order | print | `is.purchase-order.print` |
| Biomed IS · Purchasing | Purchase order | export | `is.purchase-order.export` |
| Biomed IS · Purchasing | Supplier confirmation | view | `is.supplier-confirm.view` |
| Biomed IS · Purchasing | Supplier confirmation | create | `is.supplier-confirm.create` |
| Biomed IS · Purchasing | Supplier confirmation | edit | `is.supplier-confirm.edit` |
| Biomed IS · Purchasing | Supplier confirmation | submit | `is.supplier-confirm.submit` |
| Biomed IS · Purchasing | Supplier confirmation | approve | `is.supplier-confirm.approve` |
| Biomed IS · Purchasing | Supplier confirmation | reject | `is.supplier-confirm.reject` |
| Biomed IS · Purchasing | Supplier confirmation | cancel | `is.supplier-confirm.cancel` |
| Biomed IS · Purchasing | Supplier confirmation | derive | `is.supplier-confirm.derive` |
| Biomed IS · Purchasing | Supplier confirmation | print | `is.supplier-confirm.print` |
| Biomed IS · Purchasing | Supplier confirmation | export | `is.supplier-confirm.export` |
| Biomed IS · Purchasing | Delivery in | view | `is.delivery-in.view` |
| Biomed IS · Purchasing | Delivery in | create | `is.delivery-in.create` |
| Biomed IS · Purchasing | Delivery in | edit | `is.delivery-in.edit` |
| Biomed IS · Purchasing | Delivery in | submit | `is.delivery-in.submit` |
| Biomed IS · Purchasing | Delivery in | approve | `is.delivery-in.approve` |
| Biomed IS · Purchasing | Delivery in | reject | `is.delivery-in.reject` |
| Biomed IS · Purchasing | Delivery in | cancel | `is.delivery-in.cancel` |
| Biomed IS · Purchasing | Delivery in | derive | `is.delivery-in.derive` |
| Biomed IS · Purchasing | Delivery in | print | `is.delivery-in.print` |
| Biomed IS · Purchasing | Delivery in | export | `is.delivery-in.export` |
| Biomed IS · Purchasing | Check in | view | `is.check-in.view` |
| Biomed IS · Purchasing | Check in | create | `is.check-in.create` |
| Biomed IS · Purchasing | Check in | edit | `is.check-in.edit` |
| Biomed IS · Purchasing | Check in | submit | `is.check-in.submit` |
| Biomed IS · Purchasing | Check in | approve | `is.check-in.approve` |
| Biomed IS · Purchasing | Check in | reject | `is.check-in.reject` |
| Biomed IS · Purchasing | Check in | cancel | `is.check-in.cancel` |
| Biomed IS · Purchasing | Check in | derive | `is.check-in.derive` |
| Biomed IS · Purchasing | Check in | print | `is.check-in.print` |
| Biomed IS · Purchasing | Check in | export | `is.check-in.export` |
| Biomed IS · Warehouse | Delivery out | view | `is.delivery-out.view` |
| Biomed IS · Warehouse | Delivery out | create | `is.delivery-out.create` |
| Biomed IS · Warehouse | Delivery out | edit | `is.delivery-out.edit` |
| Biomed IS · Warehouse | Delivery out | submit | `is.delivery-out.submit` |
| Biomed IS · Warehouse | Delivery out | approve | `is.delivery-out.approve` |
| Biomed IS · Warehouse | Delivery out | reject | `is.delivery-out.reject` |
| Biomed IS · Warehouse | Delivery out | cancel | `is.delivery-out.cancel` |
| Biomed IS · Warehouse | Delivery out | derive | `is.delivery-out.derive` |
| Biomed IS · Warehouse | Delivery out | print | `is.delivery-out.print` |
| Biomed IS · Warehouse | Delivery out | export | `is.delivery-out.export` |
| Biomed IS · Warehouse | Check out | view | `is.check-out.view` |
| Biomed IS · Warehouse | Check out | create | `is.check-out.create` |
| Biomed IS · Warehouse | Check out | edit | `is.check-out.edit` |
| Biomed IS · Warehouse | Check out | submit | `is.check-out.submit` |
| Biomed IS · Warehouse | Check out | approve | `is.check-out.approve` |
| Biomed IS · Warehouse | Check out | reject | `is.check-out.reject` |
| Biomed IS · Warehouse | Check out | cancel | `is.check-out.cancel` |
| Biomed IS · Warehouse | Check out | derive | `is.check-out.derive` |
| Biomed IS · Warehouse | Check out | print | `is.check-out.print` |
| Biomed IS · Warehouse | Check out | export | `is.check-out.export` |
| Biomed IS · Warehouse | Stock adjustment | view | `is.stock-adjust.view` |
| Biomed IS · Warehouse | Stock adjustment | create | `is.stock-adjust.create` |
| Biomed IS · Warehouse | Stock adjustment | edit | `is.stock-adjust.edit` |
| Biomed IS · Warehouse | Stock adjustment | submit | `is.stock-adjust.submit` |
| Biomed IS · Warehouse | Stock adjustment | approve | `is.stock-adjust.approve` |
| Biomed IS · Warehouse | Stock adjustment | reject | `is.stock-adjust.reject` |
| Biomed IS · Warehouse | Stock adjustment | cancel | `is.stock-adjust.cancel` |
| Biomed IS · Warehouse | Stock adjustment | derive | `is.stock-adjust.derive` |
| Biomed IS · Warehouse | Stock adjustment | print | `is.stock-adjust.print` |
| Biomed IS · Warehouse | Stock adjustment | export | `is.stock-adjust.export` |
| Biomed IS · Warehouse | Warehouse transfer | view | `is.stock-transfer.view` |
| Biomed IS · Warehouse | Warehouse transfer | create | `is.stock-transfer.create` |
| Biomed IS · Warehouse | Warehouse transfer | edit | `is.stock-transfer.edit` |
| Biomed IS · Warehouse | Warehouse transfer | submit | `is.stock-transfer.submit` |
| Biomed IS · Warehouse | Warehouse transfer | approve | `is.stock-transfer.approve` |
| Biomed IS · Warehouse | Warehouse transfer | reject | `is.stock-transfer.reject` |
| Biomed IS · Warehouse | Warehouse transfer | cancel | `is.stock-transfer.cancel` |
| Biomed IS · Warehouse | Warehouse transfer | derive | `is.stock-transfer.derive` |
| Biomed IS · Warehouse | Warehouse transfer | print | `is.stock-transfer.print` |
| Biomed IS · Warehouse | Warehouse transfer | export | `is.stock-transfer.export` |
| Biomed IS · Warehouse | Stock count | view | `is.stock-count.view` |
| Biomed IS · Warehouse | Stock count | create | `is.stock-count.create` |
| Biomed IS · Warehouse | Stock count | edit | `is.stock-count.edit` |
| Biomed IS · Warehouse | Stock count | submit | `is.stock-count.submit` |
| Biomed IS · Warehouse | Stock count | approve | `is.stock-count.approve` |
| Biomed IS · Warehouse | Stock count | reject | `is.stock-count.reject` |
| Biomed IS · Warehouse | Stock count | cancel | `is.stock-count.cancel` |
| Biomed IS · Warehouse | Stock count | derive | `is.stock-count.derive` |
| Biomed IS · Warehouse | Stock count | print | `is.stock-count.print` |
| Biomed IS · Warehouse | Stock count | export | `is.stock-count.export` |
| Biomed IS · Finance | Invoice | view | `is.invoice.view` |
| Biomed IS · Finance | Invoice | create | `is.invoice.create` |
| Biomed IS · Finance | Invoice | edit | `is.invoice.edit` |
| Biomed IS · Finance | Invoice | submit | `is.invoice.submit` |
| Biomed IS · Finance | Invoice | approve | `is.invoice.approve` |
| Biomed IS · Finance | Invoice | reject | `is.invoice.reject` |
| Biomed IS · Finance | Invoice | cancel | `is.invoice.cancel` |
| Biomed IS · Finance | Invoice | derive | `is.invoice.derive` |
| Biomed IS · Finance | Invoice | print | `is.invoice.print` |
| Biomed IS · Finance | Invoice | export | `is.invoice.export` |
| Biomed IS · Finance | Credit note | view | `is.credit-note.view` |
| Biomed IS · Finance | Credit note | create | `is.credit-note.create` |
| Biomed IS · Finance | Credit note | edit | `is.credit-note.edit` |
| Biomed IS · Finance | Credit note | submit | `is.credit-note.submit` |
| Biomed IS · Finance | Credit note | approve | `is.credit-note.approve` |
| Biomed IS · Finance | Credit note | reject | `is.credit-note.reject` |
| Biomed IS · Finance | Credit note | cancel | `is.credit-note.cancel` |
| Biomed IS · Finance | Credit note | derive | `is.credit-note.derive` |
| Biomed IS · Finance | Credit note | print | `is.credit-note.print` |
| Biomed IS · Finance | Credit note | export | `is.credit-note.export` |
| Biomed IS · Finance | Debit note | view | `is.debit-note.view` |
| Biomed IS · Finance | Debit note | create | `is.debit-note.create` |
| Biomed IS · Finance | Debit note | edit | `is.debit-note.edit` |
| Biomed IS · Finance | Debit note | submit | `is.debit-note.submit` |
| Biomed IS · Finance | Debit note | approve | `is.debit-note.approve` |
| Biomed IS · Finance | Debit note | reject | `is.debit-note.reject` |
| Biomed IS · Finance | Debit note | cancel | `is.debit-note.cancel` |
| Biomed IS · Finance | Debit note | derive | `is.debit-note.derive` |
| Biomed IS · Finance | Debit note | print | `is.debit-note.print` |
| Biomed IS · Finance | Debit note | export | `is.debit-note.export` |
| Biomed IS · Finance | Payment receipt | view | `is.payment-receipt.view` |
| Biomed IS · Finance | Payment receipt | create | `is.payment-receipt.create` |
| Biomed IS · Finance | Payment receipt | edit | `is.payment-receipt.edit` |
| Biomed IS · Finance | Payment receipt | submit | `is.payment-receipt.submit` |
| Biomed IS · Finance | Payment receipt | approve | `is.payment-receipt.approve` |
| Biomed IS · Finance | Payment receipt | reject | `is.payment-receipt.reject` |
| Biomed IS · Finance | Payment receipt | cancel | `is.payment-receipt.cancel` |
| Biomed IS · Finance | Payment receipt | derive | `is.payment-receipt.derive` |
| Biomed IS · Finance | Payment receipt | print | `is.payment-receipt.print` |
| Biomed IS · Finance | Payment receipt | export | `is.payment-receipt.export` |
| Biomed IS · Master data | Customers | view | `is.master-customers.view` |
| Biomed IS · Master data | Customers | create | `is.master-customers.create` |
| Biomed IS · Master data | Customers | edit | `is.master-customers.edit` |
| Biomed IS · Master data | Customers | deactivate | `is.master-customers.deactivate` |
| Biomed IS · Master data | Customers | delete | `is.master-customers.delete` |
| Biomed IS · Master data | Customers | import | `is.master-customers.import` |
| Biomed IS · Master data | Customers | export | `is.master-customers.export` |
| Biomed IS · Master data | Suppliers | view | `is.master-suppliers.view` |
| Biomed IS · Master data | Suppliers | create | `is.master-suppliers.create` |
| Biomed IS · Master data | Suppliers | edit | `is.master-suppliers.edit` |
| Biomed IS · Master data | Suppliers | deactivate | `is.master-suppliers.deactivate` |
| Biomed IS · Master data | Suppliers | delete | `is.master-suppliers.delete` |
| Biomed IS · Master data | Suppliers | import | `is.master-suppliers.import` |
| Biomed IS · Master data | Suppliers | export | `is.master-suppliers.export` |
| Biomed IS · Master data | Products | view | `is.master-products.view` |
| Biomed IS · Master data | Products | create | `is.master-products.create` |
| Biomed IS · Master data | Products | edit | `is.master-products.edit` |
| Biomed IS · Master data | Products | deactivate | `is.master-products.deactivate` |
| Biomed IS · Master data | Products | delete | `is.master-products.delete` |
| Biomed IS · Master data | Products | import | `is.master-products.import` |
| Biomed IS · Master data | Products | export | `is.master-products.export` |
| Biomed IS · Master data | Warehouses | view | `is.master-warehouses.view` |
| Biomed IS · Master data | Warehouses | create | `is.master-warehouses.create` |
| Biomed IS · Master data | Warehouses | edit | `is.master-warehouses.edit` |
| Biomed IS · Master data | Warehouses | deactivate | `is.master-warehouses.deactivate` |
| Biomed IS · Master data | Warehouses | delete | `is.master-warehouses.delete` |
| Biomed IS · Master data | Warehouses | import | `is.master-warehouses.import` |
| Biomed IS · Master data | Warehouses | export | `is.master-warehouses.export` |
| Biomed IS · Inventory and administration | Dashboard | view | `is.dashboard.view` |
| Biomed IS · Inventory and administration | Approval queue | view | `is.approval.view` |
| Biomed IS · Inventory and administration | Approval queue | export | `is.approval.export` |
| Biomed IS · Inventory and administration | Document traceability | view | `is.trace.view` |
| Biomed IS · Inventory and administration | Document traceability | export | `is.trace.export` |
| Biomed IS · Inventory and administration | IS / Portal / Budget integration | view | `is.reconcile.view` |
| Biomed IS · Inventory and administration | IS / Portal / Budget integration | export | `is.reconcile.export` |
| Biomed IS · Inventory and administration | IS / Portal / Budget integration | edit | `is.reconcile.edit` |
| Biomed IS · Inventory and administration | Stock ledger | view | `is.stocks.view` |
| Biomed IS · Inventory and administration | Stock ledger | export | `is.stocks.export` |
| Biomed IS · Inventory and administration | Stock inventory | view | `is.stock-inventory.view` |
| Biomed IS · Inventory and administration | Stock inventory | export | `is.stock-inventory.export` |
| Biomed IS · Inventory and administration | Automatic shipment records | view | `is.shipment.view` |
| Biomed IS · Inventory and administration | Automatic shipment records | print | `is.shipment.print` |
| Biomed IS · Inventory and administration | Automatic shipment records | export | `is.shipment.export` |
| Biomed IS · Inventory and administration | Expiry alerts | view | `is.expiry.view` |
| Biomed IS · Inventory and administration | Expiry alerts | export | `is.expiry.export` |
| Biomed IS · Inventory and administration | Lot hold and release | view | `is.lot-control.view` |
| Biomed IS · Inventory and administration | Lot hold and release | hold | `is.lot-control.hold` |
| Biomed IS · Inventory and administration | Lot hold and release | release | `is.lot-control.release` |
| Biomed IS · Inventory and administration | Lot hold and release | export | `is.lot-control.export` |
| Biomed IS · Inventory and administration | Physical stock counts | view | `is.cycle-count.view` |
| Biomed IS · Inventory and administration | Physical stock counts | create | `is.cycle-count.create` |
| Biomed IS · Inventory and administration | Physical stock counts | approve | `is.cycle-count.approve` |
| Biomed IS · Inventory and administration | Physical stock counts | reject | `is.cycle-count.reject` |
| Biomed IS · Inventory and administration | Physical stock counts | export | `is.cycle-count.export` |
| Biomed IS · Inventory and administration | Warehouse location transfers | view | `is.warehouse-move.view` |
| Biomed IS · Inventory and administration | Warehouse location transfers | create | `is.warehouse-move.create` |
| Biomed IS · Inventory and administration | Warehouse location transfers | approve | `is.warehouse-move.approve` |
| Biomed IS · Inventory and administration | Warehouse location transfers | reject | `is.warehouse-move.reject` |
| Biomed IS · Inventory and administration | Warehouse location transfers | export | `is.warehouse-move.export` |
| Biomed IS · Inventory and administration | Product kits and panels | view | `is.kits.view` |
| Biomed IS · Inventory and administration | Product kits and panels | create | `is.kits.create` |
| Biomed IS · Inventory and administration | Product kits and panels | delete | `is.kits.delete` |
| Biomed IS · Inventory and administration | Product kits and panels | export | `is.kits.export` |
| Biomed IS · Inventory and administration | Reports | view | `is.reports.view` |
| Biomed IS · Inventory and administration | Reports | print | `is.reports.print` |
| Biomed IS · Inventory and administration | Reports | export | `is.reports.export` |
| Biomed IS · Inventory and administration | Approval rules and settings | view | `is.rules.view` |
| Biomed IS · Inventory and administration | Approval rules and settings | edit | `is.rules.edit` |
| Biomed IS · Inventory and administration | Audit history | view | `is.history.view` |
| Biomed IS · Inventory and administration | Audit history | export | `is.history.export` |
| Biomed IS · Inventory and administration | Original source map | view | `is.legacy-map.view` |
| Biomed IS · Inventory and administration | Database backup and restore | export | `is.backup.export` |
| Biomed IS · Inventory and administration | Database backup and restore | restore | `is.backup.restore` |
| Financial · Reports | Executive dashboard | view | `budget.dashboard.view` |
| Financial · Reports | Executive dashboard | export | `budget.dashboard.export` |
| Financial · Reports | P&L summary | view | `budget.pnl.view` |
| Financial · Reports | P&L summary | export | `budget.pnl.export` |
| Financial · Reports | Product summary | view | `budget.products_summary.view` |
| Financial · Reports | Product summary | export | `budget.products_summary.export` |
| Financial · Reports | Budget summary | view | `budget.budget_summary.view` |
| Financial · Reports | Budget summary | export | `budget.budget_summary.export` |
| Financial · Worksheets | Target and revenue | view | `budget.products.view` |
| Financial · Worksheets | Target and revenue | export | `budget.products.export` |
| Financial · Worksheets | Target and revenue | edit | `budget.products.edit` |
| Financial · Worksheets | Target and revenue | actual | `budget.products.actual` |
| Financial · Worksheets | Target and revenue | commitment | `budget.products.commitment` |
| Financial · Worksheets | Cost of goods sold | view | `budget.cogs.view` |
| Financial · Worksheets | Cost of goods sold | export | `budget.cogs.export` |
| Financial · Worksheets | Cost of goods sold | edit | `budget.cogs.edit` |
| Financial · Worksheets | Cost of goods sold | actual | `budget.cogs.actual` |
| Financial · Worksheets | Cost of goods sold | commitment | `budget.cogs.commitment` |
| Financial · Worksheets | Other cost of sales | view | `budget.ocos.view` |
| Financial · Worksheets | Other cost of sales | export | `budget.ocos.export` |
| Financial · Worksheets | Other cost of sales | edit | `budget.ocos.edit` |
| Financial · Worksheets | Other cost of sales | actual | `budget.ocos.actual` |
| Financial · Worksheets | Other cost of sales | commitment | `budget.ocos.commitment` |
| Financial · Worksheets | Other cost of sales | create | `budget.ocos.create` |
| Financial · Worksheets | Other cost of sales | delete | `budget.ocos.delete` |
| Financial · Worksheets | Promotional expenses | view | `budget.expense_promo.view` |
| Financial · Worksheets | Promotional expenses | export | `budget.expense_promo.export` |
| Financial · Worksheets | Promotional expenses | edit | `budget.expense_promo.edit` |
| Financial · Worksheets | Promotional expenses | actual | `budget.expense_promo.actual` |
| Financial · Worksheets | Promotional expenses | commitment | `budget.expense_promo.commitment` |
| Financial · Worksheets | Administrative expenses | view | `budget.expense_admin.view` |
| Financial · Worksheets | Administrative expenses | export | `budget.expense_admin.export` |
| Financial · Worksheets | Administrative expenses | edit | `budget.expense_admin.edit` |
| Financial · Worksheets | Administrative expenses | actual | `budget.expense_admin.actual` |
| Financial · Worksheets | Administrative expenses | commitment | `budget.expense_admin.commitment` |
| Financial · Worksheets | Financial expenses | view | `budget.expense_finance.view` |
| Financial · Worksheets | Financial expenses | export | `budget.expense_finance.export` |
| Financial · Worksheets | Financial expenses | edit | `budget.expense_finance.edit` |
| Financial · Worksheets | Financial expenses | actual | `budget.expense_finance.actual` |
| Financial · Worksheets | Financial expenses | commitment | `budget.expense_finance.commitment` |
| Financial · Worksheets | Other expenses | view | `budget.expense_other.view` |
| Financial · Worksheets | Other expenses | export | `budget.expense_other.export` |
| Financial · Worksheets | Other expenses | edit | `budget.expense_other.edit` |
| Financial · Worksheets | Other expenses | actual | `budget.expense_other.actual` |
| Financial · Worksheets | Other expenses | commitment | `budget.expense_other.commitment` |
| Financial · Worksheets | Salary and bonus | view | `budget.person_salary.view` |
| Financial · Worksheets | Salary and bonus | export | `budget.person_salary.export` |
| Financial · Worksheets | Salary and bonus | edit | `budget.person_salary.edit` |
| Financial · Worksheets | Salary and bonus | actual | `budget.person_salary.actual` |
| Financial · Worksheets | Salary and bonus | commitment | `budget.person_salary.commitment` |
| Financial · Worksheets | Commission and incentive | view | `budget.person_incentive.view` |
| Financial · Worksheets | Commission and incentive | export | `budget.person_incentive.export` |
| Financial · Worksheets | Commission and incentive | edit | `budget.person_incentive.edit` |
| Financial · Worksheets | Commission and incentive | actual | `budget.person_incentive.actual` |
| Financial · Worksheets | Commission and incentive | commitment | `budget.person_incentive.commitment` |
| Financial · Worksheets | Social security / provident fund | view | `budget.person_social.view` |
| Financial · Worksheets | Social security / provident fund | export | `budget.person_social.export` |
| Financial · Worksheets | Social security / provident fund | edit | `budget.person_social.edit` |
| Financial · Worksheets | Social security / provident fund | actual | `budget.person_social.actual` |
| Financial · Worksheets | Social security / provident fund | commitment | `budget.person_social.commitment` |
| Financial · Worksheets | Healthcare coverage | view | `budget.person_health.view` |
| Financial · Worksheets | Healthcare coverage | export | `budget.person_health.export` |
| Financial · Worksheets | Healthcare coverage | edit | `budget.person_health.edit` |
| Financial · Worksheets | Healthcare coverage | actual | `budget.person_health.actual` |
| Financial · Worksheets | Healthcare coverage | commitment | `budget.person_health.commitment` |
| Financial · Worksheets | Local travel and expenses | view | `budget.person_local.view` |
| Financial · Worksheets | Local travel and expenses | export | `budget.person_local.export` |
| Financial · Worksheets | Local travel and expenses | edit | `budget.person_local.edit` |
| Financial · Worksheets | Local travel and expenses | actual | `budget.person_local.actual` |
| Financial · Worksheets | Local travel and expenses | commitment | `budget.person_local.commitment` |
| Financial · Worksheets | Overseas travel and expenses | view | `budget.person_overseas.view` |
| Financial · Worksheets | Overseas travel and expenses | export | `budget.person_overseas.export` |
| Financial · Worksheets | Overseas travel and expenses | edit | `budget.person_overseas.edit` |
| Financial · Worksheets | Overseas travel and expenses | actual | `budget.person_overseas.actual` |
| Financial · Worksheets | Overseas travel and expenses | commitment | `budget.person_overseas.commitment` |
| Financial · Worksheets | Training and KOM | view | `budget.person_training.view` |
| Financial · Worksheets | Training and KOM | export | `budget.person_training.export` |
| Financial · Worksheets | Training and KOM | edit | `budget.person_training.edit` |
| Financial · Worksheets | Training and KOM | actual | `budget.person_training.actual` |
| Financial · Worksheets | Training and KOM | commitment | `budget.person_training.commitment` |
| Financial · Control and administration | Cost centers | view | `budget.masters.view` |
| Financial · Control and administration | Cost centers | export | `budget.masters.export` |
| Financial · Control and administration | Cost centers | edit | `budget.masters.edit` |
| Financial · Control and administration | Cost centers | create | `budget.masters.create` |
| Financial · Control and administration | Cost centers | delete | `budget.masters.delete` |
| Financial · Control and administration | Product master | view | `budget.manage_products.view` |
| Financial · Control and administration | Product master | export | `budget.manage_products.export` |
| Financial · Control and administration | Product master | edit | `budget.manage_products.edit` |
| Financial · Control and administration | Product master | create | `budget.manage_products.create` |
| Financial · Control and administration | Product master | delete | `budget.manage_products.delete` |
| Financial · Control and administration | Expense item master | view | `budget.manage_items.view` |
| Financial · Control and administration | Expense item master | export | `budget.manage_items.export` |
| Financial · Control and administration | Expense item master | edit | `budget.manage_items.edit` |
| Financial · Control and administration | Expense item master | create | `budget.manage_items.create` |
| Financial · Control and administration | Expense item master | delete | `budget.manage_items.delete` |
| Financial · Control and administration | Actuals and commitments | view | `budget.ledger.view` |
| Financial · Control and administration | Actuals and commitments | export | `budget.ledger.export` |
| Financial · Control and administration | Actuals and commitments | edit | `budget.ledger.edit` |
| Financial · Control and administration | Actuals and commitments | create | `budget.ledger.create` |
| Financial · Control and administration | Actuals and commitments | delete | `budget.ledger.delete` |
| Financial · Control and administration | Workforce scenarios | view | `budget.workforce.view` |
| Financial · Control and administration | Workforce scenarios | export | `budget.workforce.export` |
| Financial · Control and administration | Workforce scenarios | edit | `budget.workforce.edit` |
| Financial · Control and administration | Workforce scenarios | create | `budget.workforce.create` |
| Financial · Control and administration | Workforce scenarios | delete | `budget.workforce.delete` |
| Financial · Reports | Budget monitoring reports | view | `budget.reports.view` |
| Financial · Reports | Budget monitoring reports | export | `budget.reports.export` |
| Financial · Control and administration | IS reconciliation | view | `budget.is_bridge.view` |
| Financial · Control and administration | IS reconciliation | export | `budget.is_bridge.export` |
| Financial · Control and administration | IS reconciliation | edit | `budget.is_bridge.edit` |
| Financial · Control and administration | IS reconciliation | reconcile | `budget.is_bridge.reconcile` |
| Financial · Control and administration | Submission and approvals | view | `budget.approvals.view` |
| Financial · Control and administration | Submission and approvals | export | `budget.approvals.export` |
| Financial · Control and administration | Submission and approvals | submit | `budget.approvals.submit` |
| Financial · Control and administration | Submission and approvals | department_approve | `budget.approvals.department_approve` |
| Financial · Control and administration | Submission and approvals | finance_approve | `budget.approvals.finance_approve` |
| Financial · Control and administration | Submission and approvals | director_approve | `budget.approvals.director_approve` |
| Financial · Control and administration | Submission and approvals | return | `budget.approvals.return` |
| Financial · Reports | Budget validation | view | `budget.quality.view` |
| Financial · Reports | Budget validation | export | `budget.quality.export` |
| Financial · Control and administration | Versions and backup | view | `budget.settings.view` |
| Financial · Control and administration | Versions and backup | export | `budget.settings.export` |
| Financial · Control and administration | Versions and backup | backup | `budget.settings.backup` |
| Financial · Control and administration | Versions and backup | restore | `budget.settings.restore` |
| Financial · Control and administration | Versions and backup | reset_current | `budget.settings.reset_current` |
| Financial · Control and administration | Versions and backup | reset_all | `budget.settings.reset_all` |
| Financial · Control and administration | Fiscal years | switch | `budget.fiscal-year.switch` |
| Financial · Control and administration | Fiscal years | create | `budget.fiscal-year.create` |
| Staff Portal · Function actions | Announcements | acknowledge | `portal.announcements.acknowledge` |
