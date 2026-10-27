"""Copilot preferences restrict existing permissions; never grant new ones."""
import json,time
MODULES=('portal','is','budget','developer')
DEFAULT={'enabled':True,'modules':list(MODULES),'personal_key':True,'company_key':True,'share_summary':False,'calendar_read':False,'calendar_draft':False}
CEILING={**DEFAULT,'share_summary':True,'calendar_read':True,'calendar_draft':True}
def init(c):
 c.executescript("""CREATE TABLE IF NOT EXISTS copilot_access(account_id TEXT PRIMARY KEY,preferences TEXT NOT NULL,ceiling TEXT NOT NULL);
 CREATE TABLE IF NOT EXISTS copilot_access_audit(id INTEGER PRIMARY KEY,actor_id TEXT NOT NULL,target_id TEXT NOT NULL,kind TEXT NOT NULL,payload TEXT NOT NULL,created_at INTEGER NOT NULL);""")
def validate(value):
 if not isinstance(value,dict) or set(value)-set(DEFAULT):raise ValueError('Invalid Copilot access fields')
 for k,v in value.items():
  if k=='modules':
   if not isinstance(v,list) or any(m not in MODULES for m in v) or len(v)!=len(set(v)):raise ValueError('Invalid Copilot modules')
  elif type(v) is not bool:raise ValueError('Copilot switches must be true or false')
 return value
def state(c,actor,perms,is_admin):
 row=c.execute('SELECT preferences,ceiling FROM copilot_access WHERE account_id=?',(actor[0],)).fetchone()
 own={**DEFAULT,**(json.loads(row[0]) if row else {})};ceiling={**CEILING,**(json.loads(row[1]) if row else {})}
 role_modules=list(MODULES) if is_admin else ([m for m in MODULES if 'ai.internal.use' in perms and (m=='portal' or m=='is' and 'is_view' in perms or m=='budget' and 'budget_view' in perms or m=='developer' and 'ai.developer' in perms)])
 effective={k:own[k] and ceiling[k] for k in DEFAULT if k!='modules'}
 effective['modules']=[m for m in role_modules if m in own['modules'] and m in ceiling['modules']] if effective['enabled'] else []
 from copilot_calendar import allowed
 effective['calendar_read']=effective['calendar_read'] and allowed(perms)
 effective['calendar_draft']=effective['calendar_draft'] and allowed(perms,'create')
 return {'preferences':own,'admin_ceiling':ceiling,'role_modules':role_modules,'effective':effective}
def save(c,actor,target,kind,values):
 validate(values)
 row=c.execute('SELECT preferences,ceiling FROM copilot_access WHERE account_id=?',(target,)).fetchone()
 own=json.loads(row[0]) if row else {};ceiling=json.loads(row[1]) if row else {}
 (ceiling if kind=='admin' else own).update(values)
 c.execute('INSERT OR REPLACE INTO copilot_access VALUES(?,?,?)',(target,json.dumps(own),json.dumps(ceiling)))
 c.execute('INSERT INTO copilot_access_audit(actor_id,target_id,kind,payload,created_at) VALUES(?,?,?,?,?)',(actor[0],target,kind,json.dumps(values),int(time.time())))
def snapshot(c,actor,perms,module):
 """Only aggregates; never serialize arbitrary records or personal profiles."""
 import permissions_policy as policy
 if module=='portal':
  row=c.execute("SELECT value FROM workspace WHERE key='biomed_portal_v33_clean'").fetchone()
  data=json.loads(row[0]) if row else {}
  out={}
  for field,permission in [('tasks','tasks'),('requests','requests'),('expenses','expenses'),('objectives','objectives')]:
   if permission not in perms:continue
   # Explicit ownership only; ambiguous and shared rows are omitted.
   rows=[r for r in data.get(field,[]) if isinstance(r,dict) and any(str(r.get(k,''))==str(actor[4]) for k in ('userId','employeeId','ownerId','assignedTo'))]
   out[field]={'own_record_count':len(rows)}
  return {'module':module,'scope':'own records only; counts only',**out}
 if module=='is':
  row=c.execute("SELECT value FROM workspace WHERE key='biomed_is_v50_transactions'").fetchone()
  data=json.loads(policy.read_filter(perms,'biomed_is_v50_transactions',row[0])) if row else {}
  counts={}
  for r in data.get('documents',[]):
   kind=r.get('kind','unknown')
   if 'is.'+kind+'.view' in perms:counts[kind]=counts.get(kind,0)+1
  out={'document_counts':counts}
  if 'is.stock-inventory.view' in perms:out['lot_count']=len(data.get('lots',[]))
  return {'module':module,'scope':'permission-filtered counts only',**out}
 if module=='budget':
  row=c.execute("SELECT value FROM workspace WHERE key='biomed_budget_v60_years'").fetchone()
  data=json.loads(policy.read_filter(perms,'biomed_budget_v60_years',row[0])) if row else {}
  out=[]
  for year,y in list(data.get('years',{}).items())[-10:]:
   # Amounts only if the existing financial masks allow them.
   def total(field,rows):return sum(sum(float(v) for v in r.get(field,[]) if isinstance(v,(int,float))) for r in rows)
   expenses=y.get('expenses',[]);products=y.get('products',[])
   out.append({'year':year,'expense_actual':total('actual',expenses),'expense_commitment':total('commitment',expenses),'revenue_actual':total('revenueActual',products),'cogs_actual':total('cogsActual',products)})
  return {'module':module,'scope':'permission-filtered fiscal-year totals; hidden schedules remain masked','years':out}
 return {'module':module,'scope':'No developer logs or source access is connected.'}
