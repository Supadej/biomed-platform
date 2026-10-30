"""Selected-employee meeting records and revision-specific acknowledgements."""
import datetime,json,sqlite3,uuid,base64,binascii
from pathlib import PurePath
from urllib.parse import quote
from urllib.parse import urlsplit,parse_qs
import permissions_policy as policy

def initialize(c):
 c.execute('CREATE TABLE IF NOT EXISTS minutes_records(id TEXT PRIMARY KEY,payload TEXT NOT NULL,version INTEGER NOT NULL)')
 c.execute('CREATE TABLE IF NOT EXISTS minutes_revisions(record_id TEXT,revision INTEGER,payload TEXT NOT NULL,PRIMARY KEY(record_id,revision))')
 c.execute('CREATE TABLE IF NOT EXISTS minutes_acknowledgements(record_id TEXT,revision INTEGER,user_id TEXT,acknowledged_at TEXT NOT NULL,PRIMARY KEY(record_id,revision,user_id))')
 c.execute('CREATE TABLE IF NOT EXISTS minutes_audit(id INTEGER PRIMARY KEY,record_id TEXT,at TEXT,actor TEXT,action TEXT,detail TEXT)')
 c.execute('CREATE TABLE IF NOT EXISTS minutes_files(id TEXT PRIMARY KEY,record_id TEXT NOT NULL,name TEXT NOT NULL,content BLOB NOT NULL)')
 c.execute('CREATE TABLE IF NOT EXISTS minutes_calendar(record_id TEXT PRIMARY KEY,event_id INTEGER NOT NULL)')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def people(c):
 row=c.execute("SELECT value FROM workspace WHERE key='biomed_portal_v33_clean'").fetchone();portal=json.loads(row[0]) if row else {};accounts={str(pid):(name,disabled) for pid,name,disabled in c.execute('SELECT user_id,name,disabled FROM accounts')}
 return [dict(id=str(u['id']),name=accounts.get(str(u['id']),(u.get('name',''),0))[0],department=u.get('department',''),active=u.get('active',True) is not False and not accounts.get(str(u['id']),('',0))[1]) for u in portal.get('users',[]) if u.get('id')]
def manager(perms):return 'portal.minutes.manage' in perms
def can_edit(r,pid,perms):return manager(perms) or r['owner']==pid and 'portal.minutes.edit' in perms
def visible(r,pid,perms):return policy.visibility.visible(perms,'portal.minutes',r) and (manager(perms) or r['owner']==pid or r['status']=='Published' and pid in r['employees'])
def get(c,ident,pid,perms):
 row=c.execute('SELECT payload,version FROM minutes_records WHERE id=?',(ident,)).fetchone()
 if not row:raise ValueError('Document not found')
 r=dict(json.loads(row[0]),version=row[1])
 if not visible(r,pid,perms):raise policy.PermissionDenied('This document is shared only with its selected employees')
 return r
def audit(c,r,pid,action,detail=None):c.execute('INSERT INTO minutes_audit(record_id,at,actor,action,detail) VALUES(?,?,?,?,?)',(r['id'],now(),pid,action,json.dumps(detail or {},ensure_ascii=False)))
def present(c,r,pid,perms,names,detail=False):
 acknowledgements={u:at for u,at in c.execute('SELECT user_id,acknowledged_at FROM minutes_acknowledgements WHERE record_id=? AND revision=?',(r['id'],r['revision']))}
 own=r['owner']==pid or manager(perms)
 out={k:v for k,v in r.items() if detail or k not in ['body','decisions','actions','attendees','url','employees','attachments','internalAttendees','externalAttendees','chairman']}
 out.update(ownerName=names.get(r['owner'],'Employee'),employeeCount=len(r['employees']),ackCount=sum(u in acknowledgements for u in r['employees']),myAcknowledgedAt=acknowledgements.get(pid),canEdit=can_edit(r,pid,perms),canPublish=can_edit(r,pid,perms) and 'portal.minutes.publish' in perms,canDelete=can_edit(r,pid,perms) and r['status']=='Draft' and 'portal.minutes.delete' in perms,canExport=own and 'portal.minutes.export' in perms,canAcknowledge=r['status']=='Published' and r['requiresAck'] and pid in r['employees'] and 'portal.minutes.acknowledge' in perms)
 if detail:
  out['internalAttendeeNames']=[names.get(u,'Employee') for u in r.get('internalAttendees',[])]
  out['chairmanName']=names.get(r.get('chairman'),'')
  out['employeeNames']=[names.get(u,'Employee') for u in r['employees']]
  if own:
   out['register']=[{'employee':names.get(u,'Employee'),'status':'Acknowledged' if u in acknowledgements else 'Pending','at':acknowledgements.get(u,'')} for u in r['employees']]
   out['revisionHistory']=[{'revision':rev,'title':json.loads(p).get('title'),'publishedAt':json.loads(p).get('publishedAt')} for rev,p in c.execute('SELECT revision,payload FROM minutes_revisions WHERE record_id=? ORDER BY revision DESC',(r['id'],))]
  else:out['employees']=[] # Recipients receive view/acknowledge access, not an employee directory or editing payload.
 return out

