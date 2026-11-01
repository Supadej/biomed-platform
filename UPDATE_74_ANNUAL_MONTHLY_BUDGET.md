# Annual budgeting and monthly budget approval — update 74

## Before deploying
1. In Railway, retain the SAME application service, attached volume and `BIOMED_DATABASE_PATH`. The existing Docker configuration uses `/data/biomed.sqlite3`. Confirm the path against your own Railway configuration.
2. Download a full database backup and retain uploaded attachments before deploying. Do not delete or recreate the volume or use database reset/restore/demo-seeding commands.
3. Deploy the changed source files into the same repository and service. Do NOT upload the ZIP's `data/biomed.sqlite3` over the live database. That supplied database is an unchanged snapshot, not a confirmed current production backup.
4. Docker deployments now require the existing database to be present. If startup reports that it cannot find the database, reconnect the original volume/path. Do not bypass the check by creating a blank database.
5. On startup a SQLite-consistent backup is created once at `backups/before-annual-monthly-budget-v74.sqlite3` alongside the configured database. It does not replace a separately downloaded Railway backup.

## Usage
Financial → Budget Setting & Approvals → Annual budgets & monthly approvals.
- Annual plan: revenue, product CoGS and every existing expense category, including Other Cost of Sales, personnel, travel and operating expenses. Enter monthly amounts or distribute an annual amount over twelve fiscal months. Existing category totals are prefilled; underlying records and component proportions remain intact.
- Save draft, submit, then follow the existing Department → Finance → Director approval permissions. Existing user roles and visibility rules are reused unchanged.
- Monthly budget approval: select Submit month for each fiscal month. Department → Finance → Director approval activates that month's frozen allocation. There is no requirement to wait until the month ends.
- Finance planning & control → Commitments now uses the sum of approved monthly allocations as available budget; the annual plan is shown separately. Other workbook and variance reports continue to show annual planning figures.
- Individual spending requests and their approval remain in Staff Portal. This update does not add another individual expense approval or a new automatic payment block.
- Existing performance finalization is retained separately for closing actuals after the period ends.
- After an annual revision is approved, re-submit affected months for monthly approval. The previous approved monthly allocation remains effective until its replacement completes approval. All revisions and decision histories remain available.
- Existing annual approval is NOT treated as retrospective approval of all months. Months without monthly approval have zero approved allocation, so availability may be negative where actuals/commitments already exist. No historical transaction is deleted or changed.

## Preservation
No database schema replacement, ID regeneration, account reset or master-data re-import is needed. Monthly allocations are added inside the existing versioned budget-governance record. Brands, HTML, website files, users, password hashes, roles, visibility, reporting lines, CRM stages, products, customers, warehouses and historical transactions remain in the existing database.
Automatic legacy demo randomization, sample-user cleanup and company roster/access re-imports are disabled by default. `BIOMED_ENABLE_LEGACY_DATA_IMPORTS=1` explicitly enables these old routines; leave it unset for this upgrade.

## Validation
- Existing budget-governance regression tests: passed.
- Monthly activation, revisions, permissions, invalid months, independent review, component proportions and unrelated workspace preservation: passed.
- Existing Finance workspace tests: passed.
- Python compilation and JavaScript syntax checks: passed.
- Startup on a temporary copy of the supplied database: all 83 pre-existing tables unchanged; protective backup created. The database included in this ZIP is byte-identical to the uploaded snapshot.
- Railway production database and browser rendering have not been verified here. Validate a restored staging copy and check your live backup/volume before production rollout.
