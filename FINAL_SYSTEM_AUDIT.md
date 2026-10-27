# Final system audit — 27 October 2026

## Scope and corrections

Reviewed the supplied Python/SQLite application and its website, Staff Portal,
CRM, Biomed IS, Budgeting, integration settings, catalogue management and Copilot.
The bundled demonstration database was checked locally; your Railway database
was not accessed or changed.

Changes in this release:

- Added shared utility-page styling to AI Chat Management, OpenAI Access
  Management, Product Catalogue Management and Integration Settings: consistent
  type scale, navy/teal styling, minimum control heights, wrapping navigation,
  constrained fields, checkbox alignment, focus indicators and narrow-screen
  single-column forms. Existing main workspace headers remain in place.
- Unified private-file blocking for GET and HEAD, including encoded hidden paths,
  test source, backup, database and key files. Added HTTP regression checks.
- Kept all prior permission, quotation follow-up, Calendar/Copilot instruction,
  translation, integration and demo-data fixes.

## Verification

- Full Python suite: 153 tests passed after the final changes.
- All supplied JavaScript test files passed, including the DOM-based detail-panel,
  favorites, training, incentive and tender/pipeline interaction checks.
- Parsed 15 inline scripts across top-level HTML pages.
- SQLite integrity check: OK. Foreign-key check: zero violations.
- Permission coverage checks: all 773 catalogue entries; registered CRM entity
  actions, IS transaction views, Budgeting views, Portal module access and static
  permission checks remain consistent.
- Regression coverage includes login/session and revocation, origin checks,
  private uploads/files, own/all CRM visibility, role restrictions, shared data
  masks, bridge previews/reconciliation, stale-revision rejection, workflow
  transitions, purchasing lineage, financial calculations, stock validations,
  repeatable demo imports, ledger balances and cross-document references.

## Limits and outstanding acceptance checks

This is a local source, database and automated interaction audit, not proof that
all possible actions and configurations work. A working Chromium executable was
not available and its download failed, so pixel-level screenshots, actual
responsive geometry, print layout and visual overlap checks remain outstanding.
The shared CSS improvements have not had rendered-browser visual verification.

Live Railway deployment, your production data, real API keys/billing/models,
OpenAI/Gemini replies and external Microsoft 365 links were not tested.
Copilot remains bounded summaries plus authorized Calendar tools; it does not
provide arbitrary record editing or a complete approval inbox.

## Deploy and review

1. Deploy the updated application source through your existing GitHub/Railway
   workflow. Keep the mounted SQLite database and existing environment keys.
2. No reset, demo re-import or API-key replacement is required for these fixes.
3. Sign out, sign in again and reload the browser.
4. Check desktop, tablet and phone widths. Verify the shared header, navigation,
   main filters, long dropdown labels, detail panels and Copilot open/close state.
5. Exercise one editable record and one approval as System Admin, then repeat
   with a custom restricted role. Verify direct/API denials as well as buttons.
6. Use bridge Preview before Run on demo data. Approved demo invoices can affect
   sales totals; demo budget/stock amounts are fictional.
7. Verify a permitted cross-system Copilot question and a denied function in a
   fresh conversation, with a working paid API key and summary sharing enabled.

Existing data, credentials, role assignments and API keys are preserved by this
source update. The ZIP's bundled database remains a fictional testing fixture;
never replace an existing production volume with it merely to deploy the code.
