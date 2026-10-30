import unittest,threading,io,json,os,urllib.request,http.cookiejar
from test_crm import CRM
import serve,wsgi_app
from waitress import create_server
class Live(unittest.TestCase):
 def test_login_and_manual_over_real_wsgi_listener(self):
  fixture=CRM();fixture.setUp();prior=os.environ.get('BIOMED_ALLOWED_ORIGINS');https=os.environ.get('BIOMED_HTTPS')
  try:
   salt,pw,it=serve.password_record('Local-automated-test-only-64')
   with serve.connect() as c:c.execute('INSERT INTO accounts VALUES(?,?,?,?,?,?,?,?,0,0,0,?)',('admin','admin@example.invalid','Admin','System Admin','u1',pw,salt,it,'2026-10-30'))
   server=create_server(wsgi_app.application,host='127.0.0.1',port=0,threads=2);t=threading.Thread(target=server.run,daemon=True);t.start();url='http://127.0.0.1:'+str(server.effective_port);os.environ['BIOMED_ALLOWED_ORIGINS']=url;os.environ['BIOMED_HTTPS']='0'
   try:
    client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()));self.assertEqual(client.open(url+'/api/health').status,200);body=json.dumps({'email':'admin@example.invalid','password':'Local-automated-test-only-64'}).encode();self.assertEqual(client.open(urllib.request.Request(url+'/api/auth/login',data=body,headers={'Content-Type':'application/json','Origin':url})).status,200);manual=json.load(client.open(url+'/api/user-manual'));self.assertEqual(manual['user']['role'],'System Admin');self.assertTrue(any(c['id']=='service.jobs' for c in manual['chapters']));self.assertEqual(client.open(url+'/user-manual.html').status,200)
   finally:server.task_dispatcher.shutdown();server.close();t.join(timeout=2)
  finally:
   for key,value in [('BIOMED_ALLOWED_ORIGINS',prior),('BIOMED_HTTPS',https)]:
    if value is None:os.environ.pop(key,None)
    else:os.environ[key]=value
   fixture.tearDown()
