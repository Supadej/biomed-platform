# Mobile native date/time input sizing

A shared stylesheet now constrains date, date/time, month, week and time inputs across Staff Portal, Biomed IS, Financial, service and administrative entry pages. It also applies to controls created dynamically after opening a form.

The fix explicitly includes padding in the field width, removes native intrinsic minimum sizing, constrains both physical and logical widths, and normalizes Safari's date-value wrapper. Date/time controls remain native inputs, with their original values, required/read-only/disabled states and picker behavior. Mobile text uses 16 px to avoid input-focus zoom, and controls use a consistent 44 px height.

Coverage includes search filters, form fields, dialogs and editable table cells. Labels/fieldsets containing temporal controls can shrink with their layout rather than forcing the control outside its column. No date parsing, timezone conversion, database migration or business logic was changed.

Validation used representative forms with the application styles at widths 320, 390, 430, 768 and 1280 px across Staff Portal, Biomed IS, Financial and service fixtures. All 20 cases passed containment, height, border-box and mobile font checks without page-level horizontal overflow. Additional checks passed for dialog fields, newly added date fields and retaining/editing native ISO values.

These browser checks ran in Chromium. The WebKit/Safari-specific rules have been included, but an actual iPhone Safari rendering check was not available in this environment.

Update the application files and reload the browser to load `temporal-inputs.css?v=49`. Preserve the existing deployed database. No database reset is required. The package has not been deployed automatically.
