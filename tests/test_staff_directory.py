import sys,json,unittest,hashlib,time,datetime
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import test_crm as fixtures
import serve,staff_directory as staff,permissions_policy as policy
class StaffDirectory(unittest.TestCase):
 def setUp(self):
  fixtures.CRM.setUp(self)
  with serve.connect() as c:
   data,rev=staff.workspace(c);data['departments']=['Management','Sales'];data['users'][0].update(department='Management');data['users'][1].update(department='Sales');staff.persist(c,data,rev)
   for uid,name,mail,role in [('u1','Admin One','one@example.invalid','System Admin'),('u2','Second Person','two@example.invalid','Employee')]:
    salt,digest,it=serve.password_record('Initial-password-123');c.execute('INSERT INTO accounts(id,email,name,role,user_id,password_hash,salt,iterations,created_at) VALUES(?,?,?,?,?,?,?,?,?)',(uid,mail,name,role,uid,digest,salt,it,'2026-10-29'))
   c.execute('INSERT INTO sessions VALUES(?,?,?,?)',('session','u2',int(time.time())+1000,int(time.time())))
 tearDown=fixtures.CRM.tearDown
 def user(self,c,uid):return next(u for u in staff.listing(c) if u['id']==uid)
 def call(self,c,**raw):return staff.dispatch(c,self.actor,self.perms,raw)
 def creation(self,**extra):return dict(action='create',name='New User',email='new@example.invalid',department='Sales',role='Employee',managerId='u1',password='Long-password-123',confirmPassword='Long-password-123',**extra)
 def test_create_confirm_atomic_and_no_secrets(self):
  with serve.connect() as c:
   with self.assertRaises(ValueError):staff.dispatch(c,self.actor,self.perms,{**self.creation(),'confirmPassword':'Wrong'})
   self.assertEqual(c.execute('SELECT COUNT(*) FROM accounts').fetchone()[0],2)
   result=staff.dispatch(c,self.actor,self.perms,self.creation());user=self.user(c,result['id']);self.assertEqual(user['managerId'],'u1');self.assertTrue(user['hasAccount']);self.assertNotIn('password',json.dumps(user));self.assertEqual(c.execute('SELECT COUNT(*) FROM accounts').fetchone()[0],3)
 def test_edit_updates_login_and_workspace(self):
  with serve.connect() as c:
   u=self.user(c,'u2');self.call(c,action='edit',id='u2',version=u['version'],name='Updated',email='updated@example.invalid',department='Management',role='Employee',managerId='u1')
   self.assertEqual(self.user(c,'u2')['name'],'Updated');self.assertEqual(c.execute("SELECT email FROM accounts WHERE user_id='u2'").fetchone()[0],'updated@example.invalid');self.assertFalse(c.execute("SELECT 1 FROM sessions WHERE account_id='u2'").fetchone())
   with self.assertRaises(staff.Conflict):self.call(c,action='edit',id='u2',version=0)
 def test_cycles_and_last_admin(self):
  with serve.connect() as c:
   u=self.user(c,'u2');self.call(c,action='edit',id='u2',version=0,name=u['name'],email=u['email'],department='Sales',role='Employee',managerId='u1')
   u=self.user(c,'u1')
   for changes in [dict(managerId='u2',role='System Admin'),dict(managerId='',role='Employee')]:
    with self.assertRaises(ValueError):self.call(c,action='edit',id='u1',version=u['version'],name=u['name'],email=u['email'],department='Management',**changes)
 def test_deactivate_revokes_and_library_active_only(self):
  with serve.connect() as c:
   self.call(c,action='active',id='u2',version=0,active=False)
   self.assertEqual(c.execute("SELECT disabled FROM accounts WHERE user_id='u2'").fetchone()[0],1);self.assertFalse(c.execute("SELECT 1 FROM sessions WHERE account_id='u2'").fetchone());lib=staff.dispatch(c,self.actor,self.perms,view='library');self.assertEqual([u['id'] for u in lib['users']],['u1']);self.assertEqual(set(lib['users'][0]),set(staff.BASIC))
   with self.assertRaises(ValueError):self.call(c,action='active',id='u1',version=0,active=False)
 def test_deactivate_manager_requires_reassignment(self):
  with serve.connect() as c:
   data,rev=staff.workspace(c);data['users'][0]['managerId']='u2';staff.persist(c,data,rev)
   with self.assertRaises(ValueError):self.call(c,action='active',id='u2',version=0,active=False)
 def test_reset_and_self_password(self):
  with serve.connect() as c:
   with self.assertRaises(ValueError):self.call(c,action='password',id='u1',version=0,currentPassword='wrong',password='New-password-123',confirmPassword='New-password-123')
   self.call(c,action='reset_password',id='u2',version=0,password='New-password-123',confirmPassword='New-password-123');account=next(a for a in staff.accounts(c) if a['user_id']=='u2');staff.check_password(account,'New-password-123');self.assertFalse(c.execute("SELECT 1 FROM sessions WHERE account_id='u2'").fetchone())
 def test_profile_boundaries_email_and_validation(self):
  with serve.connect() as c:
   raw=dict(action='profile',id='u1',version=0,email='one@example.invalid',mobile='0812345678',dob='1989-01-02',lineId='biomed',photo='')
   staff.dispatch(c,self.actor,self.perms,raw);self.assertEqual(self.user(c,'u1')['lineId'],'biomed');self.assertEqual(staff.dispatch(c,self.actor,self.perms,view='library')['users'][0]['mobile'],'0812345678')
   for values,error in [({'id':'u2'},policy.PermissionDenied),({'email':'new@example.invalid'},ValueError),({'dob':'2999-01-01'},ValueError),({'photo':'data:image/svg+xml;base64,abc'},ValueError)]:
    with self.assertRaises(error):staff.dispatch(c,self.actor,self.perms,{**raw,'version':self.user(c,values.get('id','u1'))['version'],**values})
   staff.dispatch(c,self.actor,self.perms,{**raw,'version':1,'email':'new@example.invalid','currentPassword':'Initial-password-123'});self.assertEqual(c.execute("SELECT email FROM accounts WHERE user_id='u1'").fetchone()[0],'new@example.invalid')
 def test_permissions_and_departments(self):
  with serve.connect() as c:
   for action in ['view','create','edit','deactivate','reset_password','manage_departments']:
    limited=self.perms-{'portal.users.'+action}
    with self.assertRaises(policy.PermissionDenied):
     if action=='view':staff.dispatch(c,self.actor,limited)
     else:staff.dispatch(c,self.actor,limited, self.creation() if action=='create' else dict(action={'deactivate':'active','manage_departments':'department'}.get(action,action),id='u2',version=0,active=False,operation='add',name='IT'))
   with self.assertRaises(ValueError):self.call(c,action='department',operation='remove',name='Sales')
   self.call(c,action='department',operation='add',name='IT');self.assertIn('IT',staff.workspace(c)[0]['departments'])
   self.call(c,action='department',operation='remove',name='IT');self.assertNotIn('IT',staff.workspace(c)[0]['departments'])
 def test_legacy_workspace_identity_bypass(self):
  with serve.connect() as c:
   old,_=staff.workspace(c);new=json.loads(json.dumps(old));new['users'][1]['role']='System Admin'
   with self.assertRaises(policy.PermissionDenied):staff.guard_workspace(c,old,new)
 def test_http_auth_creation_and_deactivation(self):
  import threading,urllib.request,urllib.error
  http=serve.ThreadingHTTPServer(('127.0.0.1',0),serve.Handler);threading.Thread(target=http.serve_forever,daemon=True).start();base='http://127.0.0.1:'+str(http.server_port)
  with serve.connect() as c:
   for token,ident in [('admin-token','u1'),('employee-token','u2')]:c.execute('INSERT INTO sessions VALUES(?,?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),ident,int(time.time())+1000,int(time.time())))
  def call(path,raw=None,token='admin-token',origin=None):
   headers={'Content-Type':'application/json'}
   if token:headers['Cookie']='biomed_session='+token
   if origin:headers['Origin']=origin
   try:
    with urllib.request.urlopen(urllib.request.Request(base+path,data=json.dumps(raw).encode() if raw is not None else None,headers=headers)) as r:return r.status,json.load(r)
   except urllib.error.HTTPError as e:return e.code,json.load(e)
  try:
   self.assertEqual(call('/api/staff-directory',token=None)[0],401)
   self.assertEqual(call('/api/staff-directory',{'action':'department','operation':'add','name':'IT'},origin='https://bad.invalid')[0],403)
   self.assertEqual(call('/api/auth/create',{**self.creation(),'confirmPassword':'mismatch'})[0],400)
   status,result=call('/api/auth/create',self.creation());self.assertEqual(status,201);self.assertIn('id',result)
   with serve.connect() as c:self.assertEqual(self.user(c,result['id'])['department'],'Sales')
   status,result=call('/api/staff-directory',{'action':'active','id':'u2','version':0,'active':False});self.assertEqual(status,200)
   self.assertEqual(call('/api/auth/me',token='employee-token')[0],401)
   self.assertEqual(call('/api/auth/login',{'email':'two@example.invalid','password':'Initial-password-123'},token=None)[0],401)
  finally:http.shutdown();http.server_close()
 def test_profile_role_migration_and_preserved_revocation(self):
  data={'roles':{'Employee':[], 'Custom':['tasks']},'permissionCatalogVersion':22}
  policy.migrate_portal(data)
  for role,grants in data['roles'].items():
   self.assertIn('user_profile',grants);self.assertIn('user_library',grants)
   if role in ['Employee','Custom']:self.assertNotIn('portal.users.reset_password',grants)
  data['roles']['Employee'].remove('portal.user_library.view');policy.migrate_portal(data);self.assertNotIn('portal.user_library.view',data['roles']['Employee'])
 def test_backup_and_reset_keep_staff_profiles(self):
  import database_admin
  with serve.connect() as c:
   self.call(c,action='profile',id='u1',version=0,email='one@example.invalid',mobile='0812345678',dob='1989-01-02',lineId='biomed',photo='')
   snapshot=database_admin.snapshot(c);self.assertIn('staff_profiles',snapshot['tables']);database_admin.reset(c)
   self.assertEqual(self.user(c,'u1')['mobile'],'0812345678');self.assertTrue(self.user(c,'u1')['hasAccount'])
if __name__=='__main__':unittest.main()
