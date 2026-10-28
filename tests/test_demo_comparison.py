import unittest,sqlite3,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import budget_demo_comparison as demo
class DemoComparison(unittest.TestCase):
 def fixture(self):
  import copy
  base=json.loads((Path(__file__).resolve().parents[1]/'budget-seed-base.json').read_text())
  year={'products':[{**p,'budget':[p['revenue']/12]*12,'cogsBudget':[p['cogs']/12]*12,'revenueActual':[0]*12,'cogsActual':[0]*12} for p in base['products']],'expenses':[{**e,'budget':[e.get('annual',0)/12]*12,'actual':[0]*12,'commitment':[0]*12} for e in base['expenses']],'ledger':[{'reference':'TEST-BUDGET-FIXTURE'}],'settings':{}}
  return {'active':2027,'years':{'2026':copy.deepcopy(year),'2027':copy.deepcopy(year)}}

 def test_years_and_ledger(self):
  old=self.fixture();new=demo.randomize(old);self.assertNotEqual(old,new)
  totals=[]
  for y in [2026,2027]:
   s=new['years'][str(y)];self.assertEqual(len(s['products']),39);totals.append(round(sum(sum(p['budget']) for p in s['products']),2))
   for p in s['products']:
    self.assertEqual(len(p['budget']),12);self.assertTrue(all(v>=0 for v in p['budget']));self.assertNotEqual(p['budget'],p['cogsBudget'])
    for field,prefix in [('revenueActual',''),('cogsActual','cogs:')]:
     for m in range(12):self.assertAlmostEqual(p[field][m],sum(l['amount'] for l in s['ledger'] if l['line']==prefix+p['id'] and l['month']==m and l['type']=='Actual'),2)
   for e in s['expenses']:
    for field,typ in [('actual','Actual'),('commitment','Commitment')]:
     for m in range(12):self.assertAlmostEqual(e[field][m],sum(l['amount'] for l in s['ledger'] if l['line']==e['id'] and l['month']==m and l['type']==typ),2)
    for field in ['budget','actual','commitment']:
     if e.get('componentRows'):
      for m in range(12):self.assertAlmostEqual(e[field][m],sum(r[field][m] for r in e['componentRows']),2)
   self.assertTrue(all(l['date'].startswith(str(y-1 if l['month']<8 else y)) for l in s['ledger']))
  self.assertNotEqual(totals[0],totals[1]);self.assertEqual(new,demo.randomize(old))
  self.assertTrue(any(new['years']['2026']['products'][0]['revenueActual'][6:]));self.assertFalse(any(new['years']['2027']['products'][0]['revenueActual'][6:]))
 def test_one_time_backup_and_real_data_skip(self):
  c=sqlite3.connect(':memory:');c.execute('CREATE TABLE workspace(key TEXT PRIMARY KEY,value TEXT,revision INTEGER)');v=json.dumps(self.fixture());c.execute('INSERT INTO workspace VALUES(?,?,1)',(demo.KEY,v));self.assertTrue(demo.apply(c));value=c.execute('SELECT value FROM workspace').fetchone()[0];self.assertFalse(demo.apply(c));self.assertEqual(value,c.execute('SELECT value FROM workspace').fetchone()[0]);self.assertEqual(v,c.execute('SELECT payload FROM deployment_data_backups').fetchone()[0]);
  c.execute('DELETE FROM workspace');c.execute('DELETE FROM deployment_data_backups');c.execute('INSERT INTO workspace VALUES(?,?,1)',(demo.KEY,json.dumps({'years':{'2026':{'ledger':[]},'2027':{'ledger':[]}}})));self.assertFalse(demo.apply(c))
if __name__=='__main__':unittest.main()
