"""Delegated Microsoft Graph calendar synchronization. No meeting invitations are sent."""
import os,json,sqlite3,uuid,time,datetime,hashlib,base64,secrets,threading,urllib.request,urllib.error
from urllib.parse import urlsplit,parse_qs,urlencode,quote
from zoneinfo import ZoneInfo
import crm_api as crm
import permissions_policy as policy
GRAPH='https://graph.microsoft.com/v1.0';SCOPES='offline_access User.Read Calendars.ReadWrite';TZ=ZoneInfo('Asia/Bangkok')
class GraphError(ValueError):
 def __init__(self,status):self.status=status;super().__init__('Microsoft authorization expired; reconnect Outlook.' if status==401 else 'Microsoft throttled requests; retry later.' if status==429 else 'Microsoft calendar request failed (HTTP '+str(status)+').')
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args):return None

def initialize(c):
 c.executescript('''CREATE TABLE IF NOT EXISTS outlook_accounts(account_id TEXT PRIMARY KEY,profile_id TEXT NOT NULL,email TEXT NOT NULL,tokens BLOB NOT NULL,mode TEXT NOT NULL DEFAULT 'push',show_private INTEGER NOT NULL DEFAULT 0,last_sync TEXT NOT NULL DEFAULT '',error TEXT NOT NULL DEFAULT '',lease_until REAL NOT NULL DEFAULT 0,lease_id TEXT NOT NULL DEFAULT '');
 CREATE TABLE IF NOT EXISTS outlook_oauth(state_hash TEXT PRIMARY KEY,account_id TEXT NOT NULL,verifier BLOB NOT NULL,expires REAL NOT NULL);
 CREATE TABLE IF NOT EXISTS outlook_events(account_id TEXT NOT NULL,event_id INTEGER NOT NULL,enabled INTEGER NOT NULL DEFAULT 1,remote_id TEXT,transaction_id TEXT NOT NULL,snapshot TEXT NOT NULL DEFAULT '{}',error TEXT NOT NULL DEFAULT '',resolution TEXT NOT NULL DEFAULT '',checked_at REAL NOT NULL DEFAULT 0,PRIMARY KEY(account_id,event_id));
 CREATE TABLE IF NOT EXISTS outlook_private(account_id TEXT NOT NULL,remote_id TEXT NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(account_id,remote_id));
 CREATE TABLE IF NOT EXISTS outlook_audit(id INTEGER PRIMARY KEY,account_id TEXT NOT NULL,at TEXT NOT NULL,action TEXT NOT NULL,event_id INTEGER,detail TEXT NOT NULL DEFAULT '');''')
 if 'checked_at' not in [r[1] for r in c.execute('PRAGMA table_info(outlook_events)')]:c.execute('ALTER TABLE outlook_events ADD COLUMN checked_at REAL NOT NULL DEFAULT 0')
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def audit(c,aid,action,eid=None,detail=''):c.execute('INSERT INTO outlook_audit(account_id,at,action,event_id,detail) VALUES(?,?,?,?,?)',(aid,stamp(),action,eid,detail))
def crypt():
 from cryptography.fernet import Fernet
 try:return Fernet(os.environ.get('BIOMED_OUTLOOK_ENCRYPTION_KEY','').encode())
 except (ValueError,TypeError):raise ValueError('Configure BIOMED_OUTLOOK_ENCRYPTION_KEY on the server') from None

def config():
 keys=['BIOMED_OUTLOOK_TENANT_ID','BIOMED_OUTLOOK_CLIENT_ID','BIOMED_OUTLOOK_CLIENT_SECRET','BIOMED_OUTLOOK_REDIRECT_URI','BIOMED_OUTLOOK_ENCRYPTION_KEY'];missing=[k for k in keys if not os.environ.get(k)];error=''
 if not missing:
  try:
   uuid.UUID(os.environ[keys[0]]);uuid.UUID(os.environ[keys[1]]);crypt();u=urlsplit(os.environ[keys[3]])
   if u.path!='/api/outlook/callback' or u.query or u.fragment or u.username or u.password or not u.hostname or (u.scheme!='https' and not(u.scheme=='http' and u.hostname in ['127.0.0.1','localhost'])):raise ValueError()
  except (ValueError,TypeError,ImportError):error='Invalid Outlook server configuration. Check tenant/client IDs, encryption key and callback URL.'
 return {'configured':not missing and not error,'missing':missing,'configurationError':error}
