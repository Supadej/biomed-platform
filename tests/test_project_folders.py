import unittest,sqlite3,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import crm_api as crm,project_folders as folders,permissions_policy as policy
class Folders(unittest.TestCase):
 def setUp(self):
  self.c=sqlite3.connect(':memory:');crm.initialize(self.c);self.actor=('a','a@test','A','System Admin','u1');self.perms={p['key'] for p in policy.CATALOG['permissions']}
  self.project=crm.insert(self.c,'Projects',{'Name':'Project A'})['Id'];self.stage=crm.insert(self.c,'ProjectPipeline',{'Name':'Open','ProjectId':self.project})['Id'];self.activity=crm.insert(self.c,'ProjectActivity',{'Name':'Task','MainUserId':1,'ProjectId':self.project,'ProjectPipelineId':self.stage})['Id']
  self.other=crm.insert(self.c,'Projects',{'Name':'Keep B'})['Id']
 def tearDown(self):self.c.close()
 def payload(self):return {'id':self.project,'version':1,'stages':1,'activities':1,'confirm_children':True}
 def test_folder_counts_and_atomic_delete(self):
  self.assertEqual(folders.listing(self.c,self.perms,1)[0]['activities'],1)
  crm.insert(self.c,'ProjectActivityUsers',{'ProjectActivityId':self.activity,'UserId':1})
  folders.delete(self.c,self.actor,self.perms,1,self.payload())
  for entity,id in [('Projects',self.project),('ProjectPipeline',self.stage),('ProjectActivity',self.activity)]:self.assertIsNone(crm.raw(self.c,entity,id))
  self.assertTrue(crm.raw(self.c,'Projects',self.other));self.assertEqual(crm.rows(self.c,'ProjectActivityUsers'),[])
 def test_denied_child_permission_and_changed_counts(self):
  with self.assertRaises(policy.PermissionDenied):folders.delete(self.c,self.actor,self.perms-{'crm.activities.delete'},1,self.payload())
  with self.assertRaises(ValueError):folders.delete(self.c,self.actor,self.perms,1,{**self.payload(),'stages':0})
  self.assertTrue(crm.raw(self.c,'ProjectActivity',self.activity))
 def test_external_reference_rolls_back_all_children(self):
  crm.insert(self.c,'Leads',{'LeadName':'Keep linked opportunity','ProjectID':self.project})
  with self.assertRaises(ValueError):folders.delete(self.c,self.actor,self.perms,1,self.payload())
  self.assertTrue(crm.raw(self.c,'Projects',self.project));self.assertTrue(crm.raw(self.c,'ProjectPipeline',self.stage));self.assertTrue(crm.raw(self.c,'ProjectActivity',self.activity))
if __name__=='__main__':unittest.main()
