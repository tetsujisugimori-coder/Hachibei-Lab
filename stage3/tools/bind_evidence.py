import hashlib,json,os,subprocess
from pathlib import Path
p=Path(os.environ['EVIDENCE_DIR']);p.mkdir(parents=True,exist_ok=True)
def git(*args):return subprocess.check_output(['git',*args],text=True).strip()
head=git('rev-parse','HEAD'); ok=os.getenv('CHECK_OUTCOME')=='success' and head==os.getenv('EXPECTED_HEAD')
obj={'head':head,'tree':git('rev-parse','HEAD^{tree}'),'expected_head':os.getenv('EXPECTED_HEAD'),'run_id':os.getenv('GITHUB_RUN_ID'),'attempt':os.getenv('GITHUB_RUN_ATTEMPT'),'evidence_complete':ok,'files':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in p.iterdir() if f.is_file()},'workflow_sha256':hashlib.sha256(Path('.github/workflows/stage3-approvals.yml').read_bytes()).hexdigest()}
(p/'identity.json').write_text(json.dumps(obj,indent=2)+'\n')
if not ok:raise SystemExit(1)
