"""Service job PDF / HTML report with saved customer acknowledgement."""
import io,json,html,re,hashlib,datetime,sqlite3
from pathlib import Path
from urllib.parse import parse_qs,urlsplit,quote
import permissions_policy as policy
ROOT=Path(__file__).parent/'reference'/'service-report'
def initialize(c):c.execute('CREATE TABLE IF NOT EXISTS service_reports(id INTEGER PRIMARY KEY,job_id TEXT NOT NULL,input_hash TEXT NOT NULL,pdf BLOB NOT NULL,created_at TEXT NOT NULL,actor TEXT NOT NULL,UNIQUE(job_id,input_hash))')
def build(job,instrument,customer,engineer,parts):
 from service_form_pdf import service
 return service(job,instrument,customer,engineer,parts)
def handle(h,connect,session,permissions):
 actor=session(h)
 if not actor:return h.reply(401,{'error':'Sign in through Staff Portal'})
 try:
  perms=permissions(actor);policy.need(perms,'service.view');policy.need(perms,'service.jobs.view');policy.need(perms,'service.jobs.print');q={k:v[0] for k,v in parse_qs(urlsplit(h.path).query).items()}
  with connect() as c:
   row=c.execute("SELECT payload,version FROM fse_records WHERE id=? AND kind='jobs'",(q.get('id'),)).fetchone()
   if not row:raise ValueError('Service job not found')
   job=dict(json.loads(row[0]),version=row[1]);i=c.execute("SELECT payload FROM fse_records WHERE id=? AND kind='instruments'",(job.get('instrumentId'),)).fetchone();inst=json.loads(i[0]) if i else {};cu=c.execute("SELECT payload FROM masters WHERE category='customers' AND id=?",(job.get('customerId') or inst.get('customerId'),)).fetchone();customer=json.loads(cu[0]) if cu else {}
   import service_catalog,service_referrals
   engineer=next((x['name'] for x in service_catalog.engineers(c) if x['id']==job.get('engineer')),job.get('engineerName') or job.get('engineer') or '');parts=service_referrals.job_parts(c,job)
   if job.get('customerSignature'):
    sig=job['customerSignature'];parts=sig.get('partsSnapshot',parts);inst=sig.get('instrumentSnapshot',inst);customer=sig.get('customerSnapshot',customer);engineer=sig.get('engineerName') or engineer
   is_html=q.get('format','pdf')=='html'
   if q.get('format','pdf') not in ['pdf','html']:raise ValueError('Choose PDF or HTML')
   if is_html:
    from report_html import service as html_report
    from service_form_pdf import service_data
    pdf=html_report(service_data(job,inst,customer,engineer,parts)).encode('utf-8')
   else:
    source=json.dumps(['report-v61-one-page',job,inst,customer,engineer,parts],sort_keys=True,ensure_ascii=False);digest=hashlib.sha256(source.encode()).hexdigest();cached=c.execute('SELECT pdf FROM service_reports WHERE job_id=? AND input_hash=?',(job['id'],digest)).fetchone()
    if cached:pdf=cached[0]
    else:
     pdf=build(job,inst,customer,engineer,parts);c.execute('INSERT OR IGNORE INTO service_reports(job_id,input_hash,pdf,created_at,actor) VALUES(?,?,?,?,?)',(job['id'],digest,pdf,datetime.datetime.now(datetime.timezone.utc).isoformat(),str(actor[4])))
  extension='.html' if is_html else '.pdf';name=re.sub(r'[^\w.-]+','-',job.get('jobNo') or job['id'])+extension;h.send_response(200);h.send_header('Content-Type','text/html; charset=utf-8' if is_html else 'application/pdf');h.send_header('Content-Length',str(len(pdf)));h.send_header('Content-Disposition',('inline' if q.get('view') else 'attachment')+"; filename*=UTF-8''"+quote(name));h.send_header('Cache-Control','no-store');h.send_header('X-Content-Type-Options','nosniff');h.end_headers();h.wfile.write(pdf)
 except policy.PermissionDenied as e:return h.reply(403,{'error':str(e)})
 except (ValueError,TypeError,KeyError,sqlite3.IntegrityError) as e:return h.reply(400,{'error':str(e)})
