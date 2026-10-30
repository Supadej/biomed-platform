# Application jobs, reference choices and optional reports

Application Service now uses a laboratory flask icon and a Service Job-style form. The main job field is a read-only, server-generated number in the format BMDASDD-MM-YY/# (for example BMDAS29-10-26/1). The date is the creation date in Thailand; the daily sequence is reserved transactionally and is not reused after removal. Topic is a separate optional field. Existing Application Service records receive the new number once on startup; their previous reference remains available in Columns and CSV exports, while existing links keep the same record ID.

Customer / institution is a dropdown backed by a managed Application Service customer reference list. Initial choices come from existing Biomed IS customer names and existing application jobs. Authorized users can use Customer reference list → Add customer / Remove. Removing a choice makes it inactive for new jobs and preserves existing job records; it does not remove the Biomed IS customer master.

Product supports multiple selections using the same shared product/brand options and searchable checkbox control as Customer Visits. Instruments use the searchable reference control from Instrument Service, matching serial, brand, model and location.

Specialist choices are restricted to active accounts with the Eligible application specialist responsibility (application_service.perform), plus System Admin. Existing assignments to people who later become ineligible remain readable as historical assignments. Application Specialist and Application Service Manager role presets are updated automatically. Custom roles can receive the new responsibilities under Roles & Permissions → Application Service.

| Responsibility | Purpose |
|---|---|
| Eligible application specialist | Makes active users in this role selectable as application specialists. |
| Manage application customer references | Allows adding/removing choices in the Application Service customer dropdown. |
| Link application jobs to Calendar | Enables calendar linking together with the relevant Calendar View/Create/Edit permissions. Assigning an event to another person also requires Calendar Assign. |

Application Service Manager receives customer-reference management and Calendar Assign. Both standard application roles receive specialist eligibility and the calendar permissions needed for their own jobs. Existing custom role grants are preserved.

The optional Application report information & customer feedback section includes area/department, instrument warranty/ownership, issue resolved, speed, preparedness, courtesy, satisfaction and comments. Customer name, touch/mouse signature and acknowledgement are optional. A saved signature is bound to the report fields; changing signed report content requires clearing the signature or obtaining a fresh signature. Expanded job details show the report and any customer acknowledgement.

The calendar option creates one linked all-day event for the assigned application specialist, using Customer / institution as its title and the job's start date as its date. Updating the job updates the same event; disabling the option or removing the job unlinks that event. Server permissions are enforced, and the existing Helpdesk referral functions remain available.

Customer Visits Records / Analysis controls now use the actual shared tab container with an explicit 18 px gap before the following card. Earlier spacing rules targeted the shared tab container while this particular page still used a generic action row.

## Update and validation
Retain the deployed database when replacing the project files. New reference tables, responsibilities and existing-job numbering migrate on startup. No database reset is required.

302 Python regression tests passed, and the final focused Application Service suite passed all 13 tests. Coverage includes customer choices, product validation, role eligibility, assignment permissions, version locking, unique numbering, existing-job migration, Helpdesk link preservation and rollback, calendar create/update/unlink/removal and permission boundaries, optional signatures and signed-report changes. DOM tests passed for Application Service form controls, product selection, instrument search, calendar date synchronization, optional signature capture/clear, permission migration, saved searches and the actual Customer Visits tab renderer. Inline script syntax checks passed.

Fresh browser preview was blocked by automatic approval review because of a browser usage limit. No new visual or physical iPhone validation is claimed for this update. The prepared preview fixtures are excluded from the delivered project. The project is not deployed automatically.
