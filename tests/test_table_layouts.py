import io,json,sqlite3,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import table_layouts as t
class LayoutTests(unittest.TestCase):
 def setUp(self):self.c=sqlite3.connect(':memory:');t.initialize(self.c)
 def call(self,user='a',body=None,origin=True):
  class H:
   def reply(self,s,v):return s,v
  h=H();raw=json.dumps(body).encode() if body else b'';h.headers={'Content-Length':str(len(raw))};h.rfile=io.BytesIO(raw)
  return t.handle(h,'GET' if body is None else 'POST',lambda:self.c,lambda h:(user,) if user else None,lambda h:origin)
 def payload(self):return {'scope':'portal:expenses:0','columns':[{'id':0,'label':'Expense date','visible':True},{'id':1,'label':'Amount','visible':False}],'groups':{}}
 def test_private_and_persistent(self):
  self.assertEqual(self.call(body=self.payload())[0],200)
  self.assertIn('portal:expenses:0',self.call()[1]['layouts']);self.assertEqual(self.call('b')[1]['layouts'],{})
 def test_reset(self):
  p=self.payload();self.call(body=p);p['reset']=True;self.call(body=p);self.assertEqual(self.call()[1]['layouts'],{})
 def test_auth_origin(self):
  self.assertEqual(self.call(user=None)[0],401);self.assertEqual(self.call(body=self.payload(),origin=False)[0],403)
 def test_widths_private_validated_and_reset(self):
  p=self.payload();p['columns'][0]['width']=360
  self.assertEqual(self.call(body=p)[0],200)
  self.assertEqual(self.call()[1]['layouts'][p['scope']]['columns'][0]['width'],360)
  self.assertEqual(self.call('another-user')[1]['layouts'],{})
  for bad in [0,79,1201,True,None,'200',100.5]:
   p['columns'][0]['width']=bad;self.assertEqual(self.call(body=p)[0],400)
  p['columns'][0]['width']=80;self.assertEqual(self.call(body=p)[0],200)
  p['reset']=True;self.call(body=p);self.assertEqual(self.call()[1]['layouts'],{})
 def test_bad_columns(self):
  for columns in [[],[{'id':0,'label':'','visible':True}],[{'id':0,'label':'A','visible':False}],[{'id':0,'label':'A','visible':True}]*2]:
   p=self.payload();p['columns']=columns;self.assertEqual(self.call(body=p)[0],400)
if __name__=='__main__':unittest.main()
