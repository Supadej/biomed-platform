# Biomed test installation — update 26

Service Jobs now shows **Email PDF** and **PDF report** beside every job, without expanding Details. Requires Service Jobs print permission. The Email PDF dialog prepares the PDF then offers device sharing, a downloaded .eml draft with the PDF attached, or a mailto draft with manual attachment. Browsers cannot force desktop mail clients to accept attachments through mailto. No email is sent automatically. Reload the page after installing this update.

## Test data

66 position-based test accounts reflect the supplied organization chart, including directors, operations, quality, accounting, procurement, LSR, diagnostics and service. The chart has no personal names; these are placeholders, not verified employees. Account names start TEST, email addresses use example.invalid. The account list and unique generated passwords are in TEST_ACCOUNT_ACCESS.json. Use only in the test installation. Existing accounts and roles are retained. IT positions are not automatically granted System Admin. Service managers approve engineer inventory; engineers cannot approve their own requests. Department managers use the existing department manager policy. Adjust individual permissions before real use.

19 product-family test items from nine represented research brands, with 57 lots and 57,000 units total, are in TEST Biomed Training Warehouse. Names/families are based on https://www.biomedthai.com/products/research.html, reviewed 28 October 2026. SKUs, prices, lots, quantities and expiry dates are fictional. These do not constitute verified manufacturer catalogue codes or actual inventory. Existing instrument history remains.

Three additional Draft documents per supported Biomed IS transaction type plus the broader fictional workflow fixtures cover customers/suppliers, quotations, orders, invoices, borrowing, returns, purchasing, delivery, HR, requests, tasks, sales and budget. Drafts do not post physical stock. Test document references use BMD-TEST identifiers to distinguish fixtures; new documents created through normal screens retain the requested daily numbering. Existing fixtures are not duplicated when the seed is rerun.

The additive seed script is seed_biomed_company.py. It backs up the database before changes. Do not run it against production stock. This download already includes the populated database; running the script is unnecessary.
