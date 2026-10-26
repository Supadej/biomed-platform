# Catalogue permissions and warehouse locations

- System Admin is explicitly allowed into the Product Catalogue UI; the catalogue backend also permits users with `approve_all`, `content`, or portal content permissions, or an explicit System Admin role.
- New Biomed IS > Master Data > Warehouse Locations page permits multiple location IDs per warehouse. Location IDs must be unique **within** a warehouse, so the same ID may exist in another warehouse.
- Existing inventory remains as warehouse-level inventory. Staff may assign part of an existing product/lot balance to a location. The allocation does not create stock or affect warehouse totals.
- Important limitation: pre-existing document posting and warehouse transfers remain warehouse-level, not location-aware. Location allocations therefore require reconciliation when movement occurs. Do not treat allocated quantities as live guaranteed bin balances without completing location-aware posting integration.
- Permissions depend on the currently authenticated account; never reset or replace an existing production database while deploying this package.
