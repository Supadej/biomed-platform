"""One authoritative number reservation across service jobs and Helpdesk tickets."""
import datetime,json

def initialize(c):c.execute('CREATE TABLE IF NOT EXISTS service_job_numbers(number TEXT PRIMARY KEY,owner TEXT NOT NULL UNIQUE)')
def reserve(c,owner,requested='',repair=False):
 initialize(c);number=str(requested or '').strip().upper()
 old_owner=c.execute('SELECT number FROM service_job_numbers WHERE owner=?',(owner,)).fetchone()
 if not number and old_owner:return old_owner[0]
 if not number:
  import document_numbers
  number=document_numbers.allocate(c,'service',owner,'BMDS',year_digits=2)
 base=number;i=2
 while True:
  found=c.execute('SELECT owner FROM service_job_numbers WHERE number=?',(number,)).fetchone()
  if not found or found[0]==owner:break
  if not repair:raise ValueError('Job number already exists. Enter a unique number or leave blank for automatic numbering.')
  number=base+'-'+str(i).zfill(2);i+=1
 # Keep retired numbers reserved to prevent historical number reuse.
 old=c.execute('SELECT number FROM service_job_numbers WHERE owner=?',(owner,)).fetchone()
 if old and old[0]!=number:c.execute('UPDATE service_job_numbers SET owner=? WHERE owner=?',('retired:'+owner+':'+old[0],owner))
 c.execute('INSERT OR IGNORE INTO service_job_numbers VALUES(?,?)',(number,owner));return number

def migrate(c):
 initialize(c);c.execute('CREATE TABLE IF NOT EXISTS job_number_migrations(name TEXT PRIMARY KEY,detail TEXT)')
 if c.execute("SELECT 1 FROM job_number_migrations WHERE name='unique-v1'").fetchone():return
 changes=[];mapping=[]
 for ident,payload in c.execute("SELECT id,payload FROM fse_records WHERE kind='jobs' ORDER BY id").fetchall():
  r=json.loads(payload);old=r.get('jobNo','');new=reserve(c,'service:'+ident,old,True)
  if old!=new:
   r['legacyJobNo']=old;r['jobNo']=new;c.execute('UPDATE fse_records SET payload=?,version=version+1 WHERE id=?',(json.dumps(r,ensure_ascii=False),ident));changes.append({'kind':'service','id':ident,'old':old,'new':new})
  mapping.append((r.get('instrumentId'),old,r.get('date'),r.get('partChangeRef'),new,ident))
 for ident,payload in c.execute("SELECT id,payload FROM fse_records WHERE kind='replacements'").fetchall():
  r=json.loads(payload);matches=[x for x in mapping if x[0]==r.get('instrumentId') and x[1]==r.get('jobNo')]
  exact=[x for x in matches if x[2]==r.get('date') or x[3] and x[3]==r.get('changeNo')]
  if len(exact)==1:matches=exact
  if len(matches)==1:
   x=matches[0];r['legacyJobNo']=r.get('jobNo');r['jobNo']=x[4];r['serviceJobId']=x[5]
  elif matches:r['reviewRequired']=True;r['comment']=(r.get('comment','')+' Job number had multiple historical visits; verify the original reference.').strip()
  c.execute('UPDATE fse_records SET payload=?,version=version+1 WHERE id=?',(json.dumps(r,ensure_ascii=False),ident))
 for ident,payload in c.execute("SELECT id,payload FROM crm_records WHERE entity='HelpDeskTickets' ORDER BY id").fetchall():
  r=json.loads(payload);old=r.get('JobNumber','');new=reserve(c,'helpdesk:'+str(ident),old,True)
  if old!=new:
   r['LegacyJobNumber']=old;r['JobNumber']=new;c.execute("UPDATE crm_records SET payload=?,version=version+1 WHERE entity='HelpDeskTickets' AND id=?",(json.dumps(r,ensure_ascii=False),ident));changes.append({'kind':'helpdesk','id':ident,'old':old,'new':new})
 c.execute("INSERT INTO job_number_migrations VALUES('unique-v1',?)",(json.dumps(changes,ensure_ascii=False),))
 return changes
