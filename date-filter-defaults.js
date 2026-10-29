/* Shared date-filter defaults. Creation forms and saved searches remain explicit. */
window.BiomedDateFilters=(()=>{
 const iso=d=>[d.getUTCFullYear(),String(d.getUTCMonth()+1).padStart(2,'0'),String(d.getUTCDate()).padStart(2,'0')].join('-');
 function today(now=new Date()){const parts=Object.fromEntries(new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Bangkok',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(now).map(x=>[x.type,x.value]));return new Date(Date.UTC(Number(parts.year),Number(parts.month)-1,Number(parts.day)))}
 function shift(day,months){const d=new Date(Date.UTC(day.getUTCFullYear(),day.getUTCMonth()+months,1));d.setUTCDate(Math.min(day.getUTCDate(),new Date(Date.UTC(d.getUTCFullYear(),d.getUTCMonth()+1,0)).getUTCDate()));return d}
 function range(now=new Date()){const day=today(now);return {from:iso(shift(day,-1)),to:iso(shift(day,1))}}
 function monthRange(now=new Date()){const r=range(now);return {from:r.from.slice(0,7),to:r.to.slice(0,7)}}
 function fiscalMonths(periods,now=new Date()){const r=monthRange(now),ix=periods.map((p,i)=>p>=r.from&&p<=r.to?i:-1).filter(i=>i>=0);return {from:ix.length?ix[0]:0,to:ix.length?ix.at(-1):-1}}
 return {range,monthRange,fiscalMonths};
})();
