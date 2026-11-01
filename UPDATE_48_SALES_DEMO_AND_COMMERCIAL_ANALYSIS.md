# Deep analysis for Staff Portal

Choose **Deep analysis** below the filters on Sales Performance, Demo & Evaluations, Quotations & Tenders, or Sales Pipeline. **Records** returns to the existing forms and registers. The view follows the page's selected dates, search, statuses and other available filters, and uses the records already authorized for that user. Switching views preserves the filters and existing record-form nodes.

## Sales Performance

- Target, invoiced achievement, attainment, remaining target and average achievement per displayed month.
- Monthly target and achievement charts on a common scale.
- Target gaps by representative and achievement composition by product line.
- Representative, product-line and monthly detail tables, including change versus the prior displayed month when a nonzero baseline exists.
- Review prompts for representatives below target, invoice entries without positive matching targets, and targeted lines without achievement.

Achievement uses the existing approved Biomed IS invoice calculation less linked approved credit notes. Manual sales actuals remain excluded. Sales Performance values use the existing THB reporting basis. A target gap is target minus achievement; negative gaps indicate achievement above target. Missing/zero targets do not produce an attainment percentage.

## Demo & Evaluations

- Active/planned demos, finished evaluations, recorded conversion, past-end-date evaluations and scheduled duration.
- Charts for current demo status, approvals, monthly starts, owners, product lines and finished evaluations by institution.
- An evaluation follow-up queue for overdue open evaluations, missing finished-evaluation feedback and missing next actions.

Finished means Completed, Converted or Closed. Cancelled approvals are excluded from active/finished-rate calculations. Conversion is Converted divided by finished evaluations. It reflects the recorded status rather than attributed invoice revenue. Scheduled days include start and end days and are not a measurement of actual usage time.

## Quotations & Tenders and Sales Pipeline

Analysis includes manual and linked records in the filtered register. It shows:

- Open and won values, closed-decision win rate, probability-weighted open value and overdue expected-close/deadline counts.
- Stage/outcome composition, Manual/Linked composition, owner and product-line values, dated-record trends and open-record ageing.
- Owner outcomes, customer concentration, follow-up review queue and won/lost justifications.
- Review prompts for deadlines passed, 30+ days without update, missing follow-up and missing/invalid probability.

Select **Analysis currency** to inspect one currency at a time. Values from different currencies are never summed. Win rate is Won divided by Won + Lost, excluding open/cancelled records. Weighted value includes only open records with an explicit valid probability from 0–100%; unknown probabilities are excluded and counted. Linked records without recorded probabilities are not assigned a guessed probability. The weighted amount is not a forecast.

Ageing uses the source record date. Staleness uses its latest recorded update, falling back to creation/source date. Missing or future dates are shown separately. Stage charts describe the current state of the filtered cohort; they do not claim historical stage-to-stage conversion. Free-text follow-up notes are not interpreted as structured due dates.

## Access and data

Analysis is read-only and requires the existing module view permission. Existing source visibility and owner/team filtering apply. No new tables, write permissions, API keys or external service are required. Including a manual tender in the pipeline continues to show its source record without creating a duplicate opportunity. Existing export, approval and editing behavior is retained.

## Validation

All 291 Python regression tests passed. New calculation tests cover sales totals/gaps/months, demo rates and overdue rules, closed-decision win rates, probability exclusions, currency separation, empty data and escaped text. Integration checks cover all four analysis tabs, filtered payload wiring, view authorization and preserving filter/draft nodes. Existing manual follow-up, row toggling and column-width checks passed.

Browser preview confirmed the sales dashboard's chart rendering and representative-filter update using fictional records. Further browser interactions timed out in the test runner; a complete responsive visual check of all four authenticated pages remains unverified.

## Installation

Preserve the deployed database, replace the application files and restart using the normal update procedure. New analysis assets are versioned for refresh. QA fixtures and test sessions are excluded. No database reset is needed. The package has not been deployed automatically.
