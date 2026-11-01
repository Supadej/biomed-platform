# Layout and button consistency — update 75

## Changes
Shared rules now cover all 14 application/public entry pages: Website/Staff Portal, Biomed IS, Financial, Instrument Service, Website Catalogue, Catalogue Administration, AI Chat Management, Copilot Access, Database Administration, Integration Settings, User Manual, News, Events and Careers. Application Service, CRM and other Staff Portal modules inherit the portal fixes.

- Consistent 44px minimum action height, padding, corner radius, typography, focus outline and disabled state. Longer labels can increase button height.
- Primary actions share a blue palette; secondary actions use pale blue; destructive buttons retain their warning treatment. Navigation, tabs, chips and semantic status styling retain their own context.
- Action groups wrap with gaps instead of forcing every action into one row.
- Fixed-height filter buttons no longer clip wrapped text.
- Checkbox/radio labels remain horizontal and checkbox dimensions remain independent of full-width text controls.
- Narrow-screen form/filter tracks collapse without imposing desktop minimum widths. Mobile form text uses 16px to avoid automatic input zoom.
- Dialog width and height remain within the viewport with vertical scrolling.
- Expanded details can wrap long content; wide tables retain their own scrolling containers.
- Controls/content with the hidden attribute cannot be revealed by generic button or action display rules.
- The earlier shared presentation rules no longer force long action labels to remain on one line.

## Validation and limits
Source audit: all 14 entry pages load the shared stylesheet. Inline JavaScript in all 19 HTML files and all 58 standalone JavaScript files passed syntax checks. Budget/Finance regression checks passed. Startup on a temporary copy of the supplied database left all 83 existing tables unchanged. The packaged SQLite snapshot remains byte-identical to the upload.

This is a source-level layout audit and correction. A working browser renderer was unavailable in the development environment, so full visual verification at desktop, tablet and phone sizes has NOT been completed. This update does not certify every dynamically generated state, every translation, every device or every button's business action. Database and application logic have not been altered for this layout update.

## Deployment
Follow UPDATE_74_ANNUAL_MONTHLY_BUDGET.md. Deploy into the same Railway service with the existing volume and database path. Do not replace the live database with the packaged snapshot. The existing preservation and backup safeguards remain enabled.

## Visual acceptance checks after deployment
Use desktop, tablet and phone widths (for example 1440, 1024, 768, 390 and 320px), including Safari on iPhone:
1. Open the main modules, switch EN/TH and open/close the navigation menu.
2. Open filters, named favourites, column chooser and multiselect controls.
3. Expand quotation, pipeline, borrowing and service-job details; open edit forms and report/email dialogs.
4. Check Roles & Permissions, reporting hierarchy, brands and product/customer/warehouse forms.
5. Check annual/monthly approval tables and decision buttons with a permitted account.
6. Confirm long labels wrap; buttons remain separated; focused controls remain visible; tables scroll inside their containers; dialog close/save actions remain reachable.
