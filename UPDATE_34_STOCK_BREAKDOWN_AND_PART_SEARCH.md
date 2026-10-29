# Update 34 — stock breakdown layout and service part search

Service Inventory Details now opens a separate, responsive stock breakdown dialog. Engineer, product ID, lot, expiry and quantity appear in labelled cards. There is no nested table or Columns control inside the summary cell, so opening Details cannot widen or crop the main register.

The service-job search previously removed catalogue entries whose declared brand/model did not match the selected instrument. This could show “No matching records” even though that product had Service Inventory stock.

All declared IS-backed parts are now searchable by catalogue number or name. Results show compatibility, the selected stock holder's usable quantity and the visible total. Entries declared for a different instrument brand/model are visible with a clear “Not compatible” label and are disabled. A service manager can correct or add an approved catalogue mapping to the intended instrument; compatibility is not silently bypassed. Brand/model comparisons now tolerate case and whitespace variants, with Unicode normalization. Server validation retains the compatibility check.

Inventory availability and catalogue compatibility are separate: stock may exist for another engineer or another instrument model. Selecting the correct stock holder still controls whose stock is deducted. Existing usage saves remain idempotent, and expired lots are excluded from new usage. A part with no IS-backed spare-part declaration receives a specific catalogue message instead of a generic stock failure.

Validation passed for stock breakdowns at 320, 390, 768, 1024 and 1440 pixels with no page/dialog overflow or nested tables. Browser testing searched the exact BMD-TEST-SPARE-7 number, showed its availability, explained an incompatible part, saved the compatible job, and confirmed a one-unit deduction from the selected holder. Service reference and inventory tests passed. No QA deductions or catalogue changes were made in the packaged database. This package has not been deployed to the live site.
