# Individual Copilot access

Open AI Chat Management > My Copilot access / Employee access limits, or open
/copilot-access.html directly while signed in. Copilot also links to this page
under My API settings. Settings remain accessible if the user disables Copilot.

System Admin:
Choose an employee and set their maximum enabled modules, personal/company key
use and record-summary sharing. This never grants a role permission.

Employee:
Enable/disable Copilot, choose allowed modules and key sources, and optionally
share authorized summaries. Role permissions and admin limits always win.
ai.internal.use is required for ordinary employees; is_view and budget_view are
also required for their corresponding modules. Developer guidance requires
ai.developer. System Admin access can also be narrowed using these settings.

Effective access = current role permissions intersect admin limits intersect
employee choices, plus the global AI service switches. Preferences are saved per
account; preference changes have an audit trail. Direct API requests are checked.

Optional data access (OFF by default):
- Staff Portal: counts of explicitly owned permitted tasks, requests, expenses
  and objectives; no employee profiles or text from those records.
- Biomed IS: counts of documents the user can view, and permitted lot count.
- Financial: fiscal-year totals after the existing role/financial masks.
- Developer: guidance only, no source files, logs, shell or SQL access.
Summaries are sent only with an OpenAI key and explicit user/admin permission;
Gemini summary sharing is blocked. Calendar event titles/times and confirmed creation are now available via the separate opt-in Calendar tools (see COPILOT_CALENDAR_INTEGRATION.md). Other raw record retrieval, unrestricted search,
record changes and automatic bug fixes are not included. Summaries are not stored
as user messages, though model replies can contain their derived totals.

Deployment:
Keep the existing Railway database, volume, API keys and encryption secret.
Startup adds access-preference and audit tables without replacing accounts.
Existing chat usage retains role-limited access; data sharing starts OFF.

Validation:
Access tests cover self-elevation attempts, admin restrictions on direct requests,
personal/company key restrictions, ownership filtering, financial masks, opt-in
summary injection, validation and audit. Existing AI/history and Gemini tests pass.
A real local HTTP test covered seeded login, schema migration, settings persistence,
and administrator account listing. No real model call, Railway test or responsive
browser test was performed.
