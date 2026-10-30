# Application job Save update

Application Service now validates through the Save handler and identifies invalid required fields directly in the form. Completed jobs identify missing work performed/results before submitting. Server errors appear in a visible, focused alert; entered values are retained and Save is re-enabled for retry. Duplicate submissions are blocked while saving. Successful saves display confirmation and identify jobs outside the current filters. If the save succeeds but refreshing the list fails, the saved record is shown locally and the message explicitly states that it was saved.

Validation: native button-click DOM checks for create/edit, required fields, Completed jobs, server rejection/retry, double clicks and refresh failure. Application backend tests verify persistence, version checks, role scope, Helpdesk/calendar transaction handling and signatures. No permission expansion or schema change. Browser/mobile visual checks and reproduction against the deployed instance were not performed.

Final verification: all 335 Python regression tests passed, along with Application Service native Save button-click, existing workspace and customer-signature DOM tests.
