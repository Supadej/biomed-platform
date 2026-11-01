# Staff Portal calendar update

The event heading now shows its start and end date/time. The responsible employee badge uses the employee's name and changes when a different employee is selected.

Collaborators and other native multi-select fields throughout the portal use searchable checkbox selections with removable selected items. Ctrl / Command is no longer needed. Existing native form values, permissions and asynchronous lookups are retained.

Calendar fields:
- Main contact: searchable selection from the existing Biomed IS customer master.
- Product / brands: multiple selections from Staff Portal Brands. Maintain the available list under Brands.
- Additional contacts: free text for names, phone numbers, email addresses and other details.
- Additional products / brands: free text; separate brands with commas.
- Customer department / location: free text.
- Files: choose multiple attachments while creating or editing an event. Maximum 10 files, 10 MB per file, 20 MB total. Adding files requires the existing CRM file-upload permission; viewing and downloading requires access to that specific event. Files are stored in the existing database and are not publicly accessible. Removal is saved with the event, and existing historical log attachments remain accessible under Notes and historical files when permitted.

The Activity log shows recorded event creation and edits, actor name, and Bangkok date/time. Historical events with no prior audit trail cannot show timestamps that were never recorded. The decorative Pickup control has been removed.

Minutes-linked calendar events can be edited by staff with Calendar editing and event visibility permissions. They remain linked to the original minutes. Calendar edits do not alter issued minutes content or acknowledgement records. New minutes revisions preserve independent calendar edits unless a corresponding meeting scheduling field changes in the minutes revision. Deleting a minutes-linked event directly is blocked; turn off calendar linking by publishing a minutes revision instead.

Historical CRM contact/product/location identifiers are preserved in storage; new calendar fields use the requested sources. Outlook synchronization is not included in this update.
