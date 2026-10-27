import os,sys,json,tempfile,threading,urllib.request,urllib.error,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import serve
class Railway(unittest.TestCase):
 def test_origin_persistence_and_api(self):
  previous=serve.DB
  with tempfile.TemporaryDirectory() as td,patch.dict(os.environ,{'RAILWAY_PUBLIC_DOMAIN':'biomed-platform-production-5b19.up.railway.app','BIOMED_ALLOWED_ORIGINS':''}):
   serve.DB=Path(td)/'volume'/'biomed.sqlite3';serve.prepare_database()
   with serve.connect() as c:c.execute('INSERT OR REPLACE INTO workspace VALUES(?,?,?)',('deployment_persistence_marker','kept',1))
   serve.prepare_database()
   with serve.connect() as c:self.assertEqual(c.execute('SELECT value FROM workspace WHERE key=?',('deployment_persistence_marker',)).fetchone()[0],'kept')
   http=serve.ThreadingHTTPServer(('127.0.0.1',0),serve.Handler);threading.Thread(target=http.serve_forever,daemon=True).start();base='http://127.0.0.1:'+str(http.server_port)
   try:
    with urllib.request.urlopen(base+'/api/health') as r:self.assertEqual(json.load(r)['database'],'SQLite')
    with self.assertRaises(urllib.error.HTTPError) as e:urllib.request.urlopen(base+'/api/auth/me')
    self.assertEqual(e.exception.code,401)
    for origin,code in [('https://biomed-platform-production-5b19.up.railway.app',401),('https://untrusted.invalid',403)]:
     req=urllib.request.Request(base+'/api/auth/login',data=json.dumps({'email':'missing@example.invalid','password':'invalid'}).encode(),headers={'Origin':origin,'Content-Type':'application/json'})
     with self.assertRaises(urllib.error.HTTPError) as e:urllib.request.urlopen(req)
     self.assertEqual(e.exception.code,code)
   finally:http.shutdown();http.server_close();serve.DB=previous
if __name__=='__main__':unittest.main()