def dispatch(c,actor,perms,method,query,body):
 policy.need(perms,'minutes');policy.need(perms,'portal.minutes.view');pid=str(actor[4]);staff=people(c);names={u['id']:u['name'] for u in staff};action=body.get('action') if method=='POST' else query.get('action','list')
 if method=='GET':
  if action=='file':
   r=get(c,query.get('id'),pid,perms);fid=query.get('file')
   if not any(a['id']==fid for a in r.get('attachments',[])):raise policy.PermissionDenied('Attachment is not shared in this revision')
   row=c.execute('SELECT name,content FROM minutes_files WHERE id=? AND record_id=?',(fid,r['id'])).fetchone()
   if not row:raise ValueError('Attachment not found')
   return {'download':row}
  if query.get('id'):return {'record':present(c,get(c,query['id'],pid,perms),pid,perms,names,True)}
  rows=[dict(json.loads(p),version=v) for p,v in c.execute('SELECT payload,version FROM minutes_records ORDER BY rowid DESC')]
  return {'records':[present(c,r,pid,perms,names) for r in rows if visible(r,pid,perms)],'employees':[u for u in staff if u['active']] if {'portal.minutes.create','portal.minutes.edit','portal.minutes.manage'}&set(perms) else [],'permissions':sorted(perms),'userId':pid}
 if action=='acknowledge':
  policy.need(perms,'portal.minutes.acknowledge');r=get(c,body.get('id'),pid,perms)
  if r['status']!='Published' or not r['requiresAck'] or pid not in r['employees']:raise policy.PermissionDenied('Only a selected employee may acknowledge this document')
  if body.get('revision')!=r['revision']:raise ValueError('A new revision was issued. Reopen the document before acknowledging.')
  stamp=now();cur=c.execute('INSERT OR IGNORE INTO minutes_acknowledgements VALUES(?,?,?,?)',(r['id'],r['revision'],pid,stamp))
  if cur.rowcount:audit(c,r,pid,'acknowledge',{'revision':r['revision']})
  return {'record':present(c,r,pid,perms,names,True)}
 if action=='export':
  policy.need(perms,'portal.minutes.export');r=get(c,body.get('id'),pid,perms)
  if r['owner']!=pid and not manager(perms):raise policy.PermissionDenied('Only the document owner or coordinator may export the register')
  audit(c,r,pid,'export register',{'revision':r['revision']});return {'record':present(c,r,pid,perms,names,True)}
 if action=='delete':
  policy.need(perms,'portal.minutes.delete');r=get(c,body.get('id'),pid,perms)
  if not can_edit(r,pid,perms) or r['status']!='Draft':raise policy.PermissionDenied('Only an authorized editor may remove a draft')
  if body.get('version')!=r['version']:raise ValueError('Document changed; refresh first')
  audit(c,r,pid,'delete draft');c.execute('DELETE FROM minutes_records WHERE id=?',(r['id'],));return {'deleted':True}
 if action!='save':raise ValueError('Unknown document operation')
 values=body.get('record',{});old=get(c,values['id'],pid,perms) if values.get('id') else None
 if old:
  if not can_edit(old,pid,perms):raise policy.PermissionDenied('Selected employees have view-only access')
  if values.get('version')!=old['version']:raise ValueError('Document changed in another session; reopen before saving')
 else:policy.need(perms,'portal.minutes.create')
 publish=body.get('publish') is True
 if publish:policy.need(perms,'portal.minutes.publish')
 if old and old['status']=='Published' and not publish:raise ValueError('Publish a new revision to change an issued document')
 r={'id':old['id'] if old else str(uuid.uuid4()),'owner':old['owner'] if old else pid,'createdAt':old['createdAt'] if old else now()}
 for field,limit in [('title',200),('body',100000),('decisions',30000),('actions',30000),('attendees',4000),('url',2000)]:
  v=values.get(field,'')
  if not isinstance(v,str) or len(v)>limit:raise ValueError('Invalid '+field)
  r[field]=v.strip()
 if not r['title'] or not r['body']:raise ValueError('Title and document text are required')
 r['type']=values.get('type','Meeting minutes')
 if r['type'] not in ['Meeting minutes','Acknowledgement']:raise ValueError('Choose a document type')
 if r['type']=='Acknowledgement':
  for field in ['attendees','decisions','actions']:r[field]=''
 for field in ['date','dueDate']:
  v=values.get(field,'') or ''
  if v:
   try:datetime.date.fromisoformat(v)
   except (TypeError,ValueError):raise ValueError('Choose a valid '+field)
  r[field]=v
 if not r['date']:raise ValueError('Document date is required')
 if r['dueDate'] and r['dueDate']<r['date']:raise ValueError('Acknowledgement due date cannot precede the document date')
 if r['url'] and (urlsplit(r['url']).scheme not in ['https','http'] or not urlsplit(r['url']).netloc):raise ValueError('Document link must use HTTP or HTTPS')
 selected=values.get('employees',[])
 if not isinstance(selected,list) or not all(isinstance(u,str) for u in selected):raise ValueError('Select employees')
 active={u['id'] for u in staff if u['active']};r['employees']=list(dict.fromkeys(selected))
 if any(u not in active for u in r['employees']):raise ValueError('Select active employees from the employee list')
 for field in ['internalAttendees']:
  users=values.get(field,[])
  if not isinstance(users,list) or not all(isinstance(u,str) and u in active for u in users):raise ValueError('Select active internal attendees')
  r[field]=list(dict.fromkeys(users)) if r['type']=='Meeting minutes' else []
 r['chairman']=values.get('chairman','') or ''
 if r['chairman'] and r['chairman'] not in active:raise ValueError('Select an active chairman')
 r['externalAttendees']=values.get('externalAttendees','')
 if not isinstance(r['externalAttendees'],str) or len(r['externalAttendees'])>10000:raise ValueError('External attendees text is too long')
 r['calendarLink']=values.get('calendarLink') is True and r['type']=='Meeting minutes'
 if r['type']!='Meeting minutes':r.update(chairman='',externalAttendees='')
 if r['calendarLink']:
  if not r['internalAttendees']:raise ValueError('Select internal attendees before linking a calendar')
  r['employees']=list(dict.fromkeys(r['employees']+r['internalAttendees']))
  for field in ['meetingStart','meetingEnd']:
   try:
    value=values.get(field,'');parsed=datetime.datetime.fromisoformat(value)
    if parsed.tzinfo is not None:raise ValueError()
   except (ValueError,TypeError):raise ValueError('Choose valid meeting start and end times (Bangkok)')
   r[field]=value
  if r['meetingEnd']<=r['meetingStart']:raise ValueError('Meeting end must be after start')
 r['attachments']=save_files(c,r,old,values.get('attachments',[]))
 if publish and not r['employees']:raise ValueError('Select at least one employee before publishing')
 r['requiresAck']=values.get('requiresAck',True) is True;r['status']='Published' if publish else 'Draft';r['revision']=(old['revision']+(1 if old['status']=='Published' else 0)) if old else 1;r['publishedAt']=now() if publish else '';r['updatedAt']=now()
 c.execute('INSERT INTO minutes_records VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload,version=excluded.version',(r['id'],json.dumps(r,ensure_ascii=False),(old['version']+1) if old else 1))
 if publish:c.execute('INSERT INTO minutes_revisions VALUES(?,?,?)',(r['id'],r['revision'],json.dumps(r,ensure_ascii=False)))
 if publish:sync_calendar(c,r,actor)
 audit(c,r,pid,'issue revision' if old and old['status']=='Published' else 'publish' if publish else 'save draft',{'revision':r['revision'],'employees':r['employees']})
 return {'id':r['id']}

