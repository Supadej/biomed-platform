# Outlook calendar synchronization

This update adds a per-employee Microsoft 365 calendar connection to Staff Portal. It is inactive until Microsoft configuration and authorization are completed. No Outlook credentials or connected mailboxes are included in this package.

## Microsoft administrator setup

1. Register an application in Microsoft Entra ID → App registrations. Use Accounts in this organizational directory only (single tenant). The integration targets Microsoft 365 work accounts in your company tenant.
2. Add a **Web** redirect URI matching the public portal URL exactly, for example `https://portal.example.com/api/outlook/callback`. For local testing, `http://localhost:8765/api/outlook/callback` or `http://127.0.0.1:8765/api/outlook/callback` can be used if registered with Microsoft. Use the same hostname to open Staff Portal so the OAuth correlation cookie returns correctly.
3. Add Microsoft Graph **delegated** permissions: `User.Read` and `Calendars.ReadWrite`. The OAuth flow also requests `offline_access` for background refresh. Apply administrator consent if required by your organization's consent policy. No application-wide mailbox permissions are used.
4. Create a confidential web application credential. This implementation uses a client secret kept only in the server environment. Set its expiry/rotation in your deployment's secret manager; do not put it in browser code, shared ZIP files or source control.
5. Install the project's existing Python dependencies: `python3 -m pip install -r requirements.txt`.
6. Configure these server environment variables and restart the server:

| Variable | Value |
|---|---|
| `BIOMED_OUTLOOK_TENANT_ID` | Company tenant UUID |
| `BIOMED_OUTLOOK_CLIENT_ID` | Registered application UUID |
| `BIOMED_OUTLOOK_CLIENT_SECRET` | Application credential secret |
| `BIOMED_OUTLOOK_REDIRECT_URI` | Exact registered Web callback URI |
| `BIOMED_OUTLOOK_ENCRYPTION_KEY` | Dedicated Fernet encryption key |

Generate the encryption key locally with:

```bash
python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

Keep this key stable across restarts and restore it together with database backups. Losing it requires employees to reconnect. Access and refresh tokens are encrypted in the existing database; they are never returned to browser APIs. Microsoft authorization codes are redacted from callback request logs.

The portal server needs outbound HTTPS access to `login.microsoftonline.com` and `graph.microsoft.com`. Register the portal's actual HTTPS hostname, configure its normal allowed origins and production HTTPS settings, and keep the server running for automatic synchronization. Polling is used, so Microsoft does not need inbound access to a webhook endpoint.

## Employee setup and use

1. Open Calendar → **Outlook calendar** → **Connect Microsoft account**.
2. Sign in using the Microsoft mailbox matching your Staff Portal company email. OAuth uses a short-lived, single-use state cookie plus PKCE. The Microsoft tenant and mailbox identity are checked before credentials are stored.
3. Open a portal event and enable **Sync this event to my Outlook calendar**, then save. Selection is personal: another employee must connect and select events for their own calendar.
4. Select **Sync now / retry** for an immediate run. Automatic synchronization checks connections about every five minutes while the server is running; a restarted server resumes the polling worker.
5. Optionally select Two-way for ordinary portal events. Accepting changes from Outlook requires the employee's normal Calendar edit permission. Minutes-linked events always follow Staff Portal, including calendar edits made in Staff Portal, and do not accept Outlook changes into issued minutes or acknowledgement records.

Only event title, start/end, all-day flag and location synchronize. Private minutes text, documents, attachments, customer details and contacts remain in Staff Portal. The integration creates individual **personal calendar copies** without adding Outlook attendees, so it sends no meeting invitations. It does not create Teams meetings or copy attachments. If someone converts a synchronized Outlook copy into a meeting with attendees or another organizer, automated writes/deletion are blocked and an error directs them to Outlook, preventing unintended meeting updates or cancellations.

For an ordinary event, a change on only one side is synchronized in the selected direction. If both sides changed since the last successful sync, a conflict appears in the connection screen. Choose Keep Staff Portal version or Keep Outlook version, then synchronize. Graph conditional updates also detect remote changes during a write. Unsupported recurring changes are flagged for review rather than modifying a series.

Portal event deletion, cancellation by removing a minutes calendar link, or loss of visibility removes the corresponding app-created personal Outlook copy on the next successful sync. Deleting an Outlook copy does not silently delete the shared portal record. The screen offers Recreate Outlook copy. Pausing an event stops future sync and retains its existing Outlook copy. Disconnecting removes stored tokens and private cached events, pauses selections, and retains existing Outlook copies; reconnect and resume selections to continue. Reconnect while a sync is running may require waiting for that run to finish.

## Private Outlook display

Enable **Show my other Outlook events privately in the portal calendar** to display other primary-calendar events from the previous 180 days and next 365 days in the month/week/day calendar. They are marked Outlook (private), visible only to the connected account, and excluded from shared portal records, CRM exports and analysis. Open them in Outlook to edit. Their cached fields contain only title, timing, location and Outlook link. The option does not import them as shared CRM events. Private overlays are hidden when filtering by a responsible employee, and respect calendar date/search filters.

This release uses each user's primary Outlook calendar. Choosing other/shared calendars, Outlook recurrence creation, mailbox-wide unattended application permissions and real-time webhook subscriptions are not included.

## Monitoring and recovery

The connection screen shows the mailbox, last synchronization, selected events, event errors, conflict actions and that employee's sync activity. Background jobs re-check current account status and permissions. Disabled staff cannot synchronize. Per-account database leases prevent concurrent manual/background sync runs. Event transaction IDs prevent duplicate creation after uncertain network retries, and immutable Graph IDs keep links stable when supported mailbox moves occur. More than 100 selected events are processed in rotating batches across runs.

Use Sync now / retry after a transient failure. Reconnect after authorization revocation or token expiry that cannot be refreshed. For HTTP 429 throttling, retry later rather than repeatedly clicking. Company permission removal stops sync; copies already in a disconnected or disabled employee's mailbox require your normal Microsoft 365 offboarding controls.

## Validation and deployment

Automated tests use a simulated Microsoft Graph service for OAuth correlation, PKCE, token encryption/rotation, duplicate prevention, direction/conflicts, minutes ownership, private cache isolation, deletion/recovery, all-day handling, access restrictions and authenticated endpoints. Browser checks exercise the portal screens. A live Microsoft tenant sign-in and end-to-end smoke test are still required after your administrator configures the app; no real mailbox has been connected or modified during development.

Official references:
- https://learn.microsoft.com/en-us/graph/auth-register-app-v2
- https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-auth-code-flow
- https://learn.microsoft.com/en-us/graph/api/user-post-events?view=graph-rest-1.0
- https://learn.microsoft.com/en-us/graph/api/event-update?view=graph-rest-1.0
- https://learn.microsoft.com/en-us/graph/outlook-immutable-id
- https://learn.microsoft.com/en-us/graph/api/calendar-list-calendarview?view=graph-rest-1.0
