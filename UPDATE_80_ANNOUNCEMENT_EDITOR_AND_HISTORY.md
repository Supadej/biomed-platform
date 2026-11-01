# Announcement editing and revision history — v80

## Use
Staff Portal → Announcements.
- Use the search field to filter notices by title or message.
- Click Edit announcement. The complete title, issuer, multiline message, acknowledgement requirement and attachment controls appear together at the top of the page.
- Update several fields and attachments in one form, add a revision note, then Save new revision. Cancel editing discards the form changes.
- Existing files remain unless selected for removal. New files can be added together; the original 25 MB/file limit remains. File changes require the existing announcement Upload permission. Content edits require Edit permission; creating notices requires Create permission.
- A save with unchanged title/message/issuer/requirement/files does not create another revision.
- Click View revision history on a notice to expand earlier versions. Each version shows its title, message, issuer, acknowledgement requirement, editor, timestamp, change note and file references. Historical attachment downloads use retained stored files.
- Existing acknowledgement records are carried forward unchanged and remain tied to their original revision. Employees acknowledge a newly published revision separately. The current acknowledgement register remains available to editors.

## History and access
Snapshots are created by the server in a separate announcement_revisions table after existing workspace permission and concurrency checks pass. Browser-supplied editor names and version increments do not determine the stored editor/version. A content/file edit increments the server's version; acknowledgement-only changes do not create another content revision. There is no UI to edit or remove earlier snapshots.

For existing notices, the current version is preserved as a baseline when it is first revised. Earlier versions that were never recorded cannot be reconstructed. A legacy baseline uses the original stored issuer/date and is marked as such, rather than inventing an earlier editor or timestamp.

Revision history requires signed-in announcement View access. It remains limited to announcements available in the current workspace. Upload and edit permissions remain separate; this release does not change staff roles or grants.

## Deployment
Replace matching code files in the existing GitHub repository and deploy the new commit. KEEP the existing Railway volume and BIOMED_DATABASE_PATH. Do not change to another database filename or replace the mounted database with the ZIP's starter database.
The new history table is created additively at startup. Existing announcements, files, staff accounts, permissions, financial references and budgets are not reset. /api/health reports announcement-history-v80 once this code is active.

## Checks
- Automated tests passed for server-controlled revision numbering, original snapshot retention, legacy baseline capture, and acknowledgement preservation.
- Existing finance and staff configuration/restart tests passed.
- Python and all inline/external JavaScript syntax checks passed.
- Bundled starter database is unchanged from v79.
- Actual Railway deployment and browser visual testing have not been performed here.