def handle(h,method,connect,session,permissions,origin):
 actor=session(h)
 if not actor:return h.reply(401,{'error':'Sign in through Staff Portal'})
 try:
  body={};query={k:v[0] for k,v in parse_qs(urlsplit(h.path).query).items()}
  if method=='POST':
   if not origin(h):return h.reply(403,{'error':'Invalid origin'})
   size=int(h.headers.get('Content-Length','0'))
   if not 0<size<=30_000_000:raise ValueError('Invalid request size')
   body=json.loads(h.rfile.read(size))
  with connect() as c:
   if method=='POST':c.execute('BEGIN IMMEDIATE')
   result=dispatch(c,actor,permissions(actor),method,query,body)
  if 'download' in result:
   name,content=result['download'];h.send_response(200);h.send_header('Content-Type','application/octet-stream');h.send_header('Content-Length',str(len(content)));h.send_header('Content-Disposition',"attachment; filename*=UTF-8''"+quote(name,safe=''));h.send_header('X-Content-Type-Options','nosniff');h.send_header('Cache-Control','no-store');h.end_headers();h.wfile.write(content);return
  return h.reply(200,result)
 except policy.PermissionDenied as e:return h.reply(403,{'error':str(e)})
 except (ValueError,KeyError,TypeError,sqlite3.IntegrityError) as e:return h.reply(400,{'error':str(e)})