def require_config():
 if not config()['configured']:raise ValueError('Outlook server setup is incomplete. Ask your administrator to follow OUTLOOK_CALENDAR_SETUP.md.')
def need(perms):crm.need(perms,'events')
def account(c,aid):
 row=c.execute('SELECT id,email,name,role,user_id FROM accounts WHERE id=? AND disabled=0',(aid,)).fetchone()
 if not row:raise policy.PermissionDenied('Staff account is disabled or missing')
 return row

def request(url,method='GET',data=None,headers=None,form=False):
 u=urlsplit(url)
 if u.scheme!='https' or u.hostname not in ['graph.microsoft.com','login.microsoftonline.com'] or u.port not in [None,443] or u.username or u.password:raise ValueError('Invalid Microsoft endpoint')
 raw=(urlencode(data).encode() if form else json.dumps(data).encode()) if data is not None else None
 req=urllib.request.Request(url,data=raw,method=method,headers={**({'Content-Type':'application/x-www-form-urlencoded' if form else 'application/json'} if raw is not None else {}),**(headers or {})})
 try:
  with urllib.request.build_opener(NoRedirect()).open(req,timeout=20) as res:
   payload=res.read(8*1024*1024+1)
   if len(payload)>8*1024*1024:raise ValueError('Microsoft response is too large')
   return json.loads(payload) if payload else {}
 except urllib.error.HTTPError as e:raise GraphError(e.code) from None
 except (urllib.error.URLError,TimeoutError):raise ValueError('Cannot reach Microsoft. Retry when the server has internet access.') from None

def token_request(data):
 require_config();return request('https://login.microsoftonline.com/'+os.environ['BIOMED_OUTLOOK_TENANT_ID']+'/oauth2/v2.0/token','POST',{**data,'client_id':os.environ['BIOMED_OUTLOOK_CLIENT_ID'],'client_secret':os.environ['BIOMED_OUTLOOK_CLIENT_SECRET'],'scope':SCOPES},form=True)
def graph(token,path,method='GET',data=None,etag=None):
 url=path if path.startswith('https://') else GRAPH+path
 if not url.startswith(GRAPH+'/'):raise ValueError('Invalid Microsoft Graph continuation URL')
 return request(url,method,data,{'Authorization':'Bearer '+token,'Prefer':'IdType="ImmutableId", outlook.timezone="SE Asia Standard Time"',**({'If-Match':etag} if etag else {})})
def pack_tokens(data,previous=None):
 if not data.get('access_token') or not data.get('refresh_token', (previous or {}).get('refresh_token')):raise ValueError('Microsoft did not grant offline calendar access. Reconnect and approve calendar access.')
 return {'access_token':data['access_token'],'refresh_token':data.get('refresh_token') or previous['refresh_token'],'expires':time.time()+int(data.get('expires_in',3600))-120}
def access(connect,aid):
 with connect() as c:row=c.execute('SELECT tokens FROM outlook_accounts WHERE account_id=?',(aid,)).fetchone()
 if not row:raise ValueError('Connect your Outlook account first')
 try:data=json.loads(crypt().decrypt(row[0]))
 except Exception:raise ValueError('Outlook credentials cannot be read. Restore the server encryption key or reconnect.') from None
 if data['expires']<time.time():
  refreshed=pack_tokens(token_request({'grant_type':'refresh_token','refresh_token':data['refresh_token']}),data)
  with connect() as c:
   cur=c.execute('UPDATE outlook_accounts SET tokens=? WHERE account_id=? AND tokens=?',(crypt().encrypt(json.dumps(refreshed).encode()),aid,row[0]))
   if not cur.rowcount:raise ValueError('Outlook connection changed. Retry sync.')
  data=refreshed
 return data['access_token']
