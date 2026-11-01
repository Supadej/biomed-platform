import sys,json,copy,io,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import test_crm as fixture
import serve,finance_workspace as fw,budget_governance as bg
class Finance(unittest.TestCase):
 setUp=fixture.CRM.setUp
 tearDown=fixture.CRM.tearDown
 def call(self,body=None,actor=None,perms=None,year=2027):
  class H:
   def reply(self,status,data):return status,data
  h=H();h.path='/api/finance-workspace?year='+str(year);h.rfile=io.BytesIO(json.dumps(body).encode());h.headers={'Content-Length':str(len(h.rfile.getvalue()))}
  return fw.handle(h,'POST' if body else 'GET',serve.connect,lambda h:actor or self.actor,lambda a:self.perms if perms is None else perms,lambda h:True)
 def post(self,action,**kw):
  actor=kw.pop('actor',None);_,d=self.call();return self.call({'action':action,'version':d['version'],**kw},actor)
 def bill(self,**extra):return {'type':'Payable','reference':'BILL-1','party':'Supplier','currency':'THB','amount':100,'date':'2026-05-01','due':'2026-06-01',**extra}
 def test_aging_partial_settlement_permissions_duplicate_and_void(self):
  self.assertEqual(self.call(perms=self.perms-{'budget.finance.view'})[0],403)
  self.assertEqual(self.post('manual',record=self.bill())[0],200)
  self.assertEqual(self.post('manual',record=self.bill())[0],400)
  _,d=self.call();bill=next(x for x in d['report']['aging'] if x['reference']=='BILL-1')
  self.assertEqual(bill['bucket'],'Over 90')
  self.assertEqual(self.post('settle',sourceId=bill['id'],amount=120,date='2026-06-01',reference='PAY-1',verified=True)[0],400)
  status,d=self.post('settle',sourceId=bill['id'],amount=40,date='2026-06-01',reference='PAY-1',verified=True);self.assertEqual(status,200,d)
  self.assertEqual(next(x for x in d['report']['aging'] if x['id']==bill['id'])['outstanding'],60)
  self.assertEqual(self.post('void',id=bill['id'],reason='Duplicate supplier bill')[0],400)
  self.assertEqual(self.post('void',id=d['finance']['settlements'][0]['id'],reason='Receipt reversed')[0],200)
  self.assertEqual(self.post('void',id=bill['id'],reason='Duplicate')[0],200)
 def test_cash_forecast_currency_and_commitment_no_double_counting(self):
  with serve.connect() as c:
   data=json.loads(c.execute("select value from workspace where key='biomed_is_v50_transactions'").fetchone()[0]);data['documents'].append({'id':'po1','kind':'purchase-order','status':'Approved','ref':'PO-1','currency':'THB','lines':[{'qty':1,'price':500}]});c.execute("update workspace set value=? where key='biomed_is_v50_transactions'",(json.dumps(data),))
   bg.initialize(c);_,s=bg.workspace(c,2027);c.execute('insert into budget_governance values(?,?,1)',('2027',json.dumps({'approved':{'lines':bg.grouped(s)},'reviews':[]})))
  _,d=self.call();key=next(x['key'] for x in d['report']['commitments'] if x['kind']=='Expense')
  status,d=self.post('mapping',id='po1',key=key,included=True);self.assertEqual(status,200,d);self.assertEqual(next(x for x in d['report']['commitments'] if x['key']==key)['additionalPO'],0)
  _,d=self.post('mapping',id='po1',key=key,included=False);self.assertEqual(next(x for x in d['report']['commitments'] if x['key']==key)['additionalPO'],500)
  _,d=self.post('manual',record=self.bill(purchaseOrderId='po1',amount=100));self.assertEqual(next(x for x in d['report']['commitments'] if x['key']==key)['additionalPO'],400)
  _,d=self.post('opening',currency='THB',date=fw.today().isoformat(),amount=1000);self.assertEqual(len(d['report']['forecast']['THB']['weeks']),13)
  _,d=self.post('cash',record={'reference':'USD PAYROLL','currency':'USD','amount':200,'direction':'Outflow','date':fw.today().isoformat()});self.assertEqual(d['report']['forecast']['USD']['weeks'][0]['closing'],-200);self.assertTrue(d['report']['forecast']['THB']['openingVerified'])
 def test_close_independent_review_and_version(self):
  with serve.connect() as c:c.execute("insert or ignore into accounts(id,email,name,role,user_id,password_hash,salt,iterations,created_at) values('test-fin','finance@example.invalid','Finance','Accounting','u1',X'00',X'00',1,'2026-01-01')")
  tasks=[{'owner':'u1','done':True,'evidence':'Reconciled workbook reference'} for t in fw.TASKS]
  status,d=self.post('close-save',month=0,tasks=tasks);self.assertEqual(status,200,d)
  self.assertEqual(self.post('close-submit',month=0)[0],200)
  self.assertEqual(self.post('close-review',month=0,approve=True)[0],403)
  status,d=self.post('close-review',month=0,approve=True,actor=('r','r@example.invalid','Reviewer','Accounting','u2'));self.assertEqual(status,200,d);self.assertEqual(d['finance']['close']['2027:0']['status'],'Reviewed')
  self.assertEqual(self.call({'action':'opening','version':0,'currency':'THB','date':fw.today().isoformat(),'amount':10})[0],409)
if __name__=='__main__':unittest.main()
