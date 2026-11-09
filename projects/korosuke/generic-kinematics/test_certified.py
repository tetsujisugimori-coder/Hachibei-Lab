"""Exact-arithmetic regression controls; optional independent mpmath is separate."""
from fractions import Fraction as F
import copy
import json
import math
from pathlib import Path
import unittest
from certified import I, SCALE, PI, ceildiv, sincos, local_rectangle, pose, motion_upper
from sweep import InputError, screen

ROOT=Path(__file__).parent
class CertifiedTests(unittest.TestCase):
    def assert_encloses(self, interval, exact):
        self.assertLessEqual(F(interval.lo,SCALE),exact)
        self.assertGreaterEqual(F(interval.hi,SCALE),exact)

    def test_signed_rounding(self):
        for n in range(-51,52):
            for d in range(1,15):
                q=F(n,d); self.assert_encloses(I.exact(q),q)
                self.assertGreaterEqual(ceildiv(n,d),q)
                self.assertLessEqual(n//d,q)

    def test_arithmetic_enclosures(self):
        values=[F(-7,3),F(-1,10**80),F(0),F(2,7),F(10**309),F(1,2**1074)]
        for a in values:
            for b in values:
                self.assert_encloses(I.exact(a)+I.exact(b),a+b)
                self.assert_encloses(I.exact(a)-I.exact(b),a-b)
                self.assert_encloses(I.exact(a)*I.exact(b),a*b)
            self.assert_encloses(I.exact(a).abs(),abs(a))
            self.assert_encloses(I.exact(a).div(13),a/13)

    def test_interval_negative_extrema(self):
        p=I(-3*SCALE,2*SCALE)*I(-5*SCALE,7*SCALE)
        self.assertEqual((p.lo,p.hi),(-21*SCALE,15*SCALE))
        self.assertEqual((I(-3,2).abs().lo,I(-3,2).abs().hi),(0,3))

    def test_cardinals_huge_and_negative(self):
        for turns in [0,-10**100,10**100]:
            for degrees, co, si in [(0,1,0),(90,0,1),(180,-1,0),(270,0,-1)]:
                c,s=sincos(F(360*turns+degrees))
                self.assertEqual((c.lo,c.hi,s.lo,s.hi),(co*SCALE,co*SCALE,si*SCALE,si*SCALE))

    def test_exact_coordinate_cancellation(self):
        p=local_rectangle({'center':(1e308,-1e308),'size':(1,1)},(1e308,-1e308))
        self.assertEqual([(x.lo,x.hi) for x in p],[(0,0),(0,0),(SCALE//2,SCALE//2),(SCALE//2,SCALE//2)])

    def test_exact_adjacent_midpoint_and_motion(self):
        a=F(2**52); b=F(float(2**52+1)); m=(a+b)/2
        self.assertTrue(a<m<b); self.assertNotEqual(F(float(m)),m)
        bound=motion_upper(F(3),max(m-a,b-m))
        self.assertGreaterEqual(F(bound,SCALE),F(3)*F(1,2)*F(PI.lo,SCALE)/180)

    def test_inexact_integer_rejected(self):
        raw=json.loads((ROOT/'example-neutral.json').read_text())
        raw['fixed'][0]['center_mm'][0]=2**54+1
        with self.assertRaises(InputError): screen(raw)

    def test_overflow_integer_rejected(self):
        raw=json.loads((ROOT/'example-neutral.json').read_text()); raw['joint']['start_deg']=10**400
        with self.assertRaises(InputError): screen(raw)

    def test_subnormal_overlap_never_clear(self):
        tiny=math.ulp(0.0)
        raw={'schema_version':1,'joint':{'pivot_mm':[0,0],'start_deg':0,'end_deg':1},
             'moving':[{'id':'m','center_mm':[0,0],'size_mm':[tiny,tiny]}],
             'fixed':[{'id':'f','center_mm':[0,0],'size_mm':[tiny,tiny]}], 'max_depth':0}
        self.assertNotEqual(screen(raw)['pairs'][0]['status'],'PROJECTED_CLEAR')

    def test_overflow_difference_is_not_float_infinity(self):
        big=float.fromhex('0x1.fffffffffffffp+1023')
        raw={'schema_version':1,'joint':{'pivot_mm':[-big,0],'start_deg':0,'end_deg':1},
             'moving':[{'id':'m','center_mm':[0,0],'size_mm':[1,1]}],
             'fixed':[{'id':'f','center_mm':[big,0],'size_mm':[1,1]}]}
        self.assertEqual(screen(raw)['pairs'][0]['status'],'PROJECTED_CLEAR')

    def test_multi_pairs_and_depth_fail_closed(self):
        raw={'schema_version':1,'joint':{'pivot_mm':[0,0],'start_deg':-1,'end_deg':1},
             'moving':[{'id':'m','center_mm':[0,0],'size_mm':[1,1]}],
             'fixed':[{'id':'touch','center_mm':[1,0],'size_mm':[1,1]},
                      {'id':'far','center_mm':[100,0],'size_mm':[1,1]}], 'max_depth':0}
        r=screen(raw); self.assertEqual(r['pair_count'],2)
        self.assertEqual(r['pairs'][0]['status'],'PROJECTED_OVERLAP')
        self.assertEqual(r['pairs'][1]['status'],'PROJECTED_CLEAR')
        raw['joint'].update(start_deg=0,end_deg=360)
        raw['fixed'][0]['center_mm']=[1.5,0]
        self.assertEqual(screen(raw)['pairs'][0]['status'],'UNRESOLVED_2D')

if __name__=='__main__': unittest.main()
