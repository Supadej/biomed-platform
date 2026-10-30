# Biomed test workspace

All operational records and figures in this copy are fictional samples. The original package remains separate. No real customer, patient or employee data is included.

## Start on Mac

Stop the older Biomed server with Control+C. Extract this ZIP into Downloads, then run:

```bash
cd ~/Downloads/Biomed_Workspace_Improvements_Mac
chmod +x START_ON_MAC.command
./START_ON_MAC.command
```

- Staff Portal: http://127.0.0.1:8765/?portal=1. Use an account from your existing database. This ZIP contains no seeded test accounts. For a deliberately fresh installation, create the first administrator with python3 setup_admin.py.
- Biomed IS: http://127.0.0.1:8765/biomed-is.html
- Financial: http://127.0.0.1:8765/biomed-budget.html

## Included

30 customers; 12 suppliers; 40 products (including one inactive); 3 warehouse locations; 107 documents covering every current IS transaction type; 176 stock movements. Sales and purchasing chains, linked invoice/credit note, borrowing/return, an automatic shipment for each completed Check Out, draft and pending/rejected records, expired stock, a quarantined lot, a pending count variance, a pending warehouse transfer and a kit definition.

The Portal includes 7 users, reporting lines, HR profiles, leave entitlements, requests and bookings, tasks, helpdesk tickets, visits, demos, appraisals, training and trainer requests, three employee lifecycle cases, expenses, an incentive scheme/withdrawn claim and an accounting payment request. Quotation and pipeline examples read the seeded IS quotations. Sales achievements continue to derive from approved invoices, with linked credit notes deducted; no manual achievements are inserted. Forms/resources and SOP/JD/KPI registers include a downloadable plain-text sample attachment.

Financial includes FY2026 and FY2027, each with 39 product lines, 144 expense lines, monthly plans/actuals/commitments, supporting ledger entries, two staffing scenarios and a submission example. Budget actuals are fictional planning examples, not automatically reconciled to the IS invoices.

## Suggested tests

1. Sign in with your configured administrator account. The sample administrator can access the modules based on its role permissions. Then open Biomed IS or Financial from the shared application navigation.
2. View Stock Inventory. Product TEST-P003 has a held lot; TEST-OLD lots are expired. Product TEST-P040 is inactive and has no stock.
3. Filter document registers by Draft, Pending or Approved. Open the document trace to follow a purchasing or sales chain. Approved records are fixtures, not evidence that the original SQL behavior is implemented.
4. In Portal → Quotations/Pipeline, find the approved quotation containing TEST-P026 and mark it Won with a reason, then choose whether to generate an Order. The quotation containing TEST-P031 is already Won with no order, so it offers Generate IS Order.
5. In IS, review Pending stock count TEST-COUNT-001 or the pending warehouse transfer for TEST-P030.
6. Review Sales Performance for August–October 2026 and test expense → payment processing. The incentive scheme is available for a newly calculated claim.
7. View FY2027 budgets and switch to FY2026. Actuals are non-zero for the first six fiscal months; commitments are in November.
8. Switch Portal users to inspect reporting scope and sharing. Employee roles retain the baseline access restrictions; use the administrator to explore all modules.

## Keep or restart

The database is already included under data/biomed.sqlite3. Launch normally; do not run the generator on each start. Changes persist in this copy. To start fresh, extract another copy of the original test ZIP into a new folder. The generator refuses to overwrite an existing database.

## Limits

This supplies test fixtures for the current app, not a populated copy of the 63 original SQL Server tables (which this app does not execute). Existing migration/report limitations remain. Kit transaction expansion, original SQL stock calculations and exact report layouts are still incomplete. File uploads still use the existing browser attachment storage; the bundled sample documents are supplied directly by this test package.
