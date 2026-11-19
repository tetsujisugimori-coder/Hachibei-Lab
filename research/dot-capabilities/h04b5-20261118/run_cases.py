"""Run fixed synthetic oracle in isolated processes with bounded execution."""
import json,sys,subprocess,hashlib,platform,datetime,pathlib
p=pathlib.Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 cases=json.loads((p/'cases.json').read_text())['cases']
 if not cases or len({c['id'] for c in cases})!=len(cases):raise ValueError('empty/duplicate cases')
 rows=[]
 for c in cases:
  raw=json.dumps(c['input'],ensure_ascii=False,sort_keys=True).encode();start=datetime.datetime.now(datetime.timezone.utc).isoformat()
  try:
   r=subprocess.run([sys.executable,str(p/'check.py')],input=raw,capture_output=True,timeout=5)
   actual=json.loads(r.stdout);ok=actual==c['expected'] and r.returncode==(0 if actual['status']=='PASS' else 2)
   row={'stdout':r.stdout.decode(),'stderr':r.stderr.decode(),'exit_code':r.returncode,'actual':actual,'result':'PASS' if ok else 'FAIL'}
  except (subprocess.TimeoutExpired,ValueError) as e:row={'result':'FAIL','error':str(e)}
  rows.append(dict(id=c['id'],input_sha256=sha(raw),expected=c['expected'],started_at=start,ended_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),timeout_seconds=5,retries=0,**row))
 out={'kind':'SYNTHETIC_ONLY','checker_sha256':sha((p/'check.py').read_bytes()),'oracle_sha256':sha((p/'cases.json').read_bytes()),'environment':platform.platform(),'python':sys.version,'actor':'implementation A','cases':rows,'pass':sum(r['result']=='PASS' for r in rows),'total':len(rows),'experiment_start':'BLOCKED','permit':False}
 print(json.dumps(out,ensure_ascii=False,indent=2));return 0 if out['pass']==out['total'] else 1
if __name__=='__main__':sys.exit(main())
