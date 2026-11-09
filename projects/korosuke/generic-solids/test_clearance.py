import math, unittest
from unittest.mock import patch
import FreeCAD as A
import Part
from solid_check import Policy, measure_pair, clearance_result

class ClearanceTests(unittest.TestCase):
    def pair(self,x,required=0,**kw):
        return measure_pair(Part.makeBox(2,2,2),Part.makeBox(2,2,2,A.Vector(x,0,0)),policy=Policy(required_clearance_mm=required,**kw))
    def test_fixed_p2_overlap_zero(self):
        r=self.pair(1); self.assertEqual(r['status'],'VOLUME_OVERLAP');self.assertEqual(r['manufacturing_clearance'],'INTERFERENCE')
    def test_contact_zero_not_clearance(self):
        r=self.pair(2);self.assertEqual(r['manufacturing_clearance'],'CONTACT_OR_WITHIN_TOLERANCE')
    def test_separation_zero(self):
        self.assertEqual(self.pair(3)['manufacturing_clearance'],'MEASURED_AT_OR_ABOVE_REQUIREMENT')
    def test_positive_requirement_below_boundary_above(self):
        for x,expect in [(2.5,'MEASURED_BELOW_REQUIREMENT'),(3,'UNRESOLVED'),(4,'MEASURED_AT_OR_ABOVE_REQUIREMENT')]:
            with self.subTest(x=x):self.assertEqual(self.pair(x,1)['manufacturing_clearance'],expect)
    def test_micro_volume_retained(self):
        r=self.pair(2-1e-4,micro_volume_mm3=.01);self.assertEqual(r['status'],'MICRO_OVERLAP_REPORTED');self.assertEqual(r['manufacturing_clearance'],'INTERFERENCE')
    def test_requirement_reporting_band(self):
        for d in [1-1e-7,1,1+1e-7]:self.assertEqual(clearance_result(0,d,1e-6,1),'UNRESOLVED')
    def test_invalid_kernel_measurements(self):
        for v in [math.nan,math.inf,-1,True]:
            with self.assertRaises(ValueError):clearance_result(v,1,1e-6,0)
    def test_contradictory_measurements(self):
        with self.assertRaises(ValueError):clearance_result(1,1,1e-6,0)
    def test_invalid_requirement_fails_closed(self):
        for x in [math.nan,math.inf,-1,True]:
            r=self.pair(3,x);self.assertEqual(r['status'],'UNRESOLVED');self.assertEqual(r['manufacturing_clearance'],'UNRESOLVED')
    def test_late_failure_resets_classification(self):
        with patch('solid_check.clearance_result',side_effect=ValueError('fault control')):
            r=self.pair(3);self.assertEqual(r['status'],'UNRESOLVED');self.assertEqual(r['manufacturing_clearance'],'UNRESOLVED')
    def test_overlap_no_requirement_not_invented(self):
        self.assertEqual(self.pair(1,None)['manufacturing_clearance'],'NOT_SPECIFIED')
    def test_near_contact_positive_requirement(self):
        self.assertEqual(self.pair(2+5e-7,1)['manufacturing_clearance'],'CONTACT_OR_WITHIN_TOLERANCE')

if __name__=='__main__':unittest.main()
