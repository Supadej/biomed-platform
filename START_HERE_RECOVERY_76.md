# Partial snapshot recovery — start here

This package restores the database from the original uploaded `Data from Github.zip`. It is NOT recovery of Railway's removed live filesystem, and it is not verified as the latest production backup. Keep any other downloaded database backups; a newer verified backup should take priority over this snapshot.

## What the snapshot contains
- 67 sign-in accounts, 67 Staff Portal users, 41 roles and role record-scope configurations.
- 21 departments; 65 users have a manager/reporting link.
- 31 operational brands.
- 9 website brands, all marked as test data. They may not include your edited brand content.
- 36 products (27 marked as test data), 9 customers (8 TEST-prefixed IDs), 5 warehouses.
- CRM: 6 sales pipeline stages, 4 helpdesk stages, 3 project stages; stored cards/events also include test fixtures.
- Website uploaded-file and catalogue tables are empty. Other assets may be referenced or embedded elsewhere; this does not recover missing external uploads.

Full counts are in `Recovery_Inventory_76.json`. Do not assume the operational records are real transactions. Review the restored site before resuming business entry.

## Railway setup — do this before entering information again
1. In the project canvas, press Cmd+K and search for creating a Volume, or right-click the canvas and use the volume creation option. Select the existing `biomed-platform` service and set its mount path to `/data`. Do not delete the service or alter another volume.
2. In the service's Variables tab, add:

   BIOMED_DATABASE_PATH=/data/biomed.sqlite3
   BIOMED_REQUIRE_EXISTING_DATABASE=1
   BIOMED_RECOVER_BUNDLED_SNAPSHOT=1

   Leave BIOMED_ENABLE_LEGACY_DATA_IMPORTS unset. Keep your existing AI encryption key and other credentials unchanged. RAILWAY_VOLUME_MOUNT_PATH is supplied by Railway when the volume is attached; do not add it manually.
3. Update the same GitHub repository using the contents of this package's top-level project folder. Keep application files at the repository root, not nested one folder deeper. The included `data/biomed.sqlite3` and `recovery-snapshot-manifest.json` must both be uploaded. This source snapshot is copied only when the mounted destination has no database file.
4. Deploy to the same service. The recovery runs at application startup, not during build or pre-deploy. If the volume is missing, not mounted or the checksum differs, startup stops without restoring. If any destination database file already exists, it is left alone; recovery does not replace it.
5. On successful startup, sign in using the accounts/passwords from the supplied snapshot. Open users/roles, reporting, visibility, brands, CRM stages and Biomed IS master data. Check what is still missing. Do not assume the demo-looking transactions are real business entries.
6. Remove BIOMED_RECOVER_BUNDLED_SNAPSHOT or set it to 0 after successful recovery. Keep BIOMED_REQUIRE_EXISTING_DATABASE=1 and BIOMED_DATABASE_PATH unchanged.
7. Download a full-system backup through the application, retain it outside Railway, and configure volume backups where available. Make another backup after re-entering missing setup.

The attached volume persists database writes across deployments while that same volume remains attached. Deleting the volume or service, changing the mount/path, or restoring an older backup can still lose changes.

## Safeguards
Recovery uses a verified snapshot and atomic create-if-absent: an existing database is never overwritten, including an empty or invalid file. A marker prevents automatic replay of the old snapshot if a previously restored database later disappears. Existing records/accounts/roles are not re-imported from legacy roster or demo scripts. Password hashes are retained, not reset.

The startup archive is a separate copy in `/data/backups`. It is not an off-site backup. Do not manually delete a database or marker to make recovery run again; inspect or archive any existing database first.

## Validation
- Original snapshot integrity: OK.
- Recovery onto a temporary simulated volume: all 83 original tables retained exactly.
- Restart after inserting new data: new record retained.
- Tests for opt-in, missing/unmounted volume, wrong database path, checksum mismatch, existing database preservation and one-time marker: passed.
- Annual/monthly budget regression checks: passed.
- Actual Railway mount/deployment and full browser visual tests remain unverified here.

The annual/monthly budgeting and layout changes from updates 74 and 75 are included. For this recovery package, the explicit recovery instructions above supersede the old instruction to require an already-populated volume before first startup.

Official volume setup reference: https://docs.railway.com/volumes
