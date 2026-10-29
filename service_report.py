"""FM-FSE-01 PDF generation using the supplied original form as the page background."""
import io,json,html,re,hashlib,datetime,sqlite3
from pathlib import Path
from urllib.parse import parse_qs,urlsplit,quote
import permissions_policy as policy
ROOT=Path(__file__).parent/'reference'/'service-report'
def initialize(c):c.execute('CREATE TABLE IF NOT EXISTS service_reports(id INTEGER PRIMARY KEY,job_id TEXT NOT NULL,input_hash TEXT NOT NULL,pdf BLOB NOT NULL,created_at TEXT NOT NULL,actor TEXT NOT NULL,UNIQUE(job_id,input_hash))')
def build(job,instrument,customer,engineer,parts):
 import fitz
 doc=fitz.open(ROOT/'FM-FSE-01.pdf');page=doc[0];
 for label in ['Area Code','Department','Start Date:','End Date:']:
  for rect in page.search_for(label):page.add_redact_annot(rect,fill=(1,1,1))
 page.add_redact_annot(fitz.Rect(30,164,246,299),fill=(1,1,1));page.apply_redactions(images=0,graphics=0)
 page.draw_rect((404,124,567,164),color=(.4,.4,.4),fill=(1,1,1),width=.4);page.draw_line((404,144),(567,144),color=(.4,.4,.4),width=.4);page.draw_rect((185,84,246,104),color=(.4,.4,.4),fill=(.85,.85,.85),width=.4);page.draw_rect((185,144,246,164),color=(.4,.4,.4),fill=(.85,.85,.85),width=.4);page.insert_text((190,97),'Service Date',fontsize=8,fontname='hebo');page.insert_text((190,157),'Engineer',fontsize=8,fontname='hebo');base_template=doc.tobytes()
 width,height=page.rect.width,page.rect.height;archive=fitz.Archive(str(ROOT));overflow=[]
 css="@font-face{font-family:Sarabun;src:url(Sarabun-Regular.ttf)}body{margin:0;padding:0}*{font-family:Sarabun;font-size:9pt;line-height:1.1;margin:0;padding:0}"
 def markup(text,size=9,spacing=None):return '<div style="font-size:'+str(size)+'pt'+(';line-height:'+str(spacing)+'pt' if spacing else '')+'">'+html.escape(str(text)).replace('\n','<br>')+'</div>'
 def fits(text,rect,size,spacing=None):
  story=fitz.Story(markup(text,size,spacing),user_css=css,archive=archive);more,_=story.place(fitz.Rect(rect));return not more
 def put(rect,label,text,size=9,target=None):
  text=str(text or '');target=target or page;spacing=19.4 if label in ['Problem/Error Code','Solution/Action','Customer feedback'] else None
  if not text:return
  if fits(text,rect,size,spacing):target.insert_htmlbox(fitz.Rect(rect),markup(text,size,spacing),css=css,archive=archive);return
  lo,hi=0,len(text)
  while lo<hi:
   mid=(lo+hi+1)//2
   if fits(text[:mid]+' …',rect,size,spacing):lo=mid
   else:hi=mid-1
  if 0<lo<len(text) and ' ' in text[:lo]:lo=text.rfind(' ',0,lo)+1
  if lo:target.insert_htmlbox(fitz.Rect(rect),markup(text[:lo]+' …',size,spacing),css=css,archive=archive)
  overflow.append((label,text[lo:]))
 def check(x,y):page.draw_line((x+1,y+6),(x+4,y+9),width=1);page.draw_line((x+4,y+9),(x+10,y+1),width=1)
 customer_name=customer.get('name') or job.get('customer') or instrument.get('customer') or ''
 for rect,label,value in [((87,85,182,102),'Job No.',job.get('jobNo')),((249,85,345,102),'Service Date',job.get('date')),((87,105,182,122),'Instrument',instrument.get('brand')),((249,105,345,122),'Customer',customer_name),((87,125,182,142),'Model',instrument.get('model')),((249,125,345,142),'Site',job.get('location') or instrument.get('location')),((87,145,182,162),'S/N',instrument.get('serial')),((249,145,345,162),'Engineer',engineer),((449,126,563,141),'Start Date',''),((449,146,563,161),'End Date','')]:put(rect,label,value,6 if label=='Engineer' else 8)
 if job.get('status')=='Completed':check(410,89)
 elif job.get('status')=='To Follow-up':check(410,109)
 put((36,170,238,191),'Acknowledgement heading','Customer acknowledgement',10)
 put((36,203,238,285),'Acknowledgement note','Customer signature and service feedback are recorded below when provided.',9)
 jobtypes=[['Sales Support','Inspection'],['Installation','Relocation'],['Uninstallation','Training'],['Calibration','Maintenance'],['Preventive Maintenance','Repair'],['Update / Upgrade','Others']]
 for index,pair in enumerate(jobtypes):
  for col,value in enumerate(pair):
   if job.get('jobType')==value:check(257+153*col,188+19.4*index)
 put((33,321,563,357),'Problem/Error Code',job.get('diagnosis') or job.get('description'))
 solution=job.get('actionTaken') or job.get('description') or ''
 if job.get('result'):solution+='\nResult: '+job['result']
 put((33,380,563,454),'Solution/Action',solution)
 for index,p in enumerate(parts[:4]):
  y=478+19.4*index
  put((33,y,181,y+17),'Part catalogue',p.get('catalogueNo'),8);put((188,y,516,y+17),'Part description',p.get('name'),8);put((523,y,563,y+17),'Part quantity',p.get('qty'),8)
 if len(parts)>4:overflow.append(('Additional parts','\n'.join(str(p.get('catalogueNo') or '')+' | '+str(p.get('name') or '')+' | Qty '+str(p.get('qty') or '') for p in parts[4:])))
 if job.get('feedbackSolved') in ['Yes','No']:check(170 if job['feedbackSolved']=='Yes' else 283,577)
 for index,key in enumerate(['feedbackSpeed','feedbackPreparedness','feedbackCourtesy','feedbackSatisfaction']):
  if job.get(key) in ['Excellent','Fair','Needs improvement']:check([170,283,436][['Excellent','Fair','Needs improvement'].index(job[key])],594+16.7*index)
 put((33,679,563,715),'Customer feedback',job.get('feedbackComment'),9)
 # Printed engineer identification and service date; no handwritten signature is fabricated.
 put((140,719,272,735),'Engineer name',engineer,8);put((140,739,272,754),'Engineer date',job.get('date'),8);put((429,719,563,735),'Customer name',job.get('customerSignatory') if not job.get('customerSignature') else '',8)
 sig=job.get('customerSignature')
 if sig:
  for stroke in sig['strokes']:
   points=[fitz.Point(430+x*130,716+y*17) for x,y in stroke];page.draw_polyline(points,color=(.07,.20,.28),width=.8)
  stamp=datetime.datetime.fromisoformat(sig['signedAt']).astimezone(datetime.timezone(datetime.timedelta(hours=7))).strftime('%d-%m-%Y %H:%M')
  put((429,736,563,745),'Customer printed name',sig['name'],6)
  put((429,746,563,755),'Customer signed date',stamp,6)
 while overflow:
  label,text=overflow.pop(0);new=doc.new_page(width=width,height=height);template=fitz.open(stream=base_template,filetype='pdf');new.show_pdf_page(new.rect,template,0);template.close();new.draw_rect((28,164,568,716),color=None,fill=(1,1,1));new.draw_rect((28,164,568,716),width=.6)
  new.insert_htmlbox((35,170,560,195),markup('Continuation - '+str(job.get('jobNo',''))+' - '+label,11),css=css,archive=archive)
  put((36,202,560,707),label,text,9,new)
 # The original company header, logo, form identifier, revision and effective-date footer are retained.
 for n,p in enumerate(doc):
  p.draw_rect((265,779,331,799),color=None,fill=(1,1,1));p.insert_text((280,792),'page '+str(n+1)+'/'+str(len(doc)),fontname='tiro',fontsize=8)
 return doc.tobytes(garbage=4,deflate=True)
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
   source=json.dumps(['report-v28',job,inst,customer,engineer,parts],sort_keys=True,ensure_ascii=False);digest=hashlib.sha256(source.encode()).hexdigest();cached=c.execute('SELECT pdf FROM service_reports WHERE job_id=? AND input_hash=?',(job['id'],digest)).fetchone()
   if cached:pdf=cached[0]
   else:
    pdf=build(job,inst,customer,engineer,parts);c.execute('INSERT OR IGNORE INTO service_reports(job_id,input_hash,pdf,created_at,actor) VALUES(?,?,?,?,?)',(job['id'],digest,pdf,datetime.datetime.now(datetime.timezone.utc).isoformat(),str(actor[4])))
  name=re.sub(r'[^\w.-]+','-',job.get('jobNo') or job['id'])+'.pdf';h.send_response(200);h.send_header('Content-Type','application/pdf');h.send_header('Content-Length',str(len(pdf)));h.send_header('Content-Disposition',('inline' if q.get('view') else 'attachment')+"; filename*=UTF-8''"+quote(name));h.send_header('Cache-Control','no-store');h.send_header('X-Content-Type-Options','nosniff');h.end_headers();h.wfile.write(pdf)
 except policy.PermissionDenied as e:return h.reply(403,{'error':str(e)})
 except (ValueError,TypeError,KeyError,sqlite3.IntegrityError) as e:return h.reply(400,{'error':str(e)})
