# Navigation, landing pages and presentation

Financial's menu groups now start with Dashboard, followed by Budget Setting & Approvals. Quick-access shortcuts remain above the grouped navigation. The duplicated approval link in Monitoring & Control is removed.

Default system entry points:

| System | Default page |
| --- | --- |
| Biomed IS | Dashboard |
| Staff Portal | Overview |
| Financial | Executive dashboard |

Explicit links to a function, task or record are preserved. Existing role permissions still govern access; a user without access to a page receives the existing permitted fallback.

Removed development banners and outdated prototype/storage/template-source notes from normal operational screens. Backup/reset confirmations, permission errors, validation notices, financial reconciliation guidance and explicit administrator-testing indicators remain available.

Dashboard metric cards use consistent spacing, padding and height. Shared filter labels, controls and action rows use consistent gaps and alignment across the primary applications. The prior centered month columns and grouped numeric editing are retained.

Validation includes default landing pages and Financial menu order at six widths; deep links to inventory, tasks and approvals; dashboard card alignment; main application navigation and viewport containment. Database contents and backend workflows are unchanged. Deploy the full package to update the live site; no database reset is required.

## Calendar employee colors

Each responsible employee has a stable, distinct calendar color based on their user ID. Month, week and day cards use the employee's accent and light background, with their name beneath the event title. A wrapping color legend identifies employees in the visible results. Table view includes the same colored employee badge, and the event editor uses the same responsible-user color.

Filtering, switching views, renaming employees and reloading do not reassign colors. Unassigned events and private Outlook items have separate neutral styles. Color accompanies names rather than replacing them. Event access, collaborators, Outlook synchronization and saved records are unchanged; this is a presentation update.

Validation includes 15 calendar view/viewport checks, distinct visible user colors, name labels and legend, reload stability, table badges, and deterministic unique colors for 1,000 numeric user IDs. Different employees may have similar hues in very large teams, so names remain visible.
