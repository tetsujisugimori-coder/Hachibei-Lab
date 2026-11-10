"""Reproduce frozen Issue 17 counterexamples against the merged baseline."""
import importlib.util
import json
import subprocess
from pathlib import Path
from approval import evaluate
from test_approval import fixture, event
BASE='3733a7e757e597d4e00fc636fc36d74b2e8f9c20'
old={};exec(compile(subprocess.check_output(['git','show',BASE+':stage3/tools/approval.py'],text=True),'baseline','exec'),old)
rows=[]
d=fixture();d['decisions'][0]['observed_choice']='EXECUTE'
for name,data in [('missing_execution_at',d)]:
    before=old['evaluate'](data)['results'][0];after=evaluate(data)['results'][0]
    rows.append({'case':name,'input':data,'before':before,'after':after,'old_defect_reproduced':before['execution'] is None,'fixed':after['execution']['status']=='INSUFFICIENT_EVIDENCE'})
for at in ['2026-01-02T00:00:00Z','2026-01-02T00:00:00.000001Z']:
    d=fixture();event(d,'AMEND',at)['expires_at']=None;d['decisions'][0]['decided_at']='2026-01-02T12:00:00Z'
    before=old['evaluate'](d)['results'][0];after=evaluate(d)['results'][0]
    rows.append({'case':'amend_'+at,'input':d,'before':before,'after':after,'old_defect_reproduced':before['decision']['status']=='VALID','fixed':after['decision']['status']=='INSUFFICIENT_EVIDENCE'})
result={'baseline':BASE,'evidence_kind':'SYNTHETIC','rows':rows}
print(json.dumps(result,indent=2))
assert all(x['old_defect_reproduced'] and x['fixed'] for x in rows)
