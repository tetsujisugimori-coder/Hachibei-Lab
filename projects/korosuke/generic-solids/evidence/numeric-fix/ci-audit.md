# Stage 3B historical CI audit

Read-only retrieval on 2026-11-09 UTC. Original decoded GitHub job logs and job summaries are retained next to this report. No repository configuration or implementation was changed by this audit.

## Observed facts

| Run | Actual checkout | Test step | Failure |
|---|---|---|---|
| 42597382913 | d313591055a4cbe90400e2e25bd2388535a71de3 | NOT_RUN | Ubuntu package freecad-python3 not found |
| 42598301091 | 9f7edc28fdf2a96aa0a8c81e4943476f18cb8206 | NOT_RUN | Ubuntu freecad has no installation candidate |
| 42599221985 | 77b7450ee00f58c28fc6c5e19a15d1b43173df63 | SUCCESS | Bind evidence: dubious ownership |
| 42603141367 | d2670ce22e0e5006e2dd25e0a85f3d5b6fb9b6b6 | SUCCESS | Bind evidence: dubious ownership |

Latest job 129112267666 recorded 26 unit/process tests, 120 analytic boxes, 9 corruption rejections and 20 Stage 3A tests as successful. The combined job conclusion is FAILURE. `git rev-parse HEAD` returned exit 128 before identity.json/SHA256SUMS.json could be written. Upload-artifact nevertheless succeeded with artifact 13666064624, 21,222 bytes and ZIP digest db7e2c88b9e9eb9782e15918060540ad8235f31ab2139f419fd800fdd13f720a. This upload is not complete success evidence.

## Ownership/configuration diagnosis

The container command mounts host `/home/runner/work` as `/__w`, runs Debian trixie without a `--user` override, sets workdir `/__w/Hachibei-Lab/Hachibei-Lab`, and explicitly sets HOME=/github/home. Checkout logs show Git 2.47.3 and a temporary HOME `/__w/_temp/3be4b31f-952b-447a-a2cf-ae62e8b205a4`; its safe.directory addition goes to that temporary global configuration. The later shell Bind evidence step does not use checkout's temporary HOME and Git rejects repository ownership. Post-checkout cleanup again switches to another temporary HOME and succeeds.

These observations establish a safe-directory configuration scope mismatch across checkout and ordinary run steps, consistent with the host-mounted ownership check. The historical logs do not include `id` or `stat`; the numeric effective UID, checkout owner and .git owner are NOT_RECORDED. Debian's default root user is an inference, not a measured UID from these runs.

## Minimal corrective design (not executed by this audit)

Prefer command-scoped `git -c safe.directory=<exact resolved GITHUB_WORKSPACE> rev-parse ...`, shared by both HEAD and tree lookups. Do not use a wildcard, recursive trust, system/global persistent change, `SUDO_UID` substitution or ownership rewriting. Verify current workdir resolves exactly to GITHUB_WORKSPACE before accepting the exception. Record effective UID/GID, workspace/.git owners, HOME, actual checkout HEAD/tree, expected PR-head SHA and runner event SHA separately. Check expected head equals actual checkout. Keep failed execution and evidence completeness separate; incomplete evidence must not be accepted just because an artifact exists.

Final CI should record these identities to distinguish the inferred ownership component from measured results. A targeted negative control should show an untrusted differently-owned repository fails without the scoped exception, while the exact intended repository succeeds with it; no persistent configuration should be modified.

## Publication scan

The saved logs were scanned for common GitHub tokens, bearer strings, private-key markers and private Space identifiers; see public-scan.json. No matching secret/private CAD identifier was found. Logs contain normal public repository paths, ephemeral hosted-runner IDs, a masked checkout token and public neutral-test output, not original character CAD. Pattern scans are limited and are not a universal leak proof.
