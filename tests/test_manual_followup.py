import unittest,sys,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import permissions_policy as p
class ManualFollowup(unittest.TestCase):
 def change(self,kind,fields,perms=None):
  old={kind:[{'id':'m1','employee':'u1','owner':'u1','amount':100,'value':100,'probability':50}]};new=copy.deepcopy(old);new[kind][0].update(fields)
  p.authorize_portal(perms if perms is not None else {kind,'portal.'+kind+'.edit'},old,new,'u1')
 def test_valid_followup_both_registers(self):
  for kind in ['pipeline','tenders']:
   for outcome in ['Monitoring','Follow-up','Won','Lost']:
    self.change(kind,{'outcome':outcome,'reason':'Decision recorded','followup':'Call next week'})
 def test_permission_validation_and_pipeline_flag(self):
  for kind in ['pipeline','tenders']:
   with self.assertRaises(p.PermissionDenied):self.change(kind,{'outcome':'Won','reason':''})
   with self.assertRaises(p.PermissionDenied):self.change(kind,{'outcome':'Unknown'})
   with self.assertRaises(p.PermissionDenied):self.change(kind,{'outcome':'Follow-up','followup':123})
   with self.assertRaises(p.PermissionDenied):self.change(kind,{'outcome':'Follow-up'},set())
  with self.assertRaises(p.PermissionDenied):self.change('tenders',{'lead':True})
  self.change('tenders',{'lead':True},{'tenders','pipeline','portal.tenders.edit','portal.pipeline.edit'})
