# CRM original-function preservation — Staff Portal integration

Source: Biomed_CRM_Integrated.zip (original, not simplified previous build).

The Staff Portal navigates to **original CRM pages** in same-origin iframe containers, rather than replacing their interfaces or business logic:
- Overview > Calendar => `/crm/event.html`
- CRM > Sales Plan => `/crm/crm.html`
- CRM > Project & Activity => `/crm/project.html`
- CRM > External Helpdesk => `/crm/helpdesk.html`

The existing CRM backend, APIs, SQL schema, forms, filters, page scripts, and records remain unchanged. Backend CRM session permissions still apply. The standalone CRM link in Staff Portal top navigation is hidden; the original CRM files are deliberately retained to support these functions.

**Not implemented by this preservation change:** automatic generation of leads from quotations/orders/invoices and the requirement for 100% incentive target attainment. Those features require a source-data contract and a separate scoped implementation and validation. An iframe preserves the original CRM behavior but does not inherently eliminate the original CRM performance bottlenecks.

When testing: sign in through Staff Portal, use each menu, and verify CRM-level authorization, record persistence, navigation, and responsive layout.
