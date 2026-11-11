#!/usr/bin/env python3
"""Offline synthetic probe. Fresh run root required; no install or deletion commands."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
from datetime import datetime, timezone


def usage(path):
    s = os.statvfs(path)
    return dict(total_bytes=s.f_blocks*s.f_frsize, available_bytes=s.f_bavail*s.f_frsize,
                free_bytes=s.f_bfree*s.f_frsize, inodes=s.f_files, free_inodes=s.f_ffree)


def fingerprint(path):
    """Metadata-only, no private file contents or filenames emitted. Excludes atime."""
    path = Path(path)
    if not path.exists():
        return {'exists': False}
    digest = hashlib.sha256()
    count = size = blocks = 0
    for base, dirs, files in os.walk(path, followlinks=False):
        dirs.sort()
        for name in sorted(dirs + files):
            p = Path(base)/name
            s = p.lstat()
            digest.update(json.dumps([str(p.relative_to(path)), s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns], separators=(',', ':')).encode())
            count += 1
            size += s.st_size
            blocks += s.st_blocks*512
    return dict(exists=True, entries=count, logical_bytes=size, allocated_bytes=blocks, metadata_sha256=digest.hexdigest())


def validated_run_root(raw):
    """Reject every symlink component before resolving '..'; no writes here.

    Intended for trusted workspace parents, not adversarial concurrent renames.
    """
    path = Path(raw).absolute()
    component = Path(path.anchor)
    for part in path.parts[1:]:
        component = component / part
        if component.is_symlink():
            raise ValueError('run root must not contain symlink components')
    resolved = path.resolve(strict=False)
    if resolved.exists() or resolved.is_relative_to(Path('/tmp').resolve()):
        raise ValueError('run root must be new and outside shared /tmp')
    return resolved


def run_owned_group(command, *, cwd, env, timeout=60):
    """POSIX: terminate only the new session's process group, even on success.

    Descendants that deliberately detach into another session are outside this
    bounded helper's guarantee; it never scans/kills arbitrary system processes.
    """
    process = subprocess.Popen(command, cwd=cwd, env=env, text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               start_new_session=True)
    timed_out = False
    output = ''
    try:
        try:
            output, _ = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as error:
            timed_out = True
            output = error.output or b''
            if isinstance(output, bytes):
                output = output.decode(errors='replace')
    finally:
        # The session/group ID is this child PID, never the caller's group.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        if timed_out or process.poll() is None:
            try:
                output, _ = process.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                # A detached descendant could retain the pipe; do not wait forever.
                process.stdout.close()
                process.wait(timeout=2)
    if timed_out:
        return -1, output + '\nTIMEOUT: owned process group terminated\n'
    return process.returncode, output


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-root', required=True)
    p.add_argument('--playwright-module', required=True)
    p.add_argument('--chromium', required=True)
    p.add_argument('--webkit', required=True)
    p.add_argument('--browser-cache', required=True)
    args = p.parse_args()
    try:
        root = validated_run_root(args.run_root)
    except (ValueError, OSError, RuntimeError) as error:
        p.error(str(error))
    root.mkdir(parents=True)
    for name in ('tmp', 'npm-cache', 'node-cache', 'xdg-cache', 'xdg-config', 'home'):
        (root/name).mkdir()
    source = Path(__file__).with_name('smoke.cjs')
    shutil.copyfile(source, root/'smoke.cjs')
    (root/'package.json').write_text(json.dumps({'name':'capacity-probe','version':'1.0.0','private':True,'scripts':{'build':'node smoke.cjs build'}})+'\n')
    env = os.environ.copy()
    env.update(TMPDIR=str(root/'tmp'), TMP=str(root/'tmp'), TEMP=str(root/'tmp'),
               HOME=str(root/'home'), npm_config_cache=str(root/'npm-cache'),
               NODE_COMPILE_CACHE=str(root/'node-cache'), XDG_CACHE_HOME=str(root/'xdg-cache'),
               XDG_CONFIG_HOME=str(root/'xdg-config'), PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD='1',
               PLAYWRIGHT_BROWSERS_PATH=args.browser_cache, PROBE_PLAYWRIGHT_MODULE=args.playwright_module,
               PROBE_CHROMIUM=args.chromium, PROBE_WEBKIT=args.webkit)
    # Do not record environment values or arbitrary private cache filenames.
    shared = {'browser-cache':args.browser_cache, 'default-npm-cache':str(Path.home()/'.npm'),
              'shared-node-cache':'/tmp/node-compile-cache'}
    result = {'schema_version':1, 'started_utc':datetime.now(timezone.utc).isoformat(),
              'scope':'synthetic offline smoke; no restart or complete cache isolation claim',
              'script_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
              'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'pre':{'workspace':usage(root), 'shared_tmp':usage('/tmp')},
              'shared_pre':{k:fingerprint(v) for k,v in shared.items()}, 'commands':[]}
    commands = [['node','--version'], ['npm','--version'], ['npm','config','get','cache'],
                ['npm','run','build','--offline'], ['node','smoke.cjs','chromium'], ['node','smoke.cjs','webkit']]
    for i, command in enumerate(commands):
        try:
            code, output = run_owned_group(command, cwd=root, env=env)
        except (OSError, subprocess.TimeoutExpired) as error:
            code, output = -1, str(error)
        # Local paths are useful for local diagnostics; publication uses substituted paths.
        output = output.replace(str(root), 'RUN_ROOT').replace(str(Path.home()), 'USER_HOME')
        (root/f'command-{i}.log').write_text(output)
        result['commands'].append(dict(argv=command,exit_code=code,status='PASS' if code == 0 else 'FAILED',output=output))
    result.update(post={'workspace':usage(root),'shared_tmp':usage('/tmp')},
                  shared_post={k:fingerprint(v) for k,v in shared.items()},
                  owned=fingerprint(root), finished_utc=datetime.now(timezone.utc).isoformat())
    result['shared_metadata_unchanged'] = {k:result['shared_pre'][k] == result['shared_post'][k] for k in shared}
    result['artifact_sha256'] = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir() if p.is_file()}
    (root/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'results':str(root/'results.json'),'commands':[{k:v for k,v in r.items() if k != 'output'} for r in result['commands']], 'shared_metadata_unchanged':result['shared_metadata_unchanged']}))
    return 0 if all(r['exit_code'] == 0 for r in result['commands']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
