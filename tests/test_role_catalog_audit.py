import unittest,json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import permissions_policy as policy,crm_api
ROOT=Path(__file__).resolve().parents[1]
class RoleAudit(unittest.TestCase):
 def test_all_literal_permission_checks_registered(self):
  known={p['key'] for p in policy.CATALOG['permissions']};missing={}
  for file in ROOT.iterdir():
   if file.suffix not in ('.py','.js','.html'):continue
   for key in re.findall(r'''['"]((?:portal|crm|is|budget|ai)\.[a-zA-Z_][a-zA-Z0-9_.-]+)['"]''',file.read_text()):
    if key.rsplit('.',1)[-1] in ('view','edit','create','delete','approve','reject','use','manage','export','import','submit','cancel','reconcile','upload','assign','view_all') and key not in known:missing.setdefault(key,[]).append(file.name)
  self.assertEqual(missing,{})
 def test_crm_entities_actions_and_app_modules_registered(self):
  known={p['key'] for p in policy.CATALOG['permissions']}
  for module in crm_api.MODULES.values():
   self.assertIn(module,policy.CATALOG['crmModules'])
  for module,item in policy.CATALOG['crmModules'].items():
   for action in item['actions']:self.assertIn('crm.'+module+'.'+action,known)
  for module in policy.CATALOG['transactions']:self.assertIn('is.'+module+'.view',known)
  for module in policy.CATALOG['budgetTabs']:self.assertIn('budget.'+module+'.view',known)
  for module in policy.CATALOG['portalModules']:self.assertIn(module,known)
  self.assertEqual(len(known),len(policy.CATALOG['permissions']))
 def test_ai_editor_rows_distinguish_independent_permissions(self):
  rows=[p for p in policy.CATALOG['permissions'] if p['key'].startswith('ai.')]
  self.assertEqual(len({p['module'] for p in rows}),len(rows))
 def test_followup_uses_real_permissions_and_pipeline_conversion(self):
  old={'isCRM':{'q1':{'outcome':'Monitoring','lead':False}}}
  new={'isCRM':{'q1':{'outcome':'Lost','reason':'Budget deferred','lead':False}}}
  policy.authorize_portal({'tenders','portal.tenders.edit'},old,new,'u1')
  with self.assertRaises(policy.PermissionDenied):policy.authorize_portal({'tenders'},old,new,'u1')
  new['isCRM']['q1']={'outcome':'Won','reason':'Approved by customer','lead':True}
  with self.assertRaises(policy.PermissionDenied):policy.authorize_portal({'tenders','portal.tenders.edit'},old,new,'u1')
  policy.authorize_portal({'tenders','portal.tenders.edit','pipeline','portal.pipeline.edit'},old,new,'u1')
  with self.assertRaises(policy.PermissionDenied):policy.authorize_portal(set(),old,new,'u1')
 def test_hidden_followups_survive_restricted_save(self):
  old={'isCRM':{'hidden':{'lead':False,'reason':'Hidden tender'},'visible':{'lead':True}}}
  value=json.dumps(old);visible=json.loads(policy.read_filter({'pipeline'},'biomed_portal_v33_clean',value))
  self.assertNotIn('hidden',visible['isCRM']);self.assertIn('visible',visible['isCRM'])
  merged=json.loads(policy.merge_scope({'pipeline'},'biomed_portal_v33_clean',value,json.dumps(visible)))
  self.assertEqual(merged,old)
 def test_upgrade_preserves_existing_denials(self):
  d={'permissionCatalogVersion':9,'roles':{'Employee':['tasks'],'System Admin':[]},'isPermissionsSeeded':True,'budgetPermissionsSeeded':True}
  policy.migrate_portal(d)
  self.assertEqual(set(d['roles']['Employee']),{'tasks','minutes','portal.minutes.view','portal.minutes.acknowledge'}|{'user_profile','portal.user_profile.view','portal.user_profile.edit','portal.user_profile.password','user_library','portal.user_library.view'});self.assertNotIn('portal.minutes.create',d['roles']['Employee']);self.assertNotIn('is.service-inventory.approve',d['roles']['Employee']);self.assertIn('ai.settings.manage',d['roles']['System Admin'])
if __name__=='__main__':unittest.main()
