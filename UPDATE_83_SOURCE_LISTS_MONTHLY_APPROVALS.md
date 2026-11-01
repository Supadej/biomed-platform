# v83 — Source references, expense selectors and monthly approvals

## Finance reset on first deployment

This release implements the requested empty Finance database on an existing installation, rather than only supplying an empty starter file. At first startup it backs up the SQLite database beside the working file as `<database-name>-before-finance-reset-v83.sqlite3`, then clears Finance fiscal-year records, cost centers, expense/product planning items, budgets, actuals, commitments, financial entries, approvals, Finance workspace records, Express profiles/imports and old financial reference data. The active fiscal year remains as a blank year. Accounts, roles, reporting hierarchy, website, Staff Portal, CRM and Biomed IS data are retained.

The reset has a database marker and runs once. Later startups preserve new Finance setup and entries. Keep the current Railway volume mount and BIOMED_DATABASE_PATH. Do not replace the working database manually. This package has not been deployed by the developer. Backup files are blocked from public static download, like the working database. Old integration mapping settings for the other systems are retained; review Finance bridge mappings after recreating cost centers/items.

## Budget form

- Source References is a dedicated tab within Annual & Monthly Budget. Authorized budget submitters can add source names, edit unused names and deactivate/reactivate references. Names with budget history cannot be renamed; deactivate and create another name instead.
- Service / other revenue source is now a dropdown from that reference list, shared by non-brand Revenue and COGS plans.
- Expense Item is a dropdown filtered by Expense menu / category, using active items created under Manage expense items. Choosing an item selects its cost center. Existing items automatically appear in the annual grid; selecting an already included item brings its annual amount into focus.
- COGS uses the label COGS Type; Revenue uses Revenue source type.
- Brand type requires Shared brand and disables the service/other source dropdown. Other types require the source dropdown and allow an optional Shared brand.
- Existing historical lines remain traceable when a reference becomes inactive.

## Annual and monthly approvals

The visible tabs are Annual Budget, Annual Budget Approval, Monthly Budget Approval, Source References, Performance Finalization, Actual Expense Recording, and Budget vs Actual.

1. Create cost centers and expense items; create service/other source references as needed.
2. Enter annual targets with all twelve fiscal-month allocations (or spread an annual amount).
3. Submit the annual budget; Department, Finance and Director approval establish the annual baseline.
4. Open Monthly Budget Approval. Each month has its own Submit month action and approval status. The same authorized approval stages apply to that month's frozen allocation.
5. Only the approved monthly allocation becomes effective for spending control. Annual approval does not automatically activate months. Performance Finalization closes actual results separately.

Revenue is a gain; COGS and all expenses are costs. Company earnings before tax remains available in the annual planning and analysis views.

## Verification

Six Python tests pass, including source-reference validation, invalid expense/category rejection, annual publication across every expense category, separate monthly approval activation, prevention of direct budget changes, announcement history, staff preservation, and a backed-up reset that runs only once. All inline and external JavaScript syntax checks pass. Browser-rendered visual verification is unavailable in this environment.
