# PACT v1.2.0 validation

Windows x64, 24 September 2026.

50 Python tests and five installer path cases passed during the build.

Ten new tests cover CSV export/import round-trip, no invented sessions/hourly history, duplicate and existing-date skips, malformed/negative/nonfinite/out-of-range values, duplicate dates, unsupported CSV schemas, imported totals in backups, older .pact compatibility, reset confirmation and Cancel, preserved settings/recovery, blocking old Garmin backfill after reset, preview-before-import, and safety-backup failures preventing changes.

Imported daily totals are included in dashboard history and CSV totals; hourly amounts remain unavailable rather than fabricated. Full ZIP exports retain imported totals separately. All prior timer, export, health, backup, undo, docking, hover, theme and slide tests remain passing.

Rendered and inspected Settings at 320 pixels and the reset confirmation dialog using synthetic data. Cancel is the default action. No reset or CSV import was performed against the user's actual database.

An isolated v1.1.1 installation was upgraded to v1.2.0 while running. Hidden launch, second-launch reveal, graceful shutdown, upgrade shutdown, database/target/token-sentinel preservation, installed startup self-test and uninstall passed. The additive imported_totals table is created without removing existing records.

ZIP integrity and release SHA-256 checksums are verified. Installer is unsigned. CSV import supports PACT daily totals exports, not arbitrary spreadsheet layouts or session/hourly CSV files. Existing dates are skipped as whole days. CSV cannot recover settings or detailed history absent from the export; .pact remains the complete migration format. Reset preserves backup files and may repopulate today's health through Garmin, while excluding older automatic backfill.
