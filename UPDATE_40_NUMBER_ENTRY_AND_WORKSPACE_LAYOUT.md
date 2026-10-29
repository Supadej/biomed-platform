# Number entry and workspace layout

## Changes

- Financial target-setting and Express import forms use the same 14px control text, regular font weight, control height and label spacing as the other Financial functions. Mobile field text uses 16px consistently for readable touch entry.
- Target/source and Express filters use responsive grids. Submit actions have their own spaced row instead of sitting at a different height beside fields.
- Annual/monthly target inputs have sufficient width for grouped amounts and decimals. Wide target tables retain their contained horizontal scroll area.
- Financial ledger Detail and Reverse actions use a wrapping action group with a visible gap.
- Number fields in Staff Portal, Biomed IS, Instrument Service and Financial automatically show thousands separators while editing, e.g. `1,234,567.89`. Decimal places and negative values are preserved where the field permits them. Identifiers and ordinary text fields are unchanged.
- Scripts, calculations and form submissions receive canonical values without commas; the formatted text is presentation only. Minimum, maximum, required and step validation remain active. Existing data and database schemas are unchanged.
- Database administration is a regular **Administration → Database administration** sidebar function in Staff Portal, Biomed IS, Instrument Service and Financial. The ad hoc header link and full-width footer bar are removed.
- The Database page now follows the shared application header, logo, system links, signed-in identity, sign-out control, desktop sidebar, mobile drawer, colors and form styles. Its function links navigate to Backup, Import/restore, Archive/reset and Administrator testing; the mobile drawer closes after choosing a function.

## Operation

Deploy the complete package to update the website. Start locally with the existing launcher if testing on Mac. No database reset, restore or production operation is needed to apply this interface update. Retain the production database rather than replacing it with the included fictional test database.

Database permissions, full-system backup/restore, protected archive/reset, and audited System Admin testing from release 39 are retained. See `UPDATE_39_DATABASE_ROLES_AND_LAYOUT.md` for those workflows.

## Validation

Python backend regression suite: 284 tests passed. Browser numeric-entry tests cover grouped display, raw values, FormData, decimals, negatives, cursor edits, programmatic updates, form resets, and required/minimum/step validation. Financial table-alignment regression passed. The specific reported screens were checked at 320, 390, 768, 1024, 1440 and 2048 pixels for layout, control typography, annual-value clipping and action-button separation. Main application navigation and viewport containment were also checked after adding the shared numeric editor.

No real Express import, Microsoft mailbox change, live reset or deployment was performed. The initial real Express report still needs the accountant's mapping validation.

## Developer note

`number-inputs.js` enhances number inputs into grouped text editors. The application's main-world `value`/`valueAsNumber` properties expose canonical numeric values; the native displayed value is formatted. A capture-phase FormData handler normalizes outgoing fields. Code inspecting numeric inputs by type should also recognize `[data-number-input]`, as the updated Financial table-alignment helper does. Automated browser `inputValue()` may return the displayed text from an isolated world; inspect the application's value via `page.evaluate` when verifying canonical values.
