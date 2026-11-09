"""Axis-aligned box formula is the oracle, not OCC or target geometry functions."""
import copy,hashlib,json,math,pathlib,platform,random,sys
import FreeCAD as A,Part
from solid_check import measure_pair
from validate_fixture_results import validate
out=pathlib.Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
rng=random.Random(31631);rows=[]
for i in range(120):
    a=[rng.uniform(-10,10) for _ in range(3)];b=[a[j]+rng.uniform(-4,4) for j in range(3)]
    sa=[rng.uniform(.5,5) for _ in range(3)];sb=[rng.uniform(.5,5) for _ in range(3)]
    overlap=[max(0,min(a[j]+sa[j],b[j]+sb[j])-max(a[j],b[j])) for j in range(3)]
    gap=[max(0,a[j]-b[j]-sb[j],b[j]-a[j]-sa[j]) for j in range(3)]
    r=measure_pair(Part.makeBox(*sa,A.Vector(*a)),Part.makeBox(*sb,A.Vector(*b)))
    rows.append({'id':f'box-{i:03d}','a':a,'b':b,'size_a':sa,'size_b':sb,'expected_volume_mm3':math.prod(overlap),'expected_distance_mm':math.sqrt(sum(g*g for g in gap)),'measured_volume_mm3':r.get('intersection_volume_mm3'),'measured_distance_mm':r.get('minimum_distance_mm'),'status':r['status']})
ids=[r['id'] for r in rows];validate(rows,ids)
mutations=[]
for name,mutate in [('false_clear',lambda r:r[0].update(status='PROJECTED_CLEAR')),('missing_row',lambda r:r.pop()),('duplicate_id',lambda r:r[0].update(id=r[1]['id'])),('missing_distance',lambda r:r[0].pop('measured_distance_mm')),('nan_volume',lambda r:r[0].update(measured_volume_mm3=float('nan'))),('wrong_volume',lambda r:r[0].update(measured_volume_mm3=12345)),('wrong_distance',lambda r:r[0].update(measured_distance_mm=12345))]:
    corrupted=copy.deepcopy(rows);mutate(corrupted)
    try:validate(corrupted,ids)
    except ValueError:mutations.append({'mutation':name,'result':'REJECTED'})
    else:raise AssertionError('fault accepted: '+name)
(out/'analytic.json').write_text(json.dumps({'oracle':'closed-form independent axis-aligned interval intersections and Euclidean gaps','seed':31631,'rows':rows,'fault_controls':mutations,'python':sys.version,'os':platform.platform(),'freecad':A.Version(),'occ':Part.OCC_VERSION},indent=2)+'\n')
print(f'PASS: {len(rows)} analytic boxes, {len(mutations)} rejected corruptions')
