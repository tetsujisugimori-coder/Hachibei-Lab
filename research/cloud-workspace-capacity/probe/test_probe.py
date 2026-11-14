"""Synthetic hardening checks only; no browsers/downloads/shared cleanup."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest

spec = importlib.util.spec_from_file_location('probe', Path(__file__).with_name('run_probe.py'))
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
ROOT = Path(os.environ['PROBE_TEST_ROOT']).resolve()
ROOT.mkdir(parents=True, exist_ok=False)


def running(pid):
    try:
        return Path(f'/proc/{pid}/stat').read_text().split(') ')[1][0] != 'Z'
    except FileNotFoundError:
        return False


class ProbeSafety(unittest.TestCase):
    def test_paths(self):
        self.assertEqual(probe.validated_run_root(ROOT/'new'), ROOT/'new')
        for target in ['/tmp/new-owned-probe', '/workspace/../tmp/new-owned-probe', ROOT]:
            with self.assertRaises(ValueError):
                probe.validated_run_root(target)
        (ROOT/'link').symlink_to('/tmp', target_is_directory=True)
        (ROOT/'dangling').symlink_to(ROOT/'missing', target_is_directory=True)
        for target in [ROOT/'link/new', ROOT/'link/../new', ROOT/'dangling/new']:
            with self.assertRaises(ValueError):
                probe.validated_run_root(target)
        self.assertFalse((ROOT/'new').exists())

    def check_group(self, timeout_case):
        sentinel = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'],
                                    start_new_session=True)
        child_file = ROOT/('timeout.pid' if timeout_case else 'normal.pid')
        code = ('import subprocess,sys,time,pathlib; '
                'p=subprocess.Popen([sys.executable,"-c","import time; time.sleep(30)"],'
                'stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); '
                f'pathlib.Path({str(child_file)!r}).write_text(str(p.pid)); '
                + ('time.sleep(30)' if timeout_case else 'print("done")'))
        try:
            rc, output = probe.run_owned_group([sys.executable, '-c', code],
                                              cwd=ROOT, env=os.environ.copy(), timeout=0.5)
            self.assertEqual(rc, -1 if timeout_case else 0)
            pid = int(child_file.read_text())
            for _ in range(50):
                if not running(pid):
                    break
                time.sleep(0.02)
            self.assertFalse(running(pid), 'owned descendant remains running')
            self.assertIsNone(sentinel.poll(), 'unrelated process was affected')
            if timeout_case:
                self.assertIn('TIMEOUT', output)
        finally:
            sentinel.terminate()
            sentinel.wait(timeout=2)

    def test_normal_exit_group_cleanup(self):
        self.check_group(False)

    def test_timeout_group_cleanup(self):
        self.check_group(True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
