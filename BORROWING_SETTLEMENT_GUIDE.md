# Borrowing, customer purchases and physical returns

This update uses the existing SQLite workspace and document approval permissions. No database reset is required. Borrowing references and handling modes are stored on each document line and remain with derived documents.

## Issue borrowed products
1. Create and approve Borrowing, including customer, products, quantities and expected return date.
2. Create Delivery Out → Check Out using the document Details actions.
3. Approve Check Out to deduct stock once and generate the Shipment. Only issued quantities become outstanding borrowing.

## Customer buys borrowed products
1. Open Borrowing → Details → Create Customer Order. It selects outstanding issued quantities with their borrowing references.
2. Edit the draft quantity for a partial settlement. Add ordinary product lines for additional requests. Alternatively, create a Customer Order and use the **Settle borrowed items** panel to select outstanding items, quantities and prices from several borrowing documents for the same customer.
3. Save, submit and approve Customer Order. Approval reduces outstanding borrowing. Draft, Pending, Rejected and Cancelled orders do not reduce it.
4. Create Sales Order → Invoice. Both settled borrowing and new products remain on the invoice.
5. Create Delivery Out from the approved Invoice. Only new products are copied to the warehouse route. Settlement-only invoices cannot generate another dispatch. Purchasing queue entries likewise contain only new products.

## Customer physically returns products
1. Open Borrowing → Details → Create Product Return, or create Product Return and select outstanding borrowed items using the return panel.
2. Select quantities and verify the actual lot, expiry, condition and receiving location. Multiple partial returns are supported. The selector carries the issued lot when identifiable.
3. Approve Product Return → create and approve Delivery In → create and approve Check In.
4. Only approved Check In adds stock and reduces outstanding borrowing. Product Return and Delivery In approval do not receive stock.
5. Use existing quarantine controls for damaged or suspect goods. This update does not automatically classify returned items as sellable or damaged.

## Follow up
Borrowing register and Borrowing Details show the all-date ledger: issued, purchased, returned, outstanding, due date, overdue/partial/closed state and linked posting references. CSV export is available. Date filters continue to apply to the document register; they do not hide older outstanding balances.

Server validation runs inside the SQLite write transaction after revision checks and permission-scope merging. Overlapping settlements/returns cannot exceed issued quantities. Settlement lines cannot enter warehouse or purchasing workflows. Customer/product consistency, original borrowing approval and return-lot quantities are checked.

Posted borrowing-related documents are protected against deletion, status reversal and line rewriting, including backup restores. Draft/rejected records can be edited or cancelled. Automated posted settlement reversal is not included; do not use a credit note alone to reopen a quantity balance. Credit notes retain their financial workflow.

## Existing records and deployment
Replace application code using your existing deployment process, retain the live data directory/database, and restart the Python server. Keep `borrowing.py` with `serve.py`. No credential or data reset is needed. This ZIP is an updated source package; it has not been deployed to the live Railway service.

Old warehouse records are inferred through their source chain only when product/lot identifies one borrowing line unambiguously. Legacy records with ambiguous links, or old Product Return documents which already posted stock before Check In, need reconciliation before processing further receipts. The update does not silently rewrite historical stock movements.

Staff Portal and Budgeting continue to consume invoices through the existing bridges. Borrowing and settlement Customer Orders do not themselves create revenue. A dedicated borrowing panel in Staff Portal/customer master is outside this update; the authoritative ledger is in Biomed IS.

## Validation
- 9 Python borrowing tests: partial and mixed purchases/returns, draft exclusion, over-settlement, competing orders, customer/product/lot mismatches, duplicate dispatch prevention, posted protection and invoice non-duplication.
- JavaScript borrowing workflow test: legacy issue inference, outstanding picker/report, settlement derivation, mixed invoice, warehouse exclusion, partial physical return and original document preservation.
- Existing JavaScript workflow suite and 17 Python workflow policy tests.

Tests exercise logic and generated screen markup. A full visual browser audit and live deployment test have not been performed.


## Borrowing report filters and summaries
- Outstanding Borrowing has its own search, customer, product, balance status and Borrow-date From/To filters. Dates default to the standard previous-month/next-month range. All dates clears the date bounds; Reset restores the standard range.
- Favorites are private to the signed-in account and scoped separately from the main Borrowing register. Saving a search includes the selected summary tab. Loading restores the whole report state in one render.
- By borrowing document: ID, customer, borrow/due dates, days since borrow, document quantity and line amount, issued quantity/value, purchased/returned/outstanding quantities and expandable product/lot/settlement details.
- By customer and By product: summed quantities and values, grouped separately for each unit and currency. Document counts are distinct borrowing documents in that group.
- Report quantities and values reflect selected product filters. Document amounts use original line quantities × borrowing unit price before discounts and VAT; issued amounts use physically issued quantity × borrowing price. Neither is an invoice total.
- Aging counts calendar days since the Borrowing document date. Filtering document dates does not truncate subsequent settlement/return activity used for current balances.
- CSV export follows the current report filters; export inside one borrowing document exports that document's product lines.
- Export controls have a separate action area, wrapping labels and responsive full-width sizing on phones to avoid touching/overlapping the report table.
- Added logic checks for customer/date filtering, all-date reset, favorite restoration, document expansion, aging fields and quantity/value aggregation. Browser visual verification was unavailable in this environment.
