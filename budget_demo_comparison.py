"""One-time, backed-up variation of the supplied fictional FY2026/FY2027 fixture."""
import copy,json,random,math
KEY='biomed_budget_v60_years'
MIGRATION='fictional-fy-comparison-v1'
def randomize(store):
    result=copy.deepcopy(store)
    for year in [2026,2027]:
        s=result['years'][str(year)];rng=random.Random(year*817+37);scale=.82 if year==2026 else 1.18;months=12 if year==2026 else 6
        old_ledger=s.get('ledger',[]);manual=[l for l in old_ledger if l.get('reference')!='TEST-BUDGET-FIXTURE' and not str(l.get('id','')).startswith('FY-DEMO-')]
        ledger=[]
        def add(line,rec,field,m,amount,typ='Actual'):
            if not amount:return
            ledger.append(dict(id=f'FY-DEMO-{year}-{line}-{typ}-{m}',date=f'{year-1 if m<8 else year}-{m+5 if m<8 else m-7:02d}-15',line=line,label=rec['name'],type=typ,month=m,amount=amount,reference=f'TEST-FY{year}-COMPARISON',note='Fictional fiscal-year comparison scenario',division=rec.get('division'),costCenter=rec.get('costCenter',rec.get('division'))))
        for i,p in enumerate(s['products']):
            base=max(15000,sum(p.get('budget',[]))/12);linefactor=rng.uniform(.72,1.38);ratio=rng.uniform(.38,.64)
            p['budget']=[round(base*scale*linefactor*(1+.12*math.sin((m+i)*math.pi/6))*rng.uniform(.90,1.12),2) for m in range(12)]
            p['cogsBudget']=[round(v*ratio*rng.uniform(.96,1.04),2) for v in p['budget']]
            p['revenueActual']=[round(v*rng.uniform(.70,1.20),2) if m<months else 0 for m,v in enumerate(p['budget'])]
            p['cogsActual']=[round(v*ratio*rng.uniform(.93,1.08),2) for v in p['revenueActual']]
            p['revenue']=round(sum(p['budget']),2);p['cogs']=round(sum(p['cogsBudget']),2)
            for m in range(12):add(p['id'],p,'revenueActual',m,p['revenueActual'][m]);add('cogs:'+p['id'],p,'cogsActual',m,p['cogsActual'][m])
        for i,e in enumerate(s['expenses']):
            base=max(350,sum(e.get('budget',[]))/12);factor=rng.uniform(.6,1.5)
            e['budget']=[round(base*scale*factor*rng.uniform(.78,1.25),2) for _ in range(12)]
            e['actual']=[round(v*rng.uniform(.65,1.18),2) if m<months else 0 for m,v in enumerate(e['budget'])]
            e['commitment']=[round(v*rng.uniform(.15,.55),2) if year==2027 and m>=months and rng.random()<.65 else 0 for m,v in enumerate(e['budget'])]
            e['annual']=round(sum(e['budget']),2)
            if e.get('componentRows'):
                weights=[rng.uniform(.5,1.5) for _ in e['componentRows']];total=sum(weights)
                for field in ['budget','actual','commitment']:
                    for row,w in zip(e['componentRows'],weights):row[field]=[round(v*w/total,2) for v in e[field]]
                    for m in range(12):e['componentRows'][-1][field][m]=round(e[field][m]-sum(row[field][m] for row in e['componentRows'][:-1]),2)
            for m in range(12):add(e['id'],e,'actual',m,e['actual'][m]);add(e['id'],e,'commitment',m,e['commitment'][m],'Commitment')
        # Preserve non-fixture entries and their financial contribution.
        for l in manual:
            line=str(l.get('line',''));rec=next((r for r in s['products' if line.startswith('prd-') or line.startswith('cogs:') else 'expenses'] if r['id']==line.removeprefix('cogs:')),None)
            field='commitment' if l.get('type')=='Commitment' else 'cogsActual' if line.startswith('cogs:') else 'revenueActual' if line.startswith('prd-') else 'actual'
            m=l.get('month')
            if rec is not None and isinstance(m,int) and 0<=m<12 and field in rec:rec[field][m]=round(rec[field][m]+float(l.get('amount',0)),2)
        s['ledger']=ledger+manual;s.setdefault('settings',{})['demoComparison']={'version':1,'year':year,'actualMonths':months,'fictional':True}
    return result

def apply(c):
    row=c.execute('SELECT value,revision FROM workspace WHERE key=?',(KEY,)).fetchone()
    if not row or not row[0]:return False
    c.execute('CREATE TABLE IF NOT EXISTS deployment_data_backups(migration TEXT PRIMARY KEY,payload TEXT NOT NULL)')
    if c.execute('SELECT 1 FROM deployment_data_backups WHERE migration=?',(MIGRATION,)).fetchone():return False
    old=json.loads(row[0]);years=old.get('years',{})
    # Only the supplied test fixture is eligible. Never infer that arbitrary budgets are demos.
    if not all(str(y) in years and any(l.get('reference')=='TEST-BUDGET-FIXTURE' for l in years[str(y)].get('ledger',[])) for y in [2026,2027]):return False
    result=randomize(old)
    c.execute('INSERT INTO deployment_data_backups VALUES(?,?)',(MIGRATION,row[0]))
    c.execute('UPDATE workspace SET value=?,revision=revision+1 WHERE key=?',(json.dumps(result,ensure_ascii=False,separators=(',',':')),KEY))
    return True
