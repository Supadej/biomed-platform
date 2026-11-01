# Biomed IS document transactions and workflow

Approval and operational progress are separate. Stored Pending/Rejected codes remain compatible with existing integrations; the interface displays Pending approval / Returned for correction.

| Document | Purpose | Transaction flow | Stock / financial effect |
|---|---|---|---|
| Quotation | Offer prices and commercial terms. | Create → approve → record Sent / Accepted / Lost / Expired → create Customer Order or Sales Order. | No stock or payment posting. |
| Customer Order | Record the customer’s purchase request. | Approved quotation → Customer Order → Sales Order. Purchasing needs can create Waiting to be Purchased. | Fulfillment follows linked Check Out quantities. Borrowing settlement lines clear borrowing balances without a second dispatch. |
| Sales Order | Authorize the sale for invoicing. | Approved Customer Order or Quotation → Sales Order → Invoice. | No stock movement by itself; fulfillment follows linked Check Out. |
| Waiting to be Purchased | Queue items that purchasing needs to source. | Manual or approved Customer Order → approval → combine requests by brand → Purchase Requisition. | Progress uses approved requisition quantities; combined allocations are attributed to each original request. |
| Purchase Requisition | Authorize a purchasing requirement. | Approved purchasing queue → PR → Purchase Order. | Progress follows approved linked Purchase Orders. |
| Purchase Order | Place the purchasing order with a supplier. | PR → PO → Supplier Confirmation. | Receiving progress follows linked approved Check In, not simply creation of Delivery In. Financial commitments require reconciliation. |
| Supplier Confirmation | Record supplier acknowledgement and confirmed terms. | PO → Supplier Confirmation → Delivery In. | Confirmation recorded; no stock movement. |
| Delivery In | Prepare/record incoming goods and receiving details. | Supplier Confirmation or Product Return → Delivery In → Check In. | No stock increase until Check In is approved. |
| Check In | Post received quantities to inventory. | Delivery In → Check In → approval. | Increases stock for the selected product, warehouse and lot; also clears eligible borrowing returns. |
| Withdrawal | Authorize an internal or non-sale issue. | Withdrawal → Delivery Out → Check Out. | Stock decreases at approved Check Out, not at Withdrawal approval. |
| Borrowing | Authorize goods issued temporarily to a customer. | Borrowing → Delivery Out → Check Out; later settle through Customer Order or return physically. | Issued − approved purchased settlement − checked-in returns = outstanding. Shows Not issued / Open / Partial / Overdue / Closed. |
| Product Return | Record goods being returned. | Borrowing → Product Return → Delivery In → Check In; credit-note linkage is available when applicable. | Borrowing return clearance occurs at Check In. New Product Returns authorize the return without posting stock. Legacy returns that already posted stock are blocked from being received a second time until their ledger is reviewed. |
| Invoice | Record the amount billed. | Sales Order → Invoice → Delivery Out; Invoice can also produce Credit Note, Debit Note or Payment Receipt. | Approval is separate from payment. Payment progress uses approved linked receipts and credit notes in the same currency. Overdue is a separate flag. |
| Delivery Out | Prepare goods for dispatch. | Invoice, Withdrawal or Borrowing → Delivery Out → Check Out. | No stock decrease until approved Check Out. |
| Check Out | Post dispatched quantities out of inventory. | Delivery Out → Check Out → approval → automatic Shipment. | Decreases stock; checks available quantities. Borrowing issues become outstanding here. |
| Shipment | Track the physical dispatch after Check Out. | Automatically generated from approved Check Out → Ready to ship → Shipped → Delivered. | No additional stock posting. Origin is Automatic; progress cannot be moved backwards. |
| Credit Note | Reduce an approved original invoice. | Invoice → Credit Note → approval. | Requires an approved invoice; approved credits cannot exceed its total. Does not automatically receive physical goods. |
| Debit Note | Record an additional billing adjustment. | Invoice → Debit Note → approval. | Separate approved financial document. Invoice payment calculation currently does not consolidate debit notes into its balance; reconcile these separately. |
| Payment Receipt | Record money received against an invoice. | Invoice → Payment Receipt → approval. | Approved linked receipts determine Unpaid / Partially paid / Paid / Settled by credit. Creating a draft receipt does not mark an invoice paid. |
| Stock Adjustment | Correct a stock discrepancy through an authorized transaction. | Create correction → submit → approve → inspect resulting ledger. | Posts its configured inventory movement. Preserve the reason and verify quantity/sign and lot; approval status does not describe increase/decrease direction. |
| Stock Count | Record a physical count and compare with the system quantity. | Stock Counts menu → enter count → Pending approval → approve or return. | Approval posts the difference. If stock changed since counting, recount. The historical document register remains in reports/traceability. |
| Warehouse Transfer | Move inventory between warehouses. | Warehouse Transfers menu → request movement → Pending approval → approve or return. | Canonical warehouse movement posts an outgoing and incoming movement. Historical transfer documents remain readable in reports/traceability. |

## Status actions
Save a draft → Submit for approval → Approve or Return for correction. Returned records can be edited and resubmitted. Cancel applies to eligible unposted drafts/returned records. Approved postings use a separate Void / Reverse action with reason and permission. It is blocked by active descendants, linked borrowing/service billing, or a negative resulting stock balance. Original postings remain in history; reversal entries offset them.

Shipment creation is automatic and does not require a second approval. Quotation progress updates the existing quotation follow-up outcome, avoiding a second independent outcome. Quantitative progress is computed from the complete server-side document chain, including records outside a user's current date filter. The projected result is returned only for documents that user can view.

Legacy Waiting, Confirmed, Received, Completed, Generated, Shipped and Paid values remain readable. They are not offered as a generic business-status toggle. Legacy labels do not substitute for missing receipt, dispatch or payment evidence.

## Roles and responsibilities
Existing create, edit, submit, approve, return/reject and cancel permissions remain. New quotation/shipment progress permissions are seeded from the corresponding existing edit grants once. New document-specific reverse permissions default to System Admin; administrators can grant them explicitly. Reverse does not grant approval permission. Reporting and financial integrations continue to use stable approval codes.

## Reconciliation after reversal
Reversing a document updates the Biomed IS document and stock ledger together. Previously imported Staff Portal/Financial projections require their existing reconciliation actions to be refreshed; they are not silently rewritten by the reversal button. Reconcile before relying on cross-system totals.

## Consolidated inventory menus
Stock Counts is the canonical physical counting screen; Warehouse Transfers is the canonical warehouse movement screen. Historical Stock Count/Stock Transfer document records are retained in Reports and Document Traceability. Existing count/move approval processes stay intact; their corrections require the corresponding controlled inventory workflow rather than editing posted history.

## Examples
- Sale: Quotation → Customer Order → Sales Order → Invoice → Delivery Out → Check Out → automatic Shipment → Payment Receipt.
- Purchase: Waiting to be Purchased → Purchase Requisition → Purchase Order → Supplier Confirmation → Delivery In → Check In.
- Borrowed goods returned: Borrowing → Delivery Out → Check Out; then Product Return → Delivery In → Check In.
- Borrowed goods purchased: Borrowing issue → Customer Order with settlement lines → Sales Order/Invoice as appropriate. Settlement lines must not cause a second dispatch; new items on the same order retain their normal dispatch flow.
