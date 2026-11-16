import hashlib, importlib.util, io, json, pathlib, stat, unittest, zipfile
P = pathlib.Path(__file__).resolve().parents[1] / 'tools' / 'verify_archive.py'
spec = importlib.util.spec_from_file_location('archive', P); a = importlib.util.module_from_spec(spec); spec.loader.exec_module(a)

class Safety(unittest.TestCase):
    def test_paths(self):
        for name in ['../x','/x','a\\b','C:x','a/../b','a//b','AUX.txt','a.','x/CON','x\x00y','x:y','a/']:
            with self.subTest(name=name), self.assertRaises(ValueError): a.safe_name(name)
        self.assertEqual(a.safe_name('originals/a.json'),'originals/a.json')
    def test_json_duplicate(self):
        with self.assertRaises(ValueError): a.parse('{"x":1,"x":2}')
    def test_wrong_package(self):
        with self.assertRaises(ValueError): a.inspect(b'bad')
    def check_zip(self, entries):
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:
            for name, data, mode in entries:
                info=zipfile.ZipInfo(name); info.external_attr=mode << 16; z.writestr(info,data)
        data=out.getvalue()
        return a.inspect(data, a.digest(data), len(data), len(entries)-1)
    def test_zip_duplicate(self):
        with self.assertRaisesRegex(ValueError,'duplicate Windows'): self.check_zip([('a',b'',0),('A',b'',0)])
    def test_symlink(self):
        with self.assertRaisesRegex(ValueError,'nonregular'): self.check_zip([('a',b'x',stat.S_IFLNK)])
    def test_path_in_zip(self):
        with self.assertRaisesRegex(ValueError,'unsafe'): self.check_zip([('../a',b'x',0)])
    def test_file_dir_collision(self):
        with self.assertRaisesRegex(ValueError,'collision'): self.check_zip([('a',b'x',0),('a/b',b'x',0)])
    def test_manifest_missing(self):
        with self.assertRaises(KeyError): self.check_zip([('a',b'x',0)])
    def test_manifest_count(self):
        with self.assertRaisesRegex(ValueError,'manifest count'): self.check_zip([('manifest.json',b'{"files":[{}]}',0)])
    def test_manifest_coverage(self):
        m=json.dumps({'files':[{'path':'missing','bytes':1,'sha256':a.digest(b'x')}] }).encode()
        with self.assertRaisesRegex(ValueError,'coverage'): self.check_zip([('a',b'x',0),('manifest.json',m,0)])
    def test_manifest_hash(self):
        m=json.dumps({'files':[{'path':'a','bytes':1,'sha256':'bad'}]}).encode()
        with self.assertRaisesRegex(ValueError,'member mismatch'): self.check_zip([('a',b'x',0),('manifest.json',m,0)])

if __name__=='__main__': unittest.main()
