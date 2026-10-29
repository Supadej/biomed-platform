import operational_brands
import service_inventory,service_report
import outlook_sync
import minutes_ack
import table_layouts
import job_numbers
import instrument_service
import application_service
import staff_directory
import document_workflow
import borrowing
"""Mac-local SQLite persistence. No external packages or network listener."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit, unquote
import json, sqlite3, os, hashlib, hmac, secrets, time, base64, re
ROOT = Path(__file__).resolve().parent
DB = Path(os.environ.get('BIOMED_DATABASE_PATH', str(ROOT / 'data' / 'biomed.sqlite3'))).resolve()
IS_KEY = 'biomed_is_v50_transactions'
import sys
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import permissions_policy as policy
import integration_api
import crm_api,crm_http,portal_crm
import budget_governance,finance_workspace,express_import,database_admin
import budget_demo_comparison
import portal_extensions
import web_catalog
import ai_chat_api
from public_website import project_public
from website_files import decode_upload,public_reference,validate_references
from urllib.parse import quote,parse_qs
def connect():
    c=sqlite3.connect(DB, timeout=20)
    c.execute('PRAGMA foreign_keys=ON')
    return c
def initialize():
    DB.parent.mkdir(parents=True,exist_ok=True)
    with connect() as c:
        integration_api.initialize(c)
        web_catalog.init(c)
        ai_chat_api.init(c)
        crm_api.initialize(c)
        portal_crm.initialize(c)
        instrument_service.initialize(c)
        application_service.initialize(c)
        table_layouts.initialize(c)
        c.executescript('''
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS workspace(key TEXT PRIMARY KEY,value TEXT,revision INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS accounts(id TEXT PRIMARY KEY,email TEXT NOT NULL UNIQUE,name TEXT NOT NULL,role TEXT NOT NULL,user_id TEXT NOT NULL,password_hash BLOB NOT NULL,salt BLOB NOT NULL,iterations INTEGER NOT NULL,disabled INTEGER NOT NULL DEFAULT 0,failed_attempts INTEGER NOT NULL DEFAULT 0,locked_until INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS user_preferences(account_id TEXT NOT NULL REFERENCES accounts(id),system TEXT NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(account_id,system));
        CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY,account_id TEXT NOT NULL REFERENCES accounts(id),expires_at INTEGER NOT NULL,created_at INTEGER NOT NULL);
        CREATE INDEX IF NOT EXISTS sessions_expiry ON sessions(expires_at);
        CREATE TABLE IF NOT EXISTS documents(id TEXT PRIMARY KEY,kind TEXT NOT NULL,reference TEXT,status TEXT,source_id TEXT,payload TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS document_kind ON documents(kind,status);
        CREATE INDEX IF NOT EXISTS document_source ON documents(source_id);
        CREATE TABLE IF NOT EXISTS document_lines(document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,position INTEGER NOT NULL,product_id TEXT,payload TEXT NOT NULL,PRIMARY KEY(document_id,position));
        CREATE TABLE IF NOT EXISTS masters(category TEXT NOT NULL,id TEXT NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(category,id));
        CREATE TABLE IF NOT EXISTS stock_records(category TEXT NOT NULL,position INTEGER NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(category,position));
        CREATE TABLE IF NOT EXISTS website_files(id TEXT PRIMARY KEY,filename TEXT NOT NULL,mime TEXT NOT NULL,content BLOB NOT NULL,created_by TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS schema_catalog(table_name TEXT NOT NULL,column_name TEXT NOT NULL,sql_type TEXT,nullable INTEGER,PRIMARY KEY(table_name,column_name));
        ''')
        staff_directory.initialize(c)
        database_admin.initialize(c)
        budget_governance.initialize(c)
        finance_workspace.initialize(c)
        express_import.initialize(c)
        outlook_sync.initialize(c)
        minutes_ack.initialize(c)
        import calendar_features
        calendar_features.initialize(c)
        instrument_service.seed_workbook(c)
        service_inventory.initialize(c)
        service_report.initialize(c)
        import service_referrals
        service_referrals.initialize(c)
        service_referrals.migrate_helpdesk_priorities(c)
        import service_catalog
        service_catalog.setup(c)
        operational_brands.initialize(c)
        import document_numbers
        document_numbers.initialize(c)
        for ident,reference in c.execute('SELECT id,reference FROM documents WHERE reference IS NOT NULL'):
            c.execute('INSERT OR IGNORE INTO document_number_reservations VALUES(?,?,?)',('is',ident,reference))
        job_numbers.migrate(c)
        instrument_service.migrate_ticket_instrument_links(c)
        application_service.migrate(c)
        mapping=json.loads((ROOT/'sql-mapping.json').read_text())
        c.executemany('INSERT OR REPLACE INTO schema_catalog VALUES(?,?,?,?)',[(t,x['name'],x['type'],x['nullable']) for t,cols in mapping['tables'].items() for x in cols])
        portal=c.execute("SELECT value FROM workspace WHERE key='biomed_portal_v33_clean'").fetchone()
        if portal and portal[0]:
            value=json.loads(portal[0])
            if policy.migrate_portal(value):c.execute("UPDATE workspace SET value=?,revision=revision+1 WHERE key='biomed_portal_v33_clean'",(encode(value),))
        staff_directory.migrate(c)
        budget_demo_comparison.apply(c)
    with connect() as c:portal_extensions.initialize(c)

def encode(v):return json.dumps(v,ensure_ascii=False,separators=(',',':'))
def project(c,value):
    data=json.loads(value)
    if not isinstance(data,dict):raise ValueError('IS workspace must be an object')
    docs=data.get('documents',[])
    if not isinstance(docs,list):raise ValueError('Invalid documents')
    c.execute('DELETE FROM document_lines');c.execute('DELETE FROM documents')
    for d in docs:
        if not d.get('id') or not d.get('kind'):raise ValueError('Document ID and kind required')
        c.execute('INSERT INTO documents VALUES(?,?,?,?,?,?)',(d['id'],d['kind'],d.get('ref'),d.get('status'),d.get('sourceId'),encode(d)))
        for i,line in enumerate(d.get('lines',[])):
            c.execute('INSERT INTO document_lines VALUES(?,?,?,?)',(d['id'],i,line.get('productId'),encode(line)))
    c.execute('DELETE FROM masters')
    for category in ['customers','suppliers','products','warehouses','kits']:
        for item in data.get(category,[]):
            ident=item if isinstance(item,str) else item.get('id',item.get('name'))
            if not ident:raise ValueError('Master ID required')
            c.execute('INSERT INTO masters VALUES(?,?,?)',(category,str(ident),encode(item)))
    c.execute('DELETE FROM stock_records')
    for category in ['lots','movements','quarantines','stockChecks','warehouseMoves']:
        for i,item in enumerate(data.get(category,[])):
            c.execute('INSERT INTO stock_records VALUES(?,?,?)',(category,i,encode(item)))
PASSWORD_ITERATIONS=310000
def password_record(password,salt=None,iterations=PASSWORD_ITERATIONS):
    salt=salt or secrets.token_bytes(16)
    return salt,hashlib.pbkdf2_hmac('sha256',password.encode(),salt,iterations,dklen=32),iterations
def session_account(handler):
    token=handler.headers.get('Cookie','')
    token=next((x.split('=',1)[1] for x in token.split('; ') if x.startswith('biomed_session=')),None)
    if not token:return None
    with connect() as c:
        account=c.execute('SELECT a.id,a.email,a.name,a.role,a.user_id FROM sessions s JOIN accounts a ON a.id=s.account_id WHERE s.token_hash=? AND s.expires_at>? AND a.disabled=0',(hashlib.sha256(token.encode()).hexdigest(),int(time.time()))).fetchone()
        if account:
            row=c.execute("SELECT value FROM workspace WHERE key='biomed_portal_v33_clean'").fetchone()
            data=json.loads(row[0]) if row and row[0] else {}
            profile=next((u for u in data.get('users',[]) if u.get('id')==account[4]),None)
            if profile and profile.get('active',True) is False:return None
            if profile:account=(*account[:3],profile.get('role',account[3]),account[4])
        return account

def portal_permissions(user_id,role):
    with connect() as c:row=c.execute('SELECT value FROM workspace WHERE key=?',('biomed_portal_v33_clean',)).fetchone()
    try:
        data=json.loads(row[0]) if row and row[0] else {}
        return set(data.get('roles',{}).get(role,[]))
    except Exception:return set()
def account_permissions(user):
    perms=portal_permissions(user[4],user[3])
    if str(user[3]).strip().lower().replace('_',' ').replace('-',' ') in ('system admin','administrator'):
        return {p['key'] for p in policy.CATALOG['permissions']} | perms
    if not perms and user[3]=='System Admin':
        with connect() as c:exists=c.execute("SELECT 1 FROM workspace WHERE key='biomed_portal_v33_clean'").fetchone()
        if not exists:return {p['key'] for p in policy.CATALOG['permissions']}
    return perms
def authorized_workspace(user,key,method):
    perms=account_permissions(user)
    if key.endswith('_before_restore'):return 'is.backup.restore' in perms or 'is.backup.export' in perms
    if key=='biomed_budget_v65_before_reset':return 'budget.settings.backup' in perms or 'budget.settings.restore' in perms
    if key.startswith('biomed_is_'):
        if key=='biomed_is_crm_order_request':return 'portal.pipeline.edit' in perms or 'is.sales-order.create' in perms
        return 'is_view' in perms
    if key.startswith('biomed_budget'):return 'budget_view' in perms
    return True

def allowed_origins():
    values={'http://127.0.0.1:8765','http://localhost:8765'}
    values.update(x.strip().rstrip('/') for x in os.environ.get('BIOMED_ALLOWED_ORIGINS','').split(',') if x.strip())
    domain=os.environ.get('RAILWAY_PUBLIC_DOMAIN','').strip()
    if domain:values.add('https://'+domain)
    return values

def valid_origin(handler):
    origin=handler.headers.get('Origin')
    return origin is None or origin in allowed_origins()

def prepare_database():
    """Copy the shipped database once; never replace an existing persistent DB."""
    DB.parent.mkdir(parents=True,exist_ok=True)
    seed=ROOT/'data'/'biomed.sqlite3'
    if DB!=seed.resolve() and not DB.exists() and seed.is_file():
        with sqlite3.connect('file:'+str(seed)+'?mode=ro',uri=True) as source:
            with sqlite3.connect(DB) as target:source.backup(target)
    initialize()

crm_http.configure(connect,lambda h:session_account(h),lambda a:account_permissions(a),lambda h:valid_origin(h))
class Handler(crm_http.CRMHandlerMixin,SimpleHTTPRequestHandler):
    def log_request(self,code='-',size='-'):
        if urlsplit(self.path).path=='/api/outlook/callback':return self.log_message('\"%s /api/outlook/callback %s\" %s %s',self.command,self.request_version,str(code),str(size))
        return super().log_request(code,size)
    def guess_type(self,path):
        content_type=super().guess_type(path)
        if content_type.startswith('text/') or content_type in ('application/javascript','application/json'):
            return content_type+'; charset=utf-8'
        return content_type
    def private_static_path(self):
        path=unquote(urlsplit(self.path).path)
        parts=Path(path).parts
        return path=='/TEST_ACCOUNT_ACCESS.json' or path.startswith('/reference/service-report/') or any(part.startswith(".") and part not in (".","..") for part in parts) or any(part in ("tests","__pycache__") for part in parts) or Path(path).suffix.lower() in (".py",".pyc",".sqlite3",".db",".sql",".zip",".bak",".pem",".key")
    def do_HEAD(self):
        if self.private_static_path():return self.send_error(404)
        path=urlsplit(self.path).path
        if path.startswith(('/reference','/data','/crm/storage/')) or Path(path).suffix in ['.py','.sqlite3','.sql','.zip']:return self.send_error(404)
        super().do_HEAD()
    def end_headers(self):
        self.send_header('Cache-Control','no-store')
        super().end_headers()
    def reply(self,status,data):
        raw=encode(data).encode();self.send_response(status)
        self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)))
        self.end_headers();self.wfile.write(raw)
    def key(self):return unquote(urlsplit(self.path).path[len('/api/storage/'):])
    def do_GET(self):
        if self.private_static_path():return self.send_error(404)
        path=urlsplit(self.path).path
        if path=='/api/database-admin':return database_admin.handle(self,'GET',connect,session_account,account_permissions,valid_origin,DB)
        if path=='/api/operational-brands':return operational_brands.handle(self,'GET',connect,session_account,account_permissions,valid_origin)
        if path=='/api/express-import':return express_import.handle(self,'GET',connect,session_account,account_permissions,valid_origin)
        if path=='/api/finance-workspace':return finance_workspace.handle(self,'GET',connect,session_account,account_permissions,valid_origin)
        if path=='/api/budget-governance':return budget_governance.handle(self,'GET',connect,session_account,account_permissions,valid_origin)
        if path=='/api/service-inventory':return service_inventory.handle(self,'GET',connect,session_account,account_permissions,valid_origin)
        if path=='/api/service-report':return service_report.handle(self,connect,session_account,account_permissions)
        if path.startswith('/api/outlook/'):return outlook_sync.handle(self,'GET',connect,session_account,account_permissions,valid_origin)
        if path=='/api/minutes':return minutes_ack.handle(self,'GET',connect,session_account,account_permissions,valid_origin)
        if path=='/api/table-layouts':return table_layouts.handle(self,'GET',connect,session_account,valid_origin)
        if path=='/api/is-workflow':return document_workflow.handle(self,'GET',connect,session_account,account_permissions,valid_origin)
        if path=='/api/staff-directory':return staff_directory.handle(self,'GET',connect,session_account,account_permissions,valid_origin)
        if path=='/api/application-service':return application_service.handle(self,'GET',connect,session_account,account_permissions,valid_origin)
        if path=='/api/service':return instrument_service.handle(self,'GET',connect,session_account,account_permissions,valid_origin)
        if path.startswith('/api/ai/'):return ai_chat_api.handle(self,'GET',connect,session_account,account_permissions,valid_origin)
        if path.startswith('/api/catalog/') and path!='/api/catalog/enquiry':return web_catalog.handle(self,'GET',connect,session_account,account_permissions,valid_origin)
        if path.startswith(('/biomedapi/','/api/crm/','/crm/storage/')) or re.fullmatch(r'/crm/assets/profile/[a-f0-9-]{36}\.jpg',path):return self.crm_request('GET')
        if path in ['/api/preferences/search-favorites','/api/portal/quotation-snapshot'] or path.startswith('/api/portal/attachments'):return portal_extensions.handle(self,'GET',connect,session_account,account_permissions,valid_origin)
        if path=='/api/preferences/quick-access':return self.quick_preferences('GET')
        if path.startswith('/api/integrations/'):
            return self.integration_request('GET')
        if path.startswith('/api/website/files/'):
            id=path.rsplit('/',1)[-1]
            with connect() as c:
                file=c.execute('SELECT filename,mime,content FROM website_files WHERE id=?',(id,)).fetchone()
                row=c.execute("SELECT value FROM workspace WHERE key='biomed_portal_v33_clean'").fetchone()
            if not file:return self.send_error(404)
            public=public_reference(json.loads(row[0]) if row and row[0] else {},id)
            actor=session_account(self)
            if not public and (not actor or 'content' not in account_permissions(actor)):return self.send_error(404)
            self.send_response(200);self.send_header('Content-Type',file[1]);self.send_header('Content-Length',str(len(file[2])));self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Disposition',"inline; filename*=UTF-8''"+quote(file[0],safe=''));self.end_headers();self.wfile.write(file[2]);return
        if path=='/api/public/website':
            with connect() as c:row=c.execute("SELECT value FROM workspace WHERE key='biomed_portal_v33_clean'").fetchone()
            return self.reply(200,project_public(json.loads(row[0]) if row and row[0] else {}))
        if path.startswith('/api/auth/me'):
            user=session_account(self)
            if not user:return self.reply(401,{'error':'Sign in required'})
            return self.reply(200,{'id':user[0],'email':user[1],'name':user[2],'role':user[3],'user_id':user[4]})
        if path.startswith('/api/storage/'):
            user=session_account(self)
            if not user:return self.reply(401,{'error':'Sign in required'})
            if not authorized_workspace(user,self.key(),'GET'):return self.reply(403,{'error':'Module view permission required'})
            with connect() as c:row=c.execute('SELECT value,revision FROM workspace WHERE key=?',(self.key(),)).fetchone()
            return self.reply(200,dict(value=policy.read_filter(account_permissions(user),self.key(),row[0]),revision=row[1]) if row else dict(value=None,revision=0))
        if path.startswith('/reference/') or path=='/reference':return self.send_error(404)
        if path.startswith('/crm/') and (path.endswith('.html') or path=='/crm/'):
            page=path.rsplit('/',1)[-1]
            module='calendar' if page in ['event.html'] else 'external_helpdesk' if 'helpdesk' in page or page=='ticket-report.html' else 'projects' if 'project' in page else 'sales_plan'
            self.send_response(302);self.send_header('Location','/?portal=1&module='+module);self.end_headers();return
        if path=='/api/health':return self.reply(200,{'database':'SQLite','schema_version':1,'release':'portal-date-defaults-20261026'})
        resolved=Path(self.translate_path(self.path)).resolve()
        if any(d in resolved.parents for d in [DB.parent.resolve(),(ROOT/'data').resolve(),(ROOT/'.git').resolve(),(ROOT/'reference').resolve()]) or resolved.suffix in ['.py','.sqlite3','.db','.wal','.shm']:return self.send_error(403)
        if path=='/app.html':
            self.send_response(302);self.send_header('Location','/biomed-is.html');self.end_headers();return
        super().do_GET()
    def integration_request(self,method):
        actor=session_account(self)
        if not actor:return self.reply(401,{'error':'Sign in required'})
        if method=='POST' and not valid_origin(self):return self.reply(403,{'error':'Invalid origin'})
        try:
            parts=urlsplit(self.path);chunks=parts.path.strip('/').split('/')
            if len(chunks)!=4:raise ValueError('Invalid integration route')
            direction,action=chunks[2:];year=parse_qs(parts.query).get('fy',['2027'])[0]
            if method=='GET' and action not in ['config','preview'] or method=='POST' and action not in ['save','run']:raise ValueError('Invalid integration method')
            body={}
            if method=='POST':
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=2*1024*1024:raise ValueError('Invalid request size')
                body=json.loads(self.rfile.read(length))
            with connect() as c:
                c.execute('BEGIN IMMEDIATE' if method=='POST' else 'BEGIN')
                result=integration_api.handle(self,direction,action,year,body,c,actor,account_permissions(actor),project)
            return self.reply(200,result)
        except policy.PermissionDenied as e:return self.reply(403,{'error':str(e)})
        except (ValueError,KeyError,TypeError) as e:return self.reply(400,{'error':str(e)})
    def quick_preferences(self,method):
        actor=session_account(self)
        if not actor:return self.reply(401,{'error':'Sign in required'})
        if method=='GET':
            with connect() as c:rows=c.execute('SELECT system,payload FROM user_preferences WHERE account_id=?',(actor[0],)).fetchall()
            return self.reply(200,{k:json.loads(v) for k,v in rows})
        if not valid_origin(self):return self.reply(403,{'error':'Invalid origin'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=4096:raise ValueError('Invalid preference size')
            data=json.loads(self.rfile.read(length));system=data.get('system');items=data.get('items')
            if system not in ['is','portal','budget','crm'] or not isinstance(items,list) or len(items)>12 or any(not isinstance(x,str) or not re.fullmatch(r'[a-z0-9_-]{1,64}',x) for x in items):raise ValueError('Choose at most 12 shortcuts')
            with connect() as c:c.execute('INSERT OR REPLACE INTO user_preferences VALUES(?,?,?)',(actor[0],system,encode(list(dict.fromkeys(items)))))
            return self.reply(200,{'saved':True})
        except (ValueError,TypeError):return self.reply(400,{'error':'Invalid preferences'})
    def do_POST(self):
        path=urlsplit(self.path).path
        if path=='/api/database-admin':return database_admin.handle(self,'POST',connect,session_account,account_permissions,valid_origin,DB)
        if path=='/api/operational-brands':return operational_brands.handle(self,'POST',connect,session_account,account_permissions,valid_origin)
        if path=='/api/express-import':return express_import.handle(self,'POST',connect,session_account,account_permissions,valid_origin)
        if path=='/api/finance-workspace':return finance_workspace.handle(self,'POST',connect,session_account,account_permissions,valid_origin)
        if path=='/api/budget-governance':return budget_governance.handle(self,'POST',connect,session_account,account_permissions,valid_origin)
        if path=='/api/service-inventory':return service_inventory.handle(self,'POST',connect,session_account,account_permissions,valid_origin)
        if path.startswith('/api/outlook/'):return outlook_sync.handle(self,'POST',connect,session_account,account_permissions,valid_origin)
        if path=='/api/minutes':return minutes_ack.handle(self,'POST',connect,session_account,account_permissions,valid_origin)
        if path=='/api/table-layouts':return table_layouts.handle(self,'POST',connect,session_account,valid_origin)
        if path=='/api/is-workflow':return document_workflow.handle(self,'POST',connect,session_account,account_permissions,valid_origin)
        if path=='/api/staff-directory':return staff_directory.handle(self,'POST',connect,session_account,account_permissions,valid_origin)
        if path=='/api/application-service':return application_service.handle(self,'POST',connect,session_account,account_permissions,valid_origin)
        if path=='/api/service':return instrument_service.handle(self,'POST',connect,session_account,account_permissions,valid_origin)
        if path.startswith('/api/ai/'):return ai_chat_api.handle(self,'POST',connect,session_account,account_permissions,valid_origin)
        if path.startswith('/api/catalog/'):return web_catalog.handle(self,'POST',connect,session_account,account_permissions,valid_origin)
        if path.startswith(('/biomedapi/','/api/crm/','/crm/storage/')) or re.fullmatch(r'/crm/assets/profile/[a-f0-9-]{36}\.jpg',path):return self.crm_request('POST')
        if path in ['/api/preferences/search-favorites','/api/portal/quotation-snapshot'] or path.startswith('/api/portal/attachments'):return portal_extensions.handle(self,'POST',connect,session_account,account_permissions,valid_origin)
        if path=='/api/preferences/quick-access':return self.quick_preferences('POST')
        if path.startswith('/api/integrations/'):
            return self.integration_request('POST')
        if path=='/api/website/uploads':
            actor=session_account(self)
            if not actor:return self.reply(401,{'error':'Sign in required'})
            if not valid_origin(self):return self.reply(403,{'error':'Invalid origin'})
            try:
                perms=account_permissions(actor);policy.need(perms,'content');policy.need(perms,'portal.content.upload');policy.need(perms,'portal.content.create','portal.content.edit')
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=15*1024*1024:raise ValueError('Maximum file size is 10 MB')
                metadata,raw=decode_upload(json.loads(self.rfile.read(length)))
                with connect() as c:c.execute('INSERT INTO website_files VALUES(?,?,?,?,?)',(metadata['id'],metadata['name'],metadata['mime'],raw,actor[0]))
                return self.reply(200,metadata)
            except policy.PermissionDenied as e:return self.reply(403,{'error':str(e)})
            except (ValueError,KeyError) as e:return self.reply(400,{'error':str(e)})
        if path not in ['/api/auth/login','/api/auth/logout','/api/auth/create']:return self.send_error(404)
        origin=self.headers.get('Origin')
        if not valid_origin(self):return self.reply(403,{'error':'Invalid origin'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=10000:raise ValueError('Invalid request')
            data=json.loads(self.rfile.read(length))
            if path=='/api/auth/login':
                email=str(data.get('email','')).strip().lower();password=str(data.get('password',''))
                with connect() as c:account=c.execute('SELECT id,email,name,role,user_id,password_hash,salt,iterations,disabled,failed_attempts,locked_until FROM accounts WHERE email=?',(email,)).fetchone()
                candidate=hashlib.pbkdf2_hmac('sha256',password.encode(),account[6] if account else b'0'*16,account[7] if account else PASSWORD_ITERATIONS,dklen=32)
                now=int(time.time())
                if not account or account[8] or account[10]>now or not hmac.compare_digest(candidate,account[5]):
                    if account and account[10]<=now:
                        failures=account[9]+1;locked=now+900 if failures>=8 else 0
                        with connect() as c:c.execute('UPDATE accounts SET failed_attempts=?,locked_until=? WHERE id=?',(0 if locked else failures,locked,account[0]))
                    return self.reply(401,{'error':'Email or password is incorrect'})
                with connect() as c:c.execute('UPDATE accounts SET failed_attempts=0,locked_until=0 WHERE id=?',(account[0],))
                token=secrets.token_urlsafe(32);now=int(time.time());token_hash=hashlib.sha256(token.encode()).hexdigest()
                with connect() as c:c.execute('DELETE FROM sessions WHERE expires_at<=?',(now,));c.execute('INSERT INTO sessions VALUES(?,?,?,?)',(token_hash,account[0],now+8*60*60,now))
                self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Set-Cookie','biomed_session='+token+'; Path=/; HttpOnly; SameSite=Strict; Max-Age=28800'+('; Secure' if os.environ.get('BIOMED_HTTPS')=='1' else ''));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(encode({'id':account[0],'email':account[1],'name':account[2],'role':account[3],'user_id':account[4]}).encode());return
            if path=='/api/auth/logout':
                user=session_account(self)
                if user:
                    token=next((x.split('=',1)[1] for x in self.headers.get('Cookie','').split('; ') if x.startswith('biomed_session=')),None)
                    if token:
                        with connect() as c:c.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(token.encode()).hexdigest(),))
                self.send_response(200);self.send_header('Set-Cookie','biomed_session=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0');self.send_header('Content-Length','2');self.end_headers();self.wfile.write(b'{}');return
            actor=session_account(self)
            if not actor or not {'users','portal.users.create'}.issubset(account_permissions(actor)):return self.reply(403,{'error':'Staff account creation permission required'})
            with connect() as c:
                c.execute('BEGIN IMMEDIATE');result=staff_directory.dispatch(c,actor,account_permissions(actor),{**data,'action':'create'})
            return self.reply(201,result)
        except policy.PermissionDenied as e:return self.reply(403,{'error':str(e)})
        except sqlite3.IntegrityError:return self.reply(409,{'error':'An account already uses that email'})
        except (ValueError,KeyError) as e:return self.reply(400,{'error':str(e)})
        except Exception:return self.reply(500,{'error':'Authentication request failed'})
    def do_PUT(self):
        if urlsplit(self.path).path.startswith(('/biomedapi/','/api/crm/')):return self.crm_request('PUT')
        self.mutate(False)
    def do_DELETE(self):
        if urlsplit(self.path).path.startswith('/api/catalog/'):return web_catalog.handle(self,'DELETE',connect,session_account,account_permissions,valid_origin)
        if urlsplit(self.path).path.startswith(('/biomedapi/','/api/crm/')):return self.crm_request('DELETE')
        self.mutate(True)
    def mutate(self,remove):
        if not urlsplit(self.path).path.startswith('/api/storage/'):return self.send_error(404)
        actor=session_account(self)
        if not actor:return self.reply(401,{'error':'Sign in required'})
        if not authorized_workspace(actor,self.key(),'PUT' if not remove else 'DELETE'):return self.reply(403,{'error':'Module edit permission required'})
        if not valid_origin(self):return self.send_error(403)
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=128*1024*1024:raise ValueError('Invalid request size')
            body=json.loads(self.rfile.read(length));key=self.key()
            value=None if remove else body['value']
            if value is not None and not isinstance(value,str):raise ValueError('String value required')
            with connect() as c:
                c.execute('BEGIN IMMEDIATE')
                row=c.execute('SELECT revision,value FROM workspace WHERE key=?',(key,)).fetchone()
                revision=row[0] if row else 0
                if body.get('revision')!=revision:return self.reply(409,{'error':'Stale workspace'})
                if key in [IS_KEY,'biomed_budget_v60_years','biomed_portal_v33_clean']:
                    if remove:raise policy.PermissionDenied('Workspace deletion is not permitted')
                    if body.get('operation') not in ['restore','reset_current','reset_all']:value=policy.merge_scope(account_permissions(actor),key,row[1] if row else None,value)
                    operational_brands.validate_workspace(c,key,row[1] if row else None,value)
                    if key=='biomed_budget_v60_years':budget_governance.guard(c,json.loads(row[1] or '{}') if row else {},json.loads(value or '{}'))
                    policy.authorize_change(account_permissions(actor),key,row[1] if row else None,value,body.get('operation'),actor_id=actor[4],admin_test=policy.admin_self_approval(actor,c))
                if key==IS_KEY:document_workflow.guard(json.loads(row[1] or '{}') if row else {},json.loads(value or '{}'))
                if key==IS_KEY and policy.admin_self_approval(actor,c):
                    prev={d['id']:d for d in json.loads(row[1] or '{}').get('documents',[])} if row else {}
                    for d in json.loads(value or '{}').get('documents',[]):
                        if d.get('owner')==actor[4] and d.get('status') in ['Approved','Rejected'] and prev.get(d['id'],{}).get('status')!=d.get('status'):policy.self_approval_audit(c,actor,'IS document',d['id'])
                if key=='biomed_portal_v33_clean':
                    staff_directory.guard_workspace(c,json.loads(row[1] or '{}') if row else {},json.loads(value or '{}'))
                    import visit_features
                    visit_features.sync(c,actor,account_permissions(actor),json.loads(row[1] or '{}') if row else {},json.loads(value or '{}'))
                    validate_references(json.loads(value or '{}'),c)
                    portal_extensions.validate_leave_references(json.loads(value or '{}'),c)
                if key==IS_KEY:
                    borrowing_state=json.loads(value or '{}')
                    borrowing_previous=json.loads(row[1] or '{}') if row else {}
                    prior_documents={d['id']:d for d in borrowing_previous.get('documents',[])}
                    for changed in borrowing_state.get('documents',[]):
                        refs=[l.get('borrowRef') for l in changed.get('lines',[]) if l.get('borrowRef')]
                        before_refs=[l.get('borrowRef') for l in prior_documents.get(changed['id'],{}).get('lines',[]) if l.get('borrowRef')]
                        if refs and refs!=before_refs and changed.get('kind') in ('customer-order','return-product'):
                            policy.need(account_permissions(actor),'is.borrowing.derive')
                    import document_numbers
                    document_numbers.assign(c,borrowing_state,borrowing_previous,preserve_references=body.get('operation')=='restore')
                    value=encode(borrowing_state)
                    borrowing.validate(borrowing_state,borrowing_previous)
                    project(c,value or '{}')
                    portal_crm.sync_documents(c,json.loads(value or '{}'),actor)
                revision+=1
                c.execute('INSERT OR REPLACE INTO workspace VALUES(?,?,?)',(key,value,revision))
            self.reply(200,{'value':policy.read_filter(account_permissions(actor),key,value),'revision':revision})
        except policy.PermissionDenied as e:self.reply(403,{'error':str(e)})
        except (ValueError,KeyError,sqlite3.IntegrityError) as e:self.reply(400,{'error':str(e)})
        except Exception as e:
            print(f'Database write failed for {self.key()}: {type(e).__name__}: {e}',flush=True)
            self.reply(500,{'error':'Database write failed; check the server Terminal for details'})
if __name__=='__main__':
    import sys,threading,webbrowser
    os.chdir(ROOT);prepare_database()
    port=int(os.environ.get('PORT','8765'))
    host=os.environ.get('BIOMED_HOST','0.0.0.0' if os.environ.get('RAILWAY_ENVIRONMENT_ID') or os.environ.get('PORT') else '127.0.0.1')
    server=ThreadingHTTPServer((host,port),Handler)
    print(f'Biomed server listening on {host}:{port}',flush=True)
    if sys.platform=='darwin' and host=='127.0.0.1':threading.Timer(.5,lambda:webbrowser.open(f'http://127.0.0.1:{port}/?portal=1')).start()
    outlook_stop=threading.Event()
    threading.Thread(target=outlook_sync.worker,args=(connect,account_permissions,outlook_stop),daemon=True,name='outlook-sync').start()
    try:server.serve_forever()
    finally:outlook_stop.set()
