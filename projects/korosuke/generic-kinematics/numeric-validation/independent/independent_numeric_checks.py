"""Independent integer-enclosure and high-precision synthetic geometry checks.

Uses exact Fraction arithmetic for interval arithmetic checks and mpmath's own
trigonometric implementation for geometry. Does not use candidate geometry in
oracle calculations. Numerical oracle evidence supplements, not replaces, proof.
"""
import argparse
from collections import Counter
import copy
from fractions import Fraction
import hashlib
import importlib
import json
import math
from pathlib import Path
import random
import sys
import time
import mpmath as mp

p = argparse.ArgumentParser()
p.add_argument('--source-dir', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
source_hashes = {name:hashlib.sha256((a.source_dir/name).read_bytes()).hexdigest() for name in ('certified.py','sweep.py')}
sys.path.insert(0, str(a.source_dir))
c = importlib.import_module('certified')
s = importlib.import_module('sweep')
rng = random.Random(202611090753)
mp.mp.dps = 740
started = time.time()
counts = Counter()
statuses = Counter()


def assert_interval(i, q):
    assert Fraction(i.lo, c.SCALE) <= q <= Fraction(i.hi, c.SCALE), (i.lo, i.hi, str(q))


def M(q):
    q = Fraction(q)
    return mp.mpf(q.numerator) / q.denominator


def trig(angle):
    q = Fraction(angle) % 360
    if q.denominator == 1 and q.numerator % 90 == 0:
        return [(mp.mpf(1), mp.mpf(0)), (mp.mpf(0), mp.mpf(1)),
                (mp.mpf(-1), mp.mpf(0)), (mp.mpf(0), mp.mpf(-1))][int(q // 90)]
    theta = M(q) * mp.pi / 180
    return mp.cos(theta), mp.sin(theta)


def oracle_polygons(moving, fixed, pivot, angle):
    co, si = trig(angle)
    cx, cy = map(M, moving['center'])
    hw, hh = (M(v)/2 for v in moving['size'])
    fx, fy = (M(Fraction(v)-Fraction(p)) for v,p in zip(fixed['center'],pivot))
    fw, fh = (M(v)/2 for v in fixed['size'])
    local = [(cx-hw,cy-hh), (cx+hw,cy-hh), (cx+hw,cy+hh), (cx-hw,cy+hh)]
    moving_points = [(x*co-y*si, x*si+y*co) for x,y in local]
    fixed_points = [(fx-fw,fy-fh),(fx+fw,fy-fh),(fx+fw,fy+fh),(fx-fw,fy+fh)]
    return moving_points, fixed_points


def oracle_pose(moving, fixed, pivot, angle):
    aa, bb = oracle_polygons(moving,fixed,pivot,angle)
    gap = max(mp.mpf(0), *(min(q[d] for q in bb)-max(q[d] for q in aa) for d in (0,1)),
              *(min(q[d] for q in aa)-max(q[d] for q in bb) for d in (0,1)))
    for polygon in (aa,bb):
        for i,p in enumerate(polygon):
            q=polygon[(i+1)%4]
            axis=(-(q[1]-p[1]),q[0]-p[0])
            assert axis != (0,0), 'Oracle precision lost a strictly positive edge'
            pa=[v[0]*axis[0]+v[1]*axis[1] for v in aa]
            pb=[v[0]*axis[0]+v[1]*axis[1] for v in bb]
            if max(pa)<min(pb) or max(pb)<min(pa):
                return False,gap
    return True,gap


def raw_case(moving, fixed, pivot=(0,0), lo=0, hi=1):
    return {'schema_version':1,'joint':{'pivot_mm':list(pivot),'start_deg':lo,'end_deg':hi},
            'moving':[{'id':'m','center_mm':list(moving['center']),'size_mm':list(moving['size'])}],
            'fixed':[{'id':'f','center_mm':list(fixed['center']),'size_mm':list(fixed['size'])}],
            'max_depth':0}


# Pure rational tests of every enclosure operation, including arbitrary negative
# intervals rather than only scalar input enclosures.
for _ in range(2500):
    nums=sorted(rng.randint(-10**100,10**100) for _ in range(4))
    aa=c.I(nums[0],nums[2]); bb=c.I(nums[1],nums[3])
    da=rng.randrange(1,100000)
    for x in (Fraction(aa.lo,c.SCALE),Fraction(aa.hi,c.SCALE)):
        assert_interval(-aa,-x)
        assert_interval(aa.abs(),abs(x))
        assert_interval(aa.div(da),x/da)
        for y in (Fraction(bb.lo,c.SCALE),Fraction(bb.hi,c.SCALE)):
            assert_interval(aa+bb,x+y)
            assert_interval(aa-bb,x-y)
            assert_interval(aa*bb,x*y)
    if aa.lo<=0<=aa.hi:
        assert_interval(aa.abs(),Fraction(0))
    q=Fraction(rng.randint(-10**320,10**320),rng.randint(1,10**320))
    assert_interval(c.I.exact(q),q)
    assert c.I.exact(q).hi-c.I.exact(q).lo<=1
    counts['exact_rational_arithmetic_cases']+=1

assert M(Fraction(c.PI.lo,c.SCALE)) < mp.pi < M(Fraction(c.PI.hi,c.SCALE))
counts['pi_enclosure_checks']+=1
angles=[Fraction(0),Fraction(45),Fraction(90),Fraction(180),Fraction(270),Fraction(360),
        Fraction(-45),Fraction(-90),Fraction(2**52)+Fraction(1,2),Fraction(2**60)+128]
for angle in (-360.,-315.,-270.,-225.,-180.,-135.,-90.,-45.,0.,45.,90.,135.,180.,225.,270.,315.,360.):
    angles.extend(Fraction(v) for v in (math.nextafter(angle,-math.inf),angle,math.nextafter(angle,math.inf)))
for _ in range(1500):
    if rng.randrange(2):
        angle=Fraction(rng.uniform(-1e18,1e18)) / 2**rng.randrange(17)
    else:
        angle=Fraction(rng.randint(-10**310,10**310),2**rng.randrange(1100))
    angles.append(angle)
for angle in angles:
    co,si=c.sincos(angle)
    oc,os=trig(angle)
    for interval,value in ((co,oc),(si,os)):
        assert M(Fraction(interval.lo,c.SCALE))<=value<=M(Fraction(interval.hi,c.SCALE)), str(angle)
    c2,s2=c.sincos(angle+360*rng.randint(-10**30,10**30))
    assert (co.lo,co.hi,si.lo,si.hi)==(c2.lo,c2.hi,s2.lo,s2.hi)
    counts['trig_and_exact_periodicity_cases']+=1

for _ in range(1000):
    radius=Fraction(rng.uniform(0,1e308))+Fraction(rng.uniform(0,1e308))
    angle=Fraction(rng.uniform(0,180))/2**rng.randrange(1100)
    upper=c.motion_upper(radius,angle)
    assert M(Fraction(upper,c.SCALE))>=M(radius)*M(angle)*mp.pi/180
    counts['motion_upper_enclosure_cases']+=1

scales=[5e-324,1e-300,1e-100,1e-60,1e-30,1.,1e30,1e100,1e300]
for _ in range(720):
    scale=rng.choice(scales)
    def v(): return rng.randint(-4,4)*scale
    def dim(): return rng.randint(1,4)*scale
    moving={'center':(v(),v()),'size':(dim(),dim())}
    fixed={'center':(v(),v()),'size':(dim(),dim())}
    pivot=(v(),v()) if rng.randrange(2) else (0.,0.)
    angle=rng.choice(angles)
    overlap,gap=c.pose(c.local_rectangle(moving),c.local_rectangle(fixed,pivot),angle)
    truth,actual_gap=oracle_pose(moving,fixed,pivot,angle)
    assert M(Fraction(gap,c.SCALE))<=actual_gap, ('gap overestimate',scale,str(angle))
    assert not overlap or truth, ('false overlap',scale,str(angle))
    counts['high_precision_pose_cases']+=1

# Midpoint corner-overlap witnesses constructed independently, spanning negative
# angles, quadrant changes, huge exact angles, scales and common translations.
for i in range(360):
    scale=rng.choice([1e-300,1e-100,1e-30,1.,1e30,1e100,1e200])
    lo=rng.choice([-360.01,-270.,-180.01,-90.01,-45.,-.01,.01,44.99,89.99,179.99,269.99,359.99,
                   float(2**52),float(-2**52),float(2**60)])
    hi=math.nextafter(lo,math.inf)
    midpoint=(Fraction(lo)+Fraction(hi))/2
    co,si=trig(midpoint)
    moving={'center':(scale,0.),'size':(scale,scale)}
    pivot=rng.choice([(0.,0.),(1e16,0.),(-1e100,1e100)])
    lx=M(scale)*mp.mpf('1.5'); ly=-M(scale)/2
    wx=M(pivot[0])+lx*co-ly*si; wy=M(pivot[1])+lx*si+ly*co
    fx,fy=float(wx),float(wy)
    width=max(float(abs(wx-M(fx))*4),scale/128,5e-324)
    height=max(float(abs(wy-M(fy))*4),scale/128,5e-324)
    # Outward-enlarge dimensions if binary64 conversion lands on a boundary.
    width=math.nextafter(width,math.inf); height=math.nextafter(height,math.inf)
    assert abs(wx-M(fx))<M(width)/2 and abs(wy-M(fy))<M(height)/2
    fixed={'center':(fx,fy),'size':(width,height)}
    raw=raw_case(moving,fixed,pivot,lo,hi)
    pair=s.screen(raw)['pairs'][0]
    statuses['constructed_overlap:'+pair['status']]+=1
    assert pair['status']!='PROJECTED_CLEAR',raw
    if pair['status']=='PROJECTED_OVERLAP':
        exact=Fraction(pair['first_observed_overlap_deg_exact'])
        assert exact==midpoint
        assert oracle_pose(moving,fixed,pivot,exact)[0]
    counts['independent_corner_overlap_witnesses']+=1

# Integer translations are exactly representable on both sides. Periodic shifts
# preserve every input angle exactly, not merely approximately.
for _ in range(120):
    moving={'center':(rng.randint(-20,20),rng.randint(-20,20)),
            'size':(rng.randint(1,20),rng.randint(1,20))}
    fixed={'center':(rng.randint(-100,100),rng.randint(-100,100)),
           'size':(rng.randint(1,20),rng.randint(1,20))}
    lo=rng.randint(-180,180); hi=lo+rng.randint(1,180)
    raw=raw_case(moving,fixed,lo=lo,hi=hi); raw['max_depth']=3
    original=s.screen(raw)['pairs'][0]
    tx,ty=rng.choice([-2**40,2**40]),rng.choice([-2**40,2**40])
    shifted=copy.deepcopy(raw)
    shifted['joint']['pivot_mm']=[tx,ty]
    shifted['fixed'][0]['center_mm']=[fixed['center'][0]+tx,fixed['center'][1]+ty]
    assert s.screen(shifted)['pairs'][0]==original
    periodic=copy.deepcopy(raw); delta=360*2**rng.choice([0,10,20,30,40])
    periodic['joint']['start_deg']+=delta; periodic['joint']['end_deg']+=delta
    rp=s.screen(periodic)['pairs'][0]
    for key in ('status','sample_count','certified_intervals','unresolved_intervals'):
        assert rp[key]==original[key],key
    if original['first_observed_overlap_deg_exact'] is not None:
        assert Fraction(rp['first_observed_overlap_deg_exact'])==Fraction(original['first_observed_overlap_deg_exact'])+delta
    counts['translation_and_periodicity_scenes']+=1

# Distinct extreme values, cancellation beyond binary64 range, and tiny positive
# dimensions must not throw or produce a CLEAR for known overlaps.
for scale in scales+[sys.float_info.max]:
    moving={'center':(0.,0.),'size':(scale,scale)}
    fixed={'center':(sys.float_info.max,-sys.float_info.max),'size':(scale,scale)}
    raw=raw_case(moving,fixed,fixed['center'],0.,1.)
    pair=s.screen(raw)['pairs'][0]
    assert pair['status']!='PROJECTED_CLEAR'
    statuses['center_overlap_extreme:'+pair['status']]+=1
    counts['extreme_center_overlap_cases']+=1
    fixed={'center':(-sys.float_info.max,sys.float_info.max),'size':(scale,scale)}
    raw=raw_case(moving,fixed,(sys.float_info.max,-sys.float_info.max),0.,1.)
    pair=s.screen(raw)['pairs'][0]
    statuses['opposite_max_coordinates:'+pair['status']]+=1
    counts['opposite_max_coordinate_cases']+=1

for scale in [1e-30,1.,1e30,1e100,1e300]:
    moving={'center':(0.,0.),'size':(scale,scale)}
    fixed={'center':(10*scale,0.),'size':(scale,scale)}
    assert s.screen(raw_case(moving,fixed))['pairs'][0]['status']=='PROJECTED_CLEAR'
    counts['ordinary_and_scaled_clear_controls']+=1

base=raw_case({'center':(0,0),'size':(1,1)},{'center':(10,0),'size':(1,1)})
invalid=[]
case=copy.deepcopy(base);case['joint']['start_deg']=-1e-15;case['joint']['end_deg']=360.;invalid.append(case)
case=copy.deepcopy(base);case['moving'][0]['center_mm'][0]=2**53+1;invalid.append(case)
case=copy.deepcopy(base);case['moving'][0]['center_mm'][0]=10**1000;invalid.append(case)
case=copy.deepcopy(base);case['joint']['start_deg']=1e308;case['joint']['end_deg']=math.nextafter(1e308,math.inf);invalid.append(case)
for case in invalid:
    try:s.screen(case)
    except s.InputError:pass
    else:raise AssertionError('invalid input accepted')
    counts['explicit_invalid_input_rejections']+=1

# Sample every independently generated CLEAR scene at exact dyadic angles. A
# vertex-to-segment distance oracle also checks the requested tolerance, rather
# than only testing polygon intersection.
def separation_squared(aa,bb):
    result=mp.inf
    for points,edges in ((aa,bb),(bb,aa)):
        for point in points:
            for i,start in enumerate(edges):
                end=edges[(i+1)%4]
                vx,vy=end[0]-start[0],end[1]-start[1]
                wx,wy=point[0]-start[0],point[1]-start[1]
                t=max(mp.mpf(0),min(mp.mpf(1),(vx*wx+vy*wy)/(vx*vx+vy*vy)))
                dx,dy=wx-t*vx,wy-t*vy
                result=min(result,dx*dx+dy*dy)
    return result

for _ in range(60):
    moving={'center':(rng.randint(-10,10),rng.randint(-10,10)),
            'size':(rng.randint(1,10),rng.randint(1,10))}
    fixed={'center':(rng.randint(-60,60),rng.randint(-60,60)),
           'size':(rng.randint(1,20),rng.randint(1,20))}
    lo=rng.randint(-180,180);hi=lo+rng.randint(1,180)
    raw=raw_case(moving,fixed,lo=lo,hi=hi)
    raw['max_depth']=4;raw['tolerance_mm']=rng.choice([0.,.01,1.,5.])
    pair=s.screen(raw)['pairs'][0]
    counts['continuous_screen_scenes']+=1
    statuses['continuous_scene:'+pair['status']]+=1
    if pair['status']!='PROJECTED_CLEAR':continue
    for step in range(65):
        angle=Fraction(lo)+Fraction(hi-lo)*Fraction(step,64)
        assert not oracle_pose(moving,fixed,(0,0),angle)[0]
        aa,bb=oracle_polygons(moving,fixed,(0,0),angle)
        assert separation_squared(aa,bb)>M(raw['tolerance_mm'])**2
        counts['clear_angle_and_tolerance_samples']+=1

assert source_hashes == {name:hashlib.sha256((a.source_dir/name).read_bytes()).hexdigest() for name in ('certified.py','sweep.py')}, 'Source changed during independent run'
report={'passed':True,'source_sha256':source_hashes,
        'seed':202611090753,'mpmath_version':mp.__version__,'mpmath_digits':mp.mp.dps,
        'counts':dict(counts),'classification_counts':dict(statuses),'elapsed_seconds':round(time.time()-started,3),
        'limits':'Deterministic finite checks supplement the separate source proof review. They are not exhaustive or a statistical error-rate estimate. No private CAD used.'}
a.output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
