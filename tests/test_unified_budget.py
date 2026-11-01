import unittest,sqlite3,json,tempfile,io,copy,sys
from pathlib import Path
from contextlib import contextmanager
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import budget_governance as bg,permissions_policy as policy
ROOT=Path(__file__).resolve().parents[1]
class Handler:
 path='/api/budget-governance?year=2027'
 def __init__(self,body=None):
  raw=json.dumps(body).encode() if body else b'';self.rfile=io.BytesIO(raw);self.headers={'Content-Length':str(len(raw))}
 def reply(self,status,body):self.status=status;self.body=body;return body
class UnifiedBudget(unittest.TestCase):
 def test_approval_publishes_revenue_costs_and_all_expense_menus(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'test.sqlite3'
   with sqlite3.connect(ROOT/'data/biomed.sqlite3') as src,sqlite3.connect(path) as dst:src.backup(dst)
   @contextmanager
   def connect():
    with sqlite3.connect(path) as c:yield c
   with connect() as c:
    data,state=bg.workspace(c,2027);self.assertEqual(state['costCenters'],[])
    state['costCenters']=[{'id':'USER','name':'Company','active':True}]
    state['expenses']=[{'id':'item-'+str(i),'name':'Test','category':cat,'costCenter':'Company','active':True,'budget':[0]*12,'actual':[0]*12,'commitment':[0]*12} for i,cat in enumerate(policy.CATEGORY)]
    c.execute('update workspace set value=? where key=?',(json.dumps(data),bg.KEY))
    owner=json.loads(c.execute("select value from workspace where key='biomed_portal_v33_clean'").fetchone()[0])['users'][0]['id']
   perms={'budget_view','budget.approvals.view','budget.approvals.submit','budget.approvals.department_approve','budget.approvals.finance_approve','budget.approvals.director_approve','budget.manage_products.view','budget.manage_items.view'}
   actors=[(None,None,'Author','System Admin',str(owner)),(None,None,'Reviewer','System Admin','reviewer')]
   def request(body=None,review=False):
    h=Handler(body);bg.handle(h,'POST' if body else 'GET',connect,lambda h:actors[int(review)],lambda a:perms,lambda h:True)
    self.assertEqual(h.status,200,h.body);return h.body
   response=request();response=request({'version':response['version'],'action':'source-reference','name':'Consulting'});lines=[]
   for kind,source,amount in [('Revenue','Consulting',1000),('COGS','Consulting',200)]:lines.append({'kind':kind,'source':source,'costCenter':'Company','revenueType':'Service','owner':owner,'target':[amount]*12})
   for i,cat in enumerate(policy.CATEGORY):
    lines.append({'lineId':'item-'+str(i),'kind':'Expense','source':cat+' · Test','expenseName':'Test','category':cat,'costCenter':'Company','revenueType':'Other','owner':owner,'target':[10]*12})
   invalid=copy.deepcopy(lines);invalid[0]['source']='Not configured'
   h=Handler({'version':response['version'],'action':'save','lines':invalid});bg.handle(h,'POST',connect,lambda h:actors[0],lambda a:perms,lambda h:True);self.assertEqual(h.status,400);self.assertIn('reference',h.body['error'])
   invalid=copy.deepcopy(lines);invalid[2]['category']='Other Cost of Sales'
   h=Handler({'version':response['version'],'action':'save','lines':invalid});bg.handle(h,'POST',connect,lambda h:actors[0],lambda a:perms,lambda h:True);self.assertEqual(h.status,400);self.assertIn('category',h.body['error'])
   response=request({'version':response['version'],'action':'submit','lines':lines})
   for i in range(3):response=request({'version':response['version'],'action':'approve'},True)
   self.assertEqual(response['governance']['approved']['status'],'Approved')
   self.assertFalse(any(m['approved'] for m in response['effectiveMonthly']))
   response=request({'version':response['version'],'action':'submit-month','month':0})
   month_id=response['governance']['monthlyBudgets'][-1]['id']
   for i in range(3):response=request({'version':response['version'],'action':'approve','id':month_id},True)
   self.assertTrue(response['effectiveMonthly'][0]['approved']);self.assertFalse(response['effectiveMonthly'][1]['approved'])
   self.assertEqual(sum(l['amount'] for l in response['effectiveMonthly'][0]['lines'] if l['kind']=='Revenue'),1000)
   with connect() as c:
    data,state=bg.workspace(c,2027);self.assertEqual(len(state['products']),1);self.assertEqual(len(state['expenses']),len(policy.CATEGORY))
    self.assertEqual(state['products'][0]['budget'],[1000]*12);self.assertEqual(state['products'][0]['cogsBudget'],[200]*12)
    self.assertEqual({x['category'] for x in state['expenses']},set(policy.CATEGORY))
    changed=copy.deepcopy(data);changed['years']['2027']['expenses'][0]['actual']=[5]*12;bg.guard(c,data,changed)
    changed['years']['2027']['expenses'][0]['budget'][0]=999
    with self.assertRaisesRegex(ValueError,'Annual & Monthly Budget'):bg.guard(c,data,changed)
 def test_draft_budget_cannot_be_changed_from_workspace(self):
  with sqlite3.connect(':memory:') as c:
   before={'years':{'2027':{'products':[],'expenses':[{'id':'a','budget':[0]*12}]}}};after=copy.deepcopy(before);after['years']['2027']['expenses'][0]['budget'][1]=1
   with self.assertRaisesRegex(ValueError,'Annual & Monthly Budget'):bg.guard(c,before,after)
if __name__=='__main__':unittest.main()
