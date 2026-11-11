"""Synthetic fixtures only. Owned artifacts retained; no shared cleanup."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('guard',Path(__file__).resolve().parents[1]/'tools/capacity_guard.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
ROOT=Path(os.environ.get('CAPACITY_TEST_ROOT',Path.cwd()/'.capacity-test-runs')).resolve()
ROOT.mkdir(parents=True,exist_ok=True)

def fresh(): return Path(tempfile.mkdtemp(prefix='synthetic-',dir=ROOT))
def git(p,*args): return subprocess.check_output(['git','-C',str(p),*args],stderr=subprocess.DEVNULL)
def repository():
    p=fresh();git(p,'init','-b','main');git(p,'config','user.name','Synthetic');git(p,'config','user.email','test@example.invalid')
    (p/'file').write_text('one\n');git(p,'add','file');git(p,'commit','-m','synthetic')
    git(p,'update-ref','refs/remotes/origin/main','HEAD');git(p,'config','remote.origin.url','.')
    git(p,'config','remote.origin.fetch','+refs/heads/*:refs/remotes/origin/*')
    git(p,'config','branch.main.remote','origin');git(p,'config','branch.main.merge','refs/heads/main');return p

def backup(p):
    b=fresh(); bundle=b/'snapshot.bundle';git(p,'bundle','create',str(bundle),'--all')
    def row(f): return {'path':str(f),'sha256':g.file_hash(f)}
    data={'head':git(p,'rev-parse','HEAD').decode().strip(),'bundle':row(bundle),'untracked':[]}
    for key,args in [('staged_patch',['--cached']),('worktree_patch',[])]:
        f=b/key;f.write_bytes(g.git(p,'diff',*args,'--binary','--no-ext-diff','--no-textconv'));data[key]=row(f)
    for i,name in enumerate(g.git(p,'ls-files','--others','--exclude-standard','-z').split(b'\0')):
        if name:
            source=os.fsdecode(name);f=b/str(i);f.write_bytes((p/source).read_bytes());data['untracked'].append({'source':source,**row(f)})
    m=b/'manifest.json';m.write_text(json.dumps(data));return m

class Thresholds(unittest.TestCase):
    def test_boundaries(self):
        for used,free,expected in [(79,20000,'OK'),(80,20000,'WARN'),(95,20000,'STOP'),(1,10000,'WARN'),(1,1000,'STOP'),(1,1001,'WARN')]:
            with self.subTest(used=used,free=free):self.assertEqual(g.classify(used,free,10000,1000,g.DEFAULT),expected)
    def test_invalid_policy(self):
        for data in [{'other':{}},{'workspace':{'other':1}},{'workspace':{'warn_percent':True}},{'workspace':{'stop_bytes':-1}},{'workspace':{'warn_percent':95}},{'workspace':{'stop_percent':101}},{'workspace':{'stop_inodes':10001}},{'workspace':{'stop_bytes':float('nan')}},{'workspace':[]}]:
            f=fresh()/'policy';f.write_text(json.dumps(data))
            with self.subTest(data=data),self.assertRaises(ValueError):g.policies(f)
    def test_independent_policies(self):
        f=fresh()/'p';f.write_text('{"workspace":{"warn_percent":85}}');p=g.policies(f)
        self.assertEqual((p['workspace']['warn_percent'],p['shared_tmp']['warn_percent']),(85,80))
    def test_missing_path_unknown(self):self.assertEqual(g.sample(fresh()/'missing',g.DEFAULT)['state'],'UNKNOWN')
    def test_inode_unavailable(self):
        s=os.statvfs(ROOT)
        class S:
            f_frsize=s.f_frsize;f_bsize=s.f_bsize;f_blocks=s.f_blocks;f_bfree=s.f_bfree;f_bavail=s.f_bavail;f_files=0;f_ffree=0;f_favail=0
        with patch.object(g.os,'statvfs',return_value=S()):self.assertEqual(g.sample(ROOT,g.DEFAULT)['state'],'UNKNOWN')
    def test_same_device_not_sum(self):
        with patch.object(g,'sample',return_value={'state':'WARN','device':1,'disk':'OK','inode':'WARN'}):r=g.measure(ROOT,g.policies())
        self.assertTrue(r['same_device']);self.assertEqual(set(r['volumes']),{'shared_tmp','workspace'});self.assertNotIn('total_available_bytes',r)

class Preservation(unittest.TestCase):
    def test_clean_cached_not_remote_proof(self):
        r=g.preservation(repository());self.assertEqual(r['state'],'CLEAN_CACHED_UPSTREAM');self.assertEqual(r['remote_freshness'],'UNKNOWN')
    def test_no_upstream(self):
        p=repository();git(p,'config','--unset','branch.main.remote');self.assertEqual(g.preservation(p)['state'],'NEEDS_PRESERVATION')
    def test_local_upstream_is_not_submission(self):
        p=repository();git(p,'branch','local-backup');git(p,'branch','--set-upstream-to=local-backup');self.assertEqual(g.preservation(p)['state'],'NEEDS_PRESERVATION')
    def test_ahead(self):
        p=repository();(p/'file').write_text('two');git(p,'commit','-am','two');self.assertEqual(g.preservation(p)['ahead_of_cached_upstream'],1)
    def test_dirty(self):
        p=repository();(p/'file').write_text('two');self.assertEqual(g.preservation(p)['state'],'NEEDS_PRESERVATION')
    def test_complete_local_artifacts(self):
        p=repository();(p/'file').write_text('stage');git(p,'add','file');(p/'file').write_text('work');(p/'new').write_text('new')
        r=g.preservation(p,backup(p));self.assertEqual(r['state'],'LOCAL_ARTIFACTS_VERIFIED');self.assertEqual(r['restart_durability'],'UNKNOWN');self.assertEqual(r['restore_test'],'NOT_RUN')
    def test_same_status_changed_content(self):
        p=repository();(p/'file').write_text('one edit');m=backup(p);(p/'file').write_text('two edit');self.assertEqual(g.preservation(p,m)['state'],'UNKNOWN')
    def test_missing_untracked(self):
        p=repository();(p/'new').write_text('new');m=backup(p);d=json.loads(m.read_text());d['untracked']=[];m.write_text(json.dumps(d));self.assertEqual(g.preservation(p,m)['state'],'UNKNOWN')
    def test_changed_untracked(self):
        p=repository();(p/'new').write_text('new');m=backup(p);(p/'new').write_text('changed');self.assertEqual(g.preservation(p,m)['state'],'UNKNOWN')
    def test_tampered_bundle(self):
        p=repository();m=backup(p);d=json.loads(m.read_text());Path(d['bundle']['path']).write_bytes(b'bad');self.assertEqual(g.preservation(p,m)['state'],'UNKNOWN')
    def test_wrong_head(self):
        p=repository();m=backup(p);d=json.loads(m.read_text());d['head']='0'*40;m.write_text(json.dumps(d));self.assertEqual(g.preservation(p,m)['state'],'UNKNOWN')
    def test_untracked_symlink(self):
        p=repository();(p/'link').symlink_to(p/'file');self.assertEqual(g.preservation(p)['state'],'UNKNOWN')
    def test_submodule(self):
        p=repository();h=git(p,'rev-parse','HEAD').decode().strip();git(p,'update-index','--add','--cacheinfo','160000,'+h+',module');self.assertEqual(g.preservation(p)['state'],'UNKNOWN')
    def test_subdirectory(self):
        p=repository();(p/'sub').mkdir();(p/'outside').write_text('not backed up');self.assertEqual(g.preservation(p/'sub')['state'],'UNKNOWN')
    def test_live_file_and_hardlink_are_not_backup(self):
        for hardlink in (False,True):
            p=repository();(p/'new').write_text('new');m=backup(p);d=json.loads(m.read_text());f=p/'new'
            if hardlink:f=fresh()/'link';os.link(p/'new',f)
            d['untracked'][0]['path']=str(f);m.write_text(json.dumps(d));self.assertEqual(g.preservation(p,m)['state'],'UNKNOWN')
    def test_non_git(self):self.assertEqual(g.preservation(fresh())['state'],'UNKNOWN')

class Runner(unittest.TestCase):
    def call(self,w,r,cmd,states=('OK',)):
        values=[{'state':s} for s in states]
        with patch.object(g,'measure',side_effect=values if len(values)>1 else None,return_value=values[0]),contextlib.redirect_stdout(io.StringIO()):
            return g.execute(w,r,w/'runs','test',cmd,g.policies(),interval=.1)
    def test_reject_paths(self):
        w=fresh();outside=fresh();(w/'link').symlink_to(outside,target_is_directory=True)
        for path,task in [(w,'x'),(outside/'r','x'),(Path('/tmp/x'),'x'),(w/'link/r','x'),(w/'r','../x')]:
            with self.subTest(path=path),self.assertRaises(ValueError):g.run_directory(w,path,task)
    def test_repo_device_mismatch(self):
        from types import SimpleNamespace
        with patch.object(g.os,'stat',side_effect=[SimpleNamespace(st_dev=1),SimpleNamespace(st_dev=2)]),self.assertRaises(ValueError):
            g.execute(ROOT,ROOT,ROOT/'r','t',['true'],g.policies())
    def test_nested_run_mount_mismatch(self):
        w=fresh();other=w/'other';other.mkdir();original=os.stat
        def changed(path,*args,**kwargs):
            result=original(path,*args,**kwargs)
            if str(path)==str(other):
                values=list(result);values[2]+=1000;return os.stat_result(values)
            return result
        with patch.object(g.os,'stat',changed),self.assertRaises(ValueError):g.run_directory(w,other/'run','x')
    def test_stop_never_starts(self):
        w=fresh();target=w/'not-created';code=f'open({str(target)!r},"w").write("bad")'
        self.assertEqual(self.call(w,repository(),[sys.executable,'-c',code],('STOP',)),20);self.assertFalse(target.exists())
        self.assertIn('capacity_STOP',next((w/'runs').glob('*/events.jsonl')).read_text())
    def test_unknown_never_starts(self):self.assertEqual(self.call(fresh(),repository(),['not-executed'],('UNKNOWN',)),21)
    def test_unpreserved_never_starts(self):
        p=repository();(p/'file').write_text('dirty');self.assertEqual(self.call(fresh(),p,['not-executed']),22)
    def test_scoped_environment_exit(self):
        w=fresh();out=w/'env.json';parent=os.environ.get('TMPDIR')
        code='import os,json;open('+repr(str(out))+',"w").write(json.dumps({k:os.environ.get(k) for k in ["TMPDIR","NODE_COMPILE_CACHE","npm_config_cache","PLAYWRIGHT_BROWSERS_PATH"]}));raise SystemExit(7)'
        self.assertEqual(self.call(w,repository(),[sys.executable,'-c',code]),7);d=json.loads(out.read_text())
        self.assertTrue(Path(d['TMPDIR']).is_relative_to(w/'runs'));self.assertEqual(os.environ.get('TMPDIR'),parent)
        self.assertEqual(d['PLAYWRIGHT_BROWSERS_PATH'],os.environ.get('PLAYWRIGHT_BROWSERS_PATH'));self.assertTrue(out.exists())
    def test_midrun_stop_only_owned_process(self):
        other=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],start_new_session=True)
        try:
            self.assertEqual(self.call(fresh(),repository(),[sys.executable,'-c','import time;time.sleep(30)'],('OK','STOP')),20);self.assertIsNone(other.poll())
        finally:other.terminate();other.wait(timeout=5)
    def test_log_failure_kills_child(self):
        original=g.Recorder.write;pids=[]
        def fail(recorder,kind,**values):
            if kind=='started':pids.append(values['pid']);raise OSError('synthetic ENOSPC')
            original(recorder,kind,**values)
        with patch.object(g.Recorder,'write',fail),contextlib.redirect_stderr(io.StringIO()):self.assertEqual(self.call(fresh(),repository(),[sys.executable,'-c','import time;time.sleep(30)']),23)
        with self.assertRaises(ProcessLookupError):os.kill(pids[0],0)
    def test_background_descendant_stopped_on_parent_exit(self):
        w=fresh();pidfile=w/'grandchild.pid'
        code='import subprocess,sys; p=subprocess.Popen([sys.executable,"-c","import time;time.sleep(30)"]);open('+repr(str(pidfile))+',"w").write(str(p.pid))'
        self.assertEqual(self.call(w,repository(),[sys.executable,'-c',code]),0)
        pid=int(pidfile.read_text());state=Path('/proc')/str(pid)/'stat'
        self.assertTrue(not state.exists() or state.read_text().split()[2]=='Z')
    def test_signal_stops_owned_child(self):
        self.assertEqual(self.call(fresh(),repository(),[sys.executable,'-c','import os,signal,time;os.kill(os.getppid(),signal.SIGTERM);time.sleep(30)']),143)
    def test_event_log_is_bounded(self):
        r=g.Recorder(fresh())
        try:
            r.bytes_written=g.LIMIT
            with self.assertRaises(OSError):r.write('too_large')
        finally:r.close()
    def test_spawn_failure(self):
        with contextlib.redirect_stderr(io.StringIO()):self.assertEqual(self.call(fresh(),repository(),['/no/such/command']),23)
    def test_invalid_interval(self):
        for interval in (0,float('nan'),301):
            with self.assertRaises(ValueError):g.execute(ROOT,ROOT,ROOT/'r','t',['true'],g.policies(),interval=interval)
    def test_cli_options_after_action(self):
        with patch.object(g,'measure',return_value={'state':'OK'}),contextlib.redirect_stdout(io.StringIO()):self.assertEqual(g.main(['check','--workspace',str(ROOT),'--repo',str(repository())]),0)

if __name__=='__main__':unittest.main()
