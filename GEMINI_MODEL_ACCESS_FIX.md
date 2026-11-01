# Gemini model access
The default is now gemini-3.1-flash-lite, listed with free-tier pricing in current
Google documentation. This does not guarantee a particular project's eligibility.

In Railway Variables set:
BIOMED_INTERNAL_GEMINI_MODEL=gemini-3.1-flash-lite
BIOMED_GEMINI_MODEL=gemini-3.1-flash-lite

Existing environment values override the default, so update any old model values.
Copy only the model identifier, without quotes. The server also normalizes a
models/ prefix and surrounding whitespace.

Copilot My API settings > Check Gemini models lists generateContent models
visible to the selected saved key. The response identifies the configured model.
Model listing alone cannot establish generation entitlement or free quota.
Keys are never returned. The check respects existing account/module permissions.

Seven mocked Gemini tests and existing AI/history tests pass. No live Google call
or Railway verification has been performed. Existing database and keys are kept.
Official references:
https://ai.google.dev/api/models
https://ai.google.dev/gemini-api/docs/pricing
