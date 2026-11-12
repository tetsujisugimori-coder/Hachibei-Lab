"""Single opt-in Linux probe; private raw outputs. Never deletes or retries."""
import argparse, datetime, hashlib, json, os, pathlib, shutil, subprocess, sys
import selectors, signal, stat, time, multiprocessing
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

# Narrow adaptation of PR #22 owned process-group control. No global PID kill.
# Deliberate setsid/daemon escape is outside this cooperative fixture's scope.
def capture(command, env, timeout=45, output_limit=1024*1024, stop_requested=lambda: False):
 if timeout <= 0 or output_limit < 1: raise ValueError('positive bounds required')
 p=subprocess.Popen(command,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
 start=time.monotonic(); events=[]; reasons=[]; output=[bytearray(),bytearray()]
 sel=selectors.DefaultSelector()
 for index,pipe in enumerate((p.stdout,p.stderr)):
  os.set_blocking(pipe.fileno(),False);sel.register(pipe,selectors.EVENT_READ,index)
 def event(kind,**kw): events.append(dict(event=kind,elapsed=time.monotonic()-start,**kw))
 event('started',pid=p.pid,pgid=p.pid)
 try:
  while sel.get_map():
   if stop_requested(): reasons.append('STOP_REQUEST');break
   if time.monotonic()-start>=timeout: reasons.append('TIMEOUT');break
   # Parent exit does not imply descendants ended. Do not wait on inherited pipes.
   if p.poll() is not None:
    event('parent_exit',code=p.returncode)
    ready=sel.select(0)
    if not ready: break
   else: ready=sel.select(min(.02,max(0,timeout-(time.monotonic()-start))))
   for key,_ in ready:
    chunk=os.read(key.fileobj.fileno(),65536)
    if not chunk: sel.unregister(key.fileobj);continue
    room=output_limit-len(output[key.data]);output[key.data].extend(chunk[:room])
    if len(chunk)>room:
     reasons.append('STDOUT_LIMIT' if key.data==0 else 'STDERR_LIMIT');break
   if reasons: break
  if p.poll() is None and not reasons:
   while p.poll() is None and time.monotonic()-start<timeout and not stop_requested(): time.sleep(.01)
   if p.poll() is None: reasons.append('STOP_REQUEST' if stop_requested() else 'TIMEOUT')
 finally:
  event('stop_requested',reason=reasons or ['POST_EXIT_GROUP_CHECK'])
  try:
   if p.poll() is not None:
    try:
     os.killpg(p.pid,0);reasons.append('DESCENDANTS_AFTER_PARENT_EXIT')
    except ProcessLookupError: pass
   os.killpg(p.pid,signal.SIGTERM);event('group_signal',signal='SIGTERM')
   end=time.monotonic()+.2
   while time.monotonic()<end:
    p.poll()
    try: os.killpg(p.pid,0)
    except ProcessLookupError: break
    time.sleep(.01)
   try: os.killpg(p.pid,signal.SIGKILL);event('group_signal',signal='SIGKILL')
   except ProcessLookupError: pass
  except ProcessLookupError: pass
  except OSError as e: reasons.append('STOP_ERROR');event('stop_error',error=str(e))
  try: p.wait(timeout=1);event('parent_reaped',code=p.returncode)
  except subprocess.TimeoutExpired: reasons.append('REAP_TIMEOUT')
  try:
   os.killpg(p.pid,0);reasons.append('GROUP_REMAINS_OR_ZOMBIE');residual='OBSERVED_GROUP'
  except ProcessLookupError: residual='OWNED_GROUP_ABSENT'
  except OSError: reasons.append('RESIDUAL_UNKNOWN');residual='UNKNOWN'
  event('residual_check',result=residual,scope='owned group in current PID namespace; escaped descendants UNKNOWN')
  sel.close();p.stdout.close();p.stderr.close()
 return dict(code=p.returncode,stdout=bytes(output[0]),stderr=bytes(output[1]),reasons=reasons,events=events,residual=residual)


def _inventory(root, max_entries=256, max_depth=8, max_bytes=32*1024**2, max_file_bytes=8*1024**2, seconds=5):
 """Bounded regular-file reader. No symlink traversal or special-file reads.
 Deadline checks are cooperative between OS calls; blocked kernel I/O is not bounded.
 """
 root=pathlib.Path(root);start=time.monotonic();files=[];total=0;entries=0
 def check():
  if time.monotonic()-start>=seconds: raise ValueError('SCAN_TIME_LIMIT')
 def walk(directory,depth):
  nonlocal total,entries
  check()
  with os.scandir(directory) as it:
   for entry in it:
    check();entries+=1
    if entries>max_entries: raise ValueError('SCAN_ENTRY_LIMIT')
    st=entry.stat(follow_symlinks=False)
    if stat.S_ISLNK(st.st_mode): raise ValueError('SCAN_SYMLINK')
    if stat.S_ISDIR(st.st_mode):
     if depth>=max_depth: raise ValueError('SCAN_DEPTH_LIMIT')
     walk(entry.path,depth+1);continue
    if not stat.S_ISREG(st.st_mode): raise ValueError('SCAN_SPECIAL_FILE')
    if st.st_size>max_file_bytes: raise ValueError('SCAN_FILE_LIMIT')
    digest=hashlib.sha256();count=0
    fd=os.open(entry.path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as f:
     opened=os.fstat(f.fileno())
     if not stat.S_ISREG(opened.st_mode) or (opened.st_dev,opened.st_ino)!=(st.st_dev,st.st_ino): raise ValueError('SCAN_CHANGED_FILE')
     while True:
      check();chunk=f.read(min(65536,max_bytes-total+1,max_file_bytes-count+1))
      if not chunk: break
      count+=len(chunk);total+=len(chunk)
      if count>max_file_bytes or total>max_bytes: raise ValueError('SCAN_READ_LIMIT')
      digest.update(chunk)
     if os.fstat(f.fileno()).st_size!=count or count!=st.st_size: raise ValueError('SCAN_CHANGED_FILE')
    files.append(dict(path=str(pathlib.Path(entry.path).relative_to(root.parent)),bytes=count,sha256=digest.hexdigest()))
 try: walk(root,0);check();return dict(files=files,complete=True,reason=None,entries=entries,bytes_read=total)
 except (OSError,ValueError) as e: return dict(files=files,complete=False,reason=str(e),entries=entries,bytes_read=total)


def inventory(root, **limits):
 """Scan in a dedicated helper so a stalled directory/read syscall cannot hold runner."""
 seconds=limits.get('seconds',5)
 if seconds<=0: return dict(files=[],complete=False,reason='SCAN_TIME_LIMIT',entries=0,bytes_read=0)
 ctx=multiprocessing.get_context('fork');reader,writer=ctx.Pipe(duplex=False)
 def scan_child():
  reader.close()
  try: writer.send(_inventory(root,**limits))
  finally: writer.close()
 proc=ctx.Process(target=scan_child);proc.start();writer.close()
 try:
  if reader.poll(seconds):
   try: result=reader.recv()
   except EOFError: result=dict(files=[],complete=False,reason='SCAN_WORKER_FAILED',entries=0,bytes_read=0)
  else: result=dict(files=[],complete=False,reason='SCAN_TIME_LIMIT',entries=None,bytes_read=None)
 finally:
  reader.close();proc.join(.1)
  if proc.is_alive(): proc.terminate();proc.join(.2)
  if proc.is_alive(): proc.kill();proc.join(.2)
 if proc.is_alive(): result.update(complete=False,reason='SCAN_STOP_UNCONFIRMED')
 return result


def save(path,data):
 with open(path,'xb') as f: f.write(data);f.flush();os.fsync(f.fileno())
 if pathlib.Path(path).read_bytes()!=data: raise OSError('evidence readback mismatch')


def read_completion(root):
 """Consumers MUST call this; result.json alone is always provisional/non-PASS."""
 root=pathlib.Path(root)
 try:
  receipt=json.loads((root/'completion.json').read_bytes())
  if set(receipt.get('sha256',{}))!={'stdout.log','stderr.log','result.json'}: return 'BLOCKED'
  for name,digest in receipt['sha256'].items():
   if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest: return 'BLOCKED'
  provisional=json.loads((root/'result.json').read_bytes())
  if provisional.get('result')!='PENDING' or provisional.get('evidence_saved') is not False: return 'BLOCKED'
  candidate=provisional.get('candidate_result')
  if candidate not in ('PASS','BLOCKED') or receipt.get('candidate_result')!=candidate: return 'BLOCKED'
  return candidate
 except (OSError,ValueError,KeyError,TypeError): return 'BLOCKED'


def execute(root, command, extra_env=None, timeout=45, output_limit=1024*1024, scan_limits=None, stop_requested=lambda:False):
 root=validate_root(root);before={k:os.environ.get(k) for k in KEYS}
 capacities={p:snapshot(p) for p in ('/tmp',str(root.parent))}
 root.mkdir();temp=root/'temp';temp.mkdir()
 env=os.environ.copy();env.update(extra_env or {})
 env.update({k:str(temp) for k in ('TMPDIR','TMP','TEMP')});env.update(NODE_COMPILE_CACHE=str(temp/'node-cache'),XDG_CACHE_HOME=str(temp/'xdg-cache'))
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 r=capture(command,env,timeout,output_limit,stop_requested)
 scan=inventory(temp,**(scan_limits or {}));after={k:os.environ.get(k) for k in KEYS}
 probe=next((f for f in scan['files'] if f['path']=='temp/probe.txt'),None)
 probe_ok=probe is not None and probe['sha256']==hashlib.sha256(b'isolated-temp-42\n').hexdigest()
 reasons=list(r['reasons'])
 if stop_requested() and 'STOP_REQUEST' not in reasons: reasons.append('STOP_REQUEST')
 if not scan['complete']: reasons.append(scan['reason'])
 if before!=after: reasons.append('PARENT_ENV_CHANGED')
 if not probe_ok: reasons.append('PROBE_MISSING_OR_MISMATCH')
 if outcome(r['code'],r['stdout'].decode(errors='replace'))!='PASS': reasons.append('PROTOCOL_OR_EXIT_FAILURE')
 report=dict(start_utc=start,end_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),command=command,exit_code=r['code'],result='BLOCKED' if reasons else 'PASS',reasons=reasons,parent_env_before=before,parent_env_after=after,parent_unchanged=before==after,capacity_before=capacities,capacity_after={p:snapshot(p) for p in capacities},files=scan['files'],inventory_complete=scan['complete'],scan=scan,process_events=r['events'],process_scope='owned process group only; escaped descendants/global residual UNKNOWN',quota_independence='UNKNOWN',untracked_browser_files='UNKNOWN',limits=dict(timeout=timeout,output_bytes_per_stream=output_limit,scan=scan_limits or 'defaults'),evidence_saved=False)
 try:
  save(root/'stdout.log',r['stdout']);save(root/'stderr.log',r['stderr'])
  provisional=dict(report,result='PENDING',candidate_result=report['result'],evidence_saved=False)
  save(root/'result.json',json.dumps(provisional,indent=2).encode())
  receipt=dict(candidate_result=report['result'],sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in ('stdout.log','stderr.log','result.json')},consumer='read_completion(root); result.json alone is never final')
  # Validate the candidate bytes before publishing a completion link. A failed
  # write/fsync/readback leaves only a non-authoritative .candidate file.
  save(root/'completion.candidate.json',json.dumps(receipt,indent=2).encode())
  os.link(root/'completion.candidate.json',root/'completion.json')
  report['evidence_saved']=True
  report['completion_receipt']='completion.json'
 except OSError as e:
  report.update(result='BLOCKED',evidence_saved=False);report['reasons'].append('EVIDENCE_SAVE_FAILURE: '+str(e))
  # Do not overwrite any conflicting file; stderr/returned report is fallback only.
  print(json.dumps(report),file=sys.stderr)
 return report


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--chromium',required=True);a=ap.parse_args()
 binary=pathlib.Path(a.chromium)
 if not binary.is_file() or not os.access(binary,os.X_OK): raise ValueError('existing executable Chromium required')
 stopped=[];handlers={}
 for sig in (signal.SIGTERM,signal.SIGINT):
  handlers[sig]=signal.signal(sig,lambda s,f:stopped.append(s))
 try:
  report=execute(a.root,['node',str(pathlib.Path(__file__).with_name('probe.cjs'))],extra_env={'PROBE_CHROMIUM':str(binary)},stop_requested=lambda:bool(stopped))
 finally:
  for sig,handler in handlers.items(): signal.signal(sig,handler)
 print(json.dumps(report));return 0 if report['result']=='PASS' else 2
if __name__=='__main__':
 try: sys.exit(main())
 except (OSError,ValueError) as e: print(type(e).__name__+': '+str(e),file=sys.stderr);sys.exit(2)
