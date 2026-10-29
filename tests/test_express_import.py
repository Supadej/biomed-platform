import sys,json,io,base64,unittest,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import test_crm as fixture
import serve,express_import as ei,finance_workspace as fw,budget_governance as bg
class Express(unittest.TestCase):
 def setUp(self):
  fixture.CRM.setUp(self)
  with serve.connect() as c:
   data=json.loads(c.execute("select value from workspace where key='biomed_is_v50_transactions'").fetchone()[0]);data['documents'][0]['party']='c1';c.execute("update workspace set value=? where key='biomed_is_v50_transactions'",(json.dumps(data),))
 tearDown=fixture.CRM.tearDown
 def call(self,body=None,actor=None,perms=None):
  class H:
   path='/api/express-import?year=2027'
   def reply(self,status,data):return status,data
  h=H();h.rfile=io.BytesIO(json.dumps(body).encode());h.headers={'Content-Length':str(len(h.rfile.getvalue()))}
  return ei.handle(h,'POST' if body else 'GET',serve.connect,lambda h:actor or self.actor,lambda a:self.perms if perms is None else perms,lambda h:True)
 def stage(self,kind,text):
  return self.call({'action':'stage','filename':'express.csv','type':kind,'file':base64.b64encode(text.encode()).decode(),'headerRow':1,'company':'Biomed','asOf':'2026-10-01','mapping':{f:f for f in ei.TYPES[kind]}})
 def review(self,action,ident,reason=''):
  _,d=self.call();b=next(x for x in d['batches'] if x['id']==ident)
  return self.call({'action':action,'id':ident,'version':b['version'],'reason':reason},actor=('r','r@example.invalid','Reviewer','Accounting','u2'))
 def test_ar_snapshot_matches_is_and_reversal(self):
  csv='reference,party,date,due,outstanding,currency\nINV-1,Hospital,01/10/2569,15/10/2569,150,THB\n'
  status,d=self.stage('Receivables',csv);self.assertEqual(status,200,d);ident=d['batches'][0]['id']
  self.assertEqual(self.call({'action':'approve','id':ident,'version':1})[0],403)
  status,d=self.review('approve',ident);self.assertEqual(status,200,d)
  with serve.connect() as c:
   f,_=fw.load(c,2027);rows,_=fw.source_rows(c,f);self.assertEqual(len(rows),1);self.assertEqual(rows[0]['outstanding'],150)
  self.assertEqual(self.stage('Receivables',csv)[0],400)
  self.assertEqual(self.review('reverse',ident,'Corrected statement')[0],200)
  with serve.connect() as c:self.assertEqual(fw.source_rows(c,fw.load(c,2027)[0])[0][0]['outstanding'],200)
 def test_actuals_replace_not_add_and_respect_locks(self):
  text='date,kind,source,costCenter,amount,currency\n2026-05-01,Revenue,Other revenue,LSR,80,THB\n'
  status,d=self.stage('Actuals',text);self.assertEqual(status,200,d);ident=d['batches'][0]['id'];self.assertEqual(self.review('approve',ident)[0],200)
  with serve.connect() as c:self.assertEqual(bg.workspace(c,2027)[1]['products'][0]['revenueActual'][0],80)
  self.assertEqual(self.review('reverse',ident,'Reverse wrong report')[0],200)
  with serve.connect() as c:self.assertEqual(bg.workspace(c,2027)[1]['products'][0]['revenueActual'][0],25)
  with serve.connect() as c:
   _,state=bg.workspace(c,2027);bg.initialize(c);c.execute('insert into budget_governance values(?,?,1)',('2027',json.dumps({'reviews':[{'status':'Approved','start':0,'end':0,'actualSnapshot':bg.actual_snapshot(state,0,0)}]})))
  status,d=self.stage('Actuals',text);self.assertEqual(status,200,d);ident=d['batches'][0]['id'];self.assertEqual(self.review('approve',ident)[0],400)
  with serve.connect() as c:self.assertEqual(bg.workspace(c,2027)[1]['products'][0]['revenueActual'][0],25)
 def test_updated_payable_snapshots_preserve_identity_and_reverse_in_order(self):
  text='reference,party,date,due,outstanding,currency\nBILL-1,Supplier,2026-05-01,2026-06-01,100,THB\n'
  status,d=self.stage('Payables',text);self.assertEqual(status,200,d);first=d['batches'][0]['id'];self.assertEqual(self.review('approve',first)[0],200)
  body={'action':'stage','filename':'updated.csv','type':'Payables','file':base64.b64encode(text.replace(',100,THB',',80,THB').encode()).decode(),'company':'Biomed','asOf':'2026-10-02','mapping':{f:f for f in ei.TYPES['Payables']}}
  status,d=self.call(body);self.assertEqual(status,200,d);second=d['batches'][0]['id'];self.assertEqual(self.review('approve',second)[0],200)
  with serve.connect() as c:
   rows=fw.source_rows(c,fw.load(c,2027)[0])[0];bills=[r for r in rows if r['reference']=='BILL-1'];self.assertEqual(len(bills),1);self.assertEqual(bills[0]['outstanding'],80)
  self.assertEqual(self.review('reverse',first,'Correction')[0],400)
  self.assertEqual(self.review('reverse',second,'Correction')[0],200)
  self.assertEqual(self.review('reverse',first,'Correction')[0],200)
 def test_validation_csv_thai_and_xlsx(self):
  raw='รหัสบัญชี,ชื่อบัญชี\n001,ธนาคาร\n'.encode('cp874');h,rows,_=ei.decode_file({'filename':'thai.csv','file':base64.b64encode(raw).decode(),'encoding':'cp874'});self.assertEqual(rows[0]['รหัสบัญชี'],'001')
  self.assertEqual(ei.date('28/10/69','BE'),'2026-10-28')
  with self.assertRaises(ValueError):ei.date('28/10/69')
  status,d=self.stage('General ledger','date,reference,lineId,account,debit,credit,currency\n2026-05-01,JV1,1,1000,10,0,THB\n');self.assertEqual(status,400);self.assertIn('balance',d['errors'][0]['error'])
  import openpyxl
  w=openpyxl.Workbook();s=w.active;s.append(['account','name','category']);s.append(['001','Cash','Asset']);stream=io.BytesIO();w.save(stream)
  h,rows,d=ei.decode_file({'filename':'accounts.xlsx','file':base64.b64encode(stream.getvalue()).decode()});self.assertEqual(rows[0]['account'],'001')
  self.assertEqual(self.call(perms=self.perms-{'budget.finance.view'})[0],403)
if __name__=='__main__':unittest.main()