def save_files(c,r,old,files,table="minutes_files"):
 if not isinstance(files,list) or len(files)>10:raise ValueError('Attach up to 10 files')
 result=[];total=0;prior={a['id']:a for a in (old or {}).get('attachments',[])}
 for a in files:
  if not isinstance(a,dict):raise ValueError('Invalid attachment')
  if a.get('id'):
   if a['id'] not in prior:raise ValueError('Attachment does not belong to this document')
   meta=prior[a['id']]
  else:
   name=a.get('name','')
   if not isinstance(name,str) or not name or len(name)>200 or any(x in name for x in ['/',chr(92),'\r','\n','\x00']):raise ValueError('Invalid attachment filename')
   if PurePath(name).suffix.lower() not in {'.pdf','.doc','.docx','.xls','.xlsx','.ppt','.pptx','.txt','.csv','.png','.jpg','.jpeg','.gif','.webp','.zip'}:raise ValueError('Unsupported attachment type')
   try:content=base64.b64decode(a.get('data',''),validate=True)
   except (ValueError,TypeError,binascii.Error):raise ValueError('Invalid attachment data')
   if not content or len(content)>10*1024*1024:raise ValueError('Each file must be between 1 byte and 10 MB')
   meta={'id':str(uuid.uuid4()),'name':name,'size':len(content)}
   c.execute('INSERT INTO '+table+' VALUES(?,?,?,?)',(meta['id'],r['id'],name,content))
  if any(x['id']==meta['id'] for x in result):raise ValueError('Duplicate attachment')
  total+=meta['size'];result.append(meta)
 if total>20*1024*1024:raise ValueError('Total attachments must not exceed 20 MB')
 return result

def sync_calendar(c,r,actor):
 """One internal event per document; no external invitations or emails."""
 import crm_api as crm
 link=c.execute('SELECT event_id FROM minutes_calendar WHERE record_id=?',(r['id'],)).fetchone()
 if not r.get('calendarLink'):
  if link:c.execute("UPDATE crm_records SET deleted=1,version=version+1 WHERE entity='Events' AND id=?",(link[0],))
  return
 crm.bind_users(c);ident=dict(c.execute('SELECT portal_user_id,crm_user_id FROM crm_identity'))
 data={'Title':r['title'],'StartDate':r['meetingStart'],'EndDate':r['meetingEnd'],'IsAllDay':False,'MainUserID':ident[r['owner']],'UserIds':[ident[u] for u in r['internalAttendees']], 'Description':'Meeting minutes · revision '+str(r['revision']),'ConferenceURL':'/?portal=1&module=minutes&minute='+r['id'],'MinutesId':r['id'],'_bridgeSource':'minutes'}
 if link:
  event=crm.raw(c,'Events',link[0]) or {};source=event.get('MinutesSchedule') or {}
  for field in ['Title','StartDate','EndDate','MainUserID','UserIds']:
   if field in source and data[field]==source[field] and field in event:data[field]=event[field]
 data['MinutesSchedule']={'Title':r['title'],'StartDate':r['meetingStart'],'EndDate':r['meetingEnd'],'MainUserID':ident[r['owner']],'UserIds':[ident[u] for u in r['internalAttendees']]}
 if link:
  c.execute("UPDATE crm_records SET deleted=0 WHERE entity='Events' AND id=?",(link[0],));crm.update(c,'Events',link[0],data);eid=link[0]
 else:
  eid=crm.insert(c,'Events',data)['Id'];c.execute('INSERT INTO minutes_calendar VALUES(?,?)',(r['id'],eid))
 crm.audit(c,actor,'Events',eid,'update from meeting minutes' if link else 'create from meeting minutes',{'minutesId':r['id'],'revision':r['revision']})
