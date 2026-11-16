# PR 30 archive and environment follow-up

2026-11-13 JST. Baseline remote df0748c1d70e0879061369d985d4aa70c4eefcb7,
tree 3248b8f6d96bc12d489ec504a56f277edcae0c9f. No runner/probe changes.
Old two TIMEOUT records, missing executed initial runner, missing pilot HEAD/tree,
quota independence UNKNOWN remain unchanged. Previous CI success is not browser success.

## Fixed archive

Original ZIP unchanged: 1,679,175 bytes; SHA-256
`47e7e14bad9964f6168142a579f2814c00816f9bfd940bcdcfb9d84756378bcc`.
543 ZIP entries include 542 manifest-covered files and manifest.json.
Independent CRC, 542 size/hash and path checks passed. Original 18 files remain
18/18, 1,163,952 bytes. Private evidence is not committed here.
Known token/key patterns found none; binary cache/Git pack complete semantic secret
analysis was not performed. The package must remain owner-private, not public.

## Archive channels are separate

Windows archive PENDING. Read-only check found no expansion of effective writable
roots; the approved archive path remains outside this executor's permission scope.
No transfer/write attempt, settings changes, privilege changes, or cleanup occurred.
Test-Path returned false in that execution context, not proof the host folder is absent.
Owner-private Space relay upload accepted the exact hash and size; separate metadata
read confirmed existence and size. This does not establish Windows disk preservation.
An updated verifier is supplied separately, preserving the original ZIP and old script.
External backup NOT_DONE. No claim of multi-copy archival resilience.

## Windows read-only environment survey

Windows registry build 26300.9974, DisplayVersion 26H2; ProductName reports Windows
10 Home. CIM OS lookup denied, so branding discrepancy is not resolved. PowerShell
7.6.9, Node v24.20.0, Python 3.14.7. Python Playwright distribution not found.
Existing Node playwright-core metadata versions 1.56.1, 1.58.2, 1.62.1; Chromium
file attributes 141.0.7390.37, 145.0.7632.6, 151.0.7922.34. No executable launched.
C: available 433,203,830,784 bytes at observation. TEMP/TMP use per-command app
sandbox directories. Browser cache exists in host LocalAppData, not virtualized
per-command LocalAppData. Presence does not prove permitted launch/access.

## New Chromium plan gate: NOT APPROVED, zero new launches

The final runner uses POSIX process groups, selectors, signals and statvfs. It is
Linux-specific. Do not silently run it on Windows, remove containment, or substitute
a mock. Current Windows inventory alone does not provide an approved compatible
runner. A Windows port or a formally permitted Linux execution environment is an
explicit unresolved prerequisite. Browser runtime and DOM remain BLOCKED/NOT_TESTED.

The next candidate plan must fix one environment, exact source HEAD/tree and
runner/probe hashes, installed Playwright/Chromium absolute paths and versions,
authorized new output/Temp root, capacity/inode and parent environment snapshot.
Use only existing binaries, no download or sandbox relaxation. One initial trial,
45-second parent deadline, bounded stdout/stderr and scan limits from runner;
fixed local HTML -> expected isolated-temp-42 -> browser close -> durable evidence.
On any failure stop, preserve raw errors/exit/signal, no retry. Only success permits
up to three total trials in fresh directories, if separately approved. Compare
actual generated files, parent environment and before/after storage, and report
observation boundaries. No browser invocation is authorized by this document.
A concrete command and final plan must be presented for separate owner approval
once the compatible environment and authorized output location are known.

## Safe manual archive procedure

Download the original ZIP and separately supplied `Verify-Archive-Safe.ps1` and
`verify_archive.py` to a new private local folder. Keep the two scripts adjacent.
The approved PR-30 parent folder must already exist. If it is genuinely absent,
create that folder manually in Explorer under the approved Dev-Artifact-Archive
location, without moving or overwriting anything. If it exists but access is denied
or sandbox visibility differs, stop; do not change ACLs or trust settings.
Open a new normal PowerShell process, then run (replace only the downloaded path):

```powershell
& .\Verify-Archive-Safe.ps1 -Package '.\Hachibei-Lab-PR30-private-transfer.zip'
```

Get-FileHash checks the original ZIP first. Python 3.14.7 already exists on the
surveyed PC; the wrapper invokes it without dependency installation. The verifier
rejects unsafe/duplicate paths, symlinks/reparse points, missing/extra members,
wrong sizes/hash and CRC; creates a fresh GUID directory under the approved PR-30
parent; saves the ZIP unchanged; and extracts with exclusive creates. A separate
Python process reads the saved ZIP and every file again. Only Windows completion
emits WINDOWS_ARCHIVE_PASS. Retain `windows-readback.json`; do not upload raw logs
or ZIP to public GitHub. If policy blocks script execution, stop and report the
error rather than change ExecutionPolicy. If any check fails, retain partial data
and BLOCKED result; do not overwrite/reuse the directory or delete it.

This is a fixed-package utility, not a hostile-concurrent-filesystem defense.
No untrusted process should modify the private destination during verification.
The wrapper and Windows file-system behavior are NOT_TESTED until owner execution.
Linux-only synthetic checks do not establish Windows success. External backup is
NOT_DONE, regardless of PC archive success.
