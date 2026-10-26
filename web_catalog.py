"""SQLite product catalogue and public enquiry API. Products default to hidden."""
import csv,io,json,re,sqlite3,uuid,datetime
from urllib.parse import urlsplit,parse_qs

def init(c):
 c.executescript("""CREATE TABLE IF NOT EXISTS web_catalog (sku TEXT PRIMARY KEY, master_id TEXT, name TEXT NOT NULL, brand TEXT DEFAULT '', category TEXT DEFAULT '', subcategory TEXT DEFAULT '', description TEXT DEFAULT '', image_url TEXT DEFAULT '', specification TEXT DEFAULT '', visible INTEGER NOT NULL DEFAULT 0, updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
 CREATE INDEX IF NOT EXISTS web_catalog_visible_brand ON web_catalog(visible,brand,sku);
 CREATE INDEX IF NOT EXISTS web_catalog_brand ON web_catalog(brand);
 CREATE TABLE IF NOT EXISTS web_enquiries (id TEXT PRIMARY KEY, created_at TEXT DEFAULT CURRENT_TIMESTAMP, contact_json TEXT NOT NULL, items_json TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'New');""")

def req_body(h,max_bytes=18_000_000):
 length=int(h.headers.get('Content-Length','0'))
 if length<1 or length>max_bytes:raise ValueError('Invalid request size')
 return h.rfile.read(length)

