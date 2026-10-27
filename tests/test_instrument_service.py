import unittest,sqlite3,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import instrument_service as f
class ServiceTest(unittest.TestCase):
 def setUp(self):
  self.c=sqlite3.connect(':memory:');f.initialize(self.c);self.actor=('a','e','Admin','System Admin','u');self.perms={'service.view','service.edit','service.manage'}|{f'service.{k}.{a}' for k in f.KINDS for a in ['view','create','edit','export','print']}
  self.i=f.save(self.c,self.actor,self.perms,dict(kind='instruments',serial='00069',location='HQ'))
 def test_entity_permission_denied(self):
  restricted={'service.view','service.edit','service.jobs.view','service.jobs.create'}
  with self.assertRaises(Exception):f.save(self.c,self.actor,restricted,dict(kind='instruments',serial='NEW'))
 def test_type_change_denied(self):
  r=f.rows(self.c)[0];r['kind']='parts'
  with self.assertRaises(ValueError):f.save(self.c,self.actor,self.perms,r)
 def test_presets(self):
  import permissions_policy as p
  data={'roles':{'Employee':[],'Service Engineer':['custom.keep']},'permissionCatalogVersion':p.CATALOG['version']-1}
  p.migrate_portal(data)
  self.assertEqual(data['roles']['Service Engineer'],['custom.keep'])
  self.assertIn('service.instruments.edit',data['roles']['Service Manager'])
  self.assertNotIn('service.jobs.edit',data['roles']['Service Viewer'])
 def test_serial_unique(self):
  with self.assertRaises(ValueError):f.save(self.c,self.actor,self.perms,dict(kind='instruments',serial='00069'))
 def test_stale(self):
  r=f.rows(self.c)[0];f.save(self.c,self.actor,self.perms,r)
  with self.assertRaises(ValueError):f.save(self.c,self.actor,self.perms,r)
 def test_permission(self):
  with self.assertRaises(Exception):f.save(self.c,self.actor,{'service.view'},dict(kind='parts',name='Pump'))
 def test_orphan(self):
  with self.assertRaises(ValueError):f.save(self.c,self.actor,self.perms,dict(kind='jobs',instrumentId='missing'))
 def test_movement(self):
  f.save(self.c,self.actor,self.perms,dict(kind='movements',instrumentId=self.i,date='2026-10-28',toLocation='Hospital'))
  self.assertEqual(next(r for r in f.rows(self.c) if r['id']==self.i)['location'],'Hospital')
 def test_completion(self):
  with self.assertRaises(ValueError):f.save(self.c,self.actor,self.perms,dict(kind='jobs',instrumentId=self.i,status='Completed'))
  f.save(self.c,self.actor,self.perms,dict(kind='jobs',instrumentId=self.i,status='Completed',jobType='Preventive Maintenance',date='2026-10-28',engineer='FSE',description='PM passed',nextMaintenance='2027-10-28'))
  self.assertEqual(next(r for r in f.rows(self.c) if r['id']==self.i)['maintenanceDue'],'2027-10-28')
 def test_bad_values(self):
  for qty in ['NaN',-1,0]:
   with self.assertRaises(ValueError):f.save(self.c,self.actor,self.perms,dict(kind='replacements',instrumentId=self.i,qty=qty))
 def test_history_import(self):
  seed=json.loads((Path(f.__file__).parent/'reference/service-import.json').read_text())
  c=sqlite3.connect(':memory:');f.initialize(c)
  for r in seed['records']:f.save(c,self.actor,self.perms,r,True)
  self.assertEqual(len(f.rows(c)),len(seed['records']))
  self.assertEqual(len({r['id'] for r in seed['records']}),len(seed['records']))
if __name__=='__main__':unittest.main()
