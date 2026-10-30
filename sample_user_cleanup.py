"""Remove only the twelve screenshot-identified, unregistered sample profiles."""
import json

KEY = 'biomed_portal_v33_clean'
VERSION = 'remove-requested-sample-users-65'
TARGETS = dict(zip(
    ['u2', 'u3', 'u4', 'u5', 'u6', 'u-accounting'],
    ['director@biomedthai.com', 'operations@biomedthai.com',
     'diag.manager@biomedthai.com', 'research@biomedthai.com',
     'sales.demo@biomedthai.com', 'accounting.demo@biomedthai.com']))
TARGETS.update({'TEST-DEMO-V2-EMP-' + str(i):
                'demo.employee' + str(i + 1) + '@example.invalid' for i in range(6)})

def apply(c):
    c.execute('CREATE TABLE IF NOT EXISTS data_migrations(name TEXT PRIMARY KEY)')
    if c.execute('SELECT 1 FROM data_migrations WHERE name=?', (VERSION,)).fetchone():
        return []
    row = c.execute('SELECT value FROM workspace WHERE key=?', (KEY,)).fetchone()
    if not row:
        return []  # Retry after first workspace creation.
    data = json.loads(row[0])
    registered = {r[0] for r in c.execute('SELECT user_id FROM accounts')}
    removed = {u['id'] for u in data.get('users', [])
               if u.get('id') in TARGETS
               and str(u.get('email', '')).lower() == TARGETS[u['id']]
               and u['id'] not in registered}
    if removed:
        data['users'] = [u for u in data['users'] if u.get('id') not in removed]
        for u in data['users']:
            if u.get('managerId') in removed:
                u['managerId'] = ''
        # Preserve all transaction owners, employee references and history.
        for uid in removed:
            c.execute('DELETE FROM staff_profiles WHERE user_id=?', (uid,))
            c.execute('INSERT INTO staff_directory_audit(at,actor,action,user_id) '
                      "VALUES(datetime('now'),'system','remove requested sample profile',?)", (uid,))
        c.execute('UPDATE workspace SET value=?,revision=revision+1 WHERE key=?',
                  (json.dumps(data, ensure_ascii=False), KEY))
    c.execute('INSERT INTO data_migrations VALUES(?)', (VERSION,))
    return sorted(removed)
