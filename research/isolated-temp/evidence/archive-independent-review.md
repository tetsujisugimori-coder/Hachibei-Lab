# Independent archive review 2026-11-13 JST

Baseline df0748c; additive archive verifier scope only. Existing runner/probe unchanged.
Reviewed Python SHA256 67e2a84ddb2e0f7eae4ec11cc6435664f9ba039648d32d12a956f264b3f8514f,
PowerShell fc65eadcd8e091cf2156e771a7911b0b7580ada90eb8c0e4f7baa7a811e1b64e,
tests e774d2905084a88e2a3041d6992dcefa2c8bf45648b040bc98abee4216cd88d8.

Separate reviewer read actual code and fixed original ZIP; 11 unit tests passed.
Independent fresh-save and separate-process readback passed as NON_WINDOWS_READBACK_PASS
(parent PID 8, readback PID 9 in that execution). Six independent negative cases:
size mutation, same-size byte mutation, missing file, added file, symlink, existing
destination reuse all rejected exit 2. Original ZIP SHA unchanged. 542 manifest files
plus manifest itself, CRC and original18 inventory checked. One documentation gap was identified: archive parent must exist. The manual
procedure now explicitly requires the parent and distinguishes genuine absence
from sandbox visibility/access denial. No code false PASS was found.

Limited fixed-package code/evidence PASS, not Windows acceptance. PowerShell and
Windows runtime NOT_TESTED; hostile concurrent filesystem races out of scope.
No Chromium launched. Public report excludes raw private records. Windows PENDING,
external backup NOT_DONE, overall PARTIAL and merge NO remain.
