#!/usr/bin/env python3
"""Opt-in, non-deleting Linux capacity guard. No daemon or global settings."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import select
import signal
import stat
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

DEFAULT = {"warn_percent": 80, "stop_percent": 95,
           "warn_bytes": 1024**3, "stop_bytes": 256*1024**2,
           "warn_inodes": 10000, "stop_inodes": 1000}
LIMIT = 8*1024**2


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def policies(path=None):
    result = {key: dict(DEFAULT) for key in ("shared_tmp", "workspace")}
    if path:
        raw = json.loads(Path(path).read_text())
        if not isinstance(raw, dict) or set(raw) - set(result):
            raise ValueError("unknown policy volume")
        for key, value in raw.items():
            if not isinstance(value, dict) or set(value) - set(DEFAULT):
                raise ValueError("unknown threshold")
            result[key].update(value)
    for value in result.values():
        if any(type(x) not in (int, float) or not math.isfinite(x) or x < 0
               for x in value.values()):
            raise ValueError("thresholds must be finite nonnegative numbers")
        if not 0 < value['warn_percent'] < value['stop_percent'] <= 100:
            raise ValueError("require 0 < warn_percent < stop_percent <= 100")
        for metric in ('bytes', 'inodes'):
            if value['stop_'+metric] > value['warn_'+metric]:
                raise ValueError("stop available threshold must not exceed warning")
    return result


def classify(used, available, warning, stop, policy):
    if used >= policy['stop_percent'] or available <= stop:
        return 'STOP'
    if used >= policy['warn_percent'] or available <= warning:
        return 'WARN'
    return 'OK'


def mount_info(path):
    """Linux mount identity, without exposing mount sources/options."""
    try:
        candidates = []
        for line in Path('/proc/self/mountinfo').read_text().splitlines():
            left, right = line.split(' - ', 1)
            mount = re.sub(r'\\([0-7]{3})', lambda m: chr(int(m[1], 8)), left.split()[4])
            if path == Path(mount) or path.is_relative_to(Path(mount)):
                candidates.append((len(mount), mount, right.split()[0]))
        _, mount, filesystem = max(candidates)
        return {'mount_point': mount, 'filesystem_type': filesystem}
    except (OSError, ValueError, IndexError):
        return {'mount_point': None, 'filesystem_type': 'UNKNOWN'}


def sample(path, policy):
    try:
        p = Path(path).resolve(strict=True)
        s = os.statvfs(p)
        block = s.f_frsize or s.f_bsize
        used = s.f_blocks - s.f_bfree
        denom = used + s.f_bavail
        if denom <= 0 or s.f_files <= 0 or s.f_favail < 0:
            raise ValueError('capacity or inode counters unavailable')
        disk_percent = used / denom * 100
        inode_percent = (s.f_files - s.f_ffree) / (s.f_files - s.f_ffree + s.f_favail) * 100
        disk = classify(disk_percent, s.f_bavail*block, policy['warn_bytes'], policy['stop_bytes'], policy)
        inode = classify(inode_percent, s.f_favail, policy['warn_inodes'], policy['stop_inodes'], policy)
        return {'path': str(p), 'device': os.stat(p).st_dev, **mount_info(p),
                'total_bytes': s.f_blocks*block, 'available_bytes': s.f_bavail*block,
                'disk_used_percent': disk_percent, 'total_inodes': s.f_files,
                'available_inodes': s.f_favail, 'inode_used_percent': inode_percent,
                'disk': disk, 'inode': inode,
                'state': 'STOP' if 'STOP' in (disk, inode) else 'WARN' if 'WARN' in (disk, inode) else 'OK'}
    except (OSError, ValueError, ZeroDivisionError) as exc:
        return {'path': str(path), 'state': 'UNKNOWN', 'error': type(exc).__name__}


def measure(workspace, policy):
    volumes = {'shared_tmp': sample('/tmp', policy['shared_tmp']),
               'workspace': sample(workspace, policy['workspace'])}
    states = [v['state'] for v in volumes.values()]
    return {'observed_at': now(), 'volumes': volumes,
            'same_device': (volumes['shared_tmp'].get('device') == volumes['workspace'].get('device'))
                           if all('device' in v for v in volumes.values()) else None,
            'state': next((s for s in ('UNKNOWN', 'STOP', 'WARN') if s in states), 'OK')}


def git(repo, *args):
    env = {**os.environ, 'GIT_OPTIONAL_LOCKS': '0'}
    cmd = ['git', '-c', 'core.fsmonitor=false', '-c', 'core.untrackedCache=false', '-C', str(repo), *args]
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env) as proc:
        data = bytearray()
        deadline = time.monotonic()+15
        try:
            while True:
                remaining = deadline-time.monotonic()
                if remaining <= 0 or not select.select([proc.stdout], [], [], remaining)[0]:
                    raise ValueError('Git read timed out')
                chunk = os.read(proc.stdout.fileno(), 65536)
                if not chunk:
                    break
                data.extend(chunk)
                if len(data) > LIMIT:
                    raise ValueError('Git output exceeds 8 MiB check limit')
            if proc.wait(timeout=max(.01, deadline-time.monotonic())):
                raise ValueError('Git read failed: '+args[0])
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
        data = bytes(data)
    return data


def file_hash(path, max_bytes=128*1024**2):
    p = Path(path)
    if p.is_symlink() or not p.is_file() or p.stat().st_size > max_bytes:
        raise ValueError('artifact must be a bounded regular file, not a symlink')
    h = hashlib.sha256()
    with p.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024**2), b''):
            h.update(chunk)
    return h.hexdigest()


def preservation(repo, manifest=None):
    """Read-only check. Remote freshness, ignored files and durability are unknown."""
    try:
        repo = Path(repo).resolve(strict=True)
        top = Path(os.fsdecode(git(repo, 'rev-parse', '--show-toplevel').strip())).resolve()
        if top != repo:
            raise ValueError('repo must be the repository root, not a subdirectory')
        head = git(repo, 'rev-parse', '--verify', 'HEAD').decode().strip()
        status = git(repo, 'status', '--porcelain=v1', '-z', '--untracked-files=all', '--ignore-submodules=none')
        # Submodule content cannot be represented by the superproject patch.
        submodules = git(repo, 'ls-files', '--stage').splitlines()
        if any(line.startswith(b'160000 ') for line in submodules):
            raise ValueError('submodules require a separate preservation review')
        staged = git(repo, 'diff', '--cached', '--binary', '--no-ext-diff', '--no-textconv', 'HEAD')
        worktree = git(repo, 'diff', '--binary', '--no-ext-diff', '--no-textconv')
        untracked = [os.fsdecode(p) for p in git(repo, 'ls-files', '--others', '--exclude-standard', '-z').split(b'\0') if p]
        untracked_hashes = {p: file_hash(repo / p, LIMIT) for p in untracked}
        try:
            upstream = git(repo, 'rev-parse', '--symbolic-full-name', '@{upstream}').decode().strip()
            if not upstream.startswith('refs/remotes/'):
                raise ValueError('local upstream is not submission evidence')
            ahead, behind = map(int, git(repo, 'rev-list', '--left-right', '--count', 'HEAD...@{upstream}').split())
        except ValueError:
            ahead = behind = None
        result = {'head': head, 'dirty': bool(status), 'untracked_count': len(untracked),
                  'ahead_of_cached_upstream': ahead, 'behind_cached_upstream': behind,
                  'remote_freshness': 'UNKNOWN', 'ignored_files': 'NOT_CHECKED',
                  'restart_durability': 'UNKNOWN', 'restore_test': 'NOT_RUN',
                  'state': 'CLEAN_CACHED_UPSTREAM' if not status and ahead == 0 else 'NEEDS_PRESERVATION'}
        if not manifest:
            return result
        raw = Path(manifest).read_bytes()
        if len(raw) > 1024**2:
            raise ValueError('manifest exceeds 1 MiB')
        data = json.loads(raw)
        if data['head'] != head:
            raise ValueError('manifest HEAD mismatch')
        def artifact(entry):
            if not isinstance(entry, dict) or not Path(entry['path']).is_absolute():
                raise ValueError('artifact paths must be absolute')
            h = file_hash(entry['path'])
            if h != entry['sha256']:
                raise ValueError('artifact checksum mismatch')
            return h
        bundle = data['bundle']
        artifact(bundle)
        git(repo, 'bundle', 'verify', bundle['path'])
        heads = git(repo, 'bundle', 'list-heads', bundle['path']).splitlines()
        if not any(line.split()[0].decode() == head for line in heads):
            raise ValueError('bundle does not contain current HEAD')
        for name, expected in (('staged_patch', staged), ('worktree_patch', worktree)):
            if artifact(data[name]) != digest(expected):
                raise ValueError(name+' does not match current content')
        copies = data['untracked']
        if not isinstance(copies, list) or len({row['source'] for row in copies}) != len(copies):
            raise ValueError('duplicate or invalid untracked entries')
        for row in copies:
            original = repo / row['source']
            saved = Path(row['path']).resolve()
            if saved.is_relative_to(repo) or (original.exists() and os.path.samefile(original, saved)):
                raise ValueError('untracked backup must be a separate external copy, not the live file or a hardlink')
        if {row['source']: artifact(row) for row in copies} != untracked_hashes:
            raise ValueError('untracked backup coverage mismatch')
        result.update(state='LOCAL_ARTIFACTS_VERIFIED', artifact_count=3+len(copies),
                      bundle_prerequisites='CHECKED_IN_CURRENT_REPO_ONLY')
        return result
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        return {'state': 'UNKNOWN', 'error': str(exc), 'restart_durability': 'UNKNOWN'}


class Recorder:
    def __init__(self, root):
        self.stream = (root/'events.jsonl').open('x', encoding='utf-8')
        self.bytes_written = 0
    def write(self, kind, **values):
        line = json.dumps({'at': now(), 'event': kind, **values}, ensure_ascii=True)+'\n'
        self.bytes_written += len(line.encode('utf-8'))
        if self.bytes_written > LIMIT:
            raise OSError('event log size limit reached')
        self.stream.write(line)
        self.stream.flush()
        os.fsync(self.stream.fileno())
    def close(self):
        self.stream.close()


def run_directory(workspace, root, task):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', task):
        raise ValueError('task must be 1-64 safe ASCII characters')
    workspace = Path(workspace).resolve(strict=True)
    root = Path(root)
    if not root.is_absolute():
        raise ValueError('run root must be absolute')
    # Existing path components may not redirect writes through symlinks.
    if any(p.is_symlink() for p in (root, *root.parents)):
        raise ValueError('run root has a symlink component')
    root = root.resolve()
    if not root.is_relative_to(workspace) or root == workspace or root.is_relative_to(Path('/tmp')):
        raise ValueError('run root must be a dedicated directory below workspace, never /tmp')
    ancestor = root
    while not ancestor.exists():
        ancestor = ancestor.parent
    if os.stat(ancestor).st_dev != os.stat(workspace).st_dev:
        raise ValueError('run root must be on the measured workspace filesystem')
    root.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix=task+'-', dir=root))
    for name in ('tmp', 'node-cache', 'npm-cache'):
        (run/name).mkdir()
    return run


def stop_group(proc, grace=3):
    """Only the group created by this invocation; no global process search."""
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.monotonic()+grace
    while time.monotonic() < deadline:
        proc.poll()
        try:
            os.killpg(proc.pid, 0)
        except ProcessLookupError:
            return
        time.sleep(.05)
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    proc.wait()


def execute(workspace, repo, root, task, command, policy, manifest=None, interval=5):
    if not math.isfinite(interval) or not .1 <= interval <= 300:
        raise ValueError('interval must be 0.1-300 seconds')
    if not command:
        raise ValueError('command required after --')
    if os.stat(repo).st_dev != os.stat(workspace).st_dev:
        raise ValueError('repo must be on the measured workspace filesystem')
    before = measure(workspace, policy)
    keep = preservation(repo, manifest)
    run = run_directory(workspace, root, task)
    recorder = Recorder(run)
    proc = None
    handlers = {}
    interrupted = []
    try:
        recorder.write('preflight', capacity=before, preservation=keep, auto_delete=False)
        print(json.dumps({'run_directory': str(run), 'capacity': before, 'preservation': keep}), flush=True)
        if before['state'] in ('STOP', 'UNKNOWN'):
            recorder.write('refused', reason='capacity_'+before['state'])
            return 20 if before['state'] == 'STOP' else 21
        if keep['state'] not in ('CLEAN_CACHED_UPSTREAM', 'LOCAL_ARTIFACTS_VERIFIED'):
            recorder.write('refused', reason='preservation_'+keep['state'])
            return 22
        env = {**os.environ, 'TMPDIR': str(run/'tmp'), 'TMP': str(run/'tmp'), 'TEMP': str(run/'tmp'),
               'NODE_COMPILE_CACHE': str(run/'node-cache'), 'npm_config_cache': str(run/'npm-cache')}
        # PLAYWRIGHT_BROWSERS_PATH/XDG_CACHE_HOME remain unchanged. No installs or cleanup.
        for sig in (signal.SIGINT, signal.SIGTERM):
            handlers[sig] = signal.signal(sig, lambda signum, frame: interrupted.append(signum))
        proc = subprocess.Popen(command, cwd=repo, env=env, start_new_session=True)
        recorder.write('started', pid=proc.pid, process_group=proc.pid)
        while True:
            if interrupted:
                stop_group(proc)
                recorder.write('stopped', reason='signal', signal=interrupted[0])
                return 128+interrupted[0]
            code = proc.poll()
            if code is not None:
                # Reap in-group background children even when the direct child exits.
                stop_group(proc)
                recorder.write('finished', child_returncode=code)
                return code if code >= 0 else 128-code
            current = measure(workspace, policy)
            recorder.write('sample', capacity=current)
            if current['state'] in ('STOP', 'UNKNOWN'):
                stop_group(proc)
                recorder.write('stopped', reason='capacity_'+current['state'])
                return 20 if current['state'] == 'STOP' else 21
            time.sleep(interval)
    except (OSError, ValueError) as exc:
        if proc is not None:
            stop_group(proc)
        try:
            recorder.write('error', error=type(exc).__name__, child_stopped=proc is not None)
        except OSError:
            pass
        # Log failure must never leave the child running; stderr is fallback, not durable proof.
        print(json.dumps({'state': 'ERROR', 'error': type(exc).__name__, 'child_stopped': proc is not None}), file=sys.stderr)
        return 23
    finally:
        for sig, old in handlers.items():
            signal.signal(sig, old)
        try:
            recorder.close()
        except OSError:
            pass


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['check', 'run'])
    p.add_argument('--workspace', required=True, type=Path)
    p.add_argument('--repo', required=True, type=Path)
    p.add_argument('--policy', type=Path)
    p.add_argument('--preservation-manifest', type=Path)
    p.add_argument('--run-root', type=Path)
    p.add_argument('--task', default='task')
    p.add_argument('--interval', type=float, default=5)
    # Split only the explicit delimiter, so options after the action still parse normally.
    raw = list(sys.argv[1:] if argv is None else argv)
    split = raw.index('--') if '--' in raw else len(raw)
    args = p.parse_args(raw[:split])
    command = raw[split+1:]
    try:
        policy = policies(args.policy)
        workspace = args.workspace.resolve(strict=True)
        repo = args.repo.resolve(strict=True)
        if not workspace.is_dir() or not repo.is_dir():
            raise ValueError('workspace/repo must be directories')
        if args.action == 'check':
            record = measure(workspace, policy)
            keep = preservation(repo, args.preservation_manifest)
            print(json.dumps({'capacity': record, 'preservation': keep, 'policy': policy, 'auto_delete': False}, indent=2))
            if record['state'] in ('STOP', 'UNKNOWN'):
                return 20 if record['state'] == 'STOP' else 21
            return 0 if keep['state'] in ('CLEAN_CACHED_UPSTREAM', 'LOCAL_ARTIFACTS_VERIFIED') else 22
        if not args.run_root:
            raise ValueError('--run-root required for run')
        return execute(workspace, repo, args.run_root, args.task, command, policy,
                       args.preservation_manifest, args.interval)
    except (OSError, ValueError) as exc:
        print(json.dumps({'state': 'ERROR', 'error': str(exc)}), file=sys.stderr)
        return 23


if __name__ == '__main__':
    sys.exit(main())
