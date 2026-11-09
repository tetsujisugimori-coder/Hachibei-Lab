"""Run explicit BRep poses in a disposable subprocess, with hash/units binding."""
import argparse, hashlib, json, math, os, pathlib, subprocess, sys, tempfile

def main():
    ap=argparse.ArgumentParser();ap.add_argument('request');ap.add_argument('--output',required=True);ap.add_argument('--worker',action='store_true');ap.add_argument('--timeout',type=float,default=120)
    args=ap.parse_args();output=pathlib.Path(args.output)
    if not args.worker:
        if not math.isfinite(args.timeout) or args.timeout<=0:ap.error('positive finite timeout required')
        with tempfile.TemporaryDirectory() as tmp:
            dst=pathlib.Path(tmp)/'result.json'
            try:
                completed=subprocess.run([sys.executable,__file__,args.request,'--worker','--output',str(dst)],capture_output=True,text=True,timeout=args.timeout)
                result=json.loads(dst.read_text()) if completed.returncode==0 and dst.exists() else {'status':'UNRESOLVED','error':'worker failure','returncode':completed.returncode,'stderr':completed.stderr[-2000:]}
            except (subprocess.TimeoutExpired,ValueError,OSError) as e: result={'status':'UNRESOLVED','error':type(e).__name__+': '+str(e)}
        output.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.NamedTemporaryFile('w',dir=output.parent,delete=False) as f:json.dump(result,f,indent=2);f.write('\n');temp=f.name
        os.replace(temp,output)
        return 2 if result['status']=='UNRESOLVED' else 0
    result={'status':'UNRESOLVED'}
    try:
        import FreeCAD as App
        from solid_check import measure_pair,transformed,Policy
        request_path=pathlib.Path(args.request).resolve();raw=request_path.read_bytes();req=json.loads(raw)
        if req['units']!='mm':raise ValueError('explicit mm units required')
        model=pathlib.Path(req['model']).resolve();digest=hashlib.sha256(model.read_bytes()).hexdigest()
        if digest!=req['model_sha256']:raise ValueError('model hash mismatch')
        if not isinstance(req['poses'],list) or not req['poses']:raise ValueError('nonempty explicit pose list required')
        identifiers=[p['id'] for p in req['poses']]
        if any(not isinstance(x,str) or not x for x in identifiers) or len(set(identifiers))!=len(identifiers):raise ValueError('unique nonempty pose ids required')
        doc=App.openDocument(str(model));measurements=[]
        def world(name):
            o=doc.getObject(name)
            if o is None or not hasattr(o,'Shape'):raise ValueError('missing solid object')
            s=o.Shape.copy()
            # Object Shape includes local Placement. Move ancestor coordinates into world.
            s.Placement=o.getGlobalPlacement().multiply(o.Placement.inverse()).multiply(s.Placement)
            return s
        for pose in req['poses']:
            a,b=world(pose['a']),world(pose['b'])
            a=transformed(a,**pose.get('transform_a',{}));b=transformed(b,**pose.get('transform_b',{}))
            r=measure_pair(a,b,policy=Policy(**req.get('policy',{})));r['pose_id']=pose['id'];measurements.append(r)
        result={'status':'UNRESOLVED' if any(r['status']=='UNRESOLVED' for r in measurements) else 'MEASUREMENTS_COMPLETED','model_sha256':digest,'request_sha256':hashlib.sha256(raw).hexdigest(),'freecad':App.Version(),'measurements':measurements,'continuous_motion':'NOT_PROVEN'}
        App.closeDocument(doc.Name)
    except Exception as e:result['error']=type(e).__name__+': '+str(e)
    output.write_text(json.dumps(result,indent=2)+'\n')
    return 0

if __name__=='__main__':sys.exit(main())
