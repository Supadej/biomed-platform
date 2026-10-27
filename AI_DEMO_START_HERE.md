# Test Copilot with fictional data

This release includes demo records in the bundled SQLite database. All records
use AI-DEMO identifiers or DEMO labels; none are real customer or company data.
The test administrator login is unchanged.

## Railway: keep your existing database

Deploy the updated source without replacing your mounted database or changing
your encryption key. Existing Railway volumes do not receive the bundled seed.
After deployment, open Railway SSH for the application service and run:

```sh
python3 seed_ai_demo.py --database /data/biomed.sqlite3 --email testadmin@example.invalid
```

If using another login, replace the email with that account's email. The script
adds Portal examples owned by that existing account. It creates no accounts,
changes no passwords, changes no roles and does not enable AI or grant permissions.
It makes a full SQLite backup first and adds only missing AI-DEMO records.
Running it again for the same account does not duplicate the examples. Existing
business records are retained. Refresh the three applications after importing.
Demo IS documents remain Draft and create no posted stock movements.
Demo Budgeting figures are independent fictional test entries, not IS postings.

## Enable the permitted functions

1. System Admin: AI Chat Management → enable internal AI. Configure a working
   OpenAI personal key, or the company key and its internal-use switch.
2. Staff Portal → OpenAI Access Management → Role defaults: choose the role,
   enable the required modules and functions, and save role limits.
3. Employee access limits: choose the employee, select allowed functions and save.
4. My access: enable Copilot, the required modules, and
   **Share permitted record summaries with OpenAI**. Select available functions
   and save. Previous saved denials are deliberately retained until changed.
5. Reopen Copilot, select the saved key and start a fresh conversation.

A role must already have the relevant application permissions, including
Internal AI use for non-admins. OpenAI access settings can restrict those rights,
but cannot grant new application rights. Private HR/payroll fields, attachments,
credentials and unowned employee records are excluded. Some functions expose
counts or metadata only. The AI does not generally create, edit, approve or
delete records; Calendar drafts still require explicit confirmation.

Try these prompts after enabling the relevant permissions:

- "List my demo tasks and requests and their status."
- "What DEMO quotations and invoices can I see in Biomed IS?"
- "Show the demo product and inventory lot count."
- "Compare permitted revenue actual, cost of goods and expense commitments in Budgeting."
- "Which modules and functions are available to you?"

Cross-system questions use all enabled and permitted module summaries.
To test denial, disable IS invoice access for the employee, save, and start a
new chat. The new AI reference snapshot must omit that function. Previously
shared messages remain in the user's history; use Clear history before a clean
permissions test. Live OpenAI billing/model availability must be tested on your
Railway installation.
