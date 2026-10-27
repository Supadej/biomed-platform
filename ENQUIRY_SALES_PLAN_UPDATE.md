# Received Enquiries / Sales Plan integration

- Received Enquiries is shown at the top of Product Catalogue Management, loaded automatically, with Refresh Enquiries button.
- Website submissions write both an enquiry and an unassigned CRM Leads record in one SQLite transaction. An unsuccessful lead creation prevents the enquiry from being accepted.
- Unassigned means `MainUserId = NULL` and `CRMPipelineId = NULL`. Staff can subsequently assign a person or stage in Sales Plan.
- Lead includes the visitor contact, company, message, and selected product names/SKUs in AdditionalInfo; expected revenue starts at zero until qualified.
- `web_enquiries.crm_lead_id` and `crm_links` record a one-to-one source link; existing enquiries remain unchanged and are not automatically backfilled.
- Preserve the production database and Railway volume when deploying. Test with a fresh enquiry and review the Unassigned Sales Plan column.
