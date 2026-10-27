import unittest,tempfile,sqlite3,json,io,sys,time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ai_chat_api as ai,crm_api as crm,copilot_calendar as calendar,copilot_access as access,permissions_policy as policy
class Calendar(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.db=str(Path(self.tmp.name)/'test.db')
  self.actor=('a','a@test','A','Employee','u1');self.other=('b','b@test','B','Employee','u2')
  self.perms={'ai.internal.use','crm_view','crm.events.view','crm.events.create'}
  with self.connect() as c:
   ai.init(c);crm.initialize(c)
   c.execute('CREATE TABLE workspace(key TEXT PRIMARY KEY,value TEXT)')
   for portal in ('u1','u2'):
    user=crm.insert(c,'Users',{'FirstName':portal})
    c.execute('INSERT INTO crm_identity VALUES(?,?)',(portal,user['Id']))
   c.execute("UPDATE ai_settings SET value='true' WHERE key='internal_enabled'")
   access.save(c,self.actor,'a','self',{'calendar_read':True,'calendar_draft':True})
  self.args={'title':'Office meeting','start':'2026-11-02T10:00:00+07:00','end':'2026-11-02T11:00:00+07:00','all_day':False,'location':'Biomed office','plan':'Discuss schedule'}
 def tearDown(self):self.tmp.cleanup()
 def connect(self):return sqlite3.connect(self.db)
 def test_draft_needs_confirmation_and_no_duplicate(self):
  with self.connect() as c:
   draft=calendar.make_draft(c,self.actor,self.perms,self.args)
   self.assertEqual(len(list(crm.rows(c,'Events'))),0)
  with self.connect() as c:
   result=calendar.confirm(c,self.actor,self.perms,draft['draft_id'])
   self.assertEqual(len(list(crm.rows(c,'Events'))),1)
  with self.connect() as c:
   repeated=calendar.confirm(c,self.actor,self.perms,draft['draft_id'])
   self.assertEqual(repeated['event_id'],result['event_id'])
   self.assertEqual(len(list(crm.rows(c,'Events'))),1)
 def test_ownership_permission_expiry(self):
  with self.connect() as c:d=calendar.make_draft(c,self.actor,self.perms,self.args)
  with self.connect() as c:
   with self.assertRaises(ValueError):calendar.confirm(c,self.other,self.perms,d['draft_id'])
   with self.assertRaises(policy.PermissionDenied):calendar.confirm(c,self.actor,{'crm_view','crm.events.view'},d['draft_id'])
   c.execute('UPDATE copilot_calendar_drafts SET expires_at=0')
  with self.connect() as c:
   with self.assertRaises(ValueError):calendar.confirm(c,self.actor,self.perms,d['draft_id'])
 def test_read_respects_own_scope(self):
  with self.connect() as c:
   crm.insert(c,'Events',{'Title':'Own event','MainUserID':1,'StartDate':'2026-11-02T10:00','EndDate':'2026-11-02T11:00'})
   crm.insert(c,'Events',{'Title':'Other employee secret','MainUserID':2,'StartDate':'2026-11-02T10:00','EndDate':'2026-11-02T11:00'})
   result=calendar.list_events(c,self.actor,self.perms,{'from_date':'2026-11-01','to_date':'2026-11-30'})
   self.assertEqual([r['Title'] for r in result['events']],['Own event'])
   with self.assertRaises(ValueError):calendar.list_events(c,self.actor,self.perms,{'from_date':'2026-01-01','to_date':'2026-12-31'})
 def test_model_prepares_only_draft(self):
  responses=[{'output':[{'type':'function_call','name':'calendar_draft','call_id':'c1','arguments':json.dumps(self.args)}]},{'output':[{'type':'message','content':[{'type':'output_text','text':'Review the draft and click Confirm save.'}]}]}]
  with patch.object(calendar.urllib.request,'urlopen',side_effect=[io.BytesIO(json.dumps(r).encode()) for r in responses]):
   result=calendar.answer(self.connect,self.actor,self.perms,{'calendar_read':True,'calendar_draft':True},[('user','Add meeting')],'sk-fake-only','gpt-4.1-mini')
  self.assertEqual(len(result['drafts']),1)
  with self.connect() as c:self.assertEqual(len(list(crm.rows(c,'Events'))),0)
 def test_confirm_endpoint_rechecks_user_limits(self):
  class H:
   path='/api/ai/internal/calendar-confirm'
   def __init__(self,ident):
    raw=json.dumps({'draft_id':ident}).encode();self.headers={'Content-Length':str(len(raw))};self.rfile=io.BytesIO(raw)
   def reply(self,status,data):return status,data
  with self.connect() as c:
   draft=calendar.make_draft(c,self.actor,self.perms,self.args)
   access.save(c,self.actor,'a','admin',{'calendar_draft':False})
  result=ai.handle(H(draft['draft_id']),'POST',self.connect,lambda h:self.actor,lambda a:self.perms,lambda h:True)
  self.assertEqual(result[0],403)
  with self.connect() as c:self.assertEqual(len(list(crm.rows(c,'Events'))),0)
if __name__=='__main__':unittest.main()
