import hashlib
import json
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPConnection
from pathlib import Path

import serve


class WorkspaceConcurrency(unittest.TestCase):
    def test_competing_creates_are_persisted_with_distinct_numbers_after_rebase(self):
        with tempfile.TemporaryDirectory() as folder:
            original = serve.DB
            self.addCleanup(setattr, serve, 'DB', original)
            serve.DB = Path(folder) / 'test.sqlite3'
            serve.prepare_database()
            with serve.connect() as connection:
                account = connection.execute(
                    "SELECT id,user_id FROM accounts WHERE role='System Admin' AND disabled=0"
                ).fetchone()
                self.assertIsNotNone(account)
                for token in ('first-test-session', 'second-test-session'):
                    connection.execute('INSERT INTO sessions VALUES (?,?,?,?)', (
                        hashlib.sha256(token.encode()).hexdigest(), account[0],
                        int(time.time()) + 600, int(time.time()),
                    ))

            class QuietHandler(serve.Handler):
                def log_message(self, *args):
                    pass

            server = serve.ThreadingHTTPServer(('127.0.0.1', 0), QuietHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                self.exercise(server.server_port, account[1])
            finally:
                server.shutdown()
                thread.join()
                server.server_close()

    def exercise(self, port, owner):
        def request(token, body=None):
            conn = HTTPConnection('127.0.0.1', port, timeout=10)
            try:
                headers = {'Cookie': 'biomed_session=' + token, 'Content-Type': 'application/json'}
                conn.request('GET' if body is None else 'PUT', '/api/storage/' + serve.IS_KEY,
                             body=None if body is None else json.dumps(body), headers=headers)
                response = conn.getresponse()
                return response.status, json.loads(response.read())
            finally:
                conn.close()

        tokens = ['first-test-session', 'second-test-session']
        status, snapshot = request(tokens[0])
        self.assertEqual(status, 200)
        barrier = threading.Barrier(2)

        def create(index):
            workspace = json.loads(snapshot['value'] or '{}')
            document = dict(id=f'quote-{index}', kind='quotation', ref='PROVISIONAL/1',
                            status='Draft', owner=owner, lines=[])
            workspace.setdefault('documents', []).append(document)
            barrier.wait(timeout=5)
            return request(tokens[index], dict(revision=snapshot['revision'], value=json.dumps(workspace))), document

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(create, range(2)))
        self.assertEqual(sorted(result[0][0] for result in results), [200, 409], results)

        loser = next(i for i, result in enumerate(results) if result[0][0] == 409)
        status, latest = request(tokens[loser])
        self.assertEqual(status, 200)
        workspace = json.loads(latest['value'])
        workspace['documents'].append(results[loser][1])
        status, saved = request(tokens[loser], dict(revision=latest['revision'], value=json.dumps(workspace)))
        self.assertEqual(status, 200, saved)

        with serve.connect() as connection:
            rows = connection.execute(
                "SELECT id,reference FROM documents WHERE kind='quotation' ORDER BY id"
            ).fetchall()
        self.assertEqual([row[0] for row in rows], ['quote-0', 'quote-1'])
        self.assertEqual(len({row[1] for row in rows}), 2)
