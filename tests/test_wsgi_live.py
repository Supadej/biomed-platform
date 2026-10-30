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
    # The production entry must support the workspace adapter's PUT/DELETE,
    # including its automatic save when opening or returning to Staff Portal.
    key='/api/storage/biomed_portal_v33_clean'
    snapshot=json.load(client.open(url+key))
    def put(value,revision):
     return client.open(urllib.request.Request(url+key,method='PUT',data=json.dumps({'value':value,'revision':revision}).encode(),headers={'Content-Type':'application/json','Origin':url}))
    saved=json.load(put(snapshot['value'],snapshot['revision']))
    self.assertEqual(saved['revision'],snapshot['revision']+1)
    returned=json.load(client.open(url+key))
    self.assertEqual(json.loads(returned['value']),json.loads(snapshot['value']))
    self.assertEqual(put(returned['value'],returned['revision']).status,200)
    with self.assertRaises(urllib.error.HTTPError) as stale:put(returned['value'],snapshot['revision'])
    self.assertEqual(stale.exception.code,409)
    # DELETE reaches the existing authorization guard; core workspaces stay protected.
    with self.assertRaises(urllib.error.HTTPError) as denied:
     client.open(urllib.request.Request(url+key,method='DELETE',data=json.dumps({'revision':saved['revision']+1}).encode(),headers={'Content-Type':'application/json','Origin':url}))
    self.assertEqual(denied.exception.code,403)
    anonymous=urllib.request.build_opener()
    with self.assertRaises(urllib.error.HTTPError) as expired:
     anonymous.open(urllib.request.Request(url+key,method='PUT',data=json.dumps({'value':returned['value'],'revision':returned['revision']}).encode(),headers={'Content-Type':'application/json','Origin':url}))
    self.assertEqual(expired.exception.code,401)
    for method in ['GET','HEAD']:
     with self.assertRaises(urllib.error.HTTPError) as private:
      client.open(urllib.request.Request(url+'/company-staff-roster-69.json',method=method))
     self.assertEqual(private.exception.code,404)
   finally:server.task_dispatcher.shutdown();server.close();t.join(timeout=2)
  finally:
   for key,value in [('BIOMED_ALLOWED_ORIGINS',prior),('BIOMED_HTTPS',https)]:
    if value is None:os.environ.pop(key,None)
    else:os.environ[key]=value
   fixture.tearDown()
