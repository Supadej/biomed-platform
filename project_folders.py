"""Project folders with permission-filtered counts and atomic dependent deletion."""
import crm_api as crm
import permissions_policy as policy
def children(c,ident):
 stages=[r for r in crm.rows(c,'ProjectPipeline') if r.get('ProjectId')==ident];ids={r['Id'] for r in stages}
 activities=[r for r in crm.rows(c,'ProjectActivity') if r.get('ProjectId')==ident or r.get('ProjectPipelineId') in ids]
 return stages,activities
def listing(c,perms,uid):
 crm.need(perms,'projects');out=[]
 for r in crm.rows(c,'Projects'):
  if not crm.visible(c,perms,'Projects',r,uid):continue
  stages,activities=children(c,r['Id'])
  out.append({'Id':r['Id'],'Name':r.get('Name'),'Description':r.get('Description'),'stages':len(stages) if 'crm.project_stages.view' in perms else None,'activities':sum(crm.visible(c,perms,'ProjectActivity',a,uid) for a in activities) if 'crm.activities.view' in perms else None,'version':c.execute('SELECT version FROM crm_records WHERE entity=? AND id=?',('Projects',r['Id'])).fetchone()[0]})
 return out
def delete(c,actor,perms,uid,data):
 ident=int(data['id']);crm.need(perms,'projects','delete');project=crm.raw(c,'Projects',ident)
 if not project:raise ValueError('Project no longer exists')
 if not crm.visible(c,perms,'Projects',project,uid):raise policy.PermissionDenied('Project is outside your scope')
 stages,activities=children(c,ident)
 if not data.get('confirm_children') and (stages or activities):raise ValueError('Confirm deletion of linked project stages and activities')
 version=c.execute('SELECT version FROM crm_records WHERE entity=? AND id=?',('Projects',ident)).fetchone()[0]
 if data.get('version')!=version:raise ValueError('Project changed; reload before deleting')
 if data.get('stages')!=len(stages) or data.get('activities')!=len(activities):raise ValueError('Project contents changed; reload before deleting')
 # Every child needs deletion permission and record scope before any mutation.
 for entity,records in [('ProjectPipeline',stages),('ProjectActivity',activities)]:
  if records:crm.need(perms,crm.MODULES[entity],'delete')
  for row in records:
   if row.get('_bridgeSource') or not crm.visible(c,perms,entity,row,uid):raise policy.PermissionDenied('A linked record cannot be deleted within your scope')
 # Some legacy schema fields (for example Leads.ProjectID) lack declared FKs.
 for entity in crm.SCHEMA:
  if entity in ('Projects','ProjectPipeline','ProjectActivity'):continue
  for row in crm.rows(c,entity):
   if any(k.lower()=='projectid' and str(v)==str(ident) for k,v in row.items()):raise ValueError('Project has linked '+entity+'; reassign those records first')
 c.execute('SAVEPOINT project_folder_delete')
 try:
  for activity in activities:
   for join,(parent,fk,_,_) in crm.JOINS.items():
    if parent=='ProjectActivity':
     for row in crm.rows(c,join):
      if row.get(fk)==activity['Id']:c.execute('UPDATE crm_records SET deleted=1,version=version+1 WHERE entity=? AND id=?',(join,row['Id']))
   crm.mutate(c,actor,perms,uid,'ProjectActivity','delete',{'Id':activity['Id']})
  for stage in stages:crm.mutate(c,actor,perms,uid,'ProjectPipeline','delete',{'Id':stage['Id']})
  result=crm.mutate(c,actor,perms,uid,'Projects','delete',{'Id':ident})
  c.execute('RELEASE SAVEPOINT project_folder_delete');return {**result,'stages':len(stages),'activities':len(activities)}
 except Exception:
  c.execute('ROLLBACK TO SAVEPOINT project_folder_delete');c.execute('RELEASE SAVEPOINT project_folder_delete');raise
