const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const source = fs.readFileSync(require.resolve('../sqlite-storage.js'), 'utf8');
const key = 'biomed_is_v50_transactions';
const a = {id:'a', subject:'Original'};
const b = {id:'b', subject:'Second document'};

function run({base, remote, local, busy = false}) {
  const alerts = [];
  const writes = [];
  let gets = 0;
  class Request {
    open(method) { this.method = method; }
    setRequestHeader() {}
    send(raw) {
      if (this.method === 'GET') {
        const first = gets++ === 0;
        this.status = 200;
        this.responseText = JSON.stringify({revision:first ? 1 : 2, value:JSON.stringify(first ? base : remote)});
      } else {
        const write = JSON.parse(raw);
        writes.push(write);
        const first = writes.length === 1;
        this.status = first ? busy ? 503 : 409 : 200;
        this.responseText = JSON.stringify(first && busy ? {code:'workspace_busy'} : {revision:3, value:write.value});
      }
    }
  }
  const window = {};
  vm.runInNewContext(source, {window, XMLHttpRequest:Request, alert:message=>alerts.push(message)});
  window.BiomedStorage.getItem(key);
  try {
    return {saved:JSON.parse(window.BiomedStorage.setItem(key, JSON.stringify(local))), writes, alerts};
  } catch (error) {
    return {error, writes, alerts};
  }
}

const separate = run({base:{documents:[]},remote:{documents:[a]},local:{documents:[b]}});
assert.deepEqual(separate.saved.documents, [b,a]);
assert.equal(separate.writes[1].revision, 2);

const conflict = run({base:{documents:[a]},remote:{documents:[{...a, subject:'Remote'}]},local:{documents:[{...a, notes:'Local'}]}});
assert.match(conflict.error.message, /document was changed/);
assert.equal(conflict.writes.length, 1);
assert.equal(conflict.alerts.length, 1);

const deletion = run({base:{documents:[a]},remote:{documents:[]},local:{documents:[{...a, subject:'Local'}]}});
assert.match(deletion.error.message, /document was changed/);
assert.equal(deletion.writes.length, 1);

const retry = run({base:{documents:[]},remote:null,local:{documents:[a]},busy:true});
assert.deepEqual(retry.saved.documents, [a]);
assert.deepEqual(retry.writes[0], retry.writes[1]);
