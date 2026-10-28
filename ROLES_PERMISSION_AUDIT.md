# Roles & responsibilities audit — 27 October 2026

Permission catalogue version: 10. Registered entries: 773.

## Corrections

- Fixed the reported `portal.isCRM.edit` failure. `isCRM` is quotation follow-up
  storage, not a permission module. Follow-up changes now require the real
  Quotation & Tender or Sales Pipeline editing permissions. Changing pipeline
  membership also requires Sales Pipeline access and edit permission.
- Validates follow-up fields/outcomes and requires a reason for Won/Lost.
- Filters follow-up records by Tender/Pipeline visibility and preserves hidden
  records when a restricted user saves another part of the workspace.
- Quotation follow-up in the Tender page now checks Tender edit permission.
  The optional IS quotation mirror is written only with IS access and quotation
  edit permission; follow-up-only users no longer attempt that IS write.
- Separated Internal Copilot, Developer guidance and AI Chat Management rows.
- Received Enquiries now has its own role-editor function heading.
- CRM function labels align with Calendar, Sales Plan, Project & Activity and
  External Helpdesk in Staff Portal.
- Role editor now shows the backend's permanent System Admin access accurately.
  Use a custom role for administrators whose application access must be limited.
  OpenAI sharing ceilings remain separate, including for System Admin.
- Catalogue upgrade preserves existing custom-role assignments and denials.
  Versioned permission-script URLs refresh the updated logic in all three apps.
- Demo import runs permission migration before storing a fresh Portal fixture.

## Audit coverage and validation

Automated catalogue checks cover literal permission checks in top-level Python,
JavaScript and HTML sources; CRM entity/action registrations; every registered
IS transaction view; Budgeting tab views; Portal module access; duplicate keys;
role migration; and the reported follow-up save/visibility/denial behavior.

Full Python suite: 150 tests passed before the final demo-migration adjustment;
the affected demo tests and catalogue audit were rerun and passed afterward.
JS workflow checks passed, permissions.js parses, and 11 inline scripts across
Staff Portal, IS and Budgeting parsed successfully.

This is a source/backend audit with local regression tests. Every interactive
role/action combination has not been manually exercised in a browser. Live
Railway and OpenAI behavior must be verified after deploying this release.

## Deploy

Update the application files in GitHub and allow Railway to deploy. Preserve the
existing SQLite volume and keys. Startup upgrades the permission catalogue;
no database reset or demo import is required. Sign out and sign back in after
deployment, then reload Roles & responsibilities. Assign desired application
access and actions to custom roles. OpenAI Access Management further limits
Copilot within those application rights.
