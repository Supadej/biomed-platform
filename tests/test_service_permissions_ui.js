const fs=require('fs'),vm=require('vm'),assert=require('assert');const elements={};const c={console,Intl,Date,location:{search:''},URLSearchParams,document:{getElementById:id=>elements[id]||=( {innerHTML:'',textContent:'',dataset:{}})}};vm.createContext(c);let code=fs.readFileSync(__dirname+'/../instrument-service.js','utf8').replace(/load\(\);\s*$/,'');vm.runInContext(code,c);
const all=JSON.parse(fs.readFileSync(__dirname+'/../permissions-catalog.json')).permissions.map(x=>x.key);c.grants=all;
vm.runInContext("state={records:[],masters:{},permissions:grants,audit:[]};render()",c);assert(elements.app.innerHTML.includes('+ New Instruments'));
vm.runInContext("state.permissions=['service.view','service.instruments.view'];render()",c);assert(!elements.app.innerHTML.includes('+ New'));assert(!elements.app.innerHTML.includes('Preview workbook import'));assert(!elements.app.innerHTML.includes('Export filtered CSV'));
console.log('PASS: service admin render; viewer controls hide create, export and import.');

const page=fs.readFileSync(__dirname+'/../instrument-service.html','utf8');assert(!page.includes('<header'));assert(!page.includes('class="bm-header-links"'));assert(page.includes('location.replace('));assert(!code.includes("document.querySelector('header').style"));
console.log('PASS: redundant service header removed; direct links route through Staff Portal; no header re-insertion.');
