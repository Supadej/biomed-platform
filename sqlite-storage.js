/* SQLite workspace adapter with safe three-way merges for concurrent browser tabs. */
window.BiomedStorage = (() => {
  const revisions = new Map(), snapshots = new Map(), volatile = new Map();
  let blocked = false, authenticated = false;
  const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
  function parseStored(raw){if(raw===undefined||raw===null)return {value:null,json:false};try{return {value:JSON.parse(raw),json:true}}catch{return {value:raw,json:false}}}
  function merge(base,local,remote,path=[]){
    if(equal(local,base))return remote;
    if(equal(remote,base)||equal(local,remote))return local;
    if(path[0]==='documents'&&path.length===2){
      throw Error('This document was changed by another user. Your save did not go through. Copy your edits if needed, then reload the document.');
    }
    if(Array.isArray(base)&&Array.isArray(local)&&Array.isArray(remote)){
      const keyed=[...base,...local,...remote].every(x=>x&&typeof x==='object'&&!Array.isArray(x)&&x.id!==undefined);
      if(keyed){const bm=new Map(base.map(x=>[String(x.id),x])),lm=new Map(local.map(x=>[String(x.id),x])),rm=new Map(remote.map(x=>[String(x.id),x])),ids=new Set([...bm.keys(),...lm.keys(),...rm.keys()]),out=[];
        for(const id of ids){
          const record=merge(bm.get(id),lm.get(id),rm.get(id),[...path,id]);
          if(record!==undefined)out.push(record);
        }
        return out;
      }
      if(path[0]==='documents')throw Error('The document list changed. Your save did not go through. Reload before trying again.');
      const bs=new Set(base),ls=new Set(local),rs=new Set(remote);return [...new Set([...remote.filter(x=>!bs.has(x)),...local.filter(x=>!bs.has(x)),...base.filter(x=>ls.has(x)&&rs.has(x))])];
    }
    if(base&&local&&remote&&typeof base==='object'&&typeof local==='object'&&typeof remote==='object'){
      const out={};
      for(const k of new Set([...Object.keys(base),...Object.keys(local),...Object.keys(remote)])){
        const value=merge(base[k],local[k],remote[k],[...path,k]);
        if(value!==undefined)Object.defineProperty(out,k,{value,enumerable:true});
      }
      return out;
    }
    throw Error('Another user changed the same information. Your save did not go through. Copy your edits if needed, then reload.');
  }
  function xhr(method,key,body){const x=new XMLHttpRequest();x.open(method,'/api/storage/'+encodeURIComponent(key),false);if(body)x.setRequestHeader('Content-Type','application/json');try{x.send(body?JSON.stringify(body):null)}catch(e){throw Error('Cannot reach Biomed. Check your connection and verify whether the change was saved before retrying.')}return x}
  function explain(x,action){let detail='';try{detail=JSON.parse(x.responseText).error||''}catch{}if(x.status===0)return 'Cannot reach Biomed. Check your connection and verify whether the change was saved before retrying.';if(x.status===401)return 'Your sign-in session has expired. Sign in again, then retry the change.';if(x.status===403)return (detail||'Your account does not have permission for this action')+'. Reload the page before retrying.';return `${action} failed (HTTP ${x.status})${detail?': '+detail:''}. Reload the page before retrying.`}

  function request(method,key,value,operation){
    key=String(key);if(blocked&&method!=='GET')throw Error('Reload this page before saving again.');
    try{
      if(method==='GET'){const x=xhr('GET',key);if(x.status===401){if(authenticated)throw Error(explain(x,'Read'));return volatile.has(key)?volatile.get(key):null}if(x.status!==200)throw Error(explain(x,'Read'));authenticated=true;const result=JSON.parse(x.responseText);revisions.set(key,result.revision);snapshots.set(key,result.value);return result.value;}
      for(let attempt=0;attempt<3;attempt++){
        let x=xhr(method,key,{value,revision:revisions.get(key)||0,operation:operation||null});
        if(x.status===401){if(!authenticated){volatile.set(key,value);return value}throw Error(explain(x,'Save'))}
        if(x.status===503){
          let error;
          try{error=JSON.parse(x.responseText)}catch{}
          if(error?.code==='workspace_busy'&&attempt===0)continue;
          if(error?.code==='workspace_busy')throw Error('Biomed is busy saving other changes. Your save did not go through. Copy your edits if needed, then reload and try again.');
        }
        if(x.status===409){
          if(method==='DELETE'||operation)throw Error('This workspace changed. Your action did not go through. Reload before trying again.');
          const fresh=xhr('GET',key);
          if(fresh.status!==200)throw Error(explain(fresh,'Refresh'));
          const latest=JSON.parse(fresh.responseText);
          const base=parseStored(snapshots.get(key)),local=parseStored(value),remote=parseStored(latest.value);
          const merged=merge(base.value,local.value,remote.value);
          value=base.json||local.json||remote.json?JSON.stringify(merged):String(merged??'');
          revisions.set(key,latest.revision);
          snapshots.set(key,latest.value);
          continue;
        }
        if(x.status!==200)throw Error(explain(x,'Save'));const result=JSON.parse(x.responseText);revisions.set(key,result.revision);snapshots.set(key,result.value);return result.value;
      }
      throw Error('Several users changed this workspace. Your save did not go through. Copy your edits if needed, then reload and try again.');
    }catch(e){if(method==='GET')throw e;alert(e.message||'Save failed. Reload the page before retrying.');blocked=true;throw e;}
  }
  function getSession(){const x=new XMLHttpRequest();x.open('GET','/api/auth/me',false);x.send(null);if(x.status===401){authenticated=false;return null}if(x.status!==200)throw Error(explain(x,'Session check'));authenticated=true;return JSON.parse(x.responseText)}
  function getQuotationSnapshot(id='',range={}){const x=new XMLHttpRequest();x.open('GET','/api/portal/quotation-snapshot?'+new URLSearchParams(id?{id}:{from:range.from??'',to:range.to??''}),false);x.send(null);if(x.status===404){const raw=request('GET','biomed_is_v50_transactions');return raw?JSON.parse(raw):null}if(x.status!==200)throw Error(explain(x,'Quotation read'));return JSON.parse(x.responseText)}
  return {getQuotationSnapshot,getItem:key=>request('GET',key),setItem:(key,value,operation)=>request('PUT',key,String(value),operation),removeItem:key=>request('DELETE',key,null),setAuthenticated:value=>{authenticated=!!value},getSession};
})();
