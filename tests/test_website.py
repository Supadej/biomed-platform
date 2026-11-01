import sys,json,tempfile,threading,unittest,urllib.request
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import public_website as w,permissions_policy as policy,serve
class Website(unittest.TestCase):
 def fixture(self):return {'users':[{'email':'private@example.invalid','salary':999}], 'roles':{'secret':['all']},'siteSections':{'services':{'certTitle':'Updated certification','certLink':'javascript:alert(1)'},'news':{'heading':'Science news'},'private':{'password':'hidden'}},'content':[{'id':'public','type':'News','title':'Published update','description':'Public','status':'published','owner':'private','link':'https://example.com'},{'id':'draft','title':'SECRET DRAFT','status':'draft'}]}
 def test_public_projection(self):
  p=w.project_public(self.fixture());raw=json.dumps(p);self.assertNotIn('private',raw);self.assertNotIn('SECRET',raw);self.assertNotIn('users',p);self.assertEqual(p['siteSections']['services']['certLink'],'');self.assertEqual(len(p['content']),1)
 def test_links(self):
  for bad in ['javascript:alert(1)','//evil.test','https://[','data:text/html,x','/\\evil.test']:self.assertEqual(w.safe_url(bad),'')
  self.assertEqual(w.safe_url('news.html'),'news.html')
  self.assertEqual(w.safe_url('/news.html'),'/news.html')
 def test_publish_permission(self):
  old={'content':[]};new={'content':[{'id':'one','status':'published','type':'News'}]}
  with self.assertRaises(policy.PermissionDenied):policy.authorize_portal({'content','portal.content.create'},old,new)
  policy.authorize_portal({'content','portal.content.create','portal.content.publish'},old,new)
 def test_public_endpoint_without_login(self):
  previous=serve.DB
  with tempfile.TemporaryDirectory() as td:
   serve.DB=Path(td)/'site.sqlite3';serve.initialize()
   with serve.connect() as c:c.execute('INSERT INTO workspace VALUES(?,?,?)',('biomed_portal_v33_clean',json.dumps(self.fixture()),1))
   http=serve.ThreadingHTTPServer(('127.0.0.1',0),serve.Handler);thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
   try:
    with urllib.request.urlopen('http://127.0.0.1:'+str(http.server_port)+'/api/public/website') as r:data=json.load(r)
    self.assertEqual(data['content'][0]['id'],'public');self.assertNotIn('roles',data)
   finally:http.shutdown();http.server_close();serve.DB=previous
if __name__=='__main__':unittest.main()
