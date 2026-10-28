# Minutes and Acknowledgement

Open Staff Portal → Human Resources → Minutes and Acknowledgement.

Create either a Meeting minutes document or an Acknowledgement document. Meeting minutes support attendees, minutes text, decisions and follow-up actions. Both types support a document date, acknowledgement due date, supporting document link and selected employees.

Save a draft to continue editing, or publish to the selected employees. Drafts are visible only to their owner and authorized coordinators. Published records are visible to selected employees, their owner and authorized coordinators. Selected employees have view-only access and can acknowledge only for themselves.

Acknowledge the current revision from the document view after confirming that it has been read. The server records the employee identity and timestamp. Repeated acknowledgement does not change the original timestamp. Publishing a new revision requests acknowledgement of the new content; previous revision content and acknowledgement records are retained. A stale acknowledgement request is rejected until the employee opens the current revision.

Owners and authorized coordinators can view and export the acknowledgement register, with employee names, pending/acknowledged status and timestamps. Recipients cannot edit the document or export other employees' acknowledgement details. Published records cannot be deleted through the draft deletion action.

Roles & Permissions includes the Minutes and Acknowledgement actions. Existing roles receive only module viewing and acknowledgement access by default; server-side employee selection still restricts every document. The new Minutes Coordinator preset provides authoring and management permissions and can be assigned by an administrator. System Admin receives the full catalog. For newly created custom roles, configure their Minutes access explicitly.

Documents, revisions, acknowledgement timestamps and audit events are stored in the existing SQLite database. No emails or external messages are sent by this function.

## Attachments and meeting participants

Attach files directly while creating a document or issuing a new revision. Both document types support up to 10 files, 10 MB each and 20 MB total. Supported types are PDF, Word, Excel, PowerPoint, text, CSV, PNG/JPEG/GIF/WebP and ZIP. Files are stored in the existing database and downloaded only after the server checks access to the current document revision. Removing a file from a new revision removes its current download access; prior revision references and file bytes remain retained with the record history. Downloads use attachment disposition and are never public URLs.

Use Select all employees / Deselect all in either the view-only audience or internal attendee section. These buttons affect the whole active employee list, including employees outside the current search results. Individual selection, search and removal remain available.

For meeting minutes, select Internal attendees from active system users, enter External attendees manually, and choose the Chairman from active system users. External attendee text does not create accounts or grant document access. Historical free-text attendee content remains available as Previous attendees text.

Optionally select Create / link meeting in internal attendees’ Staff Portal calendar and enter meeting start and end times in Bangkok time. Saving a draft creates no event. Publishing creates one shared calendar event for the selected internal attendees and adds them to the document's view-only audience. Publishing later revisions updates that same event and its attendee list. Publishing a revision with calendar linking turned off removes the linked event from the active calendar; turning it back on reuses the original event identity. Calendar edits must be made through the minutes revision workflow. The event links back to the minutes, whose own access checks still apply. Calendar access also requires the employee's normal Calendar permissions; broad calendar visibility alone does not expose confidential minutes events to unrelated employees. This integration uses the Staff Portal calendar and sends no external invitations or email.
