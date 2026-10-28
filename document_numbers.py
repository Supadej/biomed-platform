"""Daily document references, allocated under the workspace write transaction."""
import datetime,re
PREFIXES={'quotation':('BMDQ',2),'customer-order':('CORD',2),'sales-order':('SORD',2),'withdrawal':('W',2),'borrowing':('B',2),'return-product':('RT',2),'purchase-request':('PR',2),'purchase-order':('PO',2),'delivery-in':('DI',2),'delivery-out':('DO',2),'invoice':('IV',2),'credit-note':('CN',2),'debit-note':('CN',2)}
def initialize(c):
 c.execute('CREATE TABLE IF NOT EXISTS document_number_reservations(namespace TEXT,owner TEXT,reference TEXT UNIQUE,PRIMARY KEY(namespace,owner))')

def bangkok_day():return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).date()
def allocate(c,namespace,owner,prefix,day=None,year_digits=4):
 initialize(c)
 found=c.execute('SELECT reference FROM document_number_reservations WHERE namespace=? AND owner=?',(namespace,owner)).fetchone()
 if found:return found[0]
 day=day or bangkok_day();stem=prefix+day.strftime('%d-%m-'+('%y' if year_digits==2 else '%Y'))+'/'
 used={r[0] for r in c.execute('SELECT reference FROM document_number_reservations')}
 tables={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
 if 'documents' in tables:used.update(r[0] for r in c.execute('SELECT reference FROM documents'))
 if 'service_job_numbers' in tables:used.update(r[0] for r in c.execute('SELECT number FROM service_job_numbers'))
 n=1
 while stem+str(n) in used:n+=1
 reference=stem+str(n);c.execute('INSERT INTO document_number_reservations VALUES(?,?,?)',(namespace,owner,reference));return reference
def assign(c,data,previous,preserve_references=False):
 initialize(c)
 if preserve_references:
  for doc in previous.get('documents',[])+data.get('documents',[]):
   if doc.get('ref'):c.execute('INSERT OR IGNORE INTO document_number_reservations VALUES(?,?,?)',('is',doc['id'],doc['ref']))
  return
 old={d['id']:d for d in previous.get('documents',[])}
 renamed={}
 for d in reversed(data.get('documents',[])):
  prior=old.get(d['id'])
  if prior:
   if prior.get('ref')!=d.get('ref'):raise ValueError('Existing document reference cannot be changed')
  elif d.get('kind') in PREFIXES:
   prefix,digits=PREFIXES[d['kind']];before=d.get('ref');d['ref']=allocate(c,'is',d['id'],prefix,year_digits=digits)
   if before and before!=d['ref']:renamed[before]=d['ref']
 for entry in data.get('audit',[]):
  if entry.get('reference') in renamed:entry['reference']=renamed[entry['reference']]
 # Do not reuse old references, even after deletion.
 for d in previous.get('documents',[]):
  if d.get('ref'):c.execute('INSERT OR IGNORE INTO document_number_reservations VALUES(?,?,?)',('is',d['id'],d['ref']))
