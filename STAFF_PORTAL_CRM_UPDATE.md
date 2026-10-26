# Native Staff Portal CRM update

## Where to find the features

- **Overview → Calender**: click anywhere in a date cell (or focus it and press Enter/Space) to open quick event creation on that date. Enter a title, review the prefilled 09:00–10:00 times and select Create event. More options opens the full event form. Existing event buttons open their own event. Month, week, day and table views; create and edit meetings/visits; drag to reschedule; start/end time and all-day setting; responsible employee, collaborators, contacts, products, location, conference link, plan, report and comments.
- **CRM → External Helpdesk**: customer tickets, service stages, table/board views, employee assignment, priorities and due dates, instrument/model/serial details, problems and solutions, parts/service items, billable quantities, customer feedback fields, notes, attachments and printable service report.
- **CRM → Project & Activity**: project register, project stages and activities; related-record navigation, budgets, expenses, responsibilities, outcomes, next steps and notes. Choose Activities in Register for its table/board and use Project filter.
- **CRM → Sales Plan**: manual leads, sales stages and board, collaborators, customer needs and decision makers, expected and achieved revenue, closing/payment dates, notes and source document links. Targets and supporting customer/contact/product registers are available in the Register selector.

These pages run directly in Staff Portal. They use its existing header, sidebar, login, language control and permission authority. There is no embedded CRM application, iframe or legacy CRM frontend bundle. Old CRM page addresses redirect to the appropriate native feature. The original CRM database records and compatibility API remain so upgrading does not discard data.

## Odoo-style record entry

External Helpdesk, Projects, Activities and Sales Plan now use a full-page record sheet inside Staff Portal. Choose **New**, enter the large record title and primary fields, then use notebook tabs for descriptions, other information and participants. The header and sidebar remain available.

- **Save** commits the current record; **Save & New** saves and opens a fresh entry. **Discard** or **Back to list** asks before dropping unsaved changes.
- Use the stage bar to select a service, sales or activity stage. Select **Save** to apply it.
- In **External Helpdesk → Parts & service**, choose **Add a line** to enter parts, catalogue/product, quantity and billable status. Add, edit and remove these rows before saving the ticket.
- In **Projects → Stages**, add named stages and their sequence as lines before saving the project. After saving, **Activities →** opens that project's activities. New activities default to its first stage; add a stage before creating an activity in a project context.
- Main record changes and changed item/stage lines are saved atomically. A validation, permission or stale-version error rolls back that form save. Discarding a draft does not create its record or lines. Saved related records opened separately and chatter notes/attachments retain their own save actions.
- Notes, attachments and change history appear below saved records. All original fields remain available in the relevant tabs or related-record forms.

This is an Odoo-style entry experience in the existing application; no Odoo installation or additional runtime dependency is required.

## Custom stages and interactive boards

- **Sales Plan** and **External Helpdesk** open in Board view. Each stage shows its count and totals across all matching records, with **Load more** inside a column after the first 30 cards.
- For **Project & Activity**, choose **Activity board**, select a project in Project filter and apply it. The Projects register and project record forms remain available. Stages belong to their project; the all-project board prefixes stage names with the project name.
- Use **Manage stages**, the stage header **⋯** menu, or **+ Add stage**. Add or rename stages, set colours/outcomes and move them up/down, then Save stage changes. Project stage management asks you to choose its project.
- Drag a card into another column to save the stage immediately. A touch screen can drag the **⠿** handle; **Move to** on every editable card also supports keyboard and touch navigation. Open the card title to edit its details.
- Removing an occupied stage asks for a replacement stage or **Unassigned**. Records are reassigned and the stage is removed atomically. Project activities retain their project when unassigned; replacement project stages must belong to the same project. Existing child records and notes are retained.
- Stage permissions remain separate from record editing. Reassigning all records while deleting an occupied stage requires record edit and view_all permissions. Immutable legacy bridge snapshots remain read-only and can prevent removal of a stage until their source mapping is updated.

## Sales Plan target summary

The cards above Sales Plan compare visible sales opportunities against **incentive schemes whose configured threshold is exactly 100%**. Schemes below 100% actual achievement still appear so you can plan the shortfall; the existing rule requiring actual achievement of at least 100% before linking a target is unchanged.

Cards show product / incentive line, representative, selected months, target, expected sales, approved-invoice actual, remaining target, opportunity count, attainment and plan coverage. They update after stage movement and filtering. Mark a sales stage **Lost** to exclude its opportunities from expected sales. Won stages remain included. Moving a card also keeps its won/lost, helpdesk status or activity completion state consistent with the selected stage.

For each opportunity, select the exact **Product / incentive line**, responsible employee and expected closing date. Matching uses those fields and the closing month. Biomed IS-bound leads use their source product line; older leads can also match when their linked CRM product name exactly equals the incentive line. Unmapped lines and missing closing dates are flagged rather than guessed.

Targets and invoiced actuals follow the selected calendar months and the existing Incentive schemes source calculation. Expected sales follow visible opportunities and the date/search filters. Currency totals remain separate; only THB opportunities contribute to THB target comparisons. The overall target/actual/expected totals count overlapping representative–product–month combinations once; individual cards retain each scheme's own period.

## Run on a Mac

