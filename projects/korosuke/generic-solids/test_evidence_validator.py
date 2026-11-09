import copy,math,unittest
from validate_fixture_results import validate
class EvidenceTests(unittest.TestCase):
 def fixture(self,x=.5):
  shape={'a':[0,0,0],'b':[x,0,0],'size_a':[1,1,1],'size_b':[1,1,1]};volume=1-x
  row=dict(id='known-overlap',**copy.deepcopy(shape),expected_volume_mm3=volume,measured_volume_mm3=volume,expected_distance_mm=0,measured_distance_mm=0,status='VOLUME_OVERLAP' if volume>1e-6 else 'MICRO_OVERLAP_REPORTED')
  return row,{'known-overlap':shape}
 def test_independent_review_false_accept(self):
  row,trusted=self.fixture();row.update(expected_volume_mm3=0.,measured_volume_mm3=0.,expected_distance_mm=5.,measured_distance_mm=5.,status='SEPARATED_AT_POSE')
  with self.assertRaises(ValueError):validate([row],trusted)
 def test_normal_and_micro(self):
  for x in [.5,1-1e-8]:
   row,trusted=self.fixture(x);self.assertTrue(validate([row],trusted))
 def test_input_not_evidence_oracle(self):
  row,trusted=self.fixture();row['b']=[5,0,0]
  with self.assertRaises(ValueError):validate([row],trusted)
 def test_ids_not_trusted_geometry(self):
  row,_=self.fixture()
  with self.assertRaises(ValueError):validate([row],['known-overlap'])
if __name__=='__main__':unittest.main(verbosity=2)
