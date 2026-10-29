"""Calendar-specific masters, attachments and source-linked event editing."""
import json
import crm_api as crm
import permissions_policy as policy

def initialize(c):
 c.execute('CREATE TABLE IF NOT EXISTS calendar_files(id TEXT PRIMARY KEY,record_id TEXT NOT NULL,name TEXT NOT NULL,content BLOB NOT NULL)')

def references(c):
 row=c.execute("SELECT value FROM workspace WHERE key='biomed_portal_v33_clean'").fetchone();portal=json.loads(row[0]) if row else {}
 brands=[x['name'] for x in portal.get('operationalBrands',[]) if x.get('active',True)]
 if not brands:brands=list(portal.get('productLines',[]))
 customers=[]
 for ident,payload in c.execute("SELECT id,payload FROM masters WHERE category='customers' ORDER BY id"):
  x=json.loads(payload);customers.append({'id':str(ident),'name':x.get('name') or str(ident),'label':' · '.join(str(x.get(k) or '') for k in ['name','contact','phone','email']).strip(' ·')})
 if not customers:
  row=c.execute("SELECT value FROM workspace WHERE key='biomed_is_v50_transactions'").fetchone();source=json.loads(row[0]) if row else {}
  customers=[{'id':str(x['id']),'name':x.get('name') or str(x['id']),'label':' · '.join(str(x.get(k) or '') for k in ['name','contact','phone','email']).strip(' ·')} for x in source.get('customers',[]) if x.get('id')]
 employees=[{'id':u['Id'],'label':(' '.join([u.get('FirstName') or '',u.get('LastName') or ''])).strip() or 'Employee'} for u in crm.rows(c,'Users') if u.get('Enabled') is not False]
 return {'brands':brands,'customers':customers,'employees':employees}

def validate(c,clean,prior):
 refs=None
 if 'BrandNames' in clean:
  brands=clean['BrandNames']
  if not isinstance(brands,list) or not all(isinstance(x,str) for x in brands) or len(brands)>200:raise ValueError('Select brands from Staff Portal')
  refs=references(c);allowed=set(refs['brands'])|set((prior or {}).get('BrandNames') or [])
  if any(b not in allowed for b in brands):raise ValueError('Select an existing Staff Portal brand')
  clean['BrandNames']=list(dict.fromkeys(brands))
 if clean.get('ISCustomerId') and clean['ISCustomerId']!=(prior or {}).get('ISCustomerId'):
  if not any(x['id']==clean['ISCustomerId'] for x in references(c)['customers']):raise ValueError('Select an existing Biomed IS customer')
 for key in ['AdditionalContacts','AdditionalProducts','Location']:
  if key in clean and (not isinstance(clean[key],(str,type(None))) or len(clean[key] or '')>20000):raise ValueError('Invalid '+key)
 merged={**(prior or {}),**clean}
 if not merged.get('StartDate') and not merged.get('EndDate'):return # Preserve legacy API records without dates; native Calendar requires dates.
 try:
  import datetime
  start=datetime.datetime.fromisoformat(merged.get('StartDate') or '');end=datetime.datetime.fromisoformat(merged.get('EndDate') or '')
  if end<start:raise ValueError()
 except (ValueError,TypeError):raise ValueError('Choose valid start and end dates')

def files(c,result,prior,data,perms):
 if 'Attachments' not in data:return result
 if isinstance(data['Attachments'],list) and any(isinstance(a,dict) and not a.get('id') for a in data['Attachments']):policy.need(perms,'crm.files.upload')
 from minutes_ack import save_files
 initialize(c)
 meta=save_files(c,{'id':str(result['Id'])},{'attachments':(prior or {}).get('Attachments',[])},data['Attachments'],table='calendar_files')
 return crm.update(c,'Events',result['Id'],{'Attachments':meta})
