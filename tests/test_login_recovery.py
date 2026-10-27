import sys,tempfile,sqlite3,unittest,time,threading,json,urllib.request
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import serve,recover_login

class Recovery(unittest.TestCase):
 def test_recovery_and_real_login(self):
  with tempfile.TemporaryDirectory() as d:
   db=Path(d)/'test.db';old=serve.DB;serve.DB=db
   try:
    serve.initialize()
    salt,digest,it=serve.password_record('Old-password-123')
    with serve.connect() as c:
     c.execute("INSERT INTO accounts(id,email,name,role,user_id,password_hash,salt,iterations,locked_until,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",('a','admin@example.invalid','Admin','System Admin','u1',digest,salt,it,int(time.time())+900,'test'))
     c.execute("INSERT INTO sessions VALUES('old-session','a',9999999999,1)")
     c.execute("INSERT INTO workspace VALUES('business-test','preserve',1)")
    backup=recover_login.reset_password(db,'admin@example.invalid','New-password-456!')
    with serve.connect() as c:
     self.assertEqual(c.execute("SELECT value FROM workspace WHERE key='business-test'").fetchone()[0],'preserve')
     self.assertEqual(c.execute('SELECT count(*) FROM sessions').fetchone()[0],0)
     self.assertEqual(c.execute('SELECT locked_until FROM accounts').fetchone()[0],0)
    with sqlite3.connect(backup) as c:self.assertGreater(c.execute('SELECT locked_until FROM accounts').fetchone()[0],time.time())
    http=serve.ThreadingHTTPServer(('127.0.0.1',0),serve.Handler)
    t=threading.Thread(target=http.serve_forever,daemon=True);t.start()
    try:
     base='http://127.0.0.1:'+str(http.server_address[1])
     req=urllib.request.Request(base+'/api/auth/login',data=json.dumps({'email':'admin@example.invalid','password':'New-password-456!'}).encode(),headers={'Origin':'http://127.0.0.1:8765','Content-Type':'application/json'})
     with urllib.request.urlopen(req) as r:
      self.assertEqual(r.status,200);self.assertIn('biomed_session=',r.headers['Set-Cookie'])
    finally:http.shutdown();http.server_close();t.join()
   finally:serve.DB=old
 def test_missing_database_is_not_created(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'missing.db'
   with self.assertRaises(ValueError):recover_login.inspect_database(p)
   self.assertFalse(p.exists())
if __name__=='__main__':unittest.main()
