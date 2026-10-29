import unittest, copy, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from borrowing import validate, ledger

def doc(id, kind, qty, source=None, mode='issue', status='Approved', lot='LOT1'):
    return dict(id=id,ref=id,kind=kind,party='C1',status=status,sourceId=source,lines=[dict(productId='P1',qty=qty,lot=lot,borrowRef=dict(id='BR1',line=0),borrowMode=mode)])
class BorrowingTests(unittest.TestCase):
    def setUp(self):
        self.state=dict(documents=[dict(id='BR1',ref='BR1',kind='borrowing',status='Approved',party='C1',lines=[dict(productId='P1',qty=10,lot='LOT1')]),doc('OUT','check-out',10,'BR1')])
    def test_partial_mixed_settlement_and_physical_return(self):
        s=self.state
        co=doc('CO','customer-order',6,mode='settlement');co['lines'].append(dict(productId='P2',qty=5))
        s['documents'] += [co, doc('RP','return-product',4,'BR1','return'),doc('IN','delivery-in',4,'RP','return')]
        validate(s);self.assertEqual(ledger(s)[('BR1',0)]['returned'],0)
        s['documents'].append(doc('CHECK','check-in',4,'IN','return'));validate(s)
        r=ledger(s)[('BR1',0)];self.assertEqual(r['issued']-r['purchased']-r['returned'],0)
    def test_unissued_and_over_settlement(self):
        self.state['documents'].append(doc('CO','customer-order',11,mode='settlement'))
        with self.assertRaises(ValueError):validate(self.state)
    def test_draft_does_not_settle(self):
        self.state['documents'].append(doc('CO','customer-order',10,mode='settlement',status='Draft'))
        self.assertEqual(ledger(self.state)[('BR1',0)]['purchased'],0)
    def test_concurrent_merged_orders_rejected(self):
        self.state['documents'] += [doc('CO1','customer-order',6,mode='settlement'),doc('CO2','customer-order',6,mode='settlement')]
        with self.assertRaises(ValueError):validate(self.state)
    def test_wrong_customer_product_and_lot(self):
        for field,value in [('party','C2'),('productId','P2'),('lot','LOT2')]:
            s=copy.deepcopy(self.state);r=doc('RP','return-product',1,'BR1','return');receipt=doc('CI','check-in',1,'RP','return')
            if field=='party':receipt[field]=value
            else:receipt['lines'][0][field]=value
            s['documents'] += [r,receipt]
            with self.assertRaises(ValueError):validate(s)
    def test_no_second_dispatch(self):
        self.state['documents'].append(doc('OUT2','check-out',1,'BR1','settlement'))
        with self.assertRaises(ValueError):validate(self.state)
    def test_posted_cannot_disappear(self):
        old=copy.deepcopy(self.state);self.state['documents'].pop()
        with self.assertRaises(ValueError):validate(self.state,old)
    def test_invoice_does_not_settle_twice(self):
        self.state['documents'] += [doc('CO','customer-order',6,mode='settlement'),doc('SO','sales-order',6,'CO','settlement'),doc('INV','invoice',6,'SO','settlement')]
        validate(self.state);self.assertEqual(ledger(self.state)[('BR1',0)]['purchased'],6)
    def test_stripped_metadata_cannot_dispatch_settlement(self):
        co=doc('CO','customer-order',6,mode='settlement');out=doc('OUT2','delivery-out',6,'CO');out['lines'][0].pop('borrowRef');out['lines'][0].pop('borrowMode')
        self.state['documents'] += [co,out]
        with self.assertRaises(ValueError):validate(self.state)
if __name__=='__main__':unittest.main()
