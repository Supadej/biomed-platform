# Configurable integration bridges

## Where to configure

Sign in as System Admin. Staff Portal → Website & Administration → Biomed IS bridge settings → Open bridge settings configures IS → Staff Portal. Budgeting → Monitoring & Control → Staff Portal reconciliation → Open bridge settings configures Portal → Budgeting for the current fiscal year. Both connections are also accessible from integrations.html. Existing IS → Budgeting reconciliation remains separate.

## Biomed IS → Staff Portal

Enable quotations and/or approved invoice sales. Choose quotation statuses, net/gross/VAT-inclusive values, document/due date, the representative or owner source field, employee overrides, product-ID-to-Portal-product-line mappings and explicit THB currency rates. THB must remain 1. Exact existing staff IDs and valid document product-line names are used when no override exists. Names are not used as linking keys. Invoices remain approved-only; approved linked credit notes can be deducted. A multi-product invoice is split by product-line weights. Foreign currencies without configured rates, missing staff/product mappings and invalid dates appear as exceptions.

Save settings → Preview saved rules → Synchronize preview. Quotation/Tender/Pipeline and Sales Performance then use a saved integration snapshot. Refresh Staff Portal after sync. Incentive actuals that use Sales Performance use the same projection. Follow-up metadata and manual opportunities are retained. Only older automatically generated records identified by the legacy biomed-is-v50 source prefix are retired during the first reconciliation. The old approval-time fixed bridge is replaced by deliberate preview/sync; approvals no longer trigger a hidden reconciliation.

## Staff Portal → Budgeting

Choose an existing fiscal year, enable the bridge, and select expense claims, incentive claims and optional travel/budget requests. Map source type, category and/or employee department to an active expense budget line. Its cost center is used. Blank category/department means all; more specific rules win. Ambiguous rules are exceptions. Other Cost of Sales/COGS lines are excluded from this bridge.

Approved unpaid claims become commitments. A linked payment with Paid status replaces the commitment with an Actual. Choose approval/payment dates or the source claim/request date. Amount recognition can use the full approved claim amount (including advances) or the paid reimbursement amount. Portal expense amounts are treated as THB because their existing claim workflow already converts daily currency items. Payroll/headcount and inventory COGS are not automatically imported.

For optional travel/budget request commitments, link the resulting expense claim using its Linked approved travel / budget request field. An approved linked claim replaces the original request commitment. If no explicit link exists, requests and claims cannot be reliably deduplicated; leave request importing disabled until your team uses those links.

Fiscal years follow the existing May–April calendar. Reconciliation refreshes ONLY this bridge's ledger contributions across all configured years. This allows a payment in a later year to release the earlier-year commitment. Existing manual and Biomed IS entries are retained. Missing target fiscal-year settings appear as exceptions. Turning a year/stream off and reconciling removes its previously generated contribution. Cancellation/unapproval or remapping is also reflected on the next sync. No source document statuses are changed.

## Preview, permissions and history

Settings are saved separately from synchronization. Preview must use the latest saved settings. The server rejects a stale preview if source data/settings changed. Exceptions block synchronization unless the operator explicitly permits eligible records only. Review the proposed rows, exceptions and previous bridge postings that will be replaced. Refresh the destination application after syncing.

New integration permissions are granted to System Admin at startup. Other roles need integration access/view/edit/reconcile as appropriate. IS → Portal operators also need Biomed IS access and relevant quotation/invoice/credit-note views. Portal → Budgeting operators need Budgeting access, the enabled Portal source-module views, Payment processing view for actuals, and the affected budget schedule view/actual/commitment grants. Configure these under Roles & responsibilities. Removed permissions are not broadly regranted.

Each synchronization records operator, time, counts, exception count and the rules used. Synchronization is manual; no background job runs. Settings, history, projections and postings are all database-backed. Copying the SQLite database preserves them. Tables are added automatically at startup; existing records are retained. The package remains the local SQLite application, with the previously documented SQL Server runtime-adapter limitation.

## Validation

Run python3 tests/test_integrations.py. Eleven cases cover mapping/calculation, credit-note deduction, explicit FX, unmapped records, repeated-run idempotency, cross-year commitment-to-actual conversion, cancellation, ambiguous rules, request/claim linkage, permissions, preview tokens and snapshot privacy. Existing workflow, website and language checks also pass. Native browser interaction remains unverified.
