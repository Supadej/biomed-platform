"""Transactional staff identities, self-service profiles and active employee library."""
import base64,datetime,hashlib,hmac,json,re,secrets,sqlite3,time
import permissions_policy as policy
KEY='biomed_portal_v33_clean'
BASIC=('id','name','mobile','email','dob','lineId','photo','department')
class Conflict(ValueError):pass
def initialize(c):
 c.execute('CREATE TABLE IF NOT EXISTS staff_profiles(user_id TEXT PRIMARY KEY,payload TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 0)')
 c.execute('CREATE TABLE IF NOT EXISTS staff_directory_audit(id INTEGER PRIMARY KEY,at TEXT NOT NULL,actor TEXT NOT NULL,action TEXT NOT NULL,user_id TEXT NOT NULL)')
def workspace(c):
 row=c.execute('SELECT value,revision FROM workspace WHERE key=?',(KEY,)).fetchone()
 return (json.loads(row[0]),row[1]) if row else ({'users':[],'roles':{},'departments':[]},0)
def persist(c,data,revision):
 c.execute('INSERT INTO workspace VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,revision=excluded.revision',(KEY,json.dumps(data,ensure_ascii=False),revision+1))
def audit(c,actor,action,uid):c.execute('INSERT INTO staff_directory_audit(at,actor,action,user_id) VALUES(?,?,?,?)',(datetime.datetime.now(datetime.timezone.utc).isoformat(),actor[0],action,uid))
def need(perms,action):policy.need(perms,'users');policy.need(perms,'portal.users.'+action)
def text(raw,key,limit=200):
 v=raw.get(key,'')
 if not isinstance(v,str) or len(v)>limit:raise ValueError('Invalid '+key)
 return v.strip()
def email(raw):
 v=text(raw,'email',254).lower()
 if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',v):raise ValueError('Enter a valid email address')
 return v
def password(raw,key='password',confirm='confirmPassword'):
 value=raw.get(key)
 if not isinstance(value,str) or not 12<=len(value)<=256:raise ValueError('Password must contain 12 to 256 characters')
 if value!=raw.get(confirm):raise ValueError('Passwords do not match')
 return value
def check_password(account,value):
 if not isinstance(value,str) or not hmac.compare_digest(hashlib.pbkdf2_hmac('sha256',value.encode(),account['salt'],account['iterations'],dklen=32),account['password_hash']):raise ValueError('Current password is incorrect')
def accounts(c):
 c.row_factory=sqlite3.Row
 rows=[dict(r) for r in c.execute('SELECT * FROM accounts')];c.row_factory=None
 return rows
def listing(c):
 data,_=workspace(c);auth={a['user_id']:a for a in accounts(c)};out=[]
 for u in data.get('users',[]):
  if not isinstance(u,dict):continue
  ident=u['id'];a=auth.get(ident);row=c.execute('SELECT payload,version FROM staff_profiles WHERE user_id=?',(ident,)).fetchone();profile=json.loads(row[0]) if row else {}
  out.append({**{k:u.get(k,'') for k in ['id','name','email','department','role','managerId','mobile','dob','lineId','photo']},**profile,'id':ident,'name':a['name'] if a else u.get('name',''),'email':a['email'] if a else u.get('email',''),'role':u.get('role',a['role'] if a else ''),'active':not bool(a['disabled']) and u.get('active',True) is not False if a else u.get('active',True) is not False,'hasAccount':bool(a),'version':row[1] if row else 0})
 return out
def manager_valid(users,ident,manager):
 if not manager:return
 by={u['id']:u for u in users};seen={ident};node=manager
 while node:
  if node in seen:raise ValueError('Reports to cannot create a circular reporting line')
  if node not in by:raise ValueError('Choose an existing reporting manager')
  seen.add(node);node=by[node].get('managerId','')
 if not by[manager].get('active',True):raise ValueError('Choose an active reporting manager')
