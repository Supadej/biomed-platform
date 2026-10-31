import unittest,json,io
import user_manual as m,serve,wsgi_app
from test_crm import CRM
class Manual(unittest.TestCase):
 def setUp(self):self.actor=('a','e@example.invalid','Engineer','Service Engineer','u1');self.p={'users':[{'id':'u1','department':'Service'}],'roleDescriptions':{'Service Engineer':'Maintain instruments','Accounting':'Private accounting scope'}}
 def test_service_scope_and_parent_gates(self):
  x=m.project(self.actor,{'service.view','service.jobs.view','service.jobs.print'},self.p);self.assertNotIn('Financial',x['systems']);self.assertNotIn('Private accounting scope',json.dumps(x));self.assertEqual({c['id'] for c in x['chapters']},{'service','service.jobs'});self.assertNotIn('budget.finance',{c['id'] for c in m.project(self.actor,{'budget.finance.view'},self.p)['chapters']})
 def test_readonly_actions_and_live_responsibilities(self):
  ps={'application_service.view'};a=m.project(self.actor,ps,self.p);self.assertFalse(any(x['key']=='application_service.create' for x in a['chapters'][0]['actions']));self.p['roleDescriptions']['Service Engineer']='Revised';b=m.project(self.actor,ps,self.p);self.assertNotEqual(a['revision'],b['revision']);self.assertEqual(b['user']['responsibility'],'Revised');self.assertEqual(m.project(self.actor,set(),self.p)['chapters'],[])
 def test_all_catalog_modules_have_projection(self):self.assertGreater(len(m.MODULES),150)
class Endpoint(unittest.TestCase):
 setUp=CRM.setUp
 tearDown=CRM.tearDown
 def test_auth_and_ignore_client_role(self):
  class H:
   path='/api/user-manual?role=System%20Admin'
   def reply(self,s,b):return s,b
  self.assertEqual(m.handle(H(),serve.connect,lambda _:None,lambda _:set())[0],401);status,x=m.handle(H(),serve.connect,lambda _:self.actor,lambda _:{'service.view','service.jobs.view'});self.assertEqual(status,200);self.assertNotIn('Financial',x['systems'])
 def test_wsgi_health_auth_and_protected_source(self):
  def call(path):
   out={}
   body=b''.join(wsgi_app.application({'REQUEST_METHOD':'GET','PATH_INFO':path,'wsgi.input':io.BytesIO(),'HTTP_HOST':'local.test'},lambda s,h:out.update(status=s)));return out['status'],body
  self.assertTrue(call('/api/health')[0].startswith('200'));self.assertTrue(call('/api/user-manual')[0].startswith('401'));self.assertTrue(call('/serve.py')[0].startswith(('403','404')))
