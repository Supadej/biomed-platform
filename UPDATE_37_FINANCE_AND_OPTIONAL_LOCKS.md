# Update 37 — Optional period locks and Finance planning

## Period locks

Financial → Set targets & finalize performance now shows the lock policy. Authorized users can enable or disable it with a recorded reason. Performance approval and period locking are separate: approved snapshots remain available even when locks are disabled. The original default remains enabled.

Use Unlock / reopen with reason for an individual approved period. Reopening also reopens overlapping half-year/annual approvals and preserves the history. If actuals change while the policy is disabled, enabling it again marks affected approvals Reopened so corrected actuals must be reviewed again. Half-year and annual review require current, approved monthly snapshots. Approved target-budget revisions remain controlled separately through budget resubmission.

Roles & Permissions includes:
- `budget.periods.configure`: configure lock policy.
- `budget.periods.unlock`: unlock/reopen performance periods and Finance close checklists.
- `budget.finance.view`: read Finance workspace.
- `budget.finance.edit`: maintain obligations, reconciled settlements, forecast and close tasks.
- `budget.finance.review`: independently approve or return submitted Finance close checklists.

System Admin receives all catalog permissions. Accounting, Managing Director and Operations Director receive the Finance view/edit/review grants on migration; Managing Director and Operations Director also receive lock-policy and unlocking grants. Other roles can be customized. Finance access additionally requires IS invoice and purchase-order view permissions and access to all included budget schedules. Users cannot approve their own close checklist or performance submission.

## Finance planning & control

Open Financial → Finance planning & control.

### Commitments

Shows approved THB budget, entered actuals, booked commitments, additional mapped unbilled POs and remaining budget. Approved POs are listed with mapping exceptions. Choose an approved expense/COGS source and explicitly indicate whether the PO is already included in booked commitments; the default prevents adding it twice. Supplier bills linked to a PO reduce its unbilled commitment. Foreign-currency POs remain separate pending approved conversion rules. An unmapped PO does not silently consume an arbitrary budget line.

Book supplier bills and recognized costs consistently: AP entry is a Finance obligation, not an automatic posting to budget actuals. The difference between booked costs, unbilled commitments and unpaid liabilities must be reconciled by Finance.

### Receivables/payables aging

Uses approved IS customer invoices net of directly linked approved credit notes, plus Finance-entered supplier bills and external customer balances. Buckets are Current, 1–30, 31–60, 61–90 and over 90 days, separated by THB/USD/EUR/CNY.

Due-date omissions are flagged and fall back to document dates. Source receipt documents are not guessed to be fully applied payments. Record each verified payment/receipt reconciliation once with a unique bank/receipt reference, date and amount. Partial settlement is supported; overpayment, duplicate references and future-dated actual settlement are rejected. Incorrect entries can be voided with a reason; historical entries remain in the audit. Obligations with live settlements cannot be voided until their settlements are corrected.

These are operational reconciliation balances, not an authoritative general-ledger subledger. Reconcile existing receipts and supplier accounting before using them for collection/payment decisions. Finance does not send payments or emails.

### Rolling 13-week cash flow

Shows weekly opening cash, inflow, outflow, closing cash, a closing-cash graph and shortfall flags for each currency. Enter a start-of-day opening bank/cash balance and as-of date; negative balances/overdrafts are supported. Missing or stale opening balances are flagged. The horizon rolls from the current week or the opening date when later in that week.

Outstanding obligations use their due date or an expected cash date entered by Finance. Overdue items enter the first forecast week. Reconciled settlements since the opening date and additional manual movements are included in the applicable week. Do not duplicate an invoice as an additional cash entry. Different currencies are never added together without FX conversion. Additional forecast entries can be voided with a reason.

### Monthly close checklist

Standard tasks cover bank reconciliation, AR/receipts, AP/supplier statements, cutoff, inventory/service parts, accruals/prepayments, tax supporting schedules and management variance review. Assign an employee to every task; completed tasks require a supporting reference.

Save completed tasks, then submit a month that has ended. Another authorized reviewer approves or returns it. Actuals changing after submission require the checklist to be returned and rechecked. Close submissions preserve Finance and budget-actual snapshots. Unlocking requires authorization and a reason. This checklist does not automatically finalize performance or attest compliance with accounting/tax rules; use the separate performance approval workflow for that.

Finance obligations, settlements and forecast registers are shared across fiscal-year views, preventing the same source invoice from reappearing unpaid simply because the displayed fiscal year changes. Close checklists remain scoped by fiscal year and month.

## Validation and deployment

Regression tests cover Finance amounts, permissions, partial settlements, duplicate/overpayment/void guards, currency separation, PO mapping without duplicate commitments, checklist separation of duties, stale versions, optional locks and authorized unlocking. Browser checks cover all five Finance tabs at 320/768/1440 px, supplier-bill entry and lock-policy controls. Existing integration and role-catalog checks are retained.

Deploy this package to update the live application. New SQLite tables are created on first use. The included database contains no fabricated Finance settlements, approved close checklists or lock-policy changes; test transactions were run against a separate QA database.
