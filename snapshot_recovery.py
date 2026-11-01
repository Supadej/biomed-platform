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
