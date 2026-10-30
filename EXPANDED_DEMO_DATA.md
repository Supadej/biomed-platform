# Expanded fictional testing data

Deploy this source update first. Then open Railway SSH for the application and
run the same import command again, even if you imported the earlier small set:

```sh
python3 seed_ai_demo.py --database /data/biomed.sqlite3 --email testadmin@example.invalid
```

Use your existing account email if different. A full SQLite backup is created
first. The importer adds missing DEMO fixtures and preserves existing data,
accounts, passwords, roles, API keys and modified demo records. Repeat imports
do not duplicate fixtures. An import failure rolls back the additions.

Refresh each application after importing. The bundled database already includes
the expanded set for a fresh installation; Railway's existing volume needs the
command above. No reset, database replacement or new API key is required.

## Test coverage

- Staff Portal: travel, budget, leave, vehicle, room and general requests in
  Pending / Approved / Rejected / Cancelled states; tasks and support tickets;
  objectives; local/upcountry/overseas expenses; accounting payments; incentives;
  targets and actuals; training and document-register examples; employee lifecycle,
  visits, tenders, pipeline, appraisals and leave entitlements.
- Six fictional employee directory profiles report to the selected test owner.
  They have no login accounts or passwords. Existing reporting lines are retained.
- Biomed IS: over 100 documents across all 20 registered transaction types,
  including Draft / Pending / Rejected / Cancelled examples and approved
  quotations, linked sales orders and invoices. Nine products/customers/suppliers,
  four warehouses and 25 lots include held, expired, near-expiry and zero balances.
- CRM: 24 Calendar events, 24 Sales Plan records across the six pipeline stages,
  24 project activities and 24 External Helpdesk tickets, plus a project/stages.
  These are owned by the selected account's CRM identity.
- Financial: prior/current/next fiscal years, eight additional product lines,
  all 12 expense categories, monthly budgets/actuals/commitments, balanced ledger
  examples, workforce assumptions and five approval stages per fiscal year.

Most Portal/IS/CRM dates fall within the default recent-date window. Change the
fiscal-year selector for historical or future budget scenarios. Some examples
intentionally have past due dates, expired stock, losses or rejected outcomes.

All fixtures are fictional. Approved demo invoices, expenses, stock balances and
budget schedules affect displayed totals. Do not treat the resulting reports as
real financial results. Stock transaction examples are unposted Draft/Pending/
Rejected/Cancelled; demo lots are explicit fictional opening balances.
The importer sends no notifications, books no external services, changes no
real employee details and does not run integration bridges. Approved demo
invoices can be included if you explicitly run the IS-to-Portal bridge.

## AI examples

Keep Share permitted record summaries with OpenAI enabled for permitted functions.
Start a new conversation after the import and ask:

- Compare the permitted task and request statuses.
- How many demo quotations and invoices are visible?
- Summarize Sales Plan, External Helpdesk and project activity counts.
- Compare permitted actual revenue, COGS and expense commitments by fiscal year.
- Show my upcoming demo calendar events.

Current AI summaries expose bounded records/counts and permitted totals, not all
raw fields. Granting every function does not enable general writes or turn own
request summaries into an authoritative approval inbox.

## Validation

153 Python tests passed before final fixture-field corrections; affected demo
repeat-import, financial-balance and link-integrity tests passed afterward.
Live Railway rendering and live OpenAI responses have not been verified here.
