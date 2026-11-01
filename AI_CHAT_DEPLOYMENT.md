# Ask Biomed — AI & Human Live Chat

## Included
- Public website chat widget (`index.html` and `catalogue.html`).
- Staff Portal > Website & Administration > AI Chat Management: inbox, take-over/return to AI, staff replies, close, personal API settings.
- SQLite chat schema initialized on startup; history persisted in same database as the existing portal.
- Public assistant uses only **OPENAI_API_KEY** (company project), not any employee's personal API key.
- Published catalogue-only lookup provides a small number of product snippets to the assistant.
- Human handoff asks visitor for name and email, retaining the conversation in the staff inbox.

## Required Railway configuration
- Keep the existing `BIOMED_DATABASE_PATH` and persistent Railway volume unchanged. Back up production first. Do not overwrite the DB with the ZIP's sample file.
- Set `OPENAI_API_KEY` as a Railway environment secret to enable website AI replies. If absent, conversations still reach staff but AI answers are unavailable.
- Set `BIOMED_AI_ENCRYPTION_KEY` to a persistent Fernet encryption key for personal API keys. Generate privately: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. Treat this as a production secret; rotating it without migrating keys makes existing stored keys unreadable.
- Ensure `cryptography` is installed in deployment. API uses Python standard-library urllib; no OpenAI Python SDK required.
- Optional `BIOMED_AI_MODEL` defaults to `gpt-4.1-mini`. Confirm model access for your API project.
- Install dependency using `pip install cryptography` or add `cryptography` to requirements as needed.

## Limitations and essential precautions
- Personal API keys are securely stored but **not used for anonymous visitor sessions**. This avoids charging an arbitrary employee. Personal-key-backed staff AI actions are a later enhancement.
- Existing chat inbox is not yet connected automatically to Sales Plan or email notifications. Enquiry Basket integration remains intact.
- Staff inbox uses polling, not WebSockets or mobile notifications. No guaranteed immediate response.
- API backend has no public per-IP rate limiter or automated abuse prevention. Add a reverse-proxy/IP rate limit, quotas, logging, retention policy and spam protections before significant public traffic.
- Review Thailand PDPA privacy notice and obtain applicable visitor consent before rollout; this module stores messages and optionally names/emails in the Biomed database and sends text to OpenAI when AI is enabled.
- Product catalogue retrieval is a basic term match (published records only), not semantic document search.
- No medical or legal advice, quotation promises or automatic sales order generation; review output before operational use.
- For strict usage caps implement server-side per-account token accounting. The interface does not claim to cap provider billing.
- Python does not rate-limit OpenAI requests and waits synchronously up to 25s per visitor message; provision accordingly.

## Test checklist
1. Log in as System Admin; open Staff Portal > Website & Administration > AI Chat Management.
2. Verify API settings without exposing a saved secret. Save/remove a personal test key if encryption is configured.
3. Visit website and click Ask Biomed; submit a test chat; switch to staff inbox and click Take over.
4. Send human reply and confirm it appears in visitor chat (polling interval ~12 seconds).
5. Enable `OPENAI_API_KEY` and verify public AI answers; repeat without key to confirm clear fallback.
6. Test mobile and desktop chat layout and test existing Catalogue, Received Enquiries and Sales Plan functionality.
7. Verify Railway deployment uses the original persistent DB and the existing accounts remain valid.
