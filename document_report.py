"""Authenticated Biomed IS reports, with shared letterhead and paginated PDF output."""
import io,json,html,re,datetime,threading,functools
from pathlib import Path
from urllib.parse import parse_qs,urlsplit,quote
import permissions_policy as policy
import document_workflow
ROOT=Path(__file__).parent
TITLES={'quotation':'Quotation','customer-order':'Customer Order','sales-order':'Sales Order','waiting-purchase':'Waiting to be Purchased','purchase-request':'Purchase Requisition','purchase-order':'Purchase Order','supplier-confirm':'Supplier Confirmation','delivery-in':'Delivery In','check-in':'Check In','withdrawal':'Withdrawal','borrowing':'Borrowing','return-product':'Product Return','invoice':'Invoice','delivery-out':'Delivery Out','check-out':'Check Out','shipment':'Shipment','credit-note':'Credit Note','debit-note':'Debit Note','payment-receipt':'Payment Receipt','stock-adjust':'Stock Adjustment','stock-transfer':'Warehouse Transfer','stock-count':'Stock Count','cycle-count':'Physical Stock Count','warehouse-move':'Warehouse Transfer'}
PDF_LOCK=threading.RLock()
def serial_pdf(fn):
 @functools.wraps(fn)
 def render(*args,**kwargs):
  with PDF_LOCK:return fn(*args,**kwargs)
 return render
def E(value):return html.escape(str(value if value is not None else ''))
def fmt(value):
 try:return '{:,.2f}'.format(float(value or 0))
 except (ValueError,TypeError):return E(value)
def qty_fmt(value):
 try:return ('{:,.6f}'.format(float(value or 0))).rstrip('0').rstrip('.')
 except (ValueError,TypeError):return E(value)
def resolve(state,ident,kind=''):
 if kind in ['cycle-count','warehouse-move']:
  source='stockChecks' if kind=='cycle-count' else 'warehouseMoves';raw=next((x for x in state.get(source,[]) if str(x['id'])==ident),None)
  if not raw:raise ValueError('Document unavailable')
  return {**raw,'kind':kind,'date':str(raw.get('at',''))[:10],'ref':raw.get('ref') or kind.upper()+'-'+ident,'lines':[{'productId':raw.get('productId'),'qty':raw.get('count',raw.get('qty',0)),'lot':raw.get('lot',''),'price':0}]}
 d=next((x for x in state.get('documents',[]) if str(x['id'])==ident),None)
 if not d:raise ValueError('Document unavailable')
 return d
