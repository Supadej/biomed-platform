# Financial, permissions, layout and database administration

This release extends the Express V1 / Financial package. Deploy this version to update the live site. No production database was reset or restored during development.

## Opening the controls

Sign in as System Admin. Open **Database administration** from the Staff Portal sidebar or the footer in Biomed IS / Financial. The direct entry is `database-admin.html`. The database controls have separate view, export, restore, reset and configure permissions in Roles & Responsibilities → System → Database administration. Only System Admin receives these new permissions automatically. Custom roles can be granted individual database actions; changing administrator testing mode additionally requires the System Admin role.

## Roles and responsibilities

The additive migration preserves custom grants and updates the named standard roles. Review customized roles in Staff Portal before production use. Existing additional grants are not revoked.

| Function | Default responsibility |
| --- | --- |
| Prepare and submit targets / performance | Department Manager, Accounting, System Admin |
| Department review | Department Manager |
| Finance review of target / performance submissions | Accounting |
| Final target / performance approval | Managing Director, Operations Director |
| Commitments, AR/AP records, settlements and cash forecasts | Accounting; existing Director grants retained |
| Monthly close preparation and submission | Accounting |
| Monthly close review | Accounting or authorized Director, with independent review in normal mode |
| Stage Express V1 exports | Accounting; existing Director import grants retained |
| Approve/apply/reverse Express batches | Accounting or authorized Director; independent review in normal mode |
| Configure optional locks; unlock with reason | Managing Director, Operations Director |
| Service requests, returns and stock counts | Service Engineer |
| Service issue / return / count adjustment approval | Service Manager or explicitly authorized stock approver |
| Full database backup, archive/reset and restore | System Admin; granular delegation available |

System Admin has the full catalog. The standard Director role has broad pre-existing permissions; this release does not remove them. `budget.*` remains the compatible permission/API namespace although the interface is Financial.

## Administrator self-approval for testing

In Database administration, enable **test self-approval**. It applies only to the authenticated System Admin, never merely to a user holding approval permissions. Approval permissions and workflow validations still apply. Stock availability, stale counts, finalized-period protections, duplicate import detection and other validations remain enforced.

The bundled testing database has this switch ON at the user's request. Existing installations keep normal separate-review behavior until a System Admin enables it. The current state appears in Database administration and the application access link. Each exception writes a `TEST self-approval` audit record with actor, workflow, reference and timestamp. Workflow histories remain available. Switch testing mode OFF before using independent production approvals; refresh already open workflow screens after changing it.

Covered: Service Inventory issue requests, returns and stock-count adjustments; target and monthly/half-year/annual performance stages; Express batch approval; monthly close review. Existing IS document self-approval settings are also honored, with the administrator testing exception.

## Back up only

Select **Download full backup**. A consistent ZIP captures the three applications together, account password hashes, shared brands and all database-stored attachments. A protected server recovery copy is also saved in `private-archives` next to the active SQLite database. Backups are not exposed through static file serving. Download permissions are checked for every archive request.

The archive contains `manifest.json` with SHA-256 validation and `database.json` containing typed table data. It contains no executable SQL. Keep backups private. This is an application data backup, not a server image: server environment variables, Microsoft/AI encryption keys and any files stored outside the database require a separate backup. Password hashes and encrypted connection data are sensitive. Automatic backup retention/deletion is not implemented; monitor persistent-volume capacity.

## Archive and reset

Enter a reason, type **ARCHIVE AND RESET**, and confirm the action. The server writes, flushes and verifies a complete recovery archive before clearing data. Failure rolls back database changes. Reset covers operational records across **all three applications**: IS customers/suppliers/products/stock/documents; Service jobs and inventory; CRM/calendar; minutes and acknowledgements; Portal transaction arrays; Financial targets, actuals, approvals, registers and imports.

Reset retains accounts, user profiles, roles, departments, shared brands, website catalogue/content, system configuration and migration markers. It deliberately provides a usable clean workspace without removing the administrator. It does not delete remote Outlook events. Existing sessions are signed out. Sign in and reload every open application tab afterward. No live reset was performed when this update was built.

## Import / restore

Choose a **full-system backup ZIP created by the same project version**. Arbitrary SQLite files, Express backups and the older per-application JSON exports are not accepted by this full-system restore. Continue using the Express importer for Express reports.

1. Upload and select **Validate & preview**.
2. Review backup time, application scope and per-table counts. The server dry-runs restoration on a private in-memory database and checks relational integrity.
3. Enter a reason and type **RESTORE ALL DATA**.
4. Confirm replacement. A recovery archive is saved first, and all three applications are replaced in one database transaction.

The preview expires after ten minutes and is invalidated if operational data changes. Active Outlook synchronization blocks restore/reset until it finishes. Restored workspace revisions advance to reject stale open-tab saves. A backup must include an enabled System Admin account. Restored accounts and passwords become the sign-in credentials. Sessions/OAuth handshakes are discarded; administrator audit history and the local test-mode setting are preserved rather than rolled back. Outlook connections and synchronization mappings are cleared to prevent automatic mailbox writes from restored records: reconnect and review existing Outlook copies before re-enabling event sync to avoid duplicate copies. Remote events are not removed.

## Layout changes and checks

The Save recorded actuals and Export variance CSV buttons now have separate action rows with consistent table spacing. Financial panels, inputs and wrapping actions use the same spacing and minimum touch-target sizes. Existing responsive table scroll areas and inline detail layouts are retained.

Validation: full Python regression suite; additional backup/restore, permission, stale preview, schema tampering, relational rollback and administrator self-approval tests; browser audit at 320, 390, 768, 1024 and 1440 pixels across Staff Portal, IS and Financial; actual browser backup download and restore preview. Real Microsoft mailbox changes and production deployment are outside these local checks. Existing Express mappings must still be validated against your accountant's first real export.
