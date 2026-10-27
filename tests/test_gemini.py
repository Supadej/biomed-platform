import unittest,io,json,sys,tempfile,sqlite3
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ai_chat_api as ai
from cryptography.fernet import Fernet
KEY='AIza'+'fake-test-only-'*3
class H:
 path='/api/ai/internal/key'
 def __init__(self,data):
  raw=json.dumps(data).encode();self.headers={'Content-Length':str(len(raw))};self.rfile=io.BytesIO(raw)
 def reply(self,status,data):return status,data
class Gemini(unittest.TestCase):
 def test_request_and_reply(self):
  result={'candidates':[{'content':{'parts':[{'text':'สวัสดี'}]}}]}
  with patch.object(ai.urllib.request,'urlopen',return_value=io.BytesIO(json.dumps(result).encode())) as call:
   self.assertEqual(ai.internal_answer([('user','hello'),('user','again')],KEY,'portal'),'สวัสดี')
   req=call.call_args.args[0];payload=json.loads(req.data)
   self.assertIn('generativelanguage.googleapis.com',req.full_url)
   self.assertNotIn(KEY,req.full_url)
   self.assertEqual(req.get_header('X-goog-api-key'),KEY)
   self.assertEqual(len(payload['contents']),1)
   self.assertIn('NO live database',payload['systemInstruction']['parts'][0]['text'])
 def test_website_routes_to_gemini(self):
  with patch.object(ai,'gemini_answer',return_value='Product help') as call:
   self.assertEqual(ai.response_ai([('visitor','hello')],KEY,[{'name':'Published product'}]),'Product help')
   self.assertIn('Published product',call.call_args.args[2])
 def test_company_keys_separate(self):
  with patch.dict(ai.os.environ,{'GEMINI_API_KEY':KEY,'BIOMED_INTERNAL_GEMINI_API_KEY':'AIza-internal','OPENAI_API_KEY':'sk-legacy'},clear=True):
   self.assertEqual(ai.company_key(),KEY)
   self.assertEqual(ai.company_key(True),'AIza-internal')
 def test_encrypted_personal_save(self):
  with tempfile.TemporaryDirectory() as d:
   db=str(Path(d)/'test.db')
   def conn():return sqlite3.connect(db)
   with conn() as c:ai.init(c);c.execute("UPDATE ai_settings SET value='true' WHERE key='internal_enabled'")
   secret=Fernet.generate_key()
   with patch.dict(ai.os.environ,{'BIOMED_AI_ENCRYPTION_KEY':secret.decode()}):
    status,data=ai.handle(H({'key':KEY,'module':'portal'}),'POST',conn,lambda h:('a','test','Admin','System Admin','u1'),lambda a:set(),lambda h:True)
    self.assertEqual(status,200)
    with conn() as c:cipher=c.execute('SELECT key_cipher FROM ai_chat_keys').fetchone()[0]
    self.assertEqual(Fernet(secret).decrypt(cipher).decode(),KEY)
 def test_quota_does_not_claim_unlimited(self):
  import urllib.error
  self.assertIn('No paid fallback',ai.gemini_error(urllib.error.HTTPError('url',429,'limit',{},None)))
if __name__=='__main__':unittest.main()
