#!/usr/bin/env python3
"""Local server-console account recovery. Never exposed as a web endpoint."""
import argparse
import getpass
import hashlib
import os
from pathlib import Path
import secrets
import sqlite3
import time

ROOT = Path(__file__).resolve().parent

def inspect_database(db):
    if not db.is_file():
        raise ValueError('Database does not exist. Check BIOMED_DATABASE_PATH and the persistent volume; no database was created.')
    with sqlite3.connect(db.as_uri() + '?mode=ro', uri=True) as c:
        if not c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='accounts'").fetchone():
            raise ValueError('This database has no account table. Verify that this is the correct application database.')
        return c.execute('SELECT email,role,disabled,locked_until FROM accounts ORDER BY email').fetchall()

def reset_password(db, email, password):
    if len(password) < 12:
        raise ValueError('Password must contain at least 12 characters.')
    inspect_database(db)
    with sqlite3.connect(db.as_uri() + '?mode=rw', uri=True) as c:
        row = c.execute('SELECT id,disabled FROM accounts WHERE lower(trim(email))=?', (email,)).fetchone()
        if not row:
            raise ValueError('Account not found. No account was created. Verify the database path or restore your original database.')
        if row[1]:
            raise ValueError('Account is disabled. This tool does not reactivate disabled accounts.')
        backup = db.with_name(db.name + '.before-login-recovery-' + time.strftime('%Y%m%d-%H%M%S') + '-' + secrets.token_hex(3) + '.bak')
        # Exclusive file creation and restrictive permissions protect the account backup.
        fd = os.open(backup, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        with sqlite3.connect(backup) as target:
            c.backup(target)
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 310000, dklen=32)
        c.execute('UPDATE accounts SET password_hash=?,salt=?,iterations=310000,failed_attempts=0,locked_until=0 WHERE id=?', (digest, salt, row[0]))
        c.execute('DELETE FROM sessions WHERE account_id=?', (row[0],))
    return backup

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--list', action='store_true', help='Inspect accounts without changing anything')
    args = parser.parse_args()
    db = Path(os.environ.get('BIOMED_DATABASE_PATH', str(ROOT / 'data' / 'biomed.sqlite3'))).resolve()
    print('Database:', db)
    try:
        rows = inspect_database(db)
        for email, role, disabled, locked in rows:
            print(email, '|', role, '|', 'disabled' if disabled else 'active', '|', 'temporarily locked' if locked > time.time() else 'unlocked')
        if not rows:
            print('No accounts exist in this database. If this is an existing installation, check the original database/volume first. For an intentionally new installation, run: python3 setup_admin.py')
            return
        if args.list:
            return
        email = input('Existing account email to reset (blank cancels): ').strip().lower()
        if not email:
            return
        if not any(r[0].strip().lower() == email for r in rows):
            raise ValueError('Account not found; no changes made.')
        password = getpass.getpass('New password (at least 12 characters): ')
        if password != getpass.getpass('Repeat new password: '):
            raise ValueError('Passwords did not match; no changes made.')
        backup = reset_password(db, email, password)
        print('Password reset and temporary lock cleared. Existing sessions for this account were signed out.')
        print('Backup:', backup)
        print('Sign in with the account email and the new password.')
    except (ValueError, sqlite3.Error) as e:
        parser.exit(1, str(e) + '\n')

if __name__ == '__main__':
    main()
