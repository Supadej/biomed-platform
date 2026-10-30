# Role-based online manual

Open User manual in the signed-in workspace header. The interactive HTML manual includes searchable contents, system filtering, ID-only personal bookmarks, chapter printing, objectives/benefits, current user type and role responsibility, workflows, fields, permitted action instructions, troubleshooting, glossary and support guidance.

The server checks current permissions and returns only available module/action content. Responsibility descriptions come from Roles & responsibilities. Refresh access, returning to the page and periodic refresh update the projection. A requested role in the URL is ignored. Session expiry clears prior content. No new business permissions are granted.

This Railway-only edition retains SQLite and uses Waitress/WSGI via run_server.py. Dockerfile and railway.json use that entry. DEPLOY_GITHUB_RAILWAY.html is an interactive offline deployment runbook with command copying and checklists; its Markdown source is included. No separate SQL Server 2022 project is included, following the cancellation of that work.

Validation: 350 Python tests passed, plus DOM checks for personalized content/search, escaped responsibility text, bookmarks, access revocation and session expiry. Browser/mobile visual validation and real Railway deployment were not performed.
