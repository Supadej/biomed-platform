# Fix the existing Railway deployment

The live website returned HTTP 404 for /api/auth/me. This prevents Staff Portal from initializing. The repository's original serve.py listens only on localhost and permits localhost origins only. A static HTTP server serves HTML but cannot implement login or database routes.

## Upload the patch

Extract Biomed_Railway_Login_Fix.zip. Upload serve.py, Dockerfile, railway.json and .dockerignore to the ROOT of Supadej/biomed-platform, replacing serve.py. The ZIP also includes this guide and an optional regression test. Upload the extracted files, not the ZIP or its parent folder. All application HTML, CSS, JavaScript, workflows and existing database files stay unchanged.

## Railway settings

1. Open your existing biomed-platform service, connected to Supadej/biomed-platform and its deployment branch.
2. Settings: Root Directory must be the repository root (blank or /). The Dockerfile and railway.json must be at that root.
3. Remove any old static-server build/start overrides. Builder: Dockerfile. Start Command: python serve.py. Do not use python -m http.server. Healthcheck Path: /api/health. If an old target port is set, remove it so Railway uses PORT, or set a matching PORT variable deliberately.
4. Attach a persistent volume to this service, mounted at /data. Keep one instance for this SQLite deployment. Never replace an existing volume database.
5. Variables:
   BIOMED_DATABASE_PATH=/data/biomed.sqlite3
   BIOMED_HOST=0.0.0.0
   BIOMED_HTTPS=1
   BIOMED_ALLOWED_ORIGINS=https://biomed-platform-production-5b19.up.railway.app
   Railway supplies PORT; do not set 8765 unless deliberately configuring its target port too.
6. Deploy the new commit. Startup log must contain: Biomed server listening on 0.0.0.0:<port>.

On the first startup only, an absent volume database is copied from the existing repository data/biomed.sqlite3, using SQLite's backup API. Later deployments preserve the volume DB. This patch includes no database and does not reset accounts, records or passwords. If your live database is elsewhere, copy it safely into the volume before first startup instead of seeding an older repository snapshot.

## Verify

- /api/health returns JSON containing database: SQLite.
- /api/auth/me returns JSON with HTTP 401 while signed out (expected), not 404.
- Refresh the homepage with Command+Shift+R and click Staff Portal.
- Test a normal login, save a record, restart and confirm the record remains.

The patch was checked locally against the repository's policy/workflow tests and a real HTTP test for health, session routing, domain origin validation and database preservation. It has not yet been deployed to your Railway service. It retains the current application's browser-local attachment limitations; attachment storage redesign is outside this targeted login/deployment fix.
