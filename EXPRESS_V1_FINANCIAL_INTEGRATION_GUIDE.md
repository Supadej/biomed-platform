# Financial — Express Accounting Version 1 integration

The application formerly labelled Budgeting is now labelled **Financial** across navigation, headings, permissions, integrations, help text and Thai translation. Existing database keys, permission prefixes and the biomed-budget.html entry URL remain compatible, so saved records and links keep working.

This release also includes optional period locking and the new Finance planning workspace described in UPDATE_37_FINANCE_AND_OPTIONAL_LOCKS.md.

## Integration route for Express Version 1

Use a reviewed export/import workflow, without assuming Express API support or writing into its database. Express remains the accounting source of record.

Official Express instructions: https://esg.co.th/tiptech/showcont.php?clid=374

The official guide documents choosing the report, selecting Export to Excel, output to a data file, standard SDF file type, and saving with a .CSV extension. Its described workflow requires a program build dated 10 April 2019 or later; older installations may need the vendor's supported export procedure. This implementation also accepts reports saved as XLSX after cleanup.

1. In Express, export the relevant report with the correct company, dates and report scope. Keep the original file with your accounting supporting records.
2. In Financial → Express Version 1 integration, choose report type, legal-company name/code and as-of date.
3. Select CSV encoding: UTF-8, Thai Windows-874 or UTF-16. Select the delimiter and header row, or an XLSX worksheet name. Two-digit dates require an explicit CE/Thai-BE interpretation; four-digit BE years are converted to CE.
4. Preview source rows. Remove report titles, subtotals, grand totals, blank/merged header columns and duplicated rows. Preserve account and document codes as text. XLSX must contain values rather than formulas; CSV exported by Express is preferred.
5. Map Express headers to Financial fields. English and common Thai headings are suggested; constants can fill missing fields such as currency, source type or cost center. Save the profile to reuse it for the next export. Download a normalized CSV header template if the report needs preparation.
6. Validate and stage. Errors identify the row and issue. No actuals, balances or accounting records change at this stage.
7. Another authorized reviewer checks company, as-of date, row count, preview and currency-specific control totals, then approves or rejects the batch. No user may approve their own upload.
8. Download the normalized register for reconciliation. Import history retains the source filename, SHA-256 file hash, normalized records, submitting/reviewing employees and timestamps. The original uploaded file bytes are not retained; retain the original export separately.

## Supported report coverage

| Express report | Financial function | Effect after approval |
| --- | --- | --- |
| Monthly revenue / COGS / expense totals | Brand/service/other-source actuals, budget variance and performance approval | Replaces only included source/cost-center/month totals; never adds the same monthly total twice. Source names must match existing Financial target sources. |
| Customer outstanding report | Receivables aging and cash forecast | Reconciles matching IS invoice references instead of creating a duplicate; otherwise creates an external opening/outstanding balance. |
| Supplier outstanding report | Payables aging and cash forecast | Creates or updates the identified supplier outstanding balance. Later snapshots preserve its identity; same-date corrections require reversal. |
| Chart of accounts | Reviewed account register | Retains account code/name/category for reference and reconciliation. |
| General ledger | Reviewed journal register | Requires debit/credit balance by currency and document; does not silently post a second set of actuals. |
| Trial balance | Reviewed trial-balance register | Requires debit/credit balance by currency. |
| Bank statement | Supporting bank reconciliation register | Retains bank account, reference, date and debit/credit; settlement application remains an explicit Finance reconciliation action. |
| VAT report | Supporting tax register | Retains reported taxable amount and tax, including signed corrections; no automatic tax filing. |
| Withholding report | Supporting withholding register | Retains reported amounts/tax and party tax ID; no automatic filing or tax-rate inference. |
| Fixed-asset report | Asset/depreciation register | Checks cost minus accumulated depreciation equals net book value; no duplicate depreciation posting. |

The report registers support review and reconciliation. They do not recreate every Express posting screen, statutory form, payroll calculation or vendor-specific report. Continue using Express for the official accounting books and filings.

### Actuals and source mapping

Use the Actuals report type for totals you want published to Financial's monthly reports. Its fields are date, kind (Revenue/COGS/Expense), source, costCenter, amount and currency. Revenue sources can be shared brands, named services, miscellaneous and other income. Currency must already be THB; this import does not invent FX rates. Explicitly map an Express account/category to the correct Financial source, or prepare grouped monthly totals in the normalized template.

Imported GL/trial-balance rows are not also posted into actuals, preventing double counting. Negative net actuals are supported where accounting credits/reversals make them appropriate. Period locks apply to imported actuals and reversals.

### AR/AP reconciliation snapshots

Customer/supplier reference, currency and name are checked against existing balances. Differences require master-name reconciliation before application. Matching IS invoices receive an Express outstanding snapshot; their source invoice is not rewritten. The snapshot is the balance as of its date, so later verified settlements reduce it while earlier receipts/payments are treated as already included. For external balances, a newer Express snapshot updates the existing identity rather than appending another balance.

A new export for the same report type, legal entity and as-of date cannot silently overlap an active imported report. Duplicate files are blocked. To correct it, an authorized reviewer reverses the original with a reason, then imports the corrected file. An import cannot be reversed over a later balance update or edited actuals; reverse newer imports first and resolve linked settlements. Finalized actual periods must be unlocked before correction.

### Safety and access

- Roles & Permissions → Financial: Express view, stage/import, review, relevant actual-entry permissions and period unlocking are separate grants.
- Accounting/Managing Director/Operations Director presets gain Express viewing/staging. System Admin receives all catalog permissions. Reviewers still cannot approve their own imports.
- Imported legal entities cannot be mixed in the same installation's active import scope. Use a separate workspace for another company.
- Only CSV/XLSX reports are accepted, up to 10 MB and 10,000 rows per file. Express backups, database files, macros, legacy XLS and executable files are not accepted.
- Monetary validation, period-lock checks and application/reversal run in one database transaction. Stale import decisions are rejected.
- Control totals remain separated by currency. AR/AP snapshots, bank balances and forecasts must be reconciled to Express and bank supporting records.

## Practical first rollout

Start with one small export of each report your team actually uses: customer outstanding, supplier outstanding, monthly revenue/expenses and trial balance. Save a mapping profile for each layout, compare totals with Express, then have a second employee approve it. Repeat future imports using the saved profiles.

The connector was tested with CSV/XLSX fixtures, Thai Windows-874, BE/CE dates, balanced/unbalanced journals, duplicate detection, source reconciliation, reversals and protected periods. Your accountant's actual Express exports have not been supplied, so report-specific layout mapping must be validated on the first real import.
