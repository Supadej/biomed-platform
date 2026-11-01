import sys,copy,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import test_crm as fixture,serve,visit_features as vf,crm_api as crm,permissions_policy as policy
class Visits(unittest.TestCase):
 setUp=fixture.CRM.setUp
 tearDown=fixture.CRM.tearDown
 def record(self,**kw):return {'id':'v1','owner':'u1','employee':'u1','visitdate':'2026-10-29T10:30','customer':'QA Hospital','duration':'3','collaborators':['u2'],'customerTypes':['Clinician','User'],'customerStatus':'New','products':['Brand'],'discussion':'Meeting','addCalendar':True,**kw}
 def state(self,r):
  s=copy.deepcopy(self.portal);s['productLines']=['Brand'];s['visits']=[r] if r else [];return s
 def test_calendar_create_update_unlink_relink_delete(self):
  a=copy.deepcopy(self.portal);b=self.state(self.record())
  with serve.connect() as c:
   vf.sync(c,self.actor,self.perms,a,b);vf.sync(c,self.actor,self.perms,b,b);eid=c.execute("select record_id from crm_links where source='portal-visit'").fetchone()[0];e=crm.raw(c,'Events',eid)
   self.assertEqual(e['Title'],'QA Hospital · Brand');self.assertEqual(e['EndDate'],'2026-10-29T13:30');self.assertEqual(e['UserIds'],[2])
   d=self.state(self.record(customer='Updated hospital',duration='24'));vf.sync(c,self.actor,self.perms,b,d);self.assertEqual(c.execute("select record_id from crm_links where source='portal-visit'").fetchone()[0],eid);self.assertEqual(crm.raw(c,'Events',eid)['EndDate'],'2026-10-30T10:30')
   u=self.state(self.record(addCalendar=False));vf.sync(c,self.actor,self.perms,d,u);self.assertIsNone(crm.raw(c,'Events',eid));vf.sync(c,self.actor,self.perms,u,b);vf.sync(c,self.actor,self.perms,b,self.state(None));self.assertEqual(c.execute("select count(*) from crm_links where source='portal-visit'").fetchone()[0],0)
 def test_invalid_records_permissions_and_scope(self):
  for changes in [{'duration':'25'},{'duration':'1.5'},{'customerTypes':['Invalid']},{'customerStatus':'Wrong'},{'products':['Unknown']},{'collaborators':['missing']},{'visitdate':'2026-99-99'},{'visitdate':'2026-10-29'},{'addCalendar':'true'}]:
   with self.assertRaises((ValueError,policy.PermissionDenied)):
    with serve.connect() as c:vf.sync(c,self.actor,self.perms,self.portal,self.state(self.record(**changes)))
  with self.assertRaises(policy.PermissionDenied):
   with serve.connect() as c:vf.sync(c,self.actor,self.perms-{'portal.visits.calendar'},self.portal,self.state(self.record()))
  with self.assertRaises(policy.PermissionDenied):
   with serve.connect() as c:vf.sync(c,('a','','Employee','Employee','u1'),{'portal.visits.create','portal.visits.calendar'},self.portal,self.state(self.record(employee='u2')))
  with serve.connect() as c:self.assertEqual(c.execute("select count(*) from crm_links where source='portal-visit'").fetchone()[0],0)
 def test_legacy(self):
  with serve.connect() as c:
   vf.sync(c,self.actor,self.perms,self.portal,self.portal);n=copy.deepcopy(self.portal);n['visits'][0]['discussion']='Revised legacy note';vf.sync(c,self.actor,self.perms,self.portal,n)
if __name__=='__main__':unittest.main()

class NativeSort(unittest.TestCase):
 setUp=fixture.CRM.setUp
 tearDown=fixture.CRM.tearDown
 def test_native_sort_before_pagination(self):
  import portal_crm as native
  with serve.connect() as c:
   for n in [70,1,300]:crm.insert(c,'Leads',{'LeadName':'Opportunity '+str(n),'MainUserId':1,'ExpectedRevenue':n,'Creation':'2026-10-29'})
   def read(direction):return native.handle(c,self.actor,self.perms,'/api/crm/native/list?entity=Leads&sortKey=ExpectedRevenue&sortDirection='+direction+'&size=1','GET',{})
   self.assertEqual(read('asc')['items'][0]['ExpectedRevenue'],1);self.assertEqual(read('desc')['items'][0]['ExpectedRevenue'],300)
