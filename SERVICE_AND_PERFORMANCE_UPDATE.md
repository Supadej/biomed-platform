# Service and performance update · 28 October 2026

This is an updated local application package. It does not deploy or overwrite an existing installation's persistent database.

## Daily numbering

All new references use the current Bangkok creation date and a two-digit year. References are reserved inside the SQLite write transaction, remain reserved after deletion, and are unchanged when the record is edited. Existing document and historical service references are retained.

| Document | Format |
| --- | --- |
| Service job / external Helpdesk job | BMDSDD-MM-YY/# |
| Quotation | BMDQDD-MM-YY/# |
| Customer Order | CORDDD-MM-YY/# |
| Sales Order | SORDDD-MM-YY/# |
| Withdrawal | WDD-MM-YY/# |
| Borrowing | BDD-MM-YY/# |
| Return | RTDD-MM-YY/# |
| Purchase Requisition | PRDD-MM-YY/# |
| Purchase Order | PODD-MM-YY/# |
| Delivery In | DIDD-MM-YY/# |
| Delivery Out | DODD-MM-YY/# |
| Invoice | IVDD-MM-YY/# |
| Credit Note | CNDD-MM-YY/# |
| Debit Note | CNDD-MM-YY/# |

Credit and debit notes intentionally share the requested CN prefix and daily sequence. Service jobs and Helpdesk jobs share the BMDS sequence. Number assignment occurs on successful save, rather than reserving a number when an empty form opens. Existing UUID/database IDs and source links are not replaced by display references.

## Service reference lists and responsibilities

Open Staff Portal → Instrument Service → Service reference lists. A user needs `service.manage` to maintain brands, brand-specific models and locations. Lists start with existing workbook values, deduplicated without changing historical records. Models depend on the selected brand. Movement From/To use the same location list. Removing a choice does not invalidate an unchanged historical value; new values must come from the approved list.

Engineer choices use active Staff Portal employees whose current role grants service job creation or editing, plus System Admin. Disabled accounts and inactive profiles are excluded. Names are displayed; stable employee IDs remain the stored relationship. Existing engineer names remain readable in historical records.

`service.references.view` permits Biomed IS customer, product and invoice lookups within service forms. The startup permission migration grants it to existing roles that already have `service.edit`; the built-in Service Engineer and Service Manager presets include it. Custom roles can be reviewed in Roles & Permissions. Service Viewer does not automatically gain source-master lookup access. Reference-list administration remains restricted to service managers.

Customer, product and invoice entry supports search and explicit selection. The picker renders at most 20 matches at once and stores the selected source ID; typing arbitrary text does not bind a source record.

## Parts within service jobs

Declare a spare part by selecting a Biomed IS product in Spare-part catalogue and binding it to a brand/model. The catalogue number and name come from the source product, rather than manual text. Duplicate product/brand/model declarations are rejected. Unlinked historical workbook parts remain visible and are flagged in data quality monitoring; they cannot be used on new job lines until an IS-backed declaration exists.

Open a Service job and use Add spare part. Each line records the declared part, positive quantity and nonnegative unit cost. Brand/model compatibility is checked again on the server. Lines are saved atomically inside the job, with no new part-change document ID. The separate Parts replaced creation tab is removed. Historical replacement records are retained in instrument history and matched job details; unmatched historical references remain explicit for review.

Recording parts used does not post warehouse stock or create an invoice. Use the existing Biomed IS withdrawal and stock-posting workflow for physical inventory movements.

External Helpdesk uses the same brand/model/location lists, service employee choices, searchable IS references and automatic BMDS numbers. Its parts editor selects declared IS spare parts. Existing service-charge descriptions and historical ticket lines remain supported.

## Operational analysis

- **Instrument Service → Performance analysis:** defaults to a recent 12-month service-date period, with period, brand, engineer and searchable customer filters. Includes job completion trend, follow-up aging, PM coverage and missing schedules, overdue PM by location and model, engineer workload, recorded labor, repeat repair candidates within 90 days, parts quantities/costs, contract expiry and actionable review queues. All history is available explicitly. Engineer filters apply to jobs; installed-base PM/contract monitoring is current-state monitoring.
- **Sales Plan → Analysis:** graphical invoiced achievement versus 100% incentive targets by product and sales area. Overlapping scheme periods are deduplicated. Area totals use the employee's single assigned CRM sales area; missing and multiple-area assignments remain unallocated instead of duplicating the same target. Maintain CRM employee sales-area assignments to improve area analysis. Financial opportunity charts exclude non-THB amounts.
- **External Helpdesk → Analysis:** open-ticket inactivity, overdue work, assignment and date completeness, with a priority follow-up table. Employee names and service-stage names replace raw IDs where source records exist.
- **Calendar → Analysis:** responsible employee names, reporting coverage and a list of past events missing reports.
- **Project & Activity → Portfolio analysis:** workload/cost analysis and over-budget activities requiring review, using visible project/activity records.
- **Budgeting → Performance analysis:** closed-month revenue achievement, product gaps, expense overruns, commitments and completeness checks by cost center. Month input changes update the row total, footer and visible summary figures while retaining focus in the input.

