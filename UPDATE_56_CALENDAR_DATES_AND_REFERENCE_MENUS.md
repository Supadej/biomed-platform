# Calendar dates and reference menus

- Service Job and Application Job Calendar date is selectable and defaults to today in Thailand. Editing preserves a previously saved Calendar date.
- Changing job or scheduled dates no longer replaces the chosen Calendar date. Linked events use that chosen date; backend validates it.
- Instrument, Biomed IS customer and External Helpdesk search menus float below their controls, with bounded scrolling, instead of expanding form rows. Keyboard selection, Escape and focus exit close menus appropriately.
- Existing database and permissions are preserved. No deployment performed.

Validation: backend regression suite, Application Service DOM checks, shared lookup and Service Job calendar DOM checks, JavaScript syntax checks. Fresh browser visual QA unavailable due to the previously reported automatic approval usage-limit block.
