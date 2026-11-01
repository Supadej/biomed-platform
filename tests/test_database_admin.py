import sys,json,io,base64,unittest,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import test_crm as fixture
import serve,database_admin as db,permissions_policy as policy,budget_governance as bg
class DatabaseAdmin(unittest.TestCase):
 setUp=fixture.CRM.setUp
 tearDown=fixture.CRM.tearDown
 def call(self,body=None,actor=None,perms=None,origin=True):
  class H:
   def reply(self,s,d):return s,d
  h=H();h.rfile=io.BytesIO(json.dumps(body).encode());h.headers={'Content-Length':str(len(h.rfile.getvalue()))}
  return db.handle(h,'POST' if body else 'GET',serve.connect,lambda h:actor or self.actor,lambda a:self.perms if perms is None else perms,lambda h:origin,serve.DB)
 def admin(self):
  with serve.connect() as c:c.execute("insert into accounts values('admin','admin@example.invalid','Admin','System Admin','u1',X'00',X'00',1,0,0,0,'2026-01-01')")
 def backup(self):
  s,d=self.call({'action':'backup'});self.assertEqual(s,200,d);return d
 def test_backup_preview_reset_restore_roundtrip(self):
  self.admin()
  with serve.connect() as c:c.execute("insert into calendar_files values('a','event1','Thai เอกสาร.pdf',?)",(b'\x00\xffPDF',))
  b=self.backup();s,p=self.call({'action':'inspect','file':b['file']});self.assertEqual(s,200,p)
  self.assertIn('calendar_files',p['tables'])
  s,d=self.call({'action':'reset','confirm':'ARCHIVE AND RESET','reason':'QA full reset'});self.assertEqual(s,200,d)
  with serve.connect() as c:
   self.assertEqual(c.execute('select count(*) from calendar_files').fetchone()[0],0)
   self.assertEqual(c.execute('select count(*) from accounts').fetchone()[0],1)
  s,p=self.call({'action':'inspect','file':b['file']});self.assertEqual(s,200,p)
  s,d=self.call({'action':'restore','token':p['token'],'confirm':'RESTORE ALL DATA','reason':'QA restore'});self.assertEqual(s,200,d)
  with serve.connect() as c:
   self.assertEqual(c.execute('select content from calendar_files').fetchone()[0],b'\x00\xffPDF')
   self.assertFalse(c.execute('pragma foreign_key_check').fetchall())
  self.assertTrue((serve.DB.parent/'private-archives'/d['recoveryArchive']).exists())
 def test_permissions_origin_corruption_and_stale_preview(self):
  self.assertEqual(self.call(perms=set())[0],403)
  self.assertEqual(self.call({'action':'backup'},origin=False)[0],403)
  self.admin();b=self.backup()
  self.assertEqual(self.call({'action':'inspect','file':base64.b64encode(b'invalid').decode()})[0],400)
  s,p=self.call({'action':'inspect','file':b['file']});self.assertEqual(s,200,p)
  with serve.connect() as c:c.execute("insert into calendar_files values('x','1','x',X'01')")
  s,d=self.call({'action':'restore','token':p['token'],'confirm':'RESTORE ALL DATA','reason':'QA stale'});self.assertEqual(s,400);self.assertIn('changed',d['error'])
  with serve.connect() as c:self.assertEqual(c.execute('select count(*) from calendar_files').fetchone()[0],1)
  self.assertEqual(self.call({'action':'reset','confirm':'wrong','reason':'QA test'})[0],400)
 def test_admin_only_self_approval_mode_and_audit(self):
  r={'status':'Submitted','submittedBy':'u1','history':[]}
  with serve.connect() as c:
   with self.assertRaises(policy.PermissionDenied):bg.decide(r,{'action':'approve'},self.actor,self.perms,c)
  self.assertEqual(self.call({'action':'testing','enabled':True},actor=('a','','Accountant','Accounting','u1'))[0],403)
  self.assertEqual(self.call({'action':'testing','enabled':True})[0],200)
  with serve.connect() as c:
   bg.decide(r,{'action':'approve'},self.actor,self.perms,c)
   self.assertEqual(r['status'],'Department Approved')
   self.assertEqual(c.execute("select count(*) from system_admin_audit where action='TEST self-approval'").fetchone()[0],1)
   r['status']='Submitted'
   with self.assertRaises(policy.PermissionDenied):bg.decide(r,{'action':'approve'},('a','','Accountant','Accounting','u1'),self.perms,c)
  self.assertEqual(self.call({'action':'testing','enabled':False})[0],200)
 def test_schema_tamper_and_fk_failure_roll_back(self):
  self.admin()
  with serve.connect() as c:original=db.snapshot(c)
  modified=copy.deepcopy(original);modified['tables']['accounts']['columns'][0]='evil'
  self.assertEqual(self.call({'action':'inspect','file':base64.b64encode(db.pack(modified)).decode()})[0],400)
  modified=copy.deepcopy(original);modified['tables']['document_lines']['rows'].append(['missing',1,'p','{}'])
  self.assertEqual(self.call({'action':'inspect','file':base64.b64encode(db.pack(modified)).decode()})[0],400)
  with serve.connect() as c:self.assertEqual(c.execute('select count(*) from document_lines').fetchone()[0],len(original['tables']['document_lines']['rows']))
