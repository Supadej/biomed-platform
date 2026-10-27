# Instrument Service Management — 28 October 2026

## Placement and setup
The module belongs to Staff Portal because engineers plan and record work there. Biomed IS remains authoritative for customer/product masters, invoices and warehouse postings. No separate login or duplicate customer master is added.

Deploy all application files, retaining the live database and uploads. Restart the Python server, sign out/in, then open Staff Portal → CRM → Instrument Service. System Admin receives service permissions through the catalog migration. Other roles must be explicitly granted service.view, service.edit, service.export and/or service.manage in Roles & Permissions. View grants access to the whole service register, not only an engineer's own jobs. Manage controls historical import and audit visibility. Edit controls create/update. Export controls CSV export. Printing is available to viewers.

The service tables are added to the existing SQLite database on startup. Existing functions, borrowing changes and the private sign-in header are retained. Keep reference/service-import.json with the deployed code; it is intentionally blocked from public static download.

## Workbook coverage
| Source | Module | Coverage |
|---|---|---|
| Instrument List | Instruments | Serial, brand, model, IVD/RUO/Clinical RUO, asset ownership, active/inactive, location, maintenance dates, last visit, comments |
| Individual instrument sheets, row 7 | Instruments | Instrument and computer software versions; serial aliases retained |
| Instrument Tracking | Movement tracking | Date, from/to location, engineer; new movements update the instrument's current location using the latest movement date |
| History | Service jobs | Status, all 12 source job types, job number, description, invoice reference, parts-change reference, date, engineer, customer |
| Spare Part | Spare-part catalogue | Brand, model, catalogue number and description |
| Spare Part Changed ID | Parts replaced | Change ID, job number, instrument, serial, brand/model/ownership, date, location, catalogue, description, quantity |
| Column Data Set | Forms | Source instrument/asset/job type and status choices; brand/model/location/engineer remain editable text to allow new values |
| Instruction and Template | Structure | Template defines record fields; blank numbered history rows are not imported as service jobs |

## Historical import
The supplied database is now preloaded. On existing deployments, a one-time additive startup migration loads missing source records without resetting data. The optional Preview workbook import action remains available for inspection. The source contains 139 distinct instruments, 645 history entries, 220 movements, 507 spare-part catalogue entries and 191 replacement lines (1,702 records). Import IDs are deterministic and repeated imports skip existing source IDs rather than overwriting edits. History rows retain source sheet and row, including duplicate job or change numbers. Original job numbers and invoice references remain text unless manually linked to a verified Biomed IS invoice.

The instrument list contains an identical duplicate serial 100166 at rows 120 and 125. It is consolidated into one instrument with both source rows retained and an import warning. Serial variants such as 00069 versus SN00069 are retained as aliases; no general stripping of leading zeros is performed. Unknown historical job statuses remain blank rather than being marked Completed. Existing historical dates are preserved even where they differ from the filename's July 2026 label.

This import is based on values cached in the supplied workbook. It does not recalculate Excel formulas or import images, formatting, hyperlinks and blank template rows. Maintenance days are computed afresh using Bangkok's current date.

## Daily operations
- Instruments: create/edit, deactivate via status, view full history, record software versions, installation, warranty and explicit PM interval.
- Service jobs: schedule date, assign engineer, record diagnosis/actions/result, follow-up date, labor hours, charge/currency and customer acceptance text. All workbook job types are included.
- Completed jobs require service date, engineer and description. Completing maintenance can update the last visit/maintenance dates and an explicitly entered next maintenance date. The system does not assume every model has the same maintenance interval.
- Movements: preserve from/to and engineer. Use Edit to correct a record; audit history retains prior saves. Records cannot be deleted through this module.
- Spare parts and replacements: record catalogue, quantity and costs; optional warehouse reference. Recording replacement history does not deduct stock. Use the established Biomed IS warehouse approval workflow for actual stock postings.
- Contracts: track contract number, coverage, start/end, PM visits, amount/currency and status. This register does not invoice or recognize budget revenue automatically.
- Customer/product/invoice selectors reuse Biomed IS data when the user has the corresponding master/invoice view permission. IDs are validated on save. Customer/location text from Excel is never silently matched to a master by name.
- Search, brand, status, due-date window and date filters; named favorites; filtered CSV export; expandable instrument history and print-to-PDF service reports.
- Dashboard shows active instruments, overdue/due-soon maintenance and explicitly open jobs. Unknown historical job statuses are excluded from the open-job count.

## Reports and boundaries
Reports retain FM-FSE-08 as a source reference with engineer/customer signature spaces. They are generated reports, not an assertion of approval of a replacement controlled quality form. Browser Print can save a PDF. Customer acceptance is stored as text; it is not an electronic-signature service.

