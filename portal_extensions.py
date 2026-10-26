"""Account-owned search favorites and private leave evidence stored in SQLite."""
import json,re,secrets
from urllib.parse import urlsplit,parse_qs,quote
import permissions_policy as policy
from website_files import decode_upload

def initialize(c):
 c.executescript('''CREATE TABLE IF NOT EXISTS search_favorites(account_id TEXT NOT NULL REFERENCES accounts(id),scope TEXT NOT NULL,name TEXT NOT NULL,payload TEXT NOT NULL,revision INTEGER NOT NULL,PRIMARY KEY(account_id,scope,name));
 CREATE TABLE IF NOT EXISTS portal_attachments(id TEXT PRIMARY KEY,owner TEXT NOT NULL,request_id TEXT NOT NULL,filename TEXT NOT NULL,mime TEXT NOT NULL,content BLOB NOT NULL);''')

def validate_leave_references(portal,c):
 for r in portal.get('requests',[]):
  files=r.get('attachments',[])
  if not isinstance(files,list) or len(files)>5:raise ValueError('Maximum 5 attachments per request')
  for f in files:
   if not isinstance(f,dict):raise ValueError('Invalid leave attachment')
   # New private server references; preserve older attachment metadata without changing it.
   if not str(f.get('url','')).startswith('/api/portal/attachments/'):continue
   row=c.execute('SELECT owner,request_id,filename FROM portal_attachments WHERE id=?',(f.get('id'),)).fetchone()
   if not row or row[0]!=r.get('owner') or row[1]!=r.get('id') or r.get('type')!='leave' or f['url']!='/api/portal/attachments/'+str(f.get('id')):raise ValueError('Attachment does not belong to this leave request')

