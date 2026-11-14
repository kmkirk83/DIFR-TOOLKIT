# DFIR Workbench — combined source distribution

GUI 0.1 + DFIR Kit 0.2. Both uploaded source files are included together. GUI launches the bundled backend automatically; no toolkit browsing required. Duplicate dfir_workbench-1.py was omitted after byte comparison.

## Start
Extract the ENTIRE ZIP first. Python 3.10+ with Tkinter required. No pip dependencies for core functions.
Windows: double-click START-WINDOWS.bat or run `python dfir_workbench.py`.
macOS/Linux: run `python3 dfir_workbench.py` (or `sh START-UNIX.sh`).
If Python/Tk is absent, install it through your trusted OS/Python distribution; this package does not download software.

## Workflow
Case tab: enter collector, choose a NEW case directory, check authorization, Initialize case.
Collection tab: Windows inventory/logs or explicitly authorized Android ADB triage.
Account APIs: Entra or Workspace adapters; authorized short-lived DFIR_ACCESS_TOKEN must be present in the app's environment before launch. No built-in OAuth login, no assumed personal Gmail/Outlook audit access.
Import & timeline: add evidence files, import, select canonical events CSV, analyze, view JSON. Use templates/events.csv. Arbitrary native exports are NOT automatically mapped.
Protection: external age encryption of a prepared archive or OpenSSL signatures. No archive creation, key management, plaintext deletion or interactive passphrase support in GUI. Use a trusted terminal for protected keys.
Tools menu: prerequisite checks, integrity verification and visible-session-log export. View menu: Reduce motion.

## Improvements in this bundle
Backend and GUI colocated with automatic discovery; backend execution uses unbuffered Python for live output. Sources, launcher scripts, templates and reproducible integration tests are packaged together. Backend source is unchanged from the upload. GUI source changes only add Python's -u flag to backend invocations.

## Safety and boundaries
Use only with ownership/authorization. Live collection changes a system. A compromised source may supply misleading information. Findings are review prompts, not intrusion verdicts. Exit 0 does not guarantee every collector succeeded: review journal.jsonl.
Store evidence on a protected volume; logs may contain secrets. POSIX directory restriction exists; Windows ACL configuration is manual. Keep signed manifest snapshots independently. Hashes alone do not establish authenticity or custody. Never use seal to erase unexplained integrity discrepancies.
Stop only terminates the immediate process; child collectors may continue and partial evidence may remain. Concurrent operations against a case are unsupported. GUI logs are truncated; original case records are primary.
External dependencies are not bundled: ADB, age and OpenSSL. No disk imaging, memory capture, voice-cloning classification, vendor router controls or specialist forensic acquisition is added by this bundle. No maliciousness determination or attacker attribution is automated.
This is an unsigned source prototype, not an independently validated forensic suite or a standalone executable installer.

## Tests
`python -m unittest discover -s tests -v`
Includes source compilation, all CLI subcommand help interfaces, authorization enforcement, initialization/import/analysis/verification lifecycle, deliberate tampering detection and GUI/backend colocation. TEST-RESULTS.txt records actual execution. Desktop GUI rendering, physical Windows/Android collection, live APIs and external crypto tools have not been validated in this build environment (Tk not installed).

## Integrity
SHA256SUMS.json records bundled file hashes (excluding itself). It is an unsigned local integrity inventory, not publisher authentication. Preserve a trusted copy separately.
