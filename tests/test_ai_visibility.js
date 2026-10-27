// The visibility observer must never observe mutations it makes to its own widget.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync(require('node:path').join(__dirname,'../ai-chat-widget.js'),'utf8');
const code=source.slice(source.indexOf("const portal=document.getElementById('portal');"),source.indexOf('setInterval(async()=>'));
assert.ok(code.includes('new MutationObserver'));
let callback,target,options,writes=0,visible=false,hidden=false;
const portal={};const root={get hidden(){return hidden},set hidden(v){hidden=v;writes++;if(target===root||options?.subtree)throw Error('Self-observing visibility loop');}};
vm.runInNewContext(code,{root,document:{getElementById:()=>portal},getComputedStyle:()=>({display:visible?'block':'none'}),MutationObserver:class{constructor(fn){callback=fn}observe(t,o){target=t;options=o}}});
assert.equal(target,portal);assert.equal(options.subtree,undefined);
visible=true;callback();assert.equal(root.hidden,true);assert.equal(writes,1);
for(let i=0;i<100;i++)callback();assert.equal(writes,1,'unchanged visibility must not write attributes');
visible=false;callback();assert.equal(root.hidden,false);assert.equal(writes,2);
assert.match(source,/#biomed-ai-chat\[hidden\]\{display:none!important\}/);
console.log('AI visibility regression passed: portal-only observer; no repeated hidden writes.');
