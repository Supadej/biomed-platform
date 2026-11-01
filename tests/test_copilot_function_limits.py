import unittest,sys,json,sqlite3,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import copilot_access as access,copilot_functions
class Limits(unittest.TestCase):
 def setUp(self):
  self.c=sqlite3.connect(':memory:');access.init(self.c);self.actor=('a','a@test','A','Employee','u1')
  self.perms={'ai.internal.use','tasks','requests','crm_view','crm.events.view','crm.events.create','is_view','is.quotation.view'}
 def tearDown(self):self.c.close()
 def test_role_user_and_personal_intersection(self):
  self.c.execute('INSERT INTO copilot_role_access VALUES(?,?)',('Employee',json.dumps({'functions':{'portal.tasks':False},'company_key':False})))
  access.save(self.c,self.actor,'a','self',{'functions':{'portal.tasks':True,'portal.requests':False},'company_key':True})
  effective=access.state(self.c,self.actor,self.perms,False)['effective']
  self.assertFalse(effective['functions']['portal.tasks']);self.assertFalse(effective['functions']['portal.requests'])
  self.assertFalse(effective['company_key']);self.assertTrue(effective['functions']['is.quotation'])
 def test_cannot_grant_missing_base_permission(self):
  access.save(self.c,self.actor,'a','self',{'functions':{'is.invoice':True}})
  effective=access.state(self.c,self.actor,self.perms,False)['effective']
  self.assertFalse(effective['functions']['is.invoice'])
 def test_calendar_function_disable_blocks_tools(self):
  access.save(self.c,self.actor,'a','self',{'calendar_read':True,'calendar_draft':True,'functions':{'portal.calendar':False}})
  effective=access.state(self.c,self.actor,self.perms,False)['effective']
  self.assertFalse(effective['calendar_read']);self.assertFalse(effective['calendar_draft'])
 def test_function_masks_remove_summary_data(self):
  self.c.execute('CREATE TABLE workspace(key TEXT,value TEXT)')
  self.c.execute('INSERT INTO workspace VALUES(?,?)',('biomed_portal_v33_clean',json.dumps({'tasks':[{'userId':'u1'}],'requests':[{'userId':'u1'}]})))
  result=access.snapshot(self.c,self.actor,self.perms,'portal',{'portal.tasks':False,'portal.requests':True})
  self.assertNotIn('tasks',result);self.assertEqual(result['requests']['own_record_count'],1)
 def test_catalog_is_complete_and_unsupported_disabled(self):
  rows=copilot_functions.catalog();ids=[r['id'] for r in rows]
  self.assertEqual(len(ids),len(set(ids)))
  for key in ['portal.expenses','portal.payments','portal.hrprofiles','portal.calendar','crm.leads','crm.tickets','crm.activities','is.purchase-order','is.invoice','budget.products','budget.ledger']:
   self.assertIn(key,ids)
  self.assertTrue(all(r["connected"] for r in rows))
 def test_validation_and_role_revocation(self):
  with self.assertRaises(ValueError):access.validate({'functions':{'arbitrary.sql':True}})
  with self.assertRaises(ValueError):access.validate({'functions':{'portal.tasks':'true'}})
  access.save(self.c,self.actor,'a','self',{'functions':{'portal.tasks':True}})
  self.assertFalse(access.state(self.c,self.actor,set(),False)['effective']['functions']['portal.tasks'])
if __name__=='__main__':unittest.main()
