/* Explicit view switching for authorized, filtered Staff Portal payloads. */
(function(scope){
function install({root,anchor,kind,view,render,onView}){
 if(!root||!anchor)return;
 let controls=root.querySelector('.deep-analysis-controls'),panel=root.querySelector('.deep-analysis-panel');
 if(!controls){
  controls=document.createElement('div');controls.className='p-tabs deep-analysis-controls';controls.setAttribute('role','tablist');controls.setAttribute('aria-label','Records or analysis');
  for(const [value,label] of [['records','Records'],['analysis','Analysis']]){const b=document.createElement('button');b.type='button';b.textContent=label;b.dataset.deepView=value;b.setAttribute('role','tab');controls.append(b)}
  anchor.after(controls);panel=document.createElement('section');panel.className='deep-analysis-panel';panel.id='portal-deep-analysis-'+kind;panel.setAttribute('role','tabpanel');panel.setAttribute('aria-label','Analysis');controls.after(panel);
 }
 const active=view==='analysis';
 for(const button of controls.querySelectorAll('button')){
  const selected=button.dataset.deepView===(active?'analysis':'records');button.classList.toggle('selected',selected);button.setAttribute('aria-selected',String(selected));button.setAttribute('aria-pressed',String(selected));button.setAttribute('aria-controls',panel.id);
  button.onclick=()=>onView(button.dataset.deepView);
 }
 for(let sibling=panel.nextElementSibling;sibling;sibling=sibling.nextElementSibling)sibling.classList.toggle('deep-records-hidden',active);
 panel.hidden=!active;
 if(active){
  try{panel.innerHTML=render()}catch(error){panel.innerHTML='';const message=document.createElement('p');message.setAttribute('role','alert');message.textContent='Analysis could not be displayed. Return to Records and refresh this view. '+String(error.message||error);panel.append(message)}
 }
 return panel;
}
scope.BiomedAnalysisViews={install};if(typeof module!=='undefined')module.exports={install};
})(globalThis);
