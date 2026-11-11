# Isolated synthetic capacity probe

Use `run_probe.py --help` for the required explicit paths to already-installed Playwright/browser executables and a fresh workspace run root. No package installation, downloads, or file cleanup is performed. Settings apply only to the child processes.

The runner rejects existing run roots, every symlink path component, and paths that resolve beneath shared `/tmp`. Use a trusted workspace parent: this check is not protection against hostile concurrent parent-directory replacement.

Each command starts a new session/process group. After normal completion or timeout, only that owned group is terminated. Deliberately detached descendants are outside this helper's guarantee; it never discovers or kills unrelated processes.

The recorded run-01 predates these path/process hardening changes. Three synthetic hardening tests passed, including verification that a separately launched sentinel process survives. No browser smoke was rerun after hardening. See `../tmpdir-probe-2026-11-11.md` and the separate `measured_run_01` / `current` hash sections in `../evidence/tmpdir-sha256.json`.

To run tests without touching shared temp or writing bytecode:

```sh
PROBE_TEST_ROOT=/your/workspace/new-probe-test-dir \
PYTHONDONTWRITEBYTECODE=1 python3 probe/test_probe.py
```

The test root must not exist. Tests retain their own files. Run from the research directory or adjust the script path. These tests require Linux `/proc` and POSIX process groups.
