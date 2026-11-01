# Expense-menu budgets and restored Cost Center Management — v81

## Changes
- Removed the Financial Reference Lists screen, source-reference creation controls and its browser module. The old API returns a clear removed-feature response.
- Restored the original Financial → Cost Center Management page with code, name, Active status and linked-line counts. Cost centers saved through the former reference screen are copied once into the fiscal-year cost-center lists without deleting those records or overwriting existing centers.
- Cost-center dropdowns now read from Cost Center Management. The management page retains its editable code/name fields.
- Budget Setting loads expense items directly from Other Cost of Sales, operating expense, personnel and travel/training menus. Each item carries its existing record ID. Approving an allocation writes to that record's budget months; it does not create a second independent expense source.
- Use Manage Expense Items or the appropriate expense menu to add an expense item. Its category, item name, cost center and monthly amounts then appear in Budget Setting. An empty installation still has all standard expense menu categories available, without sample item records.
- New revenue/COGS lines remain available in Budget Setting. The independent Expense source creation option has been removed; expense items are created in their existing menus.
- Six category views and annual/monthly approval workflows remain available. Owner, comments, supporting files and revision history remain.
- Removed the duplicated navigation-link row below the heading. One row remains for Budget Setting, Budget Approval, Actual Expense Recording and Budget vs Actual.
- Added explicit gaps, wrapping and natural button height to financial action rows, preventing fixed-height labels from colliding with adjacent controls.
- Zero-budget new items may be added after annual approval, while changes to approved amounts still require a budget revision.

## Existing records
The old reference table is retained internally as archived data; it is not shown as an active setup function. No source/reference records, users, passwords, role settings, announcements or transactions are deleted.
Legacy category-level plans are expanded into linked item lines when preparing a new draft, preserving monthly totals and distributing them in proportion to existing item budgets (evenly when all weights are zero). Historical approved snapshots remain unchanged. Review the proposed item allocations before submitting a new revision, especially where older plans had category-only totals.

## Deploy
Keep the SAME Railway volume and BIOMED_DATABASE_PATH. Replace matching project code in GitHub and deploy the new commit. Do not replace the mounted database with the included starter snapshot or change to a new database filename. The bundled 44-user starter database is unchanged.
The health endpoint reports expense-menu-budgets-v81. Announcement editing/history and previous finance/staff changes are included.

## Validation
Tests pass for distinct expense-item budgets, publishing to the original item ID, retaining actuals, preserving aggregate totals when mapping older plans, one-time cost-center carryover, announcement history and staff preservation. All inline/external JavaScript syntax checks pass. Tests run on temporary database copies.
Full rendered browser/device visual verification and actual Railway deployment remain unverified here. Please review historical category-to-item allocations before approval; there is no automatic rewriting of historical approval snapshots.
