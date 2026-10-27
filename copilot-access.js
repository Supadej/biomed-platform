(async()=>{
const $=id=>document.getElementById(id),message=t=>$('message').textContent=t;
const api=async(path,data)=>{const r=await fetch('/api/ai/'+path,{method:data?'POST':'GET',headers:{'Content-Type':'application/json'},body:data?JSON.stringify(data):undefined,cache:'no-store'});const d=await r.json();if(!r.ok){const e=Error(d.error||'Request failed');e.status=r.status;throw e;}return d;};
const labels={enabled:'Enable Copilot for my account',personal_key:'Allow my personal API key',company_key:'Allow company internal API key',share_summary:'Share permitted record summaries with OpenAI',calendar_read:'Read my authorised Staff Portal Calendar (OpenAI)',calendar_draft:'Prepare Calendar drafts for confirmation (OpenAI)'};
let catalog=[];
const modules={portal:'Staff Portal',is:'Biomed IS',budget:'Budgeting',developer:'Developer guidance'};
function field(parent,key,title,value,disabled){const label=document.createElement('label'),input=document.createElement('input'),span=document.createElement('span');input.type='checkbox';input.dataset.key=key;input.checked=value&&!disabled;input.disabled=disabled;span.textContent=title;label.append(input,span);parent.append(label);}
function render(id,values,ceiling,role,items=catalog,self=false){
 const parent=$(id);parent.replaceChildren();
 for(const [k,title] of Object.entries(labels))field(parent,k,id==='my-fields'?title:title.replace('my account',id==='role-fields'?'this role':'this employee').replace('my personal','personal'),values[k],ceiling&&!ceiling[k]);
 for(const [k,title] of Object.entries(modules))field(parent,'module:'+k,title,values.modules.includes(k),role&&(!role.includes(k)||!ceiling.modules.includes(k)));
 const box=document.createElement('section');box.className='function-list';
 const heading=document.createElement('h3');heading.textContent='Function access limits';box.append(heading);
 const search=document.createElement('input');search.type='search';search.className='function-search';search.placeholder='Find a function';search.setAttribute('aria-label','Filter function access');box.append(search);
 for(const [title,checked] of [['Select all available functions',true],['Clear function selection',false]]){const button=document.createElement('button');button.type='button';button.textContent=title;button.onclick=()=>box.querySelectorAll('input[data-function]:not(:disabled)').forEach(i=>i.checked=checked);box.append(button);}
 const groups=[];
 for(const system of ['portal','is','budget']){
  const details=document.createElement('details');details.open=system==='portal';const summary=document.createElement('summary');summary.textContent=modules[system];details.append(summary);
  for(const item of items.filter(i=>i.system===system)){
   const label=document.createElement('label'),check=document.createElement('input'),text=document.createElement('span'),small=document.createElement('small');
   check.type='checkbox';check.dataset.function=item.id;
   const allowed=(!ceiling||ceiling.functions?.[item.id]!==false)&&(!self||item.role_allowed);
   check.disabled=!item.connected||!allowed;
   check.checked=item.connected&&allowed&&values.functions?.[item.id]!==false;
   text.textContent=item.label;small.textContent=item.mode+(self&&!item.role_allowed?' · Role does not permit access':'');
   text.append(small);label.append(check,text);details.append(label);groups.push(label);
  }box.append(details);
 }
 search.oninput=()=>{const q=search.value.toLowerCase();for(const label of groups)label.hidden=!label.textContent.toLowerCase().includes(q);if(q)box.querySelectorAll('details').forEach(d=>d.open=true);};
 parent.append(box);
}
function values(id){
 const value={modules:[],functions:{}};
 $(id).querySelectorAll('input[data-key]').forEach(i=>{if(i.dataset.key.startsWith('module:')){if(i.checked)value.modules.push(i.dataset.key.slice(7));}else value[i.dataset.key]=i.checked;});
 $(id).querySelectorAll('input[data-function]').forEach(i=>value.functions[i.dataset.function]=i.checked);
 return value;
}
async function mine(){const d=await api('internal/access');catalog=d.function_catalog;render('my-fields',d.preferences,d.admin_ceiling,d.role_modules,d.function_catalog,true);$('effective').textContent='Effective modules: '+(d.effective.modules.map(k=>modules[k]).join(', ')||'None')+'. Record summaries: '+(d.effective.share_summary?'enabled':'off')+'. Global AI service controls also apply.';}
let users=[];
function selection(){const user=users.find(u=>u.id===$('employee').value);if(user)render('admin-fields',user.access.user_ceiling,null,null,user.access.function_catalog);}
async function admins(){try{const d=await api('admin/user-access');users=d.items;const selected=$('employee').value;$('employee').replaceChildren();for(const u of users){const option=document.createElement('option');option.value=u.id;option.textContent=u.name+' · '+u.email+' · '+u.role+(u.disabled?' · disabled':'');$('employee').append(option);}if(users.some(u=>u.id===selected))$('employee').value=selected;$('admin').hidden=false;selection();}catch(e){if(e.status!==403)throw e;}}
$('employee').onchange=selection;
$('save').onclick=async()=>{try{await api('internal/access',values('my-fields'));await mine();message('Your Copilot access is saved.');}catch(e){message(e.message);}};
$('save-admin').onclick=async()=>{try{await api('admin/user-access',{account_id:$('employee').value,access:values('admin-fields')});await admins();await mine();message('Employee access limits saved.');}catch(e){message(e.message);}};
let roles=[];
function roleSelection(){const role=roles.find(r=>r.role===$('role').value);if(role)render('role-fields',role.ceiling,null,null);}
async function loadRoles(){try{const d=await api('admin/role-access');roles=d.items;const selected=$('role').value;$('role').replaceChildren();for(const r of roles){const option=document.createElement('option');option.value=r.role;option.textContent=r.role;$('role').append(option);}if(roles.some(r=>r.role===selected))$('role').value=selected;$('role-admin').hidden=false;roleSelection();}catch(e){if(e.status!==403)throw e;}}
$('role').onchange=roleSelection;
$('save-role').onclick=async()=>{try{await api('admin/role-access',{role:$('role').value,access:values('role-fields')});await loadRoles();await admins();await mine();message('Role Copilot limits saved.');}catch(e){message(e.message);}};
try{await mine();await admins();await loadRoles();}catch(e){message(e.message);}
})();
