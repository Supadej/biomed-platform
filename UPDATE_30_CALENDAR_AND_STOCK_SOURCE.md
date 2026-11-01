# Update 30 — automatic calendar dates and explicit service stock source

Calendar date is automatic and read-only. It follows Scheduled Date, then the service Date, then today's Bangkok date if neither is set. Changing either date updates the calendar date immediately. The server enforces the same rule and updates the linked event without creating a second event.

The consolidated Service Inventory total can include several engineers' custody stock. It does not mean every engineer holds that total. Previously, Service Jobs implicitly checked the assigned service engineer's balance and the shortage message did not identify the owner or available quantity.

Service Job now has **Parts supplied by engineer**. Leave it as **Use assigned service engineer**, or an authorized inventory approver may select another stock holder. A normal engineer remains restricted to their authorized custody. The form shows currently available usable quantities for the selected holder. Existing job allocations are credited back when editing, so unchanged saves do not deduct again. Expired lots are excluded from new issues.

On a shortage, the server names the checked stock holder, available usable quantity and required quantity. Stock cannot be taken silently from another engineer simply because it appears in an aggregate total. The selected stock holder is saved with the job and the deduction remains traceable in Service Inventory Track Record. The service engineer responsible for the work is kept separately.

Validation includes automatic calendar dates, an assigned engineer with zero stock, a selected stock holder with five units successfully supplying two, unchanged-save idempotence, and cross-engineer permission checks. Browser checks cover the calendar auto-update and the explicit source deduction. Existing stock data is retained. No live deployment has been performed.
