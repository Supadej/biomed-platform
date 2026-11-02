# v88 — Outlook calendar visibility and mobile presentation

Phone calendars (680 px and below) use a vertical agenda with full-width event cards and horizontal, readable titles. Empty dates are hidden except today; New event and date navigation remain available. Larger screens retain the calendar grid. Calendar event cards explicitly use block layout instead of inheriting inline-flex action-button styling, which was squeezing time/title/owner into narrow vertical strips.

The calendar shows the total cached Outlook events and how many overlap the displayed date range. Restrictive filters are flagged; Clear calendar filters clears date/search/employee filters. The Outlook connection dialog displays the cached count and earliest/latest dates. This distinguishes incomplete import from events hidden by filters or calendar positioning.

Private Outlook import now allows up to 100 result pages / 10,000 events instead of 10 pages. The previous complete cache is retained if fetching fails. The import still covers approximately 180 days before today through 365 days after today and reads the connected user's primary Outlook calendar, including recurring occurrences returned by Microsoft's calendarView API. Secondary/shared calendars are not imported by this connector. The screenshot alone does not establish whether only one date was imported or other dates were hidden by layout/filters.

## After updating

1. Keep the mounted database, Railway variables and Outlook encryption key unchanged.
2. Open Staff Portal → Calendar → Outlook calendar.
3. Keep Show my other Outlook events privately enabled; select Save sync settings if changed.
4. Select Sync now / retry and check the cached count/date range and any error.
5. Close the dialog and select Clear calendar filters. Navigate to the required month.
6. If only one date remains in the cached range, verify that the other appointments are in the connected account's primary Outlook calendar. Share the connection status/count screenshot for further diagnosis; no credentials are needed.

No additional reset was introduced. The previously requested one-time v83 Finance reset remains included if it has not already run; its marker prevents repeated clearing. This update does not reset Outlook connections or change staff permissions.

## Verification

Nine Python tests pass, including a twelve-page Outlook import spanning twelve dates and preserving the previous cache on failed refresh. Calendar rendering tests cover different dates, restrictive filters and the event-card markup; the existing budget/navigation and Staff Portal Analysis tests also pass. Inline and external JavaScript syntax checks pass. Tests use a simulated DOM; rendered mobile/Safari verification is unavailable. This package has not been deployed by the developer.
