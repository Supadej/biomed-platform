const {JSDOM}=require('jsdom'),fs=require('fs'),assert=require('assert');
const wait=()=>new Promise(r=>setTimeout(r,15));
async function scenario(shell,order,admin=true){
 const d=new JSDOM('<header class="bm-workspace-header"><nav class="bm-header-links"><a data-user-manual>User manual</a></nav></header>'+shell,{url:'https://local.test/',runScripts:'outside-only'}),w=d.window;
 w.fetch=async url=>({ok:url==='/api/auth/me'||admin,json:async()=>({adminSelfApprovalTesting:true})});
 for(const file of order)w.eval(fs.readFileSync(file,'utf8'));
 w.document.dispatchEvent(new w.Event('DOMContentLoaded'));await wait();
 const parent=w.document.querySelector('aside,.p-side');
 assert.equal(w.document.querySelectorAll('.bm-header-links [data-user-manual]').length,0);
 assert.equal(parent.querySelectorAll('[data-manual-access]').length,1);
 assert.equal(parent.querySelectorAll('.bm-admin-menu').length,1);
 assert.equal(parent.querySelector('[data-manual-access]').className,'bm-admin-link');
 if(admin){assert.equal(parent.querySelectorAll('[data-database-access]').length,1);assert.equal(parent.querySelectorAll('.bm-admin-menu a')[0].textContent,'Database administration')}
 else assert.equal(parent.querySelectorAll('[data-database-access]').length,0);
 parent.replaceChildren();await wait();
 assert.equal(parent.querySelectorAll('[data-manual-access]').length,1);
 assert.equal(parent.querySelectorAll('.bm-admin-menu').length,1);
 d.window.close();
}
(async()=>{
 for(const shell of ['<div id="portal" class="active"><aside class="p-side"></aside></div>','<div class="layout"><aside></aside></div>','<div class="shell"><aside></aside></div>']){
  await scenario(shell,['manual-access.js','database-access.js']);
  await scenario(shell,['database-access.js','manual-access.js']);
  await scenario(shell,['manual-access.js','database-access.js'],false);
 }
 const d=new JSDOM(fs.readFileSync('user-manual.html','utf8'));const header=d.window.document.querySelector('header');
 assert(header.querySelector('#biomed-system-language.sysbtn'));
 assert(header.querySelector('.bm-header-signout.sysbtn'));
 assert(header.querySelector('#account.sysuser'));
 assert([...header.querySelectorAll('nav a')].every(a=>a.classList.contains('sysbtn')));
 assert.equal(header.querySelectorAll('a[data-user-manual]').length,0);d.window.close();
 console.log('PASS shared manual header; sidebar links across three workspaces; either load order; redraw persistence; readers without database grants');
})().catch(e=>{console.error(e);process.exit(1)});
