import hashlib,json,os,sqlite3,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import snapshot_recovery as recovery
class Recovery(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'app';(self.root/'data').mkdir(parents=True);self.volume=Path(self.tmp.name)/'volume';self.volume.mkdir();self.db=self.volume/'biomed.sqlite3';self.source=self.root/'data'/'biomed.sqlite3'
  with sqlite3.connect(self.source) as c:c.execute('create table accounts(id text)');c.execute("insert into accounts values('preserved-user')")
  (self.root/'recovery-snapshot-manifest.json').write_text(json.dumps({'sha256':hashlib.sha256(self.source.read_bytes()).hexdigest()}))
 def tearDown(self):self.tmp.cleanup()
 def test_explicit_recovery_and_repeat_preservation(self):
  with patch.dict(os.environ,{'BIOMED_RECOVER_BUNDLED_SNAPSHOT':'1','RAILWAY_VOLUME_MOUNT_PATH':str(self.volume)}),patch('snapshot_recovery.os.path.ismount',return_value=True):
   self.assertTrue(recovery.recover_if_requested(self.root,self.db))
   with sqlite3.connect(self.db) as c:c.execute("insert into accounts values('new-user')")
   self.assertFalse(recovery.recover_if_requested(self.root,self.db))
   with sqlite3.connect(self.db) as c:self.assertEqual(c.execute('select count(*) from accounts').fetchone()[0],2)
   self.db.unlink()
   with self.assertRaisesRegex(RuntimeError,'already ran'):recovery.recover_if_requested(self.root,self.db)
 def test_no_opt_in_no_copy(self):
  with patch.dict(os.environ,{'BIOMED_RECOVER_BUNDLED_SNAPSHOT':'0'}):self.assertFalse(recovery.recover_if_requested(self.root,self.db));self.assertFalse(self.db.exists())
 def test_refuse_missing_volume_unmounted_wrong_path_and_checksum(self):
  with patch.dict(os.environ,{'BIOMED_RECOVER_BUNDLED_SNAPSHOT':'1','RAILWAY_VOLUME_MOUNT_PATH':''}):
   with self.assertRaises(RuntimeError):recovery.recover_if_requested(self.root,self.db)
  with patch.dict(os.environ,{'BIOMED_RECOVER_BUNDLED_SNAPSHOT':'1','RAILWAY_VOLUME_MOUNT_PATH':str(self.volume)}):
   with self.assertRaises(RuntimeError):recovery.recover_if_requested(self.root,self.db)
   with patch('snapshot_recovery.os.path.ismount',return_value=True):
    with self.assertRaises(RuntimeError):recovery.recover_if_requested(self.root,self.root/'bad.sqlite3')
    (self.root/'recovery-snapshot-manifest.json').write_text('{"sha256":"bad"}')
    with self.assertRaisesRegex(RuntimeError,'checksum'):recovery.recover_if_requested(self.root,self.db)
  self.assertFalse(self.db.exists())
if __name__=='__main__':unittest.main()
