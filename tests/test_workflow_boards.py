"""Custom workflow stages, cross-stage movement and incentive summary invariants."""
import json,unittest
import test_crm as fixtures
import serve,crm_api as crm,portal_crm as native,permissions_policy as policy
class WorkflowBoards(unittest.TestCase):
 setUp=fixtures.CRM.setUp
 tearDown=fixtures.CRM.tearDown
 def n(self,c,action,body=None,query='',perms=None):return native.handle(c,self.actor,self.perms if perms is None else perms,'/api/crm/native/'+action+query,'GET' if body is None else 'POST',body or {})
 def save(self,c,entity,values,version=None):return self.n(c,'save',{'entity':entity,'record':values,'version':version})
 def test_custom_stages_create_rename_colour_order_and_validation(self):
  with serve.connect() as c:
   stages=self.n(c,'save-stages',{'stages':[{'record':{'PipelineName':'Review','Order':1,'Color':'#aa4477','StageType':'open'}}]});r=next(x for x in stages if x['PipelineName']=='Review')
   stages=self.n(c,'save-stages',{'stages':[{'record':{'Id':r['Id'],'PipelineName':'Technical review','Order':0,'Color':'#005577','StageType':'won'},'version':r['_version']}]});self.assertEqual(stages[0]['PipelineName'],'Technical review');self.assertEqual(stages[0]['Color'],'#005577')
   before=len(crm.rows(c,'CRMPipelines'))
   with self.assertRaises(ValueError):self.n(c,'save-stages',{'stages':[{'record':{'PipelineName':'Should roll back'}},{'record':{'PipelineName':'Bad colour','Color':'red;display:none'}}]})
   self.assertEqual(len(crm.rows(c,'CRMPipelines')),before)
 def test_board_counts_and_totals_cover_all_pages(self):
  with serve.connect() as c:
   for stage,count in [(1,35),(2,32)]:
    for i in range(count):self.save(c,'Leads',{'LeadName':f'{stage} Lead {i}','CRMPipelineId':stage,'ExpectedRevenue':10,'Currency':'THB'})
   board=self.n(c,'workflow-board',query='?entity=Leads');self.assertEqual(board['total'],67)
   columns={x['stage']['Id']:x for x in board['columns'] if x['stage']}
   self.assertEqual(columns[1]['count'],35);self.assertEqual(len(columns[1]['items']),30);self.assertEqual(columns[1]['totals']['THB']['expected'],350)
   page=self.n(c,'list',query='?entity=Leads&field=CRMPipelineId&value=1&page=2&size=30');self.assertEqual(len(page['items']),5)
 def test_move_and_delete_used_stage_preserve_record_details(self):
  with serve.connect() as c:
   r=self.save(c,'Leads',{'LeadName':'Tracked','CRMPipelineId':1,'ExpectedRevenue':120,'CustomerNeeds':'Keep notes'})
   moved=self.save(c,'Leads',{'Id':r['Id'],'CRMPipelineId':5},r['_version']);self.assertTrue(moved['WinOrLost'])
   stage=self.n(c,'record',query='?entity=CRMPipelines&id=5')
   out=self.n(c,'stage-delete',{'id':5,'version':stage['_version'],'replacementId':2});self.assertEqual(out['moved'],1)
   lead=crm.raw(c,'Leads',r['Id']);self.assertEqual(lead['CRMPipelineId'],2);self.assertEqual(lead['ExpectedRevenue'],120);self.assertEqual(lead['CustomerNeeds'],'Keep notes');self.assertIsNone(lead['WinOrLost'])
 def test_used_stage_removal_checks_scope_and_rolls_back_linked_snapshots(self):
  with serve.connect() as c:
   a=self.save(c,'Leads',{'LeadName':'A','CRMPipelineId':1});b=crm.insert(c,'Leads',{'LeadName':'Locked','MainUserId':1,'CRMPipelineId':1,'_bridgeSource':'portal-crm'})
   stage=self.n(c,'record',query='?entity=CRMPipelines&id=1')
   with self.assertRaises(policy.PermissionDenied):self.n(c,'stage-delete',{'id':1,'version':stage['_version'],'replacementId':2})
   self.assertEqual(crm.raw(c,'Leads',a['Id'])['CRMPipelineId'],1);self.assertIsNotNone(crm.raw(c,'CRMPipelines',1))
   with self.assertRaises(policy.PermissionDenied):self.n(c,'stage-delete',{'id':1,'version':stage['_version'],'replacementId':'unassigned'},perms=self.perms-{'crm.leads.view_all'})
 def test_product_summary_uses_100_threshold_exact_mapping_currency_and_union(self):
  with serve.connect() as c:
   p=self.portal;p['productLines']=['Diagnostics'];p['salesTargets']=[{'rep':'u1','line':'Diagnostics','period':'2026-10','amount':100},{'rep':'u1','line':'Diagnostics','period':'2026-11','amount':200}]
   p['incentiveSchemes']=[{'id':'s1','rep':'u1','line':'Diagnostics','from':'2026-10','to':'2026-11','threshold':100},{'id':'s2','rep':'u1','line':'Diagnostics','from':'2026-10','to':'2026-10','threshold':100},{'id':'s3','rep':'u1','line':'Diagnostics','from':'2026-10','to':'2026-11','threshold':80}]
   p['integrationIS']={'salesActuals':[{'rep':'u1','line':'Diagnostics','period':'2026-10','amount':80},{'rep':'u1','line':'Diagnostics','period':'2026-11','amount':120}]};c.execute('UPDATE workspace SET value=? WHERE key=?',(json.dumps(p),native.PORTAL))
   for name,stage,value,currency,product in [('Active',1,60,'THB','Diagnostics'),('Won',5,30,'THB','Diagnostics'),('Lost',6,90,'THB','Diagnostics'),('Foreign',1,100,'EUR','Diagnostics'),('Unmapped',1,10,'THB','')]:self.save(c,'Leads',{'LeadName':name,'CRMPipelineId':stage,'ExpectedRevenue':value,'Currency':currency,'ProductLine':product,'Expected':'2026-10-20'})
   summary=self.n(c,'sales-summary');self.assertEqual(len(summary['targets']),2);self.assertEqual(summary['totalTarget'],300);self.assertEqual(summary['totalActual'],200);self.assertEqual(summary['totalExpected'],90);self.assertEqual(summary['lostCount'],1);self.assertEqual(summary['unmappedCount'],1)
   self.assertAlmostEqual(summary['attainment'],200/300*100);self.assertFalse(summary['targets'][0]['eligible'])
   octs=self.n(c,'sales-summary',query='?from=2026-10-01&to=2026-10-31');self.assertEqual(octs['totalTarget'],100);self.assertEqual(octs['totalActual'],80)
   private=self.n(c,'sales-summary',perms=self.perms-{'incentives'});self.assertFalse(private['targetsAvailable']);self.assertNotIn('totalActual',private)
 def test_helpdesk_stage_customization_board_movement_and_removal(self):
  with serve.connect() as c:
   stages=self.n(c,'save-stages',{'entity':'HelpDeskPipelines','stages':[{'record':{'Name':'Engineer visit','Order':2,'StageType':'in_progress','Color':'#224488'}}]});stage=next(x for x in stages if x['Name']=='Engineer visit')
   ticket=self.save(c,'HelpDeskTickets',{'Title':'Repair','PipelineId':stage['Id']});self.assertEqual(ticket['Status'],'Engineer visit')
   board=self.n(c,'workflow-board',query='?entity=HelpDeskTickets');self.assertEqual(next(x for x in board['columns'] if x['stage'] and x['stage']['Id']==stage['Id'])['count'],1)
   self.n(c,'stage-delete',{'entity':'HelpDeskPipelines','id':stage['Id'],'version':stage['_version'],'replacementId':'unassigned'})
   self.assertIsNone(crm.raw(c,'HelpDeskTickets',ticket['Id'])['PipelineId']);self.assertEqual(crm.raw(c,'HelpDeskTickets',ticket['Id'])['Status'],'Unassigned')
 def test_project_stages_remain_project_specific_and_keep_unassigned_activity(self):
  with serve.connect() as c:
   a=self.save(c,'Projects',{'Name':'A'});b=self.save(c,'Projects',{'Name':'B'})
   stages=self.n(c,'save-stages',{'entity':'ProjectPipeline','project':a['Id'],'stages':[{'record':{'Name':'Plan','ProjectId':a['Id'],'StageType':'open','Color':'#224488'}}]});stage=stages[0]
   other=self.save(c,'ProjectPipeline',{'Name':'B stage','ProjectId':b['Id']})
   activity=self.save(c,'ProjectActivity',{'Name':'Task','ProjectPipelineId':stage['Id']});self.assertEqual(activity['ProjectId'],a['Id'])
   with self.assertRaises(ValueError):self.n(c,'stage-delete',{'entity':'ProjectPipeline','id':stage['Id'],'version':stage['_version'],'replacementId':other['Id']})
   self.n(c,'stage-delete',{'entity':'ProjectPipeline','id':stage['Id'],'version':stage['_version'],'replacementId':'unassigned'})
   record=crm.raw(c,'ProjectActivity',activity['Id']);self.assertEqual(record['ProjectId'],a['Id']);self.assertIsNone(record['ProjectPipelineId'])
   board=self.n(c,'workflow-board',query='?entity=ProjectActivity&project='+str(a['Id']));self.assertEqual(board['total'],1);self.assertEqual(board['columns'][0]['count'],1)
if __name__=='__main__':unittest.main()
