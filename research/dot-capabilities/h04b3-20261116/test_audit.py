import copy,json,pathlib,unittest
from audit import evaluate,ROUTES,DIMENSIONS
DATA=json.loads(pathlib.Path(__file__).with_name('AUDIT.json').read_text())
class AuditTests(unittest.TestCase):
 def check(self,x,expected='FAIL'):
  o=evaluate(x);self.assertEqual(o['contract'],expected);self.assertFalse(o['execution_allowed']);self.assertEqual(o['experiment_start'],'BLOCKED');self.assertEqual(o['route_exclusivity'],'UNKNOWN');self.assertIsNone(o['method_adopted'])
 def test_current(self): self.check(DATA,'PASS')
 def test_every_cell_missing(self):
  for r in ROUTES:
   for d in DIMENSIONS:
    x=copy.deepcopy(DATA);del x['routes'][r][d];self.check(x)
 def test_provenance_missing(self):
  for key in ('observed_at','actor','environment','evidence','reason','status'):
   x=copy.deepcopy(DATA);del x['routes']['history']['available'][key];self.check(x)
 def test_bad_timestamps(self):
  for val in ('2026-11-16','2026-11-16T12:00:00','garbage',True,None):
   x=copy.deepcopy(DATA);x['routes']['history']['available']['observed_at']=val;self.check(x)
 def test_invalid_date_not_echoed(self):
  x=copy.deepcopy(DATA);marker='SYNTHETIC-INVALID-DATE-PUBLICATION-MARKER';x['routes']['history']['available']['observed_at']=marker
  self.check(x);self.assertNotIn(marker,str(evaluate(x)));self.assertEqual(evaluate(x)['reasons'],['DATE_FORMAT'])
 def test_no_evidence(self):
  for val in ([],[''],['  '],['x',None],None,'record'):
   x=copy.deepcopy(DATA);x['routes']['history']['available']['evidence']=val;self.check(x)
 def test_all_pass_is_not_execution_or_truth(self):
  x=copy.deepcopy(DATA)
  for row in x['routes'].values():
   for cell in row.values():cell['status']='PASS'
  self.check(x,'PASS');self.assertEqual(evaluate(x)['evidence_authenticity'],'UNKNOWN')
 def test_methods_never_auto_adopted(self):
  for method in ('A','B'):
   x=copy.deepcopy(DATA);x['method']=method;self.check(x)
 def test_invalid(self):
  for val in (None,True,[],{},42,'audit'):self.check(val)
 def test_missing_routes(self):
  for r in ROUTES:
   x=copy.deepcopy(DATA);del x['routes'][r];self.check(x)
 def test_wrong_status(self):
  for s in (True,[],None,'NOT_TESTED','pass'):
   x=copy.deepcopy(DATA);x['routes']['history']['available']['status']=s;self.check(x)
if __name__=='__main__':unittest.main()
