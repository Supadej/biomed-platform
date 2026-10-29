# Compact page summaries

Biomed IS register summaries now use a compact label/value strip instead of inheriting dashboard card height. The strip sits below the page heading, wraps on narrow screens, and preserves the current filtered counts and document amounts.

Removed the redundant Function and Tables shown counters. Pages without a record table no longer show an empty technical summary. Dashboard and create forms do not add another generic summary above their own content.

Dashboard metric cards in Biomed IS, Financial and Staff Portal have reduced padding and height. Staff Portal statistical cards and CRM analysis KPI cards use compact spacing as well. Calendar colors, landing pages, centered month columns, number entry and all records remain unchanged.

Validation covers document registers, approvals, inventory and customer masters at six screen widths; summary height and viewport containment; unchanged filtered values when navigating away and back; and smaller dashboard cards in the three primary applications. No backend schema change, migration or reset is required. Deploy the full package to update the site.

## Consistent Favorites

Favorites is now one fixed 128 × 44 px control across filter bars. Opening it leaves the trigger and filter row unchanged. Saved searches open in a separate, compact panel below the filter group, with explicit Close and Escape-key support. Only one Favorites panel is open at a time; removed filter groups clean up their panels. Existing per-user saved searches and filter restoration are retained.

## Staff Portal menu scrolling

On desktop, the Staff Portal sidebar is constrained to the available viewport below the header and scrolls independently of the workspace. Tablet/phone drawers retain their own scrolling. The sidebar has a visible scrollbar and prevents scrolling from spilling into the main workspace.

Validation additionally covers Favorites trigger dimensions and filter-bar stability while opening/closing across the primary applications at six widths, saved-search save/apply behavior, panel cleanup and independent desktop/mobile menu scrolling.
