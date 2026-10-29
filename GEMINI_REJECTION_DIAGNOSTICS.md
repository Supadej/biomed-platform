# Gemini rejection diagnosis
Authenticated internal responses now include Google's HTTP status, error status,
reason codes, and a capped, redacted error message. Request URLs, headers and
error metadata are not returned. Known API key strings and the exact selected
credential are redacted. Tests confirm error code visibility and key redaction.

Deploy while preserving database, API keys and encryption secret; send Hello once.
Read the NEW error, not old history. It should include e.g. HTTP 403 and a reason.
Share that error text without credentials.

Google notes that models.list success does not prove generation eligibility.
In Google AI Studio inspect the same key's project for Free tier unavailable,
Restricted, Payment needed, or blocked key notices. If Google disallows a project
on the Free tier, a new key in that same project will not restore free access.
No paid tier is enabled by this package.

Eight Gemini tests and existing history/separation tests pass. No live API call
was made; the actual user's rejection remains undiagnosed until its detail is read.
Reference: https://ai.google.dev/gemini-api/docs/troubleshooting
