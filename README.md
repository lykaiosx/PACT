# PACT v1

Run PACT_v1_Setup.exe to install or update on Windows 10/11 x64. The private runtime is included. Start Menu, Installed Apps, optional desktop/startup shortcuts and updater process management are preserved.

## This update

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

Settings → Data export offers a daily CSV or a ZIP of daily totals, hourly timers, raw sessions and Garmin observations. CSV imports into Excel or Google Sheets. Days run midnight to midnight locally. Sessions split at hour/day boundaries; open-session totals stop at export time. Missing health measurements stay blank. Historic snapshots that were never recorded cannot be reconstructed.

The panel fits the complete dashboard on available heights of at least 994 logical pixels and scrolls on smaller displays. It stays anchored right/bottom, without always-on-top. Escape closes Settings first, then hides PACT. The top arrow hides it. Hover in the top-right 9-pixel corner for 350 ms, use the tray or launch PACT again to reveal the same instance. Timers and five-minute cloud checks continue while hidden.

## Build

Extract PACT_v1_Package.zip for its runtime. In the source folder run:

```powershell
.\build.ps1 -RuntimeDirectory 'C:\path\to\runtime' -InnoCompiler 'C:\path\to\ISCC.exe'
```

Output is `dist\PACT_v1_Setup.exe`. Build tools: Inno Setup 6.7.3, the Windows .NET Framework compiler and bundled Python 3.12.10. Pinned dependencies and licenses are included. compile_designs.py regenerates current geometry; compile_assets.py is retained for the old design only. See PACT_Validation.md. The installer remains unsigned.


