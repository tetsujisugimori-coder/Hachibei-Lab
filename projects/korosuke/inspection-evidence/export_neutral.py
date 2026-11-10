"""Original neutral solid fixture for the offline viewer; no private inputs."""
import sys, json, pathlib, hashlib, math
import FreeCAD as App
import Part
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'generic-solids'))
from solid_check import measure_pair, transformed, Policy

def mesh(s):
    if s.isNull() or not s.Faces: return None
    vertices, triangles = s.tessellate(0.05)
    return {'vertices': [[v.x,v.y,v.z] for v in vertices], 'triangles': [list(t) for t in triangles]}

def build(out):
    out.mkdir(parents=True, exist_ok=True)
    d = App.newDocument('NeutralInspection')
    shapes = {'arm': Part.makeBox(20,4,4,App.Vector(0,-2,0)), 'obstacle': Part.makeBox(6,6,6,App.Vector(12,-3,-1))}
    for name, shape in shapes.items():
        o=d.addObject('Part::Feature',name);o.Shape=shape
    d.recompute(); path=out/'neutral.FCStd';d.saveAs(str(path));App.closeDocument(d.Name)
    sha=hashlib.sha256(path.read_bytes()).hexdigest();d=App.openDocument(str(path))
    roundtrip=[]
    for name in shapes:
        s=d.getObject(name).Shape
        step=out/(name+'.step');s.exportStep(str(step));reloaded=Part.Shape();reloaded.read(str(step))
        a=s.cut(reloaded).Volume;b=reloaded.cut(s).Volume
        delta=abs(s.Volume-reloaded.Volume)
        ok=reloaded.isValid() and len(reloaded.Solids)==len(s.Solids) and delta<1e-6 and a<1e-6 and b<1e-6
        roundtrip.append({'part':name,'volume_difference_mm3':delta,'bidirectional_difference_mm3':[a,b],'passed':ok})
        assert ok
    parts=[{'id':name,'name':name.title(),'role':'Original neutral test fixture','category':'internal' if name=='arm' else 'exterior','drawings':['Neutral orthographic projection in viewer']} for name in shapes]
    payload={'schema_version':1,'units':'mm','source':{'sha256':sha,'description':'Original neutral fixture; FreeCAD/OCC sampled measurements only'},'parts':parts,'poses':[]}
    for angle in (0,30,60,90):
        pid='angle-'+str(angle);a=transformed(d.getObject('arm').Shape, degrees=angle);b=d.getObject('obstacle').Shape.copy()
        r=measure_pair(a,b,policy=Policy(required_clearance_mm=0))
        mapping={'VOLUME_OVERLAP':'INTERFERENCE','MICRO_OVERLAP_REPORTED':'INTERFERENCE','CONTACT_OR_WITHIN_TOLERANCE':'CONTACT','SEPARATED_AT_POSE':'CLEAR','UNRESOLVED':'UNRESOLVED'}
        geom=[{'part_id':name,**mesh(s)} for name,s in [('arm',a),('obstacle',b)]]
        m={'a':'arm','b':'obstacle','status':mapping[r['status']],'volume_mm3':r.get('intersection_volume_mm3'),'distance_mm':r.get('minimum_distance_mm'),'tolerance_mm':r.get('effective_linear_tolerance_mm',1e-6),'evidence':{'method':'OCC_BREP','source_sha256':sha,'pose_id':pid,'angle_deg':angle},'intersection':mesh(a.common(b)) if r.get('intersection_volume_mm3',0)>0 else None}
        payload['poses'].append({'id':pid,'angle_deg':angle,'geometry':geom,'measurements':[m]})
    assert payload['poses'][0]['measurements'][0]['status']=='INTERFERENCE'
    assert payload['poses'][-1]['measurements'][0]['status']=='CLEAR'
    (out/'viewer.json').write_text(json.dumps(payload,indent=2)+'\n')
    (out/'roundtrip.json').write_text(json.dumps({'method':'OCC_BREP; empirical tolerance, not certified bound','freecad':App.Version(),'occ':Part.OCC_VERSION,'source_sha256':sha,'parts':roundtrip,'continuous_path':'UNKNOWN'},indent=2)+'\n')
    App.closeDocument(d.Name)
    print(json.dumps({'poses':4,'pairs':4,'roundtrip_parts':2,'status':'PASS'}))
if __name__=='__main__': build(pathlib.Path(sys.argv[1]))
