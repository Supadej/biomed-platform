import unittest,sqlite3,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import service_signature as s
class Signature(unittest.TestCase):
 def setUp(self):
  self.c=sqlite3.connect(':memory:');self.c.executescript('create table fse_records(id text,kind text,payload text);create table masters(category text,id text,payload text);');self.c.execute('insert into fse_records values(?,?,?)',('i','instruments',json.dumps({'serial':'001','brand':'Phadia'})));self.actor=(0,0,0,0,'engineer')
 def job(self):return {'instrumentId':'i','jobNo':'BMDS28-10-26/1','description':'Repair','customerSignature':{'name':'Customer Test','consent':True,'strokes':[[[.1,.3],[.5,.6],[.9,.4]]]}}
 def test_saved_immutable_stamp_and_changed_report(self):
  r=self.job();s.save(self.c,self.actor,r,None);self.assertEqual(r['customerSignature']['capturedBy'],'engineer');self.assertEqual(r['customerSignature']['instrumentSnapshot']['serial'],'001');self.assertIn('signedAt',r['customerSignature']);prior=json.loads(json.dumps(r));s.save(self.c,self.actor,r,prior);r['description']='Changed'
  with self.assertRaises(ValueError):s.save(self.c,self.actor,r,prior)
  r['customerSignature']=None;s.save(self.c,self.actor,r,prior)
 def test_bad_signature(self):
  for sig in [{'name':'','consent':True,'strokes':[]},{'name':'A','consent':False,'strokes':[[[0,0],[1,1]]]},{'name':'A','consent':True,'strokes':[[[0,0],[2,1]]]},{'name':'A','consent':True,'strokes':[[[0,0],[float('nan'),1]]]}]:
   r=self.job();r['customerSignature']=sig
   with self.assertRaises(ValueError):s.save(self.c,self.actor,r,None)
if __name__=='__main__':unittest.main()
