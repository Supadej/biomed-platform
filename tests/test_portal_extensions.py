"""Approval integrity, private evidence and account-owned favorite regression tests."""
import sys,json,copy,base64,tempfile,threading,unittest,urllib.request,urllib.error
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import serve,portal_extensions as ext,permissions_policy as policy
class ApprovalIntegrity(unittest.TestCase):
 def setUp(self):
  self.perms={p['key'] for p in policy.CATALOG['permissions']}|{'demos','incentives'}
  self.old={'users':[{'id':'employee','managerId':'manager'},{'id':'manager'}],'demos':[{'id':'d','employee':'employee','owner':'employee','customer':'Hospital','start':'2026-10-26','end':'2026-10-27','approvalStatus':'Draft','status':'Planned','history':[]}]}
 def transition(self,old,next,actor):
  new=copy.deepcopy(old);r=new['demos'][0];r['approvalStatus']=next;r['history'].append({'action':next,'by':actor,'reason':'Invalid dates' if next=='Rejected' else ''});return new
 def auth(self,old,new,actor,perms=None):policy.authorize_portal(self.perms if perms is None else perms,old,new,actor)
 def test_full_demo_approval_lifecycle(self):
  pending=self.transition(self.old,'Pending','employee');self.auth(self.old,pending,'employee');approved=self.transition(pending,'Approved','manager');self.auth(pending,approved,'manager');progress=copy.deepcopy(approved);progress['demos'][0].update(status='Completed',feedback='Accepted');self.auth(approved,progress,'employee')
 def test_wrong_approver_and_self_approval(self):
  pending=self.transition(self.old,'Pending','employee')
  for actor in ['employee','stranger']:
   approved=self.transition(pending,'Approved',actor)
   with self.assertRaises(policy.PermissionDenied):self.auth(pending,approved,actor,self.perms-{'approve_all'})
 def test_pending_and_approved_details_locked(self):
  pending=self.transition(self.old,'Pending','employee');changed=copy.deepcopy(pending);changed['demos'][0]['customer']='Changed'
  with self.assertRaises(policy.PermissionDenied):self.auth(pending,changed,'employee')
  approved=self.transition(pending,'Approved','manager');changed=copy.deepcopy(approved);changed['demos'][0]['equipment']='Different'
  with self.assertRaises(policy.PermissionDenied):self.auth(approved,changed,'manager')
 def test_missing_history_permission_and_delete(self):
  pending=self.transition(self.old,'Pending','employee');pending['demos'][0]['history']=[]
  with self.assertRaises(policy.PermissionDenied):self.auth(self.old,pending,'employee')
  pending=self.transition(self.old,'Pending','employee')
  with self.assertRaises(policy.PermissionDenied):self.auth(self.old,pending,'employee',self.perms-{'portal.demos.submit'})
  with self.assertRaises(policy.PermissionDenied):self.auth(pending,{**pending,'demos':[]},'employee')
 def test_rejection_redo_and_withdraw(self):
  pending=self.transition(self.old,'Pending','employee');rejected=self.transition(pending,'Rejected','manager');self.auth(pending,rejected,'manager');redo=self.transition(rejected,'Pending','employee');self.auth(rejected,redo,'employee');cancelled=self.transition(redo,'Cancelled','employee');self.auth(redo,cancelled,'employee')
 def test_scheme_edit_and_claim_snapshot_integrity(self):
  scheme={'id':'s','rep':'employee','line':'Diagnostics','from':'2026-10','to':'2026-12','threshold':100,'rate':1};old={**self.old,'productLines':['Diagnostics'],'incentiveSchemes':[scheme],'incentiveClaims':[{'id':'claim','schemeId':'s','rate':1,'amount':100,'status':'Pending'}]};new=copy.deepcopy(old);new['incentiveSchemes'][0]['rate']=2;new['incentiveClaims'][0]['schemeSnapshot']=copy.deepcopy(scheme);self.auth(old,new,'manager');bad=copy.deepcopy(new);bad['incentiveClaims'][0]['schemeSnapshot']['rate']=8
  with self.assertRaises(policy.PermissionDenied):self.auth(old,bad,'manager')
  bad=copy.deepcopy(new);bad['incentiveSchemes'][0]['rate']=float('nan')
  with self.assertRaises(policy.PermissionDenied):self.auth(old,bad,'manager')

