import sqlite3,unittest,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import job_numbers as j
class JobNumbers(unittest.TestCase):
 def setUp(self):self.c=sqlite3.connect(':memory:')
 def test_cross_system_duplicate(self):
  j.reserve(self.c,'service:1',' ST100 ')
  with self.assertRaises(ValueError):j.reserve(self.c,'helpdesk:2','st100')
 def test_auto_unique(self):
  a=j.reserve(self.c,'service:1');b=j.reserve(self.c,'helpdesk:2');self.assertNotEqual(a,b)
 def test_same_owner_edit(self):
  j.reserve(self.c,'service:1','ST100');self.assertEqual(j.reserve(self.c,'service:1','ST100'),'ST100')
 def test_retired_number_not_reused(self):
  j.reserve(self.c,'service:1','ST100');j.reserve(self.c,'service:1','ST101')
  with self.assertRaises(ValueError):j.reserve(self.c,'service:2','ST100')
 def test_repair(self):
  j.reserve(self.c,'service:1','ST100');self.assertEqual(j.reserve(self.c,'service:2','ST100',True),'ST100-02')
 def test_migration(self):
  c=self.c;c.executescript('CREATE TABLE fse_records(id TEXT,kind TEXT,payload TEXT,version INT);CREATE TABLE crm_records(entity TEXT,id INT,payload TEXT,version INT,deleted INT);')
  for ident in ['a','b']:c.execute('INSERT INTO fse_records VALUES(?,?,?,1)',(ident,'jobs',json.dumps({'jobNo':'DUP','instrumentId':ident,'date':'2026-10-01'})))
  j.migrate(c);payloads=[json.loads(p) for p, in c.execute('SELECT payload FROM fse_records')];self.assertEqual(len({p['jobNo'] for p in payloads}),2);self.assertTrue(any(p.get('legacyJobNo')=='DUP' for p in payloads));self.assertIsNone(j.migrate(c))
if __name__=='__main__':unittest.main()