CSS='''@font-face{font-family:Sarabun;src:url(Sarabun-Regular.ttf)}*{font-family:Sarabun;color:#183b50}body{font-size:9pt;line-height:1.4;margin:0}h1{font-size:20pt;margin:0 0 5pt;color:#123d56}h2{font-size:11pt;margin:16pt 0 6pt}p{margin:4pt 0}table{border-collapse:collapse;width:100%;font-size:8.5pt}th{background:#edf4f8;color:#264f65;font-weight:bold}th,td{padding:6pt;border-bottom:0.5pt solid #d8e2e9;vertical-align:top}td.num,th.num{text-align:right}.meta td{width:50%;background:#f8fafc;padding:4pt;border:0}.label{font-size:7.5pt;color:#607d8c}.note{font-size:8pt;color:#607d8c}.totals{width:52%;margin-left:48%;margin-top:10pt}.totals td{padding:5pt}.grand{font-weight:bold;background:#edf4f8}.wrap{overflow-wrap:anywhere}'''
def content(d,state):
 products={str(x['id']):x for x in state.get('products',[])};parties={str(x['id']):x for x in state.get('customers',[])+state.get('suppliers',[])};party=parties.get(str(d.get('party')),{});people={str(u['id']):u.get('name',u['id']) for u in state.get('users',[])};docs={x['id']:x for x in state.get('documents',[])}
 title=TITLES.get(d['kind'],d['kind']);status=document_workflow.LABEL.get(d.get('status'),d.get('status','Draft'));progress=document_workflow.progress(d,state.get('documents',[])) if d['kind'] not in ['cycle-count','warehouse-move'] else ('Posted' if d.get('status')=='Approved' else 'Awaiting approval' if d.get('status')=='Pending' else 'Not posted')
 meta=[('Reference',d.get('ref')),('Document date',d.get('date')),('Approval',status),('Progress',progress),('Customer / supplier',party.get('name') or 'Internal transaction'),('Prepared by',people.get(str(d.get('owner') or d.get('by')),d.get('owner') or d.get('by') or '')),('Address',party.get('address') or party.get('deliveryAddress') or d.get('deliveryAddress','')),('Tax ID',party.get('taxId','')),('Contact',d.get('contactName') or party.get('contact','')),('Source document',docs.get(d.get('sourceId'),{}).get('ref',d.get('sourceId',''))),('Warehouse / from',d.get('warehouse') or d.get('from','')),('Destination warehouse',d.get('to',''))]
 meta=[(k,v) for k,v in meta if v is not None and v!=''];rows=[];financial=d['kind'] in ['quotation','customer-order','sales-order','purchase-request','purchase-order','supplier-confirm','invoice','credit-note','debit-note','payment-receipt'];currency=d.get('currency') or 'THB'
 for i,line in enumerate(d.get('lines',[]),1):
  product=products.get(str(line.get('productId')),{});description=line.get('description') or line.get('name') or product.get('name') or line.get('productId','');sku=product.get('sku') or product.get('catalogueNo') or line.get('catalogueNo','');lot=line.get('lot') or d.get('lot','');unit=line.get('unit') or product.get('unit','');qty=line.get('qty',0);cells=[str(i),'<strong>'+E(description)+'</strong>'+('<br><span class="note">'+E(sku)+'</span>' if sku else ''),E(lot),qty_fmt(qty),E(unit)]
  if financial:cells += [fmt(line.get('price')),fmt(float(qty or 0)*float(line.get('price',0) or 0))]
  rows.append('<tr>'+''.join('<td'+(' class="num"' if j in [0,3,5,6] else '')+'>'+v+'</td>' for j,v in enumerate(cells))+'</tr>')
 heading=['No.','Product / description','Lot','Quantity','Unit']+(['Unit price','Amount'] if financial else [])
 out='<h1>'+E(title)+'</h1><p class="note">'+E(d.get('ref'))+' · '+E(status)+'</p><table class="meta">'+''.join('<tr>'+''.join('<td><span class="label">'+E(k)+'</span><br>'+E(v)+'</td>' for k,v in meta[i:i+2])+'</tr>' for i in range(0,len(meta),2))+'</table><h2>Items'+(' · '+E(currency) if financial else '')+'</h2><table><thead><tr>'+''.join('<th style="width:'+str(([24,188,62,57,40,80,80] if financial else [28,250,90,90,73])[i])+'pt">'+E(x)+'</th>' for i,x in enumerate(heading))+'</tr></thead><tbody>'+(''.join(rows) or '<tr><td colspan="'+str(len(heading))+'">No items recorded.</td></tr>')+'</tbody></table>'
 if financial:
  gross=sum(float(l.get('qty',0) or 0)*float(l.get('price',0) or 0) for l in d.get('lines',[]));f=d.get('financials') or {};sf=d.get('sourceFields') or {};sales=float(f.get('sales',sf.get('txtdiscountSP',0)) or 0);cash=float(f.get('cash',sf.get('txtdiscountC',0)) or 0);net=float(f.get('net',gross-sales-cash));tax=float(f.get('tax',net*float(sf.get('txtvatC',0) or 0)/100));grand=float(f.get('grand',net+tax));totals=[('Subtotal',gross),('Sales discount',sales),('Cash discount',cash),('Net',net),('VAT',tax),('Grand total · '+currency,grand)]
  out+='<div style="page-break-inside:avoid"><table class="totals">'+''.join('<tr'+(' class="grand"' if k.startswith('Grand') else '')+'><td>'+E(k)+'</td><td class="num">'+fmt(v)+'</td></tr>' for k,v in totals)+'</table></div>'
 fields=[('Payment terms',d.get('paymentTerms')),('Due date',d.get('paymentDue') or d.get('due')),('Delivery date',d.get('deliveryDate')),('Notes',d.get('notes') or d.get('comment') or d.get('reason')),('System quantity',d.get('system')),('Counted quantity',d.get('count')),('Variance',float(d.get('count',0))-float(d.get('system',0)) if 'count' in d else None),('Void / reversal reason',d.get('voidReason'))]
 details=[(k,v) for k,v in fields if v is not None and v!='']
 if details:out+='<h2>Additional information</h2><table>'+''.join('<tr><th style="width:28%">'+E(k)+'</th><td>'+E(v).replace('\n','<br>')+'</td></tr>' for k,v in details)+'</table>'
 out+='<p class="note" style="margin-top:18pt">Approval and transaction history are retained in Biomed IS. This report reflects the record at the time of generation.</p>'
 return out

