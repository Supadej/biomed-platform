const {JSDOM}=require(process.env.BIOMED_JSDOM_PATH||'jsdom'),fs=require('fs'),assert=require('assert'),path=require('path');
(async()=>{
const root=path.resolve(__dirname,'..'),dom=new JSDOM('<div id="root"></div>',{url:'http://localhost/',runScripts:'outside-only'}),w=dom.window;
w.HTMLElement.prototype.scrollIntoView=()=>{};
w.eval(fs.readFileSync(root+'/date-filter-defaults.js','utf8'));
let fail=false;
w.fetch=async url=>{const action=url.split('/native/')[1].split('?')[0];if(fail&&action==='list')throw Error('Simulated network error');return {ok:true,json:async()=>action==='meta'?{permissions:['events','leads','tickets','activities','projects','pipelines','ticket_stages','project_stages'].map(m=>'crm.'+m+'.view'),productLines:[]}:action==='project-folders'?[{Id:7,Name:'Test project',Description:'Folder test',stages:2,activities:3,version:1}]:action==='options'?[]:action==='workflow-board'?{columns:[],total:0,summary:null}:action==='sales-summary'?{}:{items:[],total:0,size:30}}};
w.eval(fs.readFileSync(root+'/portal-crm.js','utf8'));const host=w.document.getElementById('root');const pause=()=>new Promise(r=>setTimeout(r,20));
function selected(actions,expected){assert.deepEqual(actions.filter(a=>host.querySelector(`[data-action="${a}"]`)?.getAttribute('aria-pressed')==='true'),[expected]);}
await w.PortalCRM.mount(host,'calendar');
for(const action of ['day','week','table','month','day']){host.querySelector(`[data-action="${action}"]`).click();await pause();selected(['month','week','day','table'],action);}
fail=true;host.querySelector('[data-action="week"]').click();await pause();selected(['month','week','day','table'],'week');fail=false;
for(const mode of ['sales_plan','external_helpdesk','projects']){
 await w.PortalCRM.mount(host,mode);
 if(mode==='projects'){assert(host.textContent.includes('Project folders'));host.querySelector('[data-action=project-open]').click();await pause();assert(host.querySelector('[data-action=project-folders]'));}
 for(const action of ['table','board','table']){host.querySelector(`[data-action="${action}"]`).click();await pause();selected(['table','board'],action);}
 host.querySelector('[data-action="analytics-analysis"]').click();await pause();selected(['analytics-records','analytics-analysis'],'analytics-analysis');
 host.querySelector('[data-action="analytics-records"]').click();await pause();selected(['analytics-records','analytics-analysis'],'analytics-records');
}
console.log('PASS Calendar Month/Week/Day/Table, CRM Table/Board, Records/Analysis and failure-state selection');dom.window.close();
})().catch(e=>{console.error(e);process.exitCode=1});
