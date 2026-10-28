# Financial — current release

This package combines the latest Service Inventory fixes with the expanded Financial application.

Open the existing Financial application link (the compatible entry file remains `biomed-budget.html`).

- **Set targets & finalize performance:** brand/service/other-source revenue and expense budgets, independent approvals, optional period locks and authorized unlocking.
- **Finance planning & control:** commitment availability, AR/AP aging, reconciled settlements, 13-week cash forecasts by currency, monthly close checklist and audit history.
- **Express Version 1 integration:** CSV/XLSX report import, saved field mappings, Thai encoding/year handling, validation, independent review, duplicate protection, controlled reversal and normalized CSV export.

Express is the official accounting source of record. Financial supports planning, imported reporting and reconciliation; it does not write to Express or submit bank payments/tax returns.

Read **EXPRESS_V1_FINANCIAL_INTEGRATION_GUIDE.md** for report preparation and supported report types. Read **UPDATE_37_FINANCE_AND_OPTIONAL_LOCKS.md** for Finance workflows and role grants. Historical guides remain version-labelled.

Use two separate authorized staff accounts for upload/submission and independent approval. Assign additional custom roles through Staff Portal → Roles & Permissions. Catalog migration preserves existing grants and adds the documented Financial presets; no user password is changed.

Deploy the source package to update the live site. Back up the existing production database and retain it; do not overwrite production transactions with the bundled testing database. New tables are created on first use. Real Express report layouts still need validation against your first actual export; sample CSV/XLSX fixtures were used for development testing.
