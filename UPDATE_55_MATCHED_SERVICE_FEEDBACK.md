# Application feedback matches Service Job

The Application Job report feedback form now uses exactly the Service Job feedback fields, labels, order and choices:

1. Feedback Solved — Yes / No
2. Feedback Speed — Excellent / Fair / Needs improvement
3. Feedback Preparedness — Excellent / Fair / Needs improvement
4. Feedback Courtesy — Excellent / Fair / Needs improvement
5. Feedback Satisfaction — Excellent / Fair / Needs improvement
6. Feedback Comment — full-width text area

The grid uses the same responsive field sizing as Instrument Service, with dropdowns sharing a row when space allows and stacking on phones. The comment spans the complete grid width. Customer signature remains optional below the feedback fields.

Area code, Department, Instrument warranty and Instrument ownership are no longer shown as inputs in this feedback section. Previously saved values remain stored and are preserved when an existing job is saved. No backend, database, permissions or calendar changes.

Validation: Application Service DOM checks compare the generated feedback field order with the Service Job schema and verify matching labels/options, optional inputs, form save behavior and signature handling. JavaScript syntax checks pass. Fresh visual preview was not rerun; browser verification remained unavailable after the previously reported browser usage-limit rejection.
