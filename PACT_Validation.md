# PACT v1.0.0 validation

Windows x64 · 23 September 2026.

## Automated checks

All 26 checks passed: the existing 20 regression/export/UI checks (updated for autosave and meaningful bar targets), plus six targeted checks for this revision:

- Repeated pointer movement retains the same detail panel and position; short gaps do not hide it, leaving dismisses it, and the child panel is mouse-transparent and themed.
- Blank monthly columns and sleep legends have no hover details; unrecorded heatmap dates show Not available; ordinary controls have no native tooltips.
- Hover is restricted to the painted portion of a monthly bar.
- Theme/target edits persist without closing Settings, there is no Save button, pending numeric text commits on exit, and values survive reopening storage.
- Garmin hydration intake/goal mapping, exact US-cup conversion, zero intake and export fields.
- Hydration endpoint failure preserves other metrics and reports the partial failure; the app refresh timer is exactly 300,000 ms (five minutes).

## Visual checks

Rendered and inspected Learning/light, Settings and the themed hover panel. Verified left-facing Learning arrow, aligned italic hour legends, bold Health data, opaque Settings and automatic-save wording. Static design geometry is unchanged.

## Garmin check

Hydration mapping was verified against the Garmin response and synthetic test cases. Tests do not claim to trigger a watch upload. Watch-to-Connect latency remains outside PACT's control. New-password login/MFA was not retested.

## Windows installation

The build script compiled the launcher and installer and ran all 26 checks. Isolated upgrade tests cover hidden launch, second-launch reveal, graceful shutdown, updating a running development PACT 1.3 instance to release v1.0.0, database/target/token-sentinel preservation, and uninstall while running. A separate clean-install check runs the installed startup self-test.

Tests use a separate installation identity and synthetic data. They do not replace the user's installed app. Exports and preview tests use synthetic values. The source/runnable ZIP archives are checked for integrity. The installer is unsigned. Physical mouse/DPI combinations were not exhaustively tested; pointer-state stability was tested in Qt's event loop.

