import math, unittest
import FreeCAD as A
import Part
from solid_check import measure_pair, transformed, fourbar_pose, Policy

class SolidTests(unittest.TestCase):
    def box(self, x=0,y=0,z=0): return Part.makeBox(2,3,4,A.Vector(x,y,z))
    def test_known_volume(self):
        r=measure_pair(self.box(),self.box(1,1,1));self.assertEqual(r['status'],'VOLUME_OVERLAP');self.assertAlmostEqual(r['intersection_volume_mm3'],6)
    def test_known_distance(self):
        r=measure_pair(self.box(),self.box(5));self.assertEqual(r['status'],'SEPARATED_AT_POSE');self.assertAlmostEqual(r['minimum_distance_mm'],3)
    def test_contact(self):
        for xyz in [(2,0,0),(2,3,0),(2,3,4)]:
            r=measure_pair(self.box(),self.box(*xyz));self.assertEqual(r['status'],'CONTACT_OR_WITHIN_TOLERANCE');self.assertEqual(r['intersection_volume_mm3'],0)
    def test_tiny_overlap_retained(self):
        r=measure_pair(self.box(),self.box(2-1e-4));self.assertEqual(r['status'],'VOLUME_OVERLAP');self.assertAlmostEqual(r['intersection_volume_mm3'],12e-4)
    def test_micro_overlap_not_clear(self):
        r=measure_pair(self.box(),self.box(2-1e-4),policy=Policy(micro_volume_mm3=.01));self.assertEqual(r['status'],'MICRO_OVERLAP_REPORTED')
    def test_near_contact_not_clear(self):
        r=measure_pair(self.box(),self.box(2+5e-7));self.assertEqual(r['status'],'CONTACT_OR_WITHIN_TOLERANCE')
    def test_rotation_translation(self):
        a,b=self.box(),self.box(1,1,1)
        r=measure_pair(transformed(a,pivot=(1,2,3),axis=(1,2,3),degrees=37,translation=(17,-30,11)),transformed(b,pivot=(1,2,3),axis=(1,2,3),degrees=37,translation=(17,-30,11)))
        self.assertAlmostEqual(r['intersection_volume_mm3'],6,places=8)
    def test_copy_preserved(self):
        a=self.box();old=a.hashCode();transformed(a,degrees=90,translation=(1,2,3));self.assertEqual(a.hashCode(),old)
    def test_invalid_units(self):
        for unit in ['m','cm',None,'MM']:
            self.assertEqual(measure_pair(self.box(),self.box(),units_b=unit)['status'],'UNRESOLVED')
    def test_invalid_shape(self):
        for s in [Part.Shape(),Part.makePlane(2,3),Part.makePolygon([A.Vector(),A.Vector(1,0,0)])]:
            self.assertEqual(measure_pair(s,self.box())['status'],'UNRESOLVED')
    def test_mixed_shape_rejected(self):
        self.assertEqual(measure_pair(Part.Compound([self.box(),Part.makeLine(A.Vector(5,5,5),A.Vector(6,6,6))]),self.box())['status'],'UNRESOLVED')
    def test_multiple_solids(self):
        r=measure_pair(Part.Compound([self.box(),self.box(5)]),self.box(1));self.assertEqual(r['a']['solids'],2);self.assertAlmostEqual(r['intersection_volume_mm3'],12)
    def test_invalid_policy(self):
        for v in [math.nan, math.inf,-1,True]: self.assertEqual(measure_pair(self.box(),self.box(),policy=Policy(linear_tolerance_mm=v))['status'],'UNRESOLVED')
    def test_bad_transform(self):
        for kw in [{'degrees':math.nan},{'degrees':1e18},{'axis':(0,0,0)},{'translation':(math.inf,0,0)}]:
            with self.assertRaises(ValueError):transformed(self.box(),**kw)
    def test_clearance_separate(self):
        r=measure_pair(self.box(),self.box(2.2),policy=Policy(required_clearance_mm=.5));self.assertEqual(r['status'],'SEPARATED_AT_POSE');self.assertEqual(r['manufacturing_clearance'],'MEASURED_BELOW_REQUIREMENT')
    def test_sweep_midpoint(self):
        moving=Part.makeBox(6,1,1);fixed=Part.makeBox(1,1,1,A.Vector(-.5,4,0))
        states=[measure_pair(transformed(moving,degrees=d),fixed)['status'] for d in [0,90,180]]
        self.assertEqual(states,['SEPARATED_AT_POSE','VOLUME_OVERLAP','SEPARATED_AT_POSE'])
    def test_fourbar_closure(self):
        for angle in range(0,361,10):self.assertLess(fourbar_pose((0,0),(8,1),1,8,3,angle)['closure_residual_mm'],1e-10)
    def test_fourbar_reject(self):
        with self.assertRaises(ValueError):fourbar_pose((0,0),(30,0),1,2,2,0)

if __name__=='__main__':unittest.main(verbosity=2)
