# Filter and section spacing

Removed the shared filter-grid rule that zeroed vertical padding on filter cards. Card filters now use 20 px padding on desktop and 16 px on small screens, with border-box sizing so padding cannot increase a 100%-wide panel beyond its parent.

Added shrink constraints to field containers, responsive wrapping to action rows, and consistent 14 px separation after card heading rows. Employee Onboarding, Employee Offboarding and Promotion / Internal Role Change controls now have room below their section heading and wrap safely.

Shared changes apply to Staff Portal, Biomed IS, Financial, Instrument Service and the admin entry templates. Native date picker fixes, calendar defaults, Analysis labels and Columns settings remain included. No database or permissions changes.

Validation: 54 Chromium fixture cases (nine entry-point stylesheet stacks at 320, 390, 600, 768, 1024 and 1440 px), using representative filter panels, action controls and form inputs. Checked control containment, pairwise filter control overlap, document horizontal overflow, form-field containment and employee process heading spacing. All passed. Desktop visual inspection completed. These are representative template checks; every signed-in page state and physical iPhone Safari have not been verified.
