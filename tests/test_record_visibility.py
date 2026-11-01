"""Cross-user isolation at workspace, mutation and direct endpoint boundaries."""
import copy,json,sys,unittest,threading,urllib.request,urllib.error,time,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import permissions_policy as policy,record_visibility as v
class Visibility(unittest.TestCase):
 def setUp(self):
  self.grants={x['key'] for x in policy.CATALOG['permissions']}
  self.portal={'roles':{'Sales Representative':list(self.grants)},'users':[{'id':'s1','department':'D','managerId':'m'},{'id':'s2','department':'D','managerId':'m'},{'id':'m','department':'D','managerId':'d'},{'id':'d','department':'D'},{'id':'s3','department':'LSR'}],'tasks':[{'id':'t1','owner':'s1'},{'id':'t2','owner':'s2'}],'salesActuals':[{'id':'a1','rep':'s1','amount':100},{'id':'a2','rep':'s2','amount':900}],'roleRecordScopes':{}}
  self.docs=[{'id':'q1','kind':'quotation','owner':'s1','status':'Draft','lines':[]},{'id':'q2','kind':'quotation','owner':'s2','status':'Draft','lines':[]},{'id':'q3','kind':'quotation','owner':'s3','status':'Draft','lines':[]},{'id':'unknown','kind':'quotation','status':'Draft','lines':[]}]
  self.state={'documents':self.docs,'customers':[{'id':'c','name':'Shared hospital'}],'warehouses':['Main'],'movements':[{'id':'open','productId':'p','change':10},{'id':'m2','productId':'p','change':-1,'sourceId':'q2','notes':'Private quote'}]};self.p=self.context()
 def context(self,role='Sales Representative',uid='s1'):return v.Permissions(self.grants,('a'+uid,'','',role,uid),self.portal,self.docs,{'1':'s1','2':'s2'})
 def scope(self,m,s):self.portal['roleRecordScopes'].setdefault(self.p.actor[3],{})[m]=s
 def filtered(self,key=v.IKEY,data=None,p=None):return json.loads(policy.read_filter(p if p is not None else self.p,key,json.dumps(data if data is not None else self.state)))
 def merge(self,new,key=v.IKEY,old=None):return json.loads(policy.merge_scope(self.p,key,json.dumps(old if old is not None else self.state),json.dumps(new)))
 def test_own_quote_excludes_other_sales_despite_backup_grants(self):self.assertEqual([d['id'] for d in self.filtered()['documents']],['q1'])
 def test_scope_does_not_grant_module_access(self):self.scope('is.quotation','all');self.p.discard('is.quotation.view');self.assertEqual(self.filtered()['documents'],[])
 def test_assigned_is_distinct_from_own(self):
  self.docs[1]['assignedTo']='s1';self.assertFalse(v.visible(self.p,'is.quotation',self.docs[1]));self.scope('is.quotation','assigned');self.assertTrue(v.visible(self.p,'is.quotation',self.docs[1]))
 def test_team_is_transitive_excludes_other_branch(self):
  p=self.context('Sales Manager','d');self.assertTrue(v.visible(p,'is.quotation',self.docs[0]));self.assertTrue(v.visible(p,'is.quotation',self.docs[1]));self.assertFalse(v.visible(p,'is.quotation',self.docs[2]))
 def test_manager_supervisor_equivalence(self):
  for m in v.modules():self.assertEqual(v.default('Sales Manager',m),v.default('Sales Supervisor',m))
 def test_department_and_missing_department(self):
  self.scope('is.quotation','department');self.assertTrue(v.visible(self.p,'is.quotation',self.docs[1]));self.assertFalse(v.visible(self.p,'is.quotation',self.docs[2]));self.portal['users'][0]['department']='';self.assertFalse(v.visible(self.p,'is.quotation',self.docs[1]))
 def test_all_and_permanent_admin(self):self.scope('is.quotation','all');self.assertEqual(len(self.filtered()['documents']),4);self.assertTrue(v.visible(self.context('System Admin'),'is.quotation',self.docs[-1]))
 def test_generated_source_inheritance_and_cycle(self):
  self.assertTrue(v.visible(self.p,'is.shipment',{'id':'g','sourceId':'q1'}));self.assertFalse(v.visible(self.p,'is.shipment',{'id':'g','sourceId':'q2'}));self.docs.extend([{'id':'a','sourceId':'b'},{'id':'b','sourceId':'a'}]);self.assertFalse(v.visible(self.p,'is.shipment',self.docs[-1]))
 def test_rep_precedence_over_creator(self):self.assertFalse(v.visible(self.p,'is.quotation',{'owner':'s1','portalRep':'s2'}))
 def test_shared_masters_separate_scope(self):self.assertEqual(len(self.filtered()['customers']),1);self.scope('is.master-customers','own');self.assertEqual(self.filtered()['customers'],[])
 def test_portal_and_projections_filtered(self):
  d=copy.deepcopy(self.portal);d['isCRM']={'q1':{'lead':True},'q2':{'lead':True}};d['integrationIS']={'quotations':[{'sourceId':'q1','owner':'s1'},{'sourceId':'q2','owner':'s2'}]};r=self.filtered(v.PKEY,d);self.assertEqual(len(r['tasks']),1);self.assertEqual(len(r['salesActuals']),1);self.assertEqual(list(r['isCRM']),['q1']);self.assertEqual(len(r['integrationIS']['quotations']),1)
 def test_restricted_save_preserves_hidden_and_warehouse_strings(self):
  d=self.filtered();d['documents'][0]['notes']='Own edit';r=self.merge(d);self.assertEqual(len(r['documents']),4);self.assertEqual(next(x for x in r['documents'] if x['id']=='q2'),self.docs[1]);self.assertEqual(r['warehouses'],['Main']);policy.authorize_change(self.p,v.IKEY,json.dumps(self.state),json.dumps(r))
 def test_forged_hidden_write_or_owner_transfer(self):
  for row in [dict(self.docs[1],notes='forged'),dict(self.docs[0],owner='s2')]:
   d=self.filtered();d['documents']=[row]
   with self.assertRaises(policy.PermissionDenied):self.merge(d)
 def test_hidden_link_source(self):
  d=self.filtered();d['documents'].append({'id':'mine','kind':'sales-order','owner':'s1','sourceId':'q2'})
  with self.assertRaises(policy.PermissionDenied):self.merge(d)
 def test_hidden_portal_rows_preserved_but_cannot_be_forged(self):
  d=self.filtered(v.PKEY,self.portal);self.assertEqual(len(self.merge(d,v.PKEY,self.portal)['tasks']),2);d['tasks'].append({'id':'t2','owner':'s2','title':'forged'})
  with self.assertRaises(policy.PermissionDenied):self.merge(d,v.PKEY,self.portal)
 def test_hidden_followup_write(self):
  self.portal['isCRM']={'q2':{'outcome':'Monitoring'}};d=self.filtered(v.PKEY,self.portal);d['isCRM']['q2']={'outcome':'Follow-up'}
  with self.assertRaises(policy.PermissionDenied):self.merge(d,v.PKEY,self.portal)
 def test_shared_stock_math_private_metadata_and_merge(self):
  d=self.filtered();self.assertEqual(sum(x['change'] for x in d['movements']),9);self.assertNotIn('notes',d['movements'][1]);self.assertNotIn('sourceId',d['movements'][1]);self.assertEqual(self.merge(d)['movements'],self.state['movements']);d['movements'][1]['change']=-99
  with self.assertRaises(policy.PermissionDenied):self.merge(d)
 def test_crm_identity_mapping_and_view_all_ceiling(self):
  import crm_api as crm
  self.assertTrue(crm.scoped(self.p,'Leads',{'MainUserId':1},1));self.assertFalse(crm.scoped(self.p,'Leads',{'MainUserId':2},1));self.scope('crm.leads','assigned');self.assertTrue(crm.scoped(self.p,'Leads',{'MainUserId':2,'UserIds':[1]},1))
 def test_migration_idempotent_preserves_admin_changes(self):
  self.assertTrue(v.migrate(self.portal));self.scope('is.quotation','department');self.assertFalse(v.migrate(self.portal));self.assertEqual(v.scope(self.p,'is.quotation'),'department')
 def test_invalid_config_and_separate_permission(self):
  for bad in [{'Unknown':{}},{'Sales Representative':{'made-up':'own'}},{'Sales Representative':{'is.quotation':'invalid'}}]:
   with self.assertRaises(ValueError):v.validate_config(bad,self.portal['roles'])
  d=copy.deepcopy(self.portal);d['roleRecordScopes']={'Sales Representative':{'is.quotation':'all'}};self.p.discard('portal.roles.visibility')
  with self.assertRaises(policy.PermissionDenied):policy.authorize_change(self.p,v.PKEY,json.dumps(self.portal),json.dumps(d))
 def test_reduced_copilot_permissions_preserve_context(self):
  p=self.p.copy();p.discard('is.backup.export');self.assertIsInstance(p,v.Permissions);self.assertEqual([d['id'] for d in self.filtered(p=p)['documents']],['q1'])
