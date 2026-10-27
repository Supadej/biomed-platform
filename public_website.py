"""Explicit public projection: never return Portal workspace or private drafts."""
from urllib.parse import urlsplit
import re
SECTION_IDS={'home','solutions','portfolio','about','partners','services','insights','contact','news','events','careers'}
CONTENT_FIELDS={'id','type','title','description','body','image','link','linkLabel','publishDate','eventDate','location','deadline','department','employmentType'}
def safe_url(value):
    value=str(value or '').strip()
    if not value:return ''
    if '\\' in value or value.startswith('//') or any(ord(c)<32 for c in value):return ''
    if value.startswith(('/', '#')):return value
    if re.fullmatch(r'(?:\./)?[A-Za-z0-9_][A-Za-z0-9_./-]*(?:[?#][^\s]*)?',value):return value
    try:return value if urlsplit(value).scheme.lower() in ['http','https','mailto','tel'] else ''
    except ValueError:return ''
def project_public(portal):
    sections={}
    for id,values in portal.get('siteSections',{}).items():
        if id not in SECTION_IDS or not isinstance(values,dict):continue
        sections[id]={str(k):str(v) for k,v in values.items() if isinstance(v,(str,int,float))}
        for k,v in sections[id].items():
            if k=='image' or k.lower().endswith('link'):sections[id][k]=safe_url(v)
    content=[]
    for item in portal.get('content',[]):
        if item.get('status')!='published':continue
        out={k:str(v) for k,v in item.items() if k in CONTENT_FIELDS and isinstance(v,(str,int,float))}
        for k in ['image','link']:
            if k in out:out[k]=safe_url(out[k])
        for key in ['photos','attachments']:
            out[key]=[{'id':str(f['id']),'name':str(f.get('name','Attachment')),'mime':str(f.get('mime','')),'url':'/api/website/files/'+str(f['id'])} for f in item.get(key,[]) if isinstance(f,dict) and re.fullmatch('[a-f0-9]{32}',str(f.get('id','')))]
        content.append(out)
    brands=[]
    for item in portal.get('brands',[]):
        if not isinstance(item,dict) or item.get('active') is False:continue
        out={k:str(item.get(k,'')) for k in ['id','name','category','field','description','html']}
        out['url']=safe_url(item.get('url'))
        logo=str(item.get('logo',''))
        out['logo']=logo if len(logo)<=850000 and re.fullmatch(r'data:image/(?:png|jpeg|webp|gif);base64,[A-Za-z0-9+/=\s]+',logo) else safe_url(logo)
        brands.append(out)
    return {'siteSections':sections,'content':content,'brands':brands}
