# PACT v1.9.0

Run PACT_v1.9.0_Setup.exe to install or update on Windows 10/11 x64. The private runtime is included. Start Menu, Installed Apps, optional desktop/startup shortcuts and updater process management are preserved.

## New in v1.9.0

- Enable the optional floating widget in Settings > Desktop widget or from the tray's Show / hide widget action. Select Work, Learning, sleep score, steps, meals and creatives. It reads the same local data and uses the same theme as PACT, refreshing each second without another Garmin connection.
- Drag its header to position it; right-click to lock, hide or open settings. Size (70–150%) and opacity (40–100%) save automatically. It stays visible when the sidebar is hidden, opens PACT on click, and is not always on top. No Rainmeter dependency is required. It starts disabled; once enabled it returns on subsequent launches.
- Widget preferences are included in full backups. Its position is clamped to an available screen if a monitor is removed or the layout changes. Missing values stay unavailable; the sleep row labels the date when showing a prior night's record.
- The Learning slide replaces page turning with writing that gradually appears across a stationary open book. There is no turning sheet or final shape replacement.
- The existing PDF/named-PNG exports, six-by-five 30-day consistency layout and explicit eaten/skipped/unrecorded meal counts are retained.

## Fixed in v1.8.2

- The Learning page turn now settles into the resting illustration without a final-frame swap. Its moving sheet uses the same curves as the static page, brings writing in gradually, and blends into place. The 3.4-second ease-out and report exports remain intact.
- A rendered regression test compares the last two frames at 30 fps in light, dark and custom colors, and separately verifies that the page still moves during the animation.

## New in v1.8.1

- A visible export selector offers one PDF report or PNG slides in a ZIP. Images are grouped in a dated folder and named Slide 01 - Overview, Slide 02 - Work, and so on.
- Learning has its own unfolding-book animation, distinct from Work's rising daily bars.
- Thirty-day consistency grids use six columns and five rows. Other periods keep every real date and center any shorter final row; no extra dates are invented.
- Meals now label eaten, explicitly skipped, and unrecorded totals separately. Previously the headline counted Yes entries while the footer counted both Yes and No entries, which was confusing. Breakfast/lunch/dinner counts and the headline still count only eaten meals.

## New in v1.8.0

- Wrapped graphics and counters animate for 3.4 seconds after each 650 ms slide transition, easing out gradually. Orbit, rising bars, sun rays, softly pulsing goal grid, drawing motif, place setting, moon and stars each have a distinct treatment. All use your theme colors. Tiny outlined bars no longer leave a stray dot on the baseline.
- Export report saves all eight final slides as a PDF or a ZIP of high-resolution PNG images, ready to share. Exports include the period and edited/imported disclosure, with no credentials or private session details. These are still images/pages; animations play in PACT.
- Report selectors and navigation controls share equal heights and aligned columns. Settings and time-editor input heights are consistent, including hours and minutes.

## New in v1.7.0

- PACT Wrapped replaces the scrolling recap with eight animated slides: overview, work, busiest work day, learning, work-goal consistency, creatives, meals and sleep. Each uses Newsreader, theme colors and its own vector graphic.
- Monthly is the default. The current month is explicitly marked so far; completed months and completed Monday-Sunday weeks are selectable. Missing values show an empty state, not invented achievements. Goals use current targets and edited/imported data remains identified.
- Previous/Next, eight progress segments and left/right keys navigate slides. Optional Play advances every 5.5 seconds, stops after the last slide, and pauses when hidden. Transitions last 650 ms. Space toggles playback.
- Monthly and weekly notification preferences are separate. Notifications open the corresponding completed period. Delivery still depends on PACT running and Windows notification settings.

## New in v1.6.0

- Settings > Appearance > Width is a live 0–100 slider: 0 is the original layout for the monitor; 100 is the enlarged v1.4–v1.5 layout. Intermediate widths interpolate between those endpoints, resize immediately, save automatically and survive full backup/restore. Settings text also scales gradually. The existing readability checkbox switches between original and the remembered enlarged width. Screen bounds and docking remain respected.
- Open weekly review from Settings or the tray menu. It reviews completed Monday–Sunday weeks and supports browsing earlier weeks. Work/Learning totals, busiest recorded days, current-goal days/streaks, previous-week comparisons, creatives, meals, average sleep and daily details are computed from stored data. Coverage counts identify missing records; goal calculations use current targets. Edits/imports are identified and corrections automatically update the review.
- While PACT runs, it checks for a newly completed week at startup and hourly. If that week contains recorded data, one Windows notification announces the review; click it to open. The preference can be disabled in Settings. Windows notification settings may suppress delivery. If PACT was closed at the week boundary, the latest completed week is checked when it next runs. No email, account or external reporting service is involved.

## Fixed in v1.5.1

- Edit data uses the original Meals row with three outlined, theme-colored toggle boxes (breakfast, lunch, dinner). Filled means Yes; empty means not selected. Changes still save and enter history automatically.
- Edit history groups entries by the date being edited, newest dates first, with bold headings and a divider between dates. Each entry retains its actual edit timestamp.

## New in v1.5.0

- Settings now has Settings, Edit data and Edit history tabs. Edit data includes dated meals/creatives and the full Work/Learning time editor. Dashboard shortcuts remain available.
- Meals support Not entered, No and Yes; creatives support Not entered or a count. Entries save automatically. Undo last daily edit restores the previous value and records the undo. Earlier zero values without a recorded status appear as Not entered in this editor; nonzero legacy values remain available. Garmin measurements are read-only.
- Edit history shows each manual entry/correction, before and after values, its date and when the change was made. Time add/edit/deduct/remove and undo are included, including dashboard shortcuts. Existing retained time correction logs migrate once; earlier unlogged changes cannot be reconstructed. This is a local history, not tamper-proof certification.
- Full backups retain history and recording status. All-records exports include edit_history.csv; daily exports include edited/edit_count and blank unentered manual fields. CSV restores log an import and retain whether a daily field was blank, but cannot reconstruct original audit history. Chart hover details identify dates with edits/imports. Reset progress clears local history after its existing confirmation and safety backup.