Due indicators are calculated when the page loads/refreshes. Automated email/LINE reminders, recurring job generation, attachment upload, stock deduction, automatic invoice creation, Calendar synchronization and accounting/budget posting are not included. PM interval is stored as a planning field; next dates are entered explicitly. Full browser visual QA and production deployment remain to be performed.

## Validation
Eight new backend tests cover unique serials, stale edits, permissions, orphan links, movement updates, completed PM updates, numeric validation, and full historical import. Existing workflow syntax/interaction, role-catalog and deployment/security regression suites passed. Test imports run in disposable in-memory databases and do not change the live database.


## Permission review update
The original four module permissions have been supplemented with per-record-type view/create/edit/export/print controls for instruments, jobs, movements, parts, replacements and contracts. Import and audit now have separate permissions. The API filters records by type-view permission, requires type-create/edit on mutations, validates linked IS visibility, blocks changing a record's type, and checks export permissions on an authenticated endpoint. Printing is a UI control on viewable data; it cannot prevent a viewer from using the browser's own printing/copying tools.

Three role presets are created once if those role names do not already exist. No existing role is overwritten and no staff account is reassigned:
- Service Viewer: read-only access to all six service record types; no export/print/edit/import/audit grants.
- Service Engineer: read all six types; create/edit jobs, movements and replacements; print instruments/jobs/movements/replacements. No instrument master, part catalogue or contract editing; no bulk export, import or audit.
- Service Manager: all service view/create/edit/print/export permissions, import and audit.
- System Admin: full access through the shared permission catalog.

Use Roles & Permissions to adjust these presets and assign users. Biomed IS customer/product/invoice viewing must be granted separately if master-link selectors are needed. Service view remains module-wide within each permitted record type; this update does not implement engineer-only record ownership. Existing custom roles with only the original broad service.edit need explicit per-type permissions before editing.

Permission regression coverage now includes 11 service backend tests and six role-catalog tests, including entity denial, type-change blocking and custom-role preservation.


## External Helpdesk serial-number integration
Serial Number now appears in the main ticket form beside instrument/model. Enter the serial and save the ticket. Its related section resolves the saved serial against the instrument register's serial or explicit serialAlias, ignoring outer spaces and letter case while preserving leading zeros and punctuation. A unique match provides an Open instrument history link; unmatched or ambiguous values are explicitly reported. Changing a ticket serial changes the match on reopening; no duplicate service job is created.

Instrument details display matching External Helpdesk records with problem, solution, status and a link back to each ticket. This is a linked history view, not a second editable copy. Helpdesk permissions and own/team visibility restrict the reverse list. Opening service history requires service.view and service.instruments.view; External Helpdesk still requires crm_view and crm.tickets.view. Existing account assignments are unchanged. Matching becomes available after instrument records have been imported or created.

Additional tests cover serial aliases, leading-zero preservation, ambiguous aliases and hidden Helpdesk data without permission. Fourteen service backend tests, ten Portal CRM tests and JavaScript regression checks pass. Visual browser verification remains outstanding.


## Preloaded database and responsive fixes — latest update
The shipped SQLite database contains 139 instruments, 645 jobs, 220 movements, 507 parts and 191 replacement records. Existing deployments receive missing records through the fse-jul2026-v1 startup migration. Existing instrument serials are reused with dependent history references remapped; existing values are retained. A migration marker and audit trail record completion, and repeated starts do not overwrite edits. Do not replace a live database with the supplied database: deploy code and restart instead.

Helpdesk instrument links now use wrapping inline-flex layout, explicit line-height and spacing. Command bars, stage buttons, notebook tabs and service forms constrain their widths, wrap controls and use one-column phone layouts. Wide data tables scroll within their own containers. Dialogs are constrained to the viewport. Breakpoints address phone, tablet and desktop layouts, but actual rendered geometry at each viewport has NOT been verified: Chromium installation failed in this environment. No claim of an all-screen visual pass is made.

Validation: 16 service tests (including additive/idempotent startup seeding and preservation of existing data), 10 Portal CRM tests, service permission UI checks and existing workflow checks passed. The DOM detail suite could not run because jsdom is unavailable. SQLite integrity check returned OK.


## Staff Portal layout consistency
Removed the standalone navy Instrument Service banner and its Staff Portal/Biomed IS buttons from the HTML entirely. Removed the script that could re-display it. Direct service URLs now route through Staff Portal and preserve the instrument selection, so the existing portal header and sidebar remain authoritative. The inner page uses Staff Portal heading, content width, card, color and spacing conventions without a second layer of outer padding. Header-removal and workflow regression checks passed; rendered visual verification remains unavailable.
