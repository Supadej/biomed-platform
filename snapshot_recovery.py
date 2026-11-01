"""Explicit, one-time recovery to mounted storage. Never replace an existing DB."""
import datetime,hashlib,json,os,sqlite3,tempfile
from pathlib import Path

def mounted_destination(database):
 raw=os.environ.get('RAILWAY_VOLUME_MOUNT_PATH','')
 if not raw:raise RuntimeError('Recovery requires an attached Railway volume mounted at /data. No volume mount was reported.')
 mount=Path(raw).resolve();database=Path(database).resolve()
 if not os.path.ismount(mount):raise RuntimeError('The reported volume path is not a mounted filesystem. Recovery stopped.')
 if database==mount or not database.is_relative_to(mount):raise RuntimeError('BIOMED_DATABASE_PATH must be inside the attached Railway volume.')
 return mount

def recover_if_requested(root,database):
 if os.environ.get('BIOMED_RECOVER_BUNDLED_SNAPSHOT')!='1':return False
 database=Path(database).resolve();mounted_destination(database)
 # Existing files, even empty or invalid ones, must never be replaced automatically.
 if database.exists():return False
 marker=database.parent/'snapshot-recovery-v76.json'
 if marker.exists():raise RuntimeError('Snapshot recovery already ran on this volume. Database is now missing; restore a current backup rather than replaying the old snapshot.')
 source=Path(root)/'data'/'biomed.sqlite3';manifest=json.loads((Path(root)/'recovery-snapshot-manifest.json').read_text())
 digest=hashlib.sha256(source.read_bytes()).hexdigest()
 if digest!=manifest['sha256']:raise RuntimeError('Recovery snapshot checksum mismatch. No database was restored.')
 database.parent.mkdir(parents=True,exist_ok=True)
 fd,name=tempfile.mkstemp(prefix='recovery-',suffix='.sqlite3',dir=database.parent);os.close(fd);temporary=Path(name)
 try:
  with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as src,sqlite3.connect(temporary) as dst:
   if src.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise RuntimeError('Recovery snapshot failed its integrity check')
   src.backup(dst)
   if dst.execute('PRAGMA quick_check').fetchone()[0]!='ok' or dst.execute('SELECT count(*) FROM accounts').fetchone()[0]<1:raise RuntimeError('Restored snapshot failed verification')
  # link is an atomic create-if-absent; concurrent startups cannot overwrite a DB.
  with temporary.open('rb') as f:os.fsync(f.fileno())
  try:os.link(temporary,database)
  except FileExistsError:return False
  with marker.open('x') as f:
   json.dump({'restoredAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceSha256':digest,'source':'Uploaded GitHub snapshot; partial recovery, not verified live backup'},f,indent=2);f.flush();os.fsync(f.fileno())
  print('Recovered supplied GitHub snapshot into persistent storage. Existing database files are never overwritten.',flush=True)
  return True
 finally:
  temporary.unlink(missing_ok=True)
