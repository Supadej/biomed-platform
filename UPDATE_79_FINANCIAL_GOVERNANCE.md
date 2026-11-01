# Financial governance and shared reference lists — v79

## Deploy as an update, keeping your database
Upload this project's contents to the same GitHub repository root and deploy the new commit. KEEP the existing Railway volume and BIOMED_DATABASE_PATH used by v78 (normally /data/biomed-staff-configured-v78.sqlite3). Do not change to a new database filename for this update. The bundled starter still contains the same 44 users, but an existing mounted database is retained and not overwritten. Back up your current database before deploying.

/api/health should report financial-governance-v79. All existing staff roles, passwords, scopes and reporting links are retained. No staff reimport or database reset runs at startup. The new financial_references table is additive and initialized lazily.

## Financial reference lists
Open Financial → Cost center management, or Annual budgets & monthly approvals → Reference Lists.
Create cost centers and Service / expense / other source references. Sources have one of six budget categories. Both lists support editing unused names and activation/deactivation. Linked names cannot be renamed silently; deactivate and add a replacement to preserve historical linkage.
Cost centers are shared across fiscal years. Existing cost-center names found in stored workspaces are incorporated when the list is first initialized. Historical/inactive selections remain visible for existing records. New budget lines must select active references.
Cost-center form selectors throughout pages loaded by the project use the shared list; text inputs named costCenter are converted into dropdowns. Reference creation remains a name input intentionally. Existing record values and import values are not silently recoded.

## Budget workflows
Financial → Annual budgets & monthly approvals now separates Budget Setting, Budget Approval, Actual Expense Recording, Budget vs Actual, and Reference Lists.
Budget Setting has six selectable category views: Revenue Target, Product Cost of Sales, Other Cost of Sales, Personnel & Benefits, Travel & Training, and Other Operating Expenses. These views belong to one annual plan, with twelve monthly allocations, rather than six unrelated approval stores.
New lines select shared cost centers and managed sources (or a shared brand for brand-based Revenue/COGS). Choose a budget owner. Owner, comments and supporting documents can be edited under each line before submission. Up to three PDF/PNG/JPEG files, 1 MB each; new uploads replace the line's existing files. Documents are stored within the permission-protected governance record. Submit the whole annual plan after saving your allocations.

Department review follows the direct reporting managers of line owners, as recorded in Staff Portal. Every applicable manager must approve before the submission advances. The manager must ALSO hold budget.approvals.department_approve. Finance and Director stages continue to require their existing role permissions. If an owner has no manager, assign a reporting manager or use the existing explicitly enabled System Admin testing override. No new permissions have been silently granted to workbook roles.
Approve, Return and Reject are available. Return/Reject require a reason; rejected/returned drafts are archived when revised or resubmitted. Approved annual versions and monthly snapshots remain retained. An older approved monthly allocation remains effective while a replacement is reviewed. Approved plans cannot be edited directly through the legacy workspace endpoint.
Monthly approvals activate that month's allocation. Individual Staff Portal requests/payment approvals remain separate. Optional monthly/half-year/annual performance finalization and reopening remain available for closing recorded actuals.

## Monitoring and integration
Budget vs Actual compares recorded actuals and booked commitments to monthly-approved allocations. Finance planning & control provides the more detailed availability calculation, including mapped additional unbilled POs. Annual workbook/P&L reports continue to show annual PLANNING figures; they are not an authorization to spend the full annual plan.
Staff Portal expense mapping now permits Other Cost of Sales targets in configuration, previews and postings. Configure/enable the existing Staff Portal–Financial bridge and explicitly map source categories/departments to expense lines. Approved IS POs can continue to be mapped in Finance planning & control. These are explicit reconciliation workflows, not automatic posting of every transaction in every system. Review duplicate-counting flags before reconciliation.

## Checks and limits
Automated checks pass for reference validation, supporting-file metadata, reject/resubmit history, reporting-manager enforcement, monthly activation and approved availability. Staff preservation/restart checks pass. Python and JavaScript syntax checks pass. The starter SQLite file remains identical to v78, and all tests use temporary database copies.
Actual Railway deployment and full browser visual QA have not been performed here. Existing annual reports deliberately retain planning values, and integrations still require configured mappings/reconciliation. The source reference lists are managed within Financial; third-party imports must also use valid existing names to avoid manual reconciliation.
