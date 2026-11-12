# PR #30 follow-up: bounded runner and evidence preservation

Baseline remote HEAD `106fefeabf7239f05a0a4adb23d29d3ab428487f`, tree `fb6722f252b8026935ce4a99fde024cd176ffeab`.
Local prior commit d965693 had the same tree as remote 53e5392, but different ancestry. A non-destructive merge brought in the remote review document only. No reset, original deletion or main modification.

## Historical evidence (not overwritten)
18 original files (pilot 8 + trial 10), total 1,163,952 bytes: all size and SHA-256 comparisons matched the original ledger in a new Python process. Original pilot HEAD/tree remain missing. The actual initially executed runner revision was not found; the available submitted script is the later corrected revision, not a reconstructed original. Historical browser trial remains BLOCKED, DOM NOT_TESTED.

## Windows archive
2026-11-12 19:47:08 UTC: connected Windows environment had effective read-only access. Archive parent existed, PR-30 destination did not. Free C: 434,601,017,344 bytes. No write, privilege or settings change attempted. Windows permanent storage PENDING, external backup UNKNOWN. Private transfer ZIP with per-file hashes and PowerShell instructions is pending preparation separately; public repository does not contain raw originals.

## Scope
Only this opt-in research fixture. PR #22 remains separate, no wholesale integration or rollout. Subprocess-owned process groups, no global process killing. Escaped/daemonized descendants and global host state remain UNKNOWN. Per-project quota independence remains UNKNOWN. Shared /tmp data is not deleted/moved; parent environment is not changed. No dependency install, browser download, sandbox disabling or other project operation.

## Final verification
Results, fixed file hashes and CI are recorded in the follow-up comment and evidence files. Synthetic subprocess tests are not browser acceptance. A single final Chromium trial is authorized; stop on failure. Historical evidence is retained independently of this trial.

## Resume verification (2026-11-12 21:11 UTC)
The previous independent run preserved 2 failures among 33 tests: `test_normal` and `test_save_conflict`. Both raw records show TIMEOUT before probe generation; in the second, collision injection never occurred. This was not a false PASS, and the timing cause remains UNKNOWN. No deadline or expectation was relaxed. A new attempt passed all 33 tests (1.481s); a separate reviewer passed all 33 and 7 independent real-subprocess cases. Old failures remain in the private package.

The original P2 (result.json remained PASS after readback failure) is addressed by a provisional PENDING report and a hash-bound completion receipt. Readback/receipt failures return BLOCKED and consumers reject incomplete evidence. Production consumers must use `read_completion`, not infer acceptance from a partial JSON.

Final executable HEAD 5c428a0ab131827d01e4234902a56091c6fc46e8, tree 9c064973849ae894aa0fcd5351bdc1e47a1e5b9a. Independent code review is limited PASS; browser and archive acceptance are separate.

Exactly one final Chromium attempt at 21:11:41 UTC returned runner/Node exit 2. Chromium reported socket EPERM and SIGABRT; DOM NOT_TESTED, browser BLOCKED. The sandbox remained enabled; no retry/download/permission change occurred. This does not identify the underlying permission failure. A 17-byte probe and six Node cache files were observed in the dedicated Temp. Parent environment remained unchanged. Shared /tmp free bytes/inodes were unchanged across the snapshots; this does not prove zero transient use. The residual check reported OWNED_GROUP_ABSENT within the current PID namespace; escaped descendants and host-wide state remain UNKNOWN.

33 synthetic tests and 29 previous Stage1 regression tests are distinct from real-browser acceptance. Initial executed runner/probe version remains MISSING; the submitted later revision must not be relabelled as the original. Windows transfer and external backup remain separate pending/unknown outcomes. No public raw records are committed.
