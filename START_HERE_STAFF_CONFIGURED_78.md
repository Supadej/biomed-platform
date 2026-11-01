# Biomed fresh project with workbook staff setup — v78

This edition supersedes the admin-only starter: it includes exactly the 44 users in the newly supplied `username for Staff portal.xlsx`, 29 defined roles, 11 departments, 42 reporting links, and all 62 visibility settings for every role. Other business data remains empty.

## Login and account setup
Use each email and password from Sheet1 of the supplied workbook. All 44 passwords were verified against their salted hashes and through the local login API. No extra staff or recovery administrator has been added. System Admin is the single administrator listed in the workbook. The workbook and plaintext passwords are NOT included in the project ZIP.

- User identity, position, department and reporting manager follow Sheet1.
- The 889 permission codes and Y/N selections follow Roles, except for the 38 changes in yesterday's approved conflict-resolution plan.
- A = All records, D = Department, R = Reporting team, OR = Own records, OS = Own + assigned.
- All 1,798 role/module visibility assignments follow Visibility exactly. Visibility does not grant an action that the role's permissions deny.
- Reporting references were resolved by exact normalized names in this workbook and checked for missing managers, duplicates and cycles. Two users have no reporting manager; 42 users have resolved manager links.

## Approved conflict changes
The 35 role/application conflicts identified in Sheet7 match the previously approved plan exactly. The same decisions were applied:
- 21 roles: enable is_view, retaining their selected individual actions.
- 12 roles: enable crm_view, retaining their selected individual actions.
- HR Manager: keep is_view disabled; remove isolated is.master-customers.view and is.dashboard.view.
- Marketing Communication Specialist: keep is_view disabled; remove isolated is.master-customers.view, is.dashboard.view and is.quotation.progress.

Total: 33 permissions enabled, 5 removed, 25 roles affected. No other permission selection was changed. The rationale and exact changes are recorded in Access_Conflict_Decisions_78.json. Staff_Reporting_Map_78.json lists the imported reporting structure without passwords. Staff_Setup_Validation_78.json records the source workbook checksum and validation totals.

## Still empty
There are no website brands/catalogue items/uploads, operational brands, products, suppliers, customers, warehouses, inventory, CRM stages/cards, events, requests, expenses, financial entries, budgets or service jobs. Configure CRM stages again before creating cards. Database schema, permission definitions, application labels, standard document/status definitions and technical defaults remain so the application can run. Existing website design/company identity remains.

## Deploy on Railway
1. Keep the existing volume attached to biomed-platform at /data.
2. In Variables, set:

   BIOMED_DATABASE_PATH=/data/biomed-staff-configured-v78.sqlite3

   This is a NEW database filename. The existing old database file is left untouched. If you retain an older database path, the packaged staff setup will not replace its contents.
3. Set BIOMED_RECOVER_BUNDLED_SNAPSHOT to 0 or remove it. Keep legacy demo imports disabled. This edition does not execute the former recovery, company import or demo routines, and does not repeatedly reset user/password/role choices at startup.
4. Extract this ZIP and upload the CONTENTS of Biomed_Staff_Configured to your GitHub repository root. Include all code and data/biomed.sqlite3. Do not put the project under an extra nested folder. Commit and let Railway deploy the new commit.
5. Open your site's /api/health endpoint. It must report release staff-configured-v78. If it shows another release, the deployment is still running older code. Do not roll back expecting the new functions to remain.
6. Sign in using Sheet1. Verify Users = 44 and Roles = 29. Open Reporting Hierarchy and role visibility. Financial → Budget Setting & Approvals → Annual budgets & monthly approvals is included.
7. Export a full-system backup after confirming the setup. Keep the same volume and database path for later code updates so new settings and records survive.

This package creates the configured database only if that NEW destination file is absent. It never overwrites an existing database. It has not been deployed to your Railway account here.

## Verification
- All 44 workbook passwords succeeded through the local authentication API.
- Role grants match Roles with only the 38 approved changes.
- All users, reporting links and 1,798 scope assignments match the workbook.
- Reporting-team membership matches the imported hierarchy.
- SQLite integrity and foreign-key checks passed.
- Startup/restart retained user, permission and scope settings and a newly added test record on a temporary copy.
- Business tables and content lists remain empty.
- Source syntax checks and fresh-start/restart test passed.
- Actual Railway deployment and full browser visual verification remain unverified here.
