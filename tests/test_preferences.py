import sys,tempfile,json,threading,urllib.request,urllib.error,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import serve
class Preferences(unittest.TestCase):
 def test_account_isolation_and_validation(self):
  previous=(serve.DB,serve.session_account);actor=[None]
  with tempfile.TemporaryDirectory() as td:
   serve.DB=Path(td)/'test.sqlite3';serve.initialize()
   with serve.connect() as c:
    for id in ['a','b']:c.execute('INSERT INTO accounts VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(id,id+'@example.invalid',id,'Employee',id,b'h',b's',1,0,0,0,'now'))
   serve.session_account=lambda _:actor[0]
   http=serve.ThreadingHTTPServer(('127.0.0.1',0),serve.Handler);threading.Thread(target=http.serve_forever,daemon=True).start();url='http://127.0.0.1:'+str(http.server_port)+'/api/preferences/quick-access'
   def request(data=None,origin=None):
    headers={'Content-Type':'application/json'}
    if origin:headers['Origin']=origin
    with urllib.request.urlopen(urllib.request.Request(url,data=json.dumps(data).encode() if data is not None else None,headers=headers)) as r:return json.load(r)
   try:
    with self.assertRaises(urllib.error.HTTPError) as e:request()
    self.assertEqual(e.exception.code,401);actor[0]=('a',)
    request({'system':'is','items':['reports','stock-inventory'],'account_id':'b'})
    self.assertEqual(request()['is'],['reports','stock-inventory'])
    actor[0]=('b',);self.assertEqual(request(),{});request({'system':'portal','items':[]});self.assertEqual(request(),{'portal':[]})
    actor[0]=('a',);self.assertNotIn('portal',request())
    with self.assertRaises(urllib.error.HTTPError) as e:request({'system':'is','items':['reports']},'https://invalid.example')
    self.assertEqual(e.exception.code,403)
    with self.assertRaises(urllib.error.HTTPError) as e:request({'system':'is','items':['reports']*13})
    self.assertEqual(e.exception.code,400)
   finally:http.shutdown();http.server_close();serve.DB,serve.session_account=previous
if __name__=='__main__':unittest.main()
