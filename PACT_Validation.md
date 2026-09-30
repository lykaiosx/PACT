# PACT v1.7.0 validation

85 Python tests and five installer path cases passed. New tests cover eight distinct story graphics, leap-month totals, partial-month labels, missing data, animation progress, pause-on-hide, weekly/monthly navigation and notification opening of the completed month. The new suite also passed at 2x Qt scaling. Existing 90-day CSV/full-backup restoration and all earlier tests remain passing.

Rendered and inspected all eight slides using synthetic data. Fixed graphic clipping in the consistency grid and improved footer wrapping before building. The attached contact sheet contains sample data, not real user records. Slide transitions interpolate position over 650 ms; optional playback advances every 5.5 seconds and stops at the end or when hidden.

Packaged startup self-test and isolated upgrade from v1.6.0 passed, including hidden launch, single-instance reveal, shutdown, update preservation and uninstall. Real user data and Garmin credentials were not modified.

Monthly is the default; current-month data is marked so far on every slide. Weekly mode uses completed Monday-Sunday weeks. No all-time records are claimed. Goal streaks use current targets. Missing measurements remain unavailable. Creatives graphics show at most 64 tiles and explicitly label that cap when needed. Edits/imports are disclosed in the overview. Monthly/weekly notification triggering is tested with a mock tray; OS delivery depends on Windows settings.

Source/package archive integrity and SHA-256 checksums are verified during packaging. Installer remains unsigned.
