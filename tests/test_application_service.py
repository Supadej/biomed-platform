import sys,json,unittest,io
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import test_crm as fixtures
import serve,application_service as app,permissions_policy as policy,portal_crm as crm,crm_api
class ApplicationService(unittest.TestCase):
 def setUp(self):
  fixtures.CRM.setUp(self)
  with serve.connect() as c:
   self.account(c,'u1');c.execute("UPDATE accounts SET role='System Admin' WHERE user_id='u1'")
   choices=app.references.change(c,self.actor,self.perms,{'operation':'add','name':'Hospital'});self.customerId=next(x['id'] for x in choices if x['name']=='Hospital')
 tearDown=fixtures.CRM.tearDown
 def record(self,**values):return dict(dict(title='Training',customer='Hospital',customerId=self.customerId,specialist='u1',serviceType='Application training',status='Scheduled',start='2026-10-29T09:00'),**values)
 def account(self,c,uid):
  if not c.execute('SELECT 1 FROM accounts WHERE user_id=?',(uid,)).fetchone():c.execute('INSERT INTO accounts VALUES(?,?,?,?,?,?,?,?,0,0,0,?)',(uid,uid+'@example.invalid',uid,'Employee',uid,b'x',b'x',1,'2026-10-29'))
 def test_crud_versions_scope_and_audit(self):
  with serve.connect() as c:
   self.account(c,'u1');self.account(c,'u2');r=app.save(c,self.actor,self.perms,self.record());self.assertRegex(r['reference'],r'^BMDAS\d{2}-\d{2}-\d{2}/1$');self.assertEqual(len(app.records(c,self.actor,self.perms)),1)
   with self.assertRaises(ValueError):app.save(c,self.actor,self.perms,dict(r,version=0))
   limited={'application_service.view','application_service.edit'};other=('two','two@example.invalid','Two','Employee','u2')
   self.assertEqual(app.records(c,other,limited),[])
   with self.assertRaises(policy.PermissionDenied):app.save(c,other,limited,dict(r,title='Forged'))
   with self.assertRaises((policy.PermissionDenied,ValueError)):app.save(c,self.actor,{'application_service.view','application_service.create'},self.record(specialist='u2'))
   r=app.save(c,self.actor,self.perms,dict(r,status='Completed',workPerformed='Trained',result='Competency confirmed'));self.assertEqual(r['version'],2)
   app.delete(c,self.actor,self.perms,r['id'],2);self.assertEqual(app.records(c,self.actor,self.perms),[]);self.assertEqual(c.execute("SELECT COUNT(*) FROM application_service_audit WHERE record_id!='customer-references'").fetchone()[0],3)
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
  status,result=app.handle(H(),'POST',serve.connect,lambda h:self.actor,lambda a:self.perms,lambda h:True);self.assertEqual(status,200);self.assertIn('BMDAS',result['csv'])
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
 def test_customer_choices_products_and_eligible_roles(self):
  with serve.connect() as c:
   self.account(c,'u2');self.assertNotIn('u2',{x['id'] for x in app.references.specialists(c)})
   p=json.loads(c.execute("SELECT value FROM workspace WHERE key='biomed_portal_v33_clean'").fetchone()[0]);p['roles']['Employee'].append('application_service.perform');p['productLines']=['Diagnostics','Life Science'];c.execute("UPDATE workspace SET value=? WHERE key='biomed_portal_v33_clean'",(json.dumps(p),))
   self.assertIn('u2',{x['id'] for x in app.references.specialists(c)})
   r=app.save(c,self.actor,self.perms,self.record(products=['Diagnostics','Life Science']));self.assertEqual(len(r['products']),2)
   app.references.change(c,self.actor,self.perms,{'operation':'remove','id':self.customerId})
   self.assertEqual(app.save(c,self.actor,self.perms,dict(r,topic='Updated'))['customer'],'Hospital')
   with self.assertRaises(ValueError):app.save(c,self.actor,self.perms,self.record())
   with self.assertRaises(policy.PermissionDenied):app.references.change(c,self.actor,{'application_service.view'},{'operation':'add','name':'Blocked'})
 def test_calendar_create_update_unlink_and_delete(self):
  with serve.connect() as c:
   r=app.save(c,self.actor,self.perms,self.record(calendarEnabled=True));ident=r['calendarEventId'];event=crm_api.raw(c,'Events',ident);self.assertEqual(event['Title'],'Hospital');self.assertEqual(event['MainUserID'],crm_api.user_id(c,self.actor));self.assertTrue(event['IsAllDay'])
   r=app.save(c,self.actor,self.perms,dict(r,start='2026-10-30T10:00',calendarDate='2026-11-04'));self.assertEqual(r['calendarEventId'],ident);self.assertEqual(crm_api.raw(c,'Events',ident)['StartDate'],'2026-11-04T00:00:00')
   with self.assertRaises(policy.PermissionDenied):app.save(c,self.actor,self.perms-{'application_service.calendar'},dict(r,calendarEnabled=False))
   r=app.save(c,self.actor,self.perms,dict(r,calendarEnabled=False));self.assertIsNone(crm_api.raw(c,'Events',ident));self.assertNotIn('calendarEventId',r)
   r=app.save(c,self.actor,self.perms,dict(r,calendarEnabled=True));app.delete(c,self.actor,self.perms,r['id'],r['version']);self.assertIsNone(crm_api.raw(c,'Events',r['calendarEventId']))
 def test_optional_signature_bound_to_application_report(self):
  with serve.connect() as c:
   sig={'name':'Customer','consent':True,'strokes':[[[0.1,0.1],[0.8,0.6]]]}
   r=app.save(c,self.actor,self.perms,self.record(customerSignature=sig,feedbackSolved='Yes'));self.assertEqual(r['customerSignature']['name'],'Customer');self.assertTrue(r['customerSignature']['reportHash'])
   r=app.save(c,self.actor,self.perms,r)
   with self.assertRaises(ValueError):app.save(c,self.actor,self.perms,dict(r,result='Changed report'))
   r=app.save(c,self.actor,self.perms,dict(r,result='Changed report',customerSignature=None));self.assertNotIn('customerSignature',r)
   with self.assertRaises(ValueError):app.save(c,self.actor,self.perms,dict(r,customerSignature={'name':'C','consent':True,'strokes':[[[2,0],[0,1]]]}))
 def test_number_reuse_and_topic_optional(self):
  with serve.connect() as c:
   r=app.save(c,self.actor,self.perms,self.record(title='',topic=''));ref=r['reference'];self.assertEqual(r['topic'],'');app.delete(c,self.actor,self.perms,r['id'],r['version']);new=app.save(c,self.actor,self.perms,self.record());self.assertNotEqual(ref,new['reference']);self.assertEqual(app.save(c,self.actor,self.perms,dict(new,reference='Forged'))['reference'],new['reference'])
 def test_existing_job_migration_preserves_topic_and_old_reference(self):
  with serve.connect() as c:
   c.execute("DELETE FROM application_reference_migrations WHERE name='application-jobs-v2'")
   prior=self.record();prior.update(id='legacy-job',reference='APP-000009',createdAt='2026-10-28T10:00:00+00:00')
   c.execute('INSERT INTO application_service_records VALUES(?,?,1,0)',('legacy-job',json.dumps(prior)))
   app.migrate(c);r=app.records(c,self.actor,self.perms)[0];self.assertEqual(r['legacyReference'],'APP-000009');self.assertEqual(r['topic'],'Training');self.assertRegex(r['reference'],r'^BMDAS28-10-26/\d+$');self.assertEqual(r['customerId'],self.customerId);self.assertEqual(r['version'],2)
   app.migrate(c);self.assertEqual(app.records(c,self.actor,self.perms)[0]['reference'],r['reference'])
 def test_calendar_assignment_and_instrument_permission_boundaries(self):
  with serve.connect() as c:
   self.account(c,'u2');p=json.loads(c.execute("SELECT value FROM workspace WHERE key='biomed_portal_v33_clean'").fetchone()[0]);p['roles']['Employee'].append('application_service.perform');c.execute("UPDATE workspace SET value=? WHERE key='biomed_portal_v33_clean'",(json.dumps(p),))
   with self.assertRaises(policy.PermissionDenied):app.save(c,self.actor,self.perms-{'crm.events.assign'},self.record(specialist='u2',calendarEnabled=True))
   with self.assertRaises(policy.PermissionDenied):app.save(c,self.actor,self.perms-{'crm.events.create'},self.record(calendarEnabled=True))
   with self.assertRaises(policy.PermissionDenied):app.save(c,self.actor,self.perms-{'service.instruments.view'},self.record(instrumentId='unavailable'))
 def test_catalog_migration(self):
  old={'roles':{'System Admin':[],'Custom':['requests']},'permissionCatalogVersion':20};policy.migrate_portal(old)
  self.assertIn('application_service.assign',old['roles']['Application Service Manager']);self.assertNotIn('application_service.view_all',old['roles']['Application Specialist']);self.assertIn('application_service.view',old['roles']['System Admin']);self.assertNotIn('application_service.view',old['roles']['Custom'])
if __name__=='__main__':unittest.main()
