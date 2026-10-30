import sys,json,sqlite3,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import instrument_service as service
class HelpdeskInstrument(unittest.TestCase):
 def setUp(self):
  self.c=sqlite3.connect(':memory:');service.initialize(self.c)
  self.instrument={'id':'instrument-1','kind':'instruments','serial':'00069','serialAlias':'SN00069','brand':'Phadia','model':'Phadia 200','location':'HQ'}
  self.c.execute('INSERT INTO fse_records VALUES(?,?,?,1)',('instrument-1','instruments',json.dumps(self.instrument)))
 def test_selection_stores_stable_link_and_canonical_serial(self):
  clean={'ServiceInstrumentId':'instrument-1','SerialNumber':'tampered'};service.bind_ticket_instrument(self.c,{'service.references.view'},clean)
  self.assertEqual(clean['SerialNumber'],'00069');self.assertEqual(clean['Brand'],'Phadia');self.assertEqual(clean['Model'],'Phadia 200');self.assertEqual(clean['ServiceLocation'],'HQ')
 def test_alias_binds_without_losing_leading_zeros(self):
  clean={'SerialNumber':'sn00069'};service.bind_ticket_instrument(self.c,{'service.references.view'},clean);self.assertEqual(clean['ServiceInstrumentId'],'instrument-1');self.assertEqual(clean['SerialNumber'],'00069')
 def test_unknown_and_ambiguous_serials_rejected(self):
  for clean in [{'SerialNumber':'Unknown'},{'ServiceInstrumentId':'missing','SerialNumber':'00069'}]:
   with self.assertRaises(ValueError):service.bind_ticket_instrument(self.c,{'service.references.view'},clean)
  self.c.execute('INSERT INTO fse_records VALUES(?,?,?,1)',('instrument-2','instruments',json.dumps({'id':'instrument-2','kind':'instruments','serial':'other','serialAlias':'00069'})))
  with self.assertRaises(ValueError):service.bind_ticket_instrument(self.c,{'service.references.view'},{'SerialNumber':'00069'})
 def test_link_survives_serial_rename(self):
  self.c.execute('UPDATE fse_records SET payload=?',(json.dumps(dict(self.instrument,serial='NEW-SERIAL',serialAlias='')),))
  self.assertEqual(service.ticket_instruments(self.c,{'ServiceInstrumentId':'instrument-1','SerialNumber':'00069'})[0]['id'],'instrument-1')
 def test_historical_links_migrate_once_without_rewriting_serial(self):
  self.c.execute('CREATE TABLE crm_records(entity TEXT,id INTEGER,payload TEXT,version INTEGER,deleted INTEGER)')
  self.c.execute("INSERT INTO crm_records VALUES('HelpDeskTickets',1,?,1,0)",(json.dumps({'SerialNumber':'SN00069','Model':'Historical snapshot'}),))
  self.assertEqual(service.migrate_ticket_instrument_links(self.c)['linked'],1)
  row=json.loads(self.c.execute('SELECT payload FROM crm_records').fetchone()[0]);self.assertEqual(row['ServiceInstrumentId'],'instrument-1');self.assertEqual(row['SerialNumber'],'SN00069');self.assertEqual(row['Model'],'Historical snapshot');self.assertIsNone(service.migrate_ticket_instrument_links(self.c))
 def test_permissions_and_historical_ticket_preserved(self):
  with self.assertRaises(Exception):service.bind_ticket_instrument(self.c,set(),{'ServiceInstrumentId':'instrument-1'})
  prior={'SerialNumber':'Legacy unmatched'};self.assertIsNone(service.bind_ticket_instrument(self.c,set(),{'SerialNumber':'Legacy unmatched'},prior))
  self.assertIsNone(service.bind_ticket_instrument(self.c,set(),{}, {'SerialNumber':'00069'}))
if __name__=='__main__':unittest.main()
