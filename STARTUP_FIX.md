Startup migration fix

Newer permission catalogue entries may omit the legacy field. Migration now treats that field as optional, preserving explicit permission assignments. Verified repeated database initialization and actual HTTP startup with /api/health returning 200 on a temporary copy of the bundled database.

Deploy updated source including permissions_policy.py. Preserve your Railway database volume and environment variables. No database reset is needed. If deployment still crashes, inspect Railway Deploy Logs and provide the final traceback; this package fixes the startup error reproduced locally.