class ExtensionHTTP(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.previous=(serve.DB,serve.session_account,serve.account_permissions);serve.DB=Path(self.temp.name)/'extensions.sqlite3';serve.initialize();self.actor=None;serve.session_account=lambda _:self.actor
  self.perms={'requests','leavebalance','portal.requests.create','portal.requests.approve'};serve.account_permissions=lambda _:self.perms
  self.portal={'users':[{'id':'employee','managerId':'manager'},{'id':'manager'},{'id':'stranger'}],'requests':[]}
  with serve.connect() as c:
   for id in ['employee','manager','stranger']:c.execute('INSERT INTO accounts VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(id,id+'@example.invalid',id,'Employee',id,b'h',b's',1,0,0,0,'now'))
   c.execute('INSERT INTO workspace VALUES(?,?,1)',('biomed_portal_v33_clean',json.dumps(self.portal)))
  class Handler(serve.Handler):
   def log_message(self,*a):pass
  self.http=serve.ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=self.http.serve_forever,daemon=True).start();self.base='http://127.0.0.1:'+str(self.http.server_port)
 def tearDown(self):self.http.shutdown();self.http.server_close();serve.DB,serve.session_account,serve.account_permissions=self.previous;self.temp.cleanup()
 def as_user(self,id):self.actor=(id,id+'@example.invalid',id,'Employee',id)
 def req(self,path,body=None,origin=None):
  headers={'Content-Type':'application/json'}
  if origin:headers['Origin']=origin
  try:
   with urllib.request.urlopen(urllib.request.Request(self.base+path,data=json.dumps(body).encode() if body is not None else None,headers=headers)) as r:
    raw=r.read();return r.status,json.loads(raw) if r.headers.get_content_type()=='application/json' else raw
  except urllib.error.HTTPError as e:return e.code,json.load(e)
 def test_favorite_auth_isolation_conflict_delete(self):
  url='/api/preferences/search-favorites?scope=portal:requests:filters-0';self.assertEqual(self.req(url)[0],401);self.as_user('employee');body={'scope':'portal:requests:filters-0','name':'My pending','state':[{'key':'search#0','value':'Pending'}]};self.assertEqual(self.req(url,body)[0],200);self.assertEqual(self.req(url,body)[0],409);self.as_user('stranger');self.assertEqual(self.req(url)[1]['items'],[]);self.as_user('employee');self.assertEqual(self.req(url)[1]['items'][0]['state'],body['state']);self.assertEqual(self.req(url,{**body,'operation':'delete','revision':1})[0],200);self.assertEqual(self.req(url)[1]['items'],[])
 def test_favorite_validation_and_origin(self):
  self.as_user('employee');url='/api/preferences/search-favorites';body={'scope':'portal:requests','name':'One','state':[]};self.assertEqual(self.req(url,body,'https://invalid.example')[0],403);self.assertEqual(self.req(url,{**body,'state':[{'selector':'script','value':'bad'}]})[0],400);self.assertEqual(self.req(url,{**body,'name':''})[0],400)
 def test_leave_private_attachment_and_reference_binding(self):
  self.as_user('employee');raw=b'%PDF-1.4\nprivate leave evidence';code,file=self.req('/api/portal/attachments',{'requestId':'leave1','name':'medical.pdf','data':base64.b64encode(raw).decode()});self.assertEqual(code,200);self.assertEqual(self.req(file['url'])[0],404)
  self.portal['requests']=[{'id':'leave1','type':'leave','owner':'employee','status':'Pending','attachments':[file]}]
  with serve.connect() as c:ext.validate_leave_references(self.portal,c);c.execute('UPDATE workspace SET value=?',(json.dumps(self.portal),))
  self.assertEqual(self.req(file['url']),(200,raw));self.as_user('stranger');self.assertEqual(self.req(file['url'])[0],404);self.as_user('manager');self.assertEqual(self.req(file['url'])[0],200);bad=copy.deepcopy(self.portal);bad['requests'][0]['id']='another'
  with serve.connect() as c:
   with self.assertRaises(ValueError):ext.validate_leave_references(bad,c)
 def test_attachment_origin_type_and_count(self):
  self.as_user('employee');url='/api/portal/attachments';body={'requestId':'r','name':'file.pdf','data':base64.b64encode(b'%PDF-1.4 example').decode()};self.assertEqual(self.req(url,body,'https://invalid.example')[0],403);self.assertEqual(self.req(url,{**body,'data':base64.b64encode(b'<script>bad</script>').decode()})[0],400)
  for i in range(5):self.assertEqual(self.req(url,body)[0],200)
  self.assertEqual(self.req(url,body)[0],400)
 def test_quotation_snapshot_minimal_payload_and_private_details(self):
  self.as_user('employee');self.perms={'is_view','tenders','is.quotation.view','is.sales-order.view'}
  source={'products':[{'id':'product','privateProductField':'not returned'}]*1000,'customers':[{'id':'c','name':'Hospital','address':'private address'},{'id':'other','name':'Unrelated'}],'documents':[{'id':'q','kind':'quotation','ref':'QT-1','party':'c','status':'Approved','lines':[{'qty':2,'price':50}],'remarks':'Full quotation details'},{'id':'o','kind':'sales-order','sourceId':'q','status':'Approved','lines':[{'qty':8,'price':90}]},{'id':'inv','kind':'invoice','ref':'private invoice'}]}
  with serve.connect() as c:c.execute('INSERT INTO workspace VALUES(?,?,1)',('biomed_is_v50_transactions',json.dumps(source)))
  code,x=self.req('/api/portal/quotation-snapshot');self.assertEqual(code,200);self.assertNotIn('products',x);self.assertEqual(x['customers'],[{'id':'c','name':'Hospital'}]);q=next(d for d in x['documents'] if d['id']=='q');self.assertEqual(q['financials']['net'],100);self.assertNotIn('lines',q);self.assertNotIn('remarks',q);self.assertEqual(len(x['documents']),2);self.assertEqual(set(x['documents'][1]),{'id','kind','status','sourceId'})
  code,detail=self.req('/api/portal/quotation-snapshot?id=q');self.assertEqual(detail['documents'][0]['remarks'],'Full quotation details');self.assertEqual(self.req('/api/portal/quotation-snapshot?id=inv')[1]['documents'],[])
  self.perms.remove('is.sales-order.view');self.assertEqual(len(self.req('/api/portal/quotation-snapshot')[1]['documents']),1)
 def test_quotation_snapshot_requires_existing_source_and_portal_access(self):
  self.assertEqual(self.req('/api/portal/quotation-snapshot')[0],401);self.as_user('employee');self.perms={'tenders','is.quotation.view'};self.assertEqual(self.req('/api/portal/quotation-snapshot')[0],403);self.perms={'is_view','is.quotation.view'};self.assertEqual(self.req('/api/portal/quotation-snapshot')[0],403);self.perms={'is_view','pipeline'};self.assertEqual(self.req('/api/portal/quotation-snapshot')[1]['documents'],[])
if __name__=='__main__':unittest.main()
