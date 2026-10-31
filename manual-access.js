/* Shared sidebar utility; readers do not need database privileges. */
document.addEventListener('DOMContentLoaded',async()=>{
 try{
  const r=await fetch('/api/auth/me',{cache:'no-store'});if(!r.ok)return;
  const icon='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M12 5c-3-2-7-2-10-1v15c3-1 7-1 10 1 3-2 7-2 10-1V4c-3-1-7-1-10 1Zm0 0v15"/></svg>';
  function add(){
   document.querySelectorAll('.bm-header-links [data-user-manual]').forEach(a=>a.remove());
   const parent=document.querySelector('#portal.active .p-side')||document.querySelector('body>.shell>aside,body>.layout>aside');
   if(!parent||parent.querySelector('[data-manual-access]'))return;
   let section=parent.querySelector('.bm-admin-menu');
   if(!section){section=document.createElement('section');section.className='bm-admin-menu';section.innerHTML='<small>Help & support</small>';parent.append(section)}
   const a=document.createElement('a');a.className='bm-admin-link';a.href='user-manual.html';a.dataset.manualAccess='';a.innerHTML=icon+'<span>User manual</span>';section.append(a);
  }
  add();new MutationObserver(add).observe(document.body,{childList:true,subtree:true});
 }catch{}
});
