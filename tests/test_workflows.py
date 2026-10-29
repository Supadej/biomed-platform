import sys,copy,json,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import permissions_policy as p
class Workflows(unittest.TestCase):
 def setUp(self):
  self.perms={x['key'] for x in p.CATALOG['permissions']}
  self.co={'id':'co','kind':'customer-order','party':'C1','lines':[{'productId':'P1','qty':2}],'status':'Approved'}
  self.q={'id':'q','kind':'waiting-purchase','sourceId':'co','party':'C1','lines':copy.deepcopy(self.co['lines']),'status':'Draft'}
  self.old={'documents':[self.co]};self.new={'documents':[self.co,self.q]}
 def test_approved_queue(self):p.authorize_is(self.perms,self.old,self.new)
 def test_unapproved_rejected(self):
  self.co['status']='Pending'
  with self.assertRaises(p.PermissionDenied):p.authorize_is(self.perms,self.old,self.new)
 def test_duplicates_rejected(self):
  self.new['documents'].append(dict(self.q,id='q2'))
  with self.assertRaises(p.PermissionDenied):p.authorize_is(self.perms,self.old,self.new)
 def test_queue_snapshot(self):
  self.q['sourceId']='missing'
  with self.assertRaises(p.PermissionDenied):p.authorize_is(self.perms,self.old,self.new)
 def test_missing_permission(self):
  self.perms.remove('is.waiting-purchase.create')
  with self.assertRaises(p.PermissionDenied):p.authorize_is(self.perms,self.old,self.new)
 def test_request_from_queue(self):
  old=copy.deepcopy(self.new);old['documents'][1]['status']='Approved';new=copy.deepcopy(old);new['documents'].append({'id':'pr','kind':'purchase-request','sourceId':'q','status':'Draft'})
  p.authorize_is(self.perms,old,new)
  new['documents'].append({'id':'pr2','kind':'purchase-request','sourceId':'q','status':'Draft'})
  with self.assertRaises(p.PermissionDenied):p.authorize_is(self.perms,old,new)
 def test_manual_request(self):
  q=dict(self.q,id='manual',sourceId='')
  p.authorize_is(self.perms,{'documents':[]},{'documents':[q]})
 def test_approval_transitions(self):
  old=copy.deepcopy(self.new);new=copy.deepcopy(old);new['documents'][1]['status']='Approved'
  with self.assertRaises(p.PermissionDenied):p.authorize_is(self.perms,old,new)
  new['documents'][1]['status']='Pending';p.authorize_is(self.perms,old,new)
  old=copy.deepcopy(new);new['documents'][1]['status']='Approved';p.authorize_is(self.perms,old,new)
  new['documents'][1]['lines'][0]['qty']=9
  with self.assertRaises(p.PermissionDenied):p.authorize_is(self.perms,old,new)
 def test_pending_not_editable(self):
  old=copy.deepcopy(self.new);old['documents'][1]['status']='Pending';new=copy.deepcopy(old);new['documents'][1]['lines'][0]['qty']=9
  with self.assertRaises(p.PermissionDenied):p.authorize_is(self.perms,old,new)
 def batch_fixture(self):
  old={'products':[{'id':'P1','brand':'A','unit':'kit'}],'documents':[]}
  for id,qty in [('q1',2),('q2',3)]:old['documents'].append({'id':id,'kind':'waiting-purchase','status':'Approved','currency':'THB','lines':[{'productId':'P1','qty':qty,'price':10}]})
  pr={'id':'batch','kind':'purchase-request','status':'Draft','currency':'THB','sourceId':'q1','sourceIds':['q1','q2'],'purchasingBrand':'A','sourceAllocations':[{'requestId':'q1','requestLine':0,'productId':'P1','unit':'kit','qty':2},{'requestId':'q2','requestLine':0,'productId':'P1','unit':'kit','qty':3}],'lines':[{'productId':'P1','unit':'kit','qty':5,'price':10}]}
  new=copy.deepcopy(old);new['documents'].append(pr);return old,new
 def test_batch_consolidation(self):
  old,new=self.batch_fixture();p.authorize_is(self.perms,old,new)
 def test_batch_duplicate_reservation(self):
  old,new=self.batch_fixture();new['documents'].append(dict(copy.deepcopy(new['documents'][-1]),id='batch2'))
  with self.assertRaises(p.PermissionDenied):p.authorize_is(self.perms,old,new)
 def test_batch_wrong_quantity(self):
  old,new=self.batch_fixture();new['documents'][-1]['lines'][0]['qty']=6
  with self.assertRaises(p.PermissionDenied):p.authorize_is(self.perms,old,new)
 def test_batch_currency(self):
  old,new=self.batch_fixture();new['documents'][-1]['currency']='USD'
  with self.assertRaises(p.PermissionDenied):p.authorize_is(self.perms,old,new)
 def test_batch_source_approval(self):
  old,new=self.batch_fixture();old['documents'][0]['status']='Pending';new['documents'][0]['status']='Pending'
  with self.assertRaises(p.PermissionDenied):p.authorize_is(self.perms,old,new)
 def test_finance_visibility(self):
  d={'documents':[{'id':k,'kind':k} for k in ['invoice','credit-note','debit-note','payment-receipt','quotation']]}
  visible=json.loads(p.read_filter({'is_view','is.outstanding.view'},'biomed_is_v50_transactions',json.dumps(d)))
  self.assertEqual(len(visible['documents']),4)
 def test_manual_create(self):
  for module in ['pipeline','tenders']:
   p.authorize_portal(self.perms,{module:[]},{module:[{'id':'m','value':100,'amount':100,'probability':50}]})
   with self.assertRaises(p.PermissionDenied):p.authorize_portal(self.perms,{module:[]},{module:[{'id':'m','value':-1,'amount':-1}]})
 def test_migration_preserves_existing_grants(self):
  data={'minutesAccessV1':True,'permissionCatalogVersion':1,'isPermissionsSeeded':True,'budgetPermissionsSeeded':True,'roles':{'System Admin':['is_view'],'Custom':['is_view','is.customer-order.view']}}
  p.migrate_portal(data);self.assertIn('is.waiting-purchase.create',data['roles']['System Admin']);self.assertEqual(set(data['roles']['Custom']),{'is_view','is.customer-order.view'});self.assertFalse(p.migrate_portal(data))
if __name__=='__main__':unittest.main()
