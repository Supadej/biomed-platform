"""Borrowing quantity invariants; evaluated inside the workspace write transaction."""
import math
ACTIVE = {'Approved', 'Confirmed', 'Received', 'Completed', 'Generated', 'Shipped', 'Paid'}

def ledger(state):
    docs = {d['id']: d for d in state.get('documents', [])}
    rows = {}
    def ancestor(d, kind):
        seen = set()
        while d and d['id'] not in seen:
            seen.add(d['id'])
            if d.get('kind') == kind: return d
            d = docs.get(d.get('sourceId'))
    for d in docs.values():
        if d.get('kind') == 'borrowing':
            for i, l in enumerate(d.get('lines', [])):
                rows[(d['id'], i)] = dict(borrow=d, line=l, issued=0., purchased=0., returned=0., links=[])
    for d in docs.values():
        if d.get('status') not in ACTIVE: continue
        kind = d.get('kind')
        if kind not in ('check-out', 'check-in', 'customer-order'): continue
        for l in d.get('lines', []):
            ref = l.get('borrowRef')
            # Legacy warehouse descendants can be matched only when unambiguous.
            if not ref and kind in ('check-out', 'check-in'):
                b = ancestor(d, 'borrowing')
                if b:
                    matches = [i for i, x in enumerate(b.get('lines', [])) if x.get('productId') == l.get('productId') and (not x.get('lot') or x.get('lot') == l.get('lot'))]
                    if len(matches) == 1: ref = dict(id=b['id'], line=matches[0])
            if not ref: continue
            if not isinstance(ref, dict) or type(ref.get('line')) is not int or ref['line'] < 0: raise ValueError('Invalid borrowing line reference')
            key = (ref.get('id'), ref.get('line'))
            if key not in rows: raise ValueError('Borrowing source line does not exist')
            r = rows[key]
            if r['borrow'].get('status') not in ACTIVE: raise ValueError('Original borrowing must remain approved')
            if d.get('party') != r['borrow'].get('party'): raise ValueError('Borrowing customer must match transaction customer')
            if l.get('productId') != r['line'].get('productId'): raise ValueError('Borrowing product must match source line')
            qty = float(l.get('qty', 0))
            if not math.isfinite(qty) or qty <= 0: raise ValueError('Borrowing quantity must be positive and finite')
            if kind == 'check-out':
                origin = ancestor(d, 'borrowing')
                if not origin or origin['id'] != ref['id']: raise ValueError('Borrowing dispatch must derive from its original Borrowing document')
                if l.get('borrowMode') == 'settlement': raise ValueError('Borrowing settlement must not be dispatched again')
                r['issued'] += qty
            elif kind == 'customer-order':
                if l.get('borrowMode') != 'settlement': raise ValueError('Customer Order borrowing lines must be settlement lines')
                r['purchased'] += qty
            else:
                if l.get('borrowMode') == 'settlement': raise ValueError('Settlement cannot create a warehouse receipt')
                if not ancestor(d, 'return-product'): raise ValueError('Borrowing receipt requires Product Return → Delivery In → Check In')
                r['returned'] += qty
            r['links'].append(d['ref'])
    return rows

def validate(state, previous=None):
    previous = previous or {}
    old = {d['id']: d for d in previous.get('documents', [])}
    for d in state.get('documents', []):
        if d.get('status') not in ACTIVE: continue
        for l in d.get('lines', []):
            if l.get('borrowMode') == 'settlement' and not l.get('borrowRef'): raise ValueError('Settlement line requires borrowing reference')
            if l.get('borrowMode') == 'settlement' and d.get('kind') in ('delivery-out','check-out','shipment','delivery-in','check-in','return-product','purchase-request','purchase-order','waiting-purchase'):
                raise ValueError('Settlement lines are invoice-only and cannot move stock or be purchased again')
    prior = ledger(previous)
    current = ledger(state)
    for key, r in current.items():
        problems = (r['purchased'] + r['returned'] - r['issued'], r['issued'] - float(r['line'].get('qty', 0)))
        p = prior.get(key)
        baseline = (p['purchased'] + p['returned'] - p['issued'], p['issued'] - float(p['line'].get('qty', 0))) if p else (0, 0)
        if any(n > max(0, o) + 1e-8 for n, o in zip(problems, baseline)):
            raise ValueError('Borrowing balance exceeded: ' + r['borrow']['ref'])
    # Posted settlement/receipt references cannot be rewritten by stale clients or restores.
    new = {d['id']: d for d in state.get('documents', [])}
    for id, d in old.items():
        if d.get('status') in ACTIVE and any(l.get('borrowRef') for l in d.get('lines', [])):
            n = new.get(id)
            if not n or n.get('status') not in ACTIVE or n.get('lines') != d.get('lines') or n.get('party') != d.get('party') or n.get('sourceId') != d.get('sourceId'):
                raise ValueError('Posted borrowing transactions are immutable; retain the audit trail')
    # Warehouse routes may contain only the parent's unshipped/new product quantities.
    docs = {d['id']: d for d in state.get('documents', [])}
    for d in docs.values():
        if d.get('status') not in ACTIVE: continue
        parent = docs.get(d.get('sourceId'))
        if parent and any(l.get('borrowMode') == 'settlement' for l in parent.get('lines', [])) and d.get('kind') in ('delivery-out','check-out','shipment'):
            allowed, used = {}, {}
            for l in parent.get('lines', []):
                if l.get('borrowMode') != 'settlement': allowed[l['productId']] = allowed.get(l['productId'], 0) + float(l.get('qty', 0))
            for l in d.get('lines', []): used[l['productId']] = used.get(l['productId'], 0) + float(l.get('qty', 0))
            if any(q > allowed.get(p, 0) + 1e-8 for p, q in used.items()): raise ValueError('Warehouse quantity exceeds new purchase quantity; borrowed goods are already delivered')
    # Return receipts must use a lot actually issued, including partial receipts.
    issued, received = {}, {}
    for d in docs.values():
        if d.get('status') not in ACTIVE or d.get('kind') not in ('check-out','check-in'): continue
        for l in d.get('lines', []):
            ref = l.get('borrowRef')
            if not ref:
                b, seen = d, set()
                while b and b.get('kind') != 'borrowing' and b['id'] not in seen:
                    seen.add(b['id']); b = docs.get(b.get('sourceId'))
                if b and b.get('kind') == 'borrowing':
                    matches = [i for i,x in enumerate(b.get('lines', [])) if x.get('productId') == l.get('productId') and (not x.get('lot') or x.get('lot') == l.get('lot'))]
                    if len(matches) == 1: ref = dict(id=b['id'],line=matches[0])
            if not ref: continue
            if not isinstance(ref, dict) or type(ref.get('line')) is not int: raise ValueError('Invalid borrowing reference')
            key = (ref['id'], ref['line'], l.get('lot') or d.get('lot') or 'UNSPECIFIED')
            bucket = issued if d['kind'] == 'check-out' else received
            bucket[key] = bucket.get(key, 0) + float(l.get('qty', 0))
    for key, qty in received.items():
        if qty > issued.get(key, 0) + 1e-8: raise ValueError('Return lot quantity exceeds quantity issued for that borrowing lot')
