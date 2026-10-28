# Budget setting and Finance workflow — update 36

## Available in this update

Open Budgeting → Set targets & finalize performance. The Revenue page opens the same source-level workspace.

1. Review the prefilled target rows grouped by shared brand (or Other revenue), expense category and cost center. Existing detailed records remain available to the existing reports and integration mappings; no 300,000-item catalogue is loaded into this workflow.
2. Add sources: Brand (select shared master), Service, Miscellaneous or Other. Examples: maintenance contracts, repair fees, rental, training and other income. Add COGS targets and expense-category budgets as needed.
3. Enter all 12 May–April monthly targets. Entering an annual amount spreads it over 12 months to the cent. Save a draft or submit it.
4. A different authorized employee reviews it through Department → Finance → Director stages. Return requires a reason. Final approval publishes the targets to existing budget reports and preserves an approved revision snapshot. New revisions are edited here; ordinary spreadsheet-like budget edits are blocked after an approved baseline exists.
5. Record monthly actual totals by brand/service/expense source. Existing detailed entries are aggregated; entering a group total distributes it across existing records proportionally, retaining their IDs and mappings. Do not record both a new source and its included brand amounts. Currency is THB; conversion must occur before entering totals.
6. Verify supporting records, then submit a completed fiscal month for performance approval. The review freezes target baseline and actuals, with target/actual/variance details. Approval finalizes and locks that month. Half-year and annual review require every included month to be finalized first. Future or unfinished periods cannot be closed.
7. Director permission and a reason are required to reopen finalized performance. Reopening a month also reopens overlapping finalized half-year/annual summaries. Actuals that change during review require return and resubmission. Workspace saves, restores, aggregate actual entry and Portal-budget reconciliation honor the period locks.

Permissions reuse the existing Roles & Permissions → Budgeting → Approvals grants: view, submit, department_approve, finance_approve, director_approve and return. Recorded actuals require the relevant revenue/COGS/expense actual-entry permission. Company-wide planning requires view access to all included schedules. A user cannot approve their own submission, even as System Admin. Separate reviewer roles should be assigned to real staff accounts. Budget approval and performance approval do not approve inventory or accounting documents.

The variance register compares current entered actuals with approved annual targets and exports CSV. Performance details compare the exact selected period against its frozen baseline. Original workbook/source values remain distinguishable from approved targets. Performance approval is an internal management control, not automatic proof of bank, tax or general-ledger reconciliation.

## Recommended next functions (not implemented in update 36)

| Priority | Function | Purpose |
| --- | --- | --- |
| 1 | Rolling 13-week cash-flow forecast | Weekly opening cash, expected collections, supplier payments, payroll and closing cash; highlight shortfalls. |
| 1 | Receivables and payables aging | Current, 1–30, 31–60, 61–90 and over-90-day balances; collection owner, promise date and payment plan. |
| 1 | Budget availability and commitments | Show approved budget less actuals and approved PO/requests; avoid double counting once invoices replace commitments. |
| 1 | Monthly close checklist | Assign bank reconciliation, cut-off checks, accrued costs and document completion; evidence and reviewer sign-off. |
| 2 | Rolling forecast and scenarios | Keep approved budget fixed while Finance forecasts remaining months; best/base/worst case and cash impact. |
| 2 | Brand/service profitability | Gross margin after inventory cost, service parts, labor, freight, discounts and allocated overhead. |
| 2 | Variance thresholds and explanations | Absolute and percentage limits, named owners, due dates and corrective actions. |
| 2 | Customer credit and collection control | Credit-limit utilization, overdue balances and controlled order-release exceptions. |
| 3 | Multi-currency planning | Approved budget FX rates, transaction rates, exchange variance and cash exposures. |
| 3 | Capital expenditure register | Investment approvals, committed spend, asset handover and forecast depreciation. |
| 3 | Reconciliation and audit exports | Trace each aggregate to source document and support month-end Finance review. |

Suggested order: commitments and aging first, then cash-flow forecast, then a close checklist and rolling forecast. These functions can use existing IS documents and Portal requests, with explicit rules for statuses, dates, currency and duplicate posting.

## Delivery and validation

This is a source-package update. Deploy it to update the live application. Governance data is stored separately in the existing SQLite database, created on first use; historical records are preserved. No actual budget approvals or period closures have been fabricated in the bundled database. QA uses a separate database.

Validation: four governance regression tests cover target publication, independent approval, permission/amount/version validation, period closure and reopening, stale-review return, aggregate actual entry and rollback of locked writes. Twelve integration tests and six role-catalog tests pass. Browser checks cover 320, 768 and 1440 px, twelve-month annual spreading, source-level service targets and persistent drafts.
