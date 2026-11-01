# Workspace update

- Integration settings now use the internal workspace logo, system links, colours, controls and card styling. Staff Portal bridge navigation has a defined icon and wraps safely.
- Product-line actions have consistent heights, wrapping and separation from the table.
- In Staff Portal, Biomed IS and Financial, use **Quick access → Customize**. Choose up to 12 permitted functions. Choices are stored per authenticated account in SQLite, independently for each system. An empty selection is saved. Shortcuts never grant permissions.
- Product entry suggests product ID, description, catalogue, barcode and brand. Choosing a product retrieves its stock lot/location records. A single non-held, non-expired recorded lot is filled automatically; multiple lots require selection. Type a lot or press Down to see matches; choosing one fills expiry and the mapped line location. Balances and held/expired status are shown. Receiving still permits a new lot. Replacing a product clears the previous lot and expiry. Suggestions also cover available warehouse/location, supplier/customer IDs, staff and known brand/unit/country/storage/currency fields where present. Dates and amounts remain explicit entry fields.
- Biomed IS Reports has a keyable product filter. **Compare functions & inspect source lines** compares two functions by product, party ID or month, retaining separate currencies and units. Date/status/employee/product/currency/warehouse/text filters apply; comparison function choices are independent of the general transaction-type filter. Expand detailed source lines to open documents and trace sources, or export all filtered comparison lines. The screen pages details in groups of 50. Line values are quantity × unit price before document discounts and VAT. These comparisons do not assert that an order was fulfilled; use linked source documents for fulfilment tracking.
- Existing document summary reports show the whole value of documents containing a matching product. The new comparison line report shows only matching product lines.

## Upgrade while preserving your data

Stop the old server with Control+C. Extract this package into a new folder. Copy your current `data/biomed.sqlite3` into the new folder's `data` folder **before starting** if you want to retain your records and accounts. Otherwise the included fictional test database will be used. Start with `START_ON_MAC.command` and hard-refresh the browser with Command+Shift+R.

New preference storage is created automatically without deleting existing records. SQL Server 2012 schema and transfer scripts include preference data; this local package still runs SQLite and needs a SQL Server runtime adapter before deployment against SQL Server.

Validation: workflow/report calculations, autocomplete matching, account-isolated preference API, existing integration/public-content/security tests and JavaScript syntax checks. Native browser visual verification was not available in this environment.