def handle(h,method,connect,session_account,account_permissions,valid_origin):
 path=urlsplit(h.path).path; qs=parse_qs(urlsplit(h.path).query)
 if method!='GET' and not valid_origin(h):return h.reply(403,{'error':'Invalid origin'})
 actor=session_account(h);perms=account_permissions(actor) if actor else set()
 admin=bool(actor and ('content' in perms or 'portal.content.edit' in perms or 'portal.content.create' in perms or 'approve_all' in perms or (len(actor)>3 and str(actor[3]).lower().replace('_',' ').replace('-',' ') in ('system admin','admin'))))
 public=path in ('/api/catalog/products','/api/catalog/filters','/api/catalog/enquiry')
 if public and method not in ('GET' if path!='/api/catalog/enquiry' else 'POST',):return h.reply(405,{'error':'Method not allowed'})
 if not public and not admin:return h.reply(403,{'error':'Website management permission required'})
 try:
  with connect() as c:
   if path=='/api/catalog/products' and method=='GET':
    page=max(1,int(qs.get('page',['1'])[0]));limit=min(60,max(1,int(qs.get('limit',['24'])[0])));q=qs.get('q',[''])[0].strip()[:100];brand=qs.get('brand',[''])[0].strip()[:100];category=qs.get('category',[''])[0].strip()[:100]
    where=['visible=1'];args=[]
    if q:where.append('(name LIKE ? OR sku LIKE ? OR description LIKE ?)');args.extend(['%'+q+'%']*3)
    if brand:where.append('brand=?');args.append(brand)
    if category:where.append('category=?');args.append(category)
    clause=' AND '.join(where)
    total=c.execute('SELECT COUNT(*) FROM web_catalog WHERE '+clause,args).fetchone()[0]
    rows=c.execute('SELECT sku,name,brand,category,subcategory,description,image_url,specification FROM web_catalog WHERE '+clause+' ORDER BY name COLLATE NOCASE,sku LIMIT ? OFFSET ?',args+[limit,(page-1)*limit]).fetchall()
    return h.reply(200,{'total':total,'page':page,'limit':limit,'items':[dict(zip(('sku','name','brand','category','subcategory','description','image_url','specification'),r)) for r in rows]})
   if path=='/api/catalog/filters' and method=='GET':
    brands=c.execute('SELECT brand,COUNT(*) FROM web_catalog WHERE visible=1 AND brand<>"" GROUP BY brand ORDER BY brand LIMIT 500').fetchall()
    categories=c.execute('SELECT category,COUNT(*) FROM web_catalog WHERE visible=1 AND category<>"" GROUP BY category ORDER BY category LIMIT 500').fetchall()
    return h.reply(200,{'brands':brands,'categories':categories})
   if path=='/api/catalog/enquiry' and method=='POST':
    data=json.loads(req_body(h,30000));contact=data.get('contact',{});items=data.get('items',[])
    required=['salutation','firstName','lastName','company','email','countryCode','phone','address']
    if not isinstance(contact,dict) or any(not str(contact.get(k,'')).strip() for k in required):raise ValueError('Complete all required contact fields')
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',str(contact['email'])):raise ValueError('Invalid email')
    if not isinstance(items,list) or not 1<=len(items)<=40 or any(not isinstance(x,str) or len(x)>120 for x in items):raise ValueError('Select 1–40 products')
    items=list(dict.fromkeys(items)); placeholders=','.join('?'*len(items))
    records=c.execute('SELECT sku,name,brand,category FROM web_catalog WHERE visible=1 AND sku IN ('+placeholders+')',items).fetchall()
    if len(records)!=len(items):raise ValueError('Some selected products are no longer available')
    safe={k:str(contact.get(k,''))[:1500] for k in required+['message']}; eid=uuid.uuid4().hex
    c.execute('INSERT INTO web_enquiries(id,contact_json,items_json) VALUES(?,?,?)',(eid,json.dumps(safe),json.dumps([dict(zip(('sku','name','brand','category'),r)) for r in records])))
    return h.reply(201,{'id':eid,'submitted':True})
   if path=='/api/catalog/admin/products' and method=='GET':
    q=qs.get('q',[''])[0].strip()[:100];page=max(1,int(qs.get('page',['1'])[0]));limit=50;where='WHERE sku LIKE ? OR name LIKE ? OR brand LIKE ?' if q else '';args=['%'+q+'%']*3 if q else []
    total=c.execute('SELECT COUNT(*) FROM web_catalog '+where,args).fetchone()[0]
    rows=c.execute('SELECT sku,master_id,name,brand,category,subcategory,description,image_url,specification,visible FROM web_catalog '+where+' ORDER BY updated_at DESC,sku LIMIT ? OFFSET ?',args+[limit,(page-1)*limit]).fetchall()
    return h.reply(200,{'total':total,'page':page,'items':[dict(zip(('sku','master_id','name','brand','category','subcategory','description','image_url','specification','visible'),r)) for r in rows]})
   if path=='/api/catalog/admin/products' and method=='POST':
    d=json.loads(req_body(h,100000));sku=str(d.get('sku','')).strip()[:120];name=str(d.get('name','')).strip()[:250]
    if not sku or not name:raise ValueError('SKU and product name required')
    vals=[sku,str(d.get('master_id',''))[:120],name]+[str(d.get(k,''))[:(5000 if k in ['description','specification'] else 500)] for k in ['brand','category','subcategory','description','image_url','specification']]+[1 if d.get('visible') else 0]
    c.execute('INSERT INTO web_catalog(sku,master_id,name,brand,category,subcategory,description,image_url,specification,visible) VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(sku) DO UPDATE SET master_id=excluded.master_id,name=excluded.name,brand=excluded.brand,category=excluded.category,subcategory=excluded.subcategory,description=excluded.description,image_url=excluded.image_url,specification=excluded.specification,visible=excluded.visible,updated_at=CURRENT_TIMESTAMP',vals)
    return h.reply(200,{'saved':True})
   if path=='/api/catalog/admin/products' and method=='DELETE':
    sku=qs.get('sku',[''])[0];c.execute('DELETE FROM web_catalog WHERE sku=?',(sku,));return h.reply(200,{'removed':True})
   if path=='/api/catalog/admin/import' and method=='POST':
    # UTF-8 CSV with header; unpublished by default. Changes are transactional.
    raw=req_body(h,18_000_000);reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    if not reader.fieldnames or not {'sku','name'}<=set(reader.fieldnames):raise ValueError('CSV requires sku,name headings')
    updated=0
    for row in reader:
     sku=str(row.get('sku') or '').strip()[:120];name=str(row.get('name') or '').strip()[:250]
     if not sku or not name:continue
     keys=['brand','category','subcategory','description','image_url','specification','master_id'];v=[str(row.get(k) or '')[:5000] for k in keys]
     vis=1 if str(row.get('visible','')).strip().lower() in ['1','true','yes','show'] else 0
     # Existing visibility preserved unless explicit visible column present.
     if 'visible' not in reader.fieldnames:
      old=c.execute('SELECT visible FROM web_catalog WHERE sku=?',(sku,)).fetchone();vis=old[0] if old else 0
     c.execute('INSERT INTO web_catalog(sku,name,brand,category,subcategory,description,image_url,specification,master_id,visible) VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(sku) DO UPDATE SET name=excluded.name,brand=excluded.brand,category=excluded.category,subcategory=excluded.subcategory,description=excluded.description,image_url=excluded.image_url,specification=excluded.specification,master_id=excluded.master_id,visible=excluded.visible,updated_at=CURRENT_TIMESTAMP',[sku,name]+v[:6]+[v[6],vis]);updated+=1
     if updated>200000:raise ValueError('Maximum 200,000 rows per import')
    return h.reply(200,{'imported':updated})
   if path=='/api/catalog/admin/sync' and method=='POST':
    # Upsert master products without overwriting curated website content or visibility.
    count=0
    for ident,payload in c.execute("SELECT id,payload FROM masters WHERE category='products'"):
     try:d=json.loads(payload)
     except (ValueError,TypeError):continue
     if not isinstance(d,dict):continue
     sku=str(d.get('code') or d.get('sku') or d.get('productCode') or ident).strip()[:120]
     name=str(d.get('name') or d.get('description') or sku).strip()[:250]
     brand=str(d.get('brand') or d.get('brandName') or d.get('principal') or '')[:500]
     category=str(d.get('category') or d.get('group') or '')[:500]
     c.execute('INSERT OR IGNORE INTO web_catalog(sku,master_id,name,brand,category,visible) VALUES(?,?,?,?,?,0)',(sku,str(ident),name,brand,category));count+=1
    return h.reply(200,{'scanned':count,'note':'Existing website edits/visibility preserved. Newly discovered products hidden.'})
   if path=='/api/catalog/admin/enquiries' and method=='GET':
    rows=c.execute('SELECT id,created_at,contact_json,items_json,status FROM web_enquiries ORDER BY created_at DESC LIMIT 200').fetchall()
    return h.reply(200,{'items':[{'id':r[0],'date':r[1],'contact':json.loads(r[2]),'items':json.loads(r[3]),'status':r[4]} for r in rows]})
   if path=='/api/catalog/admin/enquiries' and method=='POST':
    d=json.loads(req_body(h,2000));status=d.get('status');
    if status not in ['New','In progress','Replied','Closed']:raise ValueError('Invalid status')
    c.execute('UPDATE web_enquiries SET status=? WHERE id=?',(status,d.get('id')));return h.reply(200,{'saved':True})
  return h.reply(404,{'error':'Unknown catalogue endpoint'})
 except (ValueError,UnicodeError,sqlite3.DatabaseError) as e:return h.reply(400,{'error':str(e)[:250]})
