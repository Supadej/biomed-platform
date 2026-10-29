import unittest,sqlite3,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import instrument_service as f
class ServiceTest(unittest.TestCase):
 def setUp(self):
  self.c=sqlite3.connect(':memory:');f.initialize(self.c);self.actor=('a','e','Admin','System Admin','u');self.perms={'service.view','service.edit','service.manage'}|{f'service.{k}.{a}' for k in f.KINDS for a in ['view','create','edit','export','print']}
  import service_catalog
  service_catalog.save_setup(self.c,self.perms,dict(version=service_catalog.setup(self.c)['version'],brands=['Demo'],models=[{'brand':'Demo','name':'Analyzer'}],locations=['HQ','Hospital']))
  self.c.executescript("CREATE TABLE accounts(user_id TEXT,name TEXT,role TEXT,disabled INTEGER); CREATE TABLE workspace(key TEXT,value TEXT); CREATE TABLE crm_identity(portal_user_id TEXT,crm_user_id INTEGER);")
  self.c.execute("INSERT INTO accounts VALUES('FSE','Engineer Name','System Admin',0)")
  self.i=f.save(self.c,self.actor,self.perms,dict(kind='instruments',serial='00069',location='HQ'))
 def test_entity_permission_denied(self):
  restricted={'service.view','service.edit','service.jobs.view','service.jobs.create'}
  with self.assertRaises(Exception):f.save(self.c,self.actor,restricted,dict(kind='instruments',serial='NEW'))
 def test_type_change_denied(self):
  r=f.rows(self.c)[0];r['kind']='parts'
  with self.assertRaises(ValueError):f.save(self.c,self.actor,self.perms,r)
 def test_presets(self):
  import permissions_policy as p
  data={'roles':{'Employee':[],'Service Engineer':['custom.keep']},'permissionCatalogVersion':13}
  p.migrate_portal(data)
  self.assertEqual(set(data['roles']['Service Engineer']),{'custom.keep','minutes','portal.minutes.view','portal.minutes.acknowledge'}|{'user_profile','portal.user_profile.view','portal.user_profile.edit','portal.user_profile.password','user_library','portal.user_library.view'})
  self.assertIn('service.instruments.edit',data['roles']['Service Manager'])
  self.assertNotIn('service.jobs.edit',data['roles']['Service Viewer'])
 def test_serial_link(self):
  r=f.rows(self.c)[0];r['serialAlias']='SN00069';f.save(self.c,self.actor,self.perms,r)
  self.assertEqual(f.match_instruments(self.c,' sn00069 ')[0]['id'],self.i)
  self.assertEqual(f.match_instruments(self.c,'00069')[0]['id'],self.i)
  self.assertEqual(f.match_instruments(self.c,'69'),[])
  self.assertEqual(f.match_instruments(self.c,''),[])
 def test_serial_ambiguous_alias(self):
  f.save(self.c,self.actor,self.perms,dict(kind='instruments',serial='Other',serialAlias='00069'))
  self.assertEqual(len(f.match_instruments(self.c,'00069')),2)
 def test_reverse_tickets_permissions(self):
  self.assertEqual(f.linked_tickets(self.c,self.actor,{'service.view'}),[])
 def test_seed_idempotent_preserves_edits(self):
  c=sqlite3.connect(':memory:');f.initialize(c);f.seed_workbook(c)
  first=f.rows(c);count=len(first);r=next(x for x in first if x['kind']=='instruments');r['comment']='Operational edit';f.save(c,self.actor,self.perms,r)
  f.seed_workbook(c)
  self.assertEqual(len(f.rows(c)),count)
  self.assertEqual(next(x for x in f.rows(c) if x['id']==r['id'])['comment'],'Operational edit')
 def test_seed_reuses_existing_serial(self):
  c=sqlite3.connect(':memory:');f.initialize(c)
  ident=f.save(c,self.actor,self.perms,dict(kind='instruments',serial='00069',comment='Keep existing'))
  f.seed_workbook(c)
  self.assertEqual(len(f.match_instruments(c,'00069')),1)
  self.assertEqual(f.match_instruments(c,'00069')[0]['comment'],'Keep existing')
  self.assertTrue(any(x.get('instrumentId')==ident for x in f.rows(c) if x['kind']=='jobs'))
 def column_request(self,actor,body=None,perms=None):
  import io
  self.c.commit()
  class H:
   def reply(self,status,value):self.response=(status,value);return self.response
  h=H();raw=json.dumps(body).encode() if body is not None else b'';h.headers={'Content-Length':str(len(raw))};h.rfile=io.BytesIO(raw)
  return f.handle(h,'POST' if body is not None else 'GET',lambda:self.c,lambda h:actor,lambda a:self.perms if perms is None else perms,lambda h:True)
 def test_column_preferences_isolated(self):
  body={'action':'columns','kind':'jobs','columns':[{'key':'jobNo','label':'Work order'},{'key':'status','label':'Stage'}]}
  self.assertEqual(self.column_request(self.actor,body)[0],200)
  self.assertEqual(self.column_request(self.actor)[1]['columnPreferences']['jobs'],body['columns'])
  other=('other','e','Other','Employee','other')
  self.assertEqual(self.column_request(other)[1]['columnPreferences'],{})
 def test_column_preferences_validation(self):
  for cols in [[],[{'key':'secret','label':'Secret'}],[{'key':'jobNo','label':''}],[{'key':'jobNo','label':'A'},{'key':'jobNo','label':'B'}]]:
   self.assertEqual(self.column_request(self.actor,{'action':'columns','kind':'jobs','columns':cols})[0],400)
 def test_column_preferences_permission(self):
  self.assertEqual(self.column_request(self.actor,{'action':'columns','kind':'jobs','columns':[{'key':'jobNo','label':'Job'}]}, {'service.view'})[0],403)
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
