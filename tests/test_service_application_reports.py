import sys,json,unittest,io,unicodedata
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import fitz,service_form_pdf as form,report_html,service_report,application_report,serve,test_crm as fixture
class Forms(unittest.TestCase):
 def service(self):
  return dict(id='s',jobNo='BMDS30-10-26/1',date='2026-10-30',status='Completed',description='Instrument startup warning.',diagnosis='Checked sensor connection.',actionTaken='Replaced the sensor and completed calibration. Ran QC together with the operator.',result='QC passed.',comment='Follow-up next week.',jobType='Repair',location='Laboratory',feedbackSolved='Yes',feedbackSpeed='Excellent',feedbackPreparedness='Excellent',feedbackCourtesy='Excellent',feedbackSatisfaction='Excellent',feedbackComment='Service completed as expected.',customerSignature=self.signature())
 def application(self):
  return dict(id='a',reference='BMDAS30-10-26/1',start='2026-10-30T09:00',end='2026-10-30T12:00',customer='Example Hospital',contact='Laboratory supervisor',topic='Operator training',serviceType='Application training',status='Completed',purpose='Support method validation and train operators.',workPerformed='Reviewed sample preparation, QC and analysis settings with the operator.',result='Validation completed.',followUp='Review the first week of results.',followUpDate='2026-11-06',products=['Diagnostics'],customerSignature=self.signature(),feedbackSolved='Yes')
 def signature(self):return {'name':'Customer Representative','signedAt':'2026-10-30T03:00:00+00:00','strokes':[[[.1,.8],[.25,.2],[.4,.65],[.6,.4],[.9,.7]]]}
 def test_one_page_normal_records_actual_names_and_signature(self):
  for data in [form.service_data(self.service(),{'brand':'Brand','model':'Model','serial':'SN-1'},{'name':'Example Hospital'},'Engineer Example',[]),form.application_data(self.application(),{'brand':'Brand','model':'Model','serial':'SN-1'},'Specialist Example')]:
   with self.subTest(title=data['title']):
    pdf=form.build(data);doc=fitz.open(stream=pdf,filetype='pdf');self.assertEqual(len(doc),1);text=unicodedata.normalize('NFKC',doc[0].get_text());self.assertIn(data['person'],text);self.assertIn('Customer Representative',text);self.assertIn('Signed:',text);self.assertIn(data['reference'],text);self.assertGreater(len(doc[0].get_drawings()),20)
 def test_long_content_not_silently_truncated(self):
  data=form.service_data(self.service(),{}, {},'Engineer',[]);data['action']='Work performed and reviewed with operator. '*200;doc=fitz.open(stream=form.build(data),filetype='pdf');self.assertGreater(len(doc),1);self.assertIn('continuation',''.join(p.get_text() for p in doc));self.assertIn('operator.',''.join(p.get_text() for p in doc))
 def test_self_contained_html_and_escaping(self):
  data=form.application_data(self.application(),{},'Specialist');data['issue']='<script>alert(1)</script>';source=report_html.service(data);self.assertIn('data:image/png;base64,',source);self.assertIn('data:font/ttf;base64,',source);self.assertIn('Customer Representative',source);self.assertIn('polyline',source);self.assertIn('&lt;script&gt;',source);self.assertNotIn('<script>alert(1)</script>',source);self.assertIn('Print report',source)
class Endpoints(unittest.TestCase):
 setUp=fixture.CRM.setUp
 tearDown=fixture.CRM.tearDown
 def handler(self,path):
  class H:
   def __init__(self):self.path=path;self.wfile=io.BytesIO();self.headers={};self.status=None
   def reply(self,status,body):self.status=status;return status,body
   def send_response(self,status):self.status=status
   def send_header(self,k,v):self.headers[k]=v
   def end_headers(self):pass
  return H()
 def test_application_scoped_pdf_html_and_permission(self):
  job=Forms().application();job.update(createdBy='u2',specialist='u2',specialistName='Specialist Example')
  with serve.connect() as c:c.execute('INSERT INTO application_service_records VALUES(?,?,1,0)',('a',json.dumps(job)))
  perms=self.perms-{'application_service.view_all'}
  h=self.handler('/api/application-report?id=a');self.assertEqual(application_report.handle(h,serve.connect,lambda _:self.actor,lambda _:perms)[0],403)
  self.assertEqual(application_report.handle(h,serve.connect,lambda _:None,lambda _:perms)[0],401)
  other=('acct2','two@example.invalid','Second','Employee','u2')
  for format,mime in [('pdf','application/pdf'),('html','text/html; charset=utf-8')]:
   h=self.handler('/api/application-report?id=a&format='+format);application_report.handle(h,serve.connect,lambda _:other,lambda _:perms);self.assertEqual(h.status,200);self.assertEqual(h.headers['Content-Type'],mime);self.assertGreater(len(h.wfile.getvalue()),1000)
  h=self.handler('/api/application-report?id=a');self.assertEqual(application_report.handle(h,serve.connect,lambda _:other,lambda _:perms-{'application_service.print'})[0],403)
 def test_service_html_and_pdf(self):
  job=Forms().service();job.update(kind='jobs',engineer='u1',engineerName='Engineer Example',instrumentId='report-inst',customerId='c1')
  with serve.connect() as c:
   c.execute('INSERT INTO fse_records VALUES(?,?,?,1)',('service-print','jobs',json.dumps(job)));c.execute('INSERT INTO fse_records VALUES(?,?,?,1)',('report-inst','instruments',json.dumps({'id':'report-inst','kind':'instruments','brand':'Brand','model':'Model','serial':'SN-1'})))
  for format,mime in [('pdf','application/pdf'),('html','text/html; charset=utf-8')]:
   h=self.handler('/api/service-report?id=service-print&format='+format);service_report.handle(h,serve.connect,lambda _:self.actor,lambda _:self.perms);self.assertEqual(h.status,200);self.assertEqual(h.headers['Content-Type'],mime);self.assertGreater(len(h.wfile.getvalue()),1000)
if __name__=='__main__':unittest.main()
