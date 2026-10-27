# Gemini key-format correction
Support both standard AIza keys and newer AQ. authorization keys. Permit key
lengths up to 4096 characters and reject whitespace. Both formats route to Gemini
using the x-goog-api-key header, never to OpenAI. Keys remain encrypted at rest.

Copilot now displays whether a personal key has been saved, refreshes that status
after save/removal, and prevents sending with an unsaved key still in the field.
The successful save message explicitly confirms readiness to send.

Six Gemini tests and existing AI/history tests pass. This validates local routing
and storage behavior, not the user's actual credential or a live Google call.

Deploy source while preserving the production database and encryption secret.
Hard refresh, paste the COMPLETE Gemini key, Save encrypted key, wait for
Personal API key: saved, then send a new message. Previous error bubbles remain
in history until cleared; they do not indicate the new save failed.

Official key-type reference: https://ai.google.dev/gemini-api/docs/api-key
