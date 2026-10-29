# Roles and responsive layout update

- Added Product Catalogue module and eight related action permissions to central registry (v8). Existing roles are migrated on next load; System Admin always receives all published permissions from the authenticated session role.
- Reconciled Staff Portal catalogue menu check, server-side catalogue API, and shared permission evaluator. Existing users and passwords are unchanged.
- Added layout overrides at desktop/tablet/mobile breakpoints for Financial, Biomed IS, Staff Portal, catalogue admin. Financial-entry button is anchored below its grid cell, and full-width on phones.
- No production database changes and no account resets.

## How to test
1. Login as a genuine System Admin; open Roles & permissions and Product Catalogue; attempt Sync, Add, Edit, Import, Enquiries.
2. Test an ordinary user without catalogue permission (access should remain denied).
3. Test desktop 1440px, tablet 768px, mobile 390px. Verify finance form button, toolbars, tables and sidebar.
4. Clear stale app cache if the old permission alert persists after deployment.

Live Railway and cross-browser end-to-end UI tests were not performed.
