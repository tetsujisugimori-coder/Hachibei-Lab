"""Run immutable red/green counterexamples and independent numerical regressions."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import mpmath

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'sweep.py'
ORIGINAL=HERE/'original'


def check_stress(r):
    counts=r.get('candidate_counts',{})
    if (r.get('total_cases')!=18000 or sum(counts.values())!=18000
        or any(k not in ('PROJECTED_OVERLAP','UNRESOLVED_2D','PROJECTED_CLEAR') for k in counts)
        or counts.get('PROJECTED_CLEAR',0)!=0
        or r.get('all_cases_have_independent_strict_overlap_witness') is not True
        or r.get('false_clear_examples')!=[]):
        raise ValueError('boundary stress gate failed')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    origin=json.loads((ORIGINAL/'IMMUTABLE.json').read_text())
    for name,expected in origin['files'].items():
        if hashlib.sha256((ORIGINAL/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('original evidence altered: '+name)
    metadata={'started_at':datetime.now(timezone.utc).isoformat(),'python':platform.python_version(),
              'platform':platform.platform(),'mpmath':mpmath.__version__,'commands':[],
              'original':origin,'source_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in [SOURCE,HERE.parent/'certified.py',HERE/'stress_with_hashes.py',Path(__file__)]}}
    for label,cmd in [('head',['git','rev-parse','HEAD']),('tree',['git','rev-parse','HEAD^{tree}']),('dirty',['git','status','--porcelain'])]:
        metadata[label]=subprocess.check_output(cmd,cwd=HERE,text=True).strip()
    env=dict(os.environ,PYTHONPATH=str(HERE.parent))
    def run(label,script,source,expected=0,extra=()):
        command=[sys.executable,str(script),'--source',str(source),'--output',str(out/(label+'.json')),*extra]
        start=time.perf_counter();p=subprocess.run(command,env=env,capture_output=True,text=True)
        (out/(label+'.log')).write_text(p.stdout+p.stderr)
        metadata['commands'].append({'label':label,'argv':command,'expected_exit':expected,'exit':p.returncode,'seconds':time.perf_counter()-start})
        (out/'run-metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
        if p.returncode!=expected: raise RuntimeError(label+' wrong exit')
        return json.loads((out/(label+'.json')).read_text())
    old=run('before-four',ORIGINAL/'reproduce_false_clear.py',ORIGINAL/'sweep-e5079db.py',1,('--regression-gate',))
    new=run('after-four',ORIGINAL/'reproduce_false_clear.py',SOURCE,0,('--regression-gate',))
    stress=run('after-boundary18000',HERE/'stress_with_hashes.py',SOURCE)
    check_stress(stress)
    baseline_stress=run('before-boundary18000',HERE/'stress_with_hashes.py',ORIGINAL/'sweep-e5079db.py')
    if baseline_stress['candidate_counts']!={'PROJECTED_OVERLAP':17731,'UNRESOLVED_2D':129,'PROJECTED_CLEAR':140}: raise ValueError('baseline mismatch')
    if baseline_stress['input_corpus_sha256']!=stress['input_corpus_sha256']: raise ValueError('different boundary inputs')
    ordinary=run('after-ordinary',ORIGINAL/'independent_checks.py',SOURCE)
    # Immutable legacy script's evaluated_head is historical metadata, not this run.
    ordinary['legacy_script_evaluated_head']=ordinary.pop('evaluated_head',None)
    ordinary['evaluated_source_hashes']=metadata['source_hashes']
    ordinary['evaluated_checkout_head']=metadata['head']
    (out/'after-ordinary.json').write_text(json.dumps(ordinary,indent=2)+'\n')
    if ordinary.get('baseline_suite_pass') is not True: raise ValueError('ordinary checks failed')
    controls=[]
    for name,mutate in [('false-clear',lambda r:r['candidate_counts'].update(PROJECTED_CLEAR=1)),
                        ('partial',lambda r:r.update(total_cases=17999)),
                        ('witness-missing',lambda r:r.update(all_cases_have_independent_strict_overlap_witness=False))]:
        damaged=json.loads(json.dumps(stress));mutate(damaged)
        try: check_stress(damaged)
        except ValueError: controls.append({'fault':name,'rejected':True})
        else: raise ValueError('gate false acceptance: '+name)
    metadata.update(completed_at=datetime.now(timezone.utc).isoformat(),gate_pass=True,negative_controls=controls,
        outcomes=[{'fixture':r['fixture'],'before':o['candidate']['status'],'after':r['candidate']['status']}
                  for o,r in zip(old['reports'],new['reports'])])
    (out/'run-metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    manifest={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(out.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.json'}
    (out/'SHA256SUMS.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'gate_pass':True,'outcomes':metadata['outcomes'],'boundary_before':baseline_stress['candidate_counts'],
       'boundary_after':stress['candidate_counts'],'same_input_sha256':stress['input_corpus_sha256'],
       'ordinary_suite_pass':ordinary['baseline_suite_pass'],'negative_controls':controls}))

if __name__=='__main__':main()
