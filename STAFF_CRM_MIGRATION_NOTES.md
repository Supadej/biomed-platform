# CRM to Staff Portal restructuring

Four separately navigable, full-width pages are added in `/staff-crm/` and linked from Staff Portal: Calendar, Sales Plan, Project & Activity, External Helpdesk. They are **not iframes** and retain original CRM feature markup, scripts, backend endpoints and data. Existing project, ticket, and lead detail links still resolve to original CRM detail URLs until those detail pages are migrated. The standalone CRM is no longer listed in the Staff Portal global header.

**Incomplete:** This is a page-shell extraction, not a complete component rewrite inside the Staff Portal SPA. The CRM backend and shared scripts remain dependencies, and original `/api/crm/session` permissions are still enforced. There is no background lead auto-generation or new 100%-attainment incentive linkage in this build. Full E2E testing on Railway and permissions/access auditing are required before deployment.
