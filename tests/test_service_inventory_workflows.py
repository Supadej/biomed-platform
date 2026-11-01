import sys,json,copy,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import test_service_inventory as fixtures
import serve,service_inventory as si,service_inventory_workflows as w,instrument_service as f,permissions_policy as policy
class Workflows(unittest.TestCase):
 call=fixtures.Inventory.call
 request=fixtures.Inventory.request
 approve=fixtures.Inventory.approve
 job=fixtures.Inventory.job
 qty=fixtures.Inventory.qty
 central=fixtures.Inventory.central
 tearDown=fixtures.Inventory.tearDown
 def setUp(self):
  fixtures.Inventory.setUp(self)
  with serve.connect() as c:self.approve(c,self.request(c,5))
 def count(self,c,qty=4,reason='One part damaged'):
  return self.call(c,{'action':'stock-check','engineer':'u2','lines':[{'productId':'p1','lot':'LOT','expiry':'2027-12-31','book':self.qty(c),'counted':qty,'reason':reason}]})['id']
 def test_count_reason_separation_stale_and_single_posting(self):
  with serve.connect() as c:
   with self.assertRaises(ValueError):self.count(c,4,'')
   ident=self.count(c);self.assertEqual(self.qty(c),5)
   with self.assertRaises(policy.PermissionDenied):self.call(c,{'action':'stock-check-approve','id':ident,'version':1})
   self.call(c,{'action':'stock-check-approve','id':ident,'version':1},self.actor);self.assertEqual(self.qty(c),4);self.assertEqual(self.central(c),5)
   with self.assertRaises(ValueError):self.call(c,{'action':'stock-check-approve','id':ident,'version':1},self.actor)
   ident=self.count(c,3);self.job(c,1)
   with self.assertRaises(ValueError):self.call(c,{'action':'stock-check-approve','id':ident,'version':1},self.actor)
   self.assertEqual(self.qty(c),3)
 def test_matching_count_and_scoping(self):
  with serve.connect() as c:
   ident=self.count(c,5,'');record=next(x for x in self.call(c)['checks'] if x['id']==ident);self.assertEqual(record['status'],'Completed');self.assertEqual(self.qty(c),5)
   with self.assertRaises(policy.PermissionDenied):self.call(c,{'action':'stock-check','engineer':'u1','lines':[]},perms=self.perms-{'is.service-inventory.approve'})
 def test_consolidated_count_preserves_holders_and_approval_audit(self):
  with serve.connect() as c:
   si.post(c,self.actor,'u1','p1','LOT','2027-12-31',5,'Test custody','TEST')
   body={'action':'stock-check','consolidated':True,'lines':[{'productId':'p1','lot':'LOT','expiry':'2027-12-31','book':10,'counted':7,'reason':'Verified physical discrepancy'}]}
   ident=self.call(c,body,self.actor)['id']
   with self.assertRaises(policy.PermissionDenied):self.call(c,{'action':'stock-check-approve','id':ident,'version':1},self.actor)
   record=next(x for x in self.call(c)['checks'] if x['id']==ident)
   self.assertEqual(sum(x['counted'] for x in record['lines'][0]['custody']),7)
   self.call(c,{'action':'stock-check-approve','id':ident,'version':1},self.engineer)
   self.assertEqual(sum(x['qty'] for x in si.balances(c)),7)
   self.assertEqual(self.central(c),5)
   self.assertTrue(all(float(x['qty']).is_integer() for x in si.balances(c)))
   self.assertEqual(len([x for x in si.entries(c) if x['reference']==record['ref']]),2)
 def test_consolidated_count_cannot_count_other_custody_without_approval_role(self):
  with serve.connect() as c:
   si.post(c,self.actor,'u1','p1','LOT','2027-12-31',5,'Test custody','TEST')
   with self.assertRaises(ValueError):self.call(c,{'action':'stock-check','consolidated':True,'lines':[{'productId':'p1','lot':'LOT','expiry':'2027-12-31','book':10,'counted':10}]},perms=self.perms-{'is.service-inventory.approve'})
 def test_billing_role_can_invoice_without_stock_approval(self):
  with serve.connect() as c:
   job=self.job(c,2,customerId='c1');perms={'is_view','is.service-inventory.view','service.view','service.jobs.view','is.invoice.view','is.invoice.create','is.invoice.edit','is.master-customers.view'}
   self.assertTrue(self.call(c,actor=self.actor,perms=perms)['jobDetails'])
   self.call(c,{'action':'add-to-invoice','jobId':job['id']},self.actor,perms)
   with self.assertRaises(policy.PermissionDenied):self.call(c,{'action':'stock-check','engineer':'u2','lines':[]},self.actor,perms)
 def test_invoice_idempotence_job_details_guard_and_unlink(self):
  with serve.connect() as c:
   job=self.job(c,2,customerId='c1');result=self.call(c,{'action':'add-to-invoice','jobId':job['id']},self.actor);data=si.warehouse_state(c);inv=next(d for d in data['documents'] if d['id']==result['invoiceId']);self.assertEqual(inv['status'],'Draft');self.assertEqual(inv['party'],'c1');self.assertEqual(inv['lines'][0]['qty'],2);self.assertEqual(self.qty(c),3);self.assertEqual(self.central(c),5)
   detail=next(j for j in self.call(c)['jobDetails'] if j['id']==job['id']);self.assertEqual(detail['billingStatus'],'Invoiced');self.assertIn('customer',detail)
   with self.assertRaises(ValueError):self.call(c,{'action':'add-to-invoice','jobId':job['id']},self.actor)
   fresh=next(j for j in f.rows(c) if j['id']==job['id'])
   with self.assertRaises(ValueError):self.job(c,3,old=fresh)
   changed=copy.deepcopy(data);changed['documents']=[d for d in changed['documents'] if d['id']!=inv['id']]
   with self.assertRaises(policy.PermissionDenied):si.protect(data,changed)
   self.call(c,{'action':'unlink-invoice','jobId':job['id']},self.actor);self.assertEqual(next(j for j in self.call(c)['jobDetails'] if j['id']==job['id'])['billingStatus'],'Open')
   fresh=next(j for j in f.rows(c) if j['id']==job['id']);self.job(c,3,old=fresh);self.assertEqual(self.qty(c),2)
if __name__=='__main__':unittest.main()
