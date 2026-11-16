import importlib.util,json,pathlib,unittest
from unittest.mock import patch
p=pathlib.Path(__file__).parents[1]/'tools/runner.py'
s=importlib.util.spec_from_file_location('runner',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Contracts(unittest.TestCase):
 def test_complete(self): self.assertEqual(m.outcome(0,json.dumps({'phase':'temp','path':'probe.txt','readback':'isolated-temp-42\n'})+'\n'+json.dumps({'phase':'dom','actual':'isolated-temp-42','profileFiles':['Preferences']})+'\n'+json.dumps({'phase':'closed'})),'PASS')
 def test_missing_evidence(self): self.assertEqual(m.outcome(0,'\n'.join(json.dumps({'phase':x}) for x in ['temp','dom','closed'])),'BLOCKED')
 def test_wrong_values(self): self.assertEqual(m.outcome(0,json.dumps({'phase':'temp','path':'/tmp/other','readback':'WRONG'})+'\n'+json.dumps({'phase':'dom','actual':'WRONG','profileFiles':[]})+'\n'+json.dumps({'phase':'closed'})),'BLOCKED')
 def test_nonzero(self): self.assertEqual(m.outcome(2,'\n'.join(json.dumps({'phase':x}) for x in ['temp','dom','closed'])),'BLOCKED')
 def test_missing(self): self.assertEqual(m.outcome(0,''),'BLOCKED')
 def test_missing_dom(self): self.assertEqual(m.outcome(0,'{"phase":"temp"}\n{"phase":"closed"}'),'BLOCKED')
 def test_reordered(self): self.assertEqual(m.outcome(0,'{"phase":"dom"}\n{"phase":"temp"}\n{"phase":"closed"}'),'BLOCKED')
 def test_bad_json(self): self.assertEqual(m.outcome(0,'broken'),'BLOCKED')
 def test_timeout(self): self.assertEqual(m.outcome(None,''),'BLOCKED')
 def test_relative(self):
  with self.assertRaises(ValueError):m.validate_root('relative')
 def test_shared(self):
  with self.assertRaises(ValueError):m.validate_root('/tmp/no-write')
 def test_existing(self):
  with self.assertRaises(ValueError):m.validate_root(str(pathlib.Path.cwd()))
 def test_low_space(self):
  with patch.object(m,'snapshot',return_value={'available':0}), self.assertRaises(ValueError):m.validate_root(str(pathlib.Path.cwd()/'nonexistent-probe-test'))
if __name__=='__main__':unittest.main()
