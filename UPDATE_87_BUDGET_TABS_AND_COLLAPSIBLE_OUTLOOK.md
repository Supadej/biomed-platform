# v87 — Budget navigation and collapsible earnings outlook

Company earnings outlook now appears as a collapsed disclosure under Annual Budget and Budget vs Actual. Select its heading to show or hide it. Expanding it retains the live calculations; editing budget amounts does not close it.

Navigation is arranged in these rows:

1. Annual Budget → Actual Expense Recording → Budget vs Actual
2. Annual Budget Approval → Monthly Budget Approval → Performance Finalization
3. Source References

The selected tab uses teal with white text, with aria-pressed and aria-current state. Inactive buttons use white with dark text. Each row stacks on narrow phone screens in the same order.

Tests cover row order, selected state, tab visibility, default collapse, preservation of expanded state while updating totals, and continued Manage Expense Items behavior. Eight Python tests pass; inline and external JavaScript syntax checks pass. Browser-rendered visual verification is unavailable. This package has not been deployed.

Keep the existing Railway volume and database path. No database reset was added or changed in v87. The previously requested one-time v83 Finance reset remains included if it has not already run. Its marker preserves new Finance entries after that reset has completed.
