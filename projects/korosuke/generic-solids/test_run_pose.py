import hashlib,json,os,pathlib,subprocess,sys,tempfile,unittest
import FreeCAD as A,Part
from solid_check import *
class RunnerTests(unittest.TestCase):
 def test_bound_model_and_hash_rejection(self):
  with tempfile.TemporaryDirectory() as tmp:
   t=pathlib.Path(tmp);d=A.newDocument('NeutralFixture')
   for n,x in [('BlockA',0),('BlockB',3)]:o=d.addObject('Part::Feature',n);o.Shape=Part.makeBox(1,1,1,A.Vector(x,0,0))
   # Nested placement is deliberately nonidentity; world distance must be 7.
   group=d.addObject('App::Part','TranslatedGroup');group.addObject(d.getObject('BlockB'));group.Placement.Base=A.Vector(5,0,0)
   d.recompute();d.saveAs(str(t/'model.FCStd'));A.closeDocument(d.Name)
   req={'units':'mm','model':str(t/'model.FCStd'),'model_sha256':hashlib.sha256((t/'model.FCStd').read_bytes()).hexdigest(),'poses':[{'id':'pose-zero','a':'BlockA','b':'BlockB'}]}
   def run():
    (t/'request.json').write_text(json.dumps(req));p=subprocess.run([sys.executable,str(pathlib.Path(__file__).with_name('run_pose.py')),str(t/'request.json'),'--output',str(t/'out.json')],capture_output=True,text=True);return p.returncode,json.loads((t/'out.json').read_text())
   code,r=run();self.assertEqual(code,0);self.assertAlmostEqual(r['measurements'][0]['minimum_distance_mm'],7)
   req['model_sha256']='0'*64;code,r=run();self.assertEqual(code,2);self.assertEqual(r['status'],'UNRESOLVED')
 def test_process_failure_not_success(self):
  with tempfile.TemporaryDirectory() as tmp:
   t=pathlib.Path(tmp);(t/'bad.json').write_text('{')
   p=subprocess.run([sys.executable,str(pathlib.Path(__file__).with_name('run_pose.py')),str(t/'bad.json'),'--output',str(t/'out.json')],capture_output=True,text=True)
   self.assertEqual(p.returncode,2);self.assertEqual(json.loads((t/'out.json').read_text())['status'],'UNRESOLVED')
if __name__=='__main__':unittest.main(verbosity=2)
