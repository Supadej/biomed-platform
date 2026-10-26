# Biomed complete platform with CRM

This package includes the website, Staff Portal, Biomed IS, Budgeting, CRM and the existing fictional test data. Read **CRM_INTEGRATION_GUIDE.md** for permissions, bridge settings, source limitations and deployment instructions.

Extract to a new test directory. Stop the previous local Biomed server with Control+C, then run from the extracted project folder:

```bash
bash start.sh
```

Alternatively run `python3 serve.py`, or double-click `START_ON_MAC.command` on macOS. Sign in at `http://127.0.0.1:8765/?portal=1`, then choose **CRM**. Use the existing shared account; CRM has no separate password.

For an existing server update, retain the persistent database and volume. **Do not overwrite your server database with the included demo database.** Startup adds CRM tables and System Admin permissions. This package has not been deployed to Railway. SQL Server files are staging/export tools; the live server still uses SQLite.

Sample administrator: `testadmin@example.invalid`
Password: `TEST-Only-ChangeMe-2026!`

Other sample accounts use the same test-only password. See TEST_GUIDE.md.

To retain your current records and accounts, stop its server and copy the old `data/biomed.sqlite3` into this folder's `data` directory before starting. The first start migrates its existing roles once. Start with the sample database to explore the included role templates.

Open Staff Portal → Website & Administration → Roles & responsibilities to configure access. PERMISSIONS_GUIDE.md includes instructions, scope details and the complete permission catalog.

This is a local SQLite test application. The SQL Server migration schema/transfer starter is included; a SQL Server runtime adapter is still required for that deployment. File attachments retain their existing browser storage.
