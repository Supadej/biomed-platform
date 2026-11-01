import unittest,tempfile,sqlite3,json,io,sys,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import serve,budget_governance as bg,financial_references as refs,permissions_policy as policy,finance_workspace as fw
class Finance79(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.prior=serve.DB;serve.DB=Path(self.temp.name)/'test.sqlite3'
  with sqlite3.connect(ROOT/'data'/'biomed.sqlite3') as a,sqlite3.connect(serve.DB) as b:a.backup(b)
  serve.prepare_database()
  with serve.connect() as c:self.actor=c.execute("select id,email,name,role,user_id from accounts where role='System Admin'").fetchone()
  self.perms={p['key'] for p in policy.CATALOG['permissions']};self.reviewer=('review','r@invalid.test','Reviewer','System Admin','reviewer')
 def tearDown(self):serve.DB=self.prior;self.temp.cleanup()
 def call(self,module,body=None,actor=None,perms=None):
  class H:
   path='/api/budget-governance?year=2027'
   def reply(self,s,d):return s,d
  h=H();raw=json.dumps(body or {}).encode();h.headers={'Content-Length':str(len(raw))};h.rfile=io.BytesIO(raw)
  return module.handle(h,'POST' if body else 'GET',serve.connect,lambda h:actor or self.actor,lambda a:self.perms if perms is None else perms,lambda h:True)
 def post(self,action,actor=None,**kw):
  _,data=self.call(bg);return self.call(bg,{'action':action,'version':data['version'],'workspaceRevision':data['workspaceRevision'],**kw},actor)
 def approve(self,id=None):
  for _ in range(3):
   status,data=self.post('approve',actor=self.reviewer,id=id);self.assertEqual(status,200,data)
 def test_reference_validation_metadata_reject_months_and_preservation(self):
  _,r=self.call(refs)
  self.assertEqual(self.call(refs,{'version':r['version'],'collection':'costCenters','name':'Management'})[0],200)
  _,r=self.call(refs);self.assertEqual(self.call(refs,{'version':r['version'],'collection':'sources','name':'Freight','group':refs.GROUPS[2]})[0],200)
  line={'kind':'Expense','source':'Freight','costCenter':'Management','owner':self.actor[4],'revenueType':'Other','target':[100]*12,'comment':'Freight supporting estimate','attachments':[{'name':'estimate.pdf','data':'data:application/pdf;base64,JVBERi0xLjQ='}]}
  self.assertEqual(self.post('submit',lines=[line])[0],200)
  self.assertEqual(self.post('reject',actor=self.reviewer,reason='Revise forecast')[0],200)
  self.assertEqual(self.post('submit',lines=[line])[0],200);self.approve()
  _,g=self.call(bg);self.assertEqual(g['governance']['submissionArchive'][0]['status'],'Rejected');self.assertEqual(g['governance']['approved']['lines'][0]['comment'],line['comment']);self.assertFalse(any(m['approved'] for m in g['effectiveMonthly']))
  status,g=self.post('submit-month',month=0);self.approve(g['governance']['monthlyBudgets'][-1]['id'])
  with serve.connect() as c:
   f,_=fw.load(c,2027);report=fw.report(c,2027,f);self.assertEqual(report['commitments'][0]['target'],100);self.assertEqual(c.execute('select count(*) from accounts').fetchone()[0],44)
  line['costCenter']='Typo';self.assertEqual(self.post('save',lines=[line])[0],400)
 def test_reporting_manager_enforcement(self):
  with serve.connect() as c:
   portal=json.loads(c.execute("select value from workspace where key='biomed_portal_v33_clean'").fetchone()[0]);u=next(x for x in portal['users'] if x.get('managerId'));manager=next(x for x in portal['users'] if x['id']==u['managerId'])
   record={'status':'Submitted','submittedBy':u['id'],'lines':[{'owner':u['id']}],'history':[]}
   with self.assertRaises(policy.PermissionDenied):bg.decide(copy.deepcopy(record),{'action':'approve'},('bad','','Bad','Department Manager','not-manager'),self.perms,c)
   actor=('manager',manager['email'],manager['name'],manager['role'],manager['id']);bg.decide(record,{'action':'approve'},actor,self.perms,c);self.assertEqual(record['status'],'Department Approved')
if __name__=='__main__':unittest.main()
