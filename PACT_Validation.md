# PACT v1.3.1 validation

Patch verification: all 58 tests, five installer path cases and the 90-day restoration check passed again. Inspected the outlined toggle in light/on and dark/off states, including a 320-pixel sidebar. The packaged startup self-test passed. The installer behavior is unchanged; the upgrade integration results below are from v1.3.0.

Windows x64, 25 September 2026.

All 58 Python tests and five installer path cases passed during the build. Eight new display tests cover unchanged default geometry, proportional adjustment and screen bounds, persistent toggling and reversal, display-change refitting, backup/reset preservation, one-time welcome dismissal, its Settings shortcut, and hidden/testing suppression. The display suite also passed at 2x Qt scaling.

Rendered and inspected the adjusted dashboard and Settings at a simulated 1280x720 work area, plus the welcome message. Newsreader and the existing theme/layout remain in use. Default sizing remains unchanged; adjusted sizing uses available logical monitor dimensions, widens the dashboard up to 600 logical pixels and scrolls vertically when needed. Real monitor hot-plugging was not exercised; signal-driven refitting is covered by an automated check.

The repeatable 90-day round-trip check passed: exported synthetic history was reset and reimported from daily CSV, restored from the original .pact backup, and restored from a backup made after CSV import. Work and Learning histories, annual totals, latest sleep, rendered charts/heatmaps and hover details matched before and after each path. All existing timer, export, Garmin mapping, autosave, theme, tooltip, undo and slide tests passed.

An isolated v1.2.0 installation was upgraded to v1.3.0 while running. Hidden launch, second-launch reveal, single-instance behavior, graceful shutdown, upgrade shutdown, database/target/token-sentinel preservation, updated startup and uninstall passed. The packaged application self-test passed. Testing used isolated data; no real user progress or Garmin credentials were modified.

Source/package ZIP integrity and release SHA-256 checksums are verified during packaging. Installer remains unsigned. Garmin checks still depend on data uploaded by the watch/phone to Garmin Connect. Display adjustment is off by default and saves automatically when toggled. Existing users see the display-options message once on their next visible launch, as do new users; hidden startup does not show it.
