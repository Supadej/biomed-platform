import sys,json,unittest,io
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import test_crm as fixtures
import serve,minutes_ack as m,permissions_policy as policy
class Minutes(unittest.TestCase):
 setUp=fixtures.CRM.setUp
 tearDown=fixtures.CRM.tearDown
 viewer=('v','v@example.invalid','Second Person','Employee','u2')
 basic={'minutes','portal.minutes.view','portal.minutes.acknowledge'}
 def call(self,c,body=None,actor=None,perms=None,query=None):
  return m.dispatch(c,actor or self.actor,self.perms if perms is None else perms,'POST' if body else 'GET',query or {},body or {})
 def make(self,c,publish=True,**extra):
  record={'type':'Meeting minutes','title':'Confidential minutes','date':'2026-10-28','body':'Meeting text','decisions':'Decision','actions':'Follow up','employees':['u2'],'requiresAck':True,**extra}
  ident=self.call(c,{'action':'save','publish':publish,'record':record})['id']
  return self.call(c,query={'id':ident})['record']
 def test_selected_view_only_and_unselected_denied(self):
  with serve.connect() as c:
   r=self.make(c)
   selected=self.call(c,actor=self.viewer,perms=self.basic,query={'id':r['id']})['record']
   self.assertEqual(selected['body'],'Meeting text');self.assertFalse(selected['canEdit']);self.assertNotIn('register',selected)
   outsider=(*self.viewer[:4],'u3')
   self.assertEqual(self.call(c,actor=outsider,perms=self.basic)['records'],[])
   with self.assertRaises(policy.PermissionDenied):self.call(c,actor=outsider,perms=self.basic,query={'id':r['id']})
   with self.assertRaises(policy.PermissionDenied):self.call(c,{'action':'save','publish':True,'record':r},self.viewer,self.basic|{'portal.minutes.edit','portal.minutes.publish'})
   with self.assertRaises(policy.PermissionDenied):self.call(c,{'action':'export','id':r['id']},self.viewer,self.basic|{'portal.minutes.export'})
 def test_acknowledgement_self_only_idempotent_and_revision_bound(self):
  with serve.connect() as c:
   r=self.make(c);body={'action':'acknowledge','id':r['id'],'revision':1,'userId':'u1'}
   
   with self.assertRaises(policy.PermissionDenied):self.call(c,body)
   first=self.call(c,body,self.viewer,self.basic)['record']['myAcknowledgedAt'];second=self.call(c,body,self.viewer,self.basic)['record']['myAcknowledgedAt'];self.assertEqual(first,second)
   self.assertEqual(c.execute('SELECT user_id FROM minutes_acknowledgements').fetchone()[0],'u2')
   self.call(c,{'action':'save','publish':True,'record':{**r,'body':'New revision'}})
   with self.assertRaises(ValueError):self.call(c,body,self.viewer,self.basic)
   current=self.call(c,actor=self.viewer,perms=self.basic,query={'id':r['id']})['record'];self.assertEqual(current['revision'],2);self.assertIsNone(current['myAcknowledgedAt'])
   self.call(c,{**body,'revision':2},self.viewer,self.basic);self.assertEqual(c.execute('SELECT COUNT(*) FROM minutes_acknowledgements').fetchone()[0],2)
 def test_drafts_hidden_and_issued_records_preserved(self):
  with serve.connect() as c:
   draft=self.make(c,False)
   self.assertEqual(self.call(c,actor=self.viewer,perms=self.basic)['records'],[])
   self.call(c,{'action':'save','publish':True,'record':draft})
   current=self.call(c,query={'id':draft['id']})['record']
   with self.assertRaises(ValueError):self.call(c,{'action':'save','publish':False,'record':current})
   with self.assertRaises(policy.PermissionDenied):self.call(c,{'action':'delete','id':current['id'],'version':current['version']})
   with self.assertRaises(ValueError):self.call(c,{'action':'save','publish':True,'record':draft})
 def test_audience_restricted_on_new_revision_and_register_export(self):
  with serve.connect() as c:
   r=self.make(c)
   self.call(c,{'action':'save','publish':True,'record':{**r,'employees':['u1']}})
   with self.assertRaises(policy.PermissionDenied):self.call(c,actor=self.viewer,perms=self.basic,query={'id':r['id']})
   exported=self.call(c,{'action':'export','id':r['id']})['record'];self.assertEqual(len(exported['register']),1);self.assertEqual(exported['register'][0]['employee'],'Admin One')
 def test_validation(self):
  with serve.connect() as c:
   for extra in [{'employees':['not-a-user']},{'employees':[]},{'body':''},{'dueDate':'2026-10-01'},{'url':'javascript:alert(1)'}]:
    with self.assertRaises(ValueError):self.make(c,**extra)
   with self.assertRaises(policy.PermissionDenied):self.call(c,{'action':'save','record':{}},self.viewer,self.basic)
 def test_attachments_access_and_revision_retention(self):
  import base64
  with serve.connect() as c:
   r=self.make(c,attachments=[{'name':'minutes.pdf','data':base64.b64encode(b'%PDF sample').decode()}]);fid=r['attachments'][0]['id']
   self.assertNotIn('data',r['attachments'][0])
   self.assertEqual(self.call(c,actor=self.viewer,perms=self.basic,query={'action':'file','id':r['id'],'file':fid})['download'][1],b'%PDF sample')
   with self.assertRaises(policy.PermissionDenied):self.call(c,actor=(*self.viewer[:4],'u3'),perms=self.basic,query={'action':'file','id':r['id'],'file':fid})
   with self.assertRaises(ValueError):self.call(c,{'action':'save','publish':True,'record':{**r,'attachments':[{'id':'foreign'}]}})
   self.call(c,{'action':'save','publish':True,'record':{**r,'attachments':[]}})
   with self.assertRaises(policy.PermissionDenied):self.call(c,actor=self.viewer,perms=self.basic,query={'action':'file','id':r['id'],'file':fid})
   old=__import__('json').loads(c.execute('SELECT payload FROM minutes_revisions WHERE record_id=? AND revision=1',(r['id'],)).fetchone()[0]);self.assertEqual(old['attachments'][0]['id'],fid)
   for attachment in [{'name':'bad.html','data':'eA=='},{'name':'../bad.pdf','data':'eA=='},{'name':'bad.pdf','data':'!invalid'}]:
    with self.assertRaises(ValueError):self.make(c,attachments=[attachment])
 def test_calendar_publish_update_unlink_and_scope(self):
  import crm_api as crm
  with serve.connect() as c:
   fields={'internalAttendees':['u2'],'externalAttendees':'Guest, Hospital','chairman':'u1','calendarLink':True,'meetingStart':'2026-10-28T09:00','meetingEnd':'2026-10-28T10:00','employees':['u1']}
   draft=self.make(c,False,**fields);self.assertEqual(crm.rows(c,'Events'),[])
   self.call(c,{'action':'save','publish':True,'record':draft});r=self.call(c,query={'id':draft['id']})['record'];self.assertEqual(r['employees'],['u1','u2']);self.assertEqual(r['chairmanName'],'Admin One')
   event=crm.rows(c,'Events')[0];self.assertTrue(crm.visible(c,self.perms,'Events',event,2));self.assertFalse(crm.visible(c,self.perms,'Events',event,999))
   with self.assertRaises(policy.PermissionDenied):crm.mutate(c,self.actor,self.perms,1,'Events','edit',{'Id':event['Id'],'Title':'Detached'})
   self.call(c,{'action':'save','publish':True,'record':{**r,'title':'Changed meeting','meetingEnd':'2026-10-28T11:00'}})
   events=crm.rows(c,'Events');self.assertEqual(len(events),1);self.assertEqual(events[0]['Id'],event['Id']);self.assertEqual(events[0]['EndDate'],'2026-10-28T11:00')
   r=self.call(c,query={'id':r['id']})['record'];self.call(c,{'action':'save','publish':True,'record':{**r,'calendarLink':False}});self.assertEqual(crm.rows(c,'Events'),[])
   r=self.call(c,query={'id':r['id']})['record'];self.call(c,{'action':'save','publish':True,'record':{**r,**fields}});self.assertEqual(crm.rows(c,'Events')[0]['Id'],event['Id'])
 def test_meeting_validation(self):
  with serve.connect() as c:
   for extra in [{'internalAttendees':['invalid']},{'chairman':'invalid'},{'calendarLink':True},{'calendarLink':True,'internalAttendees':['u2'],'meetingStart':'2026-10-28T10:00','meetingEnd':'2026-10-28T09:00'}]:
    with self.assertRaises(ValueError):self.make(c,**extra)
   r=self.make(c,type='Acknowledgement',internalAttendees=['u2'],chairman='u1',externalAttendees='Guest',calendarLink=True)
   self.assertEqual(r['internalAttendees'],[]);self.assertEqual(r['chairman'],'');self.assertFalse(r['calendarLink'])
 def test_reader_role_migration_grants_no_authoring(self):
  data={'roles':{'Employee':['announcements']},'permissionCatalogVersion':13}
  policy.migrate_portal(data)
  self.assertTrue(self.basic<=set(data['roles']['Employee']));self.assertNotIn('portal.minutes.create',data['roles']['Employee']);self.assertIn('portal.minutes.manage',data['roles']['Minutes Coordinator'])
 def test_http_authentication_and_origin(self):
  class H:
   path='/api/minutes';headers={'Content-Length':'2'};rfile=io.BytesIO(b'{}')
   def reply(self,status,value):return status,value
  self.assertEqual(m.handle(H(),'GET',serve.connect,lambda h:None,lambda a:self.perms,lambda h:True)[0],401)
  self.assertEqual(m.handle(H(),'POST',serve.connect,lambda h:self.actor,lambda a:self.perms,lambda h:False)[0],403)
if __name__=='__main__':unittest.main()
