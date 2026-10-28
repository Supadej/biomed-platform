# Deployment: preserve existing staff accounts

**Do not overwrite your existing production SQLite file with the `data/biomed.sqlite3` packaged in this archive.** That packaged file is a development/seed database, not the Railway staff-account database. The application authenticates from `BIOMED_DATABASE_PATH`, defaulting to the package `data/biomed.sqlite3` when unset.

1. Back up the existing Railway database or volume BEFORE deploying.
2. Check the Railway environment variable `BIOMED_DATABASE_PATH` and ensure it points to the SAME persistent-volume file used before this update. Keep the volume mount and path unchanged.
3. Deploy code/static assets while preserving the existing production database. Do not copy the packaged `data/biomed.sqlite3` over the production database.
4. Restart the service and sign in with the prior account.
5. If you already replaced the database, restore the previous volume snapshot / backup. Passwords cannot be recovered from screenshots or copied to another database by editing the login form. Do not create insecure backdoor accounts.
6. If the original persistent database is intact but login fails, inspect app logs and test the auth response; locked-out accounts unlock after the security lockout period. Administrator-assisted password reset should be done through an authenticated account-administration flow, not public endpoints.

# Financial movements

The budgeting ledger is NOT a general ledger: the previous Debit/Credit field merely signed a budget-line change. This release renames the UI options to Increase actual/commitment and Decrease/correction, retaining the stored Debit/Credit values for compatibility.

Record sales invoices/revenue as revenue Actual increases, genuine incurred costs as expense/COGS Actual increases, and purchase commitments as Commitments (not yet expense). A payment usually settles an existing payable and should not double count an already-booked expense. Corrections reverse the original or reduce the budget-line actual with linked reference. A double-entry GL, if introduced later, should separately post balanced account debits/credits (cash, AP, expense, revenue, etc.).