def letterhead(page,title,reference,index,total,status=''):
 import fitz
 archive=fitz.Archive(str(ROOT/'reference/service-report'));logo_doc=fitz.open()
 for path in [ROOT/'assets/report-biomed-sharp.png',ROOT/'assets/report-masci-iso13485.png']:
  pix=fitz.Pixmap(str(path));p=logo_doc.new_page(width=pix.width,height=pix.height);p.insert_image(p.rect,filename=str(path))
 def put(rect,markup):
  spare,scale=page.insert_htmlbox(rect,markup,css=CSS,archive=archive,scale_low=1)
  if spare<0:raise ValueError('Report header does not fit')
 page.show_pdf_page(fitz.Rect(32,18,282,58),logo_doc,0,clip=fitz.Rect(42,215,2129,501));page.show_pdf_page(fitz.Rect(484,12,563,100),logo_doc,1,clip=fitz.Rect(195,158,1056,1138))
 header='<div style="font-size:10pt;font-weight:bold">บริษัท ไบโอเมด ไดแอกนอสติกส์ (ประเทศไทย) จำกัด</div><div style="font-size:8pt">Biomed Diagnostics (Thailand) Co., Ltd.</div><div style="font-size:7pt">1518/4 อาคารเก่งรุ่งเรืองชัย ชั้น 7 ถ.ประชาราษฎร์ 1 แขวงวงศ์สว่าง เขตบางซื่อ กรุงเทพฯ 10800</div><div style="font-size:7pt">1518/4 Kengrungruengchai Bldg., 7th Fl., Pracharaj Sai 1 Rd., Wongsawang, Bangsue, Bangkok 10800</div>'
 put(fitz.Rect(32,61,479,112),header);page.draw_line((32,116),(563,116),color=(.13,.3,.4),width=.7)
 contact='Tel: +66 2 5870256-58   Fax: +66 2 5870255   Taxpayer ID: 012546003765<br>Email: sales@biomedthai.com   Website: www.biomedthai.com'
 put(fitz.Rect(32,120,563,144),'<div style="font-size:7.5pt">'+contact+'</div>');page.draw_line((32,804),(563,804),color=(.8,.86,.9),width=.5)
 put(fitz.Rect(32,809,480,830),'<span style="font-size:7pt">'+E(title)+' · '+E(reference)+'</span>');page.insert_text((495,821),'Page '+str(index)+' / '+str(total),fontsize=8,color=(.35,.46,.52))
 if title=='Service Report':put(fitz.Rect(32,821,480,834),'<span style="font-size:6pt">FM-FSE-01, Rev. 01 · Effective date: 18 AUG 2025</span>')
 if status in ['Draft','Pending','Rejected','Cancelled','Voided']:page.insert_text((405,45),{'Pending':'PENDING','Rejected':'RETURNED'}.get(status,status.upper()),fontsize=9,color=(.7,.15,.15))

