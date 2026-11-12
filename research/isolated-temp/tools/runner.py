"""Single opt-in Linux probe; private raw outputs. Never deletes or retries."""
import argparse, datetime, hashlib, json, os, pathlib, shutil, subprocess, sys
KEYS=('TMPDIR','TMP','TEMP','NODE_COMPILE_CACHE','XDG_CACHE_HOME')
def snapshot(p):
 s=os.statvfs(p)
 return dict(device=os.stat(p).st_dev,available=s.f_bavail*s.f_frsize,free_inodes=s.f_favail)
def validate_root(p):
 p=pathlib.Path(p)
 if not p.is_absolute() or p.is_symlink(): raise ValueError('absolute non-symlink root required')
 resolved=p.resolve()
 if resolved==pathlib.Path('/tmp') or pathlib.Path('/tmp') in resolved.parents: raise ValueError('shared /tmp forbidden')
 if p.exists(): raise ValueError('fresh directory required; never overwrite')
 if snapshot(p.parent)['available']<1024**3: raise ValueError('less than 1 GiB safety margin')
 return p
def outcome(code,stdout):
 try:
  events=[json.loads(x) for x in stdout.splitlines()]
  if code!=0 or [e['phase'] for e in events]!=['temp','dom','closed']: return 'BLOCKED'
  temp,dom,_=events
  if temp.get('readback')!='isolated-temp-42\n' or temp.get('path')!='probe.txt': return 'BLOCKED'
  if dom.get('actual')!='isolated-temp-42' or not isinstance(dom.get('profileFiles'),list) or not dom['profileFiles']: return 'BLOCKED'
  return 'PASS'
 except (ValueError,KeyError,TypeError): return 'BLOCKED'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--chromium',required=True);a=ap.parse_args()
 root=validate_root(a.root); binary=pathlib.Path(a.chromium)
 if not binary.is_file() or not os.access(binary,os.X_OK): raise ValueError('existing executable Chromium required')
 before={k:os.environ.get(k) for k in KEYS}; capacities={p:snapshot(p) for p in ('/tmp',str(root.parent))}
 root.mkdir();temp=root/'temp';temp.mkdir()
 env=os.environ.copy();env.update({k:str(temp) for k in ('TMPDIR','TMP','TEMP')});env.update(NODE_COMPILE_CACHE=str(temp/'node-cache'),XDG_CACHE_HOME=str(temp/'xdg-cache'),PROBE_CHROMIUM=str(binary))
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 cmd=['node',str(pathlib.Path(__file__).with_name('probe.cjs'))]
 try:
  r=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=45);code,stdout,stderr=r.returncode,r.stdout,r.stderr
 except subprocess.TimeoutExpired as e:
  code=None;stdout=(e.stdout or b'').decode() if isinstance(e.stdout,bytes) else (e.stdout or '');stderr=(e.stderr or b'').decode() if isinstance(e.stderr,bytes) else (e.stderr or '');stderr+='\nTimeoutExpired: '+str(e)
 (root/'stdout.log').write_text(stdout);(root/'stderr.log').write_text(stderr)
 files=[]; total=0; inventory_complete=True
 for p in temp.rglob('*'):
  if p.is_symlink() or not p.is_file(): continue
  size=p.stat().st_size
  if len(files)>=256 or size>8*1024**2 or total+size>32*1024**2:
   inventory_complete=False;break
  total+=size
  files.append(dict(path=str(p.relative_to(root)),bytes=size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
 process_names=[]
 for p in pathlib.Path('/proc').glob('[0-9]*/comm'):
  try: process_names.append(p.read_text().strip())
  except OSError: pass
 observed_probe=next((f for f in files if f['path']=='temp/probe.txt'),None)
 probe_ok=observed_probe is not None and observed_probe['sha256']==hashlib.sha256(b'isolated-temp-42\n').hexdigest()
 after={k:os.environ.get(k) for k in KEYS}
 report=dict(start_utc=start,end_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),command=cmd,exit_code=code,result=outcome(code,stdout) if before==after and inventory_complete and probe_ok else 'BLOCKED',parent_env_before=before,parent_env_after=after,parent_unchanged=before==after,capacity_before=capacities,capacity_after={p:snapshot(p) for p in capacities},files=files,quota_independence='UNKNOWN',untracked_browser_files='UNKNOWN',process_scope='PID namespace snapshot only; global residual processes UNKNOWN',visible_process_names_after=process_names,inventory_complete=inventory_complete)
 (root/'result.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));return 0 if report['result']=='PASS' and before==after else 2
if __name__=='__main__':
 try: sys.exit(main())
 except (OSError,ValueError) as e: print(type(e).__name__+': '+str(e),file=sys.stderr);sys.exit(2)
