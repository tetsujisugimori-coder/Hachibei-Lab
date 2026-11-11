import importlib.util
import pathlib
import stat
import types
import unittest
from unittest.mock import patch

p = pathlib.Path(__file__).resolve().parents[1] / 'tools' / 'diagnose.py'
spec = importlib.util.spec_from_file_location('diagnose', p)
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)

def st(ino=1, mode=stat.S_IFREG, dev=2, size=10, blocks=1):
    return types.SimpleNamespace(st_ino=ino, st_dev=dev, st_mode=mode, st_size=size,
                                 st_blocks=blocks, st_uid=1000, st_mtime_ns=123)

class Entry:
    def __init__(self, name, value): self.name, self.value = name, value
    def stat(self, follow_symlinks):
        assert follow_symlinks is False
        if isinstance(self.value, Exception): raise self.value
        return self.value

class Entries:
    def __init__(self, values): self.values = values
    def __enter__(self): return iter(self.values)
    def __exit__(self, *args): pass

MOUNT = {'id': '1', 'device': '0:2', 'root': '/', 'target': '/', 'fstype': 'tmpfs', 'read_only': False}

class Tests(unittest.TestCase):
    def runscan(self, entries, **kw):
        with patch.object(d.os, 'open', return_value=17) as op, patch.object(d.os, 'close') as close, patch.object(d.os, 'fstat', return_value=st(mode=stat.S_IFDIR)), patch.object(d.os, 'scandir', side_effect=lambda fd: Entries(entries)), patch.object(d.os.path, 'realpath', side_effect=lambda x: x):
            result = d.scan('/test', kw.pop('table', [MOUNT]), **kw)
            self.assertEqual(op.call_args.args[1], d.os.O_RDONLY | d.os.O_DIRECTORY | d.os.O_NOFOLLOW)
            self.assertEqual(close.call_count, op.call_count)
            return result
    def test_empty(self):
        self.assertEqual(self.runscan([])['status'], 'PASS')
    def test_file_sizes_owner_time(self):
        r = self.runscan([Entry('a', st(size=10000, blocks=2))])
        self.assertEqual((r['allocated_bytes'], r['logical_bytes']), (1024, 10000))
        self.assertEqual(r['top_files'][0]['uid'], 1000)
        self.assertEqual(r['top_files'][0]['mtime_ns'], 123)
    def test_hardlink_once(self):
        r = self.runscan([Entry('a', st()), Entry('b', st())])
        self.assertEqual(r['allocated_bytes'], 512)
        self.assertEqual(r['hardlink_aliases'], 1)
    def test_symlink_never_followed(self):
        r = self.runscan([Entry('link', st(mode=stat.S_IFLNK))])
        self.assertEqual(r['allocated_bytes'], 0)
        self.assertEqual(r['skips'][0]['reason'], 'symlink')
    def test_device_boundary(self):
        r = self.runscan([Entry('different', st(dev=9))])
        self.assertEqual(r['allocated_bytes'], 0)
    def test_same_device_bind_mount_boundary(self):
        r = self.runscan([Entry('bind', st(mode=stat.S_IFDIR))], table=[MOUNT, {**MOUNT, 'target': '/test/bind'}])
        self.assertEqual(r['allocated_bytes'], 0)
    def test_depth_limit(self):
        r = self.runscan([Entry('dir', st(mode=stat.S_IFDIR))], max_depth=0)
        self.assertEqual(r['status'], 'PARTIAL')
        self.assertEqual(r['skips'][0]['reason'], 'depth_limit')
    def test_entry_limit(self):
        r = self.runscan([Entry('a', st()), Entry('b', st(ino=2))], max_entries=1)
        self.assertEqual(r['entries'], 1)
        self.assertEqual(r['status'], 'PARTIAL')
    def test_time_limit(self):
        with patch.object(d.time, 'monotonic', side_effect=[0, 1, 1]):
            r = d.scan('/test', [MOUNT], max_seconds=.1)
        self.assertEqual(r['status'], 'PARTIAL')
    def test_stat_error(self):
        r = self.runscan([Entry('gone', FileNotFoundError(2, 'not logged'))])
        self.assertEqual(r['errors'][0]['errno'], 2)
        self.assertEqual(r['status'], 'PARTIAL')
    def test_permission_error(self):
        with patch.object(d.os, 'open', side_effect=PermissionError(13, 'private detail')):
            r = d.scan('/test', [MOUNT])
        self.assertEqual(r['errors'][0]['errno'], 13)
        self.assertNotIn('private detail', str(r))
    def test_root_symlink(self):
        with patch.object(d.os.path, 'realpath', return_value='/elsewhere'), patch.object(d.os, 'open') as op:
            r = d.scan('/test', [MOUNT])
        op.assert_not_called(); self.assertEqual(r['status'], 'PARTIAL')
    def test_volume_missing(self):
        with patch.object(d.os, 'stat', side_effect=FileNotFoundError(2, 'missing')):
            self.assertEqual(d.volume('/missing', [])['status'], 'UNKNOWN')
    def test_inode_zero(self):
        v = types.SimpleNamespace(f_frsize=4096, f_bsize=4096, f_blocks=100, f_bfree=20, f_bavail=10, f_files=0, f_ffree=0, f_favail=0)
        with patch.object(d.os, 'stat', return_value=st()), patch.object(d.os, 'statvfs', return_value=v):
            r = d.volume('/test', [MOUNT])
        self.assertIsNone(r['inode_used_percent']); self.assertEqual(r['available_bytes'], 40960)
    def test_mount_longest_and_stack(self):
        table = [MOUNT, {**MOUNT, 'target': '/tmp', 'id': '20', 'parent_id': '1'}, {**MOUNT, 'target': '/tmp', 'id': '3', 'parent_id': '20'}]
        self.assertEqual(d.mount_for('/tmp/a', table)['id'], '3')
        self.assertEqual(d.mount_for('/tmpx', table)['id'], '1')
    def test_ambiguous_mount_stack(self):
        table = [MOUNT, {**MOUNT, 'id': '5'}]
        self.assertIsNone(d.mount_for('/test', table))
    def samples(self):
        v = {'path': '/tmp', 'status': 'PASS', 'device': 2, 'mount': MOUNT, 'total_bytes': 1000, 'used_bytes': 100}
        a = {'schema': 1, 'environment': 'test', 'started': {'utc': '2026-11-11T00:00:00+00:00'}, 'volumes': [v]}
        b = {**a, 'started': {'utc': '2026-11-11T00:01:00+00:00'}, 'volumes': [{**v, 'used_bytes': 160}]}
        return a, b
    def test_delta(self):
        a, b = self.samples(); r = d.compare(a, b)
        self.assertEqual(r['status'], 'PASS'); self.assertEqual(r['deltas'][0]['net_bytes_per_second'], 1)
    def test_environment_mismatch(self):
        a, b = self.samples(); b['environment'] = 'other'
        self.assertEqual(d.compare(a, b)['status'], 'UNKNOWN')
    def test_mount_mismatch(self):
        a, b = self.samples(); b['volumes'][0]['mount'] = {**MOUNT, 'id': '9'}
        self.assertEqual(d.compare(a, b)['status'], 'PARTIAL')
    def test_zero_interval(self):
        a, b = self.samples(); b['started'] = a['started']
        self.assertEqual(d.compare(a, b)['status'], 'UNKNOWN')
    def test_missing_identity(self):
        a, b = self.samples(); a['environment'] = None
        self.assertEqual(d.compare(a, b)['status'], 'UNKNOWN')
    def test_malformed_snapshots(self):
        a, b = self.samples()
        for bad in [None, [], 3, {'schema': 1, 'environment': 'test', 'volumes': [None]}]:
            self.assertEqual(d.compare(bad, b)['status'], 'UNKNOWN')
    def test_invalid_capacity(self):
        a, b = self.samples()
        for value in [True, -1, float('nan'), 9999999]:
            b['volumes'][0]['used_bytes'] = value
            self.assertEqual(d.compare(a, b)['status'], 'UNKNOWN')
    def test_duplicate_volumes(self):
        a, b = self.samples(); a['volumes'] *= 2
        self.assertEqual(d.compare(a, b)['status'], 'UNKNOWN')
    def test_different_target_sets(self):
        a, b = self.samples(); b['volumes'] = []
        self.assertEqual(d.compare(a, b)['status'], 'UNKNOWN')
    def test_scandir_and_fstat_errors(self):
        for operation in ['fstat', 'scandir']:
            with patch.object(d.os, 'open', return_value=17), patch.object(d.os, 'close'), patch.object(d.os.path, 'realpath', side_effect=lambda x: x), patch.object(d.os, 'fstat', return_value=st(mode=stat.S_IFDIR)), patch.object(d.os, operation, side_effect=OSError(5, 'RAW_PRIVATE_DETAIL')):
                r = d.scan('/test', [MOUNT])
            self.assertEqual(r['status'], 'PARTIAL')
            self.assertEqual(r['errors'][0]['errno'], 5)
            self.assertNotIn('RAW_PRIVATE_DETAIL', str(r))
    def test_scandir_iteration_error(self):
        def broken_iterator():
            yield Entry('a', st())
            raise OSError(5, 'RAW_PRIVATE_DETAIL')
        r = self.runscan(broken_iterator())
        self.assertEqual(r['status'], 'PARTIAL')
        self.assertEqual(r['errors'][0]['errno'], 5)
        self.assertNotIn('RAW_PRIVATE_DETAIL', str(r))
    def test_compare_requires_explicit_utc(self):
        for suffix in ['', '+09:00']:
            a, b = self.samples()
            a['started']['utc'] = '2026-11-11T00:00:00' + suffix
            b['started']['utc'] = '2026-11-11T00:01:00' + suffix
            self.assertEqual(d.compare(a, b)['status'], 'UNKNOWN')
    def test_no_mount_no_scan(self):
        with patch.object(d, 'mounts', side_effect=PermissionError(13, '')), patch.object(d, 'identity', return_value='x'), patch.object(d, 'scan') as scan:
            r = d.snapshot([], ['/test'])
        scan.assert_not_called(); self.assertEqual(r['exit_code'], 2)

if __name__ == '__main__': unittest.main()
