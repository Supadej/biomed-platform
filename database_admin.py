"""Authenticated, transactional full-system archive/restore; no SQL from uploads."""
import base64,datetime,hashlib,io,json,os,secrets,zipfile
from pathlib import Path
import permissions_policy as policy
MAX=256*1024*1024
EXCLUDE={'sessions','outlook_oauth','database_import_preview','system_admin_audit','system_controls'}
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def initialize(c):
 c.execute('CREATE TABLE IF NOT EXISTS system_controls(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
 c.execute('CREATE TABLE IF NOT EXISTS system_admin_audit(id INTEGER PRIMARY KEY,at TEXT,actor TEXT,action TEXT,detail TEXT)')
 c.execute('CREATE TABLE IF NOT EXISTS database_import_preview(token TEXT PRIMARY KEY,account_id TEXT,expires REAL,digest TEXT,payload BLOB)')
def audit(c,actor,action,detail):
 c.execute('INSERT INTO system_admin_audit(at,actor,action,detail) VALUES(?,?,?,?)',(now(),str(actor[4]),action,json.dumps(detail,ensure_ascii=False)))
def tables(c):return {n:[r[1] for r in c.execute('PRAGMA table_info("'+n+'")')] for n, in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'") if n not in EXCLUDE}
def val(v):return {'blob':base64.b64encode(v).decode()} if isinstance(v,bytes) else v
def unval(v):
 if isinstance(v,dict):
  if set(v)!={'blob'}:raise ValueError('Invalid binary cell')
  return base64.b64decode(v['blob'],validate=True)
 if v is not None and not isinstance(v,(str,int,float)):raise ValueError('Invalid database value')
 return v
def snapshot(c):
 return {'format':'biomed-system-backup','version':1,'createdAt':now(),'scope':['Biomed IS','Staff Portal','Financial'],'tables':{t:{'columns':cols,'rows':[[val(v) for v in row] for row in c.execute('SELECT * FROM "'+t+'"')]} for t,cols in tables(c).items()}}
def pack(payload):
 raw=json.dumps(payload,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode();out=io.BytesIO()
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('database.json',raw);z.writestr('manifest.json',json.dumps({'format':'biomed-system-backup','version':1,'sha256':hashlib.sha256(raw).hexdigest(),'createdAt':payload['createdAt'],'scope':payload['scope']}))
 return out.getvalue()
def unpack(raw,c):
 if len(raw)>MAX:raise ValueError('Maximum backup upload is 256 MB')
 try:
  with zipfile.ZipFile(io.BytesIO(raw)) as z:
   if sorted(z.namelist())!=['database.json','manifest.json'] or any(i.file_size>MAX for i in z.infolist()):raise ValueError('Choose a Biomed full-system backup ZIP')
   content=z.read('database.json');manifest=json.loads(z.read('manifest.json'))
  if hashlib.sha256(content).hexdigest()!=manifest.get('sha256'):raise ValueError('Backup checksum failed')
  p=json.loads(content,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('Invalid numeric value')))
 except (zipfile.BadZipFile,KeyError,UnicodeError,json.JSONDecodeError) as e:raise ValueError('Unreadable Biomed backup') from e
 if p.get('format')!='biomed-system-backup' or p.get('version')!=1:raise ValueError('Unsupported backup version')
 schema=tables(c)
 if set(p.get('tables',{}))!=set(schema):raise ValueError('Backup schema differs. Restore with the same project version that created the backup.')
 for t,cols in schema.items():
  block=p['tables'][t]
  if block.get('columns')!=cols or not isinstance(block.get('rows'),list):raise ValueError('Backup table schema mismatch: '+t)
  for row in block['rows']:
   if not isinstance(row,list) or len(row)!=len(cols):raise ValueError('Invalid row in '+t)
   for v in row:unval(v)
 # Avoid a restored database without a usable administrator account.
 a=p['tables']['accounts'];accounts=[dict(zip(a['columns'],r)) for r in a['rows']]
 if not any(policy.is_system_admin(('', '', '',r['role'],'')) and not r['disabled'] for r in accounts):raise ValueError('Backup has no enabled System Admin account')
 return p
def fingerprint(c):
 d=snapshot(c);d.pop('createdAt');return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def archive(c,db,actor,action):
 raw=pack(snapshot(c));directory=Path(db).parent/'private-archives';directory.mkdir(exist_ok=True,mode=0o700)
 ident='Biomed-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+secrets.token_hex(8)+'.zip'
 path=directory/ident
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 # Verify bytes before any destructive change.
 unpack(path.read_bytes(),c);audit(c,actor,action,{'archive':ident,'sha256':hashlib.sha256(raw).hexdigest()})
 return ident,raw
def replace(c,p):
 old_revisions=dict(c.execute('SELECT key,revision FROM workspace'))
 c.execute('PRAGMA defer_foreign_keys=ON')
 for t in p['tables']:c.execute('DELETE FROM "'+t+'"')
 for t,b in p['tables'].items():
  c.executemany('INSERT INTO "'+t+'" VALUES('+','.join('?' for _ in b['columns'])+')',[tuple(unval(v) for v in r) for r in b['rows']])
 if c.execute('PRAGMA foreign_key_check').fetchone():raise ValueError('Backup contains broken relational references; nothing was restored')
 if c.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('Database integrity check failed')
 c.execute('DELETE FROM sessions');c.execute('DELETE FROM outlook_oauth')
 # Never automatically resume external mailbox writes after a restore.
 c.execute("DELETE FROM outlook_accounts");c.execute('DELETE FROM outlook_events');c.execute('DELETE FROM outlook_private')
 c.execute('DELETE FROM database_import_preview')
 for key,rev in c.execute('SELECT key,revision FROM workspace').fetchall():c.execute('UPDATE workspace SET revision=? WHERE key=?',(max(rev,old_revisions.get(key,0))+1,key))
def reset(c):
 # Keep authentication, roles, website/configuration and migration sentinels; clear operational records.
 keep={'accounts','user_preferences','schema_catalog','service_setup','fse_migrations','job_number_migrations','deployment_data_backups','operational_brands','operational_brand_audit','ai_settings','ai_chat_keys','copilot_role_access','copilot_access','crm_bridge_config','integration_config','table_layouts','service_column_preferences','search_favorites','web_catalog','website_files'}
 old_revisions=dict(c.execute('SELECT key,revision FROM workspace'))
 c.execute('PRAGMA defer_foreign_keys=ON')
 portal=c.execute("select value from workspace where key='biomed_portal_v33_clean'").fetchone();portal=json.loads(portal[0]) if portal else {}
 isrow=c.execute("select value from workspace where key='biomed_is_v50_transactions'").fetchone();isdata=json.loads(isrow[0]) if isrow else {}
 budget=c.execute("select value from workspace where key='biomed_budget_v60_years'").fetchone();budget=json.loads(budget[0]) if budget else {}
 for t in tables(c):
  if t not in keep and t!='workspace':c.execute('DELETE FROM "'+t+'"')
 for k,v in list(portal.items()):
  if isinstance(v,list) and k not in {'users','departments','forms','resources','content','siteSections','productLines','brands','operationalBrands','assets'}:portal[k]=[]
 for k,v in list(isdata.items()):
  if isinstance(v,list) and k not in {'users','operationalBrands'}:isdata[k]=[]
 for state in budget.get('years',{}).values():
  for k in ['products','expenses','workforce','ledger','approvals','versions']:state[k]=[]
 c.execute('DELETE FROM workspace')
 for key,value in [('biomed_portal_v33_clean',portal),('biomed_is_v50_transactions',isdata),('biomed_budget_v60_years',budget)]:c.execute('insert into workspace values(?,?,?)',(key,json.dumps(value,ensure_ascii=False),old_revisions.get(key,0)+1))
 c.execute('DELETE FROM sessions');c.execute('DELETE FROM outlook_oauth');c.execute('DELETE FROM database_import_preview')
 if c.execute('PRAGMA foreign_key_check').fetchone():raise ValueError('Reset failed relational validation; no data changed')
def handle(h,method,connect,session,permissions,origin,db):
 actor=session(h)
 if not actor:return h.reply(401,{'error':'Sign in required'})
 try:
  perms=permissions(actor);policy.need(perms,'system.database.view')
  with connect() as c:
   initialize(c)
   if method=='GET':
    directory=Path(db).parent/'private-archives'
    return h.reply(200,{'permissions':sorted(perms),'adminSelfApprovalTesting':policy.admin_self_approval(actor,c),'isSystemAdmin':policy.is_system_admin(actor),'tables':{t:c.execute('SELECT COUNT(*) FROM "'+t+'"').fetchone()[0] for t in tables(c)},'archives':[p.name for p in sorted(directory.glob('*.zip'),reverse=True)] if directory.exists() else [],'audit':[dict(zip(['at','actor','action','detail'],r)) for r in c.execute('SELECT at,actor,action,detail FROM system_admin_audit ORDER BY id DESC LIMIT 30')]})
   if not origin(h):raise policy.PermissionDenied('Invalid origin')
   length=int(h.headers.get('Content-Length',0))
   if not 0<length<=MAX*1.4:raise ValueError('Maximum request size exceeded')
   b=json.loads(h.rfile.read(length));action=b.get('action');c.execute('BEGIN IMMEDIATE')
   if action=='testing':
    policy.need(perms,'system.database.configure')
    if not policy.is_system_admin(actor):raise policy.PermissionDenied('Only System Admin can change testing mode')
    if not isinstance(b.get('enabled'),bool):raise ValueError('Choose enabled or disabled')
    c.execute('insert or replace into system_controls values(?,?)',('adminSelfApprovalTesting',json.dumps(b['enabled'])));audit(c,actor,'Test approvals configured',{'enabled':b['enabled']});return h.reply(200,{'saved':True})
   if action in ['backup','download']:
    policy.need(perms,'system.database.export')
    if action=='backup':name,raw=archive(c,db,actor,'Backup')
    else:
     name=str(b.get('name',''))
     if Path(name).name!=name or not name.endswith('.zip'):raise ValueError('Invalid archive name')
     path=Path(db).parent/'private-archives'/name
     if not path.is_file():raise ValueError('Archive not found')
     raw=path.read_bytes();audit(c,actor,'Archive downloaded',{'archive':name})
    return h.reply(200,{'filename':name,'file':base64.b64encode(raw).decode()})
   if action=='inspect':
    policy.need(perms,'system.database.restore');raw=base64.b64decode(b.get('file',''),validate=True);p=unpack(raw,c)
    # Dry run against a private in-memory clone; never modifies live rows.
    import sqlite3
    trial=sqlite3.connect(':memory:');image=bytearray(c.serialize());image[18:20]=b'\x01\x01';trial.deserialize(bytes(image));trial.execute('PRAGMA foreign_keys=ON')
    try:
     trial.execute('BEGIN');replace(trial,p);trial.rollback()
    finally:trial.close()
    token=secrets.token_urlsafe(32)
    import time
    c.execute('DELETE FROM database_import_preview WHERE expires<?',(time.time(),));c.execute('insert into database_import_preview values(?,?,?,?,?)',(token,actor[0],time.time()+600,fingerprint(c),raw))
    return h.reply(200,{'token':token,'createdAt':p['createdAt'],'tables':{t:len(x['rows']) for t,x in p['tables'].items()},'scope':p['scope']})
   if action not in ['restore','reset']:raise ValueError('Unknown database action')
   policy.need(perms,'system.database.'+action)
   if b.get('confirm')!=('RESTORE ALL DATA' if action=='restore' else 'ARCHIVE AND RESET'):raise ValueError('Type the exact confirmation phrase')
   if len(str(b.get('reason','')).strip())<5:raise ValueError('Enter a reason of at least five characters')
   if action=='restore':
    import time
    r=c.execute('select account_id,expires,digest,payload from database_import_preview where token=?',(b.get('token'),)).fetchone()
    if not r or r[0]!=actor[0] or r[1]<time.time():raise ValueError('Preview expired; inspect the backup again')
    if r[2]!=fingerprint(c):raise ValueError('Data changed after preview; inspect the backup again')
    p=unpack(r[3],c)
   import time
   if c.execute('SELECT 1 FROM outlook_accounts WHERE lease_until>?',(time.time(),)).fetchone():raise ValueError('An Outlook sync is running. Wait for it to finish before resetting or restoring.')
   name,raw=archive(c,db,actor,'Before '+action)
   if action=='restore':replace(c,p)
   else:reset(c)
   audit(c,actor,action,{'reason':b['reason'],'recoveryArchive':name})
   return h.reply(200,{'saved':True,'recoveryArchive':name,'signInRequired':True})
 except policy.PermissionDenied as e:return h.reply(403,{'error':str(e)})
 except (ValueError,KeyError,TypeError,OverflowError) as e:return h.reply(400,{'error':str(e)})
 except Exception as e:
  import logging
  logging.exception('Database administration failed')
  return h.reply(400,{'error':'Database operation failed; changes were rolled back. Check server logs.'})
