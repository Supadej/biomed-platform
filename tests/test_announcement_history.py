import unittest,sqlite3,json,copy
import announcement_history as history
class History(unittest.TestCase):
 def test_server_versions_snapshots_acknowledgements_and_legacy(self):
  c=sqlite3.connect(':memory:');actor=('a','e','Editor','System Admin','u1')
  first={'id':'notice','title':'First','body':'Original','by':'HR','required':True,'version':200,'attachments':[],'acks':[]}
  new={'announcements':[first]};history.capture(c,{},new,actor);self.assertEqual(first['version'],1)
  old=copy.deepcopy(new);new['announcements'][0]['acks']=[{'user':'u2','version':1}];history.capture(c,old,new,actor);self.assertEqual(c.execute('select count(*) from announcement_revisions').fetchone()[0],1)
  old=copy.deepcopy(new);first.update(title='Revised',body='Updated',revisionReason='Clarified schedule',version=999);history.capture(c,old,new,actor)
  self.assertEqual(first['version'],2);self.assertEqual(first['acks'][0]['version'],1)
  rows=c.execute('select payload from announcement_revisions order by version').fetchall();self.assertEqual(json.loads(rows[0][0])['title'],'First');self.assertEqual(json.loads(rows[1][0])['title'],'Revised')
  legacy={'id':'old','version':5,'title':'Old','body':'Before','by':'HR'};updated=copy.deepcopy(legacy);updated['body']='After';history.capture(c,{'announcements':[legacy]},{'announcements':[updated]},actor)
  self.assertEqual([v for v, in c.execute("select version from announcement_revisions where announcement_id='old' order by version")],[5,6])
if __name__=='__main__':unittest.main()
