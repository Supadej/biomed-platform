import unittest,json,base64,hashlib,copy
from pathlib import Path
from unittest.mock import patch
import test_crm
import serve,company_staff_import as roster,company_role_defaults as roles

class StaffRosterTests(unittest.TestCase):
 def setUp(self):
  self.fixture=test_crm.CRM();self.fixture.setUp()
  with serve.connect() as c:
   for ident,mail,uid in [('a1','one@example.invalid','u1'),('a2','two@example.invalid','u2')]:
    salt,digest,it=serve.password_record('Original-password-69')
    c.execute('INSERT INTO accounts VALUES(?,?,?,?,?,?,?,?,0,0,0,?)',(ident,mail,uid,'System Admin' if uid=='u1' else 'Employee',uid,digest,salt,it,'2026-10-30'))
    c.execute('INSERT INTO sessions VALUES(?,?,?,?)',('session-'+uid,ident,9999999999,1))
 def tearDown(self):self.fixture.tearDown()
 def entry(self,email='one@example.invalid',role='Sales Supervisor',name='ชื่อ ผู้ใช้'):
  salt,digest,it=serve.password_record('New-password-69')
  return dict(name=name,email=email,role=role,department='Diagnostics',salt=base64.b64encode(salt).decode(),passwordHash=base64.b64encode(digest).decode(),iterations=it)
 def test_mapping_stable_ids_history_sessions_and_one_time(self):
  with serve.connect() as c:
   before=json.loads(c.execute('SELECT value FROM workspace WHERE key=?',(roster.KEY,)).fetchone()[0]);other=c.execute("SELECT * FROM accounts WHERE id='a2'").fetchone()
   result=roster.apply(c,{'users':[self.entry(),self.entry('new@example.invalid','Application Specialist')]})
   self.assertEqual((result['updated'],result['created']),(1,1))
   data=json.loads(c.execute('SELECT value FROM workspace WHERE key=?',(roster.KEY,)).fetchone()[0]);u=next(u for u in data['users'] if u['id']=='u1')
   self.assertEqual(u['name'],'ชื่อ ผู้ใช้');self.assertEqual(u['department'],'Diagnostics');self.assertEqual(data['pipeline'],before['pipeline']);self.assertEqual(data['visits'],before['visits'])
   self.assertEqual(c.execute("SELECT * FROM accounts WHERE id='a2'").fetchone(),other)
   self.assertFalse(c.execute("SELECT 1 FROM sessions WHERE account_id='a1'").fetchone());self.assertTrue(c.execute("SELECT 1 FROM sessions WHERE account_id='a2'").fetchone())
   self.assertEqual(data['roles']['Sales Supervisor'],roles.grants('Sales Manager'))
   self.assertTrue(data['roleDescriptions']['Sales Supervisor'])
   self.assertFalse(roster.apply(c,{'users':[self.entry(name='Should not overwrite') ]})['applied'])
   self.assertEqual(c.execute("SELECT name FROM accounts WHERE id='a1'").fetchone()[0],'ชื่อ ผู้ใช้')
 def test_late_error_rolls_back_whole_roster(self):
  with serve.connect() as c:
   original=c.execute('SELECT value FROM workspace WHERE key=?',(roster.KEY,)).fetchone()[0];a=c.execute("SELECT * FROM accounts WHERE id='a1'").fetchone();bad=self.entry('bad@example.invalid');bad['salt']=''
   with self.assertRaises(ValueError):roster.apply(c,{'users':[self.entry(),bad]})
   self.assertEqual(c.execute("SELECT * FROM accounts WHERE id='a1'").fetchone(),a);self.assertEqual(c.execute('SELECT value FROM workspace WHERE key=?',(roster.KEY,)).fetchone()[0],original)
   self.assertFalse(c.execute('SELECT 1 FROM data_migrations WHERE name=?',(roster.VERSION,)).fetchone())
 def test_duplicate_emails_fail_without_changes(self):
  with serve.connect() as c:
   with self.assertRaises(ValueError):roster.apply(c,{'users':[self.entry(),self.entry()]})
 def test_startup_backup_and_restart_preserve_later_edits(self):
  payload=Path(self.fixture.temp.name)/'roster.json';payload.write_text(json.dumps({'users':[self.entry('two@example.invalid')]}))
  with patch.object(roster,'PAYLOAD',payload):
   serve.prepare_database()
   archives=list((serve.DB.parent/'private-archives').glob('*.zip'));self.assertEqual(len(archives),1)
   with serve.connect() as c:
    c.execute("UPDATE accounts SET name='Later profile edit' WHERE id='a2'")
    data=json.loads(c.execute('SELECT value FROM workspace WHERE key=?',(roster.KEY,)).fetchone()[0]);data['roleDescriptions']['Sales Supervisor']='Later responsibility edit';c.execute('UPDATE workspace SET value=? WHERE key=?',(json.dumps(data),roster.KEY))
   serve.prepare_database()
   with serve.connect() as c:
    self.assertEqual(c.execute("SELECT name FROM accounts WHERE id='a2'").fetchone()[0],'Later profile edit')
    data=json.loads(c.execute('SELECT value FROM workspace WHERE key=?',(roster.KEY,)).fetchone()[0]);self.assertEqual(data['roleDescriptions']['Sales Supervisor'],'Later responsibility edit')
   self.assertEqual(len(list((serve.DB.parent/'private-archives').glob('*.zip'))),1)
 def test_supervisor_manager_parity_and_functional_boundaries(self):
  for supervisor,manager in [('Sales Supervisor','Sales Manager'),('Service Engineer Supervisor','Service Manager'),('Procurement & Regulatory Supervisor','Procurement & Regulatory Manager'),('Messenger & Delivery Supervisor','Delivery Manager')]:self.assertEqual(roles.grants(supervisor),roles.grants(manager))
  for role in ['Service Engineer','Service Engineer Supervisor','Application Specialist','Application Specialist Manager','Inventory Officer','Purchasing Officer','Marketing Communication Specialist']:
   g=set(roles.grants(role));self.assertNotIn('budget_view',g);self.assertNotIn('roles',g);self.assertFalse(any(p.startswith('system.database.') for p in g))
  self.assertIn('budget.finance.review',roles.grants('Accounting Manager'));self.assertNotIn('budget.finance.review',roles.grants('Accounting'))
  self.assertIn('application_service.perform',roles.grants('Application Specialist'));self.assertNotIn('application_service.perform',roles.grants('Managing Director'))
  for role in ['System Admin','Sales Supervisor','Accounting Manager','Service Engineer Supervisor']:self.assertTrue(set(roles.grants(role))<=roles.VALID)
