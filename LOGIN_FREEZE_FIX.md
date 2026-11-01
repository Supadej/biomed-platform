# Login page freeze correction

The main page language watcher rewrote its language buttons unconditionally.
Those writes produced new child-list mutations, scheduling another translation
pass across the page. This continued even when website and internal AI were off.

The translation watcher now disconnects while updating labels and reconnects
afterward. Button labels are only changed when their value differs.

AI defaults and the existing one-time disable migration are retained.
Accounts, passwords, and business database files are unchanged.

Validation:
- New regression fails against the previous ZIP and passes with this correction.
- Dynamic English/Thai text and language switching pass.
- AI visibility regression and six backend separation tests pass.
- Main-page inline JavaScript syntax and archive integrity pass.
- Live Railway login and browser responsiveness remain unverified.

Deploy the source files while retaining the current production database and
persistent volume. Hard refresh with Cmd+Shift+R after deployment.
