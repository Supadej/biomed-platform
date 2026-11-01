# Included administrator login

Email: testadmin@example.invalid
Password: TEST-Only-ChangeMe-2026!
Role: System Admin

This NEW package includes data/biomed.sqlite3 with this account.
The password is stored as a salted hash. No other staff accounts or prior
production business records are included in this fresh database.
Website and internal AI retain their disabled defaults.

Tested through the real login HTTP endpoint and authenticated /api/auth/me.

Railway:
- If the configured database does not exist, startup copies this bundled database.
- An EXISTING volume database is retained. Deploying this ZIP does not add this
  account to an already-existing /data/biomed.sqlite3.
- For an existing empty-account database, run python3 setup_admin.py inside the
  deployed /app folder. Enter the email and password above when prompted.
- For an existing matching account, python3 recover_login.py can set its password.
Do not delete or overwrite an existing volume to activate this login.
Change this shared test password before normal operational use.
