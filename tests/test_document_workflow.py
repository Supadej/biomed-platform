import sys,json,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import test_crm as fixture
import serve,document_workflow as w,permissions_policy as p
class Workflow(unittest.TestCase):
 setUp=fixture.CRM.setUp
 tearDown=fixture.CRM.tearDown
 def doc(self,id,kind,**kw):return dict(id=id,kind=kind,ref=id,status='Approved',lines=[dict(productId='p1',qty=10,price=10)],history=[],**kw)
 def seed(self,c,docs,moves=[]):
  state=dict(documents=docs,movements=moves);c.execute('INSERT OR REPLACE INTO workspace VALUES(?,?,1)',(w.KEY,json.dumps(state)))
 def test_approval_labels_and_invoice_payment(self):
  i=self.doc('i','invoice');r=self.doc('r','payment-receipt',sourceId='i');r['lines'][0]['qty']=4
  self.assertEqual(w.progress(i,[i,r]),'Partially paid');r['lines'][0]['qty']=10;self.assertEqual(w.progress(i,[i,r]),'Paid');self.assertEqual(w.LABEL['Rejected'],'Returned for correction')
 def test_partial_receiving_and_cancelled_excluded(self):
  po=self.doc('po','purchase-order');check=self.doc('check','check-in',sourceId='po');check['lines'][0]['qty']=3
  self.assertEqual(w.progress(po,[po,check]),'Partially received');check['status']='Voided';self.assertEqual(w.progress(po,[po,check]),'Not received')
 def test_progress_permission_and_normalized_records(self):
  with serve.connect() as c:
   self.seed(c,[self.doc('q','quotation')]);body=dict(action='progress',id='q',revision=0,value='Sent')
   with self.assertRaises(p.PermissionDenied):w.mutate(c,self.actor,self.perms-{'is.quotation.progress'},body)
   w.mutate(c,self.actor,self.perms,body);self.assertEqual(json.loads(c.execute("SELECT payload FROM documents WHERE id='q'").fetchone()[0])['operationalProgress'],'Sent')
   with self.assertRaises(ValueError):w.mutate(c,self.actor,self.perms,body)
 def test_reverse_stock_once_and_block_dependents(self):
  with serve.connect() as c:
   i=self.doc('i','check-in');child=self.doc('x','invoice',sourceId='i');self.seed(c,[i,child]);body=dict(action='void',id='i',revision=0,reason='Wrong receiving')
   with self.assertRaises(ValueError):w.mutate(c,self.actor,self.perms,body)
   self.seed(c,[i],[dict(id='m',sourceId='i',productId='p1',warehouse='Main',lot='L',change=10)])
   w.mutate(c,self.actor,self.perms,body);state=json.loads(c.execute('SELECT value FROM workspace WHERE key=?',(w.KEY,)).fetchone()[0]);self.assertEqual(sum(x['change'] for x in state['movements']),0);self.assertEqual(state['documents'][0]['status'],'Voided')
   with self.assertRaises(ValueError):w.mutate(c,self.actor,self.perms,{**body,'revision':1})
 def test_negative_stock_and_forged_metadata(self):
  with serve.connect() as c:
   d=self.doc('i','check-in');self.seed(c,[d],[dict(sourceId='i',productId='p1',warehouse='Main',lot='L',change=10),dict(sourceId='other',productId='p1',warehouse='Main',lot='L',change=-9)])
   with self.assertRaises(ValueError):w.mutate(c,self.actor,self.perms,dict(action='void',id='i',revision=0,reason='Wrong receiving'))
   with self.assertRaises(p.PermissionDenied):w.guard(dict(documents=[d]),dict(documents=[{**d,'status':'Voided'}]))
 def test_return_does_not_receive_stock_twice(self):
  ret=self.doc('r','return-product');delivery=self.doc('di','delivery-in',sourceId='r');receipt=self.doc('ci','check-in',sourceId='di');move=dict(id='m',sourceId='r',change=10)
  with self.assertRaises(ValueError):w.guard(dict(documents=[ret]),dict(documents=[ret],movements=[move]))
  with self.assertRaises(ValueError):w.guard(dict(documents=[ret,delivery],movements=[move]),dict(documents=[ret,delivery,receipt],movements=[move,dict(id='new',sourceId='ci',change=10)]))
 def test_quotation_followup_and_shipment_no_backward(self):
  q=self.doc('q','quotation',portalCRM={'outcome':'Won'});self.assertEqual(w.progress(q,[q]),'Accepted')
  with serve.connect() as c:
   self.seed(c,[self.doc('s','shipment',operationalProgress='Shipped')])
   with self.assertRaises(ValueError):w.mutate(c,self.actor,self.perms,dict(action='progress',id='s',revision=0,value='Ready to ship'))
if __name__=='__main__':unittest.main()
