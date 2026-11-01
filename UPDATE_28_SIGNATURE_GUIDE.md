# Update 28 — customer signatures and service report cleanup

## Brands

Open Biomed IS → Master Data → Brands, directly below Suppliers. The New brand field has its label above it, a full-width input and a button aligned with the input. The layout wraps on narrow screens. Shared operational brand behavior and the independent website Brand Catalogue are retained.

## Service job layout

The expandable **Service report information and customer feedback** section is below the service report fields. Area Code, Department, Start Date, End Date, Instrument Warranty, Instrument Ownership and Other Instrument Status are removed from the job form, displayed job details, selectable columns, and job CSV exports. Historical stored values are retained for record preservation, but are no longer printed. Contract and warranty date fields in their own registers remain available.

The PDF keeps the supplied company heading, logo, job-type list, report sections and footer. The obsolete fields were removed from the PDF. Service Date and Engineer identify the work. The former instrument-status panel explains customer acknowledgement. Continuation pages use the revised form.

## Customer signature — mobile, iPad or computer

1. Open a Service Job's **Details** and select **Customer signature / acknowledgement**, or edit the job and expand the customer feedback section.
2. Review the report with the customer. Enter the customer name.
3. Let the customer draw with a finger, stylus or mouse and confirm the acknowledgement checkbox.
4. Save the job. The signature, customer name, server timestamp and capturing employee are stored with it.
5. View/print the PDF or use Email PDF. Both use the same report containing the saved signature, printed customer name and Bangkok date/time.

Clear signature removes it when the job is saved. Drawing a replacement replaces the previous drawing. Saving an unchanged signed job preserves its original timestamp. Changes to the signed report require clearing or capturing a new signature. A changed name or acknowledgement also requires a fresh drawing. The signed instrument/customer/parts details are snapshotted, so later master-data edits do not rewrite those details in the signed report. This is an in-person signature capture using the staff member's authorized session; no public signing link is created.

Signature capture uses the existing Service Job edit permission; report viewing/email uses the existing print permission. Job audit records retain save history. CSV exports include signer name and signing timestamp, rather than raw signature coordinates.

## Validation

Browser checks passed for actual touch input, saving/reopening the signature, unchanged signed-job saving, PDF generation, removed fields and section order. Brand form checks passed at 320, 768 and 1440 pixels. The final PDF was visually inspected. Signature validation, report, and inventory regression tests passed. The packaged database contains no fabricated customer signatures. This update has not been deployed to a live server.
