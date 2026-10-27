import unittest,tempfile,sqlite3,shutil,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import seed_ai_demo,seed_testing_data as demo,serve
class Expanded(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'app.db';shutil.copy2(Path(__file__).resolve().parents[1]/'data/biomed.sqlite3',self.path)
  self.c=sqlite3.connect(self.path)
 def tearDown(self):self.c.close();self.tmp.cleanup()
 def load(self,key):return json.loads(self.c.execute('SELECT value FROM workspace WHERE key=?',(key,)).fetchone()[0])
 def test_repeat_import_preserves_existing_rows_and_account_credentials(self):
  before=self.c.execute('SELECT * FROM accounts').fetchall();seed_ai_demo.add(self.c,'testadmin@example.invalid')
  workspace=self.c.execute('SELECT key,value FROM workspace ORDER BY key').fetchall();crm=self.c.execute('SELECT entity,id,payload FROM crm_records ORDER BY entity,id').fetchall()
  seed_ai_demo.add(self.c,'testadmin@example.invalid')
  self.assertEqual(workspace,self.c.execute('SELECT key,value FROM workspace ORDER BY key').fetchall());self.assertEqual(crm,self.c.execute('SELECT entity,id,payload FROM crm_records ORDER BY entity,id').fetchall());self.assertEqual(before,self.c.execute('SELECT * FROM accounts').fetchall())
 def test_workflow_variety_and_foreign_links(self):
  seed_ai_demo.add(self.c,'testadmin@example.invalid');p=self.load('biomed_portal_v33_clean');d=self.load('biomed_is_v50_transactions')
  for typ in ['travel','leave','budget','car','room','general']:
   statuses={r['status'] for r in p['requests'] if r['id'].startswith(demo.PREFIX) and r['type']==typ}
   self.assertEqual(statuses,{'Pending','Approved','Rejected','Cancelled'})
  self.assertGreaterEqual(len(d['documents']),100);ids={r['id'] for r in d['documents']};products={r['id'] for r in d['products']}
  for r in d['documents']:
   if r.get('sourceId'):self.assertIn(r['sourceId'],ids)
   for line in r['lines']:self.assertIn(line['productId'],products)
  for entity in ['Events','Leads','ProjectActivity','HelpDeskTickets']:self.assertGreaterEqual(self.c.execute('SELECT count(*) FROM crm_records WHERE entity=?',(entity,)).fetchone()[0],24)
 def test_generated_budget_ledger_balances_and_statuses(self):
  seed_ai_demo.add(self.c,'testadmin@example.invalid');budget=self.load('biomed_budget_v60_years')
  self.assertGreaterEqual(len(budget['years']),3)
  for y in budget['years'].values():
   for row in y['products']+y['expenses']:
    if not row['id'].startswith(demo.PREFIX):continue
    fields=[('revenueActual',row['id'],'Actual'),('cogsActual','cogs:'+row['id'],'Actual')] if row in y['products'] else [('actual',row['id'],'Actual'),('commitment',row['id'],'Commitment')]
    for field,line,typ in fields:
     for m,amount in enumerate(row[field]):self.assertAlmostEqual(amount,sum(x['amount'] for x in y['ledger'] if x.get('line')==line and x['type']==typ and x['month']==m))
   self.assertEqual({r['status'] for r in y['approvals'] if r['id'].startswith(demo.PREFIX)},{'Submitted','Department Approved','Finance Approved','Approved','Returned'})
if __name__=='__main__':unittest.main()