1. Stop the previous server with **Control+C** in its Terminal window.
2. Extract this ZIP into a new folder.
3. To retain current records, copy your current **data/biomed.sqlite3** into the new folder's **data** directory before starting. Keep a backup of the previous folder. If BIOMED_DATABASE_PATH points to an existing persistent database, retain that setting and database instead.
4. Double-click **START_ON_MAC.command**, or open Terminal in the new folder and run `bash start.sh`.
5. Open **http://127.0.0.1:8765/?portal=1** and hard-refresh with **Command+Shift+R**.

The included database is the supplied test database, not a copy of your live server. All local verification uses a separate test database. Database tables are added automatically; existing records are not reset.

## Roles and permissions

The existing `crm_view` grant now means access to the native CRM features. Existing granular CRM grants are retained; there is no second account or role system. Administrators can assign these in Staff Portal → Roles & permissions:

- Calendar: `crm.events.view` plus create/edit/delete/assign as required.
- External Helpdesk: tickets; ticket_items for parts; ticket_stages for service stages.
- Project & Activity: projects, project_stages and activities.
- Sales Plan: leads and pipelines; targets for targets; contacts, organizations, departments, products and territories for supporting registers.
- Related records need their own view grants. Collaborator pickers need users.view. Notes need logs.view/create; attachments need files.view/upload. CSV export needs that register's export grant.
- Own/all record visibility and assignment permissions remain enforced on the server. A hidden button is not the security boundary.

System Admin already has these permissions in the supplied package. No new CRM rights are automatically granted to other roles. Existing quick-access preferences stay account-specific; add the native features through Customize.

## Generate leads from Biomed IS

Open **CRM → Sales Plan → Document binding**. An authorized administrator chooses quotation, customer-order, sales-order and/or invoice and enables automatic binding. Only approved documents generate a new lead. Match any old Biomed IS employee names to Staff Portal employees; shared user IDs map automatically. Unmatched owners are skipped and included in the synchronization result.

Saving the binding imports existing qualifying documents. **Sync now** reconciles existing documents again. Later saves in Biomed IS run synchronization in the same database transaction. Disabling the binding stops future synchronization and preserves existing leads.

- Source IDs and exact `sourceId` ancestry link quotation → customer order → sales order → invoice to one opportunity. No fuzzy customer/name matching is used. Separate source chains remain separate leads.
- Repeated saves do not duplicate a lead. Multiple invoices in a chain are summed as achieved revenue in their currency. Different currencies are skipped rather than combined.
- The initial expected revenue comes from the source amount; subsequent source details are available under Bound sales documents. Staff can continue editing the sales plan, notes and stage independently. Source snapshots and automatically calculated achieved invoice revenue refresh on synchronization.
- Cancellation/status changes and removed source documents update their snapshots and achieved invoice value. Deleting a lead does not cause its existing source documents to recreate it on the next sync.
- Documents require a source owner mapped to a Staff Portal employee. Missing owner mappings, conflicting previously linked chains, immutable legacy bridge snapshots and currency conflicts are skipped for review.
- Document amounts use the source financial net amount when supplied, otherwise quantity × unit price before discount/tax. This is a sales planning linkage, not a replacement for accounting or fulfillment.

Configuration/import requires CRM leads view/create/import/assign/view_all and Biomed IS access plus view rights to the selected document types. Automatic generation is disabled until that explicit configuration is saved. Biomed IS remains authoritative for its documents.

## Incentive-linked targets and the 100% rule

Open **Sales Plan → Incentive targets**. The scheme must have a positive sales target and actual achievement of **at least 100%**. A scheme with an 80% incentive threshold still cannot link at 80% achievement. Zero targets cannot link.

Eligibility uses Staff Portal's approved-invoice/THB basis (including approved linked credit deductions), or its existing integration sales-actuals projection when configured. The server recalculates eligibility at the time of linking and refreshing. A user cannot bypass the rule with a forged browser request. Reporting scope and Incentives/Sales permissions still apply.

A linked target records scheme ID, representative, line, period, target, actual, attainment and link time. Refresh updates the existing target rather than creating another. It is a snapshot: later performance changes do not silently rewrite it; refresh rechecks 100%. Linked targets are read-only in the generic target editor.

## Verification and practical limits

- Python regression suite: 66 tests passed, including ten native-feature tests and seven workflow-board tests covering CRUD/paging, stale edits, own scope and parent access, projects/ticket items, exact document lineage/deduplication, invalid input, the 100% gate, atomic multi-line saves, rollback, child permissions, child-parent isolation, stage management, full-board counts, stage reassignment, exact incentive matching, overlap deduplication and project identity retention.
- DOM interaction checks used the real local API to verify calendar-cell click and keyboard creation, date prefill, quick save and existing-event opening; Helpdesk inline rows/save/delete/discard; project stage creation and activity context; and Sales Plan stage selection/Save & New. Workflow checks additionally verify stage add/rename/reorder, target-card refresh, native drag/drop, touch-handle movement, move selectors, safe occupied-stage removal, helpdesk workflow and project-specific activity completion. These checks do not substitute for browser layout verification.
- The native UI uses flat paginated responses instead of recursive entity expansion. Lists show 30 records/page; workflow boards load the first 30 cards per stage, with Load more for that stage and totals covering all matching records. Calendar ranges load up to 1,000 visible events/page. Related sections show the first 100 records. Searchable relation pickers return up to 100 matches and retain selected values; narrow the search for other matches.
- Automatic links use the existing SQLite runtime in this package. No new server hosting or SQL Server runtime is introduced.
- Browser installation was unavailable in this environment, so native browser rendering, touch drag gestures and printing still need a check on your Mac. Start with the supplied test data before updating a live server.
