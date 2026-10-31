# Biomed · GitHub and Railway deployment

This edition uses SQLite with a persistent Railway volume. It includes the interactive, role-filtered online manual. No SQL Server configuration is required.

## 1. Preserve your live data

Before deployment, take a consistent backup of the CURRENT live database and retain the existing encryption keys. The SQLite file bundled in a project ZIP is not necessarily your live database. Do not overwrite the existing mounted database with it. Do not delete/recreate the live volume during a code update.

A GitHub repository backs up source code; it is not a backup of the operational database. Keep database backups and secrets separately under company-controlled access.

## 2. Prepare the GitHub repository

Extract `Biomed_Portal_With_Admin_Login`. The repository root should contain `Dockerfile`, `railway.json`, `run_server.py`, `serve.py` and `requirements.txt`. If you retain the wrapper folder in the repository, set Railway Root Directory to that folder.

Use a private repository. The included `.gitignore` excludes `.env`, databases, logs, backups, virtual environments and the test-access file. It does not automatically remove files that were already tracked. Inspect the staged files before committing.

For a NEW repository, from the project folder:

```bash
git init
git add .
git status
```

Review the file list. Do not commit passwords, API keys, OAuth secrets, encryption keys or operational databases. If a database was previously tracked, remove it from the index without deleting the local file:

```bash
git rm --cached data/biomed.sqlite3
```

Run that command only if the file is actually tracked. Then commit and push:

```bash
git commit -m "Add role-based user manual and Railway production entry"
git branch -M main
git remote add origin YOUR_PRIVATE_GITHUB_REPOSITORY_URL
git push -u origin main
```

For an existing repository, retain its history and remote. Review the changes and commit the update rather than recreating the repository blindly.

## 3. Configure Railway

1. Select the intended Railway project/environment and connect the GitHub repository.
2. Check the Root Directory and use the included Dockerfile build.
3. Keep the existing volume, or attach a persistent volume at `/data` for a new service before entering live records.
4. Configure the variables below. Railway supplies `PORT`; do not replace it with the local development port.
5. Use `python run_server.py` as the start command. The supplied `railway.json` specifies it and the health check.
6. Generate/select the HTTPS domain and verify custom-domain DNS and certificate status if applicable.

```dotenv
BIOMED_HOST=0.0.0.0
BIOMED_DATABASE_PATH=/data/biomed.sqlite3
BIOMED_HTTPS=1
BIOMED_ALLOWED_ORIGINS=https://YOUR-RAILWAY-OR-CUSTOM-DOMAIN
BIOMED_THREADS=8
```

Do not add SQL Server variables. `BIOMED_ALLOWED_ORIGINS` accepts comma-separated HTTPS origins without a path or trailing slash. The automatically supplied `RAILWAY_PUBLIC_DOMAIN` is also recognized.

The production entry uses Waitress/WSGI. Keep `serve.py` for local development; the Dockerfile and Railway configuration now use `run_server.py`.

## 4. Preserve optional integration settings

Retain the existing `BIOMED_AI_ENCRYPTION_KEY` and `BIOMED_OUTLOOK_ENCRYPTION_KEY` when migrating saved encrypted credentials. Replacing them prevents decryption of the previous values.

Store provider and OAuth secrets in Railway Variables, never in Git. Keep the Outlook redirect URI consistent with the HTTPS hostname. For a standby copy, set `BIOMED_ENABLE_OUTLOOK_WORKER=0` until deliberate activation, so two deployments do not independently change the same calendar. The existing default keeps the worker enabled if you do not set this variable.

## 5. Existing service versus new service

### Updating your current live service

Deploy code while retaining its existing database path and mounted volume. The application preserves an existing database. Verify the volume/path before deploying and check representative records after startup.

### Creating a separate backup deployment

Use a separate volume and a consistent copy of current live data. Transfer it with your IT-approved authenticated method while the destination application is stopped. A raw copy of an active SQLite main file without its WAL transactions may be incomplete; use a proper SQLite backup or a clean shutdown/checkpoint.

Do not allow two independent deployments to accept normal live writes unless you have a reconciliation plan. GitHub deployment does not synchronize their databases automatically.

### Fresh repository without a committed database

A clean repository normally has no shared test login. After the service starts with the volume, run this ON THE RUNNING SERVICE/container using its mounted `/data` volume:

```bash
python bootstrap_admin.py
```

Use your team's authenticated Railway container/SSH execution facility with an interactive terminal. Running it on your own Mac instead creates a local account, not an account on Railway. The script prompts for company email, full name, password and matching confirmation. It rejects an existing account. Never add an initial password to Git or command-line arguments to bypass the interactive prompt.

## 6. Open the manual

Sign in and select **User manual** in the sidebar beside Database administration (or under Help & support), or visit `/user-manual.html` on your deployment.

The server returns only the modules and action instructions available to that account. The role responsibility description comes from current Roles & responsibilities settings. Search, system filtering, bookmarks and chapter printing are available. Refresh access updates permissions; returning to the page and periodic refresh also recheck them. A bookmarked chapter URL cannot bypass authorization.

Opening the HTML file directly from disk cannot retrieve authenticated manual content; use the running application URL.

## 7. Acceptance checks

- [ ] HTTPS `/api/health` succeeds and startup logs show no failure.
- [ ] Login, sign-out, password reset and a restricted user work.
- [ ] A uniquely named test record survives reload, process restart and redeployment.
- [ ] A Service Engineer without Financial access receives no Financial manual chapters.
- [ ] Updating the role description/actions changes the manual after Refresh access.
- [ ] Service and Application jobs save/edit, including optional Calendar and Helpdesk links.
- [ ] Existing source documents, stock balances and financial records match the pre-deployment backup.
- [ ] Column preferences, Clear filters and inline Details work.
- [ ] PDF/HTML reports and email attachment behaviour are tested on your actual Android/iPhone devices.
- [ ] Full-system backup and recovery are exercised in a separate TEST environment.

## 8. Troubleshooting

**Health check fails:** inspect build/startup logs, dependencies, Root Directory, start command and volume permissions.

**Invalid origin:** configure the exact current HTTPS origin, including the hostname but no URL path.

**Login loops:** verify HTTPS, cookie retention, database path and the account on the actual deployed database.

**Data disappears after redeployment:** check the mounted `/data` volume and `BIOMED_DATABASE_PATH`. Do not fix it by restoring a stale bundled database over live data.

**An old record is missing:** clear filters and check ownership/sharing before assuming the data was deleted.

**Email opens without attachment:** use Email with attachment where supported, or download and attach manually. The Open email app fallback cannot automatically attach the downloaded file.

## 9. Update, backup and rollback

For every update: take a recovery point, review/test the change, deploy, verify acceptance checks and record the commit. Keep database backups off the running service too. A source-code rollback is not automatically a database rollback. If new writes have occurred, preserve and reconcile them before restoring an older database. Do not reset the volume just to make a deployment appear successful.

No deployment has been performed by preparing this package. Device/browser visual validation and real Railway acceptance remain your deployment checks.

## Official references

- Railway deployments: https://docs.railway.com/deployments
- Railway volumes: https://docs.railway.com/volumes
- Waitress: https://docs.pylonsproject.org/projects/waitress/en/stable/


## Record visibility update
See UPDATE_73_RECORD_VISIBILITY.md for the new role/function limits. Keep your current persistent database volume. Initial scopes migrate once; subsequent role scope edits persist.
