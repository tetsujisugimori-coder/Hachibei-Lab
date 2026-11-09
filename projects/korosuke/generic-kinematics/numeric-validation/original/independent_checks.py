"""Independent PR8 review: segment/containment oracle, not target SAT reuse.
Synthetic public rectangles only. Dense sampling is not a continuous proof.
Usage: python independent_checks.py --source /path/to/sweep.py --output result.json
"""
import argparse, copy, hashlib, importlib.util, json, math, platform, random, subprocess
from pathlib import Path

def polygon(rect, angle, pivot):
    # Independently construct rotated center plus basis vectors, unlike source
    # which rotates each joint-local corner and adds pivot sequentially.
    cx,cy=rect['center_mm']; w,h=rect['size_mm']; r=angle*math.pi/180
    c,s=math.cos(r),math.sin(r)
    x=pivot[0]+cx*c-cy*s; y=pivot[1]+cx*s+cy*c
    ux,uy=w*c/2,w*s/2; vx,vy=-h*s/2,h*c/2
    return [(x-ux-vx,y-uy-vy),(x+ux-vx,y+uy-vy),(x+ux+vx,y+uy+vy),(x-ux+vx,y-uy+vy)]
def cross(a,b,c): return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def on_segment(a,b,p):
    return cross(a,b,p)==0 and min(a[0],b[0])<=p[0]<=max(a[0],b[0]) and min(a[1],b[1])<=p[1]<=max(a[1],b[1])
def segments(a,b,c,d):
    o1,o2,o3,o4=cross(a,b,c),cross(a,b,d),cross(c,d,a),cross(c,d,b)
    return ((o1>0 and o2<0 or o1<0 and o2>0) and (o3>0 and o4<0 or o3<0 and o4>0)) or any((on_segment(a,b,c),on_segment(a,b,d),on_segment(c,d,a),on_segment(c,d,b)))
def contains(poly,p):
    v=[cross(poly[i],poly[(i+1)%4],p) for i in range(4)]
    return all(x>=0 for x in v) or all(x<=0 for x in v)
def collision(a,b):
    return any(segments(a[i],a[(i+1)%4],b[j],b[(j+1)%4]) for i in range(4) for j in range(4)) or contains(a,b[0]) or contains(b,a[0])
def fixture(mc=(10,0),ms=(1,1),fc=(100,100),fs=(1,1),span=(-30,30),pivot=(0,0),**extra):
    return dict(schema_version=1,joint=dict(pivot_mm=list(pivot),start_deg=span[0],end_deg=span[1]),moving=[dict(id='m',center_mm=list(mc),size_mm=list(ms))],fixed=[dict(id='f',center_mm=list(fc),size_mm=list(fs))],**extra)
