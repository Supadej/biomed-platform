const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');const root=path.resolve(__dirname,'..');
const catalog=JSON.parse(fs.readFileSync(root+'/permissions-catalog.json'));const grants=new Set(catalog.permissions.map(p=>p.key));
const docs=[{id:'co',ref:'CO-1',kind:'customer-order',status:'Approved',party:'C1',lines:[{productId:'p',qty:2,price:100}]},{id:'inv',ref:'INV-1',kind:'invoice',party:'C1',status:'Approved',currency:'THB',date:'2026-10-01',due:'2026-10-15',lines:[{qty:1,price:1000}]}];
for(const [id,kind,amount,status,currency,party,sourceId] of [['p1','payment-receipt',300,'Approved','THB','C1','inv'],['c1','credit-note',100,'Approved','THB','C1','inv'],['d1','debit-note',50,'Approved','THB','C1','inv'],['pending','payment-receipt',200,'Pending','THB','C1','inv'],['fx','payment-receipt',900,'Approved','USD','C1','inv'],['other','payment-receipt',500,'Approved','THB','C2','inv'],['unlinked','payment-receipt',500,'Approved','THB','C1','']])docs.push({id,kind,status,currency,party,sourceId,lines:[{qty:1,price:amount}]});
let stored={documents:docs,customers:[{id:'C1',name:'Customer 1'}],products:[{id:'p',name:'Product'}]};const notices=[];
const c={console,URL,URLSearchParams,structuredClone,crypto:require('crypto').webcrypto,alert:m=>notices.push(m),confirm:()=>true,document:{},location:{},BiomedStorage:{getItem:k=>k==='biomed_is_v50_transactions'?JSON.stringify(stored):null,setItem(k,v){stored=JSON.parse(v);return v}},BiomedPermissions:{has:k=>grants.has(k),require:keys=>keys.every(k=>grants.has(k)),identity:()=>({user:{id:'admin'},permissions:[...grants]})}};c.window=c;vm.createContext(c);vm.runInContext(fs.readFileSync(root+'/date-filter-defaults.js','utf8'),c);vm.runInContext(fs.readFileSync(root+'/source-schema.js','utf8'),c);
const html=fs.readFileSync(root+'/biomed-is.html','utf8');let js=[...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)].map(m=>m[1]).find(s=>s.includes('const KEY='));js=js.replace("render();\nif(new URLSearchParams", "const actualRender=sourceRender;render=()=>{};window.test={borrowFiltered,borrowSum,borrowRows,borrowAvailable,borrowReport,borrowPicker,performanceProbe:()=>{const saved=renderWorkspace,calc=sourceMoney;let moneyCalls=0;sourceMoney=d=>{moneyCalls++;return calc(d)};try{renderWorkspace=()=>Array.from({length:30},(_,i)=>sourceRegisterValue('Sales',{id:'q'+i,portalRep:'perf-user',lines:[]}));return {first:actualRender(),second:actualRender(),moneyCalls}}finally{renderWorkspace=saved;sourceMoney=calc}},analysisRows,analysisGroups,reportProductMatch,productLotRows,outstandingRows,customerOutstanding,waitingPurchases,renderFunctionSummary,purchasingDescendants,customerPurchasingTrail,buildBrandRequest,brandPurchasingGroups,stockInventory,approvals,installISSuggestions,getNavigation:()=>({page,openId,search,status,from,to,sourceRegisterPage}),setLines:x=>lines=x,getDB:()=>db};\nif(new URLSearchParams");c.location.search='';vm.runInContext(js,c);

const state=c.test.getDB();
state.documents.push({id:'BR',kind:'borrowing',ref:'BR-TEST',status:'Approved',party:'C1',date:'2026-10-27',due:'2026-10-28',history:[],lines:[{productId:'p',qty:10,price:100,lot:'L1'}]}, {id:'OUT',kind:'check-out',ref:'OUT',status:'Approved',sourceId:'BR',party:'C1',lines:[{productId:'p',qty:10,lot:'L1'}]});
assert.equal(c.test.borrowRows()[0].outstanding,10);
assert(c.test.borrowPicker('customer-order').includes('BR-TEST'));
c.IS.derive('BR','customer-order');
let co=stored.documents.find(d=>d.kind==='customer-order'&&d.sourceId==='BR');
assert(co);assert.equal(co.lines[0].borrowMode,'settlement');assert.equal(co.lines[0].borrowRef.line,0);
assert(!stored.documents.find(d=>d.id==='BR').lines[0].borrowRef,'source must remain unchanged');
co=c.test.getDB().documents.find(d=>d.id===co.id);co.status='Approved';co.lines[0].qty=6;co.lines.push({productId:'p',qty:5,price:100,lot:'L2'});
assert.equal(c.test.borrowRows()[0].outstanding,4);
c.IS.derive(co.id,'sales-order');let so=c.test.getDB().documents.find(d=>d.kind==='sales-order'&&d.sourceId===co.id);assert.equal(so.lines.length,2);so.status='Approved';
c.IS.derive(so.id,'invoice');let inv=c.test.getDB().documents.find(d=>d.kind==='invoice'&&d.sourceId===so.id);assert.equal(inv.lines.length,2);inv.status='Approved';
c.IS.derive(inv.id,'delivery-out');let dispatch=c.test.getDB().documents.find(d=>d.kind==='delivery-out'&&d.sourceId===inv.id);assert.equal(dispatch.lines.length,1);assert.equal(dispatch.lines[0].qty,5);assert(!dispatch.lines[0].borrowMode);
c.IS.derive('BR','return-product');let ret=c.test.getDB().documents.find(d=>d.kind==='return-product'&&d.sourceId==='BR');assert.equal(ret.lines[0].qty,4);assert.equal(ret.lines[0].borrowMode,'return');assert.equal(ret.lines[0].lot,'L1');
assert(c.test.borrowReport().includes('Partial'));
console.log('PASS: borrowing ledger, legacy issue inference, settlement derivation, mixed invoice, warehouse exclusion, partial return, original document preservation and picker/report markup.');

c.IS.borrowReset(true);assert.equal(c.test.borrowFiltered().length,1);
c.IS.borrowFilter('customer','missing');assert.equal(c.test.borrowFiltered().length,0);
c.IS.restoreBorrowFavorite([{key:'borrow-customer#0',value:'C1'},{key:'borrow-view#0',value:'customers'},{key:'borrow-from#0',value:''},{key:'borrow-to#0',value:''}]);
assert.equal(c.test.borrowFiltered().length,1);assert(c.test.borrowReport().includes('By customer'));assert(c.test.borrowReport().includes('Different units and currencies'));
c.IS.borrowTab('documents');c.IS.borrowExpand('BR');assert(c.test.borrowReport().includes('Open borrowing document'));assert(c.test.borrowReport().includes('Days since borrow'));
c.IS.borrowFilter('from','2099-01-01');assert.equal(c.test.borrowFiltered().length,0);c.IS.borrowReset(true);
const sum=c.test.borrowSum(c.test.borrowFiltered());assert.equal(sum.issued,10);assert.equal(sum.outstanding,4);assert.equal(sum.amount,1000);
console.log('PASS: customer/date filters, all-dates reset, atomic favorite restoration, document expansion, aging and quantity/value aggregation.');
if(process.env.BORROW_PREVIEW){const css=[...html.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/g)].map(x=>x[1]).join('\n');fs.writeFileSync(process.env.BORROW_PREVIEW,'<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><style>'+css+'</style><main>'+c.test.borrowReport()+'</main>')}
