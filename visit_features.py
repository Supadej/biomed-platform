"""Validate changed visit records and atomically synchronize their calendar referral."""
import datetime,json
import crm_api as crm
import permissions_policy as policy
TYPES={'Clinician','PI','User','Laboratory','Nurse','Procurement','Management','Others'}
STATUSES={'Existing','New','Prospect','Others'}
def sync(c,actor,perms,old,new):
 previous={str(r['id']):r for r in old.get('visits',[])};current={str(r['id']):r for r in new.get('visits',[])}
 if previous==current:return
 profiles={str(u['id']):u for u in new.get('users',[])}
 admin=policy.is_system_admin(actor) or actor[3]=='Managing Director';team={str(actor[4])}
 if 'manage_sales' in perms or 'approve_all' in perms:
  for _ in range(len(profiles)):
   team|={i for i,u in profiles.items() if str(u.get('managerId')) in team}
 active={i for i,u in profiles.items() if u.get('active',True) is not False}
 brands={str(x['name']) for x in new.get('operationalBrands',[]) if x.get('active',True)}|set(new.get('productLines',[]))
 for ident in set(previous)|set(current):
  a,b=previous.get(ident),current.get(ident)
  if a==b:continue
  for record in [r for r in [a,b] if r]:
   rep=str(record.get('employee') or record.get('owner') or actor[4])
   if not admin and rep not in team:raise policy.PermissionDenied('Customer visit is outside your reporting team')
  link=c.execute("SELECT record_id FROM crm_links WHERE source='portal-visit' AND source_id=? AND entity='Events'",(ident,)).fetchone()
  if b:
   rep=str(b.get('employee') or b.get('owner') or actor[4])
   if rep not in active:raise ValueError('Choose an active sales representative')
   if 'duration' in b:
    if str(b['duration']) not in {str(i) for i in range(1,25)}:raise ValueError('Visit duration must be 1–24 hours')
   legacy_products=set((a or {}).get('products') or ([(a or {})['product']] if (a or {}).get('product') else []))
   for key,choices in [('collaborators',active),('customerTypes',TYPES),('products',brands|legacy_products)]:
    if key in b:
     values=b[key]
     if not isinstance(values,list) or len(values)>100 or len(set(values))!=len(values) or any(not isinstance(v,str) or v not in choices for v in values):raise ValueError('Choose valid '+key)
   if b.get('customerStatus') and b['customerStatus'] not in STATUSES:raise ValueError('Choose a valid customer status')
   if 'addCalendar' in b and type(b['addCalendar']) is not bool:raise ValueError('Invalid calendar option')
   if b.get('visitdate'):
    try:datetime.datetime.fromisoformat(b['visitdate'])
    except (ValueError,TypeError):raise ValueError('Choose a valid visit date & time')
   if not str(b.get('customer') or '').strip():raise ValueError('Enter the customer / institution')
  if not b or not b.get('addCalendar'):
   if link:
    policy.need(perms,'portal.visits.calendar');c.execute("UPDATE crm_records SET deleted=1,version=version+1 WHERE entity='Events' AND id=?",(link[0],));crm.audit(c,actor,'Events',link[0],'visit unlinked',{'visit':ident});c.execute("DELETE FROM crm_links WHERE source='portal-visit' AND source_id=? AND entity='Events'",(ident,))
   continue
  policy.need(perms,'portal.visits.calendar')
  if 'T' not in str(b.get('visitdate','')):raise ValueError('Calendar linking requires a visit date and time')
  start=datetime.datetime.fromisoformat(b['visitdate']);end=start+datetime.timedelta(hours=int(b.get('duration',1)))
  people={str(i):int(n) for i,n in c.execute('SELECT portal_user_id,crm_user_id FROM crm_identity')}
  if rep not in people:raise ValueError('Sales representative has no calendar profile')
  products=b.get('products') or ([b['product']] if b.get('product') else [])
  event={'Title':' · '.join([str(b['customer']),', '.join(products)]).strip(' ·'),'StartDate':start.isoformat(timespec='minutes'),'EndDate':end.isoformat(timespec='minutes'),'IsAllDay':False,'MainUserID':people[rep],'UserIds':[people[x] for x in b.get('collaborators',[]) if x in people],'Location':str(b.get('customer') or ''),'Description':str(b.get('discussion') or '')+'\nCustomer visit: /?portal=1&module=visits&visit='+ident}
  if link and crm.raw(c,'Events',link[0]):crm.update(c,'Events',link[0],event);eid=link[0]
  else:
   eid=crm.insert(c,'Events',event)['Id'];c.execute("INSERT OR REPLACE INTO crm_links VALUES('portal-visit',?,'Events',?)",(ident,eid))
  crm.audit(c,actor,'Events',eid,'customer visit sync',{'visit':ident})
