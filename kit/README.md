# DFIR Kit 0.2 — expanded engineering prototype

NOT a validated forensic product, malware scanner, full forensic acquisition system, or signed release. Use only with owner authorization. No finding attributes an attacker or establishes targeting. Original source evidence and independent review remain necessary.

## Quick start
Python 3.10+; core has no third-party Python dependencies.
```
python dfir_kit.py init ./case-001 --collector "Your name" --consent
python dfir_kit.py windows ./case-001
python dfir_kit.py import ./case-001 ./router.log ./account-export.json
python dfir_kit.py analyze ./case-001 ./templates/events.csv
python dfir_kit.py verify ./case-001
```
Run Windows collection only on Windows. Some commands require administrator rights and enabled auditing; failures go in journal.jsonl. Windows/ADB commands have NOT been tested on physical devices here. Collections are live, invasive to a limited degree, and may be affected by a compromised OS. Never run on someone else's equipment without permission. Do not install Python onto a suspect device solely for collection if preservation is critical.

## Android
```
python dfir_kit.py android ./case-001 --serial SERIAL
```
Optional --bugreport collects much more sensitive data. Requires separately installed, reviewed ADB and explicit device authorization. Does not root, bypass locks, unlock a bootloader, or perform a full filesystem acquisition. See docs/WORKFLOWS.md.

## Provider APIs
```
python dfir_kit.py api ./case-001 --provider entra --consent
python dfir_kit.py api ./case-001 --provider workspace --application login --consent
```
Supply a short-lived authorized bearer token through DFIR_ACCESS_TOKEN in the process environment. Tokens are not written by the kit. Acquire tokens using your organization's approved OAuth client; this kit DOES NOT implement OAuth login, refresh, or secure token storage. Clear the variable afterwards. Do not paste tokens into chat or command-line arguments. Entra endpoint is tenant sign-ins; Workspace supports login/admin/token/drive activity endpoints. Licensing, account type, roles, scopes, retention and tenant policies determine access. Personal Gmail/Outlook do not automatically expose enterprise audit APIs. No bypass is attempted. Raw paginated responses are preserved. These adapters are implemented but NOT live-tested or complete account coverage. Directory audits/mailbox rules are not collected by this release.

## Timeline and findings
Use templates/events.csv. Explicit source mapping is required: native EVTX/JSON/syslog are preserved but not automatically converted into the canonical CSV. Windows exports include a bounded Security event XML view (latest 5,000 matching events), not a complete parser. Normalization preserves original timestamps, timezone gaps, unknown uncertainty and clock-offset metadata. Clock offsets are NOT automatically applied. Two candidate rules (1102, 4697) flag review only. They are NOT externally reviewed or validated detections. No AI-compromise score or attribution. Tests establish software behavior, not field accuracy.

## Protected storage
Use an encrypted destination volume and controlled access BEFORE collecting. POSIX case directories get mode 0700; Windows ACL hardening is manual and not verified by this kit. Review inherited ACLs and use a dedicated evidence account/volume. No administrator can be prevented from changing local files by hashes alone.

To encrypt an already prepared archive, separately install and verify age:
```
python dfir_kit.py crypto encrypt --input case.tar --output case.tar.age --recipient AGE_PUBLIC_RECIPIENT
```
The kit does not create the archive, delete plaintext, manage keys or verify decryption. Test recovery separately; keep private keys off the suspect machine. Encryption after collection does not protect earlier plaintext copies.

To sign a manifest using an existing RSA signing key (OpenSSL installed):
```
python dfir_kit.py crypto sign --input case-001/manifest.json --key private.pem --signature manifest.sig
python dfir_kit.py crypto verify-signature --input case-001/manifest.json --key public.pem --signature manifest.sig
```
Protect the signing key separately. Export the manifest and detached signature to independently controlled storage after every collection. Signatures establish continuity under a trusted key, not original-source truth. This package itself is NOT signed.

## Integrity behavior
Normal collection checks the last local manifest before writing. Each collection regenerates the current manifest; preserve signed external snapshots to retain historical checkpoints. `seal` explicitly creates a fresh baseline without checking the old one: do not use it to hide an unexplained mismatch. Concurrent collectors are unsupported. Exclude active case directories from automated modifications. Raw output may contain secrets, names, network details, and command-line tokens: do not publish it.

## Tests / distribution
```
python -m unittest discover -s tests -v
python build_release.py
```
Build script creates a deterministic ZIP for identical source bytes under the same Python runtime, using fixed ZIP timestamps and stored entries. Cross-platform reproducibility is NOT established. No dependencies are automatically downloaded. External binaries are NOT bundled or trusted by default. Record exact versions, source and hashes before use. See docs/WORKFLOWS.md for acquisition, audio, router/ISP, validation and release gates.
