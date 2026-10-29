import sys,json,unittest,io
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import test_crm as fixtures
import serve,application_service as app,permissions_policy as policy,portal_crm as crm,crm_api
class ApplicationService(unittest.TestCase):
 setUp=fixtures.CRM.setUp
 tearDown=fixtures.CRM.tearDown
 def record(self,**values):return dict(dict(title='Training',customer='Hospital',specialist='u1',serviceType='Application training',status='Scheduled',start='2026-10-29T09:00'),**values)
 def account(self,c,uid):
  if not c.execute('SELECT 1 FROM accounts WHERE user_id=?',(uid,)).fetchone():c.execute('INSERT INTO accounts VALUES(?,?,?,?,?,?,?,?,0,0,0,?)',(uid,uid+'@example.invalid',uid,'Employee',uid,b'x',b'x',1,'2026-10-29'))
 def test_crud_versions_scope_and_audit(self):
  with serve.connect() as c:
   self.account(c,'u1');self.account(c,'u2');r=app.save(c,self.actor,self.perms,self.record());self.assertEqual(r['reference'],'APP-000001');self.assertEqual(len(app.records(c,self.actor,self.perms)),1)
   with self.assertRaises(ValueError):app.save(c,self.actor,self.perms,dict(r,version=0))
   limited={'application_service.view','application_service.edit'};other=('two','two@example.invalid','Two','Employee','u2')
   self.assertEqual(app.records(c,other,limited),[])
   with self.assertRaises(policy.PermissionDenied):app.save(c,other,limited,dict(r,title='Forged'))
   with self.assertRaises(policy.PermissionDenied):app.save(c,self.actor,{'application_service.view','application_service.create'},self.record(specialist='u2'))
   r=app.save(c,self.actor,self.perms,dict(r,status='Completed',workPerformed='Trained',result='Competency confirmed'));self.assertEqual(r['version'],2)
   app.delete(c,self.actor,self.perms,r['id'],2);self.assertEqual(app.records(c,self.actor,self.perms),[]);self.assertEqual(c.execute('SELECT COUNT(*) FROM application_service_audit').fetchone()[0],3)
 def test_helpdesk_link_create_and_delete_guard(self):
  with serve.connect() as c:
   self.account(c,'u1');ticket=crm.handle(c,self.actor,self.perms,'/api/crm/native/save','POST',{'entity':'HelpDeskTickets','record':{'Title':'Application issue','Priority':'Normal','Currency':'THB'}})
   r=app.save(c,self.actor,self.perms,self.record(ticketId=ticket['Id']))
   with self.assertRaises(ValueError):crm_api.mutate(c,self.actor,self.perms,crm_api.user_id(c,self.actor),'HelpDeskTickets','delete',{'Id':ticket['Id']})
   with self.assertRaises(policy.PermissionDenied):app.save(c,self.actor,self.perms-{'crm.tickets.view'},dict(r,ticketId=''))
   r=app.save(c,self.actor,self.perms,dict(r,ticketId=''));self.assertIsNone(r['ticketId'])
   r=app.save(c,self.actor,self.perms,self.record(newTicket={'Title':'New app ticket','Priority':'Normal','Currency':'THB'}));self.assertTrue(r['ticketId']);self.assertEqual(crm_api.raw(c,'HelpDeskTickets',r['ticketId'])['Title'],'New app ticket')
 def test_validation_and_permissions(self):
  with serve.connect() as c:
   self.account(c,'u1')
   for changes in [{'end':'2026-10-28T08:00'},{'start':'bad'},{'status':'Invalid'},{'status':'Completed'},{'followUpDate':'2026-99-99'},{'specialist':'missing'},{'instrumentId':'missing'}]:
    with self.assertRaises((ValueError,policy.PermissionDenied)):app.save(c,self.actor,self.perms,self.record(**changes))
   with self.assertRaises(policy.PermissionDenied):app.save(c,self.actor,{'application_service.view'},self.record())
 def test_http_auth_origin_and_export_scope(self):
  with serve.connect() as c:self.account(c,'u1');r=app.save(c,self.actor,self.perms,self.record())
  raw=json.dumps({'action':'export','ids':[r['id']]}).encode()
  class H:
   path='/api/application-service';headers={'Content-Length':str(len(raw))}
   def __init__(self):self.rfile=io.BytesIO(raw)
   def reply(self,status,payload):return status,payload
  self.assertEqual(app.handle(H(),'POST',serve.connect,lambda h:None,lambda a:self.perms,lambda h:True)[0],401)
  self.assertEqual(app.handle(H(),'POST',serve.connect,lambda h:self.actor,lambda a:self.perms,lambda h:False)[0],403)
  self.assertEqual(app.handle(H(),'POST',serve.connect,lambda h:self.actor,lambda a:self.perms-{'application_service.export'},lambda h:True)[0],403)
  status,result=app.handle(H(),'POST',serve.connect,lambda h:self.actor,lambda a:self.perms,lambda h:True);self.assertEqual(status,200);self.assertIn('APP-000001',result['csv'])
 def test_date_query_and_direct_record_keep_scope(self):
  with serve.connect() as c:
   self.account(c,'u1');r=app.save(c,self.actor,self.perms,self.record())
   self.assertEqual(app.records(c,self.actor,self.perms,'2026-11-01','2026-11-30'),[])
   self.assertEqual(len(app.records(c,self.actor,self.perms,'2026-11-01','2026-11-30',r['id'])),1)
   other=('two','two@example.invalid','Two','Employee','u2')
   self.assertEqual(app.records(c,other,{'application_service.view'},'2026-11-01','2026-11-30',r['id']),[])
   with self.assertRaises(ValueError):app.records(c,self.actor,self.perms,'2026-12-01','2026-11-01')
 def test_new_ticket_transaction_rollback(self):
  with serve.connect() as c:self.account(c,'u1');before=len(crm_api.rows(c,'HelpDeskTickets'))
  raw=json.dumps({'action':'save','record':self.record(instrumentId='invalid',newTicket={'Title':'Should roll back'})}).encode()
  class H:
   headers={'Content-Length':str(len(raw))}
   def __init__(self):self.rfile=io.BytesIO(raw)
   def reply(self,status,payload):return status,payload
  self.assertEqual(app.handle(H(),'POST',serve.connect,lambda h:self.actor,lambda a:self.perms,lambda h:True)[0],400)
  with serve.connect() as c:self.assertEqual(len(crm_api.rows(c,'HelpDeskTickets')),before)
 def test_catalog_migration(self):
  old={'roles':{'System Admin':[],'Custom':['requests']},'permissionCatalogVersion':20};policy.migrate_portal(old)
  self.assertIn('application_service.assign',old['roles']['Application Service Manager']);self.assertNotIn('application_service.view_all',old['roles']['Application Specialist']);self.assertIn('application_service.view',old['roles']['System Admin']);self.assertNotIn('application_service.view',old['roles']['Custom'])
if __name__=='__main__':unittest.main()
