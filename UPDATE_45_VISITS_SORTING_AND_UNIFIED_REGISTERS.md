# Customer visits, commercial registers and table presentation

## Customer visits

The visit form groups schedule and people, customer and product details, and discussion and follow-up. It adds visit date and time, duration from 1 to 24 hours, multiple collaboration people, multiple customer types, customer status, multiple product lines, and an optional internal calendar entry.

Filters support multiple representatives, product lines, customer types and customer statuses, together with search and a date range. Saved favorites preserve these multiple selections. The Columns control exposes visit, customer, schedule, follow-up and record metadata fields.

Calendar entries use the customer/institution and selected product lines as their title. Their duration follows the visit. Saving changes updates the existing linked entry; disabling the option or deleting the visit removes that internal entry. The new `portal.visits.calendar` permission controls this operation alongside the existing visit write and scope permissions. Existing visit writer roles receive this permission through the versioned migration. Administrators can adjust it in Roles & responsibilities. This action does not send Outlook invitations or write to an external mailbox.

Historical visits retain their existing dates and values. A time must be entered when editing a historical visit before it can be linked to the calendar. Previously stored product labels remain available when editing older visits.

The Analysis view follows the active filters. It shows visit volume, hours, institutions, completion and overdue follow-up; charts break down representatives, months, product coverage, customer types, customer statuses and follow-up. The review panel highlights overdue work, missing next actions and incomplete historical data. Visits tagged with several products or customer types count in each selected category; category counts therefore need not total the number of visits.

## Quotations & tenders and Sales pipeline

Manual and linked quotation records now appear in one register, with a Manual/Linked source column and source filter. Manual editing and removal remain available; linked records retain follow-up and applicable order generation. Additional selectable columns include customer, representative, product, values, dates, stages, follow-up and source metadata.

## Tables and details

Table headers support pointer and keyboard sorting, with numeric, currency, date and text comparisons. Record tables with dates start with the most recent records. Planning matrices keep their period order. Expanded details remain attached to their record when sorting. Native CRM sorting occurs before pagination; other rendered tables sort their currently displayed rows.

Columns supports searching available fields, selecting all and deselecting optional columns. Existing per-account heading, ordering and visibility preferences remain supported. Additional safe fields are exposed where available; private credentials are excluded.

Details use compact, content-height fields instead of stretched cards and a duplicate raw metadata column. Overview statistics no longer look like text inputs. Visit forms, analysis and combined registers adapt to narrow screens.

HR profile is the first Human Resources item. Minutes & Acknowledgement follows Training & Competency.

## Installation and validation

Replace the application files and restart using the existing deployment procedure. Back up the deployed database first and preserve it when updating an existing installation. Startup applies the permission migration without resetting business records. This package has not been deployed automatically.

Validation completed against a separate test database:

- 288 Python regression tests passed, including visit calendar lifecycle, validation, permissions and native CRM sorting before pagination.
- Browser checks passed for visit creation, multiple selections, calendar linking, editing and reloading, analysis, saved filters and both Manual/Linked source filters.
- 42 responsive page checks passed at widths 320, 390, 768, 1024, 1440 and 2048, including compact expanded details, expanded column selection and HR order.
- Sorting checks passed for dates, numbers, blanks, keyboard activation, attached detail rows and dynamically added optional columns.

No QA visit records or QA sessions are included in the supplied application database.
