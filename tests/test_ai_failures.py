import unittest,io,urllib.error
from unittest.mock import patch
from test_ai_separation import Separation,ai
class Failures(Separation):
 def test_failed_request_keeps_history_and_retry_excludes_error(self):
  self.config(internal_enabled=True,internal_company_key=True)
  error=urllib.error.HTTPError('https://api.openai.com/v1/responses',429,'quota',{},io.BytesIO(b'{"error":{"code":"insufficient_quota"}}'))
  with patch.dict(ai.os.environ,{'BIOMED_INTERNAL_OPENAI_API_KEY':'fake-test-key'}),patch.object(ai,'internal_answer',side_effect=error):
   status,data=self.call('/api/ai/internal/send',{'message':'Help me','key_source':'company'},self.admin)
  self.assertEqual(status,502);self.assertIn('credits',data['error'])
  history=self.call('/api/ai/internal/history?module=portal',actor=self.admin)[1]['items']
  self.assertEqual([r['sender'] for r in history],['user','error'])
  with patch.dict(ai.os.environ,{'BIOMED_INTERNAL_OPENAI_API_KEY':'fake-test-key'}),patch.object(ai,'internal_answer',return_value='Here is help') as answer:
   self.assertEqual(self.call('/api/ai/internal/send',{'message':'Try again','key_source':'company'},self.admin)[0],200)
   self.assertEqual(answer.call_args.args[0],[('user','Help me'),('user','Try again')])
if __name__=='__main__':unittest.main()
