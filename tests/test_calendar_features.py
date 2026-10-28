import sys,json,base64,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import test_crm as fixtures
import serve,portal_crm as p,crm_api as crm,minutes_ack as minutes,permissions_policy as policy
class Calendar(unittest.TestCase):
 setUp=fixtures.CRM.setUp
 tearDown=fixtures.CRM.tearDown
 def call(self,c,action='save',data=None,query='',perms=None,actor=None):return p.handle(c,actor or self.actor,self.perms if perms is None else perms,'/api/crm/native/'+action+query,'GET' if data is None else 'POST',data or {})
 def make(self,c,**extra):return self.call(c,data={'entity':'Events','record':{'Title':'Calendar customer visit','StartDate':'2026-10-28T09:00','EndDate':'2026-10-28T10:00','MainUserID':1,'UserIds':[2],**extra}})
 def test_master_fields_and_validation(self):
  with serve.connect() as c:
   portal={**self.portal,'brands':[{'id':'b1','name':'Phadia'},{'id':'b2','name':'NIOX'}]};c.execute("UPDATE workspace SET value=? WHERE key='biomed_portal_v33_clean'",(json.dumps(portal),))
   refs=self.call(c,'calendar-references');self.assertEqual(refs['brands'],['Phadia','NIOX']);self.assertEqual(refs['customers'][0]['id'],'c1');self.assertEqual(refs['employees'][1]['label'],'Second Person')
   r=self.make(c,BrandNames=['Phadia','NIOX'],ISCustomerId='c1',AdditionalContacts='Jane, 0812345678, jane@example.invalid',AdditionalProducts='Brand A, Brand B',Location='Lab 3')
   self.assertEqual(r['BrandNames'],['Phadia','NIOX']);self.assertEqual(r['ISCustomerId'],'c1');self.assertEqual(r['Location'],'Lab 3')
   for values in [{'BrandNames':['Unknown']},{'ISCustomerId':'missing'},{'EndDate':'2026-10-27T09:00'}]:
    with self.assertRaises(ValueError):self.make(c,**values)
 def test_multiple_files_and_event_scope(self):
  with serve.connect() as c:
   a=lambda name:{'name':name,'data':base64.b64encode(b'test attachment').decode()}
   r=self.make(c,Attachments=[a('agenda.pdf'),a('notes.txt')]);self.assertEqual(len(r['Attachments']),2)
   fid=r['Attachments'][0]['id'];download=self.call(c,'calendar-file',query='?id='+str(r['Id'])+'&file='+fid);self.assertEqual(download['_calendarDownload'][1],b'test attachment')
   restricted={'crm_view','crm.events.view'}
   with self.assertRaises(policy.PermissionDenied):self.call(c,'calendar-file',query='?id='+str(r['Id'])+'&file='+fid,perms=restricted,actor=(*self.actor[:4],'unknown'))
   r=self.call(c,data={'entity':'Events','version':r['_version'],'record':{'Id':r['Id'],'Attachments':[r['Attachments'][1]]}})
   with self.assertRaises(policy.PermissionDenied):self.call(c,'calendar-file',query='?id='+str(r['Id'])+'&file='+fid)
   with self.assertRaises(ValueError):self.call(c,data={'entity':'Events','version':r['_version'],'record':{'Id':r['Id'],'Attachments':[{'id':'other-event'}]}})
   history=self.call(c,'history',query='?entity=Events&id='+str(r['Id']));self.assertTrue(any(x['action']=='create' for x in history));self.assertTrue(any(x['action']=='edit' for x in history));self.assertIn('actorName',history[0]);self.assertNotIn('data',history[0]['detail'])
 def test_minutes_link_kept_and_calendar_overrides_survive_content_revision(self):
  with serve.connect() as c:
   rec={'type':'Meeting minutes','title':'Minutes meeting','date':'2026-10-28','body':'Published text','employees':['u2'],'internalAttendees':['u2'],'calendarLink':True,'meetingStart':'2026-10-28T09:00','meetingEnd':'2026-10-28T10:00'}
   rid=minutes.dispatch(c,self.actor,self.perms,'POST',{}, {'action':'save','publish':True,'record':rec})['id'];event=crm.rows(c,'Events')[0]
   version=c.execute("SELECT version FROM crm_records WHERE entity='Events' AND id=?",(event['Id'],)).fetchone()[0]
   updated=self.call(c,data={'entity':'Events','version':version,'record':{'Id':event['Id'],'Title':'Calendar edited','EndDate':'2026-10-28T11:00'}});self.assertEqual(updated['MinutesId'],rid)
   minute=minutes.get(c,rid,'u1',self.perms);self.assertEqual(minute['body'],'Published text');self.assertEqual(minute['revision'],1)
   minutes.dispatch(c,self.actor,self.perms,'POST',{}, {'action':'save','publish':True,'record':{**minute,'body':'New text'}})
   current=crm.raw(c,'Events',event['Id']);self.assertEqual(current['EndDate'],'2026-10-28T11:00');self.assertEqual(current['Title'],'Calendar edited')
   minute=minutes.get(c,rid,'u1',self.perms);minutes.dispatch(c,self.actor,self.perms,'POST',{}, {'action':'save','publish':True,'record':{**minute,'meetingEnd':'2026-10-28T12:00'}});self.assertEqual(crm.raw(c,'Events',event['Id'])['EndDate'],'2026-10-28T12:00')
   with self.assertRaises(policy.PermissionDenied):self.call(c,'delete',{'entity':'Events','record':{'Id':event['Id']},'version':c.execute("SELECT version FROM crm_records WHERE entity='Events' AND id=?",(event['Id'],)).fetchone()[0]})
if __name__=='__main__':unittest.main()