## New in v1.4.0

- Click the Work or Learning time, choose Add time, a date/start time, and an amount in hours/minutes. PACT calculates the end time. Edit exact start / end remains available for individual sessions.
- Deduct time now works directly on the selected day's total without selecting a session. It removes the latest recorded time first, then imported CSV totals if needed. It can span multiple sessions or remove the whole total. Undo restores the entire correction in one action. Deductions never alter adjacent days, even for sessions crossing midnight. Stop a running timer before deducting from that day; excessive deductions are rejected without changing records.
- Auto-adjust for readability now makes the dashboard approximately 60% larger than the default (at least 560 logical pixels wide, capped by available screen width). It uses vertical scrolling, larger Settings/hover text and stronger live text/control weights. Turning it off restores the existing layout. Full screen bounds and Windows scaling remain respected.

## Fixed in v1.3.1

- Auto-adjust for readability now has a full outlined row and a large, high-contrast checkbox. Empty means off; filled means on. Its borders and fill follow the current theme.

## New in v1.3.0

- The existing dashboard sizing remains the default. Settings → Appearance → Auto-adjust for readability enlarges the entire dashboard proportionally, including Newsreader text, icons and charts, using the monitor's available space. Smaller screens scroll vertically when needed. Turning it off restores the original sizing.
- The adjustment saves immediately, follows monitor/work-area/DPI changes, and is included in full backups. Windows DPI scaling is respected. Right/bottom docking and non-always-on-top behavior are unchanged.
- A one-time display-options message appears when PACT is first shown. Open Settings takes you directly to the panel; Got it dismisses it. Hidden startup does not show the message. Existing installations see it once after this update too.

## New in v1.2.0

- Settings Ã¢â€ ’ Backup and restore Ã¢â€ ’ Reset progress asks for explicit confirmation, defaulting to Cancel. It clears timers, daily entries, imported totals, health history and correction history while preserving goals, theme and Garmin connection. A `.pact` recovery backup is created first; if that fails, reset is cancelled. Running timers stop. Automatic Garmin backfill excludes dates before the reset day; today's readings may return on sync. Existing backup/export files are not deleted.
- Import daily totals (.csv) accepts PACT's exported daily CSV, including `daily.csv` extracted from an all-records ZIP. A preview shows date range and new/skipped counts. Existing dates with progress are skipped, so repeated imports do not double totals or overwrite records. A safety backup precedes the transactional import.
- CSV restores the daily Work/Learning totals, creatives, meals and health values present in the file. It cannot restore original session times, hourly distribution, observation history or appearance/goals that were not exported. Imported time is stored as daily totals, not fabricated sessions. It appears in analytics and daily exports, survives `.pact` backups, and is listed separately as `imported_daily_totals.csv` in full ZIP exports; unknown hourly values remain blank. Use `.pact` for complete migration. Older `.pact` backups remain supported.
## Fixed in v1.1.1

- Sync and chart hover messages wrap within the sidebar, including after resizing.
- The analytics divider remains stationary and single during both slide directions, including high-DPI displays.

## New in v1.1.0

- Click the Work or Learning time to add missed sessions, correct dates/start/end times, deduct hours from a selected session, or remove it. Stop a running timer before editing that session. Corrections update all charts, totals and exports. Overlapping sessions of the same activity and future times are rejected. Undo last correction is available in the panel and survives restarting PACT.
- Settings Ã¢â€ ’ Backup and restore creates a `.pact` file for migration, including sessions, daily entries, Garmin history, goals and appearance. Choose a backup to preview counts, then explicitly replace local data. A restorable safety backup is written beside the database first. Replacement is transactional. Timers in a backup end at capture time, and restoring never starts them automatically. Credentials are excluded; reconnect Garmin on another device. Undo history is local to the installation and resets on restore. CSV/ZIP spreadsheet exports remain separate from migration backups.
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

Settings Ã¢â€ ’ Data export offers a daily CSV or a ZIP of daily totals, hourly timers, raw sessions and Garmin observations. CSV imports into Excel or Google Sheets. Days run midnight to midnight locally. Sessions split at hour/day boundaries; open-session totals stop at export time. Missing health measurements stay blank. Historic snapshots that were never recorded cannot be reconstructed.

The panel fits the complete dashboard on available heights of at least 994 logical pixels and scrolls on smaller displays. It stays anchored right/bottom, without always-on-top. Escape closes Settings first, then hides PACT. The top arrow hides it. Hover in the top-right 9-pixel corner for 350 ms, use the tray or launch PACT again to reveal the same instance. Timers and five-minute cloud checks continue while hidden.

## Build

Extract PACT_v1.7.0_Package.zip for its runtime. In the source folder run:

```powershell
.\build.ps1 -RuntimeDirectory 'C:\path\to\runtime' -InnoCompiler 'C:\path\to\ISCC.exe'
```

Output is `dist\PACT_v1.7.0_Setup.exe`. Build tools: Inno Setup 6.7.3, the Windows .NET Framework compiler and bundled Python 3.12.10. Pinned dependencies and licenses are included. compile_designs.py regenerates current geometry; compile_assets.py is retained for the old design only. See PACT_Validation.md. The installer remains unsigned.
