const assert=require('node:assert/strict');
class Element{
 constructor(){this.children=[];this.dataset={};this.attrs={};this.classes=new Set();this.classList={toggle:(c,on)=>on?this.classes.add(c):this.classes.delete(c),contains:c=>this.classes.has(c)}}
 set className(s){this._className=s;this.classes=new Set(s.split(' '))}get className(){return this._className||''}
 setAttribute(k,v){this.attrs[k]=v}append(child){child.parent=this;this.children.push(child)}
 after(child){child.parent=this.parent;this.parent.children.splice(this.parent.children.indexOf(this)+1,0,child)}
 get nextElementSibling(){return this.parent?.children[this.parent.children.indexOf(this)+1]}
 querySelector(sel){return this.children.find(x=>x.classList.contains(sel.slice(1)))}
 querySelectorAll(){return this.children}
 set innerHTML(s){this.html=s;this.children=[]}get innerHTML(){return this.html||''}
}
global.document={createElement:()=>new Element()};global.window=global;global.dispatchEvent=()=>{};
require('../portal-deep-analysis.js');const {install}=require('../portal-analysis-views.js');
for(const kind of ['sales','demos','tenders','pipeline']){
 const root=new Element(),anchor=new Element(),records=new Element();root.append(anchor);root.append(records);
 let view='records';const payload={targets:[{rep:'u1',line:'ALEX',period:'2026-11',amount:100}],actuals:[{rep:'u1',line:'ALEX',period:'2026-11',amount:70}],months:['2026-11'],rows:[],followups:{},name:x=>x};
 const update=()=>install({root,anchor,kind,view,render:()=>BiomedDeepAnalysis.render(kind,payload),onView:v=>{view=v;update()}});
 const panel=update(),controls=root.querySelector('.deep-analysis-controls');assert.equal(panel.hidden,true);assert.equal(controls.children[0].attrs['aria-selected'],'true');
 controls.children[1].onclick();assert.equal(view,'analysis');assert.equal(panel.hidden,false);assert.ok(panel.innerHTML.includes('da-'));assert.equal(records.classList.contains('deep-records-hidden'),true);assert.equal(controls.children[1].attrs['aria-pressed'],'true');
 controls.children[0].onclick();assert.equal(view,'records');assert.equal(panel.hidden,true);assert.equal(records.classList.contains('deep-records-hidden'),false);assert.equal(root.children.length,4,'Controls and panel are reused');
 view='analysis';install({root,anchor,kind,view,render:()=>{throw Error('test failure')},onView:()=>{}});assert.equal(panel.children[0].attrs.role,'alert');assert.match(panel.children[0].textContent,/test failure/);
}
console.log('Sales, demos, quotations and pipeline: click switching, active state, record visibility, rendered analysis and error feedback passed.');
// CRM analysis must not depend on sales-summary/target permissions or a redundant record fetch.
const fs=require('node:fs'),vm=require('node:vm'),source=fs.readFileSync(require.resolve('../portal-crm.js'),'utf8');
const loadSource=source.slice(source.indexOf('async function load(){'),source.indexOf('\nasync function projectFolders(){'));
const dest={innerHTML:'',setAttribute(){},removeAttribute(){}},message={},summary={};let analyticsCalls=0;
const context={root:{querySelector:s=>s==='.pc-results'?dest:s==='[data-error]'?message:summary},mode:'sales_plan',project:'',analysisMode:true,entity:'Leads',generation:0,page:1,search:'filtered',owner:'u1',line:'ALEX',remoteSortKey:'',remoteSortDirection:'desc',field:'',value:'',from:'2026-11-01',to:'2026-11-30',view:'table',syncViewButtons(){},can:()=>true,hasRecordDates:()=>true,crmAnalysis:async q=>{assert.equal(q.owner,'u1');assert.equal(q.line,'ALEX');analyticsCalls++;return '<h2>Filtered analysis</h2>'},api:async()=>{throw Error('Analysis should not call unrelated endpoints')},error:e=>{throw e}};
vm.createContext(context);vm.runInContext(loadSource,context);context.load().then(()=>{assert.equal(analyticsCalls,1);assert.match(dest.innerHTML,/Filtered analysis/);console.log('CRM analysis loads directly using its filters without unrelated sales-summary requests.');}).catch(e=>{console.error(e);process.exitCode=1});
