#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
printf '\nBiomed platform: Website · Staff Portal · Biomed IS · Budgeting · CRM\n'
printf 'Sign in at http://127.0.0.1:%s/?portal=1\n' "${PORT:-8765}"
printf 'CRM: http://127.0.0.1:%s/crm/index.html\n\n' "${PORT:-8765}"
exec python3 serve.py
