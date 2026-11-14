"""Read-only archive identity checker; not a CAD correctness test."""
import hashlib,json,pathlib,sys,zipfile

def check(path, spec):
    errors=[]
    if hashlib.sha256(path.read_bytes()).hexdigest()!=spec['sha256']:errors.append('archive hash mismatch')
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        if len(names)!=len(set(names)):errors.append('duplicate members')
        if set(names)!=set(spec['members']):errors.append('member set mismatch')
        for name,h in spec['members'].items():
            if name not in names or hashlib.sha256(z.read(name)).hexdigest()!=h:errors.append('member mismatch: '+name)
    return errors

def main():
    if sys.argv[1:]==['--self-test']:
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/'test.zip'
            with zipfile.ZipFile(p,'w') as z:z.writestr('a','original')
            spec={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'members':{'a':hashlib.sha256(b'original').hexdigest()}}
            assert check(p,spec)==[]
            with zipfile.ZipFile(p,'w') as z:z.writestr('a','corrupt')
            assert 'archive hash mismatch' in check(p,spec)
            assert 'member mismatch: a' in check(p,spec)
        print('normal and corruption controls passed');return
    if len(sys.argv)!=3:raise SystemExit('usage: verify_archives.py STAGE1B.zip STAGE2.zip')
    specs=json.loads(pathlib.Path(__file__).with_name('inventory.json').read_text())['archives']
    result=[{'archive':s['name'],'errors':check(pathlib.Path(p),s)} for p,s in zip(sys.argv[1:],specs)]
    print(json.dumps(result,indent=2));raise SystemExit(int(any(r['errors'] for r in result)))
if __name__=='__main__':main()
