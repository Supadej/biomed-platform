# SQL Server 2012 migration materials

This folder provides a SQL Server 2012 compatible **target schema** and a starter data-transfer path for the current SQLite application. The application still runs on SQLite; these files do not make it run on SQL Server.

## Transfer steps

1. Back up and stop the SQLite app.
2. Create an empty SQL Server 2012 database and run `001_biomed_platform_sql2012.sql` in SQL Server Management Studio.
3. On a trusted migration machine with Python and `pyodbc`, export the SQLite workspace: `python export_sqlserver.py ../data/biomed.sqlite3 biomed-transfer.json`.
4. Set `BIOMED_SQLSERVER_CONNECTION` securely for the destination and run `python import_sqlserver.py biomed-transfer.json`.
5. Verify row counts and application values in a non-production staging database.

The transfer file contains password hashes and sensitive workspace data; protect it, restrict access, and delete it securely after validation. Do not place connection passwords in source code or commit them.

## Compatibility boundary

The schema uses SQL Server 2012 types and avoids newer JSON functions. It represents this app's current workspace payloads, account/session records, and indexed transaction projections. It is not a translation of the earlier 63-table / 90-view SQL Server system. The importer currently transfers workspace values and account hashes; document/master/stock projections must be rebuilt by the future SQL Server runtime adapter. That adapter, transaction and concurrency behavior, deployment security, backups, and staging tests are still required before hosting this app on SQL Server. This is a useful starting point for migration, not a guarantee of zero migration work.
