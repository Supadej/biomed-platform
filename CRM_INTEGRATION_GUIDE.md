> The standalone CRM frontend described below has been replaced. See **STAFF_PORTAL_CRM_UPDATE.md** for current feature locations and setup. The schema and compatibility API information below is retained for reference.

# Biomed CRM integration

This package is a complete copy of the existing platform (GitHub base d227472) plus the supplied ERP frontend integrated under `/crm/`. It uses the existing Python server, SQLite database and Staff Portal account session. It has not been pushed to GitHub or deployed to Railway.

## Run locally

From the extracted project directory (`bash start.sh` is also available):

```bash
python3 serve.py
```

Open `http://127.0.0.1:8765/?portal=1`, sign in with your existing account, then choose **CRM**. The direct entry is `http://127.0.0.1:8765/crm/index.html`.

The existing `START_ON_MAC.command` and Railway start command remain available. Python uses the standard library; the CRM server adds no Python packages. Browser charts, tables, icon fonts, pivot and relationship visualization still require their supplied third-party CDN libraries. Core forms and bridge screens are served by this project.

## Update an existing Railway project

Copy the extracted project files into the root of the existing GitHub repository, commit and redeploy. Retain the same service, persistent volume, `BIOMED_DATABASE_PATH`, public-domain/origin settings and start command. **Do not replace an existing server database with the demo `data/biomed.sqlite3`.** Startup creates missing CRM tables and upgrades the permission catalogue; it never replaces an existing volume database. Keep a backup before updating. This download does not itself update the live service.

## Accounts and permissions

CRM has no independent password store or JWT sign-in. `/biomedapi/*` and `/api/crm/*` check the shared HttpOnly session cookie on the server. Signing out invalidates access to all systems. Direct CRM links return to that CRM page after Staff Portal sign-in.

Staff Portal → **Roles & permissions** now contains CRM application access and module/action grants. System Admin receives newly introduced CRM grants on migration. Existing custom roles receive no automatic CRM grants. For another role, enable `crm_view`, the module's `.view`, and the actions it needs. Do not enable the entire CRM group when only sales access is intended.

Leads, events, activities and tickets support own/assigned records. Grant `.view_all` for all records and `.assign` to assign other staff. CRM files have separate view/upload grants. CRM audit returns only the current actor’s entries unless `crm.logs.view_all` is granted. CRM employee IDs are bound to Staff Portal user IDs; shared names, emails, account enablement and role grants remain managed by Staff Portal. CRM can edit profile contact details and product/territory assignments. Create/disable sign-in accounts in Staff Portal.

Some supplied screens request related master data and create change logs before saving. A sales editor normally needs users/contacts/products/territories/pipelines view plus leads view/create/edit, and logs view/create. Calendar editing needs related contacts/products/users view and events view/create/edit plus logs view/create. Project activity editing needs projects/project_stages/activities and related staff/contact view plus logs. Helpdesk item editing also needs ticket_items actions and inventory view. All writes are checked independently by the API; a visible legacy button cannot grant authority.

Stock receipts/issues preserve signed ledger quantities. Authorized deletion is audited and rejected if it would create a negative lot balance. CRM stock and Biomed IS stock are separate ledgers. Bridging IS stock creates a snapshot only.

## Bridge settings

Open CRM → **Bridge settings**, Staff Portal → **CRM bridge settings**, or the CRM links on the existing integration settings screen.

1. Choose Biomed IS, Staff Portal or Budgeting → CRM.
2. Choose record sections and individual attributes. Set document statuses/kinds or fiscal year where applicable.
3. Review destination IDs in **Master data & targets**. Provide explicit mappings where IDs differ. Mapping JSON examples: `{"source-staff-id": 2}` or `{"budget-product-id": 3}`. `pipelineMap` maps Portal stage/status labels to CRM lead pipeline IDs. `ticketPipelineMap` maps Portal helpdesk status labels to CRM ticket stage IDs; otherwise the first configured CRM stage is used while the source status is retained. Budget product mappings point to CRM **portfolio products**, not inventory SKUs. `customerMap` points IS customer IDs to existing CRM organization IDs. `costCenterMap` changes cost-center labels; it does not map sales territories.
4. Save, preview, review every exception and proposed record, then reconcile. Source access and destination import grants are both required. CRM bridge view/edit/reconcile are separate grants.

