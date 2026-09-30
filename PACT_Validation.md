# PACT v1.6.0 validation

Windows x64, 30 September 2026.

80 Python tests and five installer path cases passed. Six new tests cover live width endpoints/midpoint and backup preservation; completed-week/year boundaries and empty data; totals, goals, streaks, busiest days and comparisons; missing manual/health data and recalculation after edits; notification once-per-week and opt-out; and review navigation back to Settings. The new suite also passed with Qt 2x scaling.

The 90-day CSV/full-backup restoration check passed, including charts, heatmaps, totals, sleep and hover details. All previous display, edit-history, correction, timer, theme, hydration and export checks passed. The packaged startup self-test passed.

Rendered and inspected the live slider at its midpoint and a weekly review with synthetic activity, habits and sleep. The slider spans the original monitor-relative width to the existing enlarged width, not a percentage of screen area. Moving it updates the actual sidebar and persists the preference; the Settings font scales gradually. Full backups retain width and notification preferences.

An isolated v1.5.1 installation was upgraded to v1.6.0. Hidden launch, single-instance reveal, graceful shutdown, update shutdown, database/target/token-sentinel preservation and uninstall passed. Tests used synthetic data; real user data and Garmin credentials were not modified.

Weekly reviews cover completed Monday-Sunday weeks. Coverage counts accompany comparisons and habits; missing records are not invented. Goal streaks use current targets and cover the selected week. Prior corrections/imports are reflected in current totals and flagged. Notifications are requested once per latest completed week with recorded data while PACT is running, including a delayed check on startup and hourly checks. Native Windows notification delivery depends on user/OS settings; the trigger and opt-out were verified with a mock tray, not a live notification delivery test. Older weeks remain available through the review date selector.

Release archives and checksums are verified during packaging. Installer remains unsigned.
