import json,sqlite3,sys
if len(sys.argv)!=3:raise SystemExit('Usage: python export_sqlserver.py biomed.sqlite3 transfer.json')
c=sqlite3.connect(sys.argv[1]);c.row_factory=sqlite3.Row
payload={'workspace':[dict(r) for r in c.execute('select key,value,revision from workspace')], 'accounts':[dict(r) for r in c.execute('select id,email,name,role,user_id,hex(password_hash) password_hash,hex(salt) salt,iterations,disabled,failed_attempts,locked_until,created_at from accounts')], 'documents':[dict(r) for r in c.execute('select id,kind,reference,status,source_id,payload from documents')], 'lines':[dict(r) for r in c.execute('select document_id,position,product_id,payload from document_lines')], 'masters':[dict(r) for r in c.execute('select category,id,payload from masters')], 'stock':[dict(r) for r in c.execute('select category,position,payload from stock_records')]}
payload['preferences']=[dict(r) for r in c.execute('select account_id,system,payload from user_preferences')] if c.execute("select 1 from sqlite_master where name='user_preferences'").fetchone() else []
with open(sys.argv[2],'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False)
print('Exported',len(payload['workspace']),'workspaces,',len(payload['accounts']),'accounts,',len(payload['documents']),'documents')
