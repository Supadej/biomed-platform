"""User-requested, backed-up, one-time Finance-only reset for release 83."""
import json,sqlite3
from pathlib import Path
MARKER='finance-empty-user-request-v83'
def apply(path):
 path=Path(path)
 with sqlite3.connect(path) as c:
  c.execute('CREATE TABLE IF NOT EXISTS financial_ui_migrations(name TEXT PRIMARY KEY)')
  if c.execute('select 1 from financial_ui_migrations where name=?',(MARKER,)).fetchone():return False
 backup=path.with_name(path.stem+'-before-finance-reset-v83.sqlite3')
 # Refuse to overwrite the recovery copy on retries.
 if not backup.exists():
  with sqlite3.connect(path) as source,sqlite3.connect(backup) as target:source.backup(target)
 with sqlite3.connect(path) as c:
  c.execute('BEGIN IMMEDIATE')
  if c.execute('select 1 from financial_ui_migrations where name=?',(MARKER,)).fetchone():return False
  row=c.execute("select value from workspace where key='biomed_budget_v60_years'").fetchone();data=json.loads(row[0]) if row else {};year=str(data.get('active') or 2027)
  blank={'fy':int(year),'products':[],'expenses':[],'costCenters':[],'workforce':[],'ledger':[],'approvals':[],'versions':[],'ocosNames':[],'settings':{'divisionSplit':False}}
  value=json.dumps({'active':int(year),'years':{year:blank}})
  c.execute("insert into workspace(key,value,revision) values('biomed_budget_v60_years',?,1) on conflict(key) do update set value=excluded.value,revision=workspace.revision+1",(value,))
  # Old financial snapshots may otherwise repopulate the reset workspace.
  c.execute("delete from workspace where key like 'biomed_budget_%' and key<>'biomed_budget_v60_years'")
  for table in ['budget_governance','finance_workspace','express_batches','express_profiles','financial_references']:
   if c.execute("select 1 from sqlite_master where type='table' and name=?",(table,)).fetchone():c.execute('delete from '+table)
  c.execute("insert or ignore into financial_ui_migrations values('restore-cost-centers-v81')")
  c.execute('insert into financial_ui_migrations values(?)',(MARKER,))
 return True
