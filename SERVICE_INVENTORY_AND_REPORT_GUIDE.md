# Service reports, calendar and engineer Service Inventory

## Service Job Report

Service jobs now generate an authenticated PDF using the supplied FM-FSE-01 form as its page background. The original company heading, logo, section headings, checkbox layout, form identifier, Rev. 01 and effective date 18 AUG 2025 are retained. Long content continues on extra pages with updated page numbering. The bundled Sarabun font supports Thai and English; its Open Font License is included.

Open Instrument Service → Service jobs → Details → View / print PDF. The existing Print report action also opens this PDF for service jobs. Report generation requires Service jobs View and Print permissions. An immutable PDF snapshot is cached against the input data version. The template/font source directory is not publicly served.

Problem/Error Code uses Diagnosis, falling back to Description. Solution/Action uses Action taken, falling back to Description, followed by Result. Parts come from the job and unambiguous historical replacements. Report-specific fields and customer ratings are in the expandable Service report information and customer feedback section. Blank ratings remain blank. Printed signatory names are not digital signatures or evidence of signed acceptance.

Install the updated requirements or rebuild the Docker image. PDF generation uses PyMuPDF. No browser plugin is required.

## PDF and email

Prepare PDF for email generates the report, then offers:
- Open email / share with PDF: supported devices open their share sheet with the PDF file and job number supplied as title. Choose the mail application and review its draft. Subject handling depends on the mail app.
- Download email draft (.eml): an unsent MIME draft containing the PDF attachment and a subject equal to the job number. Open it in an app that supports .eml drafting. Some apps open this format as a preview instead of a composition window.
- Download PDF and Open email draft: universal fallback. The mailto draft has the job number as subject; attach the downloaded PDF manually.

Browsers cannot reliably attach local files through a mailto link. The system does not send email or silently launch a device application. Sharing requires the user's action.

## Service job calendar option

Select Add / update this service job in Staff Portal calendar, choose its Calendar date (or use the scheduled/service date), and save. The title is Job No. · Location · Date. An all-day event is assigned to the engineer. Missing location is stated explicitly.

Later saves update the same event. Turning the option off removes the linked event from the active calendar. Maintain source-linked job events through the service job. Calendar create/edit permission is required for changes, and assignment to another engineer requires Calendar assign permission. The job Details view links to its event. Outlook export remains an individual opt-in from Calendar.

## Engineer inventory workflow

Open Biomed IS → Warehouse & Inventory → Service Inventory, or My Service Inventory in Instrument Service.

| Tab | Purpose |
|---|---|
| Service Inventory | Current engineer balances by product, lot and expiry; request approvals |
| New Request | Request declared spare parts from existing warehouse lots |
| Return | Request return of unused parts to an existing warehouse |
| Track Record | Issue, usage, reversal and return ledger with job drill-down and authorized CSV export |

Approve a buffer of commonly needed parts per engineer, rather than requiring approval for each repair. Job usage then consumes this approved buffer immediately.

1. An engineer submits a request. Pending requests do not move stock.
2. A different approver approves. Warehouse stock decreases and engineer custody increases atomically. A requester or receiving engineer cannot approve their own request, including administrators.
3. Adding spare parts to a job consumes the selected engineer's available stock, earliest expiry first. There is no second warehouse deduction or additional job-usage approval. Insufficient or expired stock blocks the job save.
4. Unchanged saves do not deduct twice. Quantity edits reverse and repost the allocation atomically. Changes involving another engineer's custody require inventory approval permission. The ledger retains all corrections.
5. Return unused parts using Return. A different approver verifies and approves the return. Custody decreases and the warehouse receives the original product, lot and expiry. Approval rechecks the current engineer balance; stock used since submission cannot be returned again.

Approvals validate warehouse quantity, expiry, quarantine state and request version. Duplicate approvals and negative balances are blocked. Products with inventory history cannot be deleted; deactivate them instead. Approved stock postings cannot be altered in ordinary workspace saves. Transfers update the same IS workspace revision and physical movement ledger; concurrent stale saves must merge or reload.

Existing service history is baselined during migration. It is not retrospectively deducted, and reducing a historical quantity does not create a fictitious return. An increase beyond the historical quantity requires available buffer stock. This is operational custody tracking, not a new general-ledger accounting integration.

## Responsibilities and permissions

Service Engineer and existing service-edit roles receive inventory View, Request, Return and Consume access, plus basic Calendar access for service work. Service Manager and existing service-manage roles receive approval/export access. Existing warehouse-transfer approvers receive inventory approval access. System Admin receives the new catalog actions; self-approval remains blocked. Assign a separate approver before live use.

Custom roles remain configurable in Roles & Permissions. Unrelated denials are preserved. Ordinary employees receive no Service Inventory access. Engineers reconcile their held stock and actual job usage. Approvers verify replenishment lots and physically returned unused items. Managers reconcile issued quantities against held, consumed and returned quantities using Track Record.

## Deployment and validation

Back up the live database, deploy/rebuild this package, assign approvers and test a small transfer before issuing buffers. No QA requests, balances or test jobs are included in the delivered database. The package is not automatically deployed.

Validation covers separate approvals, stale/duplicate decisions, negative-stock prevention, unchanged saves, corrections, pending returns, atomic batch rollback, protected postings, historical baselines, calendar reuse and PDF access/overflow. Browser tests cover requests, approval, job consumption, PDF/mail preparation, return approval, tracking and widths 320–1440 px. Generated PDF pages are visually inspected against the supplied form. Device-specific native mail handoff still needs a check on the engineers' actual phones/mail applications.