class Endpoints(unittest.TestCase):
 def setUp(self):
  import test_crm,serve,crm_api
  self.serve=serve;self.fixture=test_crm.CRM();self.fixture.setUp();self.actor=('a2','','','Sales Representative','u2')
  with serve.connect() as c:
   p=self.fixture.portal;p['users'][1].update(role='Sales Representative',department='D');p['roles']['Sales Representative']=list(self.fixture.perms);v.migrate(p);c.execute('UPDATE workspace SET value=? WHERE key=?',(json.dumps(p),v.PKEY));self.fixture.isdata['documents'][0]['owner']='u1';self.fixture.isdata['documents'].extend([{'id':'own','ref':'MY-QUOTE','kind':'quotation','owner':'u2','status':'Draft','lines':[]},{'id':'other','ref':'PRIVATE-QUOTE','kind':'quotation','owner':'u1','status':'Draft','lines':[]}]);c.execute('UPDATE workspace SET value=? WHERE key=?',(json.dumps(self.fixture.isdata),v.IKEY));crm_api.bind_users(c)
  self.perms=serve.account_permissions(self.actor)
 def tearDown(self):self.fixture.tearDown()
 def test_report_and_workflow_direct_id_denied(self):
  import document_report,document_workflow
  class H:
   path='/api/document-report?id=other'
   def reply(self,s,d):return s,d
  self.assertEqual(document_report.handle(H(),self.serve.connect,lambda _:self.actor,lambda _:self.perms)[0],403)
  with self.serve.connect() as c:
   with self.assertRaises(policy.PermissionDenied):document_workflow.mutate(c,self.actor,self.perms,{'id':'other','action':'progress','value':'Sent'})
  H.path='/api/is-workflow';status,result=document_workflow.handle(H(),'GET',self.serve.connect,lambda _:self.actor,lambda _:self.perms,lambda _:True);self.assertEqual(status,200);self.assertEqual(set(result),{'own'})
 def test_snapshot_list_and_direct_id(self):
  import portal_extensions
  class H:
   path=''
   def reply(self,s,d):return s,d
  for path in ['/api/portal/quotation-snapshot?id=other','/api/portal/quotation-snapshot']:
   H.path=path;status,r=portal_extensions.handle(H(),'GET',self.serve.connect,lambda _:self.actor,lambda _:self.perms,lambda _:True);self.assertEqual(status,200);self.assertNotIn('PRIVATE-QUOTE',json.dumps(r))
 def test_scope_saved_renamed_deleted_with_role(self):
  import role_admin,staff_directory
  with self.serve.connect() as c:
   rev=staff_directory.workspace(c)[1];raw={'action':'visibility','role':'Sales Representative','revision':rev,'scopes':{'is.quotation':'all'}}
   with self.assertRaises(policy.PermissionDenied):role_admin.dispatch(c,self.fixture.actor,self.fixture.perms-{'portal.roles.visibility'},raw)
   role_admin.dispatch(c,self.fixture.actor,self.fixture.perms,raw);rev=staff_directory.workspace(c)[1];role_admin.dispatch(c,self.fixture.actor,self.fixture.perms,{'action':'rename','role':'Sales Representative','name':'Regional Sales','revision':rev});data,rev=staff_directory.workspace(c);self.assertEqual(data['roleRecordScopes']['Regional Sales'],{'is.quotation':'all'});self.assertNotIn('Sales Representative',data['roleRecordScopes']);role_admin.dispatch(c,self.fixture.actor,self.fixture.perms,{'action':'delete','role':'Regional Sales','replacement':'Employee','revision':rev});self.assertNotIn('Regional Sales',staff_directory.workspace(c)[0]['roleRecordScopes'])
 def test_live_storage_get_and_forged_put(self):
  serve=self.serve;token='visibility-session'
  with serve.connect() as c:
   salt,digest,it=serve.password_record('visibility-test-password');c.execute('INSERT INTO accounts VALUES(?,?,?,?,?,?,?,?,0,0,0,?)',('a2','scope@example.invalid','Sales Two','Sales Representative','u2',digest,salt,it,'2026-10-30'));c.execute('INSERT INTO sessions VALUES(?,?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),'a2',int(time.time())+600,int(time.time())))
  http=serve.ThreadingHTTPServer(('127.0.0.1',0),serve.Handler);threading.Thread(target=http.serve_forever,daemon=True).start();base='http://127.0.0.1:'+str(http.server_port)
  def req(raw=None):
   request=urllib.request.Request(base+'/api/storage/'+v.IKEY,data=json.dumps(raw).encode() if raw else None,headers={'Cookie':'biomed_session='+token,'Origin':'http://127.0.0.1:8765','Content-Type':'application/json'},method='PUT' if raw else 'GET')
   try:
    with urllib.request.urlopen(request) as r:return r.status,json.load(r)
   except urllib.error.HTTPError as e:return e.code,json.load(e)
  try:
   status,r=req();self.assertEqual(status,200);d=json.loads(r['value']);self.assertEqual([x['id'] for x in d['documents']],['own']);d['documents'].append({'id':'other','kind':'quotation','owner':'u2','notes':'forged'});self.assertEqual(req({'revision':r['revision'],'value':json.dumps(d)})[0],403)
   with serve.connect() as c:self.assertEqual(json.loads(c.execute('SELECT value FROM workspace WHERE key=?',(v.IKEY,)).fetchone()[0])['documents'][-1]['owner'],'u1')
  finally:http.shutdown();http.server_close()
if __name__=='__main__':unittest.main()
