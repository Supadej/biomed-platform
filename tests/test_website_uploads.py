import sys,tempfile,json,base64,threading,urllib.request,urllib.error,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import serve,website_files as f,public_website as public
class Uploads(unittest.TestCase):
 def test_validation(self):
  meta,raw=f.decode_upload({'name':'test.pdf','data':base64.b64encode(b'%PDF-1.4\nsample').decode()});self.assertEqual(meta['mime'],'application/pdf')
  with self.assertRaises(ValueError):f.decode_upload({'name':'test.svg','data':base64.b64encode(b'<svg/>').decode()})
 def test_access_lifecycle(self):
  previous=(serve.DB,serve.session_account,serve.account_permissions);actor=[None];grants=set()
  with tempfile.TemporaryDirectory() as td:
   serve.DB=Path(td)/'test.sqlite3';serve.initialize();serve.session_account=lambda _:actor[0];serve.account_permissions=lambda _:grants
   http=serve.ThreadingHTTPServer(('127.0.0.1',0),serve.Handler);threading.Thread(target=http.serve_forever,daemon=True).start();base='http://127.0.0.1:'+str(http.server_port)
   data=json.dumps({'name':'News.pdf','data':base64.b64encode(b'%PDF-1.4\nhello').decode()}).encode()
   def post():return urllib.request.urlopen(urllib.request.Request(base+'/api/website/uploads',data=data,headers={'Content-Type':'application/json'}))
   try:
    with self.assertRaises(urllib.error.HTTPError) as e:post()
    self.assertEqual(e.exception.code,401);actor[0]=('u','x','Name','Role','u');grants.update(['content','portal.content.create'])
    with self.assertRaises(urllib.error.HTTPError) as e:post()
    self.assertEqual(e.exception.code,403);grants.add('portal.content.upload')
    with post() as r:meta=json.load(r)
    actor[0]=None
    with self.assertRaises(urllib.error.HTTPError) as e:urllib.request.urlopen(base+meta['url'])
    self.assertEqual(e.exception.code,404)
    portal={'content':[{'id':'n','type':'News','title':'News','status':'published','attachments':[meta]}]}
    with serve.connect() as c:
     f.validate_references(portal,c);c.execute('INSERT INTO workspace VALUES(?,?,?)',('biomed_portal_v33_clean',json.dumps(portal),1))
    with urllib.request.urlopen(base+meta['url']) as r:self.assertEqual(r.headers['Content-Type'],'application/pdf');self.assertTrue(r.read().startswith(b'%PDF-'))
    self.assertEqual(public.project_public(portal)['content'][0]['attachments'][0]['id'],meta['id'])
    portal['content'][0]['status']='draft'
    with serve.connect() as c:c.execute('UPDATE workspace SET value=?',(json.dumps(portal),))
    with self.assertRaises(urllib.error.HTTPError):urllib.request.urlopen(base+meta['url'])
   finally:http.shutdown();http.server_close();serve.DB,serve.session_account,serve.account_permissions=previous
if __name__=='__main__':unittest.main()
