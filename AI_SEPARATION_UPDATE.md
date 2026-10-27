# Separate website and internal AI assistants

## Controls
Staff Portal → Website & Administration → AI Chat Management → Enable / Disable.
System Admin or `ai.settings.manage` permission is required to change controls.

- Website live chat: controls visitor chat, including human support. Default OFF.
- Website AI replies: controls automated replies independently of human support. Default OFF.
- Internal Copilot: controls authenticated assistance across Staff Portal, Biomed IS and Budgeting. Default OFF until configured.
- Company internal key: allows employees to explicitly select company billing for internal chat. Default OFF.

Switches persist in the existing application database. Disabled services reject requests on the backend. Open widgets recheck availability every 15 seconds. Existing histories are retained when disabled.

## Credentials
- `OPENAI_API_KEY`: website AI only, unchanged.
- `BIOMED_INTERNAL_OPENAI_API_KEY`: separate optional company key for internal AI. No automatic fallback to the website key.
- `BIOMED_AI_ENCRYPTION_KEY`: existing Fernet encryption secret for personal keys; retain the same value across deployments.
- `BIOMED_INTERNAL_AI_MODEL`: optional internal model; falls back to existing `BIOMED_AI_MODEL` configuration.

Internal users select My personal API key or Company internal API key. Personal keys can be saved or removed in the internal widget. API calls occur on the server. Keys are never returned to browsers. ChatGPT subscriptions do not supply these API credentials.

## Permissions and separation
System Admin has internal access. Other staff need `ai.internal.use`, plus `is_view` for Biomed IS or `budget_view` for Budgeting. Assign permissions under Roles & Permissions. New permissions are included in catalog version 9.
Website conversations remain in the visitor inbox. Internal history is scoped by authenticated account and application; another employee cannot retrieve it. Clearing history affects the current user's current application only.

## Current capability
Internal Copilot answers workflow questions, drafts text and analyzes information supplied by the user in English or Thai. It has no live business-record retrieval, automatic saving, code execution, repository access or production repair capability. Developer troubleshooting advice can be requested in chat, but a connected developer console is future work. No page records are automatically sent to the model.

## Deployment
Preserve the production database and persistent volume. This replacement ZIP intentionally excludes the packaged `data/biomed.sqlite3`, so it cannot supply a replacement account database. Existing database tables are preserved; AI settings and internal-history tables are added on startup. Configure credentials, enable Internal Copilot, and assign user permissions. No production deployment was performed in this task.

## Verification
Five automated backend tests pass: independent switches, admin/login checks, per-user history and module access, separate company billing, and mocked internal send/history/clear. Python compilation and JavaScript syntax checks pass. Real OpenAI calls and authenticated Railway workflows were not tested. Browser visual checks could not run because the Chromium executable is unavailable; desktop/tablet/mobile visual QA remains outstanding.


## Login recovery update
Fixed a website chat MutationObserver feedback loop that repeatedly wrote its own hidden attribute while observing the entire document body. Observation is now limited to the portal container, and visibility is changed only when necessary. AI widgets are cache-versioned. On the first startup of this update, all four AI controls are switched OFF for existing installations as well as new databases. This reset runs once; later administrator changes persist across restarts. Accounts, credentials and business records are retained.
