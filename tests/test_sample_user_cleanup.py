import json,sqlite3,unittest
import sample_user_cleanup as cleanup
import staff_directory

class CleanupTests(unittest.TestCase):
 def setUp(self):
  self.c=sqlite3.connect(':memory:')
  self.c.executescript('CREATE TABLE workspace(key TEXT PRIMARY KEY,value TEXT,revision INTEGER);CREATE TABLE accounts(user_id TEXT);')
  staff_directory.initialize(self.c)
 def test_exact_targets_preserve_records_and_registered_users(self):
  users=[dict(id=uid,email=email,name=uid) for uid,email in cleanup.TARGETS.items()]
  users += [dict(id='real',email='real@company.test',managerId='u3')]
  users[0]['email']='changed@company.test'  # Repurposed identity stays.
  self.c.execute('INSERT INTO accounts VALUES(?)',('u3',))
  documents=[dict(owner='u4',history=[dict(by='u5')])]
  self.c.execute('INSERT INTO workspace VALUES(?,?,7)',(cleanup.KEY,json.dumps(dict(users=users,requests=documents,roles={'Employee':['visits']}))))
  removed=cleanup.apply(self.c)
  self.assertEqual(len(removed),10)
  value,revision=self.c.execute('SELECT value,revision FROM workspace').fetchone();data=json.loads(value)
  self.assertEqual(data['requests'],documents)
  self.assertEqual({u['id'] for u in data['users']},{'u2','u3','real'})
  self.assertEqual(revision,8)
  self.assertEqual(cleanup.apply(self.c),[])
  self.assertEqual(self.c.execute('SELECT revision FROM workspace').fetchone()[0],8)
 def test_missing_workspace_retries_later(self):
  self.assertEqual(cleanup.apply(self.c),[])
  self.assertEqual(self.c.execute('SELECT count(*) FROM data_migrations').fetchone()[0],0)