def guard_last_admin(users,ident,role=None,active=None):
 old=next(u for u in users if u['id']==ident)
 if old['role']=='System Admin' and old['active'] and (role not in [None,'System Admin'] or active is False):
  if not any(u['id']!=ident and u['role']=='System Admin' and u['active'] and u['hasAccount'] for u in users):raise ValueError('Keep at least one active System Admin account')
def profile_values(raw):
 result={k:text(raw,k,100 if k!='mobile' else 50) for k in ['mobile','dob','lineId']}
 if result['dob']:
  try:
   day=datetime.date.fromisoformat(result['dob'])
   if day.isoformat()!=result['dob'] or day>datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).date():raise ValueError()
  except ValueError:raise ValueError('Choose a valid date of birth')
 photo=raw.get('photo','')
 if not isinstance(photo,str) or len(photo)>560000:raise ValueError('Profile picture must be at most 400 KB')
 if photo:
  match=re.fullmatch(r'data:image/(png|jpeg|webp);base64,([A-Za-z0-9+/=]+)',photo)
  if not match:raise ValueError('Choose a PNG, JPEG or WebP picture')
  try:blob=base64.b64decode(match[2],validate=True)
  except ValueError:raise ValueError('Invalid profile picture')
  valid={'png':blob.startswith(b'\x89PNG\r\n\x1a\n'),'jpeg':blob.startswith(b'\xff\xd8\xff'),'webp':blob.startswith(b'RIFF') and blob[8:12]==b'WEBP'}
  if len(blob)>400*1024 or not valid[match[1]]:raise ValueError('Invalid profile picture')
 result['photo']=photo;return result
def set_profile(c,uid,values,version):
 c.execute('INSERT INTO staff_profiles VALUES(?,?,?) ON CONFLICT(user_id) DO UPDATE SET payload=excluded.payload,version=excluded.version',(uid,json.dumps(values,ensure_ascii=False),version+1))
