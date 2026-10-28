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
