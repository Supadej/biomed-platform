"""Account-private table presentation preferences; no business-record writes."""
import json

def initialize(c):c.execute('CREATE TABLE IF NOT EXISTS table_layouts(account_id TEXT NOT NULL,scope TEXT NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(account_id,scope))')
def validate(body):
 scope=body.get('scope');columns=body.get('columns');groups=body.get('groups',{})
 if not isinstance(scope,str) or not 1<=len(scope)<=200:raise ValueError('Invalid table scope')
 if not isinstance(columns,list) or not 1<=len(columns)<=150:raise ValueError('Invalid columns')
 seen=set()
 for col in columns:
  if not isinstance(col,dict) or type(col.get('id')) is not int or not 0<=col['id']<150 or col['id'] in seen:raise ValueError('Invalid column identity')
  seen.add(col['id'])
  if 'width' in col and (type(col['width']) is not int or not 80<=col['width']<=1200):raise ValueError('Invalid column width (80–1200 px)')
  if type(col.get('visible')) is not bool or not isinstance(col.get('label'),str) or not 1<=len(col['label'].strip())<=120:raise ValueError('Invalid column heading')
 if not any(c['visible'] for c in columns):raise ValueError('Keep at least one column')
 if not isinstance(groups,dict) or len(groups)>100 or any(not isinstance(k,str) or len(k)>20 or not isinstance(v,str) or not 1<=len(v.strip())<=120 for k,v in groups.items()):raise ValueError('Invalid group headings')
 return scope,{'columns':columns,'groups':groups}
def handle(h,method,connect,session,origin):
 actor=session(h)
 if not actor:return h.reply(401,{'error':'Sign in required'})
 try:
  with connect() as c:
   initialize(c)
   if method=='GET':return h.reply(200,{'layouts':{s:json.loads(p) for s,p in c.execute('SELECT scope,payload FROM table_layouts WHERE account_id=?',(str(actor[0]),))}})
   if not origin(h):return h.reply(403,{'error':'Invalid origin'})
   n=int(h.headers.get('Content-Length','0'))
   if not 0<n<=65536:raise ValueError('Invalid request size')
   body=json.loads(h.rfile.read(n));scope,payload=validate(body)
   if body.get('reset'):c.execute('DELETE FROM table_layouts WHERE account_id=? AND scope=?',(str(actor[0]),scope))
   else:c.execute('INSERT OR REPLACE INTO table_layouts VALUES(?,?,?)',(str(actor[0]),scope,json.dumps(payload,ensure_ascii=False)))
  return h.reply(200,{'saved':True})
 except (ValueError,TypeError,KeyError) as e:return h.reply(400,{'error':str(e)})
