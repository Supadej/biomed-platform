# Restore account access

This package has no seeded account database and no automatic default password.

Run the following in the application folder on the machine hosting Biomed:

    python3 recover_login.py

On Railway, use a shell inside the running service container with the production
volume mounted. A local Railway CLI shell that only imports environment variables
cannot access the remote volume. On Mac, open Terminal in the extracted project
folder. The tool reads the same BIOMED_DATABASE_PATH as serve.py.

The tool first prints the database path and account emails, roles, disabled state,
and temporary-lock state. If the expected account is absent, cancel and verify
the existing persistent volume/database. Do not replace it with a fresh database.

For an existing active account, enter its email and choose a new password twice.
A complete SQLite backup is made before resetting the password and lock counter.
Existing sessions for that account are removed. Roles and business records stay
unchanged. Disabled accounts are not reactivated by this tool.

Read-only diagnosis:
    python3 recover_login.py --list

Only for an intentionally new database with no existing accounts:
    python3 setup_admin.py

Verification: a locked test account was recovered and then authenticated through
the real login HTTP endpoint (200). Backup, session revocation, business-record
preservation, and missing-database refusal were checked. Your production account
has not been inspected or reset from here.
