# PACT v1.3.0

Run PACT_v1.3.0_Setup.exe to install or update on Windows 10/11 x64. The private runtime is included. Start Menu, Installed Apps, optional desktop/startup shortcuts and updater process management are preserved.

## New in v1.3.0

- The existing dashboard sizing remains the default. Settings → Appearance → Auto-adjust for readability enlarges the entire dashboard proportionally, including Newsreader text, icons and charts, using the monitor's available space. Smaller screens scroll vertically when needed. Turning it off restores the original sizing.
- The adjustment saves immediately, follows monitor/work-area/DPI changes, and is included in full backups. Windows DPI scaling is respected. Right/bottom docking and non-always-on-top behavior are unchanged.
- A one-time display-options message appears when PACT is first shown. Open Settings takes you directly to the panel; Got it dismisses it. Hidden startup does not show the message. Existing installations see it once after this update too.

## New in v1.2.0

- Settings â†’ Backup and restore â†’ Reset progress asks for explicit confirmation, defaulting to Cancel. It clears timers, daily entries, imported totals, health history and correction history while preserving goals, theme and Garmin connection. A `.pact` recovery backup is created first; if that fails, reset is cancelled. Running timers stop. Automatic Garmin backfill excludes dates before the reset day; today's readings may return on sync. Existing backup/export files are not deleted.
- Import daily totals (.csv) accepts PACT's exported daily CSV, including `daily.csv` extracted from an all-records ZIP. A preview shows date range and new/skipped counts. Existing dates with progress are skipped, so repeated imports do not double totals or overwrite records. A safety backup precedes the transactional import.
- CSV restores the daily Work/Learning totals, creatives, meals and health values present in the file. It cannot restore original session times, hourly distribution, observation history or appearance/goals that were not exported. Imported time is stored as daily totals, not fabricated sessions. It appears in analytics and daily exports, survives `.pact` backups, and is listed separately as `imported_daily_totals.csv` in full ZIP exports; unknown hourly values remain blank. Use `.pact` for complete migration. Older `.pact` backups remain supported.
## Fixed in v1.1.1

- Sync and chart hover messages wrap within the sidebar, including after resizing.
- The analytics divider remains stationary and single during both slide directions, including high-DPI displays.

## New in v1.1.0

- Click the Work or Learning time to add missed sessions, correct dates/start/end times, deduct hours from a selected session, or remove it. Stop a running timer before editing that session. Corrections update all charts, totals and exports. Overlapping sessions of the same activity and future times are rejected. Undo last correction is available in the panel and survives restarting PACT.
- Settings â†’ Backup and restore creates a `.pact` file for migration, including sessions, daily entries, Garmin history, goals and appearance. Choose a backup to preview counts, then explicitly replace local data. A restorable safety backup is written beside the database first. Replacement is transactional. Timers in a backup end at capture time, and restoring never starts them automatically. Credentials are excluded; reconnect Garmin on another device. Undo history is local to the installation and resets on restore. CSV/ZIP spreadsheet exports remain separate from migration backups.
- The most recent completed sleep remains visible after midnight, dated by its original Garmin record. Other daily values still belong to today, and historical charts/exports retain their actual dates.
- A small indicator beside the gear uses the active theme's ink color. It gently pulses when no cloud check is available, a check is over ten minutes old, watch data is over an hour old, or a sync fails. Click it for connection status and Sync now. Five-minute background checks continue. Unknown/future Garmin day-end timestamps are described as unavailable, not treated as proof of fresh data. Stale watch data requires the watch/phone to upload to Garmin Connect first.
- Installer maintenance ignores invalid paths reported for unrelated Windows processes, preserving safe shutdown of the installation being updated.
## Existing features

- Hover details use one flat, themed Newsreader panel inside PACT. It does not intercept mouse events, remains anchored while moving within a target, waits briefly before appearing and tolerates short gaps between targets. Native tooltips on ordinary controls are removed.
- Monthly details appear only over an actual nonzero bar. Unrecorded heatmap dates say Not available, rather than inventing zero-hour records. Sleep legends are labels only; stage details are available on the mosaic. Recorded data details retain dates, durations and creatives.
- Chart legends share aligned symbol/value columns, with bold italic hour values. Health data, including water and calories, uses consistent bold typography. Learning's return arrow points left.
- Settings persist automatically. Theme/color choices and committed target edits apply immediately; leaving Settings commits any pending numeric text. There is no Save button. Credentials are never saved by this mechanism.
- Hydration intake and goal come from Garmin's hydration endpoint. Cups of Water displays US cups (236.588 mL each), preserving raw milliliters in storage and exports. The manual water editor and water-goal setting are removed. Earlier manual entries remain stored and export separately as legacy_manual_water_cups; they are never passed off as Garmin readings. Missing hydration shows a dash; a failed hydration request leaves other Garmin metrics available and reports the issue.
- PACT checks Garmin every five minutes while running, including while hidden. Sync now checks immediately unless a request is already running. There is no 15-minute delay configured in PACT. The app can only read data already uploaded to Garmin Connect; it cannot trigger the watch's Bluetooth upload.

Garmin notes that hydration on compatible watches may require opening the hydration widget while Garmin Connect is open on the paired phone. See https://support.garmin.com/en-ZA/?faq=390puZ3AgO4hM3IzakFs99&productID=707538&tab=topics .

## Data, design and behavior

The supplied Work/Learning SVG artwork and geometry remain the static design source. Newsreader is bundled. Analytics use separate work/learning targets, initially 8 and 2 hours. The 360-cell heatmap displays rolling history; monthly charts cover 30 days. Annual totals count the current calendar year independently. Dark, High Contrast, Light and Custom themes remain available.

The database remains at `%LOCALAPPDATA%\PersonalOS\personalos.sqlite3`; Garmin tokens remain at `%USERPROFILE%\.garminconnect`. Existing records and backup behavior are preserved. The additive health_log table records fetched observations. No live user data or credentials are included in these deliverables.

Settings â†’ Data export offers a daily CSV or a ZIP of daily totals, hourly timers, raw sessions and Garmin observations. CSV imports into Excel or Google Sheets. Days run midnight to midnight locally. Sessions split at hour/day boundaries; open-session totals stop at export time. Missing health measurements stay blank. Historic snapshots that were never recorded cannot be reconstructed.

The panel fits the complete dashboard on available heights of at least 994 logical pixels and scrolls on smaller displays. It stays anchored right/bottom, without always-on-top. Escape closes Settings first, then hides PACT. The top arrow hides it. Hover in the top-right 9-pixel corner for 350 ms, use the tray or launch PACT again to reveal the same instance. Timers and five-minute cloud checks continue while hidden.

## Build

Extract PACT_v1.3.0_Package.zip for its runtime. In the source folder run:

```powershell
.\build.ps1 -RuntimeDirectory 'C:\path\to\runtime' -InnoCompiler 'C:\path\to\ISCC.exe'
```

Output is `dist\PACT_v1.3.0_Setup.exe`. Build tools: Inno Setup 6.7.3, the Windows .NET Framework compiler and bundled Python 3.12.10. Pinned dependencies and licenses are included. compile_designs.py regenerates current geometry; compile_assets.py is retained for the old design only. See PACT_Validation.md. The installer remains unsigned.
