import unittest,json,time
import test_crm,serve,staff_directory,role_admin,permissions_policy as policy
class RoleAdmin(unittest.TestCase):
 def setUp(self):
  self.fixture=test_crm.CRM();self.fixture.setUp();self.actor=self.fixture.actor;self.perms=self.fixture.perms
  with serve.connect() as c:
   d,r=staff_directory.workspace(c);d['roles']['Custom Manager']=['dashboard','roles','portal.roles.edit'];d['roleDescriptions']={'Custom Manager':'Review assigned work'};d['users'][1]['role']='Custom Manager';staff_directory.persist(c,d,r)
   salt,digest,it=serve.password_record('Initial-password-72')
   c.execute('INSERT INTO accounts VALUES(?,?,?,?,?,?,?,?,0,0,0,?)',('a2','two@example.invalid','Second Person','Custom Manager','u2',digest,salt,it,'2026-10-30'))
   c.execute('INSERT INTO sessions VALUES(?,?,?,?)',('session','a2',int(time.time())+1000,int(time.time())))
 def tearDown(self):self.fixture.tearDown()
 def call(self,c,**raw):return role_admin.dispatch(c,self.actor,self.perms,{'revision':staff_directory.workspace(c)[1],**raw})
 def test_rename_updates_profiles_accounts_description_and_keeps_grants_history(self):
  with serve.connect() as c:
   old,_=staff_directory.workspace(c);out=self.call(c,action='rename',role='Custom Manager',name="Regional Manager's Team")
   d,_=staff_directory.workspace(c);new=out['role'];self.assertNotIn('Custom Manager',d['roles']);self.assertEqual(d['roles'][new],old['roles']['Custom Manager']);self.assertEqual(d['roleDescriptions'][new],'Review assigned work');self.assertEqual(d['users'][1]['role'],new);self.assertEqual(c.execute("SELECT role FROM accounts WHERE id='a2'").fetchone()[0],new);self.assertEqual(d['pipeline'],old['pipeline']);self.assertTrue(c.execute('SELECT 1 FROM sessions').fetchone());self.assertEqual(c.execute('SELECT action FROM role_admin_audit').fetchone()[0],'rename')
 def test_delete_assigned_requires_explicit_replacement_and_assignment_grant(self):
  with serve.connect() as c:
   with self.assertRaises(role_admin.Conflict):self.call(c,action='delete',role='Custom Manager')
   before=staff_directory.workspace(c)
   with self.assertRaises(policy.PermissionDenied):role_admin.dispatch(c,self.actor,self.perms-{'portal.users.assign'},{'revision':before[1],'action':'delete','role':'Custom Manager','replacement':'Employee'})
   self.assertEqual(staff_directory.workspace(c),before)
   result=self.call(c,action='delete',role='Custom Manager',replacement='Employee');d,_=staff_directory.workspace(c);self.assertEqual(result['affectedUsers'],1);self.assertNotIn('Custom Manager',d['roles']);self.assertNotIn('Custom Manager',d['roleDescriptions']);self.assertEqual(d['users'][1]['role'],'Employee');self.assertFalse(c.execute('SELECT 1 FROM sessions').fetchone())
 def test_unused_delete(self):
  with serve.connect() as c:
   d,r=staff_directory.workspace(c);d['roles']['Unused']=[];staff_directory.persist(c,d,r);out=self.call(c,action='delete',role='Unused');self.assertEqual(out['affectedUsers'],0)
 def test_protected_duplicate_reserved_and_stale(self):
  with serve.connect() as c:
   for role in ['System Admin','Employee']:
    for action in ['rename','delete']:
     with self.assertRaises(ValueError):self.call(c,action=action,role=role,name='Changed')
   for target in ['employee','SYSTEM_ADMIN','__proto__','', 'a'*121,'Bad\nRole']:
    with self.assertRaises(ValueError):self.call(c,action='rename',role='Custom Manager',name=target)
   with self.assertRaises(role_admin.Conflict):self.call(c,action='rename',role='Custom Manager',name='New',revision=0)
 def test_editor_permission_and_no_generic_workspace_bypass(self):
  with serve.connect() as c:
   with self.assertRaises(policy.PermissionDenied):role_admin.dispatch(c,self.actor,{'roles'})
   old,_=staff_directory.workspace(c);new=json.loads(json.dumps(old));del new['roles']['Custom Manager']
   with self.assertRaises(policy.PermissionDenied):staff_directory.guard_workspace(c,old,new)
 def test_self_reassignment_requests_signin(self):
  with serve.connect() as c:
   actor=('a2','','','Custom Manager','u2');out=role_admin.dispatch(c,actor,self.perms,{'revision':staff_directory.workspace(c)[1],'action':'delete','role':'Custom Manager','replacement':'Employee'});self.assertTrue(out['signInAgain'])
