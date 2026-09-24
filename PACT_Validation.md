# PACT v1.1.0 validation

Windows x64, 24 September 2026.

37 Python automated tests passed, including 11 new v1.1 tests. Five installer path cases passed separately.

- Add, deduct, edit, remove and undo Work/Learning sessions; totals, annual/weekly history and CSV data agree after changes. Cross-midnight sessions split correctly. Overlaps, future/invalid times and active-session edits are rejected. Undo persists across restart and refuses conflicting changes.
- Backup/restore preserves sessions, daily entries, health observations, goals and themes. Credentials are excluded. Timers continue on the original device but are stopped at capture time in the restored copy. Restorable safety backups are created before replacement. Invalid formats, versions, timestamps, goals and sleep stages are rejected before data replacement. Settings UI does not overwrite restored goals.
- Latest sleep retains its original date after midnight and switches when a new valid sleep record arrives. Historical data remains attributed to its actual day.
- Freshness states distinguish fresh, stale, overdue, missing, failed and in-progress checks. Future Garmin day-end boundaries do not imply fresh watch data. Indicator uses theme ink and avoids native tooltips.
- Existing 26 timer, health mapping, UI, export, docking, animation, autosave and hover tests pass. The sleep-gap fixture now supplies a dated sleep duration as well as stages.

Visual inspection: Light dashboard, Dark time editor and Settings; editor and backup controls checked at 320-pixel width. Sleep date and theme-matched dot preserve dashboard geometry. The indicator was rendered across all four themes in automated UI tests.

Installer testing found that a Windows process with an invalid path could block the old installer. Maintenance now ignores invalid unrelated process paths and retains exact installation-folder matching. Five cases cover installation executable/runtime, a similarly named sibling folder, null and malformed paths.

The v1.1.0 installer successfully updates a running isolated v1.0.0 app package, shuts down the correct instance, preserves database/targets/token sentinel, supports single-instance reveal, and uninstalls without removing data. The baseline app files were extracted from the released v1.0.0 package because the original v1.0.0 installer encountered the process-path bug on this machine. A separate fresh v1.1.0 install, installed startup self-test and uninstall all passed.

Tests used isolated synthetic data and did not replace the user's installed app. No new live watch upload or Garmin login/MFA test was performed for this release. Watch/phone cloud-upload latency remains outside PACT's control. Installer is unsigned. Migration backups replace local data rather than merge; old spreadsheet CSV/ZIP exports are not migration backups. Undo history remains local and resets on restore.
