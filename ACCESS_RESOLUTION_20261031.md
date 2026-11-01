# Reviewed resolution of the 35 application-access conflicts

This follow-up release supersedes the access-conflict warnings in the original
workbook import. All 35 reported role/application conflicts are resolved in the
packaged database. The complete decision list is in
`setup-reports/Biomed_Access_Resolution_Decisions.csv`; the 38 exact permission
changes are in `setup-reports/Biomed_Access_Resolution_Exact_Changes.csv`.

## Decisions and reasons

### Change N to Y where functional access is clearly intended

Enable `is_view` for 21 roles. Their detailed permissions form coherent document
workflows for sales, product/application support, service inventory, purchasing,
logistics, collections, administration, director coordination or IT support.
The individual actions already selected in the workbook are retained. No extra
transaction, approval, delete or export actions are added.

QMR also receives `is_view`: its stock-count view/print, supplier/warehouse
references, approval-rule viewing and audit history support quality oversight.
Its existing eight selected Biomed IS permissions are retained; no stock-posting
or transaction-approval rights are added by this correction.

Enable `crm_view` for all 12 affected roles. All have seven explicit Calendar
permissions and Calendar is implemented using the CRM backend. QMR additionally
has Helpdesk and ticket-reference permissions for customer-complaint handling.
Enabling the gate does not grant access to other CRM modules. Existing Calendar
actions, including assign/delete/import/export, are preserved as selected.

### Change isolated Y values to N where there is no coherent IS workflow

HR Manager keeps `is_view=N`. Remove `is.master-customers.view` and
`is.dashboard.view`. These are unrelated to HR's Staff Portal responsibilities,
and no IS transaction workflow was selected for this role. Its seven Calendar
permissions remain and CRM access is enabled.

Marketing Communication Specialist keeps `is_view=N`. Remove
`is.master-customers.view`, `is.dashboard.view` and `is.quotation.progress`.
The isolated quotation-progress grant lacks quotation View permission. Customer
contact and opportunity work remains available through its existing CRM contacts
and Sales Plan permissions.

Total: 33 application gates change N to Y (21 IS + 12 CRM); five individual
permissions change Y to N. This is 38 permission changes across 25 roles,
resolving the original 35 role/application conflicts.

## What is retained

Passwords, accounts, active/inactive status, user IDs, departments, reporting
lines, responsibility descriptions, record visibility and document history are
retained. Financial permissions and unrelated role choices are retained. Shared
roles apply to all staff assigned to them, including staff outside the 44-user
workbook. Record visibility still limits access to the configured records.

## Railway deployment

1. Update the existing GitHub application source with this package. Include the
   new `company_access_resolution.py` and the modified `serve.py`, along with the
   previous workbook-import files.
2. Keep the existing Railway persistent volume and BIOMED_DATABASE_PATH. Do not
   overwrite the live database with the packaged local-testing database.
3. Redeploy. Startup creates a private recovery archive before applying this
   incremental correction in one transaction. The original workbook import runs
   first only if that version has not already been installed.
4. Users assigned to changed roles must sign in again. Check a representative
   sales, service, HR, QMR and Calendar login.

The correction runs once. It does not reset passwords or reimport profiles. It
changes only the listed permission gates/grants and saves a decision audit. Roles
deleted since the workbook import are not recreated. Where an administrator has
already enabled a gate, existing grants are retained. Where the originally
affected individual permissions have all been removed, the gate is not enabled.
Later administrator changes survive restarts and redeployments.

## Verification

Database checks reconcile every exact permission change and confirm zero remaining
application-access conflicts, valid database integrity, unchanged credentials,
visibility, reporting lines and transactions. Tests cover rollback, session
revocation, prior administrator changes, missing roles, one-time execution and
the recovery archive. The optional live Waitress listener test requires Waitress
in the test environment; it is excluded from the available local regression run.
Live Railway verification remains to be performed after deployment.
