import sys,sqlite3,json,tempfile,unittest,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import serve,budget_governance as bg,cost_centers
class Mapping(unittest.TestCase):
 def test_item_budgets_update_existing_items_only(self):
  with tempfile.TemporaryDirectory() as tmp:
   prior=serve.DB;serve.DB=Path(tmp)/'db.sqlite3'
   try:
    with sqlite3.connect(ROOT/'data'/'biomed.sqlite3') as src,sqlite3.connect(serve.DB) as dst:src.backup(dst)
    serve.prepare_database()
    with serve.connect() as c:
     data,state=bg.workspace(c,2027);state['costCenters']=[{'id':'DIAG','name':'Diagnostics','active':True}]
     state['expenses']=[{'id':'freight','name':'Freight','category':'Other Cost of Sales','costCenter':'Diagnostics','budget':[20]*12,'actual':[5]*12,'commitment':[1]*12},{'id':'duty','name':'Import duty','category':'Other Cost of Sales','costCenter':'Diagnostics','budget':[30]*12,'actual':[2]*12,'commitment':[0]*12}]
     c.execute('update workspace set value=? where key=?',(json.dumps(data),bg.KEY))
     lines=bg.grouped(state);self.assertEqual(len([x for x in lines if x['kind']=='Expense']),2)
     lines[0]['target']=[90]*12;bg.publish(c,2027,lines)
     _,updated=bg.workspace(c,2027);self.assertEqual(len(updated['expenses']),2);self.assertEqual(updated['expenses'][0]['id'],'freight');self.assertEqual(updated['expenses'][0]['budget'],[90]*12);self.assertEqual(updated['expenses'][0]['actual'],[5]*12)
     legacy=[{'kind':'Expense','costCenter':'Diagnostics','source':'Other Cost of Sales','target':[500]*12}];mapped=bg.mapped_lines(legacy,state);self.assertEqual(len(mapped),2);self.assertEqual(sum(x['target'][0] for x in mapped),500)
     c.execute('create table financial_references(id integer,payload text,version integer)');c.execute('insert into financial_references values(1,?,1)',(json.dumps({'costCenters':[{'id':'NEW','name':'Research','active':True}]}),));cost_centers.migrate_legacy(c);cost_centers.migrate_legacy(c)
     _,updated=bg.workspace(c,2027);self.assertEqual(sum(x['name']=='Research' for x in updated['costCenters']),0);self.assertEqual(c.execute('select count(*) from accounts').fetchone()[0],44)
   finally:serve.DB=prior
if __name__=='__main__':unittest.main()
