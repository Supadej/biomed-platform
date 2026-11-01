import sys,copy,json,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import integration_engine as e,integration_api as api,serve,permissions_policy as policy
class Integrations(unittest.TestCase):
 def portal(self):return {'users':[{'id':'u','name':'Staff','department':'Sales'}],'productLines':['Diagnostics'],'expenses':[{'id':'x','status':'Approved','owner':'u','category':'Local expense','amount':100,'decidedAt':'2026-10-01','created':'2026-09-01'}],'payments':[]}
 def source(self):return {'customers':[{'id':'c','name':'Customer'}],'documents':[{'id':'i','ref':'INV1','kind':'invoice','status':'Approved','date':'2026-10-01','portalRep':'s','party':'c','currency':'THB','lines':[{'productId':'p','qty':2,'price':100}],'financials':{'net':180,'grand':192.6}}]}
 def store(self):return {'active':2027,'years':{'2027':{'expenses':[{'id':'line','name':'Local travel','category':'Local Traveling and Expenses','costCenter':'Sales','actual':[10]*12,'commitment':[20]*12}],'ledger':[{'id':'manual','line':'line','type':'Actual','amount':10,'month':0}]},'2028':{'expenses':[{'id':'line2','name':'Travel next year','category':'Local Traveling and Expenses','costCenter':'Sales','actual':[0]*12,'commitment':[0]*12}],'ledger':[]}}}
 def configs(self):return {y:{**copy.deepcopy(e.BUDGET_DEFAULT),'enabled':True,'rules':[{'module':'expenses','category':'Local expense','department':'Sales','target':line}]} for y,line in [('2027','line'),('2028','line2')]}
 def test_is_mappings_and_amount(self):
  c={**copy.deepcopy(e.IS_DEFAULT),'staffMap':{'s':'u'},'productMap':{'p':'Diagnostics'}};plan=e.is_projection(self.source(),self.portal(),c);self.assertEqual(plan['salesActuals'][0]['amount'],180)
  c['amountBasis']='grand';self.assertEqual(e.is_projection(self.source(),self.portal(),c)['salesActuals'][0]['amount'],192.6)
 def test_currency_and_missing_map(self):
  self.assertTrue(e.is_projection(self.source(),self.portal(),e.IS_DEFAULT)['exceptions'])
  src=self.source();src['documents'][0]['currency']='USD';c={**copy.deepcopy(e.IS_DEFAULT),'staffMap':{'s':'u'},'productMap':{'p':'Diagnostics'}};self.assertFalse(e.is_projection(src,self.portal(),c)['salesActuals']);c['rates']['USD']=35;self.assertEqual(e.is_projection(src,self.portal(),c)['salesActuals'][0]['amount'],6300)
 def test_linked_credit(self):
  src=self.source();src['documents'].append({'id':'credit','kind':'credit-note','status':'Approved','sourceId':'i','currency':'THB','lines':[{'productId':'p','qty':1,'price':20}]});c={**copy.deepcopy(e.IS_DEFAULT),'staffMap':{'s':'u'},'productMap':{'p':'Diagnostics'}};self.assertEqual(e.is_projection(src,self.portal(),c)['salesActuals'][0]['amount'],160)
 def test_repeat_run_preserves_manual(self):
  plan=e.budget_plan(self.portal(),self.store(),self.configs());a=e.reconcile_budget(self.store(),plan);b=e.reconcile_budget(a,plan);self.assertEqual(a,b);self.assertEqual(a['years']['2027']['expenses'][0]['commitment'][5],120);self.assertEqual(a['years']['2027']['ledger'][0]['id'],'manual')
 def test_payment_releases_crossyear_commitment(self):
  p=self.portal();a=e.reconcile_budget(self.store(),e.budget_plan(p,self.store(),self.configs()));p['payments']=[{'id':'paid','sourceId':'x','sourceType':'expense','owner':'u','status':'Paid','amount':80,'updatedAt':'2027-06-01'}];b=e.reconcile_budget(a,e.budget_plan(p,a,self.configs()));self.assertEqual(b['years']['2027']['expenses'][0]['commitment'][5],20);self.assertEqual(b['years']['2028']['expenses'][0]['actual'][1],100)
 def test_cancelled_source_reverses_only_bridge(self):
  p=self.portal();a=e.reconcile_budget(self.store(),e.budget_plan(p,self.store(),self.configs()));p['expenses'][0]['status']='Cancelled';b=e.reconcile_budget(a,e.budget_plan(p,a,self.configs()));self.assertEqual(b['years']['2027']['expenses'],self.store()['years']['2027']['expenses']);self.assertEqual(len(b['years']['2027']['ledger']),1)
 def test_conflicting_fiscal_date_rules_do_not_double_post(self):
  p=self.portal();p['payments']=[{'id':'paid','sourceId':'x','sourceType':'expense','owner':'u','status':'Paid','amount':100,'updatedAt':'2027-06-01'}];configs=self.configs();configs['2027']['dateBasis']='sourceDate';plan=e.budget_plan(p,self.store(),configs);self.assertFalse(plan['postings']);self.assertTrue(any('multiple fiscal' in x for x in plan['exceptions']))
 def test_ambiguous_rule(self):
  c=self.configs();c['2027']['rules']*=2;plan=e.budget_plan(self.portal(),self.store(),c);self.assertFalse(plan['postings']);self.assertTrue(plan['exceptions'])
 def test_request_claim_link(self):
  p=self.portal();p['requests']=[{'id':'r','type':'travel','status':'Approved','owner':'u','amount':100,'date':'2026-10-01','decidedAt':'2026-10-01'}];p['expenses'][0]['requestId']='r';cfg={**e.BUDGET_DEFAULT,'requests':True};rows,issues=e.portal_sources(p,cfg);self.assertEqual(len(rows),1)
 def test_budget_api_idempotent_and_permissions(self):
  previous=serve.DB
  with tempfile.TemporaryDirectory() as td:
   serve.DB=Path(td)/'test.sqlite3';serve.initialize();perms={x['key'] for x in policy.CATALOG['permissions']};actor=('a','a','Admin','System Admin','u')
   try:
    with serve.connect() as c:
     for key,data in [(api.PKEY,self.portal()),(api.IKEY,self.source()),(api.BKEY,self.store())]:c.execute('INSERT INTO workspace VALUES(?,?,?)',(key,json.dumps(data),1))
     cfg=self.configs()['2027'];api.handle(None,'portal-budget','save','2027',{'revision':0,'config':cfg},c,actor,perms,None)
     plan=api.handle(None,'portal-budget','preview','2027',{},c,actor,perms,None)
     without=perms-{'budget.person_local.commitment'}
     with self.assertRaises(policy.PermissionDenied):api.handle(None,'portal-budget','preview','2027',{},c,actor,without,None)
     api.handle(None,'portal-budget','run','2027',{'token':plan['token']},c,actor,perms,None)
     first,_=api.workspace(c,api.BKEY);preview=api.handle(None,'portal-budget','preview','2027',{},c,actor,perms,None);api.handle(None,'portal-budget','run','2027',{'token':preview['token']},c,actor,perms,None);second,_=api.workspace(c,api.BKEY);self.assertEqual(first,second)
   finally:serve.DB=previous
 def test_projection_privacy_and_ownership(self):
  portal=self.portal();portal['integrationIS']={'quotations':[{'id':'q'}],'salesActuals':[{'amount':1}],'exceptions':['private']}
  filtered=json.loads(policy.read_filter({'expenses'},api.PKEY,json.dumps(portal)));self.assertEqual(filtered['integrationIS']['salesActuals'],[]);self.assertEqual(filtered['integrationIS']['quotations'],[])
  merged=json.loads(policy.merge_scope({'expenses'},api.PKEY,json.dumps(portal),json.dumps(filtered)));self.assertEqual(merged['integrationIS'],portal['integrationIS'])
 def test_atomic_api_preview_token(self):
  previous=serve.DB
  with tempfile.TemporaryDirectory() as td:
   serve.DB=Path(td)/'test.sqlite3';serve.initialize();perms={x['key'] for x in policy.CATALOG['permissions']};actor=('a','a','Admin','System Admin','u')
   try:
    with serve.connect() as c:
     for key,data in [(api.PKEY,self.portal()),(api.IKEY,self.source()),(api.BKEY,self.store())]:c.execute('INSERT INTO workspace VALUES(?,?,?)',(key,json.dumps(data),1))
     cfg={**copy.deepcopy(e.IS_DEFAULT),'staffMap':{'s':'u'},'productMap':{'p':'Diagnostics'}}
     api.handle(None,'is-portal','save','2027',{'revision':0,'config':cfg},c,actor,perms,None)
     preview=api.handle(None,'is-portal','preview','2027',{},c,actor,perms,None)
     with self.assertRaises(ValueError):api.handle(None,'is-portal','run','2027',{'token':'wrong'},c,actor,perms,None)
     result=api.handle(None,'is-portal','run','2027',{'token':preview['token']},c,actor,perms,None);self.assertTrue(result['synced']);data,rev=api.workspace(c,api.PKEY);self.assertEqual(data['integrationIS']['salesActuals'][0]['amount'],180)
     with self.assertRaises(policy.PermissionDenied):api.handle(None,'is-portal','preview','2027',{},c,actor,set(),None)
   finally:serve.DB=previous
if __name__=='__main__':unittest.main()