Reconciliation updates by source ID, keeps source and last-sync metadata, and records a run history. It does not fuzzy-match names, create a two-way sync, run automatically, post finance transactions or change source systems. Saved bridge rules default to block runs with mapping exceptions. Partial mode must be explicitly saved. Source/config changes invalidate the preview token. Source-owned imported records are read-only in CRM; edit the source and reconcile again. Reconciliation retains snapshots when source records disappear; review their timestamps before using historical data.

### Recommended bridge attributes

| Source | Recommended attributes | Destination / purpose |
| --- | --- | --- |
| Biomed IS customers | Customer ID, organization name, contact, email, phone, billing address, tax ID, department | CRM organizations, departments, contacts and billing information |
| Biomed IS catalogue | Product ID, catalogue number/SKU, brand, product name, unit, barcode, storage | CRM inventory brands and product catalogue; retained source ID |
| Biomed IS transactions | Approved quotation/customer order/invoice reference, document kind, date, customer ID, status, currency, source reference, lines | Linked read-only snapshots for sales follow-up. Snapshot amount is quantity × price **before discounts/VAT**; open IS for authoritative totals and settlement status |
| Biomed IS stock | Product ID, warehouse, lot, expiry, quantity, held status | Read-only availability snapshots; never a second stock posting |
| Staff Portal people | Stable staff ID, name, work email, department, manager ID | Shared CRM identity plus selected staff metadata; no passwords, salary or authentication data |
| Staff Portal pipeline/tenders | Opportunity/reference ID, owner, customer, product line, expected/quoted value, stage/status, closing/deadline | Assigned CRM lead snapshots with source details |
| Staff Portal visits/helpdesk | Visit date, institution, discussion/next action; ticket ID, title, details, priority, owner, created date/status | CRM calendar/service snapshots. Original status is retained; source-specific workflow enums may require review |
| Budgeting | Fiscal year, product ID, cost center, monthly revenue target/actual, expense budget/actual/commitment | CRM targets and linked planning snapshots; explicit product ID mapping required |

Customer name fields on Portal manual entries are retained as source text; they are not silently merged with IS customers by name. Budget expense categories, cost centers and CRM sales territories remain distinct. Source role filtering applies before previews; hidden financial columns do not become accessible through a bridge.

## Supplied ERP source and SQL

`reference/ERP_Source_Code_Original.zip` preserves the supplied archive, including historical files. `reference/ERP_Original_Schema.sql` preserves the supplied SQL. The server blocks browser access to this reference directory.

The archive provides frontend pages and scripts but **does not include the `/biomedapi` backend** referenced by those scripts. A new compatibility backend implements the browser API on the project's existing database. Thus backend behavior has been reconstructed from frontend contracts and the SQL schema, not copied from a supplied API implementation. No claim is made that an unavailable backend's behavior was reproduced exactly.

The SQL contains 37 table definitions and **no data INSERT statements**. CRM initially seeds pipeline labels only; no historical ERP records have been imported. Use the bridges for the existing platform's data. A separate ERP database export would be required to migrate historical ERP records.

The original Invoice menu refers to a page missing from the archive. The integrated menu provides **Linked documents & budgets** and links into authoritative Biomed IS documents instead. The original unauthenticated ticket-report URL is adapted to the shared authenticated API and the standard report letterhead. The preserved reference archive retains the original files.

## SQL Server 2012

The live application still runs SQLite. `crm_sqlserver2012.sql` creates a SQL Server 2012-compatible CRM **staging** schema without JSON SQL functions. `export_crm_sqlserver.py` exports the CRM records, bindings, files and bridge history as inserts for an empty staging target. It excludes login credentials and sessions. Run the schema before reviewing/running the exported data:

```bash
python3 export_crm_sqlserver.py --database data/biomed.sqlite3 --output CRM_Data.sql
```

This is an export path, not a SQL Server runtime adapter. Direct deployment against SQL Server requires a tested database adapter and a planned migration of the original platform's data as well. Do not point `BIOMED_DATABASE_PATH` at a SQL Server connection string.

## Validation and limits

The project includes CRM regression tests for CRUD/relationships, granular grants, own/assigned scope, session enforcement/revocation, uploads, stock constraints, date/product filters, source immutability, mapping exceptions, repeat reconciliation and stale previews. Existing platform tests are retained. Run:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

New and supplied browser scripts and inline scripts have passed syntax checks, and local asset links have been checked. Desktop/mobile browser rendering and every legacy interaction still require acceptance testing in the deployed environment; no full real-browser rendering test was available in this build environment. Review each role with a test user before production use.
