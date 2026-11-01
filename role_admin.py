"""Atomic role rename/deletion with explicit reassignment and audit history."""
import json,datetime,unicodedata,sqlite3
import permissions_policy as policy
KEY='biomed_portal_v33_clean'
class Conflict(ValueError):pass
def name(value):
 if not isinstance(value,str):raise ValueError('Enter a role name')
 value=unicodedata.normalize('NFC',value).strip()
 if not value or len(value)>120 or any(ord(x)<32 for x in value) or value.lower() in ['__proto__','constructor','prototype']:raise ValueError('Use a role name of 1–120 characters without control characters')
 return value
def protected(value):
 return value.strip().lower().replace('_',' ').replace('-',' ') in ['system admin','administrator','employee']
def workspace(c):
 r=c.execute('SELECT value,revision FROM workspace WHERE key=?',(KEY,)).fetchone()
 if not r:raise ValueError('Staff workspace unavailable')
 return json.loads(r[0]),r[1]
def dispatch(c,actor,perms,raw=None):
 policy.need(perms,'roles');policy.need(perms,'portal.roles.edit')
 data,revision=workspace(c);roles=data.get('roles',{});profiles={u['id']:u for u in data.get('users',[])}
 accounts=c.execute('SELECT id,user_id,role FROM accounts').fetchall()
 def members(role):
  return {u['id'] for u in profiles.values() if u.get('role')==role}|{uid for aid,uid,r in accounts if profiles.get(uid,{}).get('role',r)==role}
 if raw is None:return {'revision':revision,'roles':[{'name':r,'protected':protected(r),'users':len(members(r))} for r in roles]}
 if raw.get('revision')!=revision:raise Conflict('Roles changed. Refresh the page before retrying.')
 old=name(raw.get('role'));action=raw.get('action')
 if old not in roles:raise ValueError('Role no longer exists. Refresh the page.')
 if action=='visibility':
  policy.need(perms,'portal.roles.visibility')
  settings=raw.get('scopes')
  policy.visibility.validate_config({old:settings},roles)
  data.setdefault('roleRecordScopes',{})[old]=settings
  persist_scope(c,data,actor,old,settings)
  return {'saved':True,'role':old}
 if protected(old):raise ValueError('System Admin and Employee are protected built-in roles; clone one to create a custom role.')
 ids=members(old);target=name(raw.get('name' if action=='rename' else 'replacement','')) if action=='rename' or raw.get('replacement') else ''
 if action=='rename':
  if protected(target):raise ValueError('That name is reserved for a built-in role')
  if target==old:raise ValueError('Enter a different role name')
  if any(r.casefold()==target.casefold() and r!=old for r in roles):raise ValueError('A role with that name already exists')
  data['roles']={target if r==old else r:g for r,g in roles.items()}
  scopes=data.setdefault('roleRecordScopes',{})
  if old in scopes:scopes[target]=scopes.pop(old)
  descriptions=data.setdefault('roleDescriptions',{})
  if old in descriptions:descriptions[target]=descriptions.pop(old)
 elif action=='delete':
  if target==old:raise ValueError('Choose a different replacement role')
  if target and target not in roles:raise ValueError('Choose an existing replacement role')
  if ids and not target:raise Conflict('This role is assigned to users. Choose a replacement role before deleting it.')
  if ids:policy.need(perms,'users');policy.need(perms,'portal.users.assign')
  data.setdefault('roleRecordScopes',{}).pop(old,None)
  del roles[old];data.setdefault('roleDescriptions',{}).pop(old,None)
 else:raise ValueError('Unknown role action')
 for uid in ids:
  if uid in profiles:profiles[uid]['role']=target
  c.execute('UPDATE accounts SET role=? WHERE user_id=?',(target,uid))
  c.execute('UPDATE staff_profiles SET version=version+1 WHERE user_id=?',(uid,))
  if action=='delete':c.execute('DELETE FROM sessions WHERE account_id IN (SELECT id FROM accounts WHERE user_id=?)',(uid,))
 c.execute('UPDATE workspace SET value=?,revision=revision+1 WHERE key=?',(json.dumps(data,ensure_ascii=False),KEY))
 c.execute('CREATE TABLE IF NOT EXISTS role_admin_audit(id INTEGER PRIMARY KEY,at TEXT NOT NULL,actor TEXT NOT NULL,action TEXT NOT NULL,old_name TEXT NOT NULL,new_name TEXT NOT NULL,affected_users INTEGER NOT NULL)')
 c.execute('INSERT INTO role_admin_audit(at,actor,action,old_name,new_name,affected_users) VALUES(?,?,?,?,?,?)',(datetime.datetime.now(datetime.timezone.utc).isoformat(),actor[0],action,old,target,len(ids)))
 import crm_api
 crm_api.bind_users(c)
 return {'saved':True,'role':target if target else next(iter(roles),'Employee'),'affectedUsers':len(ids),'signInAgain':action=='delete' and actor[4] in ids}
def handle(h,method,connect,session,permissions,origin):
 actor=session(h)
 if not actor:return h.reply(401,{'error':'Sign in required'})
 if method=='POST' and not origin(h):return h.reply(403,{'error':'Invalid origin'})
 try:
  raw=None
  if method=='POST':
   length=int(h.headers.get('Content-Length','0'))
   if not 0<length<=65536:raise ValueError('Invalid role request size')
   raw=json.loads(h.rfile.read(length))
   if not isinstance(raw,dict):raise ValueError('Invalid role request')
  with connect() as c:
   c.execute('BEGIN IMMEDIATE' if raw is not None else 'BEGIN');result=dispatch(c,actor,permissions(actor),raw)
  return h.reply(200,result)
 except policy.PermissionDenied as e:return h.reply(403,{'error':str(e)})
 except Conflict as e:return h.reply(409,{'error':str(e)})
 except (ValueError,TypeError,KeyError) as e:return h.reply(400,{'error':str(e)})


def persist_scope(c,data,actor,role,settings):
 c.execute('UPDATE workspace SET value=?,revision=revision+1 WHERE key=?',(json.dumps(data,ensure_ascii=False),KEY))
 c.execute('CREATE TABLE IF NOT EXISTS record_scope_audit(id INTEGER PRIMARY KEY,at TEXT,actor TEXT,role TEXT,settings TEXT)')
 c.execute('INSERT INTO record_scope_audit(at,actor,role,settings) VALUES(?,?,?,?)',(datetime.datetime.now(datetime.timezone.utc).isoformat(),str(actor[0]),role,json.dumps(settings)))


def initialize(c):
 c.execute('CREATE TABLE IF NOT EXISTS record_scope_audit(id INTEGER PRIMARY KEY,at TEXT,actor TEXT,role TEXT,settings TEXT)')