def authorize(c,actor,perms):
 need(perms);require_config();state=secrets.token_urlsafe(32);verifier=secrets.token_urlsafe(48);challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
 c.execute('DELETE FROM outlook_oauth WHERE expires<?',(time.time(),));c.execute('INSERT INTO outlook_oauth VALUES(?,?,?,?)',(hashlib.sha256(state.encode()).hexdigest(),actor[0],crypt().encrypt(verifier.encode()),time.time()+600))
 params={'client_id':os.environ['BIOMED_OUTLOOK_CLIENT_ID'],'response_type':'code','redirect_uri':os.environ['BIOMED_OUTLOOK_REDIRECT_URI'],'response_mode':'query','scope':SCOPES,'state':state,'code_challenge':challenge,'code_challenge_method':'S256','prompt':'select_account','login_hint':actor[1]}
 return 'https://login.microsoftonline.com/'+os.environ['BIOMED_OUTLOOK_TENANT_ID']+'/oauth2/v2.0/authorize?'+urlencode(params),state

def callback(connect,q,cookie,permissions):
 state=q.get('state','')
 if not state or not secrets.compare_digest(state,cookie or ''):raise ValueError('Outlook sign-in session is invalid or expired. Connect again.')
 with connect() as c:
  c.execute('BEGIN IMMEDIATE');row=c.execute('DELETE FROM outlook_oauth WHERE state_hash=? AND expires>? RETURNING account_id,verifier',(hashlib.sha256(state.encode()).hexdigest(),time.time())).fetchone()
 if not row:raise ValueError('Outlook sign-in was already used or expired. Connect again.')
 with connect() as c:actor=account(c,row[0]);need(permissions(actor));existing=c.execute('SELECT profile_id FROM outlook_accounts WHERE account_id=?',(actor[0],)).fetchone()
 if q.get('error') or not q.get('code'):raise ValueError('Microsoft sign-in was cancelled or calendar access was not approved.')
 data=pack_tokens(token_request({'grant_type':'authorization_code','code':q['code'],'redirect_uri':os.environ['BIOMED_OUTLOOK_REDIRECT_URI'],'code_verifier':crypt().decrypt(row[1]).decode()}));profile=graph(data['access_token'],'/me?$select=id,mail,userPrincipalName');email=profile.get('mail') or profile.get('userPrincipalName') or ''
 if email.casefold()!=actor[1].casefold():raise ValueError('Use the Microsoft account matching your Staff Portal company email.')
 if existing and existing[0]!=profile.get('id'):raise ValueError('Disconnect the old Outlook account before connecting a different mailbox.')
 with connect() as c:
  current=account(c,actor[0]);need(permissions(current));c.execute("INSERT INTO outlook_accounts(account_id,profile_id,email,tokens) VALUES(?,?,?,?) ON CONFLICT(account_id) DO UPDATE SET email=excluded.email,tokens=excluded.tokens,error=''",(actor[0],profile['id'],email,crypt().encrypt(json.dumps(data).encode())));audit(c,actor[0],'connect')

def visible_event(c,actor,perms,eid):
 crm.bind_users(c);r=crm.raw(c,'Events',eid)
 if not crm.visible(c,perms,'Events',r,crm.user_id(c,actor)):raise policy.PermissionDenied('Event is outside your Calendar access')
 return r

def set_event(c,actor,perms,eid,enabled):
 need(perms);visible_event(c,actor,perms,eid)
 if not isinstance(enabled,bool):raise ValueError('Choose whether to sync this event')
 if enabled and not c.execute('SELECT 1 FROM outlook_accounts WHERE account_id=?',(actor[0],)).fetchone():raise ValueError('Connect Outlook before enabling event sync')
 c.execute("INSERT INTO outlook_events(account_id,event_id,enabled,transaction_id) VALUES(?,?,?,?) ON CONFLICT(account_id,event_id) DO UPDATE SET enabled=excluded.enabled,error=''",(actor[0],eid,int(enabled),str(uuid.uuid4())));audit(c,actor[0],'enable event' if enabled else 'pause event',eid)

