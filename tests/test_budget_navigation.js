const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(require.resolve('../budget-governance.js'),'utf8');
class Node{
 constructor(){this.attrs={};this.hidden=false;this.details={open:false};this.body={innerHTML:''};this.buttons=[]}
 setAttribute(k,v){this.attrs[k]=v}removeAttribute(k){delete this.attrs[k]}
 set innerHTML(s){this.html=s;this.buttons=[...s.matchAll(/<button type="button" data-fin-view="([^"]+)">([^<]+)<\/button>/g)].map(m=>{const b=new Node();b.dataset={finView:m[1]};b.textContent=m[2];return b})}get innerHTML(){return this.html||''}
 querySelector(s){return s==='details'?this.details:this.body}querySelectorAll(){return this.buttons}
}
const sections=Object.fromEntries(['earnings','targets','monthly-budget','source-references','review','actuals','analysis'].map(k=>[k,new Node()]));let nav;
sections.targets.before=card=>{sections.earnings=card};
const root={querySelector:s=>s==='.bgov'?{prepend:n=>nav=n}:s==='#earnings [data-earnings-body]'?sections.earnings.body:sections[s.slice(1)]||null,querySelectorAll:()=>[]};
const ctx={root,document:{createElement:()=>new Node()},view:'setting',earningsOpen:false,lines:[],data:{current:[],governance:{}},months:[],BudgetEarnings:require('../budget-earnings.js'),money:String,E:String,has:()=>true};vm.createContext(ctx);
for(const name of ['earningsEditor','updateEarnings','separateViews']){const start=source.indexOf('function '+name+'('),end=source.indexOf('\nfunction ',start+10);vm.runInContext(source.slice(start,end),ctx)}
ctx.earningsEditor();assert.equal(sections.earnings.details.open,false,'Outlook starts collapsed');sections.earnings.details.open=true;sections.earnings.details.ontoggle();ctx.updateEarnings();assert.equal(sections.earnings.details.open,true,'Live totals do not close an expanded outlook');ctx.earningsEditor();assert.equal(sections.earnings.details.open,true,'Draw preserves user selection');
ctx.separateViews();assert.deepEqual(nav.buttons.map(b=>b.dataset.finView),['setting','actual','analysis','approval','monthly','review','references']);assert.equal((nav.innerHTML.match(/class="bgov-tab-row"/g)||[]).length,3);assert.match(nav.innerHTML,/data-tab-row="1"[^]*Annual Budget[^]*Actual Expense Recording[^]*Budget vs Actual/);
for(const button of nav.buttons){button.onclick();assert.equal(button.attrs['aria-pressed'],'true');assert.equal(button.attrs['aria-current'],'page');assert.equal(nav.buttons.filter(b=>b.attrs['aria-pressed']==='true').length,1)}
nav.buttons[2].onclick();assert.equal(sections.analysis.hidden,false);assert.equal(sections.earnings.hidden,false);assert.equal(sections.targets.hidden,true);
console.log('Three navigation rows, requested tab order, selected state, page visibility and collapsible outlook checks passed.');
