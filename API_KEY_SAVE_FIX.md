# Personal API key saving

The Dockerfile now installs requirements.txt, including cryptography.
Missing or invalid encryption configuration returns a clear error.

In Railway application service Variables, add BIOMED_AI_ENCRYPTION_KEY.
Generate its value privately on your Mac:
python3 -c 'import base64,secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())'

Copy the entire output as the variable value. It is a server encryption secret,
not your OpenAI API key. Keep it private and retain the same value for future
deployments so existing encrypted keys remain readable.

Deploy the updated source and apply the variable change. In My API Settings,
Encryption should show Configured. Paste your OpenAI API key and Save encrypted key.

Tests: missing/invalid configuration, encrypted storage/decryption, and six
AI separation tests pass locally. No real OpenAI API call was made.

Keep the current Railway database and volume. The bundled seeded database is
not a replacement for existing production records.
