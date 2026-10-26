"""Staff Portal CRM persistence, binding, concurrency and eligibility checks."""
import sys,json,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import test_crm as fixtures
import serve,crm_api as crm,portal_crm as native,permissions_policy as policy
class Native(unittest.TestCase):
 setUp=fixtures.CRM.setUp
 tearDown=fixtures.CRM.tearDown
 def n(self,c,action,body=None,query='',perms=None):
  return native.handle(c,self.actor,self.perms if perms is None else perms,'/api/crm/native/'+action+query,'GET' if body is None else 'POST',body or {})
 def test_native_crud_paging_and_stale_guard(self):
  with serve.connect() as c:
   for i in range(35):self.n(c,'save',{'entity':'Leads','record':{'LeadName':'Lead '+str(i),'ExpectedRevenue':i}})
   first=self.n(c,'list',query='?entity=Leads&page=1');self.assertEqual(len(first['items']),30);self.assertEqual(first['total'],35)
   row=first['items'][0];self.n(c,'save',{'entity':'Leads','record':{'Id':row['Id'],'CustomerNeeds':'New need'},'version':row['_version']})
   with self.assertRaisesRegex(ValueError,'another session'):self.n(c,'save',{'entity':'Leads','record':{'Id':row['Id'],'CustomerNeeds':'Lost update'},'version':row['_version']})
   self.assertTrue(self.n(c,'history',query='?entity=Leads&id='+str(row['Id'])))
 def test_native_own_scope_and_parent_access(self):
  with serve.connect() as c:
   own=self.n(c,'save',{'entity':'Events','record':{'Title':'Mine','MainUserID':None,'StartDate':'2026-10-26T09:00','EndDate':'2026-10-26T10:00'}})
   other=self.n(c,'save',{'entity':'Events','record':{'Title':'Other','MainUserID':2,'StartDate':'2026-10-26T09:00','EndDate':'2026-10-26T10:00'}})
   p={'crm_view','crm.events.view','crm.logs.view','crm.logs.create'}
   rows=self.n(c,'list',query='?entity=Events',perms=p);self.assertEqual([r['Id'] for r in rows['items']],[own['Id']])
   with self.assertRaises(policy.PermissionDenied):self.n(c,'save',{'entity':'Logs','record':{'EventId':other['Id'],'LogValue':'Forbidden'}},perms=p)
   self.n(c,'save',{'entity':'Logs','record':{'EventId':own['Id'],'LogValue':'Follow up','DateTime':crm.now(),'Type':0,'Visible':True,'SystemLog':'Note'}},perms=p)
 def test_native_project_ticket_and_filters(self):
  with serve.connect() as c:
   project=self.n(c,'save',{'entity':'Projects','record':{'Name':'Launch'}})
   stage=self.n(c,'save',{'entity':'ProjectPipeline','record':{'Name':'Planning','ProjectId':project['Id']}})
   activity=self.n(c,'save',{'entity':'ProjectActivity','record':{'Name':'Seminar','ProjectPipelineId':stage['Id'],'MainUserId':1,'Expense':20,'UserIds':[1,2]}})
   self.assertEqual(self.n(c,'list',query='?entity=ProjectActivity&project='+str(project['Id']))['total'],1)
   self.assertEqual(self.n(c,'list',query='?entity=ProjectActivity&owner=2')['total'],1)
   ticket=self.n(c,'save',{'entity':'HelpDeskTickets','record':{'Title':'Service','AssignedToUserId':1,'Model':'Analyzer'}})
   item=self.n(c,'save',{'entity':'HelpDeskItems','record':{'TicketId':ticket['Id'],'Description':'Part','Quantity':2,'Bill':True}})
   with self.assertRaises(ValueError):self.n(c,'delete',{'entity':'HelpDeskTickets','record':{'Id':ticket['Id']},'version':ticket['_version']})
   self.n(c,'delete',{'entity':'HelpDeskItems','record':{'Id':item['Id']},'version':item['_version']})
   self.n(c,'delete',{'entity':'HelpDeskTickets','record':{'Id':ticket['Id']},'version':ticket['_version']})
 def test_binding_idempotence_lineage_and_automatic_save(self):
  with serve.connect() as c:
   data=self.isdata;data['documents']=[{'id':'q1','ref':'Q1','kind':'quotation','status':'Approved','portalRep':'u1','party':'c1','currency':'THB','date':'2026-10-01','lines':[{'qty':1,'price':100}]},{'id':'o1','sourceId':'q1','ref':'O1','kind':'customer-order','status':'Approved','portalRep':'u1','party':'c1','date':'2026-10-02','lines':[{'qty':1,'price':100}]}]
   c.execute('UPDATE workspace SET value=? WHERE key=?',(json.dumps(data),native.IS))
   cfg=self.n(c,'binding');out=self.n(c,'binding',{'config':{**cfg['config'],'enabled':True},'revision':cfg['revision']});self.assertEqual(out['result']['created'],1)
   self.assertEqual(len(crm.rows(c,'Leads')),1);self.assertEqual(self.n(c,'sync',{})['created'],0)
   data['documents'].append({'id':'inv','sourceId':'o1','ref':'INV','kind':'invoice','status':'Approved','portalRep':'u1','party':'c1','date':'2026-10-03','lines':[{'qty':1,'price':100}]})
   counts=native.sync_documents(c,data,self.actor);self.assertEqual(counts['created'],0);lead=crm.rows(c,'Leads')[0];self.assertEqual(lead['AchivedRevenue'],100);self.assertEqual(len(lead['SourceDocuments']),3)
   p=self.perms-{'crm.leads.import'}
   with self.assertRaises(policy.PermissionDenied):self.n(c,'binding',{'config':cfg['config'],'revision':1},perms=p)
 def test_target_100_percent_gate_zero_and_duplicate(self):
  with serve.connect() as c:
   p=self.portal;p['salesTargets']=[{'id':'target','rep':'u1','line':'Diagnostics','period':'2026-10','amount':100}];p['incentiveSchemes']=[{'id':'s1','rep':'u1','line':'Diagnostics','from':'2026-10','to':'2026-10','threshold':80,'rate':1}]
   def persist(actual):
    p['integrationIS']={'salesActuals':[{'rep':'u1','line':'Diagnostics','period':'2026-10','amount':actual}]};c.execute('UPDATE workspace SET value=? WHERE key=?',(json.dumps(p),native.PORTAL))
   persist(99.99)
   with self.assertRaisesRegex(ValueError,'100%'):self.n(c,'link-target',{'schemeId':'s1'})
   persist(100);r=self.n(c,'link-target',{'schemeId':'s1'});self.assertEqual(r['TargetValue'],100);self.assertEqual(r['EndDate'],'2026-10-31')
   persist(125);again=self.n(c,'link-target',{'schemeId':'s1'});self.assertEqual(again['Id'],r['Id']);self.assertEqual(again['AttainmentAtLink'],125)
   p['salesTargets'][0]['amount']=0;persist(100)
   with self.assertRaises(ValueError):self.n(c,'link-target',{'schemeId':'s1'})
 def test_bad_dates_and_nonfinite_amounts(self):
  with serve.connect() as c:
   with self.assertRaises(ValueError):self.n(c,'save',{'entity':'Events','record':{'Title':'Bad','StartDate':'2026-10-27T12:00','EndDate':'2026-10-26T12:00'}})
   with self.assertRaises(ValueError):self.n(c,'save',{'entity':'Leads','record':{'LeadName':'Bad','ExpectedRevenue':float('inf')}})
if __name__=='__main__':unittest.main()
