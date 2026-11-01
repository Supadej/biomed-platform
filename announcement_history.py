"""Server-authored append-only announcement revision snapshots."""
import json,datetime
import permissions_policy as policy
def initialize(c):
 c.execute('CREATE TABLE IF NOT EXISTS announcement_revisions(announcement_id TEXT NOT NULL,version INTEGER NOT NULL,at TEXT NOT NULL,actor_id TEXT NOT NULL,actor_name TEXT NOT NULL,reason TEXT NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(announcement_id,version))')
def capture(c,old,new,actor):
 initialize(c);prior={x['id']:x for x in old.get('announcements',[])};fields=['title','body','by','required','attachments']
 for item in new.get('announcements',[]):
  before=prior.get(item['id']);changed=before is None or any(before.get(k)!=item.get(k) for k in fields)
  if not changed:
   item['version']=before.get('version',1);continue
  if before:
   c.execute('INSERT OR IGNORE INTO announcement_revisions VALUES(?,?,?,?,?,?,?)',(item['id'],before.get('version',1),str(before.get('updatedAt') or before.get('date') or ''),'legacy',str(before.get('by') or 'Unknown'),'Baseline preserved before first tracked edit',json.dumps(before,ensure_ascii=False)))
  if before:item['acks']=json.loads(json.dumps(before.get('acks',[])))
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
