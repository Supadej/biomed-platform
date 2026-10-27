(async()=>{
const $=id=>document.getElementById(id),message=t=>$('message').textContent=t;
const api=async(path,data)=>{const r=await fetch('/api/ai/'+path,{method:data?'POST':'GET',headers:{'Content-Type':'application/json'},body:data?JSON.stringify(data):undefined,cache:'no-store'});const d=await r.json();if(!r.ok){const e=Error(d.error||'Request failed');e.status=r.status;throw e;}return d;};
const labels={enabled:'Enable Copilot for my account',personal_key:'Allow my personal API key',company_key:'Allow company internal API key',share_summary:'Share permitted record summaries with OpenAI'};
const modules={portal:'Staff Portal',is:'Biomed IS',budget:'Budgeting',developer:'Developer guidance'};
function field(parent,key,title,value,disabled){const label=document.createElement('label'),input=document.createElement('input'),span=document.createElement('span');input.type='checkbox';input.dataset.key=key;input.checked=value&&!disabled;input.disabled=disabled;span.textContent=title;label.append(input,span);parent.append(label);}
function render(id,values,ceiling,role){const parent=$(id);parent.replaceChildren();for(const [k,title] of Object.entries(labels))field(parent,k,title,values[k],ceiling&&!ceiling[k]);for(const [k,title] of Object.entries(modules))field(parent,'module:'+k,title,values.modules.includes(k),role&&(!role.includes(k)||!ceiling.modules.includes(k)));}
function values(id){const value={modules:[]};$(id).querySelectorAll('input').forEach(i=>{if(i.dataset.key.startsWith('module:')){if(i.checked)value.modules.push(i.dataset.key.slice(7));}else value[i.dataset.key]=i.checked;});return value;}
async function mine(){const d=await api('internal/access');render('my-fields',d.preferences,d.admin_ceiling,d.role_modules);$('effective').textContent='Effective modules: '+(d.effective.modules.map(k=>modules[k]).join(', ')||'None')+'. Record summaries: '+(d.effective.share_summary?'enabled':'off')+'. Global AI service controls also apply.';}
let users=[];
function selection(){const user=users.find(u=>u.id===$('employee').value);if(user)render('admin-fields',user.access.admin_ceiling,null,null);}
async function admins(){try{const d=await api('admin/user-access');users=d.items;const selected=$('employee').value;$('employee').replaceChildren();for(const u of users){const option=document.createElement('option');option.value=u.id;option.textContent=u.name+' · '+u.email+' · '+u.role+(u.disabled?' · disabled':'');$('employee').append(option);}if(users.some(u=>u.id===selected))$('employee').value=selected;$('admin').hidden=false;selection();}catch(e){if(e.status!==403)throw e;}}
$('employee').onchange=selection;
$('save').onclick=async()=>{try{await api('internal/access',values('my-fields'));await mine();message('Your Copilot access is saved.');}catch(e){message(e.message);}};
$('save-admin').onclick=async()=>{try{await api('admin/user-access',{account_id:$('employee').value,access:values('admin-fields')});await admins();await mine();message('Employee access limits saved.');}catch(e){message(e.message);}};
try{await mine();await admins();}catch(e){message(e.message);}
})();
