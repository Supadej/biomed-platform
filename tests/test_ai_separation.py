import unittest,tempfile,sqlite3,json,io,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ai_chat_api as ai
class Handler:
 def __init__(self,path,data=None):
  self.path=path; raw=json.dumps(data or {}).encode();self.headers={'Content-Length':str(len(raw))};self.rfile=io.BytesIO(raw)
 def reply(self,status,data):self.result=(status,data);return self.result
class Separation(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.db=str(Path(self.tmp.name)/'test.db')
  with self.connect() as c:ai.init(c)
  self.admin=('a','admin@test','Admin','System Admin','u1');self.user=('b','user@test','User','Employee','u2')
 def tearDown(self):self.tmp.cleanup()
 def connect(self):return sqlite3.connect(self.db)
 def call(self,path,data=None,actor=None,perms=()):
  h=Handler(path,data);return ai.handle(h,'GET' if data is None else 'POST',self.connect,lambda h:actor,lambda a:set(perms),lambda h:True)
 def config(self,**values):return self.call('/api/ai/admin/config',values,self.admin)
 def test_independent_switches(self):
  self.config(website_enabled=False,internal_enabled=True)
  self.assertEqual(self.call('/api/ai/start',{})[0],403)
  self.assertTrue(self.call('/api/ai/internal/status?module=portal',actor=self.admin)[1]['enabled'])
  self.config(website_enabled=True,internal_enabled=False)
  self.assertEqual(self.call('/api/ai/start',{})[0],201)
  self.assertEqual(self.call('/api/ai/internal/send',{'message':'hi'},self.admin)[0],403)
 def test_admin_and_login(self):
  self.assertEqual(self.call('/api/ai/admin/config',{},self.user)[0],403)
  self.assertEqual(self.call('/api/ai/internal/history')[0],403)
  self.assertEqual(self.config(internal_enabled='yes')[0],400)
 def test_private_history_and_scope(self):
  self.config(internal_enabled=True)
  with self.connect() as c:c.execute("INSERT INTO ai_internal_messages(account_id,module,sender,content) VALUES('a','portal','user','private')")
  d=self.call('/api/ai/internal/history?module=portal',actor=self.user,perms=['ai.internal.use'])
  self.assertEqual(d[1]['items'],[])
  self.assertEqual(self.call('/api/ai/internal/history?module=budget',actor=self.user,perms=['ai.internal.use'])[0],403)
 def test_company_key_is_separate_and_explicit(self):
  self.config(internal_enabled=True)
  with patch.dict(ai.os.environ,{'OPENAI_API_KEY':'website-only'},clear=True):
   self.assertEqual(self.call('/api/ai/internal/send',{'message':'hi','key_source':'company'},self.admin)[0],403)
   self.config(internal_company_key=True)
   self.assertEqual(self.call('/api/ai/internal/send',{'message':'hi','key_source':'company'},self.admin)[0],400)
 def test_internal_send_and_clear(self):
  self.config(internal_enabled=True,internal_company_key=True)
  with patch.dict(ai.os.environ,{'BIOMED_INTERNAL_OPENAI_API_KEY':'internal-only'}),patch.object(ai,'internal_answer',return_value='Draft reply') as reply:
   r=self.call('/api/ai/internal/send',{'message':'Help me draft','key_source':'company'},self.admin)
   self.assertEqual(r[0],200);self.assertEqual(reply.call_args.args[1],'internal-only')
  self.assertEqual(len(self.call('/api/ai/internal/history',actor=self.admin)[1]['items']),2)
  self.call('/api/ai/internal/clear',{},self.admin)
  self.assertEqual(self.call('/api/ai/internal/history',actor=self.admin)[1]['items'],[])
if __name__=='__main__':unittest.main()
