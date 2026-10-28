import sys,json,unittest,io
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import test_crm as fixtures
import serve,crm_api as crm,portal_crm as native,instrument_service as service,service_referrals as refs,service_catalog as catalog
class Referrals(unittest.TestCase):
 setUp=fixtures.CRM.setUp
 tearDown=fixtures.CRM.tearDown
 def new_ticket(self,c):return native.handle(c,self.actor,self.perms,'/api/crm/native/save','POST',{'entity':'HelpDeskTickets','record':{'Title':'Referral ticket','Priority':'High','Currency':'EUR'}})
 def test_multiple_independent_jobs_and_movement_and_derived_parts(self):
  with serve.connect() as c:
   serve.project(c,json.dumps(self.isdata));ticket=self.new_ticket(c);ins=[r for r in service.rows(c) if r['kind']=='instruments'];part=service.save(c,self.actor,self.perms,{'kind':'parts','productId':'p1'})
   jobs=[]
   for i in range(2):jobs.append(service.save(c,self.actor,self.perms,{'kind':'jobs','instrumentId':ins[i]['id'],'ticketId':ticket['Id'],'status':'Scheduled','partsUsed':[{'partId':part,'qty':i+1,'unitCost':10}],'serviceAmount':100,'currency':'THB'}))
   loc=catalog.setup(c)['locations'][0];movement=service.save(c,self.actor,self.perms,{'kind':'movements','instrumentId':ins[1]['id'],'ticketId':ticket['Id'],'date':'2026-10-28','toLocation':loc})
   data=refs.summary(c,self.actor,self.perms,ticket['Id']);self.assertEqual(len(data['records']),3);self.assertEqual(len(data['parts']),2);self.assertEqual(sum(p['qty'] for p in data['parts']),3);self.assertEqual(crm.rows(c,'HelpDeskItems'),[])
   numbers=[x['jobNo'] for x in data['records'] if x['kind']=='jobs'];self.assertEqual(len(set(numbers+[ticket['JobNumber']])),3)
   self.assertEqual(crm.raw(c,'HelpDeskTickets',ticket['Id'])['Priority'],'High')
   with self.assertRaises(ValueError):crm.mutate(c,self.actor,self.perms,crm.user_id(c,self.actor),'HelpDeskTickets','delete',{'Id':ticket['Id']})
 def test_link_existing_stale_guard_and_unlink(self):
  with serve.connect() as c:
   ticket=self.new_ticket(c);inst=next(r for r in service.rows(c) if r['kind']=='instruments');ident=service.save(c,self.actor,self.perms,{'kind':'jobs','instrumentId':inst['id'],'status':'Scheduled'})
   native.handle(c,self.actor,self.perms,'/api/crm/native/link-service','POST',{'ticket':ticket['Id'],'recordId':ident,'version':1})
   with self.assertRaises(ValueError):native.handle(c,self.actor,self.perms,'/api/crm/native/link-service','POST',{'ticket':ticket['Id'],'recordId':ident,'version':1})
   record=next(r for r in service.rows(c) if r['id']==ident);record['ticketId']='';service.save(c,self.actor,self.perms,record);self.assertEqual(refs.linked_records(c,self.actor,self.perms,ticket['Id']),[])
 def test_transaction_rolls_back_new_ticket_if_service_save_fails(self):
  with serve.connect() as c:inst=next(r for r in service.rows(c) if r['kind']=='instruments');before=len(crm.rows(c,'HelpDeskTickets'))
  body={'action':'save','record':{'kind':'movements','instrumentId':inst['id'],'date':'2026-10-28','toLocation':'NOT IN LOCATION LIST'},'newTicket':{'Title':'Must roll back','Priority':'Normal','Currency':'THB'}}
  raw=json.dumps(body).encode()
  class H:
   headers={'Content-Length':str(len(raw))};rfile=io.BytesIO(raw)
   def reply(self,status,payload):return status,payload
  self.assertEqual(service.handle(H(),'POST',serve.connect,lambda h:self.actor,lambda a:self.perms,lambda h:True)[0],400)
  with serve.connect() as c:self.assertEqual(len(crm.rows(c,'HelpDeskTickets')),before)
 def test_referral_permissions_and_priority_migration(self):
  with serve.connect() as c:
   ticket=self.new_ticket(c)
   with self.assertRaises(Exception):refs.ticket(c,self.actor,self.perms-{'crm.tickets.view'},ticket['Id'])
   self.assertEqual(refs.linked_records(c,self.actor,self.perms-{'service.view'},ticket['Id']),[])
   c.execute("DELETE FROM fse_migrations WHERE name='helpdesk-priority-levels-v1'")
   old=crm.raw(c,'HelpDeskTickets',ticket['Id']);old['Priority']=2;crm.update(c,'HelpDeskTickets',ticket['Id'],old)
   self.assertEqual(refs.migrate_helpdesk_priorities(c),1);row=crm.raw(c,'HelpDeskTickets',ticket['Id']);self.assertEqual(row['Priority'],'Normal');self.assertEqual(row['LegacyPriority'],2);self.assertIsNone(refs.migrate_helpdesk_priorities(c))
 def test_responsibles_include_helpdesk_user_without_engineer_role(self):
  with serve.connect() as c:
   p=self.portal;p['roles']['Intake']=['crm_view','crm.tickets.view'];p['users'][1]['role']='Intake';c.execute('UPDATE workspace SET value=? WHERE key=?',(json.dumps(p),native.PORTAL));crm.bind_users(c)
   self.assertIn('u2',{r['id'] for r in catalog.helpdesk_responsibles(c)});self.assertNotIn('u2',{r['id'] for r in catalog.engineers(c)})
   native.handle(c,self.actor,self.perms,'/api/crm/native/save','POST',{'entity':'HelpDeskTickets','record':{'Title':'Assigned intake','AssignedToUserId':2,'Priority':'Low','Currency':'CNY'}})
   for change in [{'Priority':'Urgent'},{'Currency':'GBP'}]:
    with self.assertRaises(ValueError):native.handle(c,self.actor,self.perms,'/api/crm/native/save','POST',{'entity':'HelpDeskTickets','record':{'Title':'Invalid',**change}})
if __name__=='__main__':unittest.main()
