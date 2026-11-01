View selection correction

Fixed stale selected-button state when only the results area reloads. Calendar Month/Week/Day/Table and Sales Plan, External Helpdesk and Project & Activity Table/Board now synchronize aria-pressed with the actual view on every load. Records/Analysis are synchronized independently. Active state updates before the network call, including errors and rapid switches. Main script cache version updated.

Verified with a new DOM interaction regression for repeated switches in all four modules, plus Records/Analysis and network failure. All nine JavaScript test files passed. IS and Financial switchers rebuild their navigation on render rather than retaining this partial toolbar. No database or permission changes. Rendered browser visual verification remains outstanding.

Deploy the updated source, wait for Railway Active, then reload. No database reset or demo import is required.
