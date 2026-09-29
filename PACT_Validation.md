# PACT v1.4.0 validation

Windows x64, 29 September 2026.

67 Python tests and five installer path cases passed. The nine display tests include a large-screen check that the canvas grows more than 55%, actually scrolls, and returns to its original size when disabled. This suite also passed at 2x scaling. The eight new correction tests cover the simple Add/Deduct UI, calculated end time, multi-session and full deductions, imported and mixed totals, corrected backup restoration, cross-midnight isolation, active-timer protection, Undo collision protection and advanced full-session deduction.

The 90-day export/reset/CSV import and full-backup restoration check passed, including Work/Learning totals, rendered graphs, heatmaps, sleep and hover values. Previous correction, undo, theme, docking, autosave and Garmin mapping tests remain passing.

Visually inspected the enlarged dashboard/Settings and the simple Add/Deduct panels, including a 320-pixel sidebar. Default layout remains unchanged. Readability mode uses about 1.6 times the default width with a 560-logical-pixel minimum, bounded by the monitor width. Settings and hover text enlarge, live text uses stronger weights, and excess dashboard height scrolls. Actual monitor hot-plugging was not tested; signal-driven refitting has automated coverage.

The packaged startup check and an isolated upgrade from v1.3.1 to v1.4.0 passed: hidden startup, single-instance reveal, graceful shutdown, closing the running app for upgrade, database/target/token-sentinel preservation and uninstall. Testing did not touch real user progress or Garmin credentials.

Deductions operate on a day's latest recorded sessions first, followed by imported totals. They preserve adjacent dates and reject amounts greater than the recorded total. A running timer overlapping that date must be stopped. Each deduction is transactional and can be undone as one correction, including after restart. Imported data has no original session timestamps, so no hourly distribution is invented. Exact start/end editing remains available.

Release archives and SHA-256 checksums are verified during packaging. The Windows installer remains unsigned.
