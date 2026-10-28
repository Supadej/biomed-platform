# Update 33 — system-wide responsive containment

The Stock Check issue was caused by a table's intrinsic minimum width propagating through an unconstrained grid track. Controls and Submit then expanded beyond their card and enlarged the document on a narrow screen.

The shared responsive stylesheet now constrains workspace/grid children, forms, fieldsets, controls and table wrappers. Wide tables scroll locally. Count-entry rows become labelled cards on narrow screens. Selects, date inputs, textareas and Submit stay inside the Stock Check card. Autocomplete result lists stay in the form flow so they cannot cover Save/Cancel controls.

The review covered Staff Portal, Biomed IS, Budgeting and Instrument Service. It also found and fixed a Staff Portal filter toolbar insertion error on nested content. The public website navigation no longer widens the page behind the open portal, and wraps on narrow public pages.

Validation:

- 360 main page/viewport combinations across Biomed IS, Budgeting and Staff Portal at 320, 768 and 1440 pixels: no document-width overflow or browser errors.
- 45 Service Inventory tab/form/dialog checks at 320, 390, 768, 1024 and 1440 pixels, including populated stock-count lines and controls contained by their card.
- 15 Instrument Service editors and 15 Biomed IS transaction entry forms across phone, tablet and desktop widths.
- 15 Staff Portal editor checks across calendar, external helpdesk, sales plans, projects and minutes at phone, tablet and desktop widths.

No stock balances, count approvals, invoices or customer signatures were changed in the packaged database. Existing column preferences remain usable; wide tabular registers retain their local horizontal scroll. Install this complete package to obtain the updated HTML and stylesheet together. This package has not been deployed to the live Railway site.
