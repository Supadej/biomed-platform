const {JSDOM}=require('jsdom'),fs=require('fs'),assert=require('assert');
const dom=new JSDOM('<style>'+fs.readFileSync('responsive-containment.css','utf8')+'</style><form><div id="first"></div><div id="second"></div><button id="next">Save</button></form>',{runScripts:'outside-only'}),w=dom.window,d=w.document;
w.eval(fs.readFileSync('service-lookups.js','utf8'));
const a=w.serviceLookup(d.querySelector('#first'),'instrumentId','Instrument',[{id:'i',name:'Analyzer'}]);
w.serviceLookup(d.querySelector('#second'),'ticketId','Ticket',[{id:'t',name:'Ticket'}]);
const input=a.parentElement.querySelector('[type=search]'),menu=a.parentElement.querySelector('[role=listbox]');input.focus();assert(!menu.hidden);assert.equal(w.getComputedStyle(menu).position,'absolute');
input.dispatchEvent(new w.KeyboardEvent('keydown',{key:'ArrowDown',bubbles:true}));assert(menu.contains(d.activeElement));d.activeElement.dispatchEvent(new w.KeyboardEvent('keydown',{key:'Escape',bubbles:true,cancelable:true}));assert(menu.hidden);assert.equal(d.activeElement,input);
input.blur();input.focus();menu.querySelector('[role=option]').click();assert.equal(a.value,'i');assert(menu.hidden);
input.blur();input.focus();d.querySelector('#second input[type=search]').focus();assert(menu.hidden);const other=d.querySelector('#second [role=listbox]');assert(!other.hidden);other.querySelector('button').focus();d.querySelector('#next').focus();assert(other.hidden);
dom.window.close();console.log('PASS reference menus float without normal-flow layout, selection, Escape and keyboard exit');
// Exercise the actual Service Job calendar renderer independently of inventory fetching.
const source=fs.readFileSync('service-workspace.js','utf8'),start=source.indexOf(" if(k==='jobs'){const area="),end=source.indexOf('\n let newTicketPanel=',start),block=source.slice(start,end);
const job=new JSDOM('<form><div class="form"></div><input name="date"><input name="scheduledDate"></form>',{runScripts:'outside-only'}),j=job.window;
j.k='jobs';j.r={date:'2020-01-01',scheduledDate:'2020-01-02'};j.old=null;j.form=j.document.querySelector('form');j.grid=j.document.querySelector('.form');j.state={permissions:['crm_view','crm.events.view','crm.events.create']};j.E=x=>x;
j.eval(block);let date=j.form.elements.calendarDate;assert(!date.readOnly);assert.equal(date.value,new Intl.DateTimeFormat('sv-SE',{timeZone:'Asia/Bangkok'}).format(new Date()));date.value='2026-11-12';j.form.elements.scheduledDate.value='2026-12-01';j.form.elements.scheduledDate.dispatchEvent(new j.Event('input'));assert.equal(date.value,'2026-11-12');j.grid.replaceChildren();j.r={calendarDate:'2026-11-12'};j.eval(block);assert.equal(j.form.elements.calendarDate.value,'2026-11-12');job.window.close();console.log('PASS Service Job calendar today default, editable selection and preserved edit date');