if __name__=='__main__':unittest.main()

class TestModeWorkflows(unittest.TestCase):
 def enable(self):
  with serve.connect() as c:c.execute("insert or replace into system_controls values('adminSelfApprovalTesting','true')")
 def test_own_stock_request_return_and_count(self):
  import test_service_inventory as si_test
  import service_inventory as si
  case=si_test.Inventory();case.setUp()
  try:
   self.enable();actor=(*case.engineer[:3],'System Admin',case.engineer[4])
   with serve.connect() as c:
    request=case.request(c,5);case.call(c,{'action':'approve','id':request['id'],'version':request['version']},actor);self.assertEqual(case.qty(c),5)
    returned=case.request(c,1,'Return');case.call(c,{'action':'approve','id':returned['id'],'version':returned['version']},actor);self.assertEqual(case.qty(c),4)
    count=case.call(c,{'action':'stock-check','consolidated':True,'lines':[{'productId':'p1','lot':'LOT','expiry':'2027-12-31','book':4,'counted':3,'reason':'QA physical count'}]},actor)
    case.call(c,{'action':'stock-check-approve','id':count['id'],'version':1},actor);self.assertEqual(case.qty(c),3)
    self.assertEqual(c.execute("select count(*) from system_admin_audit where action='TEST self-approval'").fetchone()[0],3)
  finally:case.tearDown()
 def test_own_budget_stages_and_monthly_performance(self):
  import test_budget_governance as bg_test
  case=bg_test.Governance();case.setUp()
  try:
   self.enable();case.plan()
   for _ in range(3):self.assertEqual(case.post('approve')[0],200)
   s,d=case.post('review',period='Monthly',index=0,verified=True);self.assertEqual(s,200,d)
   ident=d['governance']['reviews'][-1]['id']
   for _ in range(3):self.assertEqual(case.post('approve',id=ident)[0],200)
  finally:case.tearDown()
 def test_own_express_and_close_review(self):
  import test_express_import as ex_test
  case=ex_test.Express();case.setUp()
  try:
   self.enable();s,d=case.stage('Chart of accounts','account,name,category\nCASH,Main cash,Asset\n');self.assertEqual(s,200,d)
   b=d['batches'][0];s,d=case.call({'action':'approve','id':b['id'],'version':b['version']});self.assertEqual(s,200,d)
  finally:case.tearDown()
  import test_finance_workspace as fw_test
  import finance_workspace as fw
  case=fw_test.Finance();case.setUp()
  try:
   self.enable()
   with serve.connect() as c:c.execute("insert or ignore into accounts(id,email,name,role,user_id,password_hash,salt,iterations,created_at) values('test-fin','finance@example.invalid','Finance','Accounting','u1',X'00',X'00',1,'2026-01-01')")
   tasks=[{'owner':'u1','done':True,'evidence':'QA verified reconciliation'} for _ in fw.TASKS]
   self.assertEqual(case.post('close-save',month=0,tasks=tasks)[0],200)
   self.assertEqual(case.post('close-submit',month=0)[0],200)
   s,d=case.post('close-review',month=0,approve=True);self.assertEqual(s,200,d)
  finally:case.tearDown()
