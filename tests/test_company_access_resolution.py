import copy
import json
import sqlite3
import unittest
from unittest.mock import patch

import test_crm
import serve
import company_access_resolution as fix


class AccessResolutionTests(unittest.TestCase):
 def setUp(self):
  self.fixture=test_crm.CRM();self.fixture.setUp()
  self.plan=[
   {'role':'Sales Representative','gate':'is_view','decision':'enable_access','permissions':['is.quotation.view','is.quotation.create'],'reason':'Sales quotation workflow'},
   {'role':'HR Manager','gate':'is_view','decision':'remove_isolated','permissions':['is.master-customers.view','is.dashboard.view'],'reason':'Isolated non-HR references'},
   {'role':'HR Manager','gate':'crm_view','decision':'enable_access','permissions':['crm.events.view'],'reason':'Staff Calendar'}]
  with serve.connect() as c:
   salt,digest,it=serve.password_record('Existing-admin-password')
   c.execute('INSERT INTO accounts(id,email,name,role,user_id,password_hash,salt,iterations,created_at) VALUES(?,?,?,?,?,?,?,?,?)',('a1','admin@example.invalid','Admin','System Admin','u1',digest,salt,it,'now'))
   d=json.loads(c.execute('SELECT value FROM workspace WHERE key=?',(fix.KEY,)).fetchone()[0]);d['roles']['Sales Representative']=['is.quotation.view','is.quotation.create'];d['roles']['HR Manager']=['is.master-customers.view','is.dashboard.view','crm.events.view','hrprofiles'];d['roleRecordScopes']={'Sales Representative':{'is.quotation':'own'},'HR Manager':{'crm.events':'assigned'}}
   d['users'][1]['role']='Sales Representative';d['users'].append({'id':'u3','name':'HR','role':'HR Manager','managerId':'u1','department':'HR'});c.execute('UPDATE workspace SET value=? WHERE key=?',(json.dumps(d),fix.KEY))
   for i,role in [('2','Sales Representative'),('3','HR Manager')]:
    salt,digest,it=serve.password_record('Existing-password')
    c.execute('INSERT INTO accounts(id,email,name,role,user_id,password_hash,salt,iterations,created_at) VALUES(?,?,?,?,?,?,?,?,?)',('a'+i,'user'+i+'@example.invalid','User',role,'u'+i,digest,salt,it,'now'));c.execute('INSERT INTO sessions VALUES(?,?,?,?)',('s'+i,'a'+i,9999999999,1))
 def tearDown(self):self.fixture.tearDown()
 def data(self,c):return json.loads(c.execute('SELECT value FROM workspace WHERE key=?',(fix.KEY,)).fetchone()[0])
 def test_exact_deltas_preserve_profiles_scopes_credentials_and_documents(self):
  with serve.connect() as c:
   before=self.data(c);accounts=c.execute('SELECT * FROM accounts ORDER BY id').fetchall();other=c.execute('SELECT key,value,revision FROM workspace WHERE key<>? ORDER BY key',(fix.KEY,)).fetchall()
   r=fix.apply(c,self.plan);after=self.data(c)
   self.assertEqual((r['added'],r['removed']),(2,2));self.assertIn('is_view',after['roles']['Sales Representative']);self.assertEqual(set(after['roles']['HR Manager']),{'crm_view','crm.events.view','hrprofiles'})
   self.assertEqual({k:v for k,v in before.items() if k!='roles'},{k:v for k,v in after.items() if k!='roles'})
   self.assertEqual(accounts,c.execute('SELECT * FROM accounts ORDER BY id').fetchall());self.assertEqual(other,c.execute('SELECT key,value,revision FROM workspace WHERE key<>? ORDER BY key',(fix.KEY,)).fetchall());self.assertFalse(c.execute('SELECT * FROM sessions').fetchall())
 def test_second_run_preserves_later_admin_edit(self):
  with serve.connect() as c:
   fix.apply(c,self.plan);d=self.data(c);d['roles']['Sales Representative'].remove('is_view');c.execute('UPDATE workspace SET value=? WHERE key=?',(json.dumps(d),fix.KEY));self.assertFalse(fix.apply(c,self.plan)['applied']);self.assertNotIn('is_view',self.data(c)['roles']['Sales Representative'])
 def test_previously_enabled_hr_gate_preserves_intentional_grants(self):
  with serve.connect() as c:
   d=self.data(c);d['roles']['HR Manager'].append('is_view');c.execute('UPDATE workspace SET value=? WHERE key=?',(json.dumps(d),fix.KEY));fix.apply(c,self.plan);self.assertIn('is.master-customers.view',self.data(c)['roles']['HR Manager'])
 def test_removed_functions_do_not_cause_new_application_access(self):
  with serve.connect() as c:
   d=self.data(c);d['roles']['Sales Representative']=['dashboard'];c.execute('UPDATE workspace SET value=? WHERE key=?',(json.dumps(d),fix.KEY));fix.apply(c,self.plan);self.assertNotIn('is_view',self.data(c)['roles']['Sales Representative'])
 def test_missing_roles_are_not_recreated(self):
  with serve.connect() as c:
   d=self.data(c);del d['roles']['HR Manager'];c.execute('UPDATE workspace SET value=? WHERE key=?',(json.dumps(d),fix.KEY));fix.apply(c,self.plan);self.assertNotIn('HR Manager',self.data(c)['roles'])
 def test_audit_failure_rolls_back_grants_and_sessions(self):
  with serve.connect() as c:
   c.execute('CREATE TABLE access_resolution_audit(id INTEGER PRIMARY KEY,at TEXT,version TEXT,details TEXT)');c.execute("CREATE TRIGGER fail_resolution BEFORE INSERT ON access_resolution_audit BEGIN SELECT RAISE(ABORT,'test late failure');END")
   before=self.data(c);sessions=c.execute('SELECT * FROM sessions ORDER BY token_hash').fetchall()
   with self.assertRaises(sqlite3.IntegrityError):fix.apply(c,self.plan)
   self.assertEqual(before,self.data(c));self.assertEqual(sessions,c.execute('SELECT * FROM sessions ORDER BY token_hash').fetchall());self.assertFalse(c.execute('SELECT 1 FROM data_migrations WHERE name=?',(fix.VERSION,)).fetchone())
 def test_startup_backup_once_and_restart(self):
  with serve.connect() as c:
   for name in ['company-staff-roster-69','company-access-workbook-20261031-v1']:c.execute('INSERT OR IGNORE INTO data_migrations VALUES(?)',(name,))
  with patch.object(fix,'PLAN',self.plan):
   serve.prepare_database();serve.prepare_database()
  self.assertEqual(len(list((serve.DB.parent/'private-archives').glob('*.zip'))),1)
 def test_unknown_permission_fails_before_write(self):
  p=copy.deepcopy(self.plan);p[0]['permissions']=['is.unknown.view']
  with serve.connect() as c:
   before=self.data(c)
   with self.assertRaises(ValueError):fix.apply(c,p)
   self.assertEqual(before,self.data(c))
