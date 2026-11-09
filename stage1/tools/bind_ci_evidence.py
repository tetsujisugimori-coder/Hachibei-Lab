"""Bind only public CI results to the checked-out commit. Never fetch private inputs."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess


def main():
    target = Path(os.environ['EVIDENCE_DIR'])
    target.mkdir(parents=True, exist_ok=True)
    git = lambda *args: subprocess.check_output(['git', *args], text=True).strip()
    head = git('rev-parse', 'HEAD')
    expected = os.environ['EXPECTED_HEAD']
    if head != expected:
        raise RuntimeError('checked-out commit differs from requested PR head')
    logs = ('unit.log', 'validation.json', 'diff-check.log')
    outcome = os.environ.get('CHECK_OUTCOME', 'UNKNOWN')
    complete = outcome == 'success' and all((target / n).is_file() for n in logs)
    record = {
        'head': head, 'tree': git('rev-parse', 'HEAD^{tree}'), 'expected_head': expected,
        'run_id': os.environ.get('GITHUB_RUN_ID', 'NOT_TESTED'),
        'attempt': os.environ.get('GITHUB_RUN_ATTEMPT', 'NOT_TESTED'),
        'python_version': platform.python_version(),
        'jsonschema_version': importlib.metadata.version('jsonschema'),
        'workflow_sha256': hashlib.sha256(Path('.github/workflows/stage1-inventory.yml').read_bytes()).hexdigest(),
        'check_outcome': outcome, 'evidence_complete': complete,
        'private_inputs': 'NOT_PRESENT',
    }
    (target / 'identity.json').write_text(json.dumps(record, indent=2) + '\n')
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(target.iterdir())
              if p.is_file() and p.name != 'SHA256SUMS.json'}
    (target / 'SHA256SUMS.json').write_text(json.dumps(hashes, indent=2) + '\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
