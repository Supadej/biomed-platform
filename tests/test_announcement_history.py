import unittest,sqlite3,json,copy
import announcement_history as history
class History(unittest.TestCase):
 def test_server_versions_snapshots_acknowledgements_and_legacy(self):
  c=sqlite3.connect(':memory:');actor=('a','e','Editor','System Admin','u1')
  first={'id':'notice','title':'First','body':'Original','by':'HR','required':True,'version':200,'attachments':[],'acks':[]}
  new={'announcements':[first]};history.capture(c,{},new,actor);self.assertEqual(first['version'],1)
  c.execute('CREATE TABLE workspace(key TEXT PRIMARY KEY,value TEXT,revision INTEGER)')
  c.execute('INSERT INTO workspace VALUES(?,?,1)',(history.PORTAL_KEY,json.dumps(new)))
  reader=('b','r','Reader','Employee','u2')
  status,result=history.acknowledge(c,reader,'notice',1);self.assertEqual(status,200)
  self.assertEqual(history.acknowledge(c,reader,'notice',1),(200,result))
  first['acks']=[result['acknowledgement']]
  old=copy.deepcopy(new);first['acks']=[];history.capture(c,old,new,actor)
  self.assertEqual(first['acks'],[result['acknowledgement']])
  self.assertEqual(c.execute('select count(*) from announcement_revisions').fetchone()[0],1)
  old=copy.deepcopy(new);first.update(title='Revised',body='Updated',revisionReason='Clarified schedule',version=999);history.capture(c,old,new,actor)
  self.assertEqual(first['version'],2);self.assertEqual(first['acks'][0]['version'],1)
  c.execute('UPDATE workspace SET value=?',(json.dumps(new),))
  self.assertEqual(history.acknowledge(c,reader,'notice',1)[0],409)
  self.assertEqual(history.acknowledge(c,reader,'notice',2)[0],200)
  persisted=json.loads(c.execute('SELECT value FROM workspace').fetchone()[0])
  self.assertEqual([a['version'] for a in persisted['announcements'][0]['acks']],[1,2])
  rows=c.execute('select payload from announcement_revisions order by version').fetchall();self.assertEqual(json.loads(rows[0][0])['title'],'First');self.assertEqual(json.loads(rows[1][0])['title'],'Revised')
  legacy={'id':'old','version':5,'title':'Old','body':'Before','by':'HR'};updated=copy.deepcopy(legacy);updated['body']='After';history.capture(c,{'announcements':[legacy]},{'announcements':[updated]},actor)
  self.assertEqual([v for v, in c.execute("select version from announcement_revisions where announcement_id='old' order by version")],[5,6])
if __name__=='__main__':unittest.main()
