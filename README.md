# DFIR Workbench 0.1

Local desktop wrapper for the DFIR Kit 0.2 command-line toolkit supplied earlier.

## Important: backend not bundled
This ZIP contains the GUI, not a fresh copy of the previous DFIR toolkit. Extract your earlier DFIR Kit 0.2 ZIP and select its `dfir_kit.py` using the Toolkit script Browse button. Alternatively place that script beside `dfir_workbench.py`. The GUI runs the selected Python script: review and trust that source first.

## Start
Python 3.10+ with Tkinter required. No pip packages or web server needed.

Windows: double-click START-WINDOWS.bat, or run `python dfir_workbench.py`.
macOS/Linux: run `python3 dfir_workbench.py`. Install Tk through your operating system/Python distribution if unavailable. `python -m tkinter` (or python3) is a manual Tk availability check that opens a test window.

## Workflow
1. Select your toolkit script.
2. Case tab: enter collector, check authorization, choose a NEW case path, then Initialize case. For existing cases use Active case Browse.
3. Collection: Windows inventory/log export or authorized Android ADB collection. List ADB devices shows devices in the live log; copy the desired serial into its field. No rooting or authorization bypass.
4. Account APIs: select Entra or Workspace. Workspace report dropdown and user field enable only for Workspace. Supply DFIR_ACCESS_TOKEN in the process environment before starting the GUI. OAuth login and token acquisition are NOT included. Enterprise roles/scopes/licensing apply. No automatic consumer Gmail/Outlook coverage.
5. Import & timeline: add/remove files, import the list, select canonical CSV, analyze, and view JSON output. Native exports are NOT automatically converted into timeline CSV.
6. Protection: age encryption of an existing archive, OpenSSL signing, or signature verification. Only fields relevant to the operation are used. External tools required. Passphrase-interactive keys are not supported through the GUI: use a trusted terminal. The GUI must not prompt you to remove key encryption.
7. Verify case integrity and export session log if needed. Full evidence records remain in the case; GUI output is bounded/truncated.

## UI behavior
Dark interface, native resizable desktop window, grouped tabs, tooltips, hover feedback, animated indeterminate progress, Reduce motion menu item, contextual dropdowns, validation dialogs, live output and explicit operation status. No invented completion percentages. Operations run in a background process so the UI remains responsive. One operation at a time. Buttons dispatch real toolkit commands, not simulated findings.

Case menu: select toolkit/open case/create case/open folder/exit.
Tools menu: prerequisites, verification, session-log export.
View menu: Reduce motion.
Help menu: limits and version information.

## Operational limitations
- Not a production-certified forensic product. This wrapper does not add missing backend acquisition, router, audio or analysis functionality.
- Desktop rendering, ADB, Windows, provider API and crypto integrations were NOT exercised on real target systems in the build environment.
- Running the toolkit with administrator privileges can help access Windows logs but increases script privileges. Elevation is never requested automatically.
- Stop terminates only the immediate toolkit process. Descendant acquisition processes may continue. Partial cases/manifests need review. Stop cannot safely undo changes.
- No automatic manifest resealing or silent integrity repair.
- Backend exit 0 does not guarantee every individual collector succeeded: inspect journal.jsonl.
- No shell execution. The selected backend remains arbitrary Python code you must trust.
- Token is inherited from the environment, not displayed or saved intentionally by the GUI. Case records/backend output may still contain sensitive information; review before sharing.
- Public recipient and key FILE PATHS appear in session logs, not key contents. Command output is not guaranteed secret-free.
- GUI settings are not persisted; choose paths again next launch.
- Backend and source can be modified locally; this distribution is unsigned.

## Tests
`python -m unittest discover -s tests -v`
Included tests are headless validation tests, not full UI automation. See TEST-RESULTS.txt. Visual and platform acceptance still required.
