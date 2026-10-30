import unittest,sqlite3,datetime,tempfile,threading
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import document_numbers as d,job_numbers as j
class Numbering(unittest.TestCase):
 def test_all_requested_formats_and_preserved_history(self):
  c=sqlite3.connect(':memory:');c.execute('CREATE TABLE documents(reference TEXT)');old={'documents':[{'id':'old','kind':'quotation','ref':'LEGACY'}]};data={'documents':old['documents']+[{'id':k,'kind':k,'ref':'preview-'+k} for k in d.PREFIXES]}
  d.assign(c,data,old)
  for row in data['documents'][1:]:
   prefix,digits=d.PREFIXES[row['kind']];self.assertEqual(digits,2);self.assertRegex(row['ref'],r'^'+prefix+r'\d{2}-\d{2}-\d{2}/\d+$')
  cn=[x['ref'] for x in data['documents'] if x['kind'] in ['credit-note','debit-note']];self.assertEqual(len(set(cn)),2);self.assertEqual(data['documents'][0]['ref'],'LEGACY')
  same=d.allocate(c,'is','quotation','BMDQ');self.assertEqual(same,next(x['ref'] for x in data['documents'] if x['id']=='quotation'))
 def test_job_and_ticket_share_daily_sequence(self):
  c=sqlite3.connect(':memory:');a=j.reserve(c,'service:1');b=j.reserve(c,'helpdesk:1');self.assertRegex(a,r'^BMDS\d{2}-\d{2}-\d{2}/1$');self.assertTrue(b.endswith('/2'));self.assertEqual(j.reserve(c,'service:1'),a)
 def test_existing_cannot_be_renumbered(self):
  c=sqlite3.connect(':memory:')
  with self.assertRaises(ValueError):d.assign(c,{'documents':[{'id':'1','ref':'changed'}]},{'documents':[{'id':'1','ref':'original'}]})
 def test_authorized_restore_retains_backup_references(self):
  c=sqlite3.connect(':memory:');old={'documents':[{'id':'original','kind':'invoice','ref':'OLD-INV'}]};restored={'documents':[{'id':'restored','kind':'invoice','ref':'RESTORED-INV'}]};d.assign(c,restored,old,preserve_references=True);self.assertEqual(restored['documents'][0]['ref'],'RESTORED-INV');self.assertEqual(c.execute('SELECT COUNT(*) FROM document_number_reservations').fetchone()[0],2)
 def test_counter_rolls_over_and_never_reuses(self):
  c=sqlite3.connect(':memory:');day=datetime.date(2026,10,28);a=d.allocate(c,'is','1','IV',day,2);b=d.allocate(c,'is','2','IV',day,2);new=d.allocate(c,'is','3','IV',day+datetime.timedelta(days=1),2);self.assertEqual(a,'IV28-10-26/1');self.assertEqual(b,'IV28-10-26/2');self.assertEqual(new,'IV29-10-26/1')
 def test_concurrent_allocations_are_unique(self):
  with tempfile.TemporaryDirectory() as root:
   db=Path(root)/'numbers.db';errors=[];refs=[]
   def work(i):
    try:
     with sqlite3.connect(db,timeout=10) as c:
      c.execute('BEGIN IMMEDIATE');refs.append(d.allocate(c,'is',str(i),'BMDQ',datetime.date(2026,10,28),2))
    except Exception as e:errors.append(e)
   threads=[threading.Thread(target=work,args=(i,)) for i in range(12)]
   for t in threads:t.start()
   for t in threads:t.join()
   self.assertEqual(errors,[]);self.assertEqual(len(set(refs)),12)
if __name__=='__main__':unittest.main()
