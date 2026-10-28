# Minutes and Acknowledgement

Open Staff Portal → Human Resources → Minutes and Acknowledgement.

Create either a Meeting minutes document or an Acknowledgement document. Meeting minutes support attendees, minutes text, decisions and follow-up actions. Both types support a document date, acknowledgement due date, supporting document link and selected employees.

Save a draft to continue editing, or publish to the selected employees. Drafts are visible only to their owner and authorized coordinators. Published records are visible to selected employees, their owner and authorized coordinators. Selected employees have view-only access and can acknowledge only for themselves.

Acknowledge the current revision from the document view after confirming that it has been read. The server records the employee identity and timestamp. Repeated acknowledgement does not change the original timestamp. Publishing a new revision requests acknowledgement of the new content; previous revision content and acknowledgement records are retained. A stale acknowledgement request is rejected until the employee opens the current revision.

Owners and authorized coordinators can view and export the acknowledgement register, with employee names, pending/acknowledged status and timestamps. Recipients cannot edit the document or export other employees' acknowledgement details. Published records cannot be deleted through the draft deletion action.

Roles & Permissions includes the Minutes and Acknowledgement actions. Existing roles receive only module viewing and acknowledgement access by default; server-side employee selection still restricts every document. The new Minutes Coordinator preset provides authoring and management permissions and can be assigned by an administrator. System Admin receives the full catalog. For newly created custom roles, configure their Minutes access explicitly.

Documents, revisions, acknowledgement timestamps and audit events are stored in the existing SQLite database. No emails or external messages are sent by this function.
