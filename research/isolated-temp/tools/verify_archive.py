"""Offline PR30 archive verifier. Never downloads, runs browser, or deletes files."""
import argparse, hashlib, io, json, os, pathlib, re, stat, subprocess, sys, time, zipfile
SHA = '47e7e14bad9964f6168142a579f2814c00816f9bfd940bcdcfb9d84756378bcc'
SIZE = 1679175
COUNT = 542
SOURCE = 'submitted/research/isolated-temp/evidence/private-source-manifest.json'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def safe_name(name):
    if not isinstance(name, str) or not name or '\\' in name or ':' in name:
        raise ValueError('unsafe path')
    parts = name.split('/')
    for p in parts:
        if p in ('', '.', '..') or p[-1:] in (' ', '.') or re.search(r'[\x00-\x1f<>"|?*]', p):
            raise ValueError('unsafe path')
        if re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])(?:\..*)?', p):
            raise ValueError('Windows reserved path')
    return name

def unique_object(pairs):
    d = {}
    for k, v in pairs:
        if k in d: raise ValueError('duplicate JSON key')
        d[k] = v
    return d

def parse(data):
    return json.loads(data, object_pairs_hook=unique_object)

def inspect(data, expected_sha=SHA, expected_size=SIZE, expected_count=COUNT):
    if len(data) != expected_size or digest(data) != expected_sha:
        raise ValueError('ZIP size or SHA mismatch')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        entries = z.infolist()
        if len(entries) != expected_count + 1: raise ValueError('entry count')
        seen = set(); payload = {}
        if sum(e.file_size for e in entries) > 16 * 1024 * 1024: raise ValueError('expansion limit')
        for e in entries:
            name = safe_name(e.filename)
            if name.casefold() in seen: raise ValueError('duplicate Windows path')
            seen.add(name.casefold())
            mode = e.external_attr >> 16
            if e.is_dir() or stat.S_ISLNK(mode) or (stat.S_IFMT(mode) not in (0, stat.S_IFREG)):
                raise ValueError('nonregular ZIP member')
            payload[name] = z.read(e)  # zipfile verifies CRC for every member
        for name in payload:
            if any('/'.join(name.split('/')[:i]).casefold() in seen for i in range(1, len(name.split('/')))):
                raise ValueError('file-directory collision')
        manifest = parse(payload['manifest.json'])
        rows = manifest['files']
        if len(rows) != expected_count: raise ValueError('manifest count')
        names = [safe_name(f['path']) for f in rows]
        if len(set(n.casefold() for n in names)) != len(names): raise ValueError('manifest duplicates')
        if set(names) != set(payload) - {'manifest.json'}: raise ValueError('manifest coverage')
        for f in rows:
            b = payload[f['path']]
            if len(b) != f['bytes'] or digest(b) != f['sha256']: raise ValueError('member mismatch')
        originals = parse(payload[SOURCE])['original_files']
        if len(originals) != 18 or sum(f['bytes'] for f in originals) != 1163952:
            raise ValueError('original18 inventory')
        if len({f['path'] for f in originals}) != 18: raise ValueError('original18 duplicate')
        for f in originals:
            b = payload[safe_name(f['path'])]
            if len(b) != f['bytes'] or digest(b) != f['sha256']: raise ValueError('original18 mismatch')
        return payload

def no_links(path):
    for p in [path, *path.parents]:
        if p.exists() or p.is_symlink():
            s = p.lstat()
            if stat.S_ISLNK(s.st_mode) or getattr(s, 'st_file_attributes', 0) & 0x400:
                raise ValueError('symlink/reparse path')

def read_package(path):
    no_links(path)
    with path.open('rb') as f: data = f.read(SIZE + 1)
    inspect(data)
    return data

def check_saved(dest):
    no_links(dest)
    data = read_package(dest / 'Hachibei-Lab-PR30-private-transfer.zip')
    payload = inspect(data)
    root = dest / 'contents'
    actual = set(); scanned = 0; deadline = time.monotonic() + 30
    for directory, dirs, files in os.walk(root, followlinks=False):
        scanned += len(dirs) + len(files)
        if scanned > 2000 or time.monotonic() > deadline: raise ValueError("readback scan limit")
        for n in dirs + files: no_links(pathlib.Path(directory) / n)
        for n in files:
            p = pathlib.Path(directory) / n
            rel = p.relative_to(root).as_posix(); actual.add(rel)
            if rel not in payload or p.stat().st_size != len(payload[rel]): raise ValueError('saved inventory/size')
            with p.open('rb') as f: b = f.read(len(payload[rel]) + 1)
            if digest(b) != digest(payload[rel]): raise ValueError('saved SHA mismatch')
    if actual != set(payload): raise ValueError('saved missing/extra')
    return {'result': 'WINDOWS_ARCHIVE_PASS' if os.name == 'nt' else 'NON_WINDOWS_READBACK_PASS',
            'zip_bytes': SIZE, 'zip_sha256': SHA, 'manifest_files': COUNT, 'original_files': 18,
            'crc': 'PASS', 'sha256': 'PASS', 'external_backup': 'NOT_DONE', 'pid': os.getpid()}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--package', type=pathlib.Path)
    ap.add_argument('--destination', required=True, type=pathlib.Path)
    ap.add_argument('--readback', action='store_true'); args = ap.parse_args()
    dest = args.destination.absolute(); no_links(dest)
    if args.readback:
        print(json.dumps(check_saved(dest))); return
    data = read_package(args.package.absolute()); payload = inspect(data)
    if not dest.parent.is_dir(): raise ValueError('existing archive parent required')
    dest.mkdir(exist_ok=False)  # existing directory never reused
    with (dest / 'Hachibei-Lab-PR30-private-transfer.zip').open('xb') as f:
        f.write(data); f.flush(); os.fsync(f.fileno())
    for name, b in payload.items():
        p = dest / 'contents' / name
        p.parent.mkdir(parents=True, exist_ok=True); no_links(p)
        with p.open('xb') as f:
            f.write(b); f.flush(); os.fsync(f.fileno())
    child = subprocess.run([sys.executable, str(pathlib.Path(__file__).absolute()), '--destination', str(dest), '--readback'], capture_output=True, text=True, timeout=120)
    if child.returncode: raise RuntimeError('separate readback failed: ' + child.stderr[:2000])
    receipt = json.loads(child.stdout)
    receipt['archive_parent_pid'] = os.getpid()
    with (dest / 'windows-readback.json').open('x', encoding='utf8') as f:
        json.dump(receipt, f, indent=2); f.flush(); os.fsync(f.fileno())
    print(json.dumps(receipt))

if __name__ == '__main__':
    try: main()
    except Exception as exc:
        print('ARCHIVE_BLOCKED: ' + str(exc), file=sys.stderr); sys.exit(2)
