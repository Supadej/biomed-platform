import unittest,sqlite3,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import operational_brands as b
class Brands(unittest.TestCase):
 def setUp(self):
  self.c=sqlite3.connect(':memory:');self.c.executescript('create table workspace(key text primary key,value text,revision integer);create table fse_records(id text,kind text,payload text,version integer);create table crm_records(entity text,id integer,payload text,version integer);create table service_setup(id integer,payload text,version integer);')
  for key,d in [(b.KEYS[0],{'products':[{'id':'p','brand':'Phadia'}]}),(b.KEYS[1],{'productLines':['Phadia'],'brands':[{'id':'web','name':'Independent'}]}),(b.KEYS[2],{'years':{'2027':{'products':[{'id':'b','brand':'Phadia'}]}}})]:self.c.execute('insert into workspace values(?,?,1)',(key,json.dumps(d)))
  b.initialize(self.c);self.actor=(0,0,0,0,'admin');self.perms={'is_view','is.master-products.view','is.master-products.edit'}
 def test_rename_updates_operations_but_not_website(self):
  self.c.executescript('create table documents(id text,kind text,reference text,status text,source_id text,payload text);create table document_lines(document_id text,position integer,product_id text,payload text);create table masters(category text,id text,payload text);create table stock_records(category text,position integer,payload text);')
  r=b.rows(self.c)[0];b.dispatch(self.c,self.actor,self.perms,{'action':'rename','id':r['id'],'version':r['version'],'name':'Phadia Updated'})
  for key in [b.KEYS[0],b.KEYS[2]]:
   data=self.c.execute('select value from workspace where key=?',(key,)).fetchone()[0];self.assertIn('Phadia Updated',data)
  portal=json.loads(self.c.execute('select value from workspace where key=?',(b.KEYS[1],)).fetchone()[0]);self.assertEqual(portal['brands'][0]['name'],'Independent');self.assertIn('Phadia Updated',portal['productLines'])
 def test_create_duplicate_and_permission(self):
  b.dispatch(self.c,self.actor,self.perms,{'action':'create','name':'Mabtech'})
  with self.assertRaises(sqlite3.IntegrityError):b.dispatch(self.c,self.actor,self.perms,{'action':'create','name':'mabtech'})
  with self.assertRaises(Exception):b.dispatch(self.c,self.actor,{'is_view'},{'action':'create','name':'X'})
 def test_archive_and_stale(self):
  r=b.rows(self.c)[0];b.dispatch(self.c,self.actor,self.perms,{'action':'remove','id':r['id'],'version':r['version']});self.assertFalse(b.rows(self.c)[0]['active'])
  with self.assertRaises(ValueError):b.dispatch(self.c,self.actor,self.perms,{'action':'restore','id':r['id'],'version':r['version']})
  p=json.loads(self.c.execute('select value from workspace where key=?',(b.KEYS[1],)).fetchone()[0]);self.assertEqual(p['brands'][0]['name'],'Independent');self.assertEqual(p['productLines'],[])
 def test_forged_brand_rejected(self):
  value=self.c.execute('select value from workspace where key=?',(b.KEYS[0],)).fetchone()[0];d=json.loads(value);d['products'][0]['brand']='Not approved'
  with self.assertRaises(ValueError):b.validate_workspace(self.c,b.KEYS[0],value,json.dumps(d))
if __name__=='__main__':unittest.main()
