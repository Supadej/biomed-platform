import datetime,unittest
import application_job_extras as application
import service_job_extras as service
class CalendarDates(unittest.TestCase):
 def test_today_defaults_and_selected_dates(self):
  today=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).date().isoformat()
  for validate in [lambda r:service.validate(r),lambda r:application.validate(r,r,{})]:
   r={'calendarEnabled':True,'start':'2020-01-01T09:00','date':'2020-01-01','scheduledDate':'2020-01-02'}
   validate(r);self.assertEqual(r['calendarDate'],today)
   r['calendarDate']='2026-11-12';validate(r);self.assertEqual(r['calendarDate'],'2026-11-12')
   for invalid in ['',None,'2026-02-30','20261112']:
    with self.subTest(invalid=invalid):
     with self.assertRaises(ValueError):validate(dict(r,calendarDate=invalid))
 def test_application_edit_preserves_saved_date(self):
  result={'start':'2026-12-01T09:00'}
  application.validate(result,{}, {'calendarEnabled':True,'calendarDate':'2026-11-12'})
  self.assertEqual(result['calendarDate'],'2026-11-12')
if __name__=='__main__':unittest.main()
