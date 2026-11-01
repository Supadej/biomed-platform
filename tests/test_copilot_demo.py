import unittest,sqlite3,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import copilot_access as access,copilot_functions as functions,seed_ai_demo
class Demo(unittest.TestCase):
 def setUp(self):
  self.c=sqlite3.connect(':memory:');self.c.executescript('CREATE TABLE workspace(key TEXT PRIMARY KEY,value TEXT,revision INTEGER); CREATE TABLE accounts(user_id TEXT,email TEXT,disabled INTEGER); INSERT INTO accounts VALUES("u1","a@test",0);')
  self.actor=('a','a@test','A','Employee','u1');access.init(self.c)
 def test_seed_twice_and_keep_existing(self):
  from unittest.mock import patch
  with patch('serve.project'):
   seed_ai_demo.add(self.c,'a@test')
   before=self.c.execute('SELECT key,value FROM workspace ORDER BY key').fetchall()
   seed_ai_demo.add(self.c,'a@test')
   self.assertEqual(before,self.c.execute('SELECT key,value FROM workspace ORDER BY key').fetchall())
  for key,value in before:self.assertIn('AI-DEMO-',value)
 def test_private_and_disabled_functions(self):
  d={'tasks':[{'owner':'u1','title':'Own task'},{'owner':'u2','title':'Other secret'}],'announcements':[{'title':'Public notice'},{'title':'Restricted notice','sharedWith':['u2']}],'hrprofiles':[{'owner':'u1','salary':90000,'address':'Private address'}]}
  self.c.execute('INSERT INTO workspace VALUES(?,?,1)',('biomed_portal_v33_clean',json.dumps(d)))
  perms={'tasks','announcements','hrprofiles'};mask={'portal.tasks':True,'portal.announcements':True,'portal.hrprofiles':True}
  text=json.dumps(access.snapshot(self.c,self.actor,perms,'portal',mask))
  self.assertIn('Own task',text);self.assertIn('Public notice',text)
  for secret in ('Other secret','Restricted notice','90000','Private address'):self.assertNotIn(secret,text)
  mask['portal.tasks']=False
  self.assertNotIn('Own task',json.dumps(access.snapshot(self.c,self.actor,perms,'portal',mask)))
 def test_all_catalogue_controls_available_but_role_still_required(self):
  self.assertTrue(all(r['connected'] for r in functions.catalog()))
  effective=access.state(self.c,self.actor,{'ai.internal.use','announcements'},False)['effective']
  self.assertTrue(effective['functions']['portal.announcements']);self.assertFalse(effective['functions']['portal.hrprofiles'])
if __name__=='__main__':unittest.main()