@serial_pdf
def build(d,state):
 import fitz
 from html.parser import HTMLParser
 class Tables(HTMLParser):
  def __init__(self):super().__init__(convert_charrefs=True);self.tables=[];self.table=None;self.row=None;self.cell=None
  def handle_starttag(self,tag,attrs):
   if tag=='table':self.table={'class':dict(attrs).get('class',''),'rows':[]};self.tables.append(self.table)
   elif tag=='tr':self.row=[];self.table['rows'].append(self.row)
   elif tag in ['td','th']:self.cell={'html':'','head':tag=='th','numeric':'num' in dict(attrs).get('class','').split()};self.row.append(self.cell)
   elif self.cell is not None:self.cell['html']+=self.get_starttag_text()
  def handle_endtag(self,tag):
   if tag in ['td','th']:self.cell=None
   elif tag=='tr':self.row=None
   elif tag=='table':self.table=None
   elif self.cell is not None:self.cell['html']+='</'+tag+'>'
  def handle_data(self,data):
   if self.cell is not None:self.cell['html']+=E(data)
 parser=Tables();parser.feed(content(d,state));doc=fitz.open();archive=fitz.Archive(str(ROOT/'reference/service-report'));cell_css=CSS+'body{font-size:8.5pt;margin:0;padding:0}div{margin:0;padding:0}'
 page=None;y=150
 def new_page():
  nonlocal page,y
  if len(doc)>=500:raise ValueError('Report exceeds 500 pages')
  page=doc.new_page(width=595,height=842);y=150
 def put(rect,markup):
  spare,scale=page.insert_htmlbox(rect,markup,css=cell_css,archive=archive,scale_low=1)
  if spare<0:raise ValueError('Report content does not fit its cell')
 def measure(markup,width):
  story=fitz.Story(markup,user_css=cell_css,archive=archive);more,filled=story.place(fitz.Rect(0,0,width,4000))
  if more:raise ValueError('An individual report field is too long; shorten it before printing')
  return fitz.Rect(filled).y1
 def row_height(row,widths):return max(23,max((measure(('<b>'+cell['html']+'</b>') if cell['head'] else cell['html'],widths[i]-12)+8 for i,cell in enumerate(row)),default=12))
 def draw_row(row,widths,x=32,header=False):
  nonlocal y
  height=row_height(row,widths)
  if y+height>792:return False
  if header:page.draw_rect(fitz.Rect(x,y,x+sum(widths),y+height),color=None,fill=(.93,.96,.98))
  left=x
  for i,cell in enumerate(row):
   markup=cell['html'];markup=('<div style="text-align:right">'+markup+'</div>') if cell.get('numeric') else markup;right=left+widths[i]
   if header:markup='<b>'+markup+'</b>'
   put(fitz.Rect(left+6,y+3,right-6,y+height-3),markup)
   left=right
  page.draw_line((x,y+height),(x+sum(widths),y+height),color=(.84,.89,.92),width=.4);y+=height;return True
 def overflow_row(row,widths,header=None):
  nonlocal page,y
  if y>730:new_page()
  markup=''
  for i,cell in enumerate(row):
   label=header[i]['html'] if header and i<len(header) else ''
   markup+=('<b>'+label+'</b><br>' if label else '')+cell['html']+'<br><br>'
  story=fitz.Story(markup,user_css=cell_css,archive=archive);buffer=io.BytesIO();writer=fitz.DocumentWriter(buffer);start=y;last=start
  for n in range(500):
   device=writer.begin_page(fitz.Rect(0,0,595,842));more,filled=story.place(fitz.Rect(32,start,563,792));story.draw(device);writer.end_page();last=fitz.Rect(filled).y1
   if not more:break
   start=150
  else:raise ValueError('Report field exceeds page limit')
  writer.close();fragment=fitz.open(stream=buffer.getvalue(),filetype='pdf')
  for i in range(len(fragment)):
   if i:new_page()
   page.show_pdf_page(page.rect,fragment,i)
  y=last+8
 new_page();title=TITLES.get(d['kind'],d['kind']);put(fitz.Rect(32,y,563,y+30),'<div style="font-size:20pt">'+E(title)+'</div>');y+=34;put(fitz.Rect(32,y,563,y+20),'<span class="note">'+E(d.get('ref'))+' · '+E(document_workflow.LABEL.get(d.get('status'),d.get('status','Draft')))+'</span>');y+=30
 item_seen=False
 for table in parser.tables:
  rows=table['rows'];meta=table['class']=='meta';totals=table['class']=='totals'
  if meta:widths=[265.5,265.5];x=32
  elif totals:
   widths=[160,100];x=303
   height=sum(row_height(r,widths) for r in rows)
   if y+height+12>792:new_page()
   y+=10
  elif not item_seen:
   item_seen=True;financial=len(rows[0])==7;widths=[34,175,61,51,33,80,97] if financial else [28,260,90,80,73];x=32
   if y+65>792:new_page()
   y+=12;put(fitz.Rect(32,y,563,y+20),'<b>Items'+(' · '+E(d.get('currency') or 'THB') if financial else '')+'</b>');y+=23
  else:
   widths=[145,386];x=32
   if y+65>792:new_page()
   y+=14;put(fitz.Rect(32,y,563,y+20),'<b>Additional information</b>');y+=23
  header=rows[0] if rows and all(c['head'] for c in rows[0]) else None
  for row in rows:
   actual_widths=widths[:len(row)]
   if len(row)==1:actual_widths=[sum(widths)]
   if not draw_row(row,actual_widths,x,header=row is header):
    new_page()
    if header and row is not header:draw_row(header,widths,x,header=True)
    if not draw_row(row,actual_widths,x):overflow_row(row,actual_widths,header)
 if y+48>792:new_page()
 y+=16;put(fitz.Rect(32,y,563,y+32),'<span class="note">Approval and transaction history are retained in Biomed IS. This report reflects the record at the time of generation.</span>')
 for index,page in enumerate(doc,1):letterhead(page,title,d.get('ref',''),index,len(doc),d.get('status',''))
 doc.subset_fonts()
 return doc.tobytes(garbage=4,deflate=True)

