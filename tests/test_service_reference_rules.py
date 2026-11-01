import unittest,sqlite3,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import instrument_service as f,service_catalog as refs
class References(unittest.TestCase):
 def setUp(self):
  self.c=sqlite3.connect(':memory:');f.initialize(self.c)
  self.c.executescript("CREATE TABLE masters(category TEXT,id TEXT,payload TEXT); CREATE TABLE accounts(user_id TEXT,name TEXT,role TEXT,disabled INTEGER); CREATE TABLE workspace(key TEXT,value TEXT); CREATE TABLE crm_identity(portal_user_id TEXT,crm_user_id INTEGER);")
  self.c.execute("INSERT INTO accounts VALUES('eng','Engineer Name','System Admin',0)");self.c.execute("INSERT INTO masters VALUES('products','p1',?)",(json.dumps({'name':'Approved part','sku':'SKU1'}),))
  self.actor=('a','','Admin','System Admin','a');self.perms={'service.view','service.edit','service.manage','service.references.view'}|{f'service.{k}.{a}' for k in f.KINDS for a in ['view','create','edit']}
  self.config=refs.save_setup(self.c,self.perms,{'version':refs.setup(self.c)['version'],'brands':['Brand A','Brand B'],'models':[{'brand':'Brand A','name':'Model A'},{'brand':'Brand B','name':'Model B'}],'locations':['HQ','Hospital']})
  self.inst=f.save(self.c,self.actor,self.perms,{'kind':'instruments','serial':'001','brand':'Brand A','model':'Model A','location':'HQ'})
 def test_controlled_values_and_legacy_preservation(self):
  for values in [{'brand':'typo'},{'brand':'Brand A','model':'Model B'},{'location':'Unknown'}]:
   with self.assertRaises(ValueError):f.save(self.c,self.actor,self.perms,dict(kind='instruments',serial='other',**values))
  config=dict(self.config,locations=['Hospital']);refs.save_setup(self.c,self.perms,config)
  old=next(x for x in f.rows(self.c) if x['id']==self.inst);old['comment']='Preserved old location';f.save(self.c,self.actor,self.perms,old)
 def test_reference_permissions_and_stale_settings(self):
  with self.assertRaises(Exception):refs.save_setup(self.c,{'service.view'},self.config)
  refs.save_setup(self.c,self.perms,self.config)
  with self.assertRaises(ValueError):refs.save_setup(self.c,self.perms,self.config)
 def test_is_parts_and_job_owned_lines(self):
  with self.assertRaises(ValueError):f.save(self.c,self.actor,self.perms,{'kind':'parts','catalogueNo':'manual','name':'manual'})
  part=f.save(self.c,self.actor,self.perms,{'kind':'parts','productId':'p1','name':'tampered','catalogueNo':'tampered','brand':'Brand A','model':'Model A'})
  declared=next(x for x in f.rows(self.c) if x['id']==part);self.assertEqual(declared['name'],'Approved part');self.assertEqual(declared['catalogueNo'],'SKU1')
  with self.assertRaises(ValueError):f.save(self.c,self.actor,self.perms,{'kind':'parts','productId':'p1','brand':'Brand A','model':'Model A'})
  import service_inventory
  self.perms|={'is_view','is.service-inventory.view','is.service-inventory.consume','is.service-inventory.approve'}
  service_inventory.post(self.c,self.actor,'eng','p1','QA-LOT','2027-12-31',5,'Approved issue','QA')
  job=f.save(self.c,self.actor,self.perms,{'kind':'jobs','instrumentId':self.inst,'engineer':'eng','date':'2026-10-28','status':'Completed','description':'Completed repair','partsUsed':[{'partId':part,'qty':2,'unitCost':10}]})
  r=next(x for x in f.rows(self.c) if x['id']==job);self.assertRegex(r['jobNo'],r'^BMDS\d{2}-\d{2}-\d{2}/\d+$');self.assertEqual(r['engineerName'],'Engineer Name');self.assertEqual(r['partsUsed'][0]['productId'],'p1');self.assertTrue(r['completedAt'])
  self.assertEqual(len([x for x in f.rows(self.c) if x['kind']=='replacements']),0)
  with self.assertRaises(ValueError):f.save(self.c,self.actor,self.perms,dict(r,partsUsed=[{'partId':part,'qty':0,'unitCost':1}]))
 def test_engineers_and_locations_validated(self):
  with self.assertRaises(ValueError):f.save(self.c,self.actor,self.perms,{'kind':'jobs','instrumentId':self.inst,'engineer':'Not an employee'})
  with self.assertRaises(ValueError):f.save(self.c,self.actor,self.perms,{'kind':'movements','instrumentId':self.inst,'toLocation':'Typo','date':'2026-10-28'})
  self.c.execute("UPDATE accounts SET disabled=1 WHERE user_id='eng'");self.assertEqual(refs.engineers(self.c),[])
if __name__=='__main__':unittest.main()
