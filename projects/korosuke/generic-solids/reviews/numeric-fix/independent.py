import importlib.util,sys,json,math,hashlib,platform,argparse
from pathlib import Path
from fractions import Fraction
import FreeCAD as A
import Part
base=Path(__file__).parent
ap=argparse.ArgumentParser();ap.add_argument('--before',type=Path,default=base/'before.py');ap.add_argument('--candidate',type=Path,default=base/'candidate/projects/korosuke/generic-solids/solid_check.py');ap.add_argument('--output',type=Path,default=base/'independent-results.json');args=ap.parse_args()

def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
old=load('old',args.before); new=load('new',args.candidate)
def pair(m,x,req,micro=1e-6):return m.measure_pair(Part.makeBox(2,2,2),Part.makeBox(2,2,2,A.Vector(x,0,0)),policy=m.Policy(required_clearance_mm=req,micro_volume_mm3=micro))
fixed={'before':pair(old,1,0),'after':pair(new,1,0)}
assert fixed['before']['manufacturing_clearance']=='MEASURED_AT_OR_ABOVE_REQUIREMENT'
assert fixed['after']['manufacturing_clearance']=='INTERFERENCE'
rows=[]
# Independent analytic interval geometry, not target predicate as oracle.
for i in range(-8,25):
 x=Fraction(i,4); volume=max(Fraction(0), min(Fraction(2),x+2)-max(Fraction(0),x))*4
 distance=max(Fraction(0),x-2,-x-2)
 for req in (0,Fraction(1,2),1,2):
  r=pair(new,float(x),float(req))
  expect=('INTERFERENCE' if volume>0 else 'CONTACT_OR_WITHIN_TOLERANCE' if distance==0 else 'UNRESOLVED' if distance==req else 'MEASURED_BELOW_REQUIREMENT' if distance<req else 'MEASURED_AT_OR_ABOVE_REQUIREMENT')
  assert r['manufacturing_clearance']==expect,(x,req,r,expect)
  assert abs(r['intersection_volume_mm3']-float(volume))<1e-10
  assert abs(r['minimum_distance_mm']-float(distance))<1e-10
  rows.append({'x':float(x),'requirement':float(req),'analytic_volume':float(volume),'analytic_distance':float(distance),'expected':expect,'actual':r['manufacturing_clearance']})
# Boundary classification using exact rationals of the input floats.
for d in (1-1e-7,1,1+1e-7,1-2e-6,1+2e-6):
 exact_lo=Fraction(d)-Fraction(1e-6);exact_hi=Fraction(d)+Fraction(1e-6)
 expect='MEASURED_AT_OR_ABOVE_REQUIREMENT' if exact_lo>1 else 'MEASURED_BELOW_REQUIREMENT' if exact_hi<1 else 'UNRESOLVED'
 assert new.clearance_result(0,d,1e-6,1)==expect
micro=pair(new,2-1e-4,0,.01);assert micro['manufacturing_clearance']=='INTERFERENCE' and micro['status']=='MICRO_OVERLAP_REPORTED'
for value in (math.nan,math.inf,-1,True):assert pair(new,3,value)['status']=='UNRESOLVED'
result={'fixed':fixed,'analytic_cases':rows,'analytic_count':len(rows),'boundary_count':5,'micro':micro,'python':platform.python_version(),'freecad':A.Version(),'source_sha256':hashlib.sha256(args.candidate.read_bytes()).hexdigest(),'status':'PASS','limitation':'independent interval formulas for boxes; same OCC runtime, no certified kernel error guarantee'}
args.output.write_text(json.dumps(result,indent=2)+'\n')
print('PASS',len(rows),'analytic box/clearance cases; 5 boundaries; fixed before/after; micro; invalid')
