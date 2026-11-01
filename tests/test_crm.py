"""Compatibility, authentication, permissions and reconciliation regression checks."""
import sys,json,sqlite3,tempfile,unittest,threading,urllib.request,urllib.error,hashlib,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import serve,crm_api as crm,crm_bridges as bridge,permissions_policy as policy
class CRM(unittest.TestCase):
 def setUp(self):
  from unittest.mock import patch
  import company_access_import
  self.access_payload=patch.object(company_access_import,'PAYLOAD',Path('/nonexistent-test-access-payload.json'));self.access_payload.start()
  import company_access_resolution
  self.access_resolution_plan=patch.object(company_access_resolution,'PLAN',[]);self.access_resolution_plan.start()
  self.temp=tempfile.TemporaryDirectory();self.prior=serve.DB;serve.DB=Path(self.temp.name)/'crm.sqlite3';serve.initialize();self.actor=('admin','admin@example.invalid','Admin','System Admin','u1');self.perms={p['key'] for p in policy.CATALOG['permissions']}
  self.portal={'users':[{'id':'u1','name':'Admin One','email':'one@example.invalid','role':'System Admin'},{'id':'u2','name':'Second Person','email':'two@example.invalid','role':'Employee'}],'roles':{'System Admin':list(self.perms),'Employee':['crm_view','crm.leads.view']},'pipeline':[{'id':'o1','employee':'u1','opportunity':'New opportunity','value':300,'closing':'2027-02-01','stage':'Qualified'}],'tenders':[],'visits':[{'id':'v1','owner':'u1','visitdate':'2026-11-05','customer':'Hospital','discussion':'Visit plan'}],'tickets':[],'permissionCatalogVersion':policy.CATALOG['version']}
  self.isdata={'customers':[{'id':'c1','name':'Hospital','contact':'Customer','address':'Address','taxId':'TAX','email':'customer@example.invalid'}],'products':[{'id':'p1','name':'Product','brand':'Brand','sku':'CAT1','unit':'kit'}],'documents':[{'id':'i1','ref':'INV-1','kind':'invoice','status':'Approved','currency':'THB','date':'2026-10-01','lines':[{'productId':'p1','qty':2,'price':100}]}],'movements':[{'productId':'p1','warehouse':'Main','lot':'LOT','change':5,'expiry':'2027-12-31'}]}
  self.budget={'active':2027,'years':{'2027':{'products':[{'id':'bp1','name':'Portfolio','costCenter':'LSR','budget':[100]*12,'revenueActual':[25]*12}],'expenses':[{'id':'be1','name':'Travel','category':'Promotional Expenses','costCenter':'LSR','budget':[5]*12,'actual':[2]*12,'commitment':[1]*12}],'workforce':[]}}}
  with serve.connect() as c:
   for k,v in [('biomed_portal_v33_clean',self.portal),('biomed_is_v50_transactions',self.isdata),('biomed_budget_v60_years',self.budget)]:c.execute('INSERT INTO workspace VALUES(?,?,1)',(k,json.dumps(v)))
   crm.bind_users(c)
 def tearDown(self):serve.DB=self.prior;self.temp.cleanup();self.access_payload.stop();self.access_resolution_plan.stop()
 def call(self,c,path,method='GET',data=None,perms=None):return crm.handle(c,self.actor,self.perms if perms is None else perms,'/biomedapi/'+path,method,data or {})
 def test_all_entity_crud_and_nested_contract(self):
  with serve.connect() as c:
   org=self.call(c,'organizations/create','POST',{'Name':'Hospital'});dep=self.call(c,'departments/create','POST',{'Name':'Lab','OrganizationID':org['Id']});contact=self.call(c,'contacts/create','POST',{'Name':'Contact','DepartmentID':dep['Id']});product=self.call(c,'products/create','POST',{'Name':'Portfolio'});project=self.call(c,'v2/project/create','POST',{'Name':'Project'});stage=self.call(c,'v2/project/pipelines/create','POST',{'Name':'Stage','ProjectId':project['Id']});activity=self.call(c,'v2/project/activities/create','POST',{'Name':'Activity','ProjectPipelineId':stage['Id']});lead=self.call(c,'v2/crm/leads/create','POST',{'LeadName':'Lead','MainCustomerId':contact['Id'],'ProductId':product['Id'],'UserIds':[1,2]});event=self.call(c,'v2/event/create','POST',{'Title':'Visit','MaincontactID':contact['Id'],'Mainuserid':1,'ProductIDs':[product['Id']]})
   l=self.call(c,'v2/crm/leads/'+str(lead['Id']));self.assertEqual(l['MainCustomer']['Department']['Name'],'Lab');self.assertEqual(len(l['LeadUsers']),2);self.assertNotIn('password',json.dumps(l).lower());self.assertEqual(l['Pipeline']['PipelineName'],'New lead');self.assertEqual(self.call(c,'v2/project/'+str(project['Id']))['Pipelines'][0]['Activities'][0]['Name'],'Activity')
   self.call(c,'v2/crm/leads/update','POST',{'Id':lead['Id'],'LeadName':'Updated'});self.assertEqual(crm.raw(c,'Leads',lead['Id'])['LeadName'],'Updated')
   self.call(c,'v2/event/delete','POST',{'Id':event['Id']});self.assertIsNone(crm.raw(c,'Events',event['Id']))
 def test_permissions_own_scope_nested_and_forged_get(self):
  with serve.connect() as c:
   lead=self.call(c,'v2/crm/leads/create','POST',{'LeadName':'Private','MainUserId':2});own={'crm_view','crm.leads.view','crm.leads.edit','crm.contacts.view'}
   self.assertEqual(self.call(c,'v2/crm/leads',perms=own),[])
   with self.assertRaises(policy.PermissionDenied):self.call(c,'v2/crm/leads/update','POST',{'Id':lead['Id'],'LeadName':'Forged'},own)
   with self.assertRaises(ValueError):self.call(c,'contacts/create','GET',{'Name':'Forged'})
   with self.assertRaises(policy.PermissionDenied):self.call(c,'users/create','POST',{'username':'bypass','password':'secret'})
   with self.assertRaises(policy.PermissionDenied):self.call(c,'v2/event/create','POST',{'Title':'Reassign','MainUserID':2},self.perms-{'crm.events.assign'})
 def test_stock_and_ticket_items(self):
  with serve.connect() as c:
   portal=json.loads(c.execute("SELECT value FROM workspace WHERE key='biomed_portal_v33_clean'").fetchone()[0]);portal['users'][1]['role']='Service Engineer';portal['roles']['Service Engineer']=['service.jobs.edit','crm_view','crm.tickets.view'];c.execute("UPDATE workspace SET value=? WHERE key='biomed_portal_v33_clean'",(json.dumps(portal),))
  with serve.connect() as c:
   p=self.call(c,'v2/product/inventory/create','POST',{'Name':'Inventory'});self.call(c,'v2/product/stock/add','POST',{'ProductId':p['Id'],'Quantity':10,'LotNumber':'L'});self.call(c,'v2/product/stock/remove','POST',{'ProductId':p['Id'],'Quantity':3,'LotNumber':'L'});self.assertEqual(self.call(c,'v2/product/inventory/'+str(p['Id']))['StockCount'],7)
   with self.assertRaises(ValueError):self.call(c,'v2/product/stock/remove','POST',{'ProductId':p['Id'],'Quantity':8,'LotNumber':'L'})
   ticket=self.call(c,'v2/helpdesk/ticket/create','POST',{'Title':'Ticket','AssignedToUserId':2,'CreatedByUserId':2,'HelpDeskItems':[{'Description':'Spare','Quantity':1,'InventoryProductId':p['Id']}]});item=crm.rows(c,'HelpDeskItems')[0];self.assertEqual(item['TicketId'],ticket['Id']);self.assertEqual(self.call(c,'v2/helpdesk/item',perms=self.perms-{'crm.tickets.view_all'}),[])
 def test_shortcuts_and_date_filters(self):
  with serve.connect() as c:
   self.call(c,'v2/user/CreateShortcut','POST',{'Name':'Mine','UrlParams':'crm.html','UserId':2});self.assertEqual(len(self.call(c,'v2/user/GetShortcuts/1')),1)
   with self.assertRaises(policy.PermissionDenied):self.call(c,'v2/user/GetShortcuts/2')
   self.call(c,'v2/crm/leads/create','POST',{'LeadName':'Older','Expected':'01/01/2026, 09:00'});self.call(c,'v2/crm/leads/create','POST',{'LeadName':'Newer','Expected':'01/01/2027, 09:00'});self.assertEqual(len(self.call(c,'v2/crm/leads','POST',{'expectedStart':'06/01/2026'})),1)
 def test_bridge_all_directions_idempotence_and_provenance(self):
  with serve.connect() as c:
   before=c.execute('SELECT key,value,revision FROM workspace ORDER BY key').fetchall();b=lambda direction,action,data={}:bridge.handle(c,self.actor,self.perms,'/api/crm/bridge/'+direction+'/'+action,'POST' if action in ['save','run'] else 'GET',data)
   plan=b('is-crm','preview');self.assertGreater(len(plan['items']),4);first=b('is-crm','run',{'token':plan['token']});plan=b('is-crm','preview');second=b('is-crm','run',{'token':plan['token']});self.assertEqual(second['summary']['created'],0);self.assertGreater(second['summary']['updated'],0);contact=crm.rows(c,'Contacts')[0];self.assertEqual(crm.raw(c,'Departments',contact['DepartmentID'])['OrganizationID'],crm.rows(c,'Organizations')[0]['Id'])
   with self.assertRaises(policy.PermissionDenied):self.call(c,'contacts/update','POST',{'Id':contact['Id'],'Name':'Overwrite'})
   portal=b('portal-crm','preview');self.assertFalse(portal['exceptions']);b('portal-crm','run',{'token':portal['token']});self.assertEqual(crm.rows(c,'Leads')[0]['LeadName'],'New opportunity');self.assertEqual(crm.rows(c,'Events')[0]['StartDate'],'2026-11-05')
   plan=b('budget-crm','preview');self.assertTrue(plan['exceptions']);prod=self.call(c,'products/create','POST',{'Name':'Portfolio'});cfg=b('budget-crm','config');cfg['config']['productMap']={'bp1':prod['Id']};b('budget-crm','save',{'revision':cfg['revision'],'config':cfg['config']});plan=b('budget-crm','preview');self.assertFalse(plan['exceptions']);b('budget-crm','run',{'token':plan['token']});self.assertEqual(crm.rows(c,'Targets')[0]['TargetValue'],1200);self.assertEqual(crm.rows(c,'Targets')[0]['FinancialYear'],2027);self.assertEqual(before,c.execute('SELECT key,value,revision FROM workspace ORDER BY key').fetchall())
 def test_filters_match_supplied_screens(self):
  with serve.connect() as c:
   p=self.call(c,'products/create','POST',{'Name':'Portfolio'});self.call(c,'targets/create','POST',{'Name':'FY2027','ProductID':p['Id'],'StartDate':'2026-05-01','EndDate':'2027-04-30','TargetValue':1200});self.assertEqual(len(self.call(c,'targets','POST',{'expectedStart':'2026-11-01','expectedEnd':'2027-01-31'})),1)
   brand=self.call(c,'v2/product/brands/create','POST',{'Name':'Brand','InventoryBrandType':'LSR','InventoryBrandDistriutor':'Biomed'});item=self.call(c,'v2/product/inventory/create','POST',{'Name':'Assay','BrandId':brand['Id'],'CategoryNumber':'CAT','Type':1});self.call(c,'v2/product/stock/add','POST',{'ProductId':item['Id'],'Quantity':5,'LotNumber':'L'});self.assertEqual(self.call(c,'v2/product/inventory/'+str(item['Id']))['Stocks'][0]['Type'],'Incoming');self.assertEqual(len(self.call(c,'v2/product/inventory/get','POST',{'Title':'Assay','BrandID':brand['Id'],'Min':3,'BrandType':'LSR'})),1);self.assertEqual(self.call(c,'v2/product/inventory/get','POST',{'Title':'Other'}),[])
   self.call(c,'v2/helpdesk/ticket/create','POST',{'Title':'Urgent issue','Priority':'High'});self.assertEqual(self.call(c,'v2/helpdesk/tickets','POST',{'AnyInt':2}),[])
 def test_stock_delete_and_identity_authority(self):
  with serve.connect() as c:
   p=self.call(c,'v2/product/inventory/create','POST',{'Name':'Assay'});receipt=self.call(c,'v2/product/stock/add','POST',{'ProductId':p['Id'],'Quantity':5,'LotNumber':'L'});issue=self.call(c,'v2/product/stock/remove','POST',{'ProductId':p['Id'],'Quantity':2,'LotNumber':'L'})
   with self.assertRaises(ValueError):self.call(c,'v2/product/stock/delete','POST',{'Id':receipt['Id']})
   self.call(c,'v2/product/stock/delete','POST',{'Id':issue['Id']});self.assertEqual(self.call(c,'v2/product/inventory/'+str(p['Id']))['StockCount'],5)
   self.call(c,'users/update','POST',{'Id':1,'FirstName':'Forged','Email':'forged@example.invalid','Password':'forged','Enabled':False,'Permissions':[{'Type':'admin','Value':3}],'Position':'Sales'})
   own=self.call(c,'myuser');self.assertEqual(own['FirstName'],'Admin');self.assertEqual(own['Email'],'one@example.invalid');self.assertTrue(own['Enabled']);self.assertEqual(own['Position'],'Sales');self.assertTrue(all(x['Value']==3 for x in own['Permissions']))
   with self.assertRaises(ValueError):self.call(c,'shortcuts/create','POST',{'Name':'Bad','UrlParams':'javascript:alert(1)'})
 def test_catalog_migration_preserves_custom_grants(self):
  d={'permissionCatalogVersion':5,'isPermissionsSeeded':True,'budgetPermissionsSeeded':True,'roles':{'System Admin':['users'],'Employee':['is_view']}};policy.migrate_portal(d);self.assertIn('crm_view',d['roles']['System Admin']);self.assertNotIn('crm_view',d['roles']['Employee'])
 def test_stale_and_grant_guard(self):
  with serve.connect() as c:
   path='/api/crm/bridge/is-crm/';p=bridge.handle(c,self.actor,self.perms,path+'preview','GET',{});c.execute('UPDATE workspace SET revision=revision+1')
   with self.assertRaises(ValueError):bridge.handle(c,self.actor,self.perms,path+'run','POST',{'token':p['token']})
   with self.assertRaises(policy.PermissionDenied):bridge.handle(c,self.actor,self.perms-{'is.master-customers.view'},path+'preview','GET',{})
   with self.assertRaises(policy.PermissionDenied):bridge.handle(c,self.actor,self.perms-{'crm.contacts.import'},path+'preview','GET',{})
 def test_http_shared_session_routes_revocation_and_files(self):
  with serve.connect() as c:
   salt,digest,it=serve.password_record('Test-password-123');c.execute('INSERT INTO accounts(id,email,name,role,user_id,password_hash,salt,iterations,created_at) VALUES(?,?,?,?,?,?,?,?,?)',('admin','one@example.invalid','Admin','System Admin','u1',digest,salt,it,'now'));c.execute('INSERT INTO sessions VALUES(?,?,?,?)',(hashlib.sha256(b'fixture').hexdigest(),'admin',int(time.time())+300,int(time.time())))
  class Handler(serve.Handler):
   def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(serve.ROOT),**kwargs)
   def log_message(self,*args):pass
  http=serve.ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start();base='http://127.0.0.1:'+str(http.server_port)
  def req(path,cookie=True,body=None,method=None):
   headers={'Cookie':'biomed_session=fixture'} if cookie else {}
   if body is not None:headers['Content-Type']='application/json'
   r=urllib.request.Request(base+path,headers=headers,data=json.dumps(body).encode() if body is not None else None,method=method)
   try:
    with urllib.request.urlopen(r) as response:return response.status,response.read()
   except urllib.error.HTTPError as e:return e.code,e.read()
  try:
   self.assertEqual(req('/api/crm/session',False)[0],401);self.assertEqual(req('/api/crm/session')[0],200);self.assertEqual(req('/crm/index.html')[0],200);self.assertEqual(req('/reference/ERP_Original_Schema.sql')[0],404);self.assertEqual(req('/%72eference/ERP_Original_Schema.sql')[0],404)
   code,raw=req('/biomedapi/v2/crm/leads/create',body={'LeadName':'HTTP lead'});self.assertEqual(code,200,raw);id=json.loads(raw);self.assertIsInstance(id,int);self.assertEqual(req('/biomedapi/v2/crm/leads/update/'+str(id),body={'LeadName':'PUT lead'},method='PUT')[0],200)
   self.assertEqual(req('/api/crm/export/Leads')[0],200)
   import base64
   png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=');boundary='biomed-crm-test';body=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="test.png"\r\nContent-Type: image/png\r\n\r\n').encode()+png+f'\r\n--{boundary}--\r\n'.encode();upload=urllib.request.Request(base+'/biomedapi/misc/uploadfile',data=body,headers={'Cookie':'biomed_session=fixture','Content-Type':'multipart/form-data; boundary='+boundary})
   with urllib.request.urlopen(upload) as response:filename=response.read().decode()
   self.assertEqual(req('/crm/storage/'+filename)[1],png);self.assertEqual(req('/crm/storage/'+filename,False)[0],401)
   bad=urllib.request.Request(base+'/biomedapi/misc/uploadfile',data=body.replace(b'test.png',b'test.svg'),headers={'Cookie':'biomed_session=fixture','Content-Type':'multipart/form-data; boundary='+boundary})
   with self.assertRaises(urllib.error.HTTPError) as invalid:urllib.request.urlopen(bad)
   self.assertEqual(invalid.exception.code,400)
   with serve.connect() as c:
    portal=json.loads(c.execute("SELECT value FROM workspace WHERE key='biomed_portal_v33_clean'").fetchone()[0]);portal['roles']['Restricted Admin']=[p for p in portal['roles']['System Admin'] if p not in ['crm.logs.view_all','crm.files.view']];c.execute("UPDATE accounts SET role='Restricted Admin' WHERE id='admin'");portal['users'][0]['role']='Restricted Admin';c.execute("UPDATE workspace SET value=? WHERE key='biomed_portal_v33_clean'",(json.dumps(portal),));crm.audit(c,('other',),'Leads',1,'edit',{'private':'Other actor details'})
   code,audit=req('/api/crm/audit');self.assertEqual(code,200);self.assertNotIn(b'Other actor details',audit);self.assertEqual(req('/crm/storage/'+filename)[0],403)
   self.assertEqual(req('/api/auth/login',body={'email':'one@example.invalid','password':'Test-password-123'})[0],200)
   self.assertEqual(req('/api/auth/logout',body={})[0],200);self.assertEqual(req('/api/crm/session')[0],401)
  finally:http.shutdown();http.server_close();thread.join()
if __name__=='__main__':unittest.main()
