import unittest,json,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_ai_separation import Separation,ai
import copilot_access as access
class Access(Separation):
 def test_self_cannot_elevate_role(self):
  d=self.call('/api/ai/internal/access',{'modules':['portal','budget','is','developer']},self.user,['ai.internal.use'])[1]
  self.assertEqual(d['effective']['modules'],['portal'])
  self.assertEqual(self.call('/api/ai/internal/access')[0],401)
  self.assertEqual(self.call('/api/ai/admin/user-access',{},self.user)[0],403)
 def test_admin_ceiling_blocks_direct_requests(self):
  self.config(internal_enabled=True)
  with self.connect() as c:access.save(c,self.admin,'b','admin',{'enabled':False})
  self.call('/api/ai/internal/access',{'enabled':True},self.user,['ai.internal.use'])
  for path in ('history','clear','send','models','key'):
   data=None if path=='history' else {'message':'Hi','key':'sk-test'}
   self.assertEqual(self.call('/api/ai/internal/'+path,data,self.user,['ai.internal.use'])[0],403,path)
 def test_user_narrows_own_modules(self):
  self.config(internal_enabled=True)
  self.call('/api/ai/internal/access',{'modules':['portal']},self.user,['ai.internal.use','budget_view'])
  self.assertEqual(self.call('/api/ai/internal/history?module=budget',actor=self.user,perms=['ai.internal.use','budget_view'])[0],403)
  self.assertEqual(self.call('/api/ai/internal/history?module=portal',actor=self.user,perms=['ai.internal.use'])[0],200)
 def test_summary_default_off_and_key_ceiling(self):
  self.config(internal_enabled=True,internal_company_key=True)
  d=self.call('/api/ai/internal/access',actor=self.user,perms=['ai.internal.use'])[1]
  self.assertFalse(d['effective']['share_summary'])
  with self.connect() as c:access.save(c,self.admin,'b','admin',{'company_key':False})
  with patch.object(ai,'internal_answer') as remote:
   self.assertEqual(self.call('/api/ai/internal/send',{'message':'Hi','key_source':'company'},self.user,['ai.internal.use'])[0],403)
   remote.assert_not_called()
 def test_snapshot_ownership_and_permissions(self):
  with self.connect() as c:
   c.execute('CREATE TABLE workspace(key TEXT PRIMARY KEY,value TEXT)')
   c.execute('INSERT INTO workspace VALUES(?,?)',('biomed_portal_v33_clean',json.dumps({'tasks':[{'userId':'u2','title':'private-own'},{'userId':'u1','title':'other-secret'}],'expenses':[{'userId':'u2','amount':123}]})))
   result=access.snapshot(c,self.user,{'tasks'},'portal')
   self.assertEqual(result['tasks']['own_record_count'],1)
   self.assertNotIn('expenses',result);self.assertNotIn('secret',json.dumps(result));self.assertNotIn('private-own',json.dumps(result))
 def test_budget_masks_are_retained(self):
  with self.connect() as c:
   c.execute('CREATE TABLE workspace(key TEXT PRIMARY KEY,value TEXT)')
   c.execute('INSERT INTO workspace VALUES(?,?)',('biomed_budget_v60_years',json.dumps({'years':{'2026':{'products':[{'id':'p','revenueActual':[100],'cogsActual':[80]}],'expenses':[]}}})))
   d=access.snapshot(c,self.user,{'budget.products.view'},'budget')['years'][0]
   self.assertEqual(d['revenue_actual'],100);self.assertEqual(d['cogs_actual'],0)
 def test_openai_summary_opt_in(self):
  self.config(internal_enabled=True,internal_company_key=True)
  self.call('/api/ai/internal/access',{'share_summary':True},self.admin)
  with self.connect() as c:c.execute('CREATE TABLE workspace(key TEXT PRIMARY KEY,value TEXT)')
  with patch.dict(ai.os.environ,{'BIOMED_INTERNAL_OPENAI_API_KEY':'sk-fake-only','BIOMED_INTERNAL_GEMINI_API_KEY':''}),patch.object(ai,'internal_answer',return_value='Summary') as remote:
   self.assertEqual(self.call('/api/ai/internal/send',{'message':'Count my tasks','key_source':'company'},self.admin)[0],200)
   self.assertIn('Server-generated read-only reference summary',remote.call_args.args[0][0][1])
  with self.connect() as c:
   stored=[r[0] for r in c.execute("SELECT content FROM ai_internal_messages WHERE sender='user'")]
   self.assertEqual(stored,['Count my tasks'])
 def test_invalid_preferences_rejected_and_audit(self):
  self.assertEqual(self.call('/api/ai/internal/access',{'enabled':'true'},self.user)[0],400)
  self.assertEqual(self.call('/api/ai/internal/access',{'modules':['unknown']},self.user)[0],400)
  self.call('/api/ai/internal/access',{'enabled':False},self.user)
  with self.connect() as c:self.assertEqual(c.execute('SELECT actor_id,target_id FROM copilot_access_audit').fetchone(),('b','b'))
if __name__=='__main__':unittest.main()
