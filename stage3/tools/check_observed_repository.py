"""Fixed-base preservation and bounded public scan; never print matched content."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = '55479ddee78f6ede43cbe550d8703ac1a8a66591'
WORKFLOW = '.github/workflows/stage3-approvals.yml'
NEW_TOOLS = {'stage3/tools/observed_evidence.py', 'stage3/tools/test_observed_evidence.py',
             'stage3/tools/check_observed_repository.py'}


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def check():
    names = git('ls-tree', '-r', '--name-only', BASE).decode().splitlines()
    for name in names:
        if name == WORKFLOW:
            continue
        original = git('show', BASE + ':' + name)
        if not (ROOT / name).is_file() or hashlib.sha256((ROOT / name).read_bytes()).digest() != hashlib.sha256(original).digest():
            raise ValueError('baseline changed')
    changed = set(git('diff', '--name-only', BASE).decode().splitlines())
    changed.update(git('ls-files', '--others', '--exclude-standard').decode().splitlines())
    for name in changed:
        if name not in NEW_TOOLS and name != WORKFLOW and not name.startswith('stage3/real-evidence/'):
            raise ValueError('unexpected changed path')
        p = ROOT / name
        if p.is_symlink() or not p.is_file() or p.stat().st_size > 4 * 1024 * 1024:
            raise ValueError('unsafe public file')
        content = p.read_text('utf-8')
        markers = ('sk-' + 'proj-', 'BEGIN ' + 'PRIVATE KEY', 'chatgpt.com/' + 'space/',
                   'Sentinel' + '_', 'libfile' + '_', 'user-' + 'gdb', 'approval_' + 'ref',
                   'chatgpt.com/' + 'c/', 'CalpicoFile' + '_')
        if any(marker in content for marker in markers):
            raise ValueError('bounded marker scan rejected')
    return {'baseline': BASE, 'baseline_preservation': 'PASS', 'allowed_paths': 'PASS',
            'bounded_marker_scan': 'PASS', 'universal_secret_absence': 'NOT_PROVEN'}


if __name__ == '__main__':
    try:
        print(json.dumps(check(), sort_keys=True))
    except (OSError, UnicodeError, ValueError, subprocess.CalledProcessError):
        print(json.dumps({'status': 'FAIL', 'reason': 'PUBLIC_BOUNDARY_OR_PRESERVATION_CHECK_FAILED'}))
        raise SystemExit(1)
