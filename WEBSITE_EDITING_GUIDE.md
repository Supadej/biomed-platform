# Website editing guide

Sign in to Staff Portal → Website Content. Your role needs Website Content access and the relevant create/edit/publish permissions. Publishing website sections requires publish permission. Creating or editing an item directly as Published also requires publish permission.

## Edit the homepage cards

Under Website sections — page editors, expand Quality & services. Edit the certification small heading, title, description, button label and certificate URL; the support card has corresponding fields. Save page changes. The main section heading and introduction are editable above these fields.

Expand News / resources / careers to edit the three homepage cards: title, description, link label and destination URL. Default destinations are news.html, events.html and careers.html.

## About image

Expand About Biomed. Section image URL / local asset path replaces the image on the LEFT of the About text. A bundled generated laboratory image is provided at assets/about-biomed-laboratory.png; it is illustrative and does not depict actual Biomed personnel or premises. Enter an image URL or another local assets path to replace it. Image description, About button label and destination are also editable.

## Customize the separate pages

Expand News & scientific updates page, Events & training page, or Careers at Biomed page. Edit the heading, small label, introduction and optional additional image/content. Use Preview page to open the public page. Additional HTML is rendered in a sandboxed frame.

## Publish updates

Use Create website item. Choose News (scientific updates), Event, or Career. Enter the title, summary and full article/event details/job description. Optional fields include image, publication date, event date/location, deadline, department, employment type, related/registration/application URL and its button label. Save Draft to keep it private. Publish when ready. Edit, unpublish or remove items in Content library.

The public pages show their own published category. Each item opens its own detail view. No job vacancies or upcoming events are invented; empty pages display an appropriate message until content is published. Website visitors do not need to sign in. The public endpoint returns only website sections and published item fields, without Portal users, roles, requests or drafts. The publication date controls display ordering, not scheduled publication.

## Run and preserve records

Stop the old server before starting the new folder. Copy your existing data/biomed.sqlite3 into the new data folder before first launch if you want to retain your records. No database reset or schema migration is required by this update. Refresh public pages after saving changes.

## Validation

Run python3 tests/test_website.py and node tests/test_website.js. Checks cover anonymous public access, private-data exclusion, draft exclusion, publish permissions, safe link handling, editable card fields, customized headings, category-specific lists and article details. Existing workflow checks pass. Native browser visual verification remains unavailable.
