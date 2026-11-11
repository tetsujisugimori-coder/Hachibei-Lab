"""Reproduce independent review defects and fixes using synthetic records only."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from evidence import audit, canonical, digest
from test_evidence import make_bundle, refresh_pages

BASE = 'e2a58d17955a912bd3912572cb92439b2a874c17'
ROOT = Path(__file__).resolve().parents[2]
old_source = subprocess.check_output(
    ['git', 'show', BASE + ':stage3/tools/evidence.py'], cwd=ROOT, text=True)
old = {'__name__': 'frozen_evidence'}
exec(compile(old_source, 'frozen_evidence', 'exec'), old)
rows = []

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    for index, field, value in ((0, 'issuer', 'different issuer'), (2, 'observed_choice', 'REFUSE')):
        ledger, model = make_bundle(root)
        record = copy.deepcopy(ledger['records'][index])
        payload = json.loads((root / record['artifact']).read_bytes())
        payload[field] = value
        raw = canonical(payload)
        (root / 'alternate.json').write_bytes(raw)
        record.update(id='SYN-ALT', native_id='synthetic:alternate', artifact='alternate.json',
                      original_artifact='alternate.json', sha256=digest(raw), original_sha256=digest(raw))
        ledger['records'].append(record)
        page = ledger['sources'][0]['collection']['pages'][0]
        page['record_ids'].append('SYN-ALT'); page['reported_total'] = 4
        refresh_pages(ledger, root)
        before, after = old['audit'](ledger, root, model), audit(ledger, root, model)
        code = 'CONTRADICTORY_' + record['role'] + '_CONTENT'
        rows.append({'case': code, 'changed_field': field, 'synthetic_value': value,
                     'before': before['status'], 'after': after['status'],
                     'old_defect_reproduced': before['status'] != 'CONFLICT',
                     'fixed': after['status'] == 'CONFLICT' and code in [f['code'] for f in after['findings']]})

    ledger, model = make_bundle(root)
    record = copy.deepcopy(ledger['records'][0]); raw = b'{"x":1e999}'
    (root / 'other.json').write_bytes(raw)
    record.update(id='SYN-OTHER', native_id='synthetic:other', role='OTHER', artifact='other.json',
                  original_artifact='other.json', sha256=digest(raw), original_sha256=digest(raw))
    ledger['records'].append(record)
    page = ledger['sources'][0]['collection']['pages'][0]
    page['record_ids'].append('SYN-OTHER'); page['reported_total'] = 4
    refresh_pages(ledger, root)
    before, after = old['audit'](ledger, root, model), audit(ledger, root, model)
    rows.append({'case': 'NONFINITE_EXPONENT', 'synthetic_payload': raw.decode(),
                 'before': before['status'], 'after': after['status'],
                 'old_defect_reproduced': before['status'] != 'CONFLICT',
                 'fixed': 'INVALID_RECORD_JSON' in [f['code'] for f in after['findings']]})

    ledger, model = make_bundle(root)
    ledger['sources'][0]['id'] = '\ud800'
    (root / 'ledger.json').write_text(json.dumps(ledger))
    frozen = root / 'frozen.py'; frozen.write_text(old_source)
    env = dict(os.environ, PYTHONPATH=str(ROOT / 'stage3/tools'))
    commands = (frozen, ROOT / 'stage3/tools/evidence.py')
    results = [subprocess.run([sys.executable, str(tool), 'ledger.json', '--root', str(root),
                               '--model', 'model.json'], capture_output=True, text=True, env=env)
               for tool in commands]
    before, after = results
    rows.append({'case': 'UNPAIRED_SURROGATE', 'synthetic_input': 'source ID contains escaped U+D800',
                 'before_exit': before.returncode, 'after_exit': after.returncode,
                 'old_defect_reproduced': before.returncode == 1 and 'UnicodeEncodeError' in before.stderr,
                 'fixed': after.returncode == 2 and not after.stderr and
                 json.loads(after.stdout)['input_error'] == 'INVALID_OR_UNREADABLE_INPUT'})

print(json.dumps({'baseline': BASE, 'evidence_kind': 'SYNTHETIC', 'rows': rows}, indent=2))
assert all(row['old_defect_reproduced'] and row['fixed'] for row in rows)
