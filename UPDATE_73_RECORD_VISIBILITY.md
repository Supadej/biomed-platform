# Record visibility and Railway update

## Configure access

Sign in as System Admin. Open Staff Portal → Roles & permissions → select a role → Record visibility. Search for a function, select its limit, and click Save record visibility. The setting applies to the next server request and remains saved after reload. A separate Configure record visibility permission (`portal.roles.visibility`) controls who may change it, together with role editing access.

Action permissions still decide what a user may do. Visibility decides which records those actions may reach. Giving All records does not grant a missing View, Edit, Approve, Export or Print permission. CRM View all grants do not override the new visibility setting.

| Limit | Records available |
| --- | --- |
| Own records | Records for which the user is responsible. For IS documents, the selected sales representative takes precedence over the creator/owner. |
| Own + assigned | Own records plus records explicitly assigned to the user. |
| Reporting team | Own/assigned records plus those of direct and indirect reports from Reports to. |
| Department | Own/assigned records plus those belonging to the user's department. A missing department does not match other blank departments. |
| All records | All records in the permitted function, including older unassigned records. |

Generated IS records with no explicit responsibility can inherit it from their linked source. Ambiguous or unassigned historical transactions are hidden from restricted roles. System Admin can review them and decide the correct responsibility or access setting. Do not recreate an existing transaction because it is hidden.

## Starting defaults

| Role | Transaction visibility |
| --- | --- |
| Sales Representative and other individual contributors | Own records |
| Sales Manager / Sales Supervisor | Reporting team, with equivalent limits |
| Business Director | Department |
| Managing Director / Operations Director / System Admin | All records |
| Central accounting, inventory, purchasing, procurement and logistics roles | All relevant IS transactions, subject to existing action permissions |
| Service engineer / application specialist | Own + assigned jobs; existing service custody and recipient rules also apply |

Customer, supplier, product, warehouse and service reference lists remain shared by default and have separate settings. Stock balances remain shared operational quantities for roles with stock access; private source document details are removed. Personal expense/HR records retain their own limits, even for users with broader operational access.

## Before using team access

Review User directory → Reports to and Department. The existing hierarchy is retained. Missing or incorrect reporting lines will produce an incomplete team view. Previously configured role grants and responsibilities are preserved. Supervisors and managers use the same functional default scope, without granting new actions.

## Covered paths

IS transaction lists and details, workflow actions, PDF/HTML reports, email report downloads, scoped workspace exports, quotation snapshots, Portal registers and sales projections, Calendar, Sales Plan, Helpdesk, Project & Activity, meeting minutes, Service and Application jobs, attachments, analysis and Copilot summaries use the server-side limits. Existing private-recipient and custody rules remain an additional restriction.

Saves preserve omitted hidden rows. Attempts to alter hidden records, transfer a record outside the user's visibility, or link to an inaccessible source are rejected. Role renaming carries saved scopes; deleting a role removes its scopes while reassigned users use the replacement role. Cloning with visibility administration permission copies the selected settings.

Full database backup/restore is a System Admin operation. Company-wide reconciliations and source binding require sufficiently broad source/destination access; ask System Admin to run a full reconciliation rather than granting sales staff company-wide access for that purpose.

## Deploy to Railway

1. Take a current full database backup through Database administration as System Admin.
2. Replace the project source in the existing GitHub repository with this version and commit/push using your existing deployment method.
3. Keep the current Railway persistent volume and BIOMED_DATABASE_PATH. Do not replace the live SQLite database with the packaged example database.
4. Redeploy. The server adds initial visibility settings once. Later edits are preserved across restarts.
5. Refresh open pages or sign out/in. Check Roles & permissions and review Reports to.
6. Test with two actual sales accounts: each should see only its own quotation. Test a supervisor with correctly assigned reports, then an unrelated department. Check direct report links and exports as well as the table.

The archive contains source and setup data; it has not been deployed to your Railway service.

## CSV files

- Biomed_All_889_Permissions_Checklist.csv lists each permission once, with blank Assigned roles and Feedback columns. It adds one permission to the previous 888: Configure record visibility.
- Biomed_Role_Record_Visibility.csv lists the current role/function limits separately. Fill Requested visibility and Feedback to request changes. It does not replace the action-permission checklist.

The online manual also displays the effective visibility for each accessible chapter and explains how authorized role administrators can adjust it.
