import sys,sqlite3,json,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import serve,record_visibility as rv
class StaffConfiguration(unittest.TestCase):
 def test_imported_configuration_survives_restart_and_business_stays_empty(self):
  with tempfile.TemporaryDirectory() as directory:
   prior=serve.DB;serve.DB=Path(directory)/'configured.sqlite3'
   try:
    serve.prepare_database()
    with serve.connect() as c:
     self.assertEqual(c.execute('pragma integrity_check').fetchone()[0],'ok');self.assertFalse(c.execute('pragma foreign_key_check').fetchall())
     self.assertEqual(c.execute('select count(*) from accounts').fetchone()[0],44)
     portal=json.loads(c.execute("select value from workspace where key='biomed_portal_v33_clean'").fetchone()[0]);self.assertEqual(len(portal['users']),44);self.assertEqual(len(portal['roles']),29);self.assertEqual(len(portal['departments']),11)
     self.assertTrue(all(len(x)==62 for x in portal['roleRecordScopes'].values()))
     for table in ['masters','documents','stock_records','fse_records','crm_records','website_files','web_catalog','operational_brands','application_service_records','ai_chat_keys']:self.assertEqual(c.execute('select count(*) from '+table).fetchone()[0],0,table)
     for key in ['brands','productLines','requests','tasks','tickets','content']:self.assertEqual(portal[key],[],key)
     before=(portal['users'],portal['roles'],portal['roleRecordScopes'])
     c.execute("insert into workspace values('new-record-survives','{}',1)")
    serve.prepare_database()
    with serve.connect() as c:
     after=json.loads(c.execute("select value from workspace where key='biomed_portal_v33_clean'").fetchone()[0]);self.assertEqual(before,(after['users'],after['roles'],after['roleRecordScopes']));self.assertEqual(c.execute("select count(*) from workspace where key='new-record-survives'").fetchone()[0],1)
   finally:serve.DB=prior
if __name__=='__main__':unittest.main()
