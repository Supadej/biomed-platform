window.BiomedPrint=function(d,db,m,title){
 const e=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const fmt=v=>typeof v==='number'?v.toLocaleString('en-US',{maximumFractionDigits:2,minimumFractionDigits:2}):e(v);
 const r=BiomedReportLayouts[d.kind]||{title,orientation:'Portrait',columns:['No.','Cat No.','Item / Description','Quantity','Unit','Unit Price','Amount']};
 const source=d.sourceFields||{};
 const fields=(obj,keys)=>{for(const key of keys){if(obj[key]!==undefined&&obj[key]!=='')return obj[key]}return ''};
 const party=db.customers.concat(db.suppliers).find(x=>x.id===d.party)||{};
 const partyName=fields(source,['txtcustomernamec','txtsuppliernamec','txtsuppliername'])||party.name||'';
 const address=fields(source,['txtAddressc','txtaddressc','txtaddresssupplier'])||party.address||'';
 const amountColumns=r.columns.some(x=>x.startsWith('Amount'));
 function cell(label,l,i){
  const p=db.products.find(p=>p.id===l.productId)||{},f=l.sourceFields||{},sql=label.split(' → ')[1];
  // SQL-named values are printed only when present, never inferred borrow/deposit/check quantities.
  if(sql&&Object.hasOwn(f,sql))return fmt(f[sql]);
  const name=label.split(' → ')[0];
  if(name==='No.')return i+1;
  if(name==='Cat No.')return e(l.catalogueNo||p.catalogueNo||p.sku||'');
  if(/^(Item|Description|Product)/.test(name))return e(l.description||p.name||l.productId||'');
  if(name==='Quantity'||name==='Quantity Order'||name==='Quantity In'||name==='Quantity Out'||name==='Quantity Move')return fmt(l.qty);
  if(/^(Unit Price)$/.test(name))return fmt(l.price);
  if(name==='Amount')return fmt(Math.round(Number(l.qty||0)*Number(l.price||0)*100)/100);
  if(/^(Sale Unit|Buying Unit|Unit)/.test(name))return e(l.unit||p.unit||'');
  if(name==='Lot No.')return e(l.lot||'');
  if(name==='Expire Date')return e(l.expiry||'');
  if(name==='From Location')return e(l.fromWarehouse||d.warehouse||'');
  if(name==='To Location')return e(l.toWarehouse||d.toWarehouse||'');
  return '—';
 }
 const rows=(d.lines||[]).map((l,i)=>'<tr>'+r.columns.map(c=>'<td>'+cell(c,l,i)+'</td>').join('')+'</tr>').join('');
 const delivery=fields(source,['txtattentionto'])+'\n'+fields(source,['txtaddressd']);
 const totals=amountColumns?'<table class="totals">'+[['Amount',m.amount],['Sales discount',m.sales],['Cash discount',m.cash],['Total amount',m.net],['VAT '+m.vat+'%',m.tax],['Grand total',m.grand]].map(([k,v])=>'<tr><td>'+e(k)+'</td><td>'+fmt(v)+'</td></tr>').join('')+'</table>':'';
 const html='<!doctype html><html><head><meta charset="utf-8"><title>'+e(d.ref)+'</title><style>@page{size:A4 '+r.orientation.toLowerCase()+';margin:12mm 12mm 14mm}body{font:11px Arial,sans-serif;color:#111}h1{font-size:20px}.blocks{display:grid;grid-template-columns:1fr 1fr 1fr;gap:18px;margin:16px 0;white-space:pre-line}table{width:100%;border-collapse:collapse}th,td{border:1px solid #888;padding:7px;vertical-align:top}thead{display:table-header-group}tr{break-inside:avoid}th{background:#edf1f4}.totals{width:38%;margin:15px 0 15px auto}.signatures{display:flex;justify-content:space-around;margin-top:55px;break-inside:avoid}.signatures p{border-top:1px solid #333;min-width:150px;padding-top:8px;text-align:center}.remarks{white-space:pre-line;clear:both}.review{color:#666;font-size:9px;margin-top:20px}@media print{button{display:none}}'+BiomedReportBranding.styles+'</style></head><body><table class="bm-report-frame"><thead><tr><td>'+BiomedReportBranding.header({orientation:r.orientation,title:r.title,reference:d.ref,date:d.date})+'</td></tr></thead><tbody><tr><td><h1 class="bm-report-title">'+e(r.title)+'</h1><div class="blocks"><div><b>Customer / Supplier</b>\n'+e(partyName)+'\n'+e(address)+'</div><div><b>Delivery to</b>\n'+e(delivery)+'</div><div><b>'+e(d.ref)+'</b>\nDate: '+e(d.date)+'\nReference: '+e(d.externalRef||'')+'\nCurrency: '+e(d.currency||'THB')+'\nStatus: '+e(d.status)+'</div></div><table><thead><tr>'+r.columns.map(c=>'<th>'+e(c.split(' → ')[0])+'</th>').join('')+'</tr></thead><tbody>'+rows+'</tbody></table>'+totals+'<div class="remarks">'+e(fields(source,['txtremarkC','txtremark'])||d.remark||'')+'</div><div class="signatures"><p>Prepared by</p><p>Approved by</p><p>Received by / Date</p></div><p class="review">Layout review · Unmapped values appear as —. Kit expansion and original report calculations remain subject to verification.</p></td></tr></tbody></table><div class="bm-report-toolbar"><button id="bm-print-report" disabled onclick="window.print()">Preparing header…</button></div></body></html>';
 const w=window.open('','_blank');if(!w)return alert('Allow popups to preview the report.');w.document.write(html);w.document.close();BiomedReportBranding.prepareWindow(w);
};
