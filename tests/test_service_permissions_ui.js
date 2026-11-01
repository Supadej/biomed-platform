const fs=require('fs'),vm=require('vm'),assert=require('assert');const elements={};const c={window:{addEventListener(){}},console,Intl,Date,location:{search:''},URLSearchParams,document:{getElementById:id=>elements[id]||=( {innerHTML:'',textContent:'',dataset:{}})}};vm.createContext(c);let code=fs.readFileSync(__dirname+'/../instrument-service.js','utf8').replace(/^load\(\);/m,'');vm.runInContext(code,c);
const all=JSON.parse(fs.readFileSync(__dirname+'/../permissions-catalog.json')).permissions.map(x=>x.key);c.grants=all;
vm.runInContext("state={records:[],masters:{},permissions:grants,audit:[]};render()",c);assert(elements.app.innerHTML.includes('+ New Instruments'));
vm.runInContext("state.permissions=['service.view','service.instruments.view'];render()",c);assert(!elements.app.innerHTML.includes('+ New'));assert(!elements.app.innerHTML.includes('Preview workbook import'));assert(!elements.app.innerHTML.includes('Export filtered CSV'));
console.log('PASS: service admin render; viewer controls hide create, export and import.');

const page=fs.readFileSync(__dirname+'/../instrument-service.html','utf8');assert(!page.includes('<header'));assert(!page.includes('class="bm-header-links"'));assert(page.includes('location.replace('));assert(!code.includes("document.querySelector('header').style"));
console.log('PASS: redundant service header removed; direct links route through Staff Portal; no header re-insertion.');

assert(page.includes('min-width:112px'));assert(page.includes('white-space:nowrap!important'));assert(page.includes('margin:12px 0 22px!important'));assert(page.includes('max-width:none;width:100%'));
const host=fs.readFileSync(__dirname+'/../index.html','utf8');assert(host.includes("event.source!==frame.contentWindow"));assert(host.includes('biomed-service-height'));
console.log('PASS: full-width host resizing, explicit action/table gap and non-wrapping Details control.');

vm.runInContext("state={records:[],masters:{},permissions:grants,audit:[],columnPreferences:{}};tab='jobs';render()",c);
assert(elements.app.innerHTML.includes('<th>Job No.</th>'));assert(elements.app.innerHTML.includes('<th>Serial No./Brand/Model</th>'));assert(elements.app.innerHTML.includes('<th>Job Type</th>'));
vm.runInContext("state.columnPreferences.jobs=[{key:'status',label:'Work status'},{key:'jobNo',label:'Job reference'}];render()",c);
assert(elements.app.innerHTML.indexOf('<th>Work status</th>')<elements.app.innerHTML.indexOf('<th>Job reference</th>'));
vm.runInContext("tab='movements';render()",c);assert(elements.app.innerHTML.includes('<th>From Location</th>'));assert(elements.app.innerHTML.includes('<th>To Location</th>'));
vm.runInContext("tab='parts';render()",c);assert(elements.app.innerHTML.includes('<th>Catalogue No</th>'));assert(elements.app.innerHTML.includes('<th>Name</th>'));
vm.runInContext("tab='replacements';render()",c);assert(elements.app.innerHTML.includes('<th>Qty</th>'));assert(elements.app.innerHTML.includes('<th>Part replaced Catalogue No / Name</th>'));
vm.runInContext("tab='contracts';render()",c);assert(elements.app.innerHTML.includes('<th>Start Date</th>'));assert(elements.app.innerHTML.includes('<th>End Date</th>'));
console.log('PASS: exact per-tab defaults, renamed headings, saved ordering and independent tab layouts.');
