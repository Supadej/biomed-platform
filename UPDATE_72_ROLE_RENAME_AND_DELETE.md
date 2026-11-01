# Rename or delete a role

In Staff Portal open Roles & permissions, select a role, and use the Role name / Rename role controls above Responsibilities. Delete role is alongside it. These controls require the existing Roles → Edit permission; no permission codes were added, so the catalogue remains at 888.

- Renaming updates the saved role, responsibility description, assigned directory users, login accounts and CRM identities in one transaction. Grants and stable user IDs remain unchanged. Existing document history is retained.
- Deleting an unused role removes its definition and responsibility description.
- Deleting an assigned role requires selecting a different existing Replacement role and having User directory → Assign permission. All affected users, including inactive profiles, move to that role. Their sessions are revoked so the new permissions apply at sign-in.
- System Admin and the default Employee role are protected built-in names. Clone them to create custom roles.
- Concurrent updates are rejected for review. Changes are recorded in role_admin_audit. Generic workspace saves cannot bypass the role removal controls.
- The role controls stack vertically on small screens and show errors inline. The online manual describes the new controls.

Deploy the complete project to the existing Railway service and refresh open pages. Keep the existing persistent volume. No role is renamed or removed simply by deploying this release; these changes happen only when you use the controls.