Charts have explicit cohorts and missing-data notes. Status completion is not a response-time SLA or first-time-fix measure. Repeated repair counts indicate instruments to investigate, not a failure rate adjusted for utilization. Labor totals do not measure utilization without available capacity. Service amounts remain separated by currency; parts cost totals explicitly identify THB-only coverage. Newly completed jobs record a completion timestamp for future monitoring; no historical completion timestamp is fabricated.

Navigation icons now distinguish service, calendar, projects, sales planning, revenue targets, COGS, compensation, health, travel, training, finance and administration.

## Installation and persistence

Back up the existing installation before replacing application code. Keep its existing `BIOMED_DATABASE_PATH` / data volume. Startup applies additive schema and permission migrations; the shipped database is used only when a persistent database does not exist. Historical references are retained. No live deployment has been performed by this update.

## External Helpdesk instrument picker

The serial field is now a searchable Instrument Service picker, like the instrument selection on a service job. Search by serial, serial alias, brand, model or location and explicitly choose an instrument. Its stable ID is stored as `ServiceInstrumentId`, while the canonical serial, brand/model and location are populated for a new selection. Open instrument history is available beside the picker, and the saved ticket appears in the instrument's Helpdesk history. A stored link survives later serial corrections. Source customer/product references populate when available to the user's lookup permissions.

New or changed serials must resolve to an existing instrument; ambiguous and unknown references are rejected. Unchanged historical unmatched serials remain editable. Startup adds explicit links to historical tickets only when the existing serial or explicit alias matches one instrument, retaining the original serial and other historical snapshot fields. Lookup and history access retain their permission checks.

## Helpdesk referrals and ticket form · latest update

A Helpdesk ticket is an optional referral parent for multiple service jobs and movements. Each work record keeps its own identity, job number, instrument, status, dates, report, parts and charges. The ticket serial is context and does not constrain every referred job or movement to the same instrument. No statuses, job numbers or charges are synchronized into the parent ticket.

- From a saved Helpdesk ticket, use **Create service job**, **Create movement**, or **Link existing job / movement**. Creation opens a draft with the ticket referral selected; a record is created only when saved.
- In a service job or movement's Edit form, select an existing Helpdesk referral or check **Create a new Helpdesk ticket when saving this record**. Creation of the ticket, service record and referral occurs in one database transaction. A failed or stale service save rolls back the new ticket as well.
- Each work record has one optional ticket referral; a ticket can have any number of work records. Referrals can be changed or cleared by authorized users. Referral changes are audited in the ticket history. A ticket with linked work cannot be deleted accidentally; it can be closed independently.
- Existing-record linking checks the source record's version and edit permission. Ticket visibility and assignment scope still apply. Service users need Helpdesk view access to select referrals and Helpdesk create access to create tickets. This update does not reassign users or grant additional access to custom roles.

The free-text **Instrument** field is removed; the searchable **Serial number** picker remains. Brand and model are selected from that instrument automatically. Priority choices are High, Normal and Low. Unrecognized historical priority codes are standardized to Normal during the one-time startup migration, with the original code retained as LegacyPriority for reference; no meaning is inferred from the old numeric code. Currency choices are THB, USD, EUR and CNY for new selections. Responsible person choices include active employees whose roles can access External Helpdesk, rather than only engineers. Service stage remains a dropdown without a search box.

**Parts & Service** is a read-only view of the linked jobs' parts, service reports, labor hours and service amounts, with the originating job and currency displayed. It refreshes when the ticket opens, when returning focus from another work tab, or via **Refresh linked work**. Updating a source job does not create duplicate ticket items. Legacy manual ticket items and service figures remain in a collapsed reference section; new labor and service charges are maintained in the source jobs. The ticket's own closure requires a responsible person and solution, and does not require duplicating a service job's service date.

## Latest Helpdesk presentation

Parts & Service now contains exactly three work tables: Service Jobs, Spare Parts Used and Movements. A single toolbar in that tab provides creation, existing-record linking and refresh actions. The repeated referral section below the form has been removed. Existing-record selection opens a separate panel with explicit input/action spacing and a Cancel action.

Fees is a separate validated, nonnegative ticket field, placed immediately before Currency. Customer Acceptance is on its own following row. Ticket fees do not overwrite the charges on linked service jobs. The print action is in the ticket command bar, and the serial picker provides the instrument-history link without a duplicate card below the form.

The link picker and action controls were checked at 320, 390, 640, 768, 1024 and 1440 pixels. The input-to-button gap is 16 pixels at those widths. The three work tables retain column customization and horizontal scrolling.

Human Resources now includes Minutes and Acknowledgement. See MINUTES_AND_ACKNOWLEDGEMENT_GUIDE.md for selected-employee access, authoring permissions and acknowledgement behavior.
