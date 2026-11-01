# v85 — Other Cost of Sales by Brand and Expense Item

## Form alignment

The Annual & Monthly Budget form places instructions on a full-width row. Labels and controls align to the top of their grid cells; hidden controls collapse. The grid adapts to desktop, tablet and phone widths. Manage Expense Items uses the same field spacing and full-width action/help rows.

## Separate planning types

Annual & Monthly Budget now has Revenue, Cost of Goods Sold, Other Cost of Sales, and Expenses as distinct plan selections.

- Other Cost of Sales uses Shared brand and Expense Item. Its items are filtered by the selected brand and the Other Cost of Sales category.
- Expenses uses Expense menu/category and Expense Item, without a brand.
- Cost center and budget owner remain available. Existing items appear automatically in the planning grid; choosing an existing item focuses its budget field.
- Existing Revenue/COGS source-reference behavior remains available.

## Manage expense items: Add / Edit

Select Other Cost of Sales when adding an item to require a Shared brand. The item register shows an editable brand selector for Other Cost of Sales rows. Other expense rows have no brand selector. Item names and cost centers remain editable.

Old Other Cost of Sales items without brands remain visible and retain their amounts. Assign their brand in Manage Expense Items before submitting a new annual plan. The update does not invent brand mappings. Old approved snapshots remain available as recorded; new revisions use the mapped brand/item identities.

The backend distinguishes Other Cost of Sales by brand, item and cost center. The same item name under different brands does not share a budget line. Approval publishes values back to the linked item ID, preserving recorded actuals. Other Cost of Sales remains a cost deducted from company earnings. Operating expense budgets remain item-based. No new database reset was introduced.

## Updating

Keep the current Railway volume and database path. The previously requested one-time v83 Finance reset remains included: if it has not run on the database, it will back up the database and clear Finance once on startup. If it already ran, newly entered Finance data remains. This release adds no second reset.

## Checks

Eight Python tests pass, including brand requirements, ordinary-expense brand rejection, separation of matching item names under two brands, publication to the original item, legacy ID mapping, annual/monthly approvals and data preservation. Staff Portal Analysis interaction tests also pass. All inline and external JavaScript syntax checks pass. Browser-rendered alignment verification is unavailable in this environment. This project has not been deployed by the developer.
