import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import service_report as reports
import fitz
class Report(unittest.TestCase):
 def sample(self):return {'id':'test','jobNo':'BMDS28-10-26/1','date':'2026-10-28','status':'Completed','jobType':'Repair','diagnosis':'Aspiration error','actionTaken':'Replaced the valve.','department':'ห้องปฏิบัติการ','feedbackComment':'บริการดี','feedbackSolved':'Yes'}
 def test_compact_template_and_thai_fields(self):
  pdf=reports.build(self.sample(),{'serial':'00069','brand':'Phadia','model':'Phadia 200','location':'Siriraj'},{'name':'โรงพยาบาลศิริราช'},'สมชาย',[{'catalogueNo':'SP-1','name':'Valve','qty':1}]);d=fitz.open(stream=pdf,filetype='pdf');self.assertEqual(len(d),1);text=d[0].get_text()
  for expected in ['Biomed Diagnostics (Thailand) Co., Ltd.','Service Report','FM-FSE-01, Rev. 01','Effective date: 18 AUG 2025','BMDS28-10-26/1','00069','SP-1','Valve','โรงพยาบาลศิริราช','สมชาย']:self.assertIn(expected,text)
  words=d[0].get_text('words');job=next(w for w in words if 'BMDS28-10-26/1' in w[4]);self.assertGreaterEqual(job[0],32);self.assertLess(job[2],300);self.assertGreater(job[1],180);self.assertLess(job[3],210)
 def test_overflow_is_retained_with_pagination(self):
  r=self.sample();r['diagnosis']='Detailed problem and findings. '*120+'END-PROBLEM';r['actionTaken']='Actions and safety verification. '*170+'END-SOLUTION';parts=[{'catalogueNo':'SP-'+str(i),'name':'Part '+str(i),'qty':i+1} for i in range(12)]
  pdf=reports.build(r,{'serial':'00069'},{},'Engineer',parts);d=fitz.open(stream=pdf,filetype='pdf');text='\n'.join(p.get_text() for p in d);self.assertGreater(len(d),1)
  for expected in ['END-PROBLEM','END-SOLUTION','SP-11','Part 11']:self.assertIn(expected,text)
  for i,p in enumerate(d):self.assertIn('Page '+str(i+1)+' / '+str(len(d)),p.get_text())
if __name__=='__main__':unittest.main()
