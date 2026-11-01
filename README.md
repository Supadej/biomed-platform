Latest staff roster update: [Mapping and deployment](UPDATE_69_COMPANY_STAFF_MAPPING.md) · [Role authorization defaults](COMPANY_ROLE_AUTHORIZATION_69.html)

# Biomed · Online manual and Railway edition

**Start here:** [Interactive GitHub/Railway deployment guide](DEPLOY_GITHUB_RAILWAY.html) ([Markdown](DEPLOY_GITHUB_RAILWAY.md)).

Sign in and choose **User manual** in the sidebar beside Database administration (or under Help & support). Its content follows your saved role and action permissions. Open it through the running site, not directly as a disk file.

This edition uses SQLite with a persistent Railway volume. No separate SQL Server 2022 project is included. Production entry: `python run_server.py`. Preserve the current live database and encryption keys; do not overwrite them with the bundled local/test database.

[Manual update and validation](UPDATE_64_USER_MANUAL.md)

[Latest update: mobile menu and report email](UPDATE_63_MOBILE_MENU_AND_REPORT_EMAIL.md)

[Latest update: Application job Save](UPDATE_62_APPLICATION_JOB_SAVE.md)

[Latest update: PDF and HTML reports](UPDATE_61_REPORTS.md)

[Latest update: details, columns and date clearing](UPDATE_60_DETAILS_COLUMNS_AND_CLEAR_FILTERS.md)

[Latest update: inline user editing, password reset and Portal sign-in](UPDATE_59_INLINE_USER_EDIT_RESET_AND_PORTAL_LOGIN.md)

[Latest update: document statuses and transaction flows](UPDATE_58_DOCUMENT_STATUS_AND_FLOW.md)

[Latest update: staff accounts, profiles and library](UPDATE_57_STAFF_ACCOUNTS_PROFILES_AND_LIBRARY.md)

[Latest update: Calendar dates and reference menus](UPDATE_56_CALENDAR_DATES_AND_REFERENCE_MENUS.md)

[Latest update: matched Service Job feedback](UPDATE_55_MATCHED_SERVICE_FEEDBACK.md)

[Latest update: Application jobs and reports](UPDATE_54_APPLICATION_JOBS_AND_REPORTS.md)

[Latest update: Application Service and compact controls](UPDATE_53_APPLICATION_SERVICE_AND_COMPACT_CONTROLS.md)

[Latest update: filter and section spacing](UPDATE_52_FILTER_AND_SECTION_SPACING.md)

[Latest update: Analysis and calendar defaults](UPDATE_51_ANALYSIS_AND_CALENDAR_DEFAULTS.md)

[Latest update: single Columns menu](UPDATE_50_SINGLE_COLUMNS_MENU.md)

Latest update: [Mobile date/time input sizing](UPDATE_49_MOBILE_DATE_INPUTS.md).

Latest update: [Staff Portal deep analysis](UPDATE_48_SALES_DEMO_AND_COMMERCIAL_ANALYSIS.md).

Latest update: see [Smooth rows and manual follow-up](UPDATE_47_SMOOTH_ROWS_AND_MANUAL_FOLLOWUP.md).

Latest update: see [Presentation and column widths](UPDATE_46_PRESENTATION_AND_COLUMN_WIDTHS.md) for interface changes and resizing instructions.

## Latest workflow update

Sales Plan now has customizable stages, a drag-and-drop board and product target cards for 100% incentive schemes. External Helpdesk and Project activities use the same stage management and interactive boards. Use **Activity board** in Project & Activity. See STAFF_PORTAL_CRM_UPDATE.md for setup, permissions and matching rules.

# Biomed platform — native Staff Portal CRM

See **STAFF_PORTAL_CRM_UPDATE.md** for the updated navigation, installation, permissions, document binding and 100% incentive target rule.

This update adds clickable calendar-date quick creation and Odoo-style record sheets with tabs, stage bars, Save/Discard, Save & New and inline item entry.

The separate CRM frontend has been removed. Its four selected features now run inside Staff Portal.

# Biomed complete platform with CRM

This package includes the website, Staff Portal, Biomed IS, Financial, CRM and the existing fictional test data. Read **CRM_INTEGRATION_GUIDE.md** for permissions, bridge settings, source limitations and deployment instructions.

Extract to a new test directory. Stop the previous local Biomed server with Control+C, then run from the extracted project folder:

```bash
bash start.sh
```

Alternatively run `python3 serve.py`, or double-click `START_ON_MAC.command` on macOS. Sign in at `http://127.0.0.1:8765/?portal=1`, then open the CRM group in Staff Portal. Use the existing shared account; CRM has no separate password.

For an existing server update, retain the persistent database and volume. **Do not overwrite your server database with the included demo database.** Startup adds CRM tables and System Admin permissions. This package has not been deployed to Railway. SQL Server files are staging/export tools; the live server still uses SQLite.

This ZIP includes a fresh database with testadmin@example.invalid / TEST-Only-ChangeMe-2026! as System Admin. See ADMIN_LOGIN_INCLUDED.md for existing Railway volume instructions.
For a new installation only, run `python3 setup_admin.py` to create the first administrator.
For an existing account that cannot sign in, run `python3 recover_login.py` in the application directory on the server. See LOGIN_RECOVERY.md.

To retain your current records and accounts, stop its server and copy the old `data/biomed.sqlite3` into this folder's `data` directory before starting. The first start migrates its existing roles once. Start with the sample database to explore the included role templates.

Open Staff Portal → Website & Administration → Roles & permissions to configure access. PERMISSIONS_GUIDE.md includes instructions, scope details and the complete permission catalog.

This is a local SQLite test application. The SQL Server migration schema/transfer starter is included; a SQL Server runtime adapter is still required for that deployment. File attachments retain their existing browser storage.
