import sys,sqlite3,copy,json,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import budget_governance as bg
ROOT=Path(__file__).resolve().parents[1]
class OtherCOSBrands(unittest.TestCase):
 def test_same_item_different_brands_stays_separate_and_publishes_by_id(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'db.sqlite3'
   with sqlite3.connect(ROOT/'data/biomed.sqlite3') as source,sqlite3.connect(path) as target:source.backup(target)
   with sqlite3.connect(path) as c:
    for b in ['Brand A','Brand B']:c.execute('insert into operational_brands values(?,?,1,1)',(b,b))
    data,state=bg.workspace(c,2027);state['expenses']=[{'id':str(i),'name':'Freight','category':'Other Cost of Sales','brand':b,'costCenter':'Lab','budget':[20]*12,'actual':[5]*12,'commitment':[0]*12} for i,b in enumerate(['Brand A','Brand B'])]
    state['expenses'].append({'id':'office','name':'Rent','category':'Administrative Expenses','costCenter':'Lab','budget':[30]*12,'actual':[1]*12,'commitment':[0]*12})
    c.execute('update workspace set value=? where key=?',(json.dumps(data),bg.KEY))
    lines=bg.grouped(state);self.assertEqual(len(lines),3);self.assertNotEqual(lines[0]['source'],lines[1]['source']);self.assertEqual(lines[0]['brand'],'Brand A');self.assertEqual(lines[1]['brand'],'Brand B');self.assertEqual(lines[2]['brand'],'')
    lines[0]['target']=[99]*12;bg.publish(c,2027,lines)
    _,updated=bg.workspace(c,2027);self.assertEqual(updated['expenses'][0]['budget'],[99]*12);self.assertEqual(updated['expenses'][1]['budget'],[20]*12);self.assertEqual(updated['expenses'][0]['actual'],[5]*12)
    # Historical line IDs survive the new brand-aware source label.
    legacy=[{'kind':'Expense','source':'Other Cost of Sales · Freight','costCenter':'Lab','lineId':'0','target':[77]*12}]
    mapped=bg.mapped_lines(legacy,updated);self.assertEqual(len(mapped),1);self.assertEqual(mapped[0]['brand'],'Brand A');self.assertEqual(mapped[0]['target'],[77]*12)
 def test_manage_items_rejects_missing_other_cos_brand_and_brand_on_expenses(self):
  with sqlite3.connect(':memory:') as c:
   c.execute('create table operational_brands(id text,name text,active int,version int)');c.execute("insert into operational_brands values('a','Brand A',1,1)")
   before={'years':{'2027':{'expenses':[]}}}
   item={'id':'a','name':'Freight','category':'Other Cost of Sales','costCenter':'Lab','budget':[0]*12}
   def changed(x):return {'years':{'2027':{'expenses':[x]}}}
   with self.assertRaisesRegex(ValueError,'active shared Brand'):bg.guard(c,before,changed(item))
   item['brand']='Brand A';bg.guard(c,before,changed(item))
   item['category']='Administrative Expenses'
   with self.assertRaisesRegex(ValueError,'do not use Brand'):bg.guard(c,before,changed(item))
   item['brand']='';bg.guard(c,before,changed(item))
if __name__=='__main__':unittest.main()
