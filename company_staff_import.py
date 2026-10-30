"""One-time, transactional import of the explicitly supplied staff roster.

Payload contains salted password hashes only. The source workbook is not served
or included in the project. Existing identities and transaction links stay stable.
"""
import json,datetime,uuid,base64
from pathlib import Path
import company_role_defaults

KEY='biomed_portal_v33_clean'
VERSION='company-staff-roster-69'
PAYLOAD=Path(__file__).with_name('company-staff-roster-69.json')

def pending(c):
 return PAYLOAD.is_file() and bool(c.execute('SELECT 1 FROM workspace WHERE key=?',(KEY,)).fetchone()) and not c.execute('SELECT 1 FROM data_migrations WHERE name=?',(VERSION,)).fetchone()

def apply(c,payload=None):
 c.execute('CREATE TABLE IF NOT EXISTS data_migrations(name TEXT PRIMARY KEY)')
 if c.execute('SELECT 1 FROM data_migrations WHERE name=?',(VERSION,)).fetchone():return {'applied':False}
 if payload is None:
  if not PAYLOAD.is_file():return {'applied':False}
  payload=json.loads(PAYLOAD.read_text())
 row=c.execute('SELECT value,revision FROM workspace WHERE key=?',(KEY,)).fetchone()
 if not row:return {'applied':False}
 c.execute('SAVEPOINT company_staff_import')
 try:
  data=json.loads(row[0]);users=data.setdefault('users',[]);entries=payload['users']
  emails=[x['email'].strip().lower() for x in entries]
  if len(emails)!=len(set(emails)):raise ValueError('Roster contains duplicate login emails')
  if not entries:raise ValueError('Roster is empty')
  roles=sorted({x['role'] for x in entries});depts=sorted({x['department'] for x in entries})
  for role in roles:
   data.setdefault('roles',{})[role]=company_role_defaults.grants(role)
   data.setdefault('roleDescriptions',{})[role]=company_role_defaults.responsibility(role)
  # Existing reference names remain valid for historical and unmatched users.
  data['departments']=list(dict.fromkeys(depts+data.get('departments',[])))
  now=datetime.datetime.now(datetime.timezone.utc).isoformat();counts={'applied':True,'updated':0,'created':0,'roles':len(roles),'departments':len(depts)}
  for source in entries:
   mail=source['email'].strip().lower();name=source['name'].strip();role=source['role'];dept=source['department']
   if not name or not dept or '@' not in mail:raise ValueError('Invalid roster identity')
   account=c.execute('SELECT id,user_id FROM accounts WHERE lower(email)=?',(mail,)).fetchone()
   profiles=[u for u in users if str(u.get('email','')).lower()==mail]
   if len(profiles)>1:raise ValueError('Multiple staff profiles use roster email')
   uid=account[1] if account else profiles[0]['id'] if profiles else str(uuid.uuid4())
   if profiles and profiles[0]['id']!=uid:raise ValueError('Account and directory identity disagree')
   profile=next((u for u in users if u['id']==uid),None)
   if profile and not account and str(profile.get('email','')).lower()!=mail:raise ValueError('Existing staff identity has a different email')
   salt=base64.b64decode(source['salt'],validate=True);digest=base64.b64decode(source['passwordHash'],validate=True);iterations=source['iterations']
   if len(salt)!=16 or len(digest)!=32 or not isinstance(iterations,int) or iterations<310000:raise ValueError('Invalid roster password hash')
   if account:
    c.execute('UPDATE accounts SET name=?,email=?,role=?,password_hash=?,salt=?,iterations=?,failed_attempts=0,locked_until=0 WHERE id=?',(name,mail,role,digest,salt,iterations,account[0]))
    c.execute('DELETE FROM sessions WHERE account_id=?',(account[0],));counts['updated']+=1
   else:
    c.execute('INSERT INTO accounts(id,email,name,role,user_id,password_hash,salt,iterations,created_at) VALUES(?,?,?,?,?,?,?,?,?)',(str(uuid.uuid4()),mail,name,role,uid,digest,salt,iterations,now));counts['created']+=1
   if profile is None:profile={'id':uid,'active':True,'managerId':''};users.append(profile)
   profile.update(name=name,email=mail,role=role,department=dept,position=role)
   profile.pop('testData',None)
   # Do not reactivate disabled users or invent reporting assignments.
   c.execute('UPDATE staff_profiles SET version=version+1 WHERE user_id=?',(uid,))
   c.execute('INSERT INTO staff_directory_audit(at,actor,action,user_id) VALUES(?,?,?,?)',(now,'system','company roster import 69',uid))
   for record in data.get('hrprofiles',[]):
    if str(record.get('employee') or record.get('owner'))==uid:record.update(email=mail,position=role)
  c.execute('UPDATE workspace SET value=?,revision=revision+1 WHERE key=?',(json.dumps(data,ensure_ascii=False),KEY))
  import crm_api
  crm_api.bind_users(c)
  c.execute('INSERT INTO data_migrations VALUES(?)',(VERSION,))
  c.execute('RELEASE company_staff_import');return counts
 except Exception:
  c.execute('ROLLBACK TO company_staff_import');c.execute('RELEASE company_staff_import');raise
