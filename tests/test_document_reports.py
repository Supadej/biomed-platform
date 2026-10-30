import sys,json,unittest,io
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import fitz,test_crm as fixture,serve,document_report as report,permissions_policy as policy
class Reports(unittest.TestCase):
 setUp=fixture.CRM.setUp
 tearDown=fixture.CRM.tearDown
 def sample(self,kind='invoice',count=1):return {'id':'r','kind':kind,'ref':'BMD-2026-001','status':'Approved','date':'2026-10-30','party':'c','owner':'u','currency':'THB','lines':[{'productId':'p','qty':2,'price':1250,'lot':'L1'} for _ in range(count)],'notes':'Thai / ทดสอบ'}
 def data(self,d):return {'documents':[d],'products':[{'id':'p','name':'Reagent / ชุดตรวจ','sku':'CAT-001','unit':'kit'}],'customers':[{'id':'c','name':'Example Hospital','address':'Bangkok'}],'users':[{'id':'u','name':'Sales Representative'}]}
 def test_all_document_types_generate_pdf(self):
  for kind in report.TITLES:
   with self.subTest(kind=kind):
    d=self.sample(kind);pdf=report.build(d,self.data(d));doc=fitz.open(stream=pdf,filetype='pdf');text=__import__('unicodedata').normalize('NFKC',''.join(p.get_text() for p in doc));self.assertIn('BMD-2026-001',text);self.assertIn(report.TITLES[kind],text);self.assertGreater(len(pdf),1000)
 def test_long_report_repeats_header_and_table_and_keeps_totals(self):
  d=self.sample(count=45);doc=fitz.open(stream=report.build(d,self.data(d)),filetype='pdf');self.assertGreater(len(doc),1)
  for page in doc:
   text=page.get_text();self.assertIn('Taxpayer ID',text);self.assertIn('BMD-2026-001',text);self.assertIn('sales@biomedthai.com',text)
   for word in page.get_text('words'):self.assertGreaterEqual(word[0],30);self.assertLessEqual(word[2],566)
  full=''.join(p.get_text() for p in doc);self.assertIn('Grand total',full);self.assertEqual(full.count('CAT-001'),45)
  totals=[p.get_text() for p in doc if 'Grand total' in p.get_text()][0];self.assertIn('Subtotal',totals)
 def test_endpoint_auth_and_print_permission(self):
  class H:
   path='/api/document-report?id=i1'
   def reply(self,s,d):return s,d
  h=H();self.assertEqual(report.handle(h,serve.connect,lambda _:None,lambda _:self.perms)[0],401)
  self.assertEqual(report.handle(h,serve.connect,lambda _:self.actor,lambda _:self.perms-{'is.invoice.print'})[0],403)
 def test_stock_count_and_move_resolution(self):
  state={'stockChecks':[{'id':'s','ref':'SC-1','productId':'p','count':5,'system':3,'at':'2026-10-30'}],'warehouseMoves':[{'id':'m','productId':'p','qty':4,'from':'A','to':'B','at':'2026-10-30'}]}
  self.assertEqual(report.resolve(state,'s','cycle-count')['lines'][0]['qty'],5);self.assertEqual(report.resolve(state,'m','warehouse-move')['kind'],'warehouse-move')
if __name__=='__main__':unittest.main()
