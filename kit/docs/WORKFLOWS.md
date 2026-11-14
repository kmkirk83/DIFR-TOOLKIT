# Specialist workflows and release gates

## Windows file acquisition
Use `import` for individual accessible files; it is a logical copy, not a filesystem/disk image. Capture hashes before and after copying, source timestamps and collection actions. Do not mistake a matching hash for trustworthy source data. Accessing files can alter source metadata; locked, deleted and alternate-stream data are not comprehensively acquired. Use a qualified examiner for media acquisition.

## Disk/memory acquisition
1. Obtain written scope and device identifiers; preserve active incidents without delaying isolation.
2. Choose an acquisition tool and exact version based on supported media/OS and published testing, not brand alone. NIST CFTT/CFReDS can inform selection and test fixtures.
3. Record tool binary hash, operator, start/end UTC, timezone/clock state and media identity. For disk, select appropriate write blocking and evidence destination; document deviations.
4. For memory, use a compatible, authorized signed capture tool. Memory acquisition changes memory and can crash systems; specialist review required.
5. Acquire into an appropriately protected destination; independently verify output with the acquisition tool and an independent method where applicable. Preserve errors, logs and verification results.
6. Import acquisition reports and manifests; do not try to import a huge image just to duplicate it through this prototype. Record externally stored image identifiers and hashes in the custody form.
This kit deliberately DOES NOT launch disk-imaging or memory-driver commands. No acquisition workflow has been independently validated by this release.

## Android compatibility and specialist acquisition
Maintain a test matrix by model, Android build, security patch, ADB version and authorization state. Verify available commands against known fixtures. Never unlock the bootloader as a DIY preservation step. Bugreports are diagnostic snapshots, not complete device images. Escalate locked devices, filesystem extraction and spyware investigation to qualified specialists. The included matrix is blank: no physical-device certification is claimed.

## Router/ISP adapters
Import original config exports, syslog and support responses; no universal login or vendor parser is supplied. Record router model/build and export method. Request ISP WAN outages, traffic-volume windows, relevant public IP assignment and retention deadlines. Obtain written preservation requests through appropriate channels where required. Do not access neighbors' networks. Vendor-specific live integration and ISP cooperation remain deployment work, not something software can guarantee.

## Voice examination
Preserve original audio/message/container; record independent speaker verification and each transfer. Work on copies. Ask a qualified examiner to evaluate codec/transcoding history, editing, channel artifacts and available reference samples. Request methods, limitations and uncertainty in writing. There is no supplied AI voice detector and no reliable conclusion from a familiar-sounding voice alone.

## Detection quality
Included candidate rules flag Security 1102 and 4697 as review-required observations. Legitimate maintenance and software installation are explicit alternatives. Build labeled benign and malicious fixture sets, preserve expected outputs, track false positives/negatives by rule/version, and have an independent reviewer approve before production. No external review or real-world sensitivity/specificity estimate exists for this release.

## Production release gates
- Threat model, code review, supported-platform matrix and signed artifact provenance.
- Known-answer testing with documented source datasets and negative controls.
- Live Windows, Android and provider sandbox testing; partial-failure and rate-limit tests.
- Pinned external binaries/dependencies and reviewed provenance; no auto-updates during acquisition.
- Key management, Windows ACL testing, encrypted-at-rest collection, restore tests, and independently retained signed checkpoints.
- Validated source-specific parsers with provenance and clock uncertainty.
- Network/vendor integrations tested against supported firmware, not guessed credentials.
- Repeat builds in isolated environments with byte-for-byte comparison.
- Independently publish signing-key fingerprint through a trusted channel. Signing a release locally is not publisher authentication without that trust channel.

## Public guidance consulted
NIST Digital Forensics: https://www.nist.gov/itl/ai/digital-forensics
NIST Digital Evidence Preservation: https://www.nist.gov/itl/csd/secure-systems-and-applications/computer-forensics-tool-testing-program-cftt/digital
Microsoft Entra audit overview: https://learn.microsoft.com/en-us/graph/api/resources/azure-ad-auditlog-overview
Android log availability limitations: https://securitylab.amnesty.org/latest/2026/05/android-intrusion-logging-as-a-new-source-of-data-for-consensual-forensic-analysis/
