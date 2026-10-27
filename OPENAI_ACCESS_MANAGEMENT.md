# OpenAI Access Management

New Staff Portal menu:
Website & Administration > OpenAI Access Management

Also linked from AI Chat Management and Internal Copilot > My API settings.
This opens inside the Staff Portal workspace. Direct page: /copilot-access.html.

Three levels:
- Role defaults: System Admin sets Copilot ceilings for every employee in a role.
- Employee limits: System Admin can narrow those ceilings for one account.
- My access: Each employee can narrow their own role/admin allowances.
Existing application permissions and global AI switches remain authoritative.

Function inventory:
Searchable groups cover Staff Portal functions, Sales Plan, Project & Activity,
External Helpdesk, Biomed IS transactions/inventory functions, and Budgeting tabs.
It is derived from the permission catalogue. Every row displays connector status.
Guidance-only rows have disabled data-access controls; these do not pretend to
offer raw-record reads or changes.

Implemented data access:
- Own permitted task/request/expense/objective counts.
- Sales Plan, Project & Activity and External Helpdesk counts using native CRM
  own/all record scope.
- Permitted IS document and inventory lot counts.
- Budgeting totals after existing financial masks and Copilot function restrictions.
- Calendar reads and event drafts requiring explicit Confirm save.
Record summaries still require the separate Share permitted record summaries
switch. Calendar reads/drafts have separate opt-ins. OpenAI keys only for record
access; Gemini record sharing remains blocked.

Enforcement:
Role permissions intersect role ceilings, employee ceilings and personal settings.
Function restrictions are applied before generating summaries; backup/export
permissions cannot bypass a Copilot opt-out. Calendar function denial disables
both tools. Settings changes have audit records. No general record write tool,
SQL, shell, source-code access or automatic bug fixing is introduced.

Deployment:
Keep your existing Railway database, volume, keys and encryption setting.
Startup adds the role-policy table. Existing role/application permissions are
not rewritten. The bundled sample database is not a production replacement.

Validation:
Six new function-limit tests, existing access and Calendar tests, AI/history and
Gemini tests pass. Authenticated local HTTP tests verified role-policy writes,
catalogue output and effective access. Main-page and new JS scripts parse.
Live OpenAI requests, Railway and responsive browser QA remain unverified.
