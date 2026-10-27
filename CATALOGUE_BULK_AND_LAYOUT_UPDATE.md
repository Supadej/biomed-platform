# Catalogue bulk publication + portal layout update

- Catalogue Management now renders inside the existing Staff Portal navigation using a same-origin embedded management workspace. Opening the management page directly continues to show its standalone header.
- Bulk visibility tool filters by brand, category, current published/hidden state, and product/SKU substring. Preview shows the exact matching count; the user confirms the update. Updates operate over every matching catalogue row (not only the displayed page), with an optimistic count check to catch changes between preview and submission.
- An empty filter matches the entire catalogue: preview and confirmation are required before changing all entries.
- Enquiry Basket drawer uses responsive 3-/2-/1-column forms and smaller-screen overflow safeguards.
- Existing source data, authentication accounts and password values are unchanged. Preserve the deployed SQLite database and persistent volume during deployment.

## Validation limitations

Python and inline JavaScript parsing were checked. No live Railway authenticated or browser screenshot testing was performed. Back up data before deployment and test bulk changes on a small filtered sample before performing large-scale publication.
