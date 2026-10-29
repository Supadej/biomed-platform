// Emulate DOM mutation delivery, including identical textContent assignments.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const html=fs.readFileSync(path.join(__dirname,'../index.html'),'utf8');
const code=html.match(/<script id="biomed-lang-v6">([\s\S]*?)<\/script>/)[1];
const frames=[],mutations=[];let observer,writes=0;
const changed=()=>{if(observer?.connected&&!mutations.length)mutations.push(()=>observer.callback());};
function button(initial){let value=initial;return {get textContent(){return value},set textContent(v){value=v;writes++;changed()}};}
const buttons={langBtn:button('EN / ไทย'),'bm31-language':button('EN / ไทย')};
const parent={tagName:'BUTTON',closest:()=>null};
const nodes=[{nodeValue:'Sign in',parentElement:parent}];
const context={document:{body:{},documentElement:{},querySelectorAll:()=>[],getElementById:id=>buttons[id],createTreeWalker:()=>{let i=0;return {nextNode:()=>nodes[i++]}}},NodeFilter:{SHOW_TEXT:4},BiomedStorage:{getItem:()=> 'en',setItem(){}},MutationObserver:class{constructor(fn){this.callback=fn;observer=this}observe(){this.connected=true}disconnect(){this.connected=false}},requestAnimationFrame:fn=>frames.push(fn)};
context.window=context;vm.runInNewContext(code,context);
function settle(){let steps=0;while(mutations.length||frames.length){assert.ok(++steps<10,'translation must settle instead of scheduling itself forever');while(mutations.length)mutations.shift()();if(frames.length)frames.shift()();}}
settle();assert.equal(writes,0,'unchanged labels should not be rewritten');
context.BiomedLanguage.set('th');settle();assert.equal(nodes[0].nodeValue,'เข้าสู่ระบบ');assert.equal(buttons.langBtn.textContent,'ไทย / EN');
nodes.push({nodeValue:'Save',parentElement:parent});changed();settle();assert.equal(nodes[1].nodeValue,'บันทึก');
context.BiomedLanguage.set('en');settle();assert.equal(nodes[0].nodeValue,'Sign in');assert.equal(nodes[1].nodeValue,'Save');
assert.ok(observer.connected,'watcher must reconnect for later page changes');
console.log('Login translation regression passed: stable labels, no observer feedback, dynamic EN/TH content.');