def dispatch(c,actor,perms,raw=None,view='users'):
 initialize(c);users=listing(c);data,revision=workspace(c);me=next((u for u in users if u['id']==actor[4]),None)
 if raw is None:
  if view=='users':need(perms,'view');rows=users
  elif view=='profile':policy.need(perms,'user_profile');policy.need(perms,'portal.user_profile.view');rows=[me] if me else []
  elif view=='library':policy.need(perms,'user_library');policy.need(perms,'portal.user_library.view');rows=[{k:u.get(k,'') for k in BASIC} for u in users if u['active']]
  else:raise ValueError('Unknown staff view')
  return {'users':rows,'departments':data.get('departments',[]),'roles':sorted(data.get('roles',{})) if view=='users' else [],'userId':actor[4],'permissions':sorted(perms)}
 action=raw.get('action');ident=raw.get('id',actor[4]);prior=next((u for u in users if u['id']==ident),None)
 if action=='department':
  need(perms,'manage_departments');names=data.setdefault('departments',[]);name=text(raw,'name');operation=raw.get('operation')
  if not name:raise ValueError('Enter a department name')
  if operation=='add':
   if any(n.casefold()==name.casefold() for n in names):raise ValueError('Department already exists')
   names.append(name)
  elif operation=='remove':
   if any(u['department']==name for u in users):raise ValueError('This department is assigned to users. Reassign them before removing it.')
   if name not in names:raise ValueError('Department unavailable')
   names.remove(name)
  else:raise ValueError('Choose add or remove')
  persist(c,data,revision);audit(c,actor,'department '+operation,name);return {'saved':True}
 if action=='create':
  need(perms,'create');value=password(raw);name=text(raw,'name');mail=email(raw);role=text(raw,'role');dept=text(raw,'department');manager=text(raw,'managerId')
  if not name or role not in data.get('roles',{}):raise ValueError('Choose a valid name and role')
  if role!='Employee':need(perms,'assign')
  if dept not in data.get('departments',[]):raise ValueError('Choose a department from the reference list')
  if any(u['email'].casefold()==mail for u in users):raise ValueError('Email already in use')
  ident=secrets.token_hex(16);manager_valid(users,ident,manager)
  if manager:need(perms,'edit')
  import serve
  salt,digest,it=serve.password_record(value)
  c.execute('INSERT INTO accounts(id,email,name,role,user_id,password_hash,salt,iterations,created_at) VALUES(?,?,?,?,?,?,?,?,?)',(secrets.token_hex(16),mail,name,role,ident,digest,salt,it,datetime.datetime.now(datetime.timezone.utc).isoformat()))
  data.setdefault('users',[]).append({'id':ident,'name':name,'email':mail,'department':dept,'role':role,'managerId':manager,'active':True});persist(c,data,revision);set_profile(c,ident,{},0);audit(c,actor,'create',ident);return {'saved':True,'id':ident}
 if not prior:raise ValueError('User unavailable')
 if raw.get('version')!=prior['version']:raise Conflict('User changed. Refresh before saving.')
 account=next((a for a in accounts(c) if a['user_id']==ident),None);u=next(u for u in data['users'] if u['id']==ident)
 if action=='edit':
  need(perms,'edit');name=text(raw,'name');mail=email(raw);dept=text(raw,'department');role=text(raw,'role');manager=text(raw,'managerId')
  if not name or role not in data.get('roles',{}):raise ValueError('Choose a valid name and role')
  if dept not in data.get('departments',[]):raise ValueError('Choose a department from the reference list')
  if role!=prior['role']:need(perms,'assign')
  manager_valid(users,ident,manager);guard_last_admin(users,ident,role=role)
  if any(x['id']!=ident and x['email'].casefold()==mail for x in users):raise ValueError('Email already in use')
  u.update(name=name,email=mail,department=dept,role=role,managerId=manager)
  if account:
   c.execute('UPDATE accounts SET name=?,email=?,role=? WHERE user_id=?',(name,mail,role,ident))
   if role!=prior['role'] or mail!=prior['email']:c.execute('DELETE FROM sessions WHERE account_id=?',(account['id'],))
  persist(c,data,revision)
 elif action=='active':
  need(perms,'deactivate');active=raw.get('active')
  if type(active) is not bool:raise ValueError('Choose active or inactive')
  if ident==actor[4] and not active:raise ValueError('You cannot deactivate your own account')
  guard_last_admin(users,ident,active=active)
  if not active and any(x.get('managerId')==ident and x['active'] for x in users):raise ValueError('Reassign this user’s active direct reports before deactivating the user')
  u['active']=active
  if account:c.execute('UPDATE accounts SET disabled=?,failed_attempts=0,locked_until=0 WHERE user_id=?',(int(not active),ident));c.execute('DELETE FROM sessions WHERE account_id=?',(account['id'],))
  persist(c,data,revision)
 elif action in ['reset_password','password']:
  if not account:raise ValueError('This historical staff record has no login account')
  if action=='reset_password':need(perms,'reset_password')
  else:
   policy.need(perms,'user_profile');policy.need(perms,'portal.user_profile.password')
   if ident!=actor[4]:raise policy.PermissionDenied('You can change only your own password')
   check_password(account,raw.get('currentPassword'))
  value=password(raw);import serve
  salt,digest,it=serve.password_record(value);c.execute('UPDATE accounts SET password_hash=?,salt=?,iterations=?,failed_attempts=0,locked_until=0 WHERE id=?',(digest,salt,it,account['id']));c.execute('DELETE FROM sessions WHERE account_id=?',(account['id'],))
 elif action=='profile':
  policy.need(perms,'user_profile');policy.need(perms,'portal.user_profile.edit')
  if ident!=actor[4]:raise policy.PermissionDenied('You can edit only your own profile')
  values=profile_values(raw);mail=email(raw)
  if mail!=prior['email']:
   if not account:raise ValueError('Login account unavailable')
   check_password(account,raw.get('currentPassword'))
   if any(x['id']!=ident and x['email'].casefold()==mail for x in users):raise ValueError('Email already in use')
   c.execute('UPDATE accounts SET email=? WHERE id=?',(mail,account['id']));u['email']=mail;persist(c,data,revision)
  set_profile(c,ident,values,prior['version']);audit(c,actor,action,ident);return {'saved':True}
 else:raise ValueError('Unknown staff action')
 row=c.execute('SELECT payload FROM staff_profiles WHERE user_id=?',(ident,)).fetchone();set_profile(c,ident,json.loads(row[0]) if row else {},prior['version']);audit(c,actor,action,ident);return {'saved':True,'signInAgain':ident==actor[4] and (action in ['password','reset_password'] or action=='edit' and (mail!=prior['email'] or role!=prior['role']))}
