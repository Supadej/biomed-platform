# Update 29 — consolidated Service Inventory

Service Inventory now shows one summary row per catalogue/part number and unit. Quantities are summed across the engineer and lot balances visible to the signed-in user. For example, six engineers holding 25 of BMD-TEST-SPARE-8 now show one row with 150 available.

Open Details to see each engineer, product ID, lot, expiry and quantity. Multiple lots show a lot count and the earliest known expiry in the summary. Different units are kept separate. Search filters apply before the total and support catalogue/SKU as well as engineer, product name and lot. Engineers still see only their own authorized balances; approvers can see their authorized combined balance.

The underlying custody ledger, approval records, lot allocations and automatic job deductions are retained. The former repeated rows represented separate engineer custody, rather than duplicated stock postings. Consolidation changes the summary presentation; it does not add stock or merge custody ownership.

Validation covered six × 25 = 150, multiple lots, restricted subsets and differing units. Browser verification confirmed eight summary parts, a single PART-8 row totalling 150, and six underlying engineer detail rows. This package has not been deployed.