def handle(h,connect,session,permissions):
 actor=session(h)
 if not actor:return h.reply(401,{'error':'Sign in required'})
 try:
  q=parse_qs(urlsplit(h.path).query);ident=q.get('id',[''])[0];kind=q.get('kind',[''])[0];perms=permissions(actor);policy.need(perms,'is_view')
  with connect() as c:
   row=c.execute('SELECT value FROM workspace WHERE key=?',(document_workflow.KEY,)).fetchone();state=json.loads(row[0]) if row else {};portal=c.execute("SELECT value FROM workspace WHERE key='biomed_portal_v33_clean'").fetchone();people=json.loads(portal[0]).get('users',[]) if portal else [];state['users']=list({str(u['id']):u for u in state.get('users',[])+people}.values());d=resolve(state,ident,kind);policy.visibility.need(perms,'is.'+d['kind'],d);state=json.loads(policy.read_filter(perms,document_workflow.KEY,json.dumps(state)));policy.need(perms,'is.'+d['kind']+'.view');policy.need(perms,'is.'+d['kind']+'.print');format=q.get('format',['pdf'])[0]
   if format not in ['pdf','html']:raise ValueError('Choose PDF or HTML')
   if format=='html':
    from report_html import document as html_report
    pdf=html_report(d,state).encode('utf-8')
   else:pdf=build(d,state)
  filename=re.sub(r'[^\w.-]+','-',d.get('ref') or ident)[:100]+('.html' if format=='html' else '.pdf');h.send_response(200);h.send_header('Content-Type','text/html; charset=utf-8' if format=='html' else 'application/pdf');h.send_header('Content-Length',str(len(pdf)));h.send_header('Content-Disposition',('inline' if q.get('view') else 'attachment')+"; filename*=UTF-8''"+quote(filename));h.send_header('Cache-Control','no-store');h.send_header('X-Content-Type-Options','nosniff');h.end_headers();h.wfile.write(pdf)
 except policy.PermissionDenied as e:return h.reply(403,{'error':str(e)})
 except (ValueError,KeyError,TypeError) as e:return h.reply(400,{'error':str(e)})
