# Document approval and operational progress

Approval codes remain stable for existing integrations. The UI displays Pending approval and Returned for correction. Progress is separate and server-derived from the complete linked document chain, independent of the current date filter. Quotations and shipments have permission-controlled progress actions; quotation outcomes use the existing follow-up outcome. Shipment origin is Automatic.

Receiving, fulfillment, requisition/order and invoice payment progress use approved linked quantities or amounts. Borrowing progress uses the existing borrowing ledger. Payment progress accounts for receipts and credits in the invoice currency; separate debit notes still require financial reconciliation.

Void / Reverse requires a document-specific permission, a reason and unchanged history revision. Active descendants, borrowing links, service-inventory billing links and negative stock after reversal block the action. Original stock movements are retained with offsetting reversal entries. JSON and normalized SQL document projections are updated together. Previously imported Portal/Financial data requires the existing reconciliation actions to be refreshed after reversal.

New Product Return approvals no longer post stock immediately. Physical returns are received once through Delivery In → Check In. Returns that already posted stock under the legacy behavior are blocked from a second receiving posting and require ledger review.

Stock Counts and Warehouse Transfers menus point to the canonical physical-count and paired warehouse-movement screens. Historical document registers remain available through Reports/Traceability. Matching existing inventory permissions migrate once. New reverse permissions default to System Admin and may be explicitly assigned. Existing quotation/shipment edit grants seed the corresponding new progress permissions.

See DOCUMENT_TRANSACTION_GUIDE.md or document-flow-guide.html for every document's purpose, chain and transaction effect. The guide is linked in document details.

The new status panel uses wrapping flex rows, separate labels/actions, 44 px controls and a mobile stacking rule. Fresh rendered browser/device verification remains blocked by the previously reported automatic approval usage-limit rejection; no new visual QA is claimed.

No automatic deployment. Existing bundled database bytes are preserved. New permissions migrate on startup.

Validation: full Python regression suite 325 passed; focused workflow tests and DOM action/permission checks passed after final refinements. All Biomed IS inline scripts and the new script passed syntax checks.
