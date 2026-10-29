"""Touch-drawn customer acknowledgement, validated and bound to report content."""
import json,hashlib,datetime,math
FIELDS='instrumentId customerId engineer jobNo jobType status date location description diagnosis actionTaken result laborHours serviceAmount currency customerAcceptance partsUsed feedbackSolved feedbackSpeed feedbackPreparedness feedbackCourtesy feedbackSatisfaction feedbackComment customerSignatory'.split()
def digest(r):return hashlib.sha256(json.dumps({k:r.get(k) for k in FIELDS},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def save(c,actor,r,old):
 sig=r.get('customerSignature');prior=(old or {}).get('customerSignature')
 if sig is None:return
 if sig==prior:
  if sig.get('reportHash')!=digest(r):raise ValueError('The report changed after signing. Clear the signature or ask the customer to sign the revised report.')
  return
 if not isinstance(sig,dict):raise ValueError('Invalid customer signature')
 name=str(sig.get('name') or '').strip();strokes=sig.get('strokes')
 if not name or len(name)>200 or sig.get('consent') is not True:raise ValueError('Enter the customer name and confirm acknowledgement before signing')
 if not isinstance(strokes,list) or not 1<=len(strokes)<=100:raise ValueError('Draw a customer signature')
 count=0;clean=[]
 for stroke in strokes:
  if not isinstance(stroke,list) or len(stroke)<2:raise ValueError('Draw a complete signature stroke')
  points=[]
  for point in stroke:
   if not isinstance(point,list) or len(point)!=2 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=1 for v in point):raise ValueError('Invalid signature coordinates')
   count+=1
   if count>5000:raise ValueError('Signature too complex; clear and sign again')
   points.append([round(v,5) for v in point])
  clean.append(points)
 if prior and clean==prior.get('strokes'):raise ValueError('Ask the customer to draw a new signature for the revised report.')
 row=c.execute("select payload from fse_records where id=? and kind='instruments'",(r.get('instrumentId'),)).fetchone();inst=json.loads(row[0]) if row else {}
 row=c.execute("select payload from masters where category='customers' and id=?",(r.get('customerId') or inst.get('customerId'),)).fetchone();customer=json.loads(row[0]) if row else {}
 import service_referrals
 parts=service_referrals.job_parts(c,r)
 r['customerSignatory']=name
 r['customerSignature']={'name':name,'strokes':clean,'consent':True,'signedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'capturedBy':str(actor[4]),'reportHash':digest(r),'instrumentSnapshot':inst,'customerSnapshot':customer,'partsSnapshot':parts,'engineerName':r.get('engineerName') or r.get('engineer') or ''}