def status(c,actor,perms):
 need(perms);row=c.execute('SELECT email,mode,show_private,last_sync,error FROM outlook_accounts WHERE account_id=?',(actor[0],)).fetchone();out={**config(),'connected':bool(row),'events':[],'history':[],'privateEvents':[]}
 if not row:return out
 out.update(dict(zip(['email','mode','showPrivate','lastSync','error'],row)))
 for eid,enabled,error,remote in c.execute('SELECT event_id,enabled,error,remote_id FROM outlook_events WHERE account_id=?',(actor[0],)):
  try:r=visible_event(c,actor,perms,eid)
  except policy.PermissionDenied:continue
  out['events'].append({'id':eid,'title':r.get('Title') or 'Untitled event','enabled':bool(enabled),'error':error,'synced':bool(remote),'minutesLinked':bool(r.get('MinutesId'))})
 out['history']=[dict(zip(['at','action','eventId','detail'],r)) for r in c.execute('SELECT at,action,event_id,detail FROM outlook_audit WHERE account_id=? ORDER BY id DESC LIMIT 30',(actor[0],))]
 if row[2]:out['privateEvents']=[json.loads(r[0]) for r in c.execute('SELECT payload FROM outlook_private WHERE account_id=?',(actor[0],))]
 return out

def local_shape(r):
 def dt(s):return datetime.datetime.fromisoformat(str(s).replace('Z','+00:00')).replace(tzinfo=None,microsecond=0).isoformat()
 start=dt(r['StartDate']);end=dt(r['EndDate']);all_day=bool(r.get('IsAllDay'))
 if all_day:start=start[:10]+'T00:00:00';end=(datetime.date.fromisoformat(end[:10])+datetime.timedelta(days=1)).isoformat()+'T00:00:00'
 return {'subject':r.get('Title') or 'Untitled event','start':{'dateTime':start,'timeZone':'SE Asia Standard Time'},'end':{'dateTime':end,'timeZone':'SE Asia Standard Time'},'isAllDay':all_day,'location':{'displayName':r.get('Location') or ''}}
def remote_shape(r):
 def dt(key):
  obj=r[key];value=datetime.datetime.fromisoformat(obj['dateTime'].replace('Z','+00:00'));zone=obj.get('timeZone','UTC')
  if value.tzinfo is None:value=value.replace(tzinfo=TZ if zone in ['SE Asia Standard Time','Asia/Bangkok'] else datetime.timezone.utc if zone in ['UTC','Etc/UTC'] else ZoneInfo(zone))
  return value.astimezone(TZ).replace(tzinfo=None,microsecond=0).isoformat()
 return {'subject':r.get('subject') or 'Untitled event','start':{'dateTime':dt('start'),'timeZone':'SE Asia Standard Time'},'end':{'dateTime':dt('end'),'timeZone':'SE Asia Standard Time'},'isAllDay':bool(r.get('isAllDay')),'location':{'displayName':(r.get('location') or {}).get('displayName') or ''}}
def pull_values(shape):
 end=shape['end']['dateTime']
 if shape['isAllDay']:end=(datetime.date.fromisoformat(end[:10])-datetime.timedelta(days=1)).isoformat()+'T23:59:00'
 return {'Title':shape['subject'],'StartDate':shape['start']['dateTime'],'EndDate':end,'IsAllDay':shape['isAllDay'],'Location':shape['location']['displayName']}

def personal_copy(remote):
 if remote.get('attendees') or remote.get('isOrganizer') is False:raise ValueError('Outlook copy has meeting attendees or another organizer. Manage it in Outlook; automatic updates are paused to avoid sending invitations or cancellations.')

