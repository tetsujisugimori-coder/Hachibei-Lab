"""Verify bytes of a small local synthetic evidence ZIP, never upload/network."""
import hashlib,json,pathlib,stat,zipfile

def verify(path):
 with zipfile.ZipFile(path) as z:
  names=z.namelist()
  if not names or len(names)!=len(set(names)):raise ValueError('empty or duplicate')
  for i in z.infolist():
   p=pathlib.PurePosixPath(i.filename)
   if p.is_absolute() or '..' in p.parts or '\\' in i.filename or ':' in i.filename or i.is_dir() or stat.S_ISLNK(i.external_attr>>16):raise ValueError('unsafe path')
   if i.file_size>10_000_000:raise ValueError('size bound')
  if sum(i.file_size for i in z.infolist())>30_000_000:raise ValueError('total bound')
  if z.testzip() is not None:raise ValueError('CRC')
  m=json.loads(z.read('manifest.json'))
  if type(m) is not list or not m or any(type(r) is not dict for r in m):raise ValueError('manifest')
  expected=[r.get('path') for r in m]
  if len(set(expected))!=len(expected) or set(expected)!=(set(names)-{'manifest.json'}):raise ValueError('set mismatch')
  for r in m:
   b=z.read(r['path'])
   if type(r.get('size')) is not int or r['size']!=len(b) or r.get('sha256')!=hashlib.sha256(b).hexdigest():raise ValueError('content mismatch')
  return {'status':'PASS','entries':len(names),'payloads':len(m),'sha256':hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()}
