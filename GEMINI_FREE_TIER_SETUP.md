# Google Gemini free-tier setup

1. Visit https://aistudio.google.com/apikey and sign in to your Google account.
2. Create a Gemini API key in a project eligible for the Free tier. Check the
   project's tier in AI Studio. Do not enable paid billing if you want free-only
   usage. Free-tier quotas and regional/account eligibility apply.
3. Deploy this ZIP's source while retaining your current production database,
   volume and BIOMED_AI_ENCRYPTION_KEY.
4. Open AI Chat Management > My API Settings, paste your Gemini key (AIza... or AQ...),
   and Save encrypted key. This replaces your current PERSONAL provider key.
5. Enable Internal Copilot in Enable / Disable and select My personal API key.
6. Send Hello. Gemini keys route to Gemini; OpenAI keys continue routing to OpenAI.

Model: gemini-2.5-flash-lite. Optionally override via
BIOMED_INTERNAL_GEMINI_MODEL (internal) and BIOMED_GEMINI_MODEL (website).
Model availability and free-tier eligibility can change.

Company configuration in Railway:
- GEMINI_API_KEY: public website visitor chat.
- BIOMED_INTERNAL_GEMINI_API_KEY: internal company assistant.
Then enable the matching service / internal company-key switch in admin.
Gemini company variables take priority over corresponding OpenAI variables.
There is no automatic paid-provider fallback or paid-billing activation.
The application cannot verify that a Google project is on a free billing tier;
use a Free-tier project to avoid paid charges.

Data use:
Google says free-tier prompts and replies may be used to improve its products.
Use general workflow questions only; do not send confidential business, customer,
employee or patient information. No live database retrieval is included.

Validation:
Five mocked Gemini tests cover REST request/response parsing, personal encrypted
key saving, separate company keys, public catalogue context, and quota messaging.
Existing AI separation/history tests and JavaScript syntax checks pass.
No live Google request or Railway browser test has been performed.

Official references:
https://ai.google.dev/gemini-api/docs/pricing
https://ai.google.dev/gemini-api/docs/billing
https://ai.google.dev/api/generate-content
