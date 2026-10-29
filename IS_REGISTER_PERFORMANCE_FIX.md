IS register performance correction

Quotation, Customer Orders and Sales Orders share the mapped register renderer. Sales-name cells previously fetched the complete Portal workspace synchronously for each row. The renderer now caches staff names for one render and refreshes on the next render. Customer/supplier and document lookups use render-scoped maps. Monetary calculations are performed only for financial columns. Pagination remains 30 rows and permissions remain unchanged.

Regression verified: 30 sales-name cells make one Portal read instead of 30; a second render reads fresh staff data; nonfinancial cells perform no unused total calculations. All nine JavaScript test files passed. Actual Railway latency has not been measured. Initial application loads still use the existing synchronous workspace adapter, so this does not eliminate every possible source of latency.

Deploy updated source then reload Biomed IS. Preserve your database and keys; no reset or demo import is needed.
