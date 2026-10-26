# Native Staff Portal CRM — rebuild

The four Staff Portal pages now call `/api/staff-crm/<module>/<action>` directly; they no longer depend on the legacy CRM browser client or its `/biomedapi/` endpoints for record creation.

Modules:
- Overview > Calendar: events, schedule, customer, participants, status, priority.
- CRM > Sales Plan: leads, status, customer, value, targets, attainment, incentive gate; manual record entry and selected-document lead creation from Biomed IS.
- CRM > Project & Activity: projects, owner, team, progress, deadline and stage.
- CRM > External Helpdesk: customer tickets, assignment, category, priority, statuses, resolution.

Storage: new `staff_crm_items`, `staff_crm_audit`, and `staff_crm_import` tables in the existing configured SQLite database. Automatically created during server startup. Legacy CRM records are imported once into the new tables; ORIGINAL CRM records are NOT deleted. Legacy payloads are preserved in `legacyData` for reconciliation. This is a one-time copy, not a live two-way sync. No production data will be removed by this change.

IMPORTANT: Deploy with your existing persistent Railway volume and `BIOMED_DATABASE_PATH=/data/biomed.sqlite3`. Do not replace the live database with the demo DB in the project ZIP. Back up the production DB and test on a staging copy before deployment. SQLite must use a persistent volume and single writer instance.

Current scope / known limitations:
- Provides reliable create, read, update, delete for native records with backend validation.
- Existing legacy related activity/ticket child tables, attachments, user assignments and sophisticated CRM reports are not yet fully migrated into the new native workflows. Legacy CRM remains in the package for recovery.
- Document lead generation uses the existing Biomed IS `documents` table and explicit user selection; continuous background synchronization is not implemented.
- Incentive schemes: server enforces >=100% attainment when a scheme label is set, but selecting an authenticated scheme ID from the Staff Portal incentive subsystem, payment approval flows, and target period reconciliation require further integration. Do not treat typed labels as approved incentive payouts.
- Permission access reuses existing Staff Portal permissions (dashboard, pipeline, tasks, helpdesk) and is checked on the server. For production, define independent CRUD capabilities in Roles & Permissions.

Local verification: Python compile checks, JS parse check, SQLite in-memory CRUD, repeated legacy import, duplicate document prevention, and incentive threshold checks. End-to-end browser and deployed Railway checks remain required.
