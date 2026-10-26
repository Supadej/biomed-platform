"""HTTP adapter. All original CRM API routes use the existing signed-in account cookie."""
import json,sqlite3,uuid,re,mimetypes
from urllib.parse import urlsplit,quote
from email.parser import BytesParser
from email import policy as email_policy
import crm_api as api
import permissions_policy as permissions
CONNECT=ACTOR=PERMS=ORIGIN=None
def configure(connect,actor,perms,origin):
 global CONNECT,ACTOR,PERMS,ORIGIN
 CONNECT,ACTOR,PERMS,ORIGIN=connect,actor,perms,origin
class CRMHandlerMixin:
 def crm_request(self,method):
  actor=ACTOR(self)
  if not actor:return self.reply(401,{'error':'Sign in through Staff Portal to use CRM'})
  if method!='GET' and not ORIGIN(self):return self.reply(403,{'error':'Invalid origin'})
  path=urlsplit(self.path).path
  try:
   perms=PERMS(actor);permissions.need(perms,'crm_view')
   with CONNECT() as c:
    if method!='GET':c.execute('BEGIN IMMEDIATE')
    if path.startswith('/api/crm/native/'):
     import portal_crm
     result=portal_crm.handle(c,actor,perms,self.path,method,self.crm_json() if method!='GET' else {})
    elif path.startswith('/api/crm/bridge/'):
     import crm_bridges
     data=self.crm_json() if method!='GET' else {}
     result=crm_bridges.handle(c,actor,perms,self.path,method,data)
    elif path=='/api/crm/session':
     api.bind_users(c);uid=api.user_id(c,actor);result={'account':{'id':actor[0],'name':actor[2],'role':actor[3],'user_id':actor[4]},'permissions':sorted(perms),'user':api.serialize(c,'Users',api.raw(c,'Users',uid),perms,uid),'schemaVersion':1}
    elif path=='/api/crm/schema':
     api.need(perms,'settings');result={k:{'fields':{f:t for f,t in v['fields'].items() if f.lower() not in ['password','username']},'foreignKeys':v['foreignKeys']} for k,v in api.SCHEMA.items()}
    elif path=='/api/crm/linked-data':
     api.need(perms,'finance');result=[json.loads(r[0]) for r in c.execute("SELECT payload FROM crm_records WHERE entity='ExternalSnapshots' AND deleted=0 ORDER BY id DESC")]
    elif path.startswith('/api/crm/export/'):
     entity=path.rsplit('/',1)[-1]
     if entity not in api.MODULES:raise ValueError('Unknown CRM entity')
     api.need(perms,api.MODULES[entity],'export');api.bind_users(c);uid=api.user_id(c,actor);result=[api.serialize(c,entity,r,perms,uid) for r in api.rows(c,entity) if api.visible(c,perms,entity,r,uid)];api.audit(c,actor,entity,None,'export',{'count':len(result)})
    elif path=='/api/crm/audit':
     api.need(perms,'logs');audit_rows=c.execute('SELECT * FROM crm_audit ORDER BY id DESC LIMIT 1000').fetchall() if 'crm.logs.view_all' in perms else c.execute('SELECT * FROM crm_audit WHERE actor=? ORDER BY id DESC LIMIT 1000',(str(actor[0]),)).fetchall();result=[dict(zip(['id','at','actor','entity','recordId','action','detail'],r)) for r in audit_rows]
    elif path.startswith('/biomedapi/misc/uploadfile') or path.startswith('/biomedapi/upload/profile'):
     return self.crm_upload(c,actor,perms,path)
    elif path.startswith('/crm/storage/') or path.startswith('/crm/assets/profile/'):
     return self.crm_file(c,actor,perms,path)
    else:
     data=self.crm_json() if method!='GET' else {}
     result=api.handle(c,actor,perms,self.path,method,data)
     # Original create dialogs expect a plain JSON number from response.text().
     if method=='POST' and path.endswith('/create') and isinstance(result,dict) and 'Id' in result:result=result['Id']
   return self.reply(200,result)
  except permissions.PermissionDenied as e:return self.reply(403,{'error':str(e)})
  except (ValueError,TypeError,KeyError,sqlite3.IntegrityError) as e:return self.reply(400,{'error':str(e)})
 def crm_json(self):
  n=int(self.headers.get('Content-Length','0'))
  if n==0:return {}
  if not 0<n<=4*1024*1024:raise ValueError('Maximum CRM request size is 4 MB')
  return json.loads(self.rfile.read(n))
 def crm_upload(self,c,actor,perms,path):
  api.need(perms,'files','upload');n=int(self.headers.get('Content-Length','0'))
  if not 0<n<=12*1024*1024:raise ValueError('Maximum attachment size is 10 MB')
  ctype=self.headers.get('Content-Type','')
  if not ctype.startswith('multipart/form-data'):raise ValueError('Multipart file required')
  message=BytesParser(policy=email_policy.default).parsebytes(('Content-Type: '+ctype+'\r\nMIME-Version: 1.0\r\n\r\n').encode()+self.rfile.read(n))
  part=next((p for p in message.iter_parts() if p.get_content_disposition()=='form-data' and p.get_param('name',header='content-disposition')=='file'),None)
  if not part:raise ValueError('Choose a file')
  raw=part.get_payload(decode=True);name=(part.get_filename() or 'attachment').replace('\\','/').rsplit('/',1)[-1]
  if not raw or len(raw)>10*1024*1024:raise ValueError('Maximum attachment size is 10 MB')
  ext=name.rsplit('.',1)[-1].lower() if '.' in name else ''
  allowed={'pdf':'application/pdf','png':'image/png','jpg':'image/jpeg','jpeg':'image/jpeg','webp':'image/webp','docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document','xlsx':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','csv':'text/csv','txt':'text/plain'}
  mime=allowed.get(ext)
  if not mime:raise ValueError('Use PDF, PNG/JPEG/WebP, DOCX, XLSX, CSV or TXT')
  if mime=='application/pdf' and not raw.startswith(b'%PDF-') or mime=='image/png' and not raw.startswith(b'\x89PNG\r\n\x1a\n') or mime=='image/jpeg' and not raw.startswith(b'\xff\xd8\xff') or mime=='image/webp' and not (raw.startswith(b'RIFF') and raw[8:12]==b'WEBP'):raise ValueError('File content does not match its extension')
  if ext in ['docx','xlsx']:
   import zipfile,io
   try:
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
     if '[Content_Types].xml' not in z.namelist():raise ValueError('Invalid Office file')
   except zipfile.BadZipFile:raise ValueError('Invalid Office file')
  id=str(uuid.uuid4());c.execute('INSERT INTO crm_files VALUES(?,?,?,?,?)',(id,name,mime,raw,str(actor[0])))
  if '/profile/' in path:
   api.need(perms,'users','edit');uid=int(path.rsplit('/',1)[1]);api.update(c,'Users',uid,{'ProfilePic':id})
  api.audit(c,actor,'files',None,'upload',{'id':id,'name':name})
  c.commit();payload=(id if '/profile/' in path else id+'.'+ext).encode();self.send_response(200);self.send_header('Content-Type','text/plain');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
 def crm_file(self,c,actor,perms,path):
  api.need(perms,'files');id=path.rsplit('/',1)[-1].split('.',1)[0]
  if not re.fullmatch('[a-f0-9-]{36}',id):return self.send_error(404)
  row=c.execute('SELECT name,mime,content FROM crm_files WHERE id=?',(id,)).fetchone()
  if not row:return self.send_error(404)
  self.send_response(200);self.send_header('Content-Type',row[1]);self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Security-Policy',"sandbox; default-src 'none'");self.send_header('Content-Length',str(len(row[2])));self.send_header('Content-Disposition',('inline' if row[1].startswith('image/') or row[1]=='application/pdf' else 'attachment')+"; filename*=UTF-8''"+quote(row[0],safe=''));self.end_headers();self.wfile.write(row[2])
