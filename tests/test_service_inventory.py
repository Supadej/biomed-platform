import sys,json,unittest,copy,io
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import test_crm as fixtures
import serve,service_inventory as si,instrument_service as f,permissions_policy as policy,crm_api as crm
class Inventory(unittest.TestCase):
 def setUp(self):
  fixtures.CRM.setUp(self);self.engineer=('second','two@example.invalid','Second','Service Engineer','u2')
  with serve.connect() as c:
   p=copy.deepcopy(self.portal);p['users'][1]['role']='Service Engineer';p['roles']['Service Engineer']=list(self.perms);c.execute("UPDATE workspace SET value=? WHERE key='biomed_portal_v33_clean'",(json.dumps(p),));crm.bind_users(c)
   data=copy.deepcopy(self.isdata);data['warehouses']=['Main'];data['movements']=[{'id':'receipt','productId':'p1','warehouse':'Main','lot':'LOT','expiry':'2027-12-31','change':10}];c.execute("UPDATE workspace SET value=? WHERE key='biomed_is_v50_transactions'",(json.dumps(data),));serve.project(c,json.dumps(data))
   self.inst=f.save(c,self.actor,self.perms,{'kind':'instruments','serial':'QA-INVENTORY-1'});self.part=f.save(c,self.actor,self.perms,{'kind':'parts','productId':'p1'})
 tearDown=fixtures.CRM.tearDown
 def call(self,c,body=None,actor=None,perms=None):
  c.execute('SAVEPOINT inventory_test')
  try:r=si.dispatch(c,actor or self.engineer,self.perms if perms is None else perms,body);c.execute('RELEASE inventory_test');return r
  except Exception:c.execute('ROLLBACK TO inventory_test');c.execute('RELEASE inventory_test');raise
 def request(self,c,qty=5,kind='Request'):
  ident=self.call(c,{'action':'request','kind':kind,'lines':[{'productId':'p1','warehouse':'Main','lot':'LOT','expiry':'2027-12-31','qty':qty}]})['id'];return next(r for r in self.call(c)['requests'] if r['id']==ident)
 def approve(self,c,r):return self.call(c,{'action':'approve','id':r['id'],'version':r['version']},self.actor)
 def central(self,c):return sum(m['change'] for m in si.warehouse_state(c)['movements'] if m.get('productId')=='p1')
 def qty(self,c):return sum(x['qty'] for x in si.balances(c) if x['engineer']=='u2' and x['productId']=='p1')
 def job(self,c,qty=2,old=None,**extra):
  r={**(old or {}),'kind':'jobs','instrumentId':self.inst,'engineer':'u2','date':'2026-10-28','description':'Repair report','partsUsed':[{'partId':self.part,'qty':qty,'unitCost':100}],**extra};ident=f.save(c,self.engineer,self.perms,r);return next(x for x in f.rows(c) if x['id']==ident)
 def test_approval_issue_consumption_idempotent_edit_and_return(self):
  with serve.connect() as c:
   req=self.request(c);self.assertEqual(self.central(c),10);self.assertEqual(self.qty(c),0)
   with self.assertRaises(policy.PermissionDenied):self.call(c,{'action':'approve','id':req['id'],'version':req['version']})
   self.approve(c,req);self.assertEqual(self.central(c),5);self.assertEqual(self.qty(c),5)
   with self.assertRaises(ValueError):self.approve(c,req)
   job=self.job(c);self.assertEqual(self.qty(c),3);self.assertEqual(self.central(c),5)
   job=self.job(c,old=job);self.assertEqual(self.qty(c),3)
   job=self.job(c,qty=3,old=job);self.assertEqual(self.qty(c),2)
   job=self.job(c,qty=1,old=job);self.assertEqual(self.qty(c),4)
   ret=self.request(c,qty=2,kind='Return');self.approve(c,ret);self.assertEqual(self.qty(c),2);self.assertEqual(self.central(c),7)
   self.assertEqual(sum(x['qty'] for x in si.entries(c) if x['reference']==job['id']),-1)
 def test_negative_stock_and_stale_request_blocked(self):
  with serve.connect() as c:
   req=self.request(c,20)
   with self.assertRaises(ValueError):self.approve(c,req)
   self.assertEqual(self.central(c),10);self.assertEqual(self.qty(c),0)
   r=self.request(c,5)
   with self.assertRaises(ValueError):self.call(c,{'action':'approve','id':r['id'],'version':0},self.actor)
   self.approve(c,r)
   with self.assertRaises(ValueError):self.job(c,qty=6)
   self.assertEqual(self.qty(c),5)
 def test_explicit_custody_owner_when_service_engineer_has_no_stock(self):
  with serve.connect() as c:
   self.approve(c,self.request(c,5))
   with self.assertRaisesRegex(ValueError,'0.*usable'):
    f.save(c,self.actor,self.perms,{'kind':'jobs','instrumentId':self.inst,'engineer':'u1','date':'2026-10-28','partsUsed':[{'partId':self.part,'qty':2,'unitCost':10}]})
   ident=f.save(c,self.actor,self.perms,{'kind':'jobs','instrumentId':self.inst,'engineer':'u1','inventoryEngineer':'u2','date':'2026-10-28','partsUsed':[{'partId':self.part,'qty':2,'unitCost':10}]})
   self.assertEqual(self.qty(c),3)
   job=next(r for r in f.rows(c) if r['id']==ident);f.save(c,self.actor,self.perms,job);self.assertEqual(self.qty(c),3)
   with self.assertRaises(policy.PermissionDenied):
    f.save(c,self.actor,self.perms-{'is.service-inventory.approve'},{'kind':'jobs','instrumentId':self.inst,'engineer':'u1','inventoryEngineer':'u2','date':'2026-10-28','partsUsed':[{'partId':self.part,'qty':1,'unitCost':10}]})
 def test_pending_return_rechecks_current_balance(self):
  with serve.connect() as c:
   self.approve(c,self.request(c,5));ret=self.request(c,5,'Return');self.job(c,qty=2)
   with self.assertRaises(ValueError):self.approve(c,ret)
   self.assertEqual(self.qty(c),3);self.assertEqual(self.central(c),5)
 def test_multi_line_approval_is_atomic_and_stock_postings_protected(self):
  with serve.connect() as c:
   r=self.request(c,6);row=c.execute('SELECT payload FROM service_inventory_requests WHERE id=?',(r['id'],)).fetchone();payload=json.loads(row[0]);payload['lines'].append({**payload['lines'][0],'index':1});c.execute('UPDATE service_inventory_requests SET payload=? WHERE id=?',(json.dumps(payload),r['id']))
   with self.assertRaises(ValueError):self.approve(c,r)
   self.assertEqual(self.central(c),10);self.assertEqual(self.qty(c),0)
   normal=self.request(c,2);self.approve(c,normal);data=si.warehouse_state(c);modified=copy.deepcopy(data);modified['movements']=[m for m in modified['movements'] if not m.get('serviceInventory')]
   with self.assertRaises(policy.PermissionDenied):policy.authorize_is(self.perms,data,modified)
 def test_scope_rejection_and_historical_baseline(self):
  with serve.connect() as c:
   req=self.request(c)
   basic=self.perms-{'is.service-inventory.approve'}
   other=si.dispatch(c,self.actor,basic);self.assertEqual(other['requests'],[])
   with self.assertRaises(policy.PermissionDenied):self.call(c,{'action':'request','kind':'Request','engineer':'u1','lines':req['lines']},perms=basic)
   with self.assertRaises(ValueError):self.call(c,{'action':'reject','id':req['id'],'version':1},self.actor)
   self.call(c,{'action':'reject','id':req['id'],'version':1,'reason':'No replenishment needed'},self.actor);self.assertEqual(self.qty(c),0)
   historical={'id':'historical-test','kind':'jobs','instrumentId':self.inst,'engineer':'u2','partsUsed':[{'partId':self.part,'productId':'p1','qty':3,'unitCost':10}]};c.execute('INSERT INTO fse_records VALUES(?,?,?,1)',(historical['id'],'jobs',json.dumps(historical)));si.initialize(c)
   f.save(c,self.engineer,self.perms,{**historical,'version':1,'description':'Historical correction'});self.assertEqual(self.qty(c),0)
 def test_job_calendar_and_pdf_endpoint_auth(self):
  import service_report
  with serve.connect() as c:
   ident=f.save(c,self.engineer,self.perms,{'kind':'jobs','instrumentId':self.inst,'engineer':'u2','date':'2026-10-28','description':'Scheduled visit','calendarEnabled':True,'calendarDate':'2026-10-29'})
   r=next(x for x in f.rows(c) if x['id']==ident);event=crm.raw(c,'Events',r['calendarEventId']);self.assertIn(r['jobNo'],event['Title']);self.assertIn('2026-10-29',event['Title'])
   f.save(c,self.engineer,self.perms,{**r,'scheduledDate':'2026-10-30','calendarDate':'2026-10-29'});event2=crm.raw(c,'Events',r['calendarEventId']);self.assertIn('2026-10-29',event2['Title']);self.assertEqual(event['Id'],event2['Id'])
   r=next(x for x in f.rows(c) if x['id']==ident);f.save(c,self.engineer,self.perms,{**r,'calendarEnabled':False});self.assertIsNone(crm.raw(c,'Events',event['Id']))
  class H:
   path='/api/service-report?id='+ident
   def reply(self,status,value):return status,value
  self.assertEqual(service_report.handle(H(),serve.connect,lambda h:None,lambda a:self.perms)[0],401)
 def test_expired_and_quarantined_warehouse_stock_is_blocked(self):
  with serve.connect() as c:
   data=si.warehouse_state(c);data['quarantines']=[{'productId':'p1','lot':'LOT','status':'Quarantined'}];c.execute('UPDATE workspace SET value=? WHERE key=?',(json.dumps(data),si.KEY));r=self.request(c)
   with self.assertRaisesRegex(ValueError,'Quarantined'):self.approve(c,r)
   data['quarantines']=[];data['movements'][0]['expiry']='2000-01-01';c.execute('UPDATE workspace SET value=? WHERE key=?',(json.dumps(data),si.KEY));ident=self.call(c,{'action':'request','kind':'Request','lines':[{'productId':'p1','warehouse':'Main','lot':'LOT','expiry':'2000-01-01','qty':1}]})['id'];req=next(r for r in self.call(c)['requests'] if r['id']==ident)
   with self.assertRaisesRegex(ValueError,'Expired'):self.approve(c,req)
   self.assertEqual(self.central(c),10);self.assertEqual(self.qty(c),0)
 def test_role_migration(self):
  p={'roles':{'Service Engineer':['service.edit','service.jobs.view','service.jobs.create'],'Warehouse':['is.stock-transfer.approve'],'Employee':[]},'permissionCatalogVersion':14};policy.migrate_portal(p)
  self.assertIn('is.service-inventory.consume',p['roles']['Service Engineer']);self.assertNotIn('is.service-inventory.approve',p['roles']['Service Engineer']);self.assertIn('is.service-inventory.approve',p['roles']['Warehouse']);self.assertNotIn('is.service-inventory.view',p['roles']['Employee'])
if __name__=='__main__':unittest.main()