def sync(connect,actor,perms,permissions_fn=None):
 need(perms);require_config();aid=actor[0];lease=secrets.token_urlsafe(16)
 with connect() as c:
  cur=c.execute('UPDATE outlook_accounts SET lease_until=?,lease_id=? WHERE account_id=? AND lease_until<?',(time.time()+900,lease,aid,time.time()))
  if not cur.rowcount:raise ValueError('Outlook is disconnected or a sync is already running')
 try:
  token=access(connect,aid)
  with connect() as c:
   conn=c.execute('SELECT mode,show_private FROM outlook_accounts WHERE account_id=?',(aid,)).fetchone();jobs=c.execute('SELECT event_id,remote_id,transaction_id,snapshot,resolution FROM outlook_events WHERE account_id=? AND enabled=1 ORDER BY checked_at,event_id',(aid,)).fetchall()
  successes=0;failures=0;attempted=0
  for eid,rid,transaction,snapshot,resolution in jobs[:100]:
   attempted+=1
   try:
    with connect() as c:
     lease_row=c.execute('UPDATE outlook_accounts SET lease_until=? WHERE account_id=? AND lease_id=?',(time.time()+900,aid,lease))
     if not lease_row.rowcount:raise ValueError('Outlook connection changed; retry sync')
     selected=c.execute('SELECT enabled FROM outlook_events WHERE account_id=? AND event_id=?',(aid,eid)).fetchone()
     if not selected or not selected[0]:continue
     current=account(c,aid);current_perms=permissions_fn(current) if permissions_fn else perms;need(current_perms)
     try:r=visible_event(c,current,current_perms,eid)
     except policy.PermissionDenied:r=None
    if r is None:
     if rid:
      try:
       deleting=graph(token,'/me/events/'+quote(rid,safe=''));personal_copy(deleting);graph(token,'/me/events/'+quote(rid,safe=''),'DELETE')
      except GraphError as e:
       if e.status!=404:raise
     with connect() as c:c.execute('DELETE FROM outlook_events WHERE account_id=? AND event_id=?',(aid,eid));audit(c,aid,'remove Outlook copy',eid)
     successes+=1
     continue
    local=local_shape(r);previous=json.loads(snapshot);remote=graph(token,'/me/events/'+quote(rid,safe='')) if rid else None
    if remote:personal_copy(remote)
    if remote and remote.get('type') not in [None,'singleInstance']:raise ValueError('Recurring Outlook events cannot update portal records. Manage this series in Outlook.')
    shape=remote_shape(remote) if remote else None;local_changed=local!=previous.get('local');remote_changed=shape!=previous.get('remote')
    if remote and remote.get('isCancelled'):raise ValueError('Outlook copy was cancelled. Review it before resuming sync.')
    if remote and remote_changed and conn[0]=='two-way' and not r.get('MinutesId') and resolution!='portal':
     if local_changed and resolution!='outlook':raise ValueError('Conflict: both calendars changed. Choose which version to keep.')
     if 'crm.events.edit' not in current_perms:raise policy.PermissionDenied('Calendar edit permission is required to accept Outlook changes')
     with connect() as c:
      c.execute('BEGIN IMMEDIATE');current=account(c,aid);current_perms=permissions_fn(current) if permissions_fn else perms;crm.need(current_perms,'events','edit');latest=visible_event(c,current,current_perms,eid)
      if local_shape(latest)!=local:raise ValueError('Portal event changed during sync. Retry.')
      if latest.get('MinutesId'):raise ValueError('Minutes-linked events remain controlled by Staff Portal')
      crm.mutate(c,current,current_perms,crm.user_id(c,current),'Events','edit',{'Id':eid,**pull_values(shape)});audit(c,aid,'receive Outlook update',eid)
     local=shape
    elif not remote:
     body={**local,'transactionId':transaction,'body':{'contentType':'Text','content':'Staff Portal event. Meeting minutes and attachments remain protected in Staff Portal.'}}
     remote=graph(token,'/me/events','POST',body);rid=remote['id'];shape=remote_shape(remote)
     with connect() as c:c.execute('UPDATE outlook_events SET remote_id=? WHERE account_id=? AND event_id=?',(rid,aid,eid));audit(c,aid,'create Outlook copy',eid)
    elif local_changed or remote_changed or resolution=='portal':
     remote=graph(token,'/me/events/'+quote(rid,safe=''),'PATCH',local,remote.get('@odata.etag'));shape=remote_shape(remote) if remote.get('start') else local
     with connect() as c:audit(c,aid,'send portal update',eid)
    with connect() as c:
     # Store the version actually transmitted, so changes made during network requests remain pending.
     c.execute("UPDATE outlook_events SET remote_id=?,snapshot=?,error='',resolution='',checked_at=? WHERE account_id=? AND event_id=?",(rid,json.dumps({'local':local,'remote':shape}),time.time(),aid,eid))
    successes+=1
   except Exception as e:
    message=str(e) if isinstance(e,(ValueError,policy.PermissionDenied)) else 'Sync failed. Retry or reconnect Outlook.'
    if isinstance(e,GraphError) and e.status==412:message='Conflict: Outlook changed during sync. Choose which version to keep.'
    if isinstance(e,GraphError) and e.status==404:message='Outlook copy was deleted. Use Recreate copy to resume.'
    with connect() as c:c.execute('UPDATE outlook_events SET error=?,checked_at=? WHERE account_id=? AND event_id=?',(message,time.time(),aid,eid));audit(c,aid,'event sync failed',eid,message)
    failures+=1
    if isinstance(e,GraphError) and e.status in [401,429]:break
  if conn[1]:
   with connect() as c:
    refreshed_actor=account(c,aid);need(permissions_fn(refreshed_actor) if permissions_fn else perms)
   refresh_private(connect,aid,token)
  with connect() as c:
   c.execute("UPDATE outlook_accounts SET last_sync=?,error=? WHERE account_id=? AND lease_id=?",(stamp(),str(failures)+' event(s) need attention' if failures else '',aid,lease));audit(c,aid,'sync finished',detail=str(successes)+' processed; '+str(failures)+' need attention')
  return {'processed':successes,'failed':failures,'remaining':max(0,len(jobs)-attempted)}
 except Exception as e:
  message=str(e) if isinstance(e,(ValueError,policy.PermissionDenied)) else 'Outlook synchronization failed.'
  with connect() as c:c.execute('UPDATE outlook_accounts SET error=? WHERE account_id=? AND lease_id=?',(message,aid,lease))
  raise ValueError(message) from None
 finally:
  with connect() as c:c.execute('UPDATE outlook_accounts SET lease_until=0,lease_id=? WHERE account_id=? AND lease_id=?',('',aid,lease))

