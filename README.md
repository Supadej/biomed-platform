# Biomed complete test workspace — granular roles and permissions

This complete package includes the website, Staff Portal, Biomed IS, Budgeting and fictional test data.

Stop the previous Biomed server with Control+C. Save the ZIP to Downloads, then run:

```bash
unzip -o "$HOME/Downloads/Biomed_Workspace_Improvements_Mac.zip" -d "$HOME/Downloads" &&
cd "$HOME/Downloads/Biomed_Workspace_Improvements_Mac" &&
chmod +x START_ON_MAC.command &&
./START_ON_MAC.command
```

Open http://127.0.0.1:8765/?portal=1 and press Command+Shift+R.

Sample administrator: `testadmin@example.invalid`
Password: `TEST-Only-ChangeMe-2026!`

Other sample accounts use the same test-only password. See TEST_GUIDE.md.

To retain your current records and accounts, stop its server and copy the old `data/biomed.sqlite3` into this folder's `data` directory before starting. The first start migrates its existing roles once. Start with the sample database to explore the included role templates.

Open Staff Portal → Website & Administration → Roles & responsibilities to configure access. PERMISSIONS_GUIDE.md includes instructions, scope details and the complete permission catalog.

This is a local SQLite test application. The SQL Server migration schema/transfer starter is included; a SQL Server runtime adapter is still required for that deployment. File attachments retain their existing browser storage.
