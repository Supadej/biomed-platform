# Consistent centered month columns

Month headers, monthly values, editable number fields and monthly totals are now centered consistently. This applies to target setting, source actuals, cost and expense schedules, summaries and other table-based screens across the applications, including embedded pages.

The shared rule recognizes month names and year labels, generic Month columns, Thai month names, and grouped monthly headings. It recalculates after tables are rendered, columns are reordered, and labels are translated. Other source/name columns and annual totals retain their existing alignment. Number formatting and saved values are unchanged.

The regression checks cover multi-level headings, merged cells, monthly inputs, values and totals, Thai labels and reordered columns. Financial browser checks cover seven table views at six screen widths.

Deploy the full updated package. No database migration or reset is required.
