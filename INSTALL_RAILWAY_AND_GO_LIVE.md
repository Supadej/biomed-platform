# Biomed v92 Railway deployment

This is the Railway SQLite save-safeguard release based on v88. PostgreSQL support is a separate migration. Use this guide for v92 in place of earlier deployment or Finance reset instructions.

## 1. Back up production

1. In Railway, select your Biomed project, the **Production** environment, and the existing Biomed service.
2. Record the currently deployed commit, volume mount, and exact value of `BIOMED_DATABASE_PATH`. The v88 default is `/data/biomed-staff-configured-v78.sqlite3`. Use the value from your own live service.
3. Under **Backups**, create a manual volume backup and confirm it appears. Keep a current recovery copy and record the time. Confirm the existing users and at least one known recent document in the live app.
4. Keep the existing volume and secrets. This release removes the automatic v83 Finance reset from startup.

Railway volume backup instructions  
https://docs.railway.com/volumes/backups

## 2. Deploy a staging copy

1. Unzip the release. Commit the application files to a **staging branch in your private repository**. The folder with `Dockerfile` and `railway.json` must be the repository root or the Railway service's configured root directory. Keep credentials and production database copies out of Git.
2. In Railway, create a **Staging** environment. Add a Biomed service from the staging branch. Give it its own volume mounted at `/data`. Leave production linked to its current branch.
3. Set `BIOMED_DATABASE_PATH` to the staging database file inside that volume. The release can seed a fresh staging file. If testing real record visibility or data retention, provision a separate copy of the current database using a SQLite-consistent backup. Keep staging access limited to authorized testers.
4. Set `BIOMED_ENABLE_OUTLOOK_WORKER=0` and omit production Outlook and other integration secrets in staging. Give staging its own Railway domain and allow its HTTPS origin in `BIOMED_ALLOWED_ORIGINS` if required. Use a staging database path and test accounts.
5. Deploy. Open `/api/health` on the staging hostname. Then sign in and confirm you can open Biomed IS.

Railway environment instructions  
https://docs.railway.com/environments

## 3. Verify saves before promotion

Use two browsers or private browser sessions and two staff test accounts with appropriate permissions.

| Test | Expected result |
|---|---|
| Open two quotations before either user saves. Create a different quotation in each session and click Save at nearly the same time. | Both quotations are present after refresh and have different server-assigned references. |
| Open the same draft quotation in both sessions. Make different changes in each session. Save the first, then the second. | The second session shows a conflict. After refresh, the first change is still present. |
| Repeat separate saves for orders and invoices, and exercise your usual quotation-to-order workflow. | Required document links, line items, and references are intact. |
| Two staff acknowledge the same announcement revision while an editor has it open. Save an unrelated Portal change from the editor’s session, then refresh. | Both acknowledgements remain present. Publishing a new revision requires a new acknowledgement, and the earlier revision keeps its records. |
| Test with ordinary staff roles, then redeploy staging and sign back in. | Saved records persist and visibility follows each user's existing role. |

Record the time, module, and document ID for any failure. A temporary busy response permits one retry of the rolled-back workspace save. If a browser loses its connection, check the record after reconnecting before re-entering it.

## 4. Promote to production

1. Schedule a short pause in staff edits. Create a fresh backup of the production volume.
2. Promote the tested source commit to the branch linked to the existing production Biomed service.
3. Keep the production database path and volume. Set `BIOMED_REQUIRE_EXISTING_DB=1` on that service so a wrong or missing database path stops startup. Preserve existing integration variables.
4. Deploy and wait for the health check. Confirm that the known recent document, user access, Finance balances and permissions match the existing deployment before resuming staff edits.
5. If verification fails, pause writes and review the deploy logs and database path. Roll back the application code to a known-good release that cannot trigger a pending Finance reset. Keep the current database volume in place for an application rollback. A volume restore rewinds data to the backup time and should be handled separately from a code rollback.

## 5. Activate portal.biomedthai.com

1. In the production Biomed service, go to **Settings → Public Networking → Custom Domain** and enter `portal.biomedthai.com`.
2. In the authoritative DNS provider for `biomedthai.com`, create the **CNAME and TXT** exactly as displayed by Railway. Keep unrelated website and email records intact.
3. Wait for Railway verification and HTTPS. Add `https://portal.biomedthai.com` to the comma-separated `BIOMED_ALLOWED_ORIGINS` if the service serves multiple domains. Keep only the trusted origins you need.
4. If Outlook is enabled, register `https://portal.biomedthai.com/api/outlook/callback` as a **Web** redirect in Microsoft Entra and set the identical value in `BIOMED_OUTLOOK_REDIRECT_URI`. Keep the existing Outlook encryption key. Redeploy, then test sign-in, a document save, and an Outlook connection on the new hostname.
5. Send staff the production HTTPS URL after verification.

Railway custom domain instructions  
https://docs.railway.com/networking/domains/working-with-domains

## PostgreSQL production gate

The current IS workspace stores documents in one shared JSON record. A PostgreSQL cutover requires moving document writes to independent records, preserving visibility, stock and linked-document rules, and assigning document references atomically. A database connection change alone still leaves concurrent writes competing over the same shared record.

Before a PostgreSQL cutover, import a copy of the production data into staging, reconcile row counts and document links, and test simultaneous creation, same-record edits, duplicate requests, and stock posting. Perform the final transfer during a write pause. Keep the old database available for reconciliation and establish how writes made after cutover would be carried back before planning any rollback.
