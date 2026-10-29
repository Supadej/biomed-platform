# Update 27 — reports, usable stock and shared brands

## Service jobs

Each register row has **Details** and **Email PDF**. Expand Details for **View / print PDF**. The email dialog wraps its actions with spacing and puts Close on a separate row. PDF reports print the assigned engineer's name (including historical engineer names) in Service Eng. Signature and the service end date, or service date, in its Date cell. Printed identification is not a handwritten or digital signature.

## Ready-to-use testing database

The database is already populated; do not run the seed scripts just to start testing.

- All 36 products have posted test stock. The previous lot-only fixtures did not feed the live inventory calculation; explicit opening movements now do.
- Eight TEST spare-part products are linked to the Service spare-part catalogue and to existing instrument brand/model combinations.
- Six TEST service employees each received 25 of each spare part through separately approved requests: 48 custody balances. Six completed TEST repair jobs demonstrate two-part consumption, leaving 1,188 units in engineer custody. Central stock is not deducted again when a job consumes engineer stock.
- Stock Ledger includes the opening quantities and approved transfers. Service Inventory Track Record includes approved issues and service-job use.
- Three TEST Product Kits and 19 brand-linked research budget lines per test fiscal year are defined. Existing sample documents, customers, suppliers, HR, sales, calendar and budget data are retained.

For a quick service test, use an account in TEST_ACCOUNT_ACCESS.json whose role is Service Engineer, or use the Service Manager account to inspect all balances. In Service Inventory, each engineer sees their own stock; approvers see all engineers. In Service Jobs choose the same engineer, an instrument matching one of the **TEST** spare-part catalogue entries, and add that part. Saving uses the approved custody balance. Increasing usage deducts only the change; decreasing usage reverses the excess. Request and approval must use different employees. Historical imported parts without a verified product binding are preserved; use the explicitly linked TEST entries for consumption tests.

All test quantities, documents, costs, catalogue codes and position-placeholder identities are fictional. Existing imported service history is retained. Test login credentials are included for local installation and are blocked from public HTTP download.

## Navigation

- Warehouse & Inventory: Stock Ledger → Service Inventory.
- Master Data: Products → Product Kits.
- Management: Brands.

## Shared operational brands

Biomed IS → Management → Brands is the operational brand master. Users with Products view/edit permission can manage it. It supports adding, renaming, archiving and restoring brands with duplicate-name and stale-version checks. Renames propagate within one transaction to product brand fields, service instruments/reference lists, current CRM brand fields, Staff Portal sales/incentive lines and Financial brand fields. Existing case variants were aligned. Reload other open views after changes.

Biomed IS Products uses a Brand selector. Financial Manage Products and the inline product tools use the same list. Calendar brand choices and External Helpdesk/Instrument Service brand choices come from this master. Staff Portal sales-line administration and Service reference settings direct brand maintenance to Biomed IS instead of creating a separate list.

Removal archives a brand so it cannot be chosen for a new assignment; existing historical references remain readable. The **Website & Admin → Brand Catalogue** remains independent and is not renamed or archived by operational brand changes. Budget product names remain free descriptions; their separate Brand field uses the shared list.

## Validation

Report generation, shared-brand rename/archive/permission/version validation, engineer inventory and calendar tests passed. Browser checks covered the email dialog at 320, 390, 768, 1024 and 1440 pixels, visible job actions, stock and custody data, brand creation, and shared brand selectors in IS and Financial. This package has not been deployed to a live server.
