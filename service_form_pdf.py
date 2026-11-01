"""Compact Service / Application report with actual saved customer acknowledgement."""
import datetime,html
from pathlib import Path
from document_report import letterhead,CSS,E,qty_fmt,serial_pdf
ROOT=Path(__file__).parent

@serial_pdf
def build(data):
 import fitz
 doc=fitz.open();page=doc.new_page(width=595,height=842);archive=fitz.Archive(str(ROOT/'reference/service-report'));overflow=[];css=CSS+'body{margin:0;padding:0;font-size:8.5pt;line-height:1.25}p{margin:0;padding:0}'
 def markup(text,size=8.5):return '<div style="font-size:'+str(size)+'pt">'+E(text or '').replace('\n','<br>')+'</div>'
 def fits(text,rect,size):
  story=fitz.Story(markup(text,size),user_css=css,archive=archive);more,_=story.place(fitz.Rect(rect));return not more
 def put(rect,text,label='',size=8.5):
  text=str(text or '')
  if not text:text='—'
  for font in [size,8,7.5]:
   if fits(text,rect,font):
    page.insert_htmlbox(rect,markup(text,font),css=css,archive=archive,scale_low=1);return
  overflow.append((label or 'Additional information',text));page.insert_htmlbox(rect,markup('See continuation: '+(label or 'report details'),8),css=css,archive=archive,scale_low=1)
 def band(y,label):
  page.draw_rect(fitz.Rect(32,y,563,y+16),fill=(.92,.95,.97),color=(.78,.85,.9),width=.4);put((39,y+2,557,y+15),label,size=9)
 def narrative(y,height,label,text):
  band(y,label);page.draw_rect(fitz.Rect(32,y+16,563,y+height),color=(.8,.86,.9),width=.4);put((39,y+21,556,y+height-4),text,label)
 put((32,150,440,179),data['title'],size=17);put((443,154,563,176),data.get('status',''),size=9)
 meta=data.get('meta',[])
 for i,(label,value) in enumerate(meta[:10]):
  col=i%2;row=i//2;x=32+col*265.5;y=184+row*24
  page.draw_rect(fitz.Rect(x,y,x+265.5,y+24),color=(.8,.86,.9),width=.35);put((x+6,y+2,x+260,y+23),label+': '+str(value or '—'),label,size=8.3)
 if len(meta)>10:overflow.extend(meta[10:])
 narrative(310,48,data.get('issueLabel','Problem / diagnosis'),data.get('issue'))
 narrative(367,67,data.get('actionLabel','Solution / action taken'),data.get('action'))
 narrative(443,64,'Result / follow-up',data.get('result'))
 band(513,data.get('partsLabel','Parts used'))
 parts=data.get('parts',[])
 if parts:
  text='\n'.join(str(p.get('catalogueNo') or '')+' · '+str(p.get('name') or '')+' · Qty '+qty_fmt(p.get('qty',0)) for p in parts)
 else:text='No parts recorded.' if data.get('partsLabel','Parts used')=='Parts used' else data.get('products') or 'No product recorded.'
 put((39,533,556,571),text,data.get('partsLabel','Parts used'))
 page.draw_rect((32,529,563,576),color=(.8,.86,.9),width=.4)
 band(583,'Customer feedback')
 feedback=data.get('feedback',{});keys=[('feedbackSolved','Issue resolved'),('feedbackSpeed','Speed'),('feedbackPreparedness','Preparedness'),('feedbackCourtesy','Courtesy'),('feedbackSatisfaction','Satisfaction')]
 for i,(key,label) in enumerate(keys):
  x=32+i*106.2;page.draw_rect((x,599,x+106.2,632),color=(.8,.86,.9),width=.35);put((x+5,601,x+101,614),label,size=7.5);put((x+5,616,x+101,630),feedback.get(key) or 'Not rated',size=8)
 put((39,639,556,681),'Comments: '+str(feedback.get('feedbackComment') or '—'),'Customer comments')
 page.draw_rect((32,632,563,686),color=(.8,.86,.9),width=.4)
 page.draw_rect((32,690,292,790),color=(.7,.8,.86),width=.5);page.draw_rect((303,690,563,790),color=(.7,.8,.86),width=.5)
 put((40,701,284,716),data.get('personLabel','Service engineer')+' - printed name',size=8)
 put((40,724,284,748),data.get('person') or 'Not assigned','Engineer / specialist name',size=10)
 put((40,760,284,783),'Date: '+str(data.get('date') or '—'),size=8)
 put((311,695,555,708),'Customer acknowledgement',size=8)
 sig=data.get('signature')
 if sig:
  for stroke in sig.get('strokes',[]):
   if len(stroke)>1:page.draw_polyline([fitz.Point(343+float(x)*180,710+float(y)*54) for x,y in stroke],color=(.07,.2,.28),width=.85)
  stamp=sig.get('signedAt','')
  try:stamp=datetime.datetime.fromisoformat(stamp).astimezone(datetime.timezone(datetime.timedelta(hours=7))).strftime('%d/%m/%Y %H:%M')
  except (ValueError,TypeError):pass
  put((311,766,555,778),sig.get('name') or data.get('customerSignatory'),size=8)
  put((311,779,555,789),'Signed: '+stamp,size=7.5)
 else:
  put((311,729,555,754),'Customer signature not provided',size=8)
  if data.get('customerSignatory'):put((311,763,555,783),data['customerSignatory'],size=8)
 if overflow:
  # Keep the primary form readable; preserve all oversized content in labelled continuation pages.
  markup_overflow='<h2>'+E(data['title'])+' - continuation</h2>'+''.join('<h3>'+E(label)+'</h3><p>'+E(text).replace('\n','<br>')+'</p>' for label,text in overflow)
  import io
  buffer=io.BytesIO();writer=fitz.DocumentWriter(buffer);story=fitz.Story(markup_overflow,user_css=css,archive=archive)
  for index in range(500):
   device=writer.begin_page(fitz.Rect(0,0,595,842));more,_=story.place(fitz.Rect(32,152,563,792));story.draw(device);writer.end_page()
   if not more:break
  else:raise ValueError('Report content exceeds page limit')
  writer.close();extra=fitz.open(stream=buffer.getvalue(),filetype='pdf');doc.insert_pdf(extra)
 for i,p in enumerate(doc,1):letterhead(p,data['title'],data.get('reference',''),i,len(doc),data.get('status',''))
 doc.subset_fonts()
 return doc.tobytes(garbage=4,deflate=True)

