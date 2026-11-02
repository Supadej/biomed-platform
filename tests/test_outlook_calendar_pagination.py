import unittest,tempfile,sqlite3,json,sys
from pathlib import Path
from contextlib import contextmanager
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import outlook_sync as outlook
class OutlookPagination(unittest.TestCase):
 def test_multiple_pages_and_dates_are_cached(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'db.sqlite3'
   @contextmanager
   def connect():
    with sqlite3.connect(path) as c:yield c
   with connect() as c:outlook.initialize(c)
   calls=[]
   def graph(token,url):
    calls.append(url);i=len(calls);day=f'2026-11-{i:02d}'
    r={'id':str(i),'subject':'Meeting '+str(i),'start':{'dateTime':day+'T09:00:00','timeZone':'Asia/Bangkok'},'end':{'dateTime':day+'T10:00:00','timeZone':'Asia/Bangkok'}}
    return {'value':[r],**({'@odata.nextLink':'https://graph.microsoft.com/v1.0/me/calendarView?page='+str(i+1)} if i<12 else {})}
   with patch.object(outlook,'graph',side_effect=graph):outlook.refresh_private(connect,'user','token')
   with connect() as c:
    rows=[json.loads(r[0]) for r in c.execute('select payload from outlook_private')];self.assertEqual(len(rows),12);self.assertEqual(len({r['start'][:10] for r in rows}),12)
   # A failed refresh never deletes the previously complete cache.
   with patch.object(outlook,'graph',side_effect=ValueError('Network failure')):
    with self.assertRaises(ValueError):outlook.refresh_private(connect,'user','token')
   with connect() as c:self.assertEqual(c.execute('select count(*) from outlook_private').fetchone()[0],12)
if __name__=='__main__':unittest.main()
