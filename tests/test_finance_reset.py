import sys,unittest,tempfile,sqlite3,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import finance_reset,budget_governance as bg
ROOT=Path(__file__).resolve().parents[1]
class FinanceReset(unittest.TestCase):
 def test_only_finance_cleared_once_with_recoverable_backup(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'db.sqlite3'
   with sqlite3.connect(ROOT/'data/biomed.sqlite3') as source,sqlite3.connect(path) as target:source.backup(target)
   with sqlite3.connect(path) as c:
    portal=c.execute("select value from workspace where key='biomed_portal_v33_clean'").fetchone()[0]
    c.execute("insert into workspace values('other-system-test','{\"keep\":true}',1)")
    data,state=bg.workspace(c,2027);state['costCenters']=[{'id':'OLD','name':'Old Center','active':True}];state['expenses']=[{'id':'old-expense'}]
    c.execute('update workspace set value=? where key=?',(json.dumps(data),bg.KEY));bg.initialize(c);c.execute('insert into budget_governance values(?,?,?)',('2027','{}',1))
   self.assertTrue(finance_reset.apply(path));backup=path.with_name('db-before-finance-reset-v83.sqlite3');self.assertTrue(backup.is_file())
   with sqlite3.connect(backup) as c:
    _,old=bg.workspace(c,2027);self.assertEqual(old['costCenters'][0]['name'],'Old Center')
   with sqlite3.connect(path) as c:
    data,state=bg.workspace(c,2027);self.assertEqual(state['costCenters'],[]);self.assertEqual(state['expenses'],[]);self.assertEqual(c.execute('select count(*) from budget_governance').fetchone()[0],0)
    self.assertEqual(c.execute('select count(*) from accounts').fetchone()[0],44);self.assertEqual(c.execute("select value from workspace where key='biomed_portal_v33_clean'").fetchone()[0],portal);self.assertTrue(c.execute("select 1 from workspace where key='other-system-test'").fetchone())
    state['costCenters']=[{'id':'NEW','name':'New Center','active':True}];c.execute('update workspace set value=? where key=?',(json.dumps(data),bg.KEY))
   self.assertFalse(finance_reset.apply(path))
   with sqlite3.connect(path) as c:self.assertEqual(bg.workspace(c,2027)[1]['costCenters'][0]['name'],'New Center')
if __name__=='__main__':unittest.main()
