# Product Catalogue & Enquiry Basket

- Public page `/catalogue.html`: published product search, brand/category filters, pagination, enquiry basket, contact form.
- Staff page `/catalogue-admin.html`: edits, hide/show, import UTF-8 CSV, sync from Biomed IS Product Master, incoming enquiry queue.
- Admin access uses existing website content permissions and login cookie. New database tables are created by `serve.py` on startup.
- Product Master sync is **manual** (click Sync) and **adds missing master items only**; existing curated catalogue details and publication flags are preserved. Newly synced products are hidden. The catalogue data is independent from Product Master edits until next sync.
- CSV columns: sku,name,brand,category,subcategory,description,image_url,specification,master_id,visible. Required sku/name. Up to 18 MB and 200,000 rows/file. CSV explicit visible 1 publishes, 0 hides; otherwise existing flags are preserved.
- Enquiries are persisted and staff can move their status New / In progress / Replied / Closed. Sending emails and creating CRM leads automatically are **not** implemented.
- For 100K+ catalogue entries this uses SQLite paginated results, but fuzzy searches with `%term%` will require full text indexing and load testing before heavy production traffic. CSV is one transaction and is limited to 18MB per file.
- Before deployment, back up database. Run authenticated acceptance testing, especially permission roles, CSV imports, and end-to-end enquiry submission.
