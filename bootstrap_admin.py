"""Interactive creation only; never overwrites an existing user."""
import os,getpass,json,uuid
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(os.environ.get('BIOMED_ENV_FILE',str(Path(__file__).parent/'.env')),override=False)
import serve,permissions_policy as policy
if __name__=='__main__':
 serve.prepare_database();email=input('New administrator company email: ').strip().lower();name=input('Full name: ').strip();pw=getpass.getpass('Password (at least 12 characters): ');confirm=getpass.getpass('Confirm password: ')
 if not name or '@' not in email or len(pw)<12 or pw!=confirm:raise SystemExit('Check name, email, password length and confirmation.')
 with serve.connect() as c:
  if c.execute('SELECT 1 FROM accounts WHERE email=?',(email,)).fetchone():raise SystemExit('Account already exists. Nothing changed.')
  ident=str(uuid.uuid4());salt,digest,it=serve.password_record(pw)
  import datetime
  c.execute('INSERT INTO accounts VALUES(?,?,?,?,?,?,?,?,0,0,0,?)',(ident,email,name,'System Admin',ident,digest,salt,it,datetime.datetime.now(datetime.timezone.utc).isoformat()))
  row=c.execute("SELECT value,revision FROM workspace WHERE key='biomed_portal_v33_clean'").fetchone();data=json.loads(row[0]) if row else {};data.setdefault('roles',{})['System Admin']=[p['key'] for p in policy.CATALOG['permissions']];data.setdefault('users',[]).append({'id':ident,'name':name,'email':email,'role':'System Admin','active':True});policy.migrate_portal(data);c.execute('INSERT OR REPLACE INTO workspace VALUES(?,?,?)',('biomed_portal_v33_clean',json.dumps(data,ensure_ascii=False),row[1]+1 if row else 1))
 print('Administrator created. Sign in through the configured HTTPS address.')
