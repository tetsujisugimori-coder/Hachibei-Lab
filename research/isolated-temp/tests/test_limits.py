"""Real runner subprocess fixtures; not browser acceptance. Files retained per run."""
import importlib.util,json,os,pathlib,sys,time,unittest,uuid
from unittest.mock import patch
p=pathlib.Path(__file__).parents[1]/'tools/runner.py'
s=importlib.util.spec_from_file_location('bounded_runner',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
BASE=pathlib.Path(os.environ.get('ISOLATED_TEST_ROOT',str(pathlib.Path.cwd()/'.isolated-test-evidence')))
BASE.mkdir(exist_ok=True,parents=True)
GOOD="""import os,pathlib,json
pathlib.Path(os.environ['TMPDIR'],'probe.txt').write_text('isolated-temp-42\\n')
for e in [{'phase':'temp','path':'probe.txt','readback':'isolated-temp-42\\n'},{'phase':'dom','actual':'isolated-temp-42','profileFiles':['Preferences']},{'phase':'closed'}]: print(json.dumps(e),flush=True)
"""
class Limits(unittest.TestCase):
 def run_case(self,source,**kw):
  root=BASE/str(uuid.uuid4())
  before=dict(os.environ)
  result=m.execute(root,[sys.executable,'-B','-c',source],timeout=kw.pop('timeout',1),**kw)
  self.assertEqual(dict(os.environ),before)
  if result['evidence_saved']: self.assertEqual(m.read_completion(root),result['result'])
  return result,root
 def test_normal(self):
  r,_=self.run_case(GOOD);self.assertEqual(r['result'],'PASS')
 def test_missing(self):
  r,_=self.run_case('print("{}")');self.assertEqual(r['result'],'BLOCKED')
 def test_nonzero(self):
  r,_=self.run_case(GOOD+'raise SystemExit(3)');self.assertEqual(r['result'],'BLOCKED')
 def test_stdout_excess(self):
  r,root=self.run_case('print("x"*10000)',output_limit=512)
  self.assertIn('STDOUT_LIMIT',r['reasons']);self.assertLessEqual((root/'stdout.log').stat().st_size,512)
 def test_stderr_excess(self):
  r,root=self.run_case('import sys;sys.stderr.write("x"*10000)',output_limit=512)
  self.assertIn('STDERR_LIMIT',r['reasons']);self.assertLessEqual((root/'stderr.log').stat().st_size,512)
 def test_timeout(self):
  r,_=self.run_case('import time;time.sleep(10)',timeout=.1);self.assertIn('TIMEOUT',r['reasons'])
 def test_stop_request(self):
  start=time.monotonic();r,_=self.run_case('import time;time.sleep(10)',stop_requested=lambda:time.monotonic()-start>.1)
  self.assertIn('STOP_REQUEST',r['reasons'])
 def test_parent_early_exit_and_resistant_descendant(self):
  src=GOOD+"\nimport subprocess,sys\nsubprocess.Popen([sys.executable,'-c','import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(10)'])\nimport time;time.sleep(.1)\n"
  start=time.monotonic();r,_=self.run_case(src)
  # A descendant surviving parent means protocol alone cannot earn PASS.
  self.assertEqual(r['result'],'BLOCKED');self.assertLess(time.monotonic()-start,3)
  self.assertTrue(any(e.get('signal')=='SIGKILL' for e in r['process_events']))
 def test_scan_entries(self):
  r,_=self.run_case(GOOD,scan_limits={'max_entries':0});self.assertFalse(r['inventory_complete']);self.assertEqual(r['result'],'BLOCKED')
 def test_scan_depth(self):
  r,_=self.run_case(GOOD+"\npathlib.Path(os.environ['TMPDIR'],'a').mkdir()",scan_limits={'max_depth':0})
  self.assertEqual(r['result'],'BLOCKED')
 def test_scan_read_bytes(self):
  r,_=self.run_case(GOOD,scan_limits={'max_bytes':1});self.assertEqual(r['result'],'BLOCKED')
 def test_scan_timeout(self):
  r,_=self.run_case(GOOD,scan_limits={'seconds':.000001});self.assertEqual(r['result'],'BLOCKED')
 def test_scan_special_file(self):
  r,_=self.run_case(GOOD+"\nos.mkfifo(pathlib.Path(os.environ['TMPDIR'],'pipe'))")
  self.assertEqual(r['result'],'BLOCKED');self.assertIn('SCAN_SPECIAL_FILE',r['reasons'])
 def test_scan_read_failure(self):
  with patch.object(m.os,'scandir',side_effect=PermissionError('injected scan denial')):
   r,_=self.run_case(GOOD)
  self.assertEqual(r['result'],'BLOCKED');self.assertFalse(r['inventory_complete'])
 def test_save_failure(self):
  with patch.object(m,'save',side_effect=OSError('injected disk error')):
   r,_=self.run_case(GOOD)
  self.assertFalse(r['evidence_saved']);self.assertEqual(r['result'],'BLOCKED')
 def test_result_write_then_failure(self):
  original=m.save
  def broken(path,data):
   original(path,data)
   if path.name=='result.json': raise OSError('injected result post-write verification failure')
  with patch.object(m,'save',side_effect=broken): r,root=self.run_case(GOOD)
  self.assertEqual(r['result'],'BLOCKED');self.assertFalse(r['evidence_saved'])
  self.assertEqual(json.loads((root/'result.json').read_text())['result'],'PENDING')
  self.assertEqual(m.read_completion(root),'BLOCKED');self.assertFalse((root/'completion.json').exists())
 def test_receipt_write_then_failure(self):
  original=m.save
  def broken(path,data):
   original(path,data)
   if path.name=='completion.candidate.json': raise OSError('injected receipt post-write failure')
  with patch.object(m,'save',side_effect=broken): r,root=self.run_case(GOOD)
  self.assertEqual(r['result'],'BLOCKED');self.assertEqual(m.read_completion(root),'BLOCKED')
  self.assertFalse((root/'completion.json').exists())
 def test_completion_hash_rejects_mutation(self):
  r,root=self.run_case(GOOD);self.assertEqual(r['result'],'PASS')
  (root/'stdout.log').write_text('changed test copy')
  self.assertEqual(m.read_completion(root),'BLOCKED')
 def test_save_conflict(self):
  r,_=self.run_case(GOOD+"\npathlib.Path(os.environ['TMPDIR']).parent.joinpath('stdout.log').write_text('retained')")
  self.assertFalse(r['evidence_saved']);self.assertEqual(r['result'],'BLOCKED')
 def test_unrelated_process_survives(self):
  import subprocess
  other=subprocess.Popen([sys.executable,'-c','import time;time.sleep(10)'])
  try:
   self.run_case('import time;time.sleep(10)',timeout=.1);self.assertIsNone(other.poll())
  finally: other.terminate();other.wait()
if __name__=='__main__':unittest.main()
