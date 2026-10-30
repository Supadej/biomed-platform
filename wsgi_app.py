"""Production WSGI transport around the existing request handlers."""
import io,os,threading
from email.message import Message
import serve
class Request(serve.Handler):
 def __init__(self,e):
  self.command=e['REQUEST_METHOD'];self.path=e.get('PATH_INFO','/')+('?' + e['QUERY_STRING'] if e.get('QUERY_STRING') else '');self.headers=Message()
  for k,v in e.items():
   if k.startswith('HTTP_'):self.headers[k[5:].replace('_','-')]=str(v)
  for k,n in [('CONTENT_TYPE','Content-Type'),('CONTENT_LENGTH','Content-Length')]:
   if e.get(k):self.headers[n]=str(e[k])
  self.rfile=e['wsgi.input'];self.wfile=io.BytesIO();self.directory=str(serve.ROOT);self.client_address=(e.get('REMOTE_ADDR','127.0.0.1'),0);self.request_version='HTTP/1.1';self.requestline=self.command+' '+self.path+' HTTP/1.1';self.close_connection=True;self.status=200;self.output_headers=[]
 def send_response(self,code,message=None):self.status=code
 def send_header(self,k,v):self.output_headers.append((str(k),str(v)))
 def end_headers(self):
  if not any(k.lower()=='cache-control' for k,v in self.output_headers):self.send_header('Cache-Control','no-store')
 def log_request(self,*args):pass
 def log_error(self,fmt,*args):print('HTTP error: '+fmt%args,flush=True)
def application(e,start_response):
 r=Request(e)
 try:
  if r.command=='GET':r.do_GET()
  elif r.command=='HEAD':r.do_HEAD()
  elif r.command=='POST':r.do_POST()
  elif r.command=='PUT':r.do_PUT()
  elif r.command=='DELETE':r.do_DELETE()
  else:r.send_error(405,'Method not allowed')
 except Exception:
  import traceback
  traceback.print_exc();r.status=500;r.output_headers=[('Content-Type','application/json'),('Cache-Control','no-store')];r.wfile=io.BytesIO(b'{"error":"Server error. Contact the administrator with time and record reference."}')
 body=r.wfile.getvalue()
 if not any(k.lower()=='content-length' for k,v in r.output_headers):r.output_headers.append(('Content-Length',str(len(body))))
 start_response(str(r.status)+' '+r.responses.get(r.status,('Response',))[0],r.output_headers);return [b'' if r.command=='HEAD' else body]
_started=False
def create_app():
 global _started
 if not _started:
  serve.prepare_database()
  if os.environ.get('BIOMED_ENABLE_OUTLOOK_WORKER','1')=='1':threading.Thread(target=serve.outlook_sync.worker,args=(serve.connect,serve.account_permissions,threading.Event()),daemon=True,name='outlook-sync').start()
  _started=True
 return application
