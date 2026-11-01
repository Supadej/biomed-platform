"""Dropdown choices from the existing fiscal-year Cost Center Management records."""
import json
from urllib.parse import parse_qs,urlsplit

def migrate_legacy(c):
 if not c.execute("select 1 from sqlite_master where name='financial_references'").fetchone():return
 row=c.execute('select payload from financial_references where id=1').fetchone()
 if not row:return
 c.execute('CREATE TABLE IF NOT EXISTS financial_ui_migrations(name TEXT PRIMARY KEY)')
 if c.execute("select 1 from financial_ui_migrations where name='restore-cost-centers-v81'").fetchone():return
 centers=json.loads(row[0]).get('costCenters',[])
 raw=c.execute("select value from workspace where key='biomed_budget_v60_years'").fetchone()
 if raw:
  data=json.loads(raw[0])
  for state in data.get('years',{}).values():
   items=state.setdefault('costCenters',[])
   for center in centers:
    if not any(x.get('name','').casefold()==center['name'].casefold() for x in items):items.append(center)
  c.execute("update workspace set value=?,revision=revision+1 where key='biomed_budget_v60_years'",(json.dumps(data,ensure_ascii=False),))
 c.execute("insert into financial_ui_migrations values('restore-cost-centers-v81')")
def handle(h,connect,session):
 if not session(h):return h.reply(401,{'error':'Sign in required'})
 with connect() as c:
  migrate_legacy(c);row=c.execute("select value from workspace where key='biomed_budget_v60_years'").fetchone();data=json.loads(row[0]) if row else {}
  year=parse_qs(urlsplit(h.path).query).get('year',[str(data.get('active',''))])[0];state=data.get('years',{}).get(year,{})
  return h.reply(200,{'costCenters':state.get('costCenters',[])})
