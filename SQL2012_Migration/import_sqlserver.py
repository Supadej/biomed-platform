"""Load exported workspace data into SQL Server 2012 (requires pyodbc)."""
import json,os,sys,pyodbc
if len(sys.argv)!=2:raise SystemExit('Usage: python import_sqlserver.py biomed-transfer.json')
connection=os.environ.get('BIOMED_SQLSERVER_CONNECTION')
if not connection:raise SystemExit('Set BIOMED_SQLSERVER_CONNECTION securely before running.')
data=json.load(open(sys.argv[1],encoding='utf-8'));cn=pyodbc.connect(connection);cur=cn.cursor()
cur.execute('SET XACT_ABORT ON; BEGIN TRANSACTION;')
for row in data['workspace']:
 cur.execute('IF EXISTS(SELECT 1 FROM dbo.BiomedWorkspace WHERE WorkspaceKey=?) UPDATE dbo.BiomedWorkspace SET Payload=?,Revision=?,UpdatedAt=SYSUTCDATETIME() WHERE WorkspaceKey=? ELSE INSERT dbo.BiomedWorkspace(WorkspaceKey,Payload,Revision) VALUES(?,?,?)',row['key'],row['value'],row['revision'],row['key'],row['key'],row['value'],row['revision'])
for a in data['accounts']:
 cur.execute('IF NOT EXISTS(SELECT 1 FROM dbo.BiomedAccount WHERE AccountId=?) INSERT dbo.BiomedAccount(AccountId,Email,DisplayName,RoleName,PortalUserId,PasswordHash,PasswordSalt,PasswordIterations,Disabled,FailedAttempts,LockedUntil,CreatedAt) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',a['id'],a['id'],a['email'],a['name'],a['role'],a['user_id'],bytes.fromhex(a['password_hash']),bytes.fromhex(a['salt']),a['iterations'],a['disabled'],a['failed_attempts'],a['locked_until'],a['created_at'])
for r in data.get('preferences',[]):
 cur.execute('IF EXISTS(SELECT 1 FROM dbo.BiomedUserPreference WHERE AccountId=? AND SystemName=?) UPDATE dbo.BiomedUserPreference SET Payload=? WHERE AccountId=? AND SystemName=? ELSE INSERT dbo.BiomedUserPreference(AccountId,SystemName,Payload) VALUES(?,?,?)',r['account_id'],r['system'],r['payload'],r['account_id'],r['system'],r['account_id'],r['system'],r['payload'])
# Index tables are rebuilt from canonical application workspaces during target runtime initialization.
cur.execute('COMMIT');cn.commit();print('Imported workspace data and account hashes. Restart/rebuild indexed projections with the SQL Server API adapter before serving traffic.')
