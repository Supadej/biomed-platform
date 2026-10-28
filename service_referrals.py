"""Optional Helpdesk referrals: one ticket may reference many independent service records."""
import json,datetime
import permissions_policy as policy

def initialize(c):
 c.execute('CREATE TABLE IF NOT EXISTS service_ticket_links(record_id TEXT PRIMARY KEY REFERENCES fse_records(id) ON DELETE CASCADE,ticket_id INTEGER NOT NULL,created_at TEXT NOT NULL)')
 c.execute('CREATE INDEX IF NOT EXISTS service_ticket_parent ON service_ticket_links(ticket_id)')
def ticket(c,actor,perms,ident):
 import crm_api as crm
 policy.need(perms,'crm_view');crm.need(perms,'tickets');crm.bind_users(c);uid=crm.user_id(c,actor)
 try:ident=int(ident)
 except (TypeError,ValueError):raise ValueError('Select a Helpdesk ticket')
 obj=crm.raw(c,'HelpDeskTickets',ident)
 if not obj or not crm.visible(c,perms,'HelpDeskTickets',obj,uid):raise policy.PermissionDenied('Ticket is unavailable or outside your Helpdesk scope')
 return obj

def visible_tickets(c,actor,perms):
 import crm_api as crm
 if not {'crm_view','crm.tickets.view'}<=set(perms):return []
 crm.bind_users(c)
 uid=crm.user_id(c,actor)
 return [{'id':r['Id'],'name':str(r.get('JobNumber') or '#'+str(r['Id']))+' · '+str(r.get('Title') or ''),'title':r.get('Title'),'instrumentId':r.get('ServiceInstrumentId'),'serial':r.get('SerialNumber')} for r in crm.rows(c,'HelpDeskTickets') if crm.visible(c,perms,'HelpDeskTickets',r,uid)]
def validate(c,actor,perms,record,prior):
 if record.get('kind') not in ['jobs','movements']:
  if record.get('ticketId'):raise ValueError('Only service jobs and movements have Helpdesk referrals')
  return
 old=(prior or {}).get('ticketId');new=record.get('ticketId')
 if str(old or '')!=str(new or ''):
  if old:ticket(c,actor,perms,old)
  if new:ticket(c,actor,perms,new)
 if new:record['ticketId']=int(new)
 else:record.pop('ticketId',None)
def persist(c,record,actor=None):
 initialize(c);old=c.execute('SELECT ticket_id FROM service_ticket_links WHERE record_id=?',(record['id'],)).fetchone();previous=old[0] if old else None;current=record.get('ticketId')
 if previous==current:return
 if current:c.execute('INSERT INTO service_ticket_links VALUES(?,?,?) ON CONFLICT(record_id) DO UPDATE SET ticket_id=excluded.ticket_id,created_at=excluded.created_at',(record['id'],current,datetime.datetime.now(datetime.timezone.utc).isoformat()))
 else:c.execute('DELETE FROM service_ticket_links WHERE record_id=?',(record['id'],))
 if actor:
  import crm_api
  for ident,action in [(previous,'unlink service referral'),(current,'link service referral')]:
   if ident:crm_api.audit(c,actor,'HelpDeskTickets',ident,action,{'serviceRecordId':record['id'],'kind':record['kind'],'jobNo':record.get('jobNo')})
def create_ticket(c,actor,perms,record,values):
 import portal_crm,crm_api
 allowed={k:values.get(k) for k in ['Title','Problem','Priority','Currency','AssignedToUserId'] if values.get(k) not in (None,'')}
 if not str(allowed.get('Title') or '').strip():raise ValueError('New Helpdesk ticket needs a title')
 allowed.setdefault('Priority','Normal');allowed.setdefault('Currency','THB')
 stages=sorted(crm_api.rows(c,'HelpDeskPipelines'),key=lambda x:x.get('Order') or x['Id'])
 stage=next((s for s in stages if portal_crm.workflow_stage_type('HelpDeskPipelines',s)=='open'),None)
 if stage:allowed['PipelineId']=stage['Id']
 if record.get('instrumentId'):allowed['ServiceInstrumentId']=record['instrumentId']
 result=portal_crm.handle(c,actor,perms,'/api/crm/native/save','POST',{'entity':'HelpDeskTickets','record':allowed})
 return result['Id']
def linked_records(c,actor,perms,ticket_id):
 ticket(c,actor,perms,ticket_id);initialize(c)
 if 'service.view' not in perms:return []
 return [dict(json.loads(p),version=v) for kind,p,v in c.execute('SELECT r.kind,r.payload,r.version FROM service_ticket_links l JOIN fse_records r ON r.id=l.record_id WHERE l.ticket_id=?',(int(ticket_id),)) if 'service.'+kind+'.view' in perms]
def job_parts(c,job):
 result=[dict(p,jobId=job['id'],jobNo=job.get('jobNo'),currency=p.get('currency') or job.get('currency') or 'THB',source='Service job') for p in job.get('partsUsed',[])]
 for payload, in c.execute("SELECT payload FROM fse_records WHERE kind='replacements'"):
  p=json.loads(payload)
  matched=p.get('serviceJobId')==job['id'] if p.get('serviceJobId') else not p.get('reviewRequired') and p.get('jobNo')==job.get('jobNo') and p.get('instrumentId')==job.get('instrumentId')
  if matched:result.append(dict(p,jobId=job['id'],jobNo=job.get('jobNo'),currency=p.get('currency') or job.get('currency') or 'THB',source='Historical job part'))
 return result

def summary(c,actor,perms,ticket_id):
 rows=linked_records(c,actor,perms,ticket_id);inst={i:json.loads(p) for i,p in c.execute("SELECT id,payload FROM fse_records WHERE kind='instruments'")}
 for r in rows:r['serial']=inst.get(r.get('instrumentId'),{}).get('serial','')
 parts=[p for r in rows if r['kind']=='jobs' for p in job_parts(c,r)]
 return {'records':rows,'parts':parts,'canLink':any({'service.view','service.edit','service.'+k+'.view','service.'+k+'.edit'}<=set(perms) for k in ['jobs','movements']),'canCreateJob':{'service.view','service.edit','service.jobs.view','service.jobs.create'}<=set(perms),'canCreateMovement':{'service.view','service.edit','service.movements.view','service.movements.create'}<=set(perms)}

def migrate_helpdesk_priorities(c):
 """Standardize the offered levels while retaining unmapped historical values."""
 c.execute('CREATE TABLE IF NOT EXISTS fse_migrations(name TEXT PRIMARY KEY,applied_at TEXT,detail TEXT)')
 name='helpdesk-priority-levels-v1'
 if c.execute('SELECT 1 FROM fse_migrations WHERE name=?',(name,)).fetchone():return
 count=0
 for ident,payload in c.execute("SELECT id,payload FROM crm_records WHERE entity='HelpDeskTickets' AND deleted=0").fetchall():
  r=json.loads(payload)
  if r.get('Priority') not in ['High','Normal','Low']:
   if r.get('Priority') not in (None,''):r.setdefault('LegacyPriority',r['Priority'])
   r['Priority']='Normal';c.execute("UPDATE crm_records SET payload=?,version=version+1 WHERE entity='HelpDeskTickets' AND id=?",(json.dumps(r,ensure_ascii=False),ident));count+=1
 c.execute('INSERT INTO fse_migrations VALUES(?,?,?)',(name,datetime.datetime.now(datetime.timezone.utc).isoformat(),json.dumps({'standardizedToNormal':count,'originalValuesRetained':True})))
 return count
