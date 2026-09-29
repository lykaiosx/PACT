# PACT v1.5.0 validation

Windows x64, 30 September 2026.

74 Python tests and five installer path cases passed. Seven new cases cover Settings tabs and dated edits without changing today, unknown versus explicit zero, daily Undo preserving a history entry, time add/deduct/undo audit, backup/reset/restore history, export flags and import provenance, rejected health/future edits, and one-time migration of earlier time corrections.

The 90-day CSV and full-backup restoration check passed, including chart/heatmap rendering, hover details, annual totals and sleep. All earlier time, hydration, theme, docking, correction and backup checks passed. The ZIP export test now expects edit_history.csv in addition to existing files.

Visually inspected Edit data and Edit history in light mode and Edit data in dark mode at a 320-pixel sidebar width. Tabs, inputs and borders follow the theme. Daily inputs save automatically and distinguish Not entered, No/zero and Yes/nonzero. Garmin measurements remain read-only. Existing zero entries without recorded status cannot reliably be distinguished from default values and are shown as Not entered in the dated editor/export.

An isolated v1.4.0 installation was upgraded to v1.5.0. Hidden startup, single-instance reveal, graceful shutdown, update shutdown, database/target/token-sentinel preservation and uninstall passed. The packaged startup self-test passed. No real user data or Garmin credentials were modified.

History persists in full backups and is included in all-records ZIP exports. CSV imports log their provenance but cannot recover the original history. Reset clears local history after confirmation and a safety backup. Earlier retained time corrections migrate once, while unlogged historical daily changes cannot be reconstructed. Undo adds a record; this is local history, not tamper-proof certification. The history panel loads the most recent 200 records and supports Show more history.

Release archives and SHA-256 checksums are verified during packaging. The Windows installer remains unsigned.
