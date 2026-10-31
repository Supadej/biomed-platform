# Record visibility validation

- Full Python regression suite: 399 tests passed.
- Includes 25 focused isolation and endpoint tests for own, assigned, recursive reporting teams, departments, all, unassigned records, CRM identity mapping, direct report URLs, quotation snapshots, forged saves, hidden-row preservation, stock metadata masks, migration and role rename/deletion.
- Real WSGI listener tests cover login, Portal saving, session expiry and stale revisions.
- Browser checks: saving/reloading role visibility and responsive controls at 1440, 768, 390 and 320 pixels; no page JavaScript errors or control overlaps in the tested views.
- DOM checks: visibility controls, protected administrator settings, permission checks, search and failed-save recovery; existing role administration, manual and report controls.
- Packaged database: 67 account rows and 161 document rows unchanged. Only visibility configuration, permission migration metadata and an empty configuration audit table were added.
- Not deployed to the live Railway service. Physical Android/iOS testing was not performed.
