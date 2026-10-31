# Staff, reporting hierarchy and role access update

**Follow-up applied:** the 35 original workbook application-access conflicts are
resolved in this release. See `ACCESS_RESOLUTION_20261031.md` and the resolution
CSV reports for the 33 gate additions and five isolated permission removals.
The original workbook descriptions below document the initial import.

This release applies the approved workbook dated 31 October 2026.

## Applied configuration

- 44 existing accounts matched by login email. Names, supplied passwords, roles,
  departments and Reports to are mapped without changing account or staff IDs.
- 42 reporting links and two top-level users. All manager names resolve and the
  hierarchy has no cycles.
- 29 role configurations, including HR Manager which currently has no listed user.
- All 889 permission choices per role are applied exactly: Y grants, N removes.
- All 62 visibility settings per role are applied exactly: A = all,
  D = department, R = reporting team, OR = own, OS = own plus assigned.
- Existing role responsibility descriptions are preserved. The workbook has no
  replacement responsibility text.
- The other 23 staff profiles remain unchanged. Two use roles configured by this
  workbook, so the updated permissions also apply to them. Roles are shared.

## Important access conflicts

See `setup-reports/Biomed_Access_Setup_Conflicts.csv` for 35 application-access
conflicts. For example, Sales Representative has individual Biomed IS permissions
marked Y but `is_view` (Biomed IS application access) marked N. Those permissions
cannot be used until application access is enabled. The import preserves N and
does not silently expand access. CRM has the same dependency on `crm_view`.

To resolve a conflict, an authorized administrator can use Staff Portal > Roles &
permissions, select the role and enable the required application-access checkbox.
Visibility alone never grants module access or edit/approve rights. System Admin
retains its existing unrestricted recovery access.

## Deploy to your existing Railway database

1. Keep the existing Railway persistent volume and BIOMED_DATABASE_PATH setting.
   Do not replace or upload a seed database over the live database.
2. Update the GitHub application source with this release, including the new
   `company_access_import.py` and `company-access-workbook-20261031.json` files,
   and the changed `serve.py`. Keep the JSON file: it contains the import mapping
   and salted password hashes, not plaintext passwords. The web server blocks it.
3. Redeploy the Railway service. The existing production startup calls
   `prepare_database`, saves a private recovery archive and applies the migration
   in one database transaction. An identity mismatch aborts the deployment import
   without leaving a partial mapping. Review Railway logs if startup fails.
4. Affected sessions are invalidated. Sign in again with the workbook credentials.
5. Check User Directory > Reports to, Roles & permissions > Record visibility,
   and a representative employee login. The online manual reflects current access.
6. Review the access-conflict CSV before staff acceptance testing.

The migration runs once. Subsequent password, hierarchy, role and visibility
changes made through the application are retained on restart/redeployment.
The older roster migration runs first when upgrading an older installation.

## Recovery

The pre-import archive is saved beneath the database directory in
`private-archives`. Use your existing database-administration recovery process.
Keep a copy of the persistent database/volume before any manual recovery.
Restoring pre-import data intentionally restores its old accounts and access.
The bundled database is already updated for local testing; it is not a replacement
for the company live database.

## Setup reports

`setup-reports/Biomed_User_Reporting_Mapping.csv` lists the applied users and
managers without passwords. `Biomed_Role_Visibility_Applied.csv` lists every
submitted visibility selection. `Biomed_Access_Setup_Conflicts.csv` lists
application-access conflicts requiring review.
