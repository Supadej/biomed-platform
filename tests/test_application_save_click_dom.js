const {JSDOM}=require('jsdom'),fs=require('fs'),assert=require('assert');
const wait=()=>new Promise(resolve=>setTimeout(resolve,20));
(async()=>{
 const d=new JSDOM('<main></main>',{url:'https://local.test/?portal=1',runScripts:'outside-only'}),w=d.window;
 w.HTMLElement.prototype.scrollIntoView=()=>{};w.confirm=()=>true;w.structuredClone=structuredClone;w.ResizeObserver=class{observe(){}disconnect(){}};w.HTMLCanvasElement.prototype.getContext=()=>null;
 let records=[],writes=0,rejectSave=false,rejectRefresh=false;
 const data=()=>({userId:'u1',permissions:['view','create','edit','assign'].map(k=>'application_service.'+k),specialists:[{id:'u1',name:'Specialist'}],customers:[{id:'c1',name:'Hospital',active:true}],products:['Diagnostics'],instruments:[],tickets:[],records:structuredClone(records)});
 w.fetch=async(url,options)=>{if(options?.body){writes++;const body=JSON.parse(options.body);if(rejectSave)return {ok:false,status:400,json:async()=>({error:'The report changed after signing. Clear the signature or ask the customer to sign the revised report.'})};await wait();const r={...body.record,id:'job1',reference:'BMDAS30-10-26/1',customer:'Hospital',version:(body.record.version||0)+1};records=[r];return {ok:true,json:async()=>({record:r})}}if(rejectRefresh)throw Error('Network unavailable');return {ok:true,json:async()=>data()}};
 for(const file of ['date-filter-defaults.js','service-lookups.js','application-signature.js','multi-select.js','application-service.js'])w.eval(fs.readFileSync(file,'utf8'));
 await w.ApplicationService.mount(w.document.querySelector('main'));const doc=w.document;
 doc.querySelector('[data-app-action=new]').click();let form=doc.querySelector('.app-form'),save=()=>form.querySelector('button[type=submit]').click();
 // Native button click must expose validation rather than silently refusing submit.
 save();assert.equal(writes,0);assert(!form.querySelector('[data-form-error]').hidden);assert(form.querySelector('[data-form-error]').textContent.includes('Customer / institution'));assert.equal(doc.activeElement,form.elements.customerId);
 form.elements.customerId.value='c1';form.elements.status.value='Completed';save();assert.equal(writes,0);assert(form.querySelector('[data-form-error]').textContent.includes('work performed'));
 form.elements.workPerformed.value='Operator training';form.elements.result.value='Training completed';save();save();await wait();await wait();assert.equal(writes,1);assert(doc.querySelector('[data-app-editor]').hidden);assert.equal(records[0].customerSignature,null);assert(doc.querySelector('[data-app-notice]').textContent.includes('Application job saved'));assert.equal(w.ApplicationService.dirty,false);
 // Edit persists version and re-enables Save after a server-side rejection.
 doc.querySelector('[data-app-action="edit:job1"]').click();form=doc.querySelector('.app-form');form.elements.topic.value='Revised topic';form.dispatchEvent(new w.Event('input',{bubbles:true}));rejectSave=true;save();await wait();assert.equal(writes,2);assert(!form.querySelector('[data-form-error]').hidden);assert(form.querySelector('[data-form-error]').textContent.includes('report changed'));assert(!form.querySelector('button[type=submit]').disabled);assert.equal(form.elements.topic.value,'Revised topic');assert(w.ApplicationService.dirty);
 rejectSave=false;save();await wait();await wait();assert.equal(records[0].version,2);assert.equal(records[0].topic,'Revised topic');
 // A successful save followed by refresh failure stays saved and cannot create a duplicate.
 doc.querySelector('[data-app-action="edit:job1"]').click();form=doc.querySelector('.app-form');form.elements.topic.value='Saved despite refresh failure';rejectRefresh=true;save();await wait();await wait();assert.equal(records[0].version,3);assert(doc.querySelector('[data-app-error]').textContent.includes('Application job saved'));assert(doc.querySelector('[data-app-record="job1"]'));assert(doc.querySelector('[data-app-editor]').hidden);
 d.window.close();console.log('PASS native Save clicks: required/Completed validation, create/edit, double-click protection, visible server errors, retry and refresh-failure recovery');
})().catch(error=>{console.error(error);process.exit(1)});
