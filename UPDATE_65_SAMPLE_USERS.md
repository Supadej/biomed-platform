# Requested sample user removal

Removed the twelve directory profiles shown in the supplied screenshots: Managing Director, Operations Director, Diagnostics Manager, Research Specialist, Sales Specialist, Accounting Officer (Demo), and DEMO Employees 1–6. These profiles had no login accounts.

Deploy this project to the existing Railway service using the existing persistent volume and database variables. On startup, a transactional, one-time migration removes these same sample profiles from the existing database. Do not replace the live database with the bundled database. Take a normal backup before deploying.

The migration matches both original profile ID and email. Repurposed profiles and profiles with registered login accounts are preserved. Existing transaction records, owners, history, role definitions and other users remain unchanged. Removed managers are cleared from remaining directory profiles, if applicable. The original sample profiles were also removed from initial directory defaults.

After deployment, refresh User directory and User library. All twelve screenshot profiles should be absent. This package has not been deployed to Railway by ChatGPT.