def handle(h,method,connect,session,permissions,origin):
 actor=session(h)
 if not actor:return h.reply(401,{'error':'Sign in required'})
 if method=='POST' and not origin(h):return h.reply(403,{'error':'Invalid origin'})
 try:
  from urllib.parse import urlsplit,parse_qs
  raw=None
  if method=='POST':
   length=int(h.headers.get('Content-Length','0'))
   if not 0<length<=600000:raise ValueError('Invalid staff request size')
   raw=json.loads(h.rfile.read(length))
   if not isinstance(raw,dict):raise ValueError('Invalid staff request')
  view=parse_qs(urlsplit(h.path).query).get('view',['users'])[0]
  with connect() as c:
   c.execute('BEGIN IMMEDIATE' if raw is not None else 'BEGIN');result=dispatch(c,actor,permissions(actor),raw,view)
  return h.reply(200,result)
 except policy.PermissionDenied as e:return h.reply(403,{'error':str(e)})
 except Conflict as e:return h.reply(409,{'error':str(e)})
 except sqlite3.IntegrityError:return h.reply(409,{'error':'An account already uses that email'})
 except (ValueError,KeyError,TypeError) as e:return h.reply(400,{'error':str(e)})

def guard_workspace(c,old,new):
 """Identity/profile writes use audited staff endpoints; hierarchy edits stay compatible."""
 if set(old.get('roles',{}))-set(new.get('roles',{})):raise policy.PermissionDenied('Use Rename role or Delete role in Roles & responsibilities to remove a role')
 if old.get('departments')!=new.get('departments'):
  names=new.get('departments',[])
  if not isinstance(names,list) or any(not isinstance(n,str) or not n.strip() or len(n)>200 for n in names) or len({n.casefold() for n in names})!=len(names):raise ValueError('Enter unique department names')
  removed=set(old.get('departments',[]))-set(names)
  if any(u.get('department') in removed for u in new.get('users',[])):raise ValueError('Reassign users before removing their department')
 before={u['id']:u for u in old.get('users',[])};after={u['id']:u for u in new.get('users',[])}
 for ident,a in before.items():
  b=after.get(ident)
  if b is None:raise policy.PermissionDenied('Deactivate users through User directory instead of deleting them')
  for key in ['name','email','department','active','mobile','dob','lineId','photo','role']:
   if a.get(key)!=b.get(key):raise policy.PermissionDenied('Use User directory or User Profile to change '+key)
  if a.get('managerId')!=b.get('managerId'):
   manager_valid(new.get('users',[]),ident,b.get('managerId'))
   row=c.execute('SELECT payload,version FROM staff_profiles WHERE user_id=?',(ident,)).fetchone()
   set_profile(c,ident,json.loads(row[0]) if row else {},row[1] if row else 0)
 for ident in set(after)-set(before):
  if before or c.execute('SELECT 1 FROM accounts WHERE user_id=?',(ident,)).fetchone():raise policy.PermissionDenied('Use User directory to create staff accounts')


def migrate(c):
 data,revision=workspace(c)
 if data.get('staffDepartmentsV1') or not data.get('users'):return
 names=list(dict.fromkeys(data.get('departments',[])+[u.get('department','').strip() for u in data['users'] if u.get('department','').strip()]))
 data['departments']=names or ['Management','Administration','Sales','Service','Human Resources','Accounting & Finance']
 data['staffDepartmentsV1']=True;persist(c,data,revision)
