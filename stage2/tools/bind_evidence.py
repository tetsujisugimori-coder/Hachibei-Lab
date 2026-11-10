"""Bind public CI logs to the exact checked-out commit. No private inputs."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    dest=Path(os.environ['EVIDENCE_DIR']);dest.mkdir(parents=True,exist_ok=True)
    git=lambda *args:subprocess.check_output(['git','-C',str(ROOT),*args],text=True).strip()
    head=git('rev-parse','HEAD');expected=os.environ.get('EXPECTED_HEAD','UNKNOWN')
    required=['unit.log','stage1-regression.log','validation.json','diff-check.log']
    outcome=os.environ.get('CHECK_OUTCOME','UNKNOWN')
    complete=head==expected and outcome=='success' and all((dest/x).is_file() for x in required)
    identity={'head':head,'tree':git('rev-parse','HEAD^{tree}'),'expected_head':expected,'run_id':os.environ.get('GITHUB_RUN_ID','LOCAL'),'attempt':os.environ.get('GITHUB_RUN_ATTEMPT','0'),'check_outcome':outcome,'evidence_complete':complete,'workflow_sha256':sha(ROOT/'.github/workflows/stage2-relations.yml'),'private_inputs':'NOT_PRESENT'}
    (dest/'identity.json').write_text(json.dumps(identity,indent=2)+'\n')
    manifest={p.name:sha(p) for p in sorted(dest.iterdir()) if p.is_file() and p.name!='SHA256SUMS.json'}
    (dest/'SHA256SUMS.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(identity));return 0 if complete else 1
if __name__=='__main__':sys.exit(main())
