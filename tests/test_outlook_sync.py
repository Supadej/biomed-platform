import sys,json,unittest,copy,os,time,io
from pathlib import Path
from unittest.mock import patch
from cryptography.fernet import Fernet
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import test_crm as fixtures
import serve,outlook_sync as out,crm_api as crm,portal_crm,minutes_ack,permissions_policy as policy
class Outlook(unittest.TestCase):
 def setUp(self):
  fixtures.CRM.setUp(self);self.actor=('admin','one@example.invalid','Admin','System Admin','u1')
  self.env=patch.dict(os.environ,{'BIOMED_OUTLOOK_TENANT_ID':str(__import__('uuid').uuid4()),'BIOMED_OUTLOOK_CLIENT_ID':str(__import__('uuid').uuid4()),'BIOMED_OUTLOOK_CLIENT_SECRET':'fixture-not-real','BIOMED_OUTLOOK_REDIRECT_URI':'http://127.0.0.1:8765/api/outlook/callback','BIOMED_OUTLOOK_ENCRYPTION_KEY':Fernet.generate_key().decode()});self.env.start();self.addCleanup(self.env.stop)
  with serve.connect() as c:
   c.execute('INSERT INTO accounts(id,email,name,role,user_id,password_hash,salt,iterations,created_at) VALUES(?,?,?,?,?,?,?,?,?)',('admin','one@example.invalid','Admin','System Admin','u1','fixture','fixture',1,'now'))
   data={'access_token':'secret-access','refresh_token':'secret-refresh','expires':time.time()+3600};c.execute('INSERT INTO outlook_accounts(account_id,profile_id,email,tokens) VALUES(?,?,?,?)',('admin','mailbox-one','one@example.invalid',out.crypt().encrypt(json.dumps(data).encode())))
  self.remotes={};self.calls=[];self.serial=0
  self.fake=patch.object(out,'graph',side_effect=self.graph);self.fake.start();self.addCleanup(self.fake.stop)
 tearDown=fixtures.CRM.tearDown
 def graph(self,token,path,method='GET',data=None,etag=None):
  self.calls.append((path,method,copy.deepcopy(data),etag));self.assertEqual(token,'secret-access')
  if path.startswith('/me?$select'):return {'id':'mailbox-one','mail':'one@example.invalid'}
  if path.startswith('/me/calendarView?'):return {'value':list(self.remotes.values())}
  if method=='POST':
   # Model Microsoft's transactionId idempotency for retries.
   existing=next((x for x in self.remotes.values() if x.get('transactionId')==data.get('transactionId')),None)
   if existing:return copy.deepcopy(existing)
   self.serial+=1;rid='remote-'+str(self.serial);r={'id':rid,'@odata.etag':'v1','type':'singleInstance','webLink':'https://outlook.office.com/calendar/item/'+rid,**copy.deepcopy(data)};self.remotes[rid]=r;return copy.deepcopy(r)
  rid=path.split('/')[-1]
  if rid not in self.remotes:raise out.GraphError(404)
  if method=='DELETE':del self.remotes[rid];return {}
  if method=='PATCH':
   if etag and etag!=self.remotes[rid]['@odata.etag']:raise out.GraphError(412)
   self.remotes[rid].update(copy.deepcopy(data));self.remotes[rid]['@odata.etag']='v'+str(time.time());return copy.deepcopy(self.remotes[rid])
  return copy.deepcopy(self.remotes[rid])
 def event(self,**extra):
  with serve.connect() as c:
   r=crm.mutate(c,self.actor,self.perms,1,'Events','create',{'Title':'Private planning','StartDate':'2026-10-28T09:00','EndDate':'2026-10-28T10:00','Location':'Lab','UserIds':[2],**extra});out.set_event(c,self.actor,self.perms,r['Id'],True);return r['Id']
 def sync(self):return out.sync(serve.connect,self.actor,self.perms,lambda a:self.perms)
 def test_push_idempotence_edit_deletion_and_no_invitations(self):
  eid=self.event();self.sync();self.sync();self.assertEqual(len(self.remotes),1)
  self.assertEqual(sum(method=='POST' for _,method,_,_ in self.calls),1)
  self.assertFalse(any('attendees' in (data or {}) for _,_,data,_ in self.calls))
  with serve.connect() as c:crm.mutate(c,self.actor,self.perms,1,'Events','edit',{'Id':eid,'Title':'Updated from portal'})
  self.sync();self.assertEqual(next(iter(self.remotes.values()))['subject'],'Updated from portal')
  with serve.connect() as c:crm.mutate(c,self.actor,self.perms,1,'Events','delete',{'Id':eid})
  self.sync();self.assertEqual(self.remotes,{})
 def test_two_way_and_conflict_resolution(self):
  eid=self.event();self.sync();rid=next(iter(self.remotes))
  with serve.connect() as c:c.execute("UPDATE outlook_accounts SET mode='two-way'")
  self.remotes[rid]['subject']='Changed in Outlook';self.sync()
  with serve.connect() as c:self.assertEqual(crm.raw(c,'Events',eid)['Title'],'Changed in Outlook');crm.mutate(c,self.actor,self.perms,1,'Events','edit',{'Id':eid,'Title':'Concurrent portal change'})
  self.remotes[rid]['subject']='Concurrent Outlook change';result=self.sync();self.assertEqual(result['failed'],1)
  with serve.connect() as c:
   self.assertIn('Conflict:',c.execute('SELECT error FROM outlook_events').fetchone()[0]);self.assertEqual(crm.raw(c,'Events',eid)['Title'],'Concurrent portal change');c.execute("UPDATE outlook_events SET resolution='outlook'")
  self.sync()
  with serve.connect() as c:self.assertEqual(crm.raw(c,'Events',eid)['Title'],'Concurrent Outlook change')
 def test_minutes_remain_portal_controlled(self):
  with serve.connect() as c:
   rid=minutes_ack.dispatch(c,self.actor,self.perms,'POST',{}, {'action':'save','publish':True,'record':{'title':'Official meeting','body':'Do not export confidential body','date':'2026-10-28','employees':['u2'],'internalAttendees':['u2'],'calendarLink':True,'meetingStart':'2026-10-28T09:00','meetingEnd':'2026-10-28T10:00'}})['id'];eid=crm.rows(c,'Events')[0]['Id'];out.set_event(c,self.actor,self.perms,eid,True);c.execute("UPDATE outlook_accounts SET mode='two-way'")
  self.sync();remote=next(iter(self.remotes.values()));self.assertNotIn('Do not export confidential body',str(remote));remote['subject']='Outlook attempted change';self.sync();self.assertEqual(remote['subject'],'Official meeting')
  with serve.connect() as c:self.assertEqual(minutes_ack.get(c,rid,'u1',self.perms)['revision'],1)
 def test_private_cache_is_self_only_and_no_duplicate_copies(self):
  self.event();self.sync();other={'id':'private-meeting','subject':'Personal appointment','start':{'dateTime':'2026-10-28T05:00:00','timeZone':'UTC'},'end':{'dateTime':'2026-10-28T06:00:00','timeZone':'UTC'},'type':'singleInstance'};self.remotes[other['id']]=other
  with serve.connect() as c:c.execute('UPDATE outlook_accounts SET show_private=1')
  self.sync()
  with serve.connect() as c:
   own=out.status(c,self.actor,self.perms);self.assertEqual(len(own['privateEvents']),1);self.assertEqual(own['privateEvents'][0]['start'],'2026-10-28T12:00:00');self.assertNotIn('secret-access',json.dumps(own));self.assertFalse(out.status(c,('second','two@example.invalid','Second','Employee','u2'),self.perms)['connected'])
 def test_refresh_rotation_and_credential_encryption(self):
  with serve.connect() as c:
   data={'access_token':'expired','refresh_token':'old-refresh','expires':0};c.execute('UPDATE outlook_accounts SET tokens=?',(out.crypt().encrypt(json.dumps(data).encode()),))
  with patch.object(out,'token_request',return_value={'access_token':'new-access','refresh_token':'rotated-refresh','expires_in':3600}):self.assertEqual(out.access(serve.connect,'admin'),'new-access')
  with serve.connect() as c:
   blob=c.execute('SELECT tokens FROM outlook_accounts').fetchone()[0];self.assertNotIn(b'new-access',blob);self.assertEqual(json.loads(out.crypt().decrypt(blob))['refresh_token'],'rotated-refresh')
 def test_oauth_pkce_single_use_email_match_and_state_cookie(self):
  with serve.connect() as c:url,state=out.authorize(c,self.actor,self.perms)
  self.assertIn('code_challenge_method=S256',url);self.assertNotIn('fixture-not-real',url)
  with self.assertRaises(ValueError):out.callback(serve.connect,{'state':state,'code':'fixture'},'wrong-cookie',lambda a:self.perms)
  with patch.object(out,'token_request',return_value={'access_token':'secret-access','refresh_token':'secret-refresh','expires_in':3600}):out.callback(serve.connect,{'state':state,'code':'fixture'},state,lambda a:self.perms)
  with self.assertRaises(ValueError):out.callback(serve.connect,{'state':state,'code':'fixture'},state,lambda a:self.perms)
  with serve.connect() as c:url,state=out.authorize(c,self.actor,self.perms)
  with patch.object(out,'token_request',return_value={'access_token':'secret-access','refresh_token':'secret-refresh','expires_in':3600}),patch.object(out,'graph',return_value={'id':'other','mail':'outsider@example.invalid'}):
   with self.assertRaises(ValueError):out.callback(serve.connect,{'state':state,'code':'fixture'},state,lambda a:self.perms)
 def test_scope_lease_and_permission_revocation(self):
  eid=self.event()
  with serve.connect() as c:
   c.execute('UPDATE outlook_accounts SET lease_until=?',(time.time()+900,))
  with self.assertRaises(ValueError):self.sync()
  with serve.connect() as c:c.execute('UPDATE outlook_accounts SET lease_until=0')
  with self.assertRaises(policy.PermissionDenied):out.sync(serve.connect,self.actor,set())
  self.sync()
  # Remove visibility and ensure only this integration's personal copy is removed.
  with serve.connect() as c:crm.update(c,'Events',eid,{'MainUserID':2,'UserIds':[]})
  reduced=self.perms-{'crm.events.view_all'};out.sync(serve.connect,self.actor,reduced,lambda a:reduced);self.assertEqual(len(self.remotes),0)
 def test_deleted_remote_reports_recovery_without_duplicate_post(self):
  self.event();self.sync();self.remotes.clear();result=self.sync();self.assertEqual(result['failed'],1);self.assertEqual(len(self.remotes),0)
  with serve.connect() as c:self.assertTrue(c.execute('SELECT error FROM outlook_events').fetchone()[0].startswith('Outlook copy was deleted'))
 def test_all_day_and_safe_graph_host(self):
  r={'Title':'All day','StartDate':'2026-10-28T09:00','EndDate':'2026-10-28T10:00','IsAllDay':True};shape=out.local_shape(r);self.assertEqual(shape['start']['dateTime'],'2026-10-28T00:00:00');self.assertEqual(shape['end']['dateTime'],'2026-10-29T00:00:00');self.assertEqual(out.pull_values(shape)['EndDate'],'2026-10-28T23:59:00')
  with self.assertRaises(ValueError):out.request('https://attacker.invalid/steal')
  # Restore the real graph wrapper to verify continuation-link validation.
  self.fake.stop()
  with self.assertRaises(ValueError):out.graph('secret-access','https://attacker.invalid/steal')
 def test_native_event_selection_is_personal(self):
  with serve.connect() as c:
   result=portal_crm.handle(c,self.actor,self.perms,'/api/crm/native/save','POST',{'entity':'Events','record':{'Title':'Selected for Outlook','StartDate':'2026-10-28T09:00','EndDate':'2026-10-28T10:00','OutlookSync':True}})
   mine=portal_crm.handle(c,self.actor,self.perms,'/api/crm/native/record?entity=Events&id='+str(result['Id']),'GET',{})
   other=portal_crm.handle(c,('second','two@example.invalid','Second','Employee','u2'),self.perms,'/api/crm/native/record?entity=Events&id='+str(result['Id']),'GET',{})
   self.assertTrue(mine['OutlookSync']);self.assertFalse(other['OutlookSync'])
 def test_copy_converted_to_meeting_is_not_updated_or_cancelled(self):
  eid=self.event();self.sync();remote=next(iter(self.remotes.values()));remote['attendees']=[{'emailAddress':{'address':'someone@example.invalid'}}]
  with serve.connect() as c:crm.mutate(c,self.actor,self.perms,1,'Events','edit',{'Id':eid,'Title':'Changed portal'})
  self.assertEqual(self.sync()['failed'],1);self.assertFalse(any(method=='PATCH' for _,method,_,_ in self.calls))
  with serve.connect() as c:crm.mutate(c,self.actor,self.perms,1,'Events','delete',{'Id':eid})
  self.assertEqual(self.sync()['failed'],1);self.assertFalse(any(method=='DELETE' for _,method,_,_ in self.calls))
 def test_http_auth_origin_and_unconfigured_status(self):
  class H:
   path='/api/outlook/status';headers={'Content-Length':'2'};rfile=io.BytesIO(b'{}')
   def reply(self,status,value):return status,value
  self.assertEqual(out.handle(H(),'GET',serve.connect,lambda h:None,lambda a:self.perms,lambda h:True)[0],401)
  H.path='/api/outlook/disconnect';self.assertEqual(out.handle(H(),'POST',serve.connect,lambda h:self.actor,lambda a:self.perms,lambda h:False)[0],403)
  with patch.dict(os.environ,{'BIOMED_OUTLOOK_CLIENT_SECRET':''}):self.assertFalse(out.config()['configured'])
if __name__=='__main__':unittest.main()
