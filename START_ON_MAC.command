#!/bin/zsh
cd "$(dirname "$0")" || exit 1
PORT=8765
printf '\nBiomed Test Workspace · SQLite\n'
if lsof -nP -iTCP:$PORT -sTCP:LISTEN >/dev/null 2>&1; then
  printf '\nPort %s is already in use. Stop the older Biomed terminal server using Control+C first.\n' "$PORT"
  printf 'Then run this command again.\n'
  exit 1
fi
printf 'Website: http://127.0.0.1:%s/\n' "$PORT"
printf 'Staff Portal: http://127.0.0.1:%s/?portal=1\n' "$PORT"
printf 'Biomed IS: http://127.0.0.1:%s/biomed-is.html?source=1\n' "$PORT"
printf 'Budgeting: http://127.0.0.1:%s/biomed-budget.html\n' "$PORT"
python3 serve.py