def refresh_private(connect,aid,token):
 today=datetime.datetime.now(TZ).date();query=urlencode({'startDateTime':(today-datetime.timedelta(days=180)).isoformat()+'T00:00:00+07:00','endDateTime':(today+datetime.timedelta(days=365)).isoformat()+'T00:00:00+07:00','$top':100,'$select':'id,subject,start,end,isAllDay,location,webLink,isCancelled,type'});path='/me/calendarView?'+query;events=[]
 for _ in range(10):
  data=graph(token,path);events.extend(data.get('value',[]));path=data.get('@odata.nextLink')
  if not path:break
 else:raise ValueError('Outlook private calendar has too many events in the sync window. Narrow the calendar before enabling this option.')
 with connect() as c:
  mapped={r[0] for r in c.execute('SELECT remote_id FROM outlook_events WHERE account_id=? AND remote_id IS NOT NULL',(aid,))};c.execute('DELETE FROM outlook_private WHERE account_id=?',(aid,))
  for r in events:
   if r['id'] in mapped or r.get('isCancelled'):continue
   shape=remote_shape(r);item={'id':r['id'],'title':shape['subject'],'start':shape['start']['dateTime'],'end':shape['end']['dateTime'],'allDay':shape['isAllDay'],'location':shape['location']['displayName'],'webLink':r.get('webLink','')}
   c.execute('INSERT INTO outlook_private VALUES(?,?,?)',(aid,r['id'],json.dumps(item)))

def worker(connect,permissions,stop):
 while not stop.wait(60):
  try:
   if not config()['configured']:continue
   with connect() as c:ids=[a for a,last in c.execute('SELECT account_id,last_sync FROM outlook_accounts') if not last or (datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(last)).total_seconds()>300]
   for aid in ids:
    if stop.is_set():return
    try:
     with connect() as c:actor=account(c,aid)
     sync(connect,actor,permissions(actor),permissions)
    except Exception:pass # Status and per-event audit store actionable errors; never log credentials.
  except Exception:pass

