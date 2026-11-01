/* UI translation only: database values, input values and option codes remain unchanged. */
window.BiomedLanguage=(()=>{
 const request=new XMLHttpRequest();request.open('GET','ui-translations-th.json?v=financial-38',false);request.send(null);const dict=request.status===200?JSON.parse(request.responseText):{};
 const normal=s=>String(s).replace(/\s+/g,' ').trim();let active='en',observer,scheduled=false;const originals=new WeakMap(),placeholders=new WeakMap();
 try{active=BiomedStorage.getItem('biomed_ui_lang')==='th'?'th':'en'}catch{}
 function thai(value){const key=normal(value);if(dict[key])return dict[key];const lead=key.match(/^([^\p{L}\p{N}]+)(.+)$/u);if(lead&&dict[normal(lead[2])])return lead[1]+dict[normal(lead[2])];const record=key.match(/^(.+?) records$/);if(record&&dict[record[1]])return '\u0e23\u0e32\u0e22\u0e01\u0e32\u0e23'+dict[record[1]];const count=key.match(/^(.+?)\s*(\(\d+\)|[\u00b7:]\s*\d+.*)$/);if(count&&dict[normal(count[1])])return dict[normal(count[1])]+' '+count[2];return value}
 function eligible(p){if(!p||p.closest('script,style,noscript,textarea,[contenteditable], [data-no-translate],.bm-db-suggestions,.sysuser,#session-user,.budget-role'))return false;const cell=p.closest('td');if(cell&&!p.closest('button,.tag,.pill'))return false;if(p.closest('.bm-brand-group label,.bm-brand-group b'))return false;return true}
 function apply(){scheduled=false;if(!document.body)return;observer?.disconnect();
 // HTML option values otherwise follow translated text; pin their original codes first.
 for(const option of document.querySelectorAll('option'))if(!option.hasAttribute('value'))option.setAttribute('value',option.value);
 const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let node;while(node=walker.nextNode()){if(!eligible(node.parentElement)||!normal(node.nodeValue))continue;let entry=originals.get(node);if(!entry||node.nodeValue!==entry.en&&node.nodeValue!==entry.th){const en=node.nodeValue,key=normal(en),translated=thai(key);entry={en,th:translated===key?en:en.match(/^\s*/)[0]+translated+en.match(/\s*$/)[0]};originals.set(node,entry)}const wanted=entry[active];if(node.nodeValue!==wanted)node.nodeValue=wanted;}
 for(const input of document.querySelectorAll('input[placeholder],textarea[placeholder]')){if(!placeholders.has(input))placeholders.set(input,input.placeholder);input.placeholder=active==='th'?thai(placeholders.get(input)):placeholders.get(input);}
 document.documentElement.lang=active;const button=(document.getElementById('biomed-system-language')||document.getElementById('langBtn'));if(button){button.textContent=active==='th'?'\u0e44\u0e17\u0e22 / EN':'EN / \u0e44\u0e17\u0e22';button.setAttribute('aria-label',active==='th'?'Switch to English':'\u0e40\u0e1b\u0e25\u0e35\u0e48\u0e22\u0e19\u0e40\u0e1b\u0e47\u0e19\u0e20\u0e32\u0e29\u0e32\u0e44\u0e17\u0e22');button.setAttribute('aria-pressed',String(active==='th'));}
 observer?.observe(document.body,{childList:true,subtree:true,characterData:true});
 }
 function schedule(){if(!scheduled){scheduled=true;requestAnimationFrame(apply)}}
 function set(lang){active=lang==='th'?'th':'en';try{BiomedStorage.setItem('biomed_ui_lang',active)}catch{}apply()}
 function init(){observer=new MutationObserver(schedule);apply()}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
 return {set,get:()=>active,toggle:()=>set(active==='en'?'th':'en'),translateText:thai};
})();
