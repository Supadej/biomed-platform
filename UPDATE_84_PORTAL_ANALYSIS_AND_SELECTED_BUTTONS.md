# v84 — Staff Portal selected buttons and Analysis switching

Selected view buttons now use a persistent teal background with white text. This covers Records/Analysis tabs, Table/Board controls, calendar views and existing selected tab buttons. Inactive controls use a white background and dark text. The selected state uses aria-selected/aria-pressed and remains distinct from hover.

Sales Performance, Demos, Quotations & Tender and Sales Pipeline use an explicit analysis view controller. Clicking Analysis opens its panel, hides record content, retains the filters, and scrolls to the analysis. Clicking Records restores record content. Rendering failures appear as an error in the panel. Current view permissions and authorized, filtered payloads remain in use.

CRM Analysis now loads directly without a redundant records request or an unrelated sales-summary request that could fail before analysis was reached. Selecting Table, Board or another calendar layout exits Analysis mode. View selection is synchronized as loading begins.

## Updating

Upload the project contents to GitHub and retain the current Railway volume and database path. No additional database reset was introduced in v84. **The previously requested one-time v83 Finance reset is still included: if it has not run on your database, it will back up the database and clear Finance once at first startup.** If it already ran, the existing marker preserves subsequently entered Finance data.

## Verification

Six Python tests pass. JavaScript interaction tests cover record/analysis click switching, selected attributes, record visibility, real analysis rendering for Sales Performance/Demos/Quotations/Pipeline, error display and direct CRM analysis loading with selected filters. All inline and external JavaScript syntax checks pass. These interaction tests use a simulated DOM; browser-rendered visual verification remains unavailable. This project has not been deployed by the developer.
