import tempfile,subprocess,pathlib,sys,json
script=pathlib.Path(__file__).resolve().parents[2]/'run_pose.py'
with tempfile.TemporaryDirectory() as tmp:
 out=pathlib.Path(tmp)/'result.json'
 p=subprocess.run([sys.executable,str(script),'nonexistent-request.json','--output',str(out),'--timeout','0.000000001'],capture_output=True,text=True)
 r=json.loads(out.read_text());assert p.returncode==2 and r['status']=='UNRESOLVED' and 'TimeoutExpired' in r['error'];print(json.dumps(dict(returncode=p.returncode,status=r['status'],error_type='TimeoutExpired'),indent=2))
