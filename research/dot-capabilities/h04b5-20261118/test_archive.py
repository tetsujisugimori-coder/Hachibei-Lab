import unittest,zipfile,json,hashlib,tempfile,pathlib
from archive import verify
class Tests(unittest.TestCase):
 def make(self,root,name='payload.txt',payload=b'harmless synthetic\n',manifest=True,mutate=False,extra=False):
  p=root/'evidence.zip';m=[{'path':name,'size':len(payload),'sha256':hashlib.sha256(payload).hexdigest()}]
  with zipfile.ZipFile(p,'w') as z:
   z.writestr(name,b'modified' if mutate else payload)
   if manifest:z.writestr('manifest.json',json.dumps(m))
   if extra:z.writestr('extra.txt','extra')
  return p
 def test_archive(self):
  with tempfile.TemporaryDirectory(dir=pathlib.Path(__file__).parent) as d:
   r=pathlib.Path(d)
   self.assertEqual(verify(self.make(r))['payloads'],1)
   for kw in [{'manifest':False},{'mutate':True},{'extra':True},{'name':'../escape'},{'name':'/absolute'}]:
    with self.assertRaises((ValueError,KeyError)):verify(self.make(r,**kw))
   p=self.make(r); b=p.read_bytes();p.write_bytes(b.replace(b'harmless synthetic',b'corrupt! synthetic'))
   with self.assertRaises((ValueError,zipfile.BadZipFile)):verify(p)
if __name__=='__main__':unittest.main()
