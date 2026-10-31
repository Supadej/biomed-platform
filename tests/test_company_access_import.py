import base64
import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import test_crm
import serve
import company_access_import as access
import permissions_policy as policy
import record_visibility as visibility


class AccessImportTests(unittest.TestCase):
 def setUp(self):
  self.fixture=test_crm.CRM();self.fixture.setUp()
  salt,digest,it=serve.password_record('New-access-password-2026')
  self.payload={'roles':{'System Admin':[p['key'] for p in policy.CATALOG['permissions']], 'Employee':['dashboard','crm_view','crm.leads.view']},
   'scopes':{'System Admin':{m:'all' for m in visibility.modules()},'Employee':{m:'assigned' for m in visibility.modules()}},'users':[]}
  with serve.connect() as c:
   for i,email in [('1','one@example.invalid'),('2','two@example.invalid')]:
    c.execute('INSERT INTO accounts(id,email,name,role,user_id,password_hash,salt,iterations,created_at) VALUES(?,?,?,?,?,?,?,?,?)',('a'+i,email,'Old name','System Admin' if i=='1' else 'Employee','u'+i,digest,salt,it,'now'))
    c.execute('INSERT INTO sessions VALUES(?,?,?,?)',('s'+i,'a'+i,9999999999,1))
    self.payload['users'].append(dict(name='Updated '+i,email=email,role='System Admin' if i=='1' else 'Employee',department='Sales',managerEmail='' if i=='1' else 'one@example.invalid',salt=base64.b64encode(salt).decode(),passwordHash=base64.b64encode(digest).decode(),iterations=it))
 def tearDown(self):
  self.fixture.tearDown();self.fixture.doCleanups()
 def test_exact_mapping_preservation_and_restart(self):
  with serve.connect() as c:
   before=json.loads(c.execute('SELECT value FROM workspace WHERE key=?',(access.KEY,)).fetchone()[0]);others=c.execute('SELECT key,value FROM workspace WHERE key<>? ORDER BY key',(access.KEY,)).fetchall()
   self.assertTrue(access.apply(c,self.payload)['applied'])
   data=json.loads(c.execute('SELECT value FROM workspace WHERE key=?',(access.KEY,)).fetchone()[0])
   self.assertEqual(data['roles']['Employee'],self.payload['roles']['Employee']);self.assertEqual(data['roleRecordScopes']['Employee'],self.payload['scopes']['Employee'])
   self.assertEqual(data['users'][1]['managerId'],'u1');self.assertEqual(data['users'][1]['id'],before['users'][1]['id'])
   self.assertEqual(data['pipeline'],before['pipeline']);self.assertEqual(data['visits'],before['visits']);self.assertEqual(others,c.execute('SELECT key,value FROM workspace WHERE key<>? ORDER BY key',(access.KEY,)).fetchall())
   self.assertEqual(c.execute('SELECT count(*) FROM sessions').fetchone()[0],0)
   c.execute("UPDATE accounts SET name='Later edit' WHERE id='a2'")
   self.assertFalse(access.apply(c,self.payload)['applied']);self.assertEqual(c.execute("SELECT name FROM accounts WHERE id='a2'").fetchone()[0],'Later edit')
 def test_reporting_cycle_rejected(self):
  self.payload['users'][0]['managerEmail']='two@example.invalid'
  with serve.connect() as c:
   with self.assertRaisesRegex(ValueError,'cycle'):access.apply(c,self.payload)
 def test_missing_live_user_rolls_back(self):
  self.payload['users'][1]['email']='missing@example.invalid'
  with serve.connect() as c:
   before=c.execute('SELECT value FROM workspace WHERE key=?',(access.KEY,)).fetchone()[0]
   with self.assertRaisesRegex(ValueError,'identity not unique'):access.apply(c,self.payload)
   self.assertEqual(before,c.execute('SELECT value FROM workspace WHERE key=?',(access.KEY,)).fetchone()[0]);self.assertFalse(c.execute('SELECT 1 FROM data_migrations WHERE name=?',(access.VERSION,)).fetchone())
 def test_late_failure_rolls_back_accounts_and_workspace(self):
  with serve.connect() as c:
   before=c.execute('SELECT value FROM workspace WHERE key=?',(access.KEY,)).fetchone()[0];accounts=c.execute('SELECT * FROM accounts ORDER BY id').fetchall()
   with patch('crm_api.bind_users',side_effect=RuntimeError('late failure')):
    with self.assertRaises(RuntimeError):access.apply(c,self.payload)
   self.assertEqual(before,c.execute('SELECT value FROM workspace WHERE key=?',(access.KEY,)).fetchone()[0]);self.assertEqual(accounts,c.execute('SELECT * FROM accounts ORDER BY id').fetchall())
 def test_startup_backup_and_idempotence(self):
  with serve.connect() as c:
   c.execute('INSERT OR IGNORE INTO data_migrations VALUES(?)',('company-staff-roster-69',))
  path=Path(self.fixture.temp.name)/'approved.json';path.write_text(json.dumps(self.payload))
  with patch.object(access,'PAYLOAD',path):
   serve.prepare_database();serve.prepare_database()
  self.assertEqual(len(list((serve.DB.parent/'private-archives').glob('*.zip'))),1)
 def test_payload_not_public(self):
  h=object.__new__(serve.Handler);h.path='/company-access-workbook-20261031.json'
  self.assertTrue(h.private_static_path())
 def test_unknown_permission_rejected(self):
  self.payload['roles']['Employee'].append('unknown.permission')
  with self.assertRaises(ValueError):access.validate(self.payload)
