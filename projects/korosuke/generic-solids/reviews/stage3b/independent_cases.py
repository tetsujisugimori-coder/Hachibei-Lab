import sys,pathlib,math,json
sys.path[:0]=[str(pathlib.Path(__file__).resolve().parents[2])]
import FreeCAD as A,Part
from solid_check import measure_pair,transformed
rows=[]
def check(name,a,b,vol,dist,status,**kw):
 r=measure_pair(a,b,**kw); assert r['status']==status,(name,r)
 if vol is not None: assert abs(r['intersection_volume_mm3']-vol)<1e-9,(name,r)
 if dist is not None: assert abs(r['minimum_distance_mm']-dist)<1e-8,(name,r)
 rows.append(dict(name=name,status=r['status'],volume=r.get('intersection_volume_mm3'),distance=r.get('minimum_distance_mm')))
u=Part.makeBox(1,1,1)
for name,pos,dist in [('face',(1,0,0),0),('edge',(1,1,0),0),('vertex',(1,1,1),0),('diagonal',(2,3,3),3)]:check(name,u,Part.makeBox(1,1,1,A.Vector(*pos)),0,dist,'CONTACT_OR_WITHIN_TOLERANCE' if dist==0 else 'SEPARATED_AT_POSE')
# Resolvable small-scale geometry with analytical overlap below the default micro threshold.
a=Part.makeBox(.01,.01,.01); b=Part.makeBox(.01,.01,.01,A.Vector(.009,0,0));check('real-micro-overlap',a,b,1e-7,0,'MICRO_OVERLAP_REPORTED')
# Own explicit vertex transform oracle for a quarter turn about non-origin pivot.
s=transformed(u,pivot=(2,3,0),degrees=90,translation=(4,5,6));check('non-origin-transform',s,Part.makeBox(1,1,1,A.Vector(8,6,6)),1,0,'VOLUME_OVERLAP')
check('units-rejected',u,u,None,None,'UNRESOLVED',units_a='inch')
class Broken:
 def isNull(self):raise RuntimeError('injected shape failure')
check('kernel-exception',Broken(),u,None,None,'UNRESOLVED')
# Analytic sphere disjoint distance and contained intersection volume, unlike box-only tests.
check('spheres-gap',Part.makeSphere(2),Part.makeSphere(1,A.Vector(5,0,0)),0,2,'SEPARATED_AT_POSE')
check('spheres-contained',Part.makeSphere(2),Part.makeSphere(1),4*math.pi/3,0,'VOLUME_OVERLAP')
print(json.dumps({'checks':rows,'pass_count':len(rows)},indent=2))
