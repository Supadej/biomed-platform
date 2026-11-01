import unittest,json,sys,tempfile,sqlite3,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import permissions_policy as policy
class Startup(unittest.TestCase):
 def test_seed_roles_migrate_without_legacy_and_repeat_is_noop(self):
  data=json.loads((Path(__file__).resolve().parents[1]/'portal-seed-base.json').read_text())
  self.assertTrue(any('legacy' not in p for p in policy.CATALOG['permissions']))
  self.assertTrue(policy.migrate_portal(data))
  self.assertFalse(policy.migrate_portal(data))
  admin=data['roles']['System Admin'];self.assertIn('ai.internal.use',admin)
  self.assertNotIn('ai.settings.manage',data['roles']['Employee'])
 def test_packaged_database_initializes(self):
  import serve
  old=serve.DB
  try:
   with tempfile.TemporaryDirectory() as folder:
    serve.DB=Path(folder)/'test.sqlite3';shutil.copy2(Path(__file__).resolve().parents[1]/'data/biomed.sqlite3',serve.DB)
    serve.initialize();serve.initialize()
    with serve.connect() as c:self.assertEqual(c.execute('pragma integrity_check').fetchone()[0],'ok')
  finally:serve.DB=old
if __name__=='__main__':unittest.main()
