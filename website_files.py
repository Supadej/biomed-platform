"""Database-backed website images/PDFs; uploads are private until referenced by published content."""
import base64,binascii,re,secrets
MAX_FILE=10*1024*1024
def decode_upload(data):
    name=str(data.get('name','')).replace('\\','/').split('/')[-1]
    if not name or len(name)>180 or any(ord(c)<32 for c in name):raise ValueError('Invalid filename')
    try:raw=base64.b64decode(data.get('data',''),validate=True)
    except (binascii.Error,ValueError,TypeError):raise ValueError('Invalid file data')
    if not 0<len(raw)<=MAX_FILE:raise ValueError('Each attachment must be 10 MB or smaller')
    if raw.startswith(b'\x89PNG\r\n\x1a\n'):mime='image/png'
    elif raw.startswith(b'\xff\xd8\xff'):mime='image/jpeg'
    elif raw[:4]==b'RIFF' and raw[8:12]==b'WEBP':mime='image/webp'
    elif raw.startswith(b'%PDF-'):mime='application/pdf'
    else:raise ValueError('Upload PNG, JPEG, WebP or PDF files only')
    id=secrets.token_hex(16)
    return {'id':id,'name':name,'mime':mime,'size':len(raw),'url':'/api/website/files/'+id},raw
def file_ids(item):
    ids={str(f.get('id','')) for key in ['photos','attachments'] for f in item.get(key,[]) if isinstance(f,dict)}
    image=str(item.get('image',''))
    if image.startswith('/api/website/files/'):ids.add(image.rsplit('/',1)[-1])
    return ids
def public_reference(portal,id):return any(x.get('status')=='published' and id in file_ids(x) for x in portal.get('content',[]))
def validate_references(portal,connection):
    for item in portal.get('content',[]):
        for key,limit in [('photos',6),('attachments',3)]:
            files=item.get(key,[])
            if not isinstance(files,list) or len(files)>limit:raise ValueError('Maximum 6 photos and 3 PDFs per item')
            for f in files:
                if not isinstance(f,dict):raise ValueError('Invalid attachment')
                row=connection.execute('SELECT mime FROM website_files WHERE id=?',(str(f.get('id','')),)).fetchone()
                if not row:raise ValueError('Attachment is missing; upload the file again')
                if key=='photos' and not row[0].startswith('image/') or key=='attachments' and row[0]!='application/pdf':raise ValueError('Invalid attachment type')
