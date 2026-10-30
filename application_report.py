"""Scoped PDF application reports using the shared one-page report layout."""
import json,re
from urllib.parse import parse_qs,urlsplit,quote
import permissions_policy as policy
import application_service as app
from service_form_pdf import application

def handle(h,connect,session,permissions):
 actor=session(h)
 if not actor:return h.reply(401,{'error':'Sign in required'})
 try:
  perms=permissions(actor);policy.need(perms,'application_service.view');policy.need(perms,'application_service.print');q=parse_qs(urlsplit(h.path).query)
  with connect() as c:
   row=c.execute('SELECT payload FROM application_service_records WHERE id=? AND deleted=0',(q.get('id',[''])[0],)).fetchone()
   if not row:raise ValueError('Application job unavailable')
   job=json.loads(row[0])
   if not app.visible(job,actor,perms):raise policy.PermissionDenied('Application job unavailable')
   row=c.execute("SELECT payload FROM fse_records WHERE id=? AND kind='instruments'",(job.get('instrumentId',''),)).fetchone();instrument=json.loads(row[0]) if row else {};specialist=job.get('specialistName')
   if not specialist:
    person=c.execute('SELECT name FROM accounts WHERE user_id=?',(job.get('specialist'),)).fetchone();specialist=person[0] if person else job.get('specialist','')
   format=q.get('format',['pdf'])[0]
   if format not in ['pdf','html']:raise ValueError('Choose PDF or HTML')
   if format=='html':
    from report_html import service as html_report
    from service_form_pdf import application_data
    pdf=html_report(application_data(job,instrument,specialist)).encode('utf-8')
   else:pdf=application(job,instrument,specialist)
  filename=re.sub(r'[^\w.-]+','-',job.get('reference') or job['id'])[:100]+('.html' if format=='html' else '.pdf');h.send_response(200);h.send_header('Content-Type','text/html; charset=utf-8' if format=='html' else 'application/pdf');h.send_header('Content-Length',str(len(pdf)));h.send_header('Content-Disposition',('inline' if q.get('view') else 'attachment')+"; filename*=UTF-8''"+quote(filename));h.send_header('Cache-Control','no-store');h.send_header('X-Content-Type-Options','nosniff');h.end_headers();h.wfile.write(pdf)
 except policy.PermissionDenied as e:return h.reply(403,{'error':str(e)})
 except (ValueError,KeyError,TypeError) as e:return h.reply(400,{'error':str(e)})