def service_data(job,instrument,customer,engineer,parts):
 extras=' · '.join(str(v) for v in [job.get('areaCode'),job.get('department'),job.get('instrumentWarranty'),job.get('instrumentOwnership')] if v)
 meta=[('Job No.',job.get('jobNo')),('Service date',job.get('date')),('Customer / institution',customer.get('name') or job.get('customer') or instrument.get('customer')),('Site / location',job.get('location') or instrument.get('location')),('Instrument',' / '.join(str(v) for v in [instrument.get('brand'),instrument.get('model')] if v) or '—'),('Serial number',instrument.get('serial')),('Service engineer',engineer),('Job type',job.get('jobType')),('Department / instrument status',extras),('Schedule / period',' · '.join(str(v) for v in [job.get('scheduledDate'),job.get('startDate'),job.get('endDate')] if v))]
 result='\n'.join(str(v) for v in [job.get('result'),job.get('comment')] if v)
 return dict(title='Service Report',reference=job.get('jobNo') or job.get('id'),status=job.get('status'),date=job.get('date'),meta=meta,issue='\n'.join(str(v) for v in [job.get('description'),('Diagnosis: '+job['diagnosis']) if job.get('diagnosis') and job.get('diagnosis')!=job.get('description') else ''] if v),action=job.get('actionTaken'),result=result,parts=parts,feedback=job,person=engineer,personLabel='Service engineer',signature=job.get('customerSignature'),customerSignatory=job.get('customerSignatory'))

def service(job,instrument,customer,engineer,parts):return build(service_data(job,instrument,customer,engineer,parts))

def application_data(job,instrument,specialist):
 meta=[('Application job',job.get('reference')),('Start date / time',job.get('start')),('Customer / institution',job.get('customer')),('Topic',job.get('topic')),('Contact person',job.get('contact')),('End date / time',job.get('end')),('Instrument',' / '.join(str(v) for v in [instrument.get('brand'),instrument.get('model')] if v) or '—'),('Serial number',instrument.get('serial')),('Application specialist',specialist),('Service type',job.get('serviceType'))]
 result='\n'.join(str(v) for v in [job.get('result'),('Follow-up: '+job['followUp']) if job.get('followUp') else '',('Due: '+job['followUpDate']) if job.get('followUpDate') else ''] if v)
 return dict(title='Application Report',reference=job.get('reference'),status=job.get('status'),date=str(job.get('start',''))[:10],meta=meta,issueLabel='Purpose / application requirement',issue=job.get('purpose'),actionLabel='Application work performed',action=job.get('workPerformed'),result=result,parts=[],partsLabel='Product / application scope',products=', '.join(job.get('products',[])) or job.get('productLine'),feedback=job,person=specialist,personLabel='Application specialist',signature=job.get('customerSignature'),customerSignatory=job.get('customerSignatory'))

def application(job,instrument,specialist):return build(application_data(job,instrument,specialist))
