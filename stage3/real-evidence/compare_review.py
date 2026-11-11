"""Reproduce the independent optional-model contract finding on synthetic input."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import types

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / 'stage3/tools'
sys.path.insert(0, str(TOOLS))
from evidence import canonical
from observed_evidence import validate
from test_observed_evidence import fixture
from test_approval import fixture as model_fixture

BEFORE = '3f2bf01f4bd55254aa1e3bc3f1391a853b4254ff'
source = subprocess.check_output(['git', 'show', BEFORE + ':stage3/tools/observed_evidence.py'], cwd=ROOT, text=True)
old = types.ModuleType('independent_before')
exec(compile(source, 'independent_before', 'exec'), old.__dict__)
invalid = fixture(); invalid['model'] = {'invalid': 'synthetic'}
old.validate(invalid)
try:
    validate(invalid)
except ValueError:
    after_invalid = 'REJECTED'
else:
    raise AssertionError('invalid model accepted by validate')
rows = [{'case': 'invalid_optional_model_validate', 'before': 'ACCEPTED', 'after': after_invalid}]
env = dict(os.environ, PYTHONPATH=str(TOOLS), PYTHONDONTWRITEBYTECODE='1')
for size in (1000, 1001):
    snapshot = fixture(); model = model_fixture(); snapshot['model'] = model
    original = model['decisions'][0]
    model['decisions'] = [dict(copy.deepcopy(original), id='SYN-D-' + str(i)) for i in range(size)]
    before = subprocess.run([sys.executable, '-c', source], input=canonical(snapshot), capture_output=True, env=env, check=False)
    after = subprocess.run([sys.executable, str(TOOLS / 'observed_evidence.py')], input=canonical(snapshot), capture_output=True, env=env, check=False)
    assert before.returncode == 0 and after.returncode == (0 if size == 1000 else 2)
    assert before.stderr == after.stderr == b''
    assert json.loads(before.stdout)['operation'] == json.loads(after.stdout)['operation'] == 'HOLD'
    rows.append({'case': 'synthetic_decisions_' + str(size), 'before_exit': before.returncode,
                 'after_exit': after.returncode, 'before_and_after_operation': 'HOLD'})
print(json.dumps({'evidence_kind': 'SYNTHETIC', 'finding': 'P2_OPTIONAL_MODEL_INPUT_CONTRACT',
                  'before_commit': BEFORE, 'status': 'PASS', 'cases': rows}, sort_keys=True, indent=2))
