# Presentation and column width update

## Shared presentation

Shared rules now apply across Staff Portal, Biomed IS, Financial, instrument service and administrative pages. This replaces the main causes of cramped headings, fragmented labels and uneven filters:

- Consistent 44 px filter controls, readable text sizes and aligned labels.
- Compact multiple-selection triggers with searchable, bounded dropdowns; opening choices no longer stretches the filter row. Escape and outside click close the dropdown.
- A separate row for filter actions and Favorites.
- Default column widths chosen for source, descriptions, names, dates, values, statuses and actions. Wide tables scroll inside their panel rather than squeezing words into unreadable fragments.
- Sort indicators and resize handles occupy separate positions in headings.
- Dates with time are displayed in readable Thailand time; original values remain available for sorting and on hover.
- Numeric values align right; monthly and annual target headings and inputs remain centered.
- Compact Details fields and constrained detail/edit content within wide tables.

Public website presentation and document report templates retain their own styling.

## Adjusting widths

Every application table handled by the shared Columns system now supports column resizing. Existing instrument-service column selectors receive a separate **Column widths** editor so their own visibility controls are retained.

1. Drag the right edge of a column heading using a mouse or touch.
2. Alternatively open **Columns**, enter **Width (px)** and choose **Save columns**.
3. Resize handles support Left/Right arrow keys in 10 px increments; Shift changes the step to 40 px.
4. Double-click a handle or press Home on it to restore that column's default.
5. **Reset widths** restores widths while retaining headings, visibility and order. **Restore defaults** restores the entire shared table layout.

Widths are saved to the signed-in account, separately for each table. They follow their original columns when reordered or hidden. Limits are 80–1200 px. Narrow custom widths may require wrapping or show an ellipsis; full text remains in the cell and on hover. Tables may expand to fill their available panel when the combined widths are smaller than the panel.

Previously saved visibility and heading preferences remain valid. Shared commercial/visit table identifiers now ignore changes in the matching-record count, so future searches retain the same layout. Preferences saved under earlier count-dependent identifiers may need to be selected once again.

Printed business reports are not interactive workspace tables; their report layout remains controlled by their existing report templates.

## Validation and limits

- 289 Python regression tests passed, including width validation, per-account isolation and reset behavior.
- DOM checks passed for widths, pointer/keyboard resizing, persistence, reordering, hidden columns, reset, native service selectors, merged headers and retained form/button handlers.
- Presentation checks passed for filter action grouping, multiple selection, public-page isolation, readable dates and target alignment.
- Browser checks used representative fixtures with fictional records and the application's existing styles and shared scripts: visits, commercial register, leave and target entry at 1280, 768, 390 and 320 px. All 16 cases kept controls at 44 px and prevented page-level horizontal overflow. Dropdown containment, width entry, keyboard resizing and reset were also checked.
- These browser checks cover representative layouts; they are not a visual verification of every authenticated page or every user-selected column combination.

## Installation

Use the existing update procedure: back up the deployed database, replace application files and restart. Preserve the existing deployed database. No database reset or new permissions are required. Asset versions were updated so the browser loads the revised shared files.

The supplied application database has not been populated with QA records. Preview fixtures and test sessions are excluded from the delivery. This ZIP has not been deployed automatically.
