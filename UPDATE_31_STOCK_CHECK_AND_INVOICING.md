# Update 31 — Service Inventory stock checks and invoicing

## Stock Check

A new Stock Check tab records physical counts by engineer, part, lot and expiry. Tick the lots counted, enter physical quantities, and justify each discrepancy. Matching counts are stored as Completed without stock adjustment. Discrepancies become Pending approval.

The requester and stock holder cannot approve their own discrepancy. An inventory approver can approve or reject, with a required rejection reason. Approval rechecks book stock: if parts moved after counting, the count must be cancelled and repeated. Approved differences post once to the engineer custody ledger, with count reference, timestamps, reasons and decision history. They do not change central warehouse stock. Pending checks may be cancelled by their requester or an approver.

Stock checks use Service Inventory request permission; adjustments use Service Inventory approve permission. Existing role overrides are retained. Accounting gains read access to Service Inventory and Service Jobs for billing, without count submission or stock approval permissions.

## Track Record

Service-job activity now shows Job No., customer, billing status and invoice reference. Job details expands the serial/brand/model, location, date, type/status, responsible engineer, report problem, diagnosis, action and result in place. Open the full job for additional details. CSV exports include job/customer/billing status/invoice.

The Open/Invoiced filter applies to billable service-job activity. Stock transfers, counts and adjustments remain ledger activity with no billing status.

## Add job parts to invoice

Users with Service Inventory access, Service Job view, and Invoice view/create or edit permissions can add a job's current allocated parts to a new Draft invoice or an existing Draft invoice for the same customer and currency. Existing customer bindings must match. Where the job has no linked customer, select an existing Biomed IS customer; the searchable list supports large registers.

The action invoices all current parts allocated to that job, grouped by IS product, once per job. It uses product selling prices, not the internal usage cost. Review prices, VAT and invoice details before submitting the invoice through its normal approval workflow. Invoiced means included in an invoice; the Draft/approved state and invoice number are shown separately. No additional warehouse or engineer-stock deduction occurs when adding an invoice.

Duplicate additions are rejected transactionally. While invoiced, job parts quantities or custody ownership cannot change. Users with Invoice edit permission can remove the job's lines from a Draft invoice, returning the job to Open; then correct usage and add it again. A cancelled invoice also returns the job's billing status to Open. Approved invoices must use the normal cancellation/finance process. Linked service lines cannot be silently removed, duplicated or have quantities changed through an ordinary workspace save; edit selling prices through the normal invoice screen.

## Validation

Tests cover mandatory reasons, separate approval, stale counts, single posting, matching counts, permissions, invoice creation, duplicate prevention, billing read access without approval powers, usage locking, and unlinking Draft invoices. Browser tests covered count submission/approval, adding parts to a Draft invoice, Invoiced status, and expanded job details. The packaged database retains its existing test stock; no QA count adjustments or invoices were inserted into it. This update has not been deployed to a live server.
