# Shared temporary storage Stage 1

[Emergency report and ledgers](REPORT.md) for [Issue #27](https://github.com/tetsujisugimori-coder/Hachibei-Lab/issues/27), related [Issue #20](https://github.com/tetsujisugimori-coder/Hachibei-Lab/issues/20).

Linux / Python 3.11+, standard library only. Explicit opt-in, metadata read-only, stdout JSON. No subprocess, network, remediation, filesystem creation/deletion/move/compression, process stopping, or environment changes. Invoke Python with -B to prevent bytecode caches.

## Commands

    python -B research/shared-temp-stage1/tools/diagnose.py snapshot --path /tmp --path /workspace
    python -B research/shared-temp-stage1/tools/diagnose.py snapshot --path /tmp --scan-root /tmp --max-entries 20000 --max-seconds 5 --max-depth 5
    python -B research/shared-temp-stage1/tools/diagnose.py compare first.json second.json
    python -B -m unittest discover -s research/shared-temp-stage1/tests -v

Do not loop when startup fails. Store stdout only in an approved private location. Output is PRIVATE_REVIEW_REQUIRED, never automatically public. It includes paths, mount roots, owners and timestamps. It excludes file bodies, command lines, environment values, credentials, raw boot IDs and overlay source/upperdir options. compare reads only the explicit snapshot inputs, maximum 1 MiB each.

Capacity output includes UTC/JST start/end, total/free/available bytes and inodes, mount identity, environment hash and exit/error metadata. It does not establish provider quota, persistence, CPU/memory/process limits or causes. Zero inode capacity means inode percentage UNKNOWN, not exhaustion.

Optional scan: defaults 20,000 entries / 5 seconds / depth 5 / top20. CLI bounds: 100,000 entries, 30 seconds, depth20, top100; at most 16 capacity paths and four scan roots. Symlinks and nested mounts, including same-device bind mounts, are excluded. Directory opens use no-follow FDs; unique device/inode pairs deduplicate hardlinks, assigning the first observed group. Directories count their inode sizes; the root inode is excluded. Allocated and logical sizes differ. Incomplete totals are lower bounds, not whole-volume rankings. No deletion eligibility is inferred.

Time bounds are cooperative between filesystem calls, not a timeout on a stuck kernel call. Mount changes and concurrent renames are not atomic. PASS means completion of the stated restricted scan scope, not global filesystem coverage. Deleted-open files and excluded mounts remain unknown.

Comparison requires matching schema/environment/path/mount/device/total capacity and increasing explicit UTC timestamps. Namespace changes can make calls incomparable. The rate is net used bytes divided by start-time interval, not gross generation, ownership or causation. A flat full filesystem is not healthy.

Exit0 means requested observations completed in scope. Exit2 means unavailable, partial, incompatible or invalid input. Neither guarantees capacity health. The 29 synthetic tests are mocked and create no real fixtures.

CI checks the exact PR HEAD with a single lightweight job: source/test digest identity, 29 mock contracts, and capacity-only smoke on its own disposable GitHub runner. It never uploads user-environment raw evidence. Runtime isolation and recovery are separate acceptance questions.

## Review corrections

Independent initial review identified uncaught I/O exceptions, naive timestamps accepted for rate comparison, and unsafe maximum-mount-ID selection. All three were fixed and the same counterexamples rechecked. Errors now retain type/errno without raw details, compare requires explicit UTC, and mount selection uses parentage plus device verification or UNKNOWN.

The tool/test bytes were recovered from retained authoring text after local command startup became unavailable. Their SHA-256 values exactly match the independently recorded tested versions; no fresh shell execution or raw evidence transfer was used for that recovery. Report consolidation and hosted CI are reviewed separately for the final commit.