def handle(h,method,connect,session,permissions,valid_origin):
 actor=session(h)
 if not actor:return h.reply(401,{'error':'Sign in required'})
 path=urlsplit(h.path).path
 try:
  if method!='GET' and not valid_origin(h):return h.reply(403,{'error':'Invalid origin'})
  if path=='/api/portal/quotation-snapshot' and method=='GET':
   perms=permissions(actor);policy.need(perms,'is_view');policy.need(perms,'pipeline','tenders')
   can_read_quotes='is.quotation.view' in perms or 'is.backup.export' in perms
   can_read_orders='is.sales-order.view' in perms or 'is.backup.export' in perms
   id=parse_qs(urlsplit(h.path).query).get('id',[''])[0]
   kinds=(['quotation'] if can_read_quotes else [])+(['sales-order'] if can_read_orders and not id else [])
   if not kinds:return h.reply(200,{'documents':[],'customers':[]})
   with connect() as c:
    sql="SELECT d.value FROM workspace w,json_each(w.value,'$.documents') d WHERE w.key='biomed_is_v50_transactions' AND json_extract(d.value,'$.kind') IN ("+','.join('?' for _ in kinds)+')'
    params=list(kinds)
    if id:sql+=" AND CAST(json_extract(d.value,'$.id') AS TEXT)=?";params.append(id)
    docs=[json.loads(row[0]) for row in c.execute(sql,params)]
    parties={str(d.get('party','')) for d in docs if d.get('kind')=='quotation'}
    customers=[]
    if parties:
     # Read only customer IDs/names; do not send the master/product workspace.
     for row in c.execute("SELECT json_extract(c.value,'$.id'),json_extract(c.value,'$.name') FROM workspace w,json_each(w.value,'$.customers') c WHERE w.key='biomed_is_v50_transactions'"):
      if str(row[0]) in parties:customers.append({'id':row[0],'name':row[1]})
   if not id:
    summaries=[]
    for d in docs:
     if d.get('kind')=='sales-order':summaries.append({k:d.get(k) for k in ['id','kind','status','sourceId']});continue
     record={k:d.get(k) for k in ['id','ref','kind','party','status','date','portalRep','owner','portalLine','currency']}
     record['sourceVersion']=1;record['financials']={'net':d.get('financials',{}).get('net',0) if d.get('sourceVersion') and d.get('financials') else sum(float(line.get('qty') or 0)*float(line.get('price') or 0) for line in d.get('lines',[]))};summaries.append(record)
    docs=summaries
   return h.reply(200,{'documents':docs,'customers':customers})
  if path=='/api/preferences/search-favorites':
   if method=='GET':
    scope=parse_qs(urlsplit(h.path).query).get('scope',[''])[0]
    with connect() as c:rows=c.execute('SELECT name,payload,revision FROM search_favorites WHERE account_id=? AND scope=? ORDER BY name',(actor[0],scope)).fetchall()
    return h.reply(200,{'items':[{'name':r[0],'state':json.loads(r[1]),'revision':r[2]} for r in rows]})
   length=int(h.headers.get('Content-Length','0'))
   if not 0<length<=65536:raise ValueError('Favorite is too large')
   x=json.loads(h.rfile.read(length));scope=x.get('scope');name=x.get('name');state=x.get('state');op=x.get('operation','save')
   if not isinstance(scope,str) or not re.fullmatch(r'[A-Za-z0-9_.:/ -]{1,220}',scope):raise ValueError('Invalid search scope')
   if not isinstance(name,str) or not 1<=len(name.strip())<=100:raise ValueError('Name the favorite (up to 100 characters)')
   name=name.strip()
   if op not in ['save','delete']:raise ValueError('Invalid operation')
   if op=='save' and (not isinstance(state,list) or len(state)>80 or any(not isinstance(s,dict) or set(s)!={'key','value'} or not isinstance(s['key'],str) or len(s['key'])>500 or not isinstance(s['value'],str) or len(s['value'])>5000 for s in state)):raise ValueError('Invalid filter state')
   with connect() as c:
    c.execute('BEGIN IMMEDIATE');old=c.execute('SELECT revision FROM search_favorites WHERE account_id=? AND scope=? AND name=?',(actor[0],scope,name)).fetchone();revision=old[0] if old else 0
    if x.get('revision',0)!=revision:return h.reply(409,{'error':'This favorite changed in another tab. Refresh favorites and try again.'})
    if op=='delete':c.execute('DELETE FROM search_favorites WHERE account_id=? AND scope=? AND name=?',(actor[0],scope,name))
    else:
     if not old and c.execute('SELECT count(*) FROM search_favorites WHERE account_id=? AND scope=?',(actor[0],scope)).fetchone()[0]>=50:raise ValueError('Maximum 50 favorites per list')
     c.execute('INSERT OR REPLACE INTO search_favorites VALUES(?,?,?,?,?)',(actor[0],scope,name,json.dumps(state),revision+1))
   return h.reply(200,{'saved':True,'revision':revision+1})
  perms=permissions(actor);user_id=actor[4]
  if path=='/api/portal/attachments' and method=='POST':
   policy.need(perms,'portal.requests.create');policy.need(perms,'requests','leavebalance')
   length=int(h.headers.get('Content-Length','0'))
   if not 0<length<=15*1024*1024:raise ValueError('Each attachment must be 10 MB or smaller')
   x=json.loads(h.rfile.read(length));request_id=x.get('requestId','')
   if not isinstance(request_id,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',request_id):raise ValueError('Invalid request ID')
   f,raw=decode_upload(x)
   with connect() as c:
    r=c.execute("SELECT value FROM workspace WHERE key='biomed_portal_v33_clean'").fetchone();p=json.loads(r[0]) if r else {};request=next((r for r in p.get('requests',[]) if r.get('id')==request_id),None)
    if request and (request.get('owner')!=user_id or request.get('type')!='leave' or request.get('status')!='Pending'):raise policy.PermissionDenied('Only your pending leave request may receive attachments')
    if c.execute('SELECT count(*) FROM portal_attachments WHERE owner=? AND request_id=?',(user_id,request_id)).fetchone()[0]>=5:raise ValueError('Maximum 5 attachments per request')
    c.execute('INSERT INTO portal_attachments VALUES(?,?,?,?,?,?)',(f['id'],user_id,request_id,f['name'],f['mime'],raw))
   f['url']='/api/portal/attachments/'+f['id'];return h.reply(200,f)
  if path.startswith('/api/portal/attachments/') and method=='GET':
   id=path.rsplit('/',1)[-1]
   with connect() as c:
    f=c.execute('SELECT owner,request_id,filename,mime,content FROM portal_attachments WHERE id=?',(id,)).fetchone();p=c.execute("SELECT value FROM workspace WHERE key='biomed_portal_v33_clean'").fetchone();p=json.loads(p[0]) if p else {}
   r=next((r for r in p.get('requests',[]) if f and r.get('id')==f[1] and any(a.get('id')==id for a in r.get('attachments',[]))),None)
   manager=next((u.get('managerId') for u in p.get('users',[]) if f and u.get('id')==f[0]),None)
   allowed=f and r and (user_id==f[0] or 'approve_all' in perms or manager==user_id and 'portal.requests.approve' in perms or 'approve_leave' in perms and 'portal.requests.approve' in perms)
   if not allowed:return h.reply(404,{'error':'Attachment unavailable'})
   policy.need(perms,'requests','leavebalance')
   h.send_response(200);h.send_header('Content-Type',f[3]);h.send_header('Content-Length',str(len(f[4])));h.send_header('Content-Disposition',"inline; filename*=UTF-8''"+quote(f[2],safe=''));h.send_header('X-Content-Type-Options','nosniff');h.send_header('Content-Security-Policy',"sandbox; default-src 'none'");h.end_headers();h.wfile.write(f[4]);return
  return h.reply(404,{'error':'Unknown portal endpoint'})
 except policy.PermissionDenied as e:return h.reply(403,{'error':str(e)})
 except (ValueError,TypeError,KeyError) as e:return h.reply(400,{'error':str(e)})
