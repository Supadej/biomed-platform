# Application Service and compact workspace controls

## Application Service
CRM order: External Helpdesk, Instrument Service, Application Service, Project & Activity, Sales Plan. Application Service uses the existing Staff Portal header, navigation, login and Roles & Permissions.

Application specialists can create service work orders with an assigned specialist, service type, start/end date and time, customer/contact/product line, optional instrument and Helpdesk links, purpose, work performed, result, customer feedback and follow-up action/due date. Work types cover training, validation, troubleshooting, optimization, demonstrations, installation support and customer follow-up. Completed jobs require work performed and result.

The register provides search, date/status/specialist filters, newest-first sorting, selectable/renamable/resizable columns, CSV export, smooth expandable reports, editing and audited removal. Analysis summarizes the filtered jobs by status and highlights overdue follow-up. Named search favorites work with this module. Initial and applied date filters are sent to the server.

Helpdesk tickets show linked Application Service jobs under Parts & Service. Users with Create access can start a new job from a saved ticket. Jobs can link an existing visible ticket, change/remove a referral, or create a new ticket while saving. A job links to one ticket; a ticket may have multiple jobs. Direct record links open the selected job even outside the initial date range. Tickets with active application-service referrals cannot be deleted until those links are removed.

## Roles & responsibilities
A new Application Service group appears in Roles & Permissions with View, View all, Create, Edit, Delete, Assign, Export and Audit permissions. System Admin receives these through the existing catalog migration. New presets are added if absent:

| Preset | Responsibility |
|---|---|
| Application Specialist | View assigned or created jobs; create/edit jobs and export visible records; view scoped Helpdesk tickets and create new tickets; view the instrument register for optional linking. |
| Application Service Manager | Specialist permissions plus view all application jobs, assign specialists, remove jobs and view audit history; view all Helpdesk tickets. |

Assign the appropriate role or grant these permissions to an existing custom role in Staff Portal → Roles & Permissions. Existing custom role grants are preserved. Server checks enforce record scope, action permissions, origin validation, link access, active assignees and optimistic version locking. New ticket creation and job saving share one transaction. Removed jobs are retained in the database with audit history.

## Interface cleanup
Records/Analysis tabs now have a consistent gap above their content. Leave balance tabs use a compact card and smaller buttons. Payment Clear filters, record count and Favorites share a dedicated, wrapping action row with space above it. Outdated demo, browser-only and implementation notices were removed from document, resource, objectives, payments and other screens. Validation messages and relevant reconciliation guidance remain. Existing customer data and uploaded files were not cleared.

## Update and validation
Replace project files using the normal update process and retain the deployed database. Startup adds Application Service tables and role presets automatically; no database reset is needed. The bundled database is unchanged. Existing backup/reset operations include the new tables automatically.

296 Python regression tests passed, followed by seven focused Application Service backend tests including scope, assignment, version conflicts, validation, Helpdesk links, transaction rollback, date queries, export permission, and catalog migration. DOM checks passed for forms, detail toggles, save, Analysis, Favorites restoration, read-only controls, role migration and navigation permissions; existing column-width, disclosure and Instrument Service checks also passed. Thirty Chromium responsive fixture cases passed at 320, 390, 600, 768, 1024 and 1440 px across register, form, Analysis, expanded report and payment/tab layouts. No control overlap, field escape or page-level horizontal overflow was detected. Tabs retained a 16 px content gap; the compact Leave card was 60 px high when buttons fit on one row.

Browser fixtures used fictional data and actual application scripts/styles. Every signed-in production state and physical iPhone Safari have not been verified. The ZIP is not deployed automatically.
