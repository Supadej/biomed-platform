/* Costs are recorded as positive inputs and deducted exactly once. */
(function(scope){
function totals(lines,field,month){const t={revenue:0,cogs:0,otherCostOfSales:0,expenses:0,earnings:0};for(const l of lines){const values=l[field]||[],n=month===undefined?values.reduce((a,b)=>a+Number(b||0),0):Number(values[month]||0);const key=l.kind==='Revenue'?'revenue':l.kind==='COGS'?'cogs':l.group==='Other Cost of Sales Budget'||l.category==='Other Cost of Sales'||String(l.source).startsWith('Other Cost of Sales')?'otherCostOfSales':'expenses';t[key]+=n}t.earnings=t.revenue-t.cogs-t.otherCostOfSales-t.expenses;return t}
const api={calculate:(plan,current,approved)=>({plan:totals(plan,'target'),approved:totals(approved,'target'),actual:totals(current,'actual'),months:Array.from({length:12},(_,i)=>totals(plan,'target',i))})};scope.BudgetEarnings=api;if(typeof module!=='undefined')module.exports=api;
})(globalThis);