def handle(h,method,connect,session,permissions,origin):
 q={k:v[0] for k,v in parse_qs(urlsplit(h.path).query).items()};action=urlsplit(h.path).path.rsplit('/',1)[-1]
 try:
  if action=='callback' and method=='GET':
   from http.cookies import SimpleCookie
   cookies=SimpleCookie();cookies.load(h.headers.get('Cookie',''));cookie=cookies.get('biomed_outlook_oauth');callback(connect,q,cookie.value if cookie else '',permissions)
   h.send_response(303);h.send_header('Location','/?portal=1&module=calendar&outlook=connected');h.send_header('Set-Cookie','biomed_outlook_oauth=; Path=/api/outlook/callback; HttpOnly; SameSite=Lax; Max-Age=0');h.send_header('Cache-Control','no-store');h.end_headers();return
  actor=session(h)
  if not actor:return h.reply(401,{'error':'Sign in through Staff Portal'})
  perms=permissions(actor);need(perms)
  if method=='GET' and action=='status':
   with connect() as c:return h.reply(200,status(c,actor,perms))
  if method!='POST' or not origin(h):raise policy.PermissionDenied('Invalid request origin')
  n=int(h.headers.get('Content-Length','0'))
  if not 0<n<=16000:raise ValueError('Invalid Outlook request size')
  data=json.loads(h.rfile.read(n))
  if action=='sync':return h.reply(200,sync(connect,actor,perms,permissions))
  with connect() as c:
   c.execute('BEGIN IMMEDIATE')
   if action=='connect':
    url,state=authorize(c,actor,perms);c.commit();h.send_response(200);raw=json.dumps({'url':url}).encode();h.send_header('Content-Type','application/json');h.send_header('Content-Length',str(len(raw)));h.send_header('Set-Cookie','biomed_outlook_oauth='+state+'; Path=/api/outlook/callback; HttpOnly; SameSite=Lax; Max-Age=600'+('; Secure' if os.environ['BIOMED_OUTLOOK_REDIRECT_URI'].startswith('https:') else ''));h.send_header('Cache-Control','no-store');h.end_headers();h.wfile.write(raw);return
   if action=='disconnect':
    row=c.execute('SELECT lease_until FROM outlook_accounts WHERE account_id=?',(actor[0],)).fetchone()
    if row and row[0]>time.time():raise ValueError('Wait for the running sync to finish before disconnecting')
    for table in ['outlook_accounts','outlook_private','outlook_oauth']:c.execute('DELETE FROM '+table+' WHERE account_id=?',(actor[0],))
    c.execute('UPDATE outlook_events SET enabled=0 WHERE account_id=?',(actor[0],));audit(c,actor[0],'disconnect')
   elif action=='settings':
    if not c.execute('SELECT 1 FROM outlook_accounts WHERE account_id=?',(actor[0],)).fetchone():raise ValueError('Connect Outlook first')
    if data.get('mode') not in ['push','two-way']:raise ValueError('Choose a sync direction')
    if data['mode']=='two-way':crm.need(perms,'events','edit')
    c.execute('UPDATE outlook_accounts SET mode=?,show_private=? WHERE account_id=?',(data['mode'],int(data.get('showPrivate') is True),actor[0]))
    if not data.get('showPrivate'):c.execute('DELETE FROM outlook_private WHERE account_id=?',(actor[0],))
    audit(c,actor[0],'change sync settings')
   elif action=='event':set_event(c,actor,perms,int(data['id']),data.get('enabled'))
   elif action=='resolve':
    eid=int(data['id']);r=visible_event(c,actor,perms,eid);choice=data.get('choice')
    if choice not in ['portal','outlook','recreate']:raise ValueError('Choose a conflict resolution')
    if choice=='outlook':
     crm.need(perms,'events','edit')
     if r.get('MinutesId'):raise ValueError('Minutes-linked events remain controlled by Staff Portal')
    if choice=='recreate':c.execute("UPDATE outlook_events SET remote_id=NULL,transaction_id=?,snapshot='{}',resolution='',error='' WHERE account_id=? AND event_id=? AND error LIKE 'Outlook copy was deleted%'",(str(uuid.uuid4()),actor[0],eid))
    else:c.execute("UPDATE outlook_events SET resolution=?,error='' WHERE account_id=? AND event_id=?",(choice,actor[0],eid))
    audit(c,actor[0],'resolve '+choice,eid)
   else:raise ValueError('Unknown Outlook operation')
  return h.reply(200,{'saved':True})
 except policy.PermissionDenied as e:return h.reply(403,{'error':str(e)})
 except (ValueError,TypeError,KeyError) as e:return h.reply(400,{'error':str(e)})
