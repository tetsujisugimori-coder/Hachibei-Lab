#!/usr/bin/env python3
"""Metadata-only diagnostic. Output is private and must be reviewed before sharing."""
import argparse
import datetime as dt
import hashlib
import json
import math
import os
import stat
import sys
import time

SCHEMA = 1
MAX_METADATA = 1024 * 1024

def stamp():
    now = dt.datetime.now(dt.timezone.utc)
    return {'utc': now.isoformat(), 'jst': now.astimezone(dt.timezone(dt.timedelta(hours=9))).isoformat()}

def error(exc):
    return {'type': type(exc).__name__, 'errno': getattr(exc, 'errno', None)}

def metadata(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = f.read(MAX_METADATA + 1)
    if len(data) > MAX_METADATA:
        raise ValueError('metadata exceeds size limit')
    return data

def unescape(value):
    for a, b in [('\\040', ' '), ('\\011', '\t'), ('\\012', '\n'), ('\\134', '\\')]:
        value = value.replace(a, b)
    return value

def mounts():
    result = []
    for line in metadata('/proc/self/mountinfo').splitlines():
        left, right = line.split(' - ', 1)
        a, b = left.split(), right.split()
        result.append({'id': a[0], 'parent_id': a[1], 'device': a[2], 'root': unescape(a[3]),
                       'target': unescape(a[4]), 'fstype': b[0],
                       'read_only': 'ro' in a[5].split(',')})
    return result

def contains(path, root):
    return path == root or path.startswith(root.rstrip('/') + '/')

def mount_for(path, table):
    candidates = [m for m in table if contains(path, m['target'])]
    if not candidates:
        return None
    deepest = max(len(m['target']) for m in candidates)
    candidates = [m for m in candidates if len(m['target']) == deepest]
    # Mount IDs can be reused. Resolve stacked mounts by parentage, not ID order.
    parents = {m.get('parent_id') for m in candidates}
    visible = [m for m in candidates if m['id'] not in parents]
    return visible[0] if len(visible) == 1 else None

def identity():
    # Boot ID and namespace descriptors distinguish environments, not users.
    raw = metadata('/proc/sys/kernel/random/boot_id').strip()
    raw += '|' + os.readlink('/proc/self/ns/mnt')
    return hashlib.sha256(raw.encode()).hexdigest()

def volume(path, table):
    try:
        if os.path.realpath(path) != path:
            return {'path': path, 'status': 'UNKNOWN', 'error': {'type': 'SymlinkTarget', 'errno': None}}
        s = os.stat(path)
        v = os.statvfs(path)
        unit = v.f_frsize or v.f_bsize
        mounted = mount_for(path, table)
        matched = mounted is not None and mounted['device'] == f'{os.major(s.st_dev)}:{os.minor(s.st_dev)}'
        return {'path': path, 'status': 'PASS' if matched else 'UNKNOWN', 'device': s.st_dev,
                'mount': mounted, 'mount_identity_verified': matched, 'total_bytes': v.f_blocks * unit,
                'free_bytes': v.f_bfree * unit, 'available_bytes': v.f_bavail * unit,
                'used_bytes': (v.f_blocks - v.f_bfree) * unit,
                'inodes': v.f_files, 'free_inodes': v.f_ffree,
                'available_inodes': v.f_favail,
                'inode_used_percent': (100 * (v.f_files - v.f_ffree) / v.f_files) if v.f_files else None}
    except (OSError, ValueError) as exc:
        return {'path': path, 'status': 'UNKNOWN', 'error': error(exc)}

def scan(root, table, max_entries=20000, max_seconds=5, max_depth=5, top=20):
    """Each directory uses a no-follow FD; no file content is opened.

    Byte totals count unique (device,inode) objects, including directories. A
    hardlink is assigned to the first observed top-level group. Traversal order
    is not guaranteed; partial totals are lower bounds, never full usage.
    """
    start = time.monotonic()
    out = {'root': root, 'status': 'PARTIAL', 'entries': 0, 'allocated_bytes': 0,
           'logical_bytes': 0, 'errors': [], 'skips': [], 'top_files': [],
           'top_level': [], 'hardlink_aliases': 0,
           'limits': {'entries': max_entries, 'seconds': max_seconds, 'depth': max_depth}}
    groups, seen, files = {}, set(), []
    boundary = {m['target'] for m in table if m['target'] != root and contains(m['target'], root)}
    stopped = False
    def skip(path, reason):
        # Bounded by visited entry budget.
        out['skips'].append({'path': path, 'reason': reason})
    def walk(path, depth, group, expected_dev=None):
        nonlocal stopped
        if stopped:
            return
        if time.monotonic() - start >= max_seconds:
            skip(path, 'time_limit'); stopped = True; return
        if out['entries'] >= max_entries:
            skip(path, 'entry_limit'); stopped = True; return
        try:
            fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        except OSError as exc:
            out['errors'].append({'path': path, **error(exc)}); return
        try:
            rs = os.fstat(fd)
            if expected_dev is not None and rs.st_dev != expected_dev:
                skip(path, 'device_boundary'); return
            with os.scandir(fd) as entries:
                for entry in entries:
                    if out['entries'] >= max_entries:
                        skip(path, 'entry_limit'); stopped = True; break
                    if time.monotonic() - start >= max_seconds:
                        skip(path, 'time_limit'); stopped = True; break
                    out['entries'] += 1
                    p = os.path.join(path, entry.name)
                    g = group or entry.name
                    try:
                        s = entry.stat(follow_symlinks=False)
                        if stat.S_ISLNK(s.st_mode):
                            skip(p, 'symlink'); continue
                        if s.st_dev != rs.st_dev or p in boundary:
                            skip(p, 'mount_boundary'); continue
                        key = (s.st_dev, s.st_ino)
                        if key in seen:
                            out['hardlink_aliases'] += 1; continue
                        seen.add(key)
                        alloc = s.st_blocks * 512
                        out['allocated_bytes'] += alloc
                        out['logical_bytes'] += s.st_size
                        item = groups.setdefault(g, {'name': g, 'allocated_bytes': 0, 'logical_bytes': 0})
                        item['allocated_bytes'] += alloc; item['logical_bytes'] += s.st_size
                        if stat.S_ISREG(s.st_mode):
                            files.append({'path': p, 'allocated_bytes': alloc, 'logical_bytes': s.st_size,
                                          'uid': s.st_uid, 'mtime_ns': s.st_mtime_ns})
                            files.sort(key=lambda f: f['allocated_bytes'], reverse=True)
                            del files[top:]
                        elif stat.S_ISDIR(s.st_mode):
                            if depth >= max_depth:
                                skip(p, 'depth_limit')
                            else:
                                walk(p, depth + 1, g, rs.st_dev)
                    except OSError as exc:
                        out['errors'].append({'path': p, **error(exc)})
                    if stopped:
                        break
        except OSError as exc:
            out['errors'].append({'path': path, **error(exc)})
        finally:
            try:
                os.close(fd)
            except OSError as exc:
                out['errors'].append({'path': path, **error(exc)})
    if os.path.realpath(root) != root:
        skip(root, 'symlink_root_or_ancestor')
    else:
        walk(root, 0, None)
    out['top_files'] = files
    out['top_level'] = sorted(groups.values(), key=lambda g: g['allocated_bytes'], reverse=True)[:top]
    out['elapsed_seconds'] = time.monotonic() - start
    incomplete = any(s['reason'] not in ('symlink', 'mount_boundary', 'device_boundary') for s in out['skips'])
    out['status'] = 'PARTIAL' if out['errors'] or incomplete else 'PASS'
    out['scope'] = 'Unique objects below root, excluding symlinks and nested mounts; root inode excluded.'
    return out

def snapshot(paths, scan_roots=(), **limits):
    started = stamp()
    failures = []
    try:
        env = identity()
    except (OSError, ValueError) as exc:
        env = None; failures.append({'operation': 'identity', **error(exc)})
    try:
        table = mounts()
    except (OSError, ValueError, IndexError) as exc:
        table = []; failures.append({'operation': 'mounts', **error(exc)})
    result = {'schema': SCHEMA, 'visibility': 'PRIVATE_REVIEW_REQUIRED', 'started': started,
              'environment': env, 'errors': failures, 'volumes': [volume(p, table) for p in paths],
              'scans': []}
    # No mount metadata means bind mount exclusions cannot be guaranteed.
    if scan_roots and not table:
        failures.append({'operation': 'scan', 'type': 'MountTableUnavailable', 'errno': None})
    else:
        result['scans'] = [scan(p, table, **limits) for p in scan_roots]
    result['ended'] = stamp()
    result['exit_code'] = 2 if failures or any(v['status'] != 'PASS' or not v['mount'] for v in result['volumes']) or any(s['status'] != 'PASS' for s in result['scans']) else 0
    return result

def compare(before, after):
    out = {'schema': SCHEMA, 'visibility': 'PRIVATE_REVIEW_REQUIRED', 'status': 'UNKNOWN', 'deltas': [],
           'interpretation': 'Net change only; not gross generation, ownership, or causation.'}
    if not isinstance(before, dict) or not isinstance(after, dict):
        out['reason'] = 'invalid_snapshot'; return out
    if before.get('schema') != SCHEMA or after.get('schema') != SCHEMA or not before.get('environment') or before.get('environment') != after.get('environment'):
        out['reason'] = 'incompatible_environment_or_schema'; return out
    try:
        first = dt.datetime.fromisoformat(before['started']['utc'])
        second = dt.datetime.fromisoformat(after['started']['utc'])
        if first.utcoffset() != dt.timedelta(0) or second.utcoffset() != dt.timedelta(0):
            raise ValueError('timestamps must explicitly identify UTC')
        seconds = (second - first).total_seconds()
        if not math.isfinite(seconds) or seconds <= 0:
            raise ValueError('invalid interval')
        if not isinstance(before['volumes'], list) or not isinstance(after['volumes'], list) or not all(isinstance(v, dict) for v in before['volumes'] + after['volumes']):
            raise ValueError('invalid volume collection')
        if len({v['path'] for v in before['volumes']}) != len(before['volumes']) or len({v['path'] for v in after['volumes']}) != len(after['volumes']):
            raise ValueError('duplicate volume paths')
        if {v['path'] for v in before['volumes']} != {v['path'] for v in after['volumes']}:
            raise ValueError('different target path sets')
        old = {v['path']: v for v in before['volumes']}
        for v in after['volumes']:
            a = old.get(v['path'])
            if not a or a.get('status') != 'PASS' or v.get('status') != 'PASS' or not a.get('mount') or a['mount'] != v.get('mount') or a.get('device') != v.get('device') or a['total_bytes'] != v['total_bytes']:
                out['deltas'].append({'path': v['path'], 'status': 'UNKNOWN', 'reason': 'incompatible_volume'}); continue
            if any(type(x) is not int or x < 0 for x in [v['used_bytes'], a['used_bytes'], v['total_bytes'], a['total_bytes']]) or v['used_bytes'] > v['total_bytes'] or a['used_bytes'] > a['total_bytes']:
                raise ValueError('invalid capacity values')
            delta = v['used_bytes'] - a['used_bytes']
            out['deltas'].append({'path': v['path'], 'status': 'PASS', 'seconds': seconds,
                                  'used_bytes_delta': delta, 'net_bytes_per_second': delta / seconds})
        out['status'] = 'PASS' if out['deltas'] and all(x['status'] == 'PASS' for x in out['deltas']) else 'PARTIAL'
    except (ValueError, KeyError, TypeError, AttributeError, OverflowError):
        out['deltas'] = []
        out['status'] = 'UNKNOWN'
        out['reason'] = 'invalid_snapshot'
    return out

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('snapshot')
    p.add_argument('--path', action='append', required=True)
    p.add_argument('--scan-root', action='append', default=[])
    p.add_argument('--max-entries', type=int, default=20000)
    p.add_argument('--max-seconds', type=float, default=5)
    p.add_argument('--max-depth', type=int, default=5)
    p.add_argument('--top', type=int, default=20)
    c = sub.add_parser('compare'); c.add_argument('before'); c.add_argument('after')
    args = parser.parse_args(argv)
    if args.command == 'compare':
        try:
            result = compare(json.loads(metadata(args.before)), json.loads(metadata(args.after)))
            code = 0 if result['status'] == 'PASS' else 2
        except (OSError, ValueError) as exc:
            result = {'status': 'UNKNOWN', 'error': error(exc)}; code = 2
    else:
        if not (1 <= args.max_entries <= 100000 and math.isfinite(args.max_seconds) and 0 < args.max_seconds <= 30 and 0 <= args.max_depth <= 20 and 1 <= args.top <= 100):
            parser.error('limits exceed permitted ranges')
        if len(args.path) > 16 or len(args.scan_root) > 4:
            parser.error('at most 16 capacity paths and 4 scan roots per invocation')
        paths = [os.path.abspath(p) for p in args.path]
        roots = [os.path.abspath(p) for p in args.scan_root]
        result = snapshot(paths, roots, max_entries=args.max_entries, max_seconds=args.max_seconds, max_depth=args.max_depth, top=args.top)
        code = result['exit_code']
    print(json.dumps(result, indent=2, allow_nan=False))
    return code

if __name__ == '__main__':
    sys.exit(main())