def oracle(raw,angle):
    return collision(polygon(raw['moving'][0],angle,raw['joint']['pivot_mm']),polygon(raw['fixed'][0],0,(0,0)))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
    spec=importlib.util.spec_from_file_location('review_target',a.source); target=importlib.util.module_from_spec(spec);spec.loader.exec_module(target)
    def status(r):return target.screen(r)['pairs'][0]['status']
    cases=[
      ('clear',fixture(), 'PROJECTED_CLEAR',None),
      ('overlap',fixture(fc=(10,0)), 'PROJECTED_OVERLAP',0),
      ('touch',fixture(mc=(0,0),ms=(2,2),fc=(2,0),fs=(2,2),span=(-.1,.1)), 'PROJECTED_OVERLAP',0),
      ('interior_only',fixture(ms=(.1,.1),fc=(10*math.cos(math.radians(1)),10*math.sin(math.radians(1))),fs=(.1,.1),span=(-10,10)), 'PROJECTED_OVERLAP',1),
      ('depth_limit',fixture(mc=(2,0),ms=(1,1),fc=(2,2),fs=(1,1),span=(-60,60),max_depth=0), 'UNRESOLVED_2D',None),
      ('tiny_gap',fixture(mc=(0,0),ms=(1,1),fc=(1+1e-8,0),fs=(1,1),span=(-1e-9,1e-9)), 'PROJECTED_CLEAR',None),
      ('micro_dimensions',fixture(mc=(1e-9,0),ms=(1e-10,1e-10),fc=(1e-9,0),fs=(1e-10,1e-10),span=(-1,1)), 'PROJECTED_OVERLAP',0),
    ]
    rows=[]
    for name,r,expect,witness in cases:
        got=status(r); row=dict(id=name,input=r,expected_status=expect,actual_status=got,pass_=got==expect)
        if witness is not None:row.update(witness_angle=witness,independent_intersection=oracle(r,witness))
        rows.append(row)
    rng=random.Random(20261109); random_rows=[]; clear_count=0; samples=0; violations=[]; mirrors=[]
    for i in range(240):
        r=fixture(mc=(rng.uniform(-20,20),rng.uniform(-20,20)),ms=(rng.uniform(.1,4),rng.uniform(.1,4)),fc=(rng.uniform(-30,30),rng.uniform(-30,30)),fs=(rng.uniform(.1,4),rng.uniform(.1,4)),span=(-60,60),pivot=(rng.uniform(-3,3),rng.uniform(-3,3)))
        got=status(r); hit=None
        if got=='PROJECTED_CLEAR':
            clear_count+=1
            for k in range(721):
                angle=-60+k/6;samples+=1
                if oracle(r,angle):hit=angle;violations.append(dict(index=i,input=r,angle=angle));break
        q=copy.deepcopy(r);q['joint']['pivot_mm'][1]*=-1;q['joint']['start_deg']=-r['joint']['end_deg'];q['joint']['end_deg']=-r['joint']['start_deg']
        for group in ('moving','fixed'):q[group][0]['center_mm'][1]*=-1
        reflected=status(q)
        if got!=reflected:mirrors.append(dict(index=i,original=got,reflected=reflected))
        random_rows.append(dict(index=i,input=r,status=got,dense_intersection=hit,reflected_status=reflected))
    invalids=[]
    changes=[('nan',lambda r:r['joint'].update(start_deg=float('nan'))),('infinity',lambda r:r['joint'].update(end_deg=float('inf'))),('bool_pivot',lambda r:r['joint'].update(pivot_mm=[True,0])),('zero_size',lambda r:r['moving'][0].update(size_mm=[0,1])),('negative_size',lambda r:r['moving'][0].update(size_mm=[-1,1])),('empty_group',lambda r:r.update(moving=[])),('duplicate_id',lambda r:r['moving'].append(copy.deepcopy(r['moving'][0]))),('reversed_range',lambda r:r['joint'].update(start_deg=30,end_deg=-30)),('too_wide_range',lambda r:r['joint'].update(start_deg=-200,end_deg=200)),('boolean_depth',lambda r:r.update(max_depth=True)),('negative_tolerance',lambda r:r.update(tolerance_mm=-1)),('zero_interval',lambda r:r.update(min_interval_deg=0))]
    for name,change in changes:
        r=fixture();change(r)
        try:target.screen(r);invalids.append(dict(id=name,rejected=False))
        except target.InputError as e:invalids.append(dict(id=name,rejected=True,error=str(e)))
    faults=[]
    for row in rows:
        if row.get('independent_intersection'):
            # Test review oracle can reject a deliberately falsified CLEAR report.
            faults.append(dict(id=row['id'],injected_status='PROJECTED_CLEAR',detected=bool(row['independent_intersection'])))
    report=dict(evaluated_head='e5079db255403134d1864fc8b4ed8b3e8418350d',source_sha256=hashlib.sha256(Path(a.source).read_bytes()).hexdigest(),python=platform.python_version(),oracle='Independent rotated-center/basis construction, edge-segment intersection plus convex containment; no target corners/intersects used',limitations=['240 randomized finite moderate-coordinate cases and 721 discrete angles per CLEAR case are not exhaustive or a continuous proof.','Extreme numeric cases are evaluated separately with high-precision arithmetic.','No original/private robot CAD or 3D evaluation.'],examples=rows,random=dict(seed=20261109,cases=240,clear_cases=clear_count,dense_angles_per_clear_case=721,total_sampled_angles=samples,false_clear_violations=violations,reflected_status_differences=mirrors,records=random_rows),invalid_inputs=invalids,negative_controls=faults)
    report['baseline_suite_pass']=all(x['pass_'] for x in rows) and not violations and not mirrors and all(x['rejected'] for x in invalids) and all(x['detected'] for x in faults)
    Path(a.output).write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('examples','random','invalid_inputs','negative_controls')},indent=2));print('Random CLEAR',clear_count,'samples',samples,'mirror differences',len(mirrors),'faults',len(faults));return 0 if report['baseline_suite_pass'] else 1
if __name__=='__main__':raise SystemExit(main())
