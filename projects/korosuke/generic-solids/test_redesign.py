import unittest
import FreeCAD as App
import Part
from neutral_redesign import fixture
from redesign_check import compare_redesign
from solid_check import Policy


class RedesignTests(unittest.TestCase):
    def run_case(self, depth=4):
        return fixture(depth)

    def test_relief_preserves_lands_and_web(self):
        a,b,k=self.run_case(); r=compare_redesign(a,b,**k)
        self.assertEqual(r['status'], 'PASS', r['errors'])
        initial=r['targets'][0]
        self.assertAlmostEqual(initial['before']['intersection_volume_mm3'],32)
        self.assertAlmostEqual(initial['after']['intersection_volume_mm3'],0)
        self.assertAlmostEqual(initial['after']['minimum_distance_mm'],1)
        self.assertEqual(len(r['neighbors']),6)
        self.assertEqual(r['continuous_motion'],'NOT_PROVEN')

    def test_boundary_is_unresolved(self):
        a,b,k=self.run_case(); k['policy']=Policy(required_clearance_mm=1)
        r=compare_redesign(a,b,**k)
        self.assertEqual(r['initial_targets'],'UNRESOLVED')
        self.assertEqual(r['sampled_targets'],'UNRESOLVED')
        self.assertEqual(r['status'],'UNRESOLVED')

    def test_no_op_is_not_redesign(self):
        a,b,k=self.run_case(); self.assertEqual(compare_redesign(a,a,**k)['status'],'UNRESOLVED')

    def test_deletion_rejected(self):
        a,b,k=self.run_case(); del b['slider']
        self.assertEqual(compare_redesign(a,b,**k)['status'],'UNRESOLVED')

    def test_destroyed_support_rejected(self):
        a,b,k=self.run_case(7)
        self.assertEqual(compare_redesign(a,b,**k)['status'],'UNRESOLVED')

    def test_contact_is_not_clearance(self):
        a,b,k=self.run_case(2)
        r=compare_redesign(a,b,**k)
        self.assertEqual(r['initial_targets'],'FAIL')
        self.assertEqual(r['targets'][0]['after']['status'],'CONTACT_OR_WITHIN_TOLERANCE')

    def test_new_neighbor_collision(self):
        a,b,k=self.run_case()
        b['bracket']=b['bracket'].fuse(Part.makeBox(6,2,2,App.Vector(11,0,0))).removeSplitter()
        r=compare_redesign(a,b,**k)
        self.assertEqual(r['initial_targets'],'PASS')
        self.assertEqual(r['new_neighbor_overlap'],'FAIL')
        self.assertNotEqual(r['status'],'PASS')

    def test_threshold_relaxation_not_an_input(self):
        a,b,k=self.run_case(2)
        k['policy']=Policy(micro_volume_mm3=1e10,required_clearance_mm=0)
        self.assertNotEqual(compare_redesign(a,b,**k)['status'],'PASS')

    def test_pose_inventory_and_initial_required(self):
        for poses in ([],[{'slider':{'degrees':1}}],[{}, {'unknown':{}}]):
            a,b,k=self.run_case(); k['poses']=poses
            self.assertEqual(compare_redesign(a,b,**k)['status'],'UNRESOLVED')

    def test_invalid_solid(self):
        a,b,k=self.run_case(); b['bracket']=Part.Shape()
        self.assertEqual(compare_redesign(a,b,**k)['status'],'UNRESOLVED')

    def test_clearance_requirement_required(self):
        a,b,k=self.run_case(); k['policy']=Policy()
        self.assertEqual(compare_redesign(a,b,**k)['status'],'UNRESOLVED')


if __name__=='__main__': unittest.main()
