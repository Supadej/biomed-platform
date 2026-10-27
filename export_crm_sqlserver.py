"""Export CRM tables as SQL Server 2012 staging inserts; no account credentials exported.
Usage: python3 export_crm_sqlserver.py --database data/biomed.sqlite3 --output CRM_Data.sql
Review the output and run crm_sqlserver2012.sql first on an EMPTY staging target.
This utility does not connect to or modify SQL Server, or implement a runtime adapter.
"""
import argparse,sqlite3
from pathlib import Path
TABLES=[('crm_records','CrmRecords'),('crm_identity','CrmIdentity'),('crm_audit','CrmAudit'),('crm_files','CrmFiles'),('crm_links','CrmLinks'),('crm_bridge_config','CrmBridgeConfig'),('crm_bridge_runs','CrmBridgeRuns')]
def literal(value):
 if value is None:return 'NULL'
 if isinstance(value,bytes):return '0x'+value.hex()
 if isinstance(value,(int,float)):return str(value)
 return "N'"+str(value).replace("'","''")+"'"
def export(database,output):
 database=Path(database).resolve();output=Path(output).resolve()
 if output==database:raise ValueError('Choose a separate output SQL path')
 if not database.is_file():raise ValueError('Database does not exist')
 with sqlite3.connect(database.as_uri()+'?mode=ro',uri=True) as c:
  c.execute('BEGIN');lines=['-- CRM staging export; no login credentials or sessions.','SET XACT_ABORT ON;','BEGIN TRANSACTION;'];counts={}
  for source,target in TABLES:
   if not c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(source,)).fetchone():counts[source]=0;continue
   rows=c.execute('SELECT * FROM '+source).fetchall();counts[source]=len(rows)
   for row in rows:lines.append('INSERT INTO dbo.'+target+' VALUES('+','.join(literal(x) for x in row)+');')
  lines.append('COMMIT TRANSACTION;');output.write_text('\n'.join(lines)+'\n',encoding='utf-8');return counts
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--database',default='data/biomed.sqlite3');p.add_argument('--output',default='CRM_Data.sql');args=p.parse_args();print(export(args.database,args.output))
