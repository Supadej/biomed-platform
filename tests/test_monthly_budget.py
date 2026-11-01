import copy,json,unittest
from test_budget_governance import Governance
import serve,budget_governance as bg,finance_workspace as fw

class MonthlyBudget(Governance):
 def test_monthly_approval_activation_revision_and_permissions(self):
  self.plan();self.approve()
  _,d=self.call();self.assertFalse(any(x['approved'] for x in d['effectiveMonthly']))
  self.assertEqual(self.post('submit-month',month=True)[0],400)
  self.assertEqual(self.post('submit-month',month=12)[0],400)
  status,d=self.post('submit-month',month=0);self.assertEqual(status,200,d)
  ident=d['governance']['monthlyBudgets'][-1]['id']
  self.assertEqual(self.post('submit-month',month=0)[0],400)
  self.assertEqual(self.post('approve',id=ident)[0],403)
  _,current=self.call();status,_=self.call({'action':'submit-month','month':1,'version':current['version']},perms=self.perms-{'budget.approvals.submit'});self.assertEqual(status,403)
  self.approve(ident);_,d=self.call();self.assertTrue(d['effectiveMonthly'][0]['approved']);self.assertFalse(d['effectiveMonthly'][1]['approved'])
  self.assertEqual(self.post('submit-month',month=0)[0],400)
  with serve.connect() as c:
   f,_=fw.load(c,2027);report=fw.report(c,2027,f)
   self.assertTrue(all(x['target']==200 and x['annualPlan']==2400 for x in report['commitments']))
  lines=copy.deepcopy(d['governance']['approved']['lines'])
  for line in lines:line['target']=[300]*12
  self.assertEqual(self.post('submit',lines=lines)[0],200);self.approve()
  _,d=self.call();self.assertEqual(d['effectiveMonthly'][0]['lines'][0]['amount'],200)
  status,d=self.post('submit-month',month=0);ident=d['governance']['monthlyBudgets'][-1]['id'];self.approve(ident)
  _,d=self.call();self.assertEqual(d['effectiveMonthly'][0]['lines'][0]['amount'],300)
  self.assertEqual(len(d['governance']['monthlyBudgets']),2)
 def test_component_and_nonbudget_data_preserved(self):
  with serve.connect() as c:
   data,state=bg.workspace(c,2027);state['expenses'][0]['componentRows']=[{'id':'a','budget':[1]*12},{'id':'b','budget':[4]*12}]
   c.execute('update workspace set value=? where key=?',(json.dumps(data),bg.KEY))
   before={key:value for key,value in c.execute('select key,value from workspace') if key!=bg.KEY}
  self.plan();self.approve()
  with serve.connect() as c:
   _,state=bg.workspace(c,2027);rows=state['expenses'][0]['componentRows'];self.assertEqual(rows[0]['budget'],[40]*12);self.assertEqual(rows[1]['budget'],[160]*12)
   self.assertEqual(before,{key:value for key,value in c.execute('select key,value from workspace') if key!=bg.KEY})
 def test_month_cannot_be_submitted_without_annual_plan(self):
  self.assertEqual(self.post('submit-month',month=0)[0],400)

if __name__=='__main__':unittest.main()
