# Report update 61

- Biomed IS Overview Details expands the selected document in place.
- All Biomed IS document types, Service jobs and Application jobs provide Print report and Email report with PDF or self-contained HTML choices.
- Print report opens the selected format for printing. Email report prepares a downloadable attachment and an editable .eml draft; it never sends automatically. Native sharing is available when supported by the device.
- Shared Biomed Diagnostics and MASCI ISO13485 letterhead, embedded Sarabun fonts and selectable report text.
- Service and Application reports use a compact A4 template including feedback, engineer/specialist printed name and the actual saved customer signature. Normal entries fit one page; long narratives or parts lists continue without truncation.
- Reports use authenticated saved records and print permissions. Application reports also enforce record visibility. New print permissions migrate from existing corresponding export grants.
- Existing signed Service snapshots remain authoritative. No fabricated signatures or approval marks. No database schema change.

Validation: PDF render review, Python regression suite and report/disclosure DOM checks. Browser and physical-device visual verification was unavailable because the preview usage limit blocked browser access. No deployment performed.

Final validation: 335 Python tests passed; report, workflow, application, signature, lookup, table-layout and disclosure DOM checks passed. All HTML inline scripts and changed JavaScript parsed successfully.
