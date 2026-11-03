"""Server-authored append-only announcement revision snapshots."""
import json,datetime,sqlite3
import permissions_policy as policy
def initialize(c):
 c.execute('CREATE TABLE IF NOT EXISTS announcement_revisions(announcement_id TEXT NOT NULL,version INTEGER NOT NULL,at TEXT NOT NULL,actor_id TEXT NOT NULL,actor_name TEXT NOT NULL,reason TEXT NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(announcement_id,version))')
def capture(c,old,new,actor):
 initialize(c);prior={x['id']:x for x in old.get('announcements',[])};fields=['title','body','by','required','attachments']
 for item in new.get('announcements',[]):
  before=prior.get(item['id']);changed=before is None or any(before.get(k)!=item.get(k) for k in fields)
  incoming=item.get('acks',[])
  saved=before.get('acks',[]) if before else []
  if not changed and any(ack not in saved for ack in incoming):
   raise ValueError('Refresh Staff Portal and use the Acknowledge button to record acknowledgement.')
  item['acks']=saved
  if not changed:
   item['version']=before.get('version',1);continue
  if before:
   c.execute('INSERT OR IGNORE INTO announcement_revisions VALUES(?,?,?,?,?,?,?)',(item['id'],before.get('version',1),str(before.get('updatedAt') or before.get('date') or ''),'legacy',str(before.get('by') or 'Unknown'),'Baseline preserved before first tracked edit',json.dumps(before,ensure_ascii=False)))
  item['version']=(before.get('version',1)+1) if before else 1
  item['updatedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat();item['updatedBy']=str(actor[4]);item['updatedName']=actor[2]
  reason=str(item.get('revisionReason') or ('Published' if not before else 'Announcement updated')).strip()[:2000]
  if before and not reason:raise ValueError('Enter a revision note')
  c.execute('INSERT INTO announcement_revisions VALUES(?,?,?,?,?,?,?)',(item['id'],item['version'],item['updatedAt'],str(actor[4]),actor[2],reason,json.dumps(item,ensure_ascii=False)))
def handle(h,connect,session,permissions):
 actor=session(h)
 if not actor:return h.reply(401,{'error':'Sign in required'})
 try:
  perms=permissions(actor);policy.need(perms,'announcements');policy.need(perms,'portal.announcements.view')
  from urllib.parse import parse_qs,urlsplit
  ident=parse_qs(urlsplit(h.path).query).get('id',[''])[0]
  with connect() as c:
   initialize(c);row=c.execute("select value from workspace where key='biomed_portal_v33_clean'").fetchone();portal=json.loads(row[0]) if row else {}
   item=next((x for x in portal.get('announcements',[]) if x['id']==ident),None)
   if not item:return h.reply(404,{'error':'Announcement not found'})
   revisions=[{'version':v,'at':at,'editor':name,'reason':reason,'snapshot':json.loads(raw)} for v,at,name,reason,raw in c.execute('select version,at,actor_name,reason,payload from announcement_revisions where announcement_id=? order by version desc',(ident,))]
   if not revisions:revisions=[{'version':item.get('version',1),'at':item.get('date',''),'editor':item.get('by','Unknown'),'reason':'Existing version; earlier edits were not recorded','snapshot':item}]
   return h.reply(200,{'revisions':revisions})
 except policy.PermissionDenied as e:return h.reply(403,{'error':str(e)})

PORTAL_KEY='biomed_portal_v33_clean'


def acknowledge(c,actor,ident,version):
 row=c.execute('SELECT value FROM workspace WHERE key=?',(PORTAL_KEY,)).fetchone()
 portal=json.loads(row[0]) if row else {}
 item=next((entry for entry in portal.get('announcements',[]) if entry['id']==ident),None)
 if item is None:return 404,{'error':'Announcement not found'}
 if item.get('version',1)!=version:
  return 409,{'error':'A new revision was published. Reload and read it before acknowledging.'}
 acks=item.setdefault('acks',[])
 user_id=str(actor[4])
 saved=next((ack for ack in acks if str(ack.get('user'))==user_id and ack.get('version')==version),None)
 if saved is None:
  saved={'user':user_id,'name':actor[2],'version':version,'at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
  acks.append(saved)
  c.execute('UPDATE workspace SET value=?,revision=revision+1 WHERE key=?',(json.dumps(portal,ensure_ascii=False),PORTAL_KEY))
 return 200,{'acknowledgement':saved}


def handle_acknowledge(h,connect,session,permissions,origin):
 actor=session(h)
 if not actor:return h.reply(401,{'error':'Sign in required'})
 if not origin(h):return h.reply(403,{'error':'Invalid origin'})
 try:
  perms=permissions(actor)
  policy.need(perms,'announcements')
  policy.need(perms,'portal.announcements.acknowledge')
  length=int(h.headers.get('Content-Length','0'))
  if not 0<length<=4096:raise ValueError('Invalid acknowledgement request')
  body=json.loads(h.rfile.read(length))
  if not isinstance(body,dict):raise ValueError('Invalid acknowledgement request')
  ident=body['id'];version=body['version']
  if not isinstance(ident,str) or not ident or type(version) is not int or version<1:
   raise ValueError('Invalid announcement or revision')
  with connect() as c:
   c.execute('BEGIN IMMEDIATE')
   status,result=acknowledge(c,actor,ident,version)
  return h.reply(status,result)
 except policy.PermissionDenied as e:return h.reply(403,{'error':str(e)})
 except (ValueError,KeyError,TypeError) as e:return h.reply(400,{'error':str(e)})
 except sqlite3.OperationalError as e:
  if (getattr(e,'sqlite_errorcode',0)&255) in (sqlite3.SQLITE_BUSY,sqlite3.SQLITE_LOCKED):
   return h.reply(503,{'error':'Biomed is busy. Try acknowledging this revision again.'})
  raise
