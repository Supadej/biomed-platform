/* Staff Portal header controls shared by the four native CRM routes. */
(function(){
 function init(){
  var user=document.getElementById('staff-crm-session-user');
  if(user)fetch('/api/auth/me',{credentials:'same-origin'}).then(function(r){return r.ok?r.json():null}).then(function(info){if(info)user.textContent=[info.name,info.role].filter(Boolean).join(' · ')}).catch(function(){});
  var out=document.getElementById('staff-crm-signout');
  if(out)out.addEventListener('click',function(){window.BiomedWorkspaceHeader.signout()});
  var lang=document.getElementById('staff-crm-language');
  if(lang)lang.addEventListener('click',function(){
    var current=document.documentElement.lang==='th'?'th':'en';
    var next=current==='th'?'en':'th';
    document.documentElement.lang=next;
    try{localStorage.setItem('biomed-language',next)}catch(e){}
    // Existing CRM language engine continues to translate the page.
    document.dispatchEvent(new CustomEvent('biomed-language-change',{detail:{language:next}}));
    if(window.BiomedLanguage&&typeof window.BiomedLanguage.setLanguage==='function')window.BiomedLanguage.setLanguage(next);
  });
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
