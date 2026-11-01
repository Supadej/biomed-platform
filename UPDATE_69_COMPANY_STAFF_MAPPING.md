# Staff roster mapping and deployment

The supplied workbook maps 44 existing login accounts to 28 roles and 11 departments. Names, login emails, supplied passwords, role titles and departments are applied exactly. Existing IDs, business records, photos, mobile numbers, reporting lines and other profile data are retained. Forty-three passwords change; the administrator password already matched.

## Deploy on Railway

1. Deploy this complete project to the existing Railway service, keeping the existing persistent volume and database variables.
2. On the first startup, a verified recovery archive is saved before the roster import. It is available under Database administration → Saved recovery archives.
3. The import updates matching accounts by login email and retains their stable user IDs. The bundled database already contains the mappings. An existing Railway database receives the same one-time import.
4. Affected sessions are revoked. Sign in using the login email and password in the supplied workbook. All listed emails currently use example.invalid exactly as supplied.
5. Open User directory to review the 44 profiles, Departments and Reports to. Review Roles & responsibilities or COMPANY_ROLE_AUTHORIZATION_69.html for default grants.
6. Later password resets, profile changes and role edits are not overwritten on the next deployment. The import has a one-time migration marker. Do not delete it to repeat the import.

## Mapping decisions

- The 23 existing accounts omitted from the workbook remain unchanged. No unrequested accounts are deleted or deactivated.
- Eleven roster departments are added to the reference list. Existing department names remain for the other users and historical continuity.
- Supervisors receive the same functional management tier as managers: sales, engineering service, procurement, or delivery respectively. This does not give every supervisor system administration or finance access.
- Source contains no Reports to column. Existing reporting assignments are retained; 13 imported users report to unlisted accounts and need review before live approvals. No reporting relationships were guessed.
- Existing disabled accounts remain disabled.
- Existing document history is preserved. Linked records continue to refer to the same account/user IDs.
- The new import payload contains salted password hashes only. The source workbook is not included; use your original workbook for the supplied login credentials.
- The online manual reflects the imported roles and responsibilities automatically.

See COMPANY_ROLE_AUTHORIZATION_69.html for a detailed, expandable permission matrix.
