# Staff accounts, profiles and employee library

## User directory
- Native Staff Portal screen with responsive two-column forms, paired password fields, separate action rows and a horizontally scrollable staff table on small devices.
- Initial password and confirmation must match in both browser and backend before creation. Accounts and staff identity are created in one transaction; Employee is the default role.
- Search and active/inactive filters; edit name, email, department, role and Reports to. Account email/name/role and staff identity stay synchronized.
- Department reference list supports adding and removing unused departments. Existing assigned departments are retained during migration.
- Activate/deactivate and reset passwords with separate permission checks. Deactivation and password resets revoke existing sessions. Self-deactivation, removal of the last active System Admin, circular reporting lines and deactivating a manager with active direct reports are blocked.

## User Profile and User Library
- Overview menu contains User Profile and User Library.
- Each user can edit their own picture, mobile number, email, date of birth and LINE ID; their name/role/department remain administered in User directory.
- Picture upload supports PNG/JPEG/WebP, resizing locally before saving. Pictures may be removed.
- Changing account email requires current password. Self-service password change requires current password, new password and matching confirmation; password changes require signing in again.
- User Library shows active staff only: picture, name, mobile, email, DOB and LINE ID, with search and department filter. It exposes no password hashes, account IDs or administrative controls.

## Persistence and permissions
- New staff_profiles and staff_directory_audit tables are created at startup. Existing database content is preserved.
- Account actions are authenticated, origin checked, validated, audited and saved transactionally with optimistic version checks.
- Catalog version 23 adds separate User Profile/User Library access, self-profile and password actions, plus user view/edit/deactivate/reset password/manage departments actions.
- Existing employee roles receive profile/library access once. Existing user administrators receive the corresponding directory controls. Custom business grants are retained; later revocations remain revoked.
- Reporting hierarchy remains linked to the same managerId. Legacy generic identity writes cannot bypass the staff endpoints.
- Database backups include the new tables. Operational reset preserves personal profiles alongside accounts.

## Validation and delivery
- Full Python regression suite: 317 passed, followed by a passing additional profile backup/reset test and focused staff/database checks.
- Staff account/profile/library DOM interaction checks, previous Application Service and reference-menu/Calendar regressions, and JavaScript/inline-script syntax checks passed.
- Browser visual/device QA was not rerun because the previous automatic approval usage-limit block remains unresolved. Responsive styling has been implemented, but fresh rendered visual verification is incomplete.
- Full ZIP delivery only; no automatic deployment. Existing bundled database bytes preserved.
