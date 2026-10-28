import sys,json,io,copy,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import test_crm as fixture
import serve,budget_governance as bg
class Governance(unittest.TestCase):
 setUp=fixture.CRM.setUp
 tearDown=fixture.CRM.tearDown
 def call(self,body=None,actor=None,perms=None):
  class H:
   path='/api/budget-governance?year=2027'
   def reply(self,status,data):return status,data
  h=H();h.rfile=io.BytesIO(json.dumps(body).encode());h.headers={'Content-Length':str(len(h.rfile.getvalue()))}
  return bg.handle(h,'POST' if body else 'GET',serve.connect,lambda h:actor or self.actor,lambda a:self.perms if perms is None else perms,lambda h:True)
 def post(self,action,**kw):
  actor=kw.pop('actor',None);_,data=self.call();body={'version':data['version'],'workspaceRevision':data['workspaceRevision'],'action':action,**kw};return self.call(body,actor)
 def approve(self,id=None):
  actor=('reviewer','review@example.invalid','Finance Reviewer','System Admin','u2')
  for i in range(3):
   status,result=self.post('approve',id=id,actor=actor);self.assertEqual(status,200,result)
 def plan(self):
  _,data=self.call();lines=data['current']
  for l in lines:l['target']=[200]*12
  self.assertEqual(self.post('submit',lines=lines)[0],200)
 def test_plan_publish_and_independent_approval(self):
  self.plan();self.assertEqual(self.post('approve')[0],403);self.approve()
  with serve.connect() as c:
   _,s=bg.workspace(c,'2027');self.assertEqual(s['products'][0]['budget'],[200]*12);self.assertEqual(s['expenses'][0]['budget'],[200]*12)
   g,v=bg.load(c,'2027');self.assertEqual(g['approved']['revision'],1);self.assertEqual(len(g['approvedVersions']),1)
 def test_period_lock_reopen_and_stale_snapshot(self):
  self.plan();self.approve();status,result=self.post('review',period='Monthly',index=0,verified=True);self.assertEqual(status,200,result);ident=result['governance']['reviews'][-1]['id'];self.approve(ident)
  with serve.connect() as c:
   old,_=bg.workspace(c,'2027');new=copy.deepcopy(old);new['years']['2027']['products'][0]['revenueActual'][0]=99
   with self.assertRaisesRegex(ValueError,'finalized'):bg.guard(c,old,new)
  status,result=self.post('reopen',id=ident,reason='Correct verified posting');self.assertEqual(status,200,result)
  with serve.connect() as c:bg.guard(c,old,new)
  status,result=self.post('review',period='Monthly',index=1,verified=True);ident=result['governance']['reviews'][-1]['id']
  with serve.connect() as c:
   data,s=bg.workspace(c,'2027');s['products'][0]['revenueActual'][1]=42;c.execute('update workspace set value=? where key=?',(json.dumps(data),bg.KEY))
  status,result=self.post('approve',id=ident,actor=('r','r@example.invalid','Reviewer','System Admin','u2'));self.assertEqual(status,400);self.assertIn('changed',result['error'])
  self.assertEqual(self.post('return',id=ident,reason='Actuals updated',actor=('r','r@example.invalid','Reviewer','System Admin','u2'))[0],200)
 def test_actual_source_entry_and_finalized_write_rollback(self):
  self.plan();self.approve()
  _,d=self.call();lines=d['current']
  for l in lines:l['target']=[40]*12
  status,result=self.post('actual',lines=lines);self.assertEqual(status,200,result)
  status,result=self.post('review',period='Monthly',index=0,verified=True);self.approve(result['governance']['reviews'][-1]['id'])
  lines[0]['target'][0]=50;status,result=self.post('actual',lines=lines);self.assertEqual(status,400,result)
  with serve.connect() as c:self.assertEqual(bg.workspace(c,'2027')[1]['products'][0]['revenueActual'][0],40)
 def test_validation_permissions_revision_and_future_period(self):
  _,d=self.call();self.assertEqual(self.call({'action':'save','version':999,'lines':d['current']})[0],409)
  self.assertEqual(self.call(perms={'budget_view'})[0],403)
  lines=d['current'];lines[0]['target'][0]=float('nan');self.assertEqual(self.post('save',lines=lines)[0],400)
  self.plan();self.approve();self.assertEqual(self.post('review',period='Annual',index=0,verified=True)[0],400)
  self.assertEqual(self.post('review',period='Monthly',index=0,verified=False)[0],400)
  self.assertEqual(self.post('review',period='Half-year',index=1,verified=True)[0],400)
if __name__=='__main__':unittest.main()
