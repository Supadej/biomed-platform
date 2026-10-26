# 26 October 2026 update

## Added
- Records / Analysis tabs for CRM Calendar, External Helpdesk, Project & Activity and Sales Plan. Analyses aggregate matching API query results (up to 5,000) and indicate when filtered results exceed the cap.
- Records / Analysis tabs for Expense claims and Performance appraisals, with grouped distributions and relevant aggregate measures.
- New Budgeting financial entry cost-center selection, Debit / Credit direction, separate financial ledger columns, Detail and non-destructive reversal audit history.
- Accounting payment marking Paid prompts for creation of a real Budgeting financial entry: current fiscal year, existing cost center, expense line and payment reference. Payment remains Processing when cancelled or financial posting fails.
- A reversed payment-linked Budgeting financial entry reopens its Staff Portal payment queue to Processing, with history.

## Important limitations / deployment notes
- Finance and portal workspace mutations use the current BiomedStorage application storage adapter. No distributed transaction exists across separate storage writes; Finance should reconcile after any network failure. Back up current database before deployment.
- Appraisal analysis follows explicit appraisal filters. Expense analysis respects report scope, but presently does not read the on-screen expense filter controls; this is a known limitation.
- For some pre-existing ledger entries created before this update, debit/credit is inferred by signed amount. Historical reversed entries remain in the audit ledger rather than being deleted.
- This package has passed JavaScript syntax checks but has not undergone live authenticated browser/backend integration testing.
