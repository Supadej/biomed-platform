# Railway workspace save fix

The production WSGI entry now forwards PUT and DELETE requests to the existing application handlers. Staff Portal's storage adapter uses PUT when saving workspace data, including its initialization save after login or returning to the portal. These methods were omitted from the new production entry.

The existing authenticated handlers retain their permission checks, origin validation, transaction handling and revision conflict checks. The change also restores PUT-based workspace saves in Biomed IS and Financial. No database replacement or password changes are required.

Verified through a real local Waitress listener: sign-in, workspace read, save, return/read, second save, stale revision rejection (409), core workspace deletion rejection (403) and unauthenticated save rejection (401).

Deploy this project to the existing Railway service, preserving its persistent volume and variables. Reload open pages after deployment, then sign in. If an HTTP 500 persists, inspect the Railway deployment logs at the time of the error; a screenshot alone does not identify a separate database failure.
