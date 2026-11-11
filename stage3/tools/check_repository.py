import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
baseline=json.loads((ROOT/'stage3/evidence/baseline.json').read_text())
for name,digest in baseline['files'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest, name
# Other research areas have legitimately merged since the original Stage 3
# baseline. Preserve that original hash check; scope this PR against its own
# fixed start, rather than incorrectly treating those merges as this change.
current=json.loads((ROOT/'stage3/evidence-foundation/baseline.json').read_text())
for name,digest in current['files'].items():
    if name not in current['allowed_existing_changes']:
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
changed=subprocess.check_output(['git','diff','--name-only',current['commit']],cwd=ROOT,text=True).splitlines()
for name in changed:
    assert name.startswith('stage3/') or name=='.github/workflows/stage3-approvals.yml',name
# A bounded leak scan, not proof of absence of all private information.
for f in (ROOT/'stage3').rglob('*'):
    if f.is_file() and '__pycache__' not in str(f):
        t=f.read_text()
        for marker in ['sk-'+'proj-','BEGIN '+'PRIVATE KEY','chatgpt.com/'+'space/','Sentinel'+'_','libfile'+'_']:
            assert marker not in t, str(f)
print(json.dumps({'baseline_files_unchanged':len(baseline['files']),'current_baseline_files_preserved':len(current['files'])-len(current['allowed_existing_changes']),'allowed_diff':True,'bounded_public_scan':True}))
