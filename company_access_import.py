"""One-time application of the approved 2026-10-31 access workbook.

Only salted password hashes ship with the application. Startup takes a recovery
archive before this transactional migration; later administrator edits survive.
"""
import base64
import datetime
import json
from pathlib import Path

import company_staff_import
import permissions_policy as policy
import record_visibility

KEY = company_staff_import.KEY
VERSION = 'company-access-workbook-20261031-v1'
PAYLOAD = Path(__file__).with_name('company-access-workbook-20261031.json')


def pending(c):
    return (PAYLOAD.is_file()
            and bool(c.execute('SELECT 1 FROM workspace WHERE key=?', (KEY,)).fetchone())
            and not c.execute('SELECT 1 FROM data_migrations WHERE name=?', (VERSION,)).fetchone())


def validate(payload):
    roles, scopes, users = payload['roles'], payload['scopes'], payload['users']
    valid = {p['key'] for p in policy.CATALOG['permissions']}
    if not roles or not users or set(roles) != set(scopes):
        raise ValueError('Incomplete workbook access mapping')
    for grants in roles.values():
        if not isinstance(grants, list) or len(grants) != len(set(grants)) or set(grants) - valid:
            raise ValueError('Invalid workbook permission codes')
    record_visibility.validate_config(scopes, roles)
    if any(set(s) != set(record_visibility.modules()) for s in scopes.values()):
        raise ValueError('Workbook must specify every visibility module')
    if set(roles.get('System Admin', [])) != valid:
        raise ValueError('Workbook must preserve System Admin recovery access')
    emails = [u['email'].strip().lower() for u in users]
    if len(emails) != len(set(emails)):
        raise ValueError('Duplicate workbook login emails')
    links = {}
    for u in users:
        email = u['email'].strip().lower()
        manager = u['managerEmail'].strip().lower()
        if u['role'] not in roles or not u['name'].strip() or not u['department'].strip():
            raise ValueError('Invalid workbook user mapping')
        if '@' not in email or manager and manager not in emails:
            raise ValueError('Unresolved reporting identity')
        links[email] = manager
        if (len(base64.b64decode(u['salt'], validate=True)) != 16
                or len(base64.b64decode(u['passwordHash'], validate=True)) != 32
                or not isinstance(u['iterations'], int) or u['iterations'] < 310000):
            raise ValueError('Invalid workbook password hash')
    for email in links:
        seen = set()
        while email:
            if email in seen:
                raise ValueError('Reporting hierarchy contains a cycle')
            seen.add(email)
            email = links[email]


def apply(c, payload=None):
    c.execute('CREATE TABLE IF NOT EXISTS data_migrations(name TEXT PRIMARY KEY)')
    if c.execute('SELECT 1 FROM data_migrations WHERE name=?', (VERSION,)).fetchone():
        return {'applied': False}
    if payload is None:
        if not PAYLOAD.is_file():
            return {'applied': False}
        payload = json.loads(PAYLOAD.read_text())
    validate(payload)
    row = c.execute('SELECT value FROM workspace WHERE key=?', (KEY,)).fetchone()
    if not row:
        return {'applied': False}
    c.execute('SAVEPOINT company_access_import')
    try:
        data = json.loads(row[0])
        users = data.get('users', [])
        resolved = {}
        # All identities must already exist. Never guess or create duplicates.
        for source in payload['users']:
            email = source['email'].strip().lower()
            profiles = [u for u in users if str(u.get('email', '')).strip().lower() == email]
            accounts = c.execute('SELECT id,user_id FROM accounts WHERE lower(email)=?', (email,)).fetchall()
            if len(profiles) != 1 or len(accounts) != 1 or profiles[0]['id'] != accounts[0][1]:
                raise ValueError('Workbook account/profile identity not unique: ' + email)
            resolved[email] = (profiles[0], accounts[0][0])
        # Finish legacy catalog upgrades before installing explicit Y/N choices.
        policy.migrate_portal(data)
        data.setdefault('roles', {}).update(payload['roles'])
        data.setdefault('roleRecordScopes', {}).update(payload['scopes'])
        for role in payload['roles']:
            data.setdefault('roleDescriptions', {}).setdefault(role, '')
        data['departments'] = list(dict.fromkeys(data.get('departments', []) + [u['department'] for u in payload['users']]))
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        affected = {u['id'] for u in users if u.get('role') in payload['roles']}
        for source in payload['users']:
            email = source['email'].strip().lower()
            profile, account_id = resolved[email]
            manager = source['managerEmail'].strip().lower()
            profile.update(name=source['name'], email=email, role=source['role'],
                           position=source['role'], department=source['department'],
                           managerId=resolved[manager][0]['id'] if manager else '')
            affected.add(profile['id'])
            c.execute('UPDATE accounts SET name=?,role=?,password_hash=?,salt=?,iterations=?,failed_attempts=0,locked_until=0 WHERE id=?',
                      (source['name'], source['role'], base64.b64decode(source['passwordHash']),
                       base64.b64decode(source['salt']), source['iterations'], account_id))
            for record in data.get('hrprofiles', []):
                if str(record.get('employee') or record.get('owner')) == profile['id']:
                    record.update(email=email, position=source['role'])
            c.execute('INSERT INTO staff_directory_audit(at,actor,action,user_id) VALUES(?,?,?,?)',
                      (now, 'system', VERSION, profile['id']))
        for uid in affected:
            c.execute('DELETE FROM sessions WHERE account_id IN (SELECT id FROM accounts WHERE user_id=?)', (uid,))
            c.execute('UPDATE staff_profiles SET version=version+1 WHERE user_id=?', (uid,))
        c.execute('UPDATE workspace SET value=?,revision=revision+1 WHERE key=?', (json.dumps(data, ensure_ascii=False), KEY))
        import crm_api
        crm_api.bind_users(c)
        c.execute('INSERT INTO data_migrations VALUES(?)', (VERSION,))
        c.execute('RELEASE company_access_import')
        return {'applied': True, 'users': len(payload['users']), 'roles': len(payload['roles']),
                'visibilityModules': len(record_visibility.modules())}
    except Exception:
        c.execute('ROLLBACK TO company_access_import')
        c.execute('RELEASE company_access_import')
        raise
