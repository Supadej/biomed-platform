# v82 — Annual & Monthly Budget

All revenue, Cost of Goods Sold (COGS), Other Cost of Sales and expense targets are set under Financial → Annual & Monthly Budget. Existing expense menu items load automatically. New expense lines can also be created here: choose the expense menu category, item name, cost center, owner, comments and supporting files. Enter all twelve May–April allocations or spread an annual amount evenly. Existing approval, revision, monthly activation and period-lock controls remain.

Revenue is a gain. COGS, Other Cost of Sales and all other expenses are costs. The company earnings outlook displays the working plan, approved annual plan and entered actuals separately, plus monthly working-plan earnings. Earnings before tax = revenue − COGS − Other Cost of Sales − all other expenses. This does not calculate income tax or assert net profit after tax.

Revenue/COGS actual-entry screens and expense worksheets use the same underlying records as approved budgets. Annual approval publishes new sources/items into their menus. Worksheets accept monthly actuals; budgets and commitments in worksheet views are read only. Commitments continue through financial entries and existing integrations. Favorable variance is actual minus budget for revenue and budget minus actual for costs. Draft or pending targets do not activate spending limits; monthly approval remains required. Actual totals already recorded through an integration should not be entered again as additional ledger entries.

Cost Center Management starts empty in the included starter database. Automatic cost-center generation has been removed. Existing user-created centers and historical links on an installed database are preserved. Add your own centers before creating new budget lines.

Workforce scenarios remain available for modelling; they no longer apply budget amounts directly outside the consolidated approval flow. Direct workspace attempts to change budget amounts are rejected on the server even before an annual plan is approved.

## Updating Railway

Upload the contents of this project to your repository. Keep the currently working Railway volume mount and BIOMED_DATABASE_PATH unchanged. Do not replace or delete the database on your mounted volume. The included starter database is used only when the configured database does not exist; it has the existing 44 configured staff accounts, with no business records or cost centers.

## Verification

Five Python tests cover staff/database preservation, announcement history, existing expense mapping, all expense-menu categories through annual approval, prevention of direct draft/approved budget edits, and continued actual entry. JavaScript syntax checks cover all inline and external scripts. Earnings calculations are tested for annual and monthly totals, actuals, and a loss scenario. Browser-rendered visual verification is unavailable in this environment. This package has not been deployed to Railway.
