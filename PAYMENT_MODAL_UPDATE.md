# Payment processing: Mark Paid financial entry modal

- Payment Processing > Mark paid opens the same nine-field financial-entry form used in Financial (Type, Budget line, Cost center, Month, Debit/Credit, Amount THB, Document / Source Ref, Comment, submit button).
- The form's submit button reads **Mark Paid**.
- Payment status remains Processing until the entry is validated, saved in the active financial-year Financial ledger, and the Staff Portal payment update completes.
- Budget line options are filtered by the selected cost center. Amount is prefilled from the payment request, and all required fields are validated.
- Closing the form does not change payment status.
- A failed Staff Portal save attempts to roll back the linked Financial entry.
- Financial's existing reversal workflow continues to reopen the linked payment.

**Deploy:** Backup application storage/database and replace the current project with this ZIP. Test as an Accounting user with an approved payment and configured cost centers and budget lines. The project uses BiomedStorage shared application storage for its financial entries; live Railway validation has not been performed.
