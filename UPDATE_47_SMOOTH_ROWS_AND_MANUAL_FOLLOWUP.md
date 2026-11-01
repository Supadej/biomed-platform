# Smooth row information and manual commercial follow-up

## In-place expansion

Record information previously caused a complete page render in several registers. Some paths also forced horizontal and vertical scrolling. These behaviors made the toggle jump and triggered table/layout rebuilding.

Row details now expand and collapse in place with a short 180 ms height/opacity transition. Row nodes, filters, sorting and saved column widths are retained. Rapid clicks cancel and reverse the active transition, and closed information is cached until the surrounding data is refreshed. Closing information from within its panel returns focus to the originating button. The operating system's reduced-motion setting skips animation.

The update covers Staff Portal details and inline editing, manual and linked commercial follow-up drawers, Biomed IS transaction details, borrowing report breakdowns, instrument service records, service inventory/job breakdowns, and native information summaries. Navigation menus, multiple-select filters, Favorites and Columns keep their own controls.

Expanded content stays within the visible horizontal table viewport without resetting the horizontal scroll position. Details/Hide and Edit/Close edit controls reserve room for both labels to avoid changing the action row height when toggled. Navigation, data changes and saved edits still render the appropriate refreshed view.

## Manual quotations/tenders and sales pipeline

Manual records now expose **Manage follow-up**, as linked records do. Both use a separate, consistent row panel instead of cramming a management form into the Actions cell.

Manual follow-up supports:

- Outcome or stage.
- Won/lost justification; a reason is required for either outcome.
- Follow-up action/date.
- Updated employee/time and a history entry.
- Including a manual tender in Sales Pipeline, with pipeline-edit permission. The pipeline displays the source tender rather than creating a duplicate business record. Users must retain source-tender visibility to see it there.

Editing a tender-derived pipeline row uses the source tender's permissions. Follow-up changes require the existing module edit permission and the existing owner/team scope. Changing the pipeline inclusion flag additionally requires pipeline edit permission. These checks also run on the server. Manual records do not generate a Biomed IS sales order; the existing order-generation flow remains available for eligible linked quotations.

The normal Edit forms retain follow-up data and align their stage/status with the latest follow-up. Manual Won/Lost reasons and follow-up notes are visible in record details and available as optional register columns.

## Validation

All 291 Python regression tests passed, including new manual follow-up authorization/validation checks. DOM checks cover interrupted animations, reduced motion, native summaries, focus/input/scroll retention, cached detail/edit rows, switching records without page redraws, manual follow-up forms and source-tender pipeline inclusion. Existing column and alignment checks also passed.

Browser checks used fictional layout fixtures to verify row expansion, repeated toggling, final collapse, and content containment while horizontally scrolled. They do not constitute a visual audit of every authenticated workflow.

## Installation

Preserve the existing database, replace application files and restart using the normal update procedure. No database reset or new role permission is required. Updated asset versions refresh the shared scripts. Preview fixtures and QA records are excluded. The package has not been deployed automatically.
