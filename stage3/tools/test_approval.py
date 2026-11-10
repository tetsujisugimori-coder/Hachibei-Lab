import copy
import json
from pathlib import Path
import unittest
from approval import evaluate, instant, explain


def fixture():
    return {'schema_version':'1.0','evidence_kind':'SYNTHETIC','observed_at':'2026-01-03T00:00:00Z','history_complete_through':'2026-01-03T00:00:00Z','approvals':[{'id':'SYN-A','issuer':'synthetic owner','authority':{'status':'VERIFIED','evidence':'synthetic authority fixture'},'source':'synthetic:grant','version':'1','retrieved_at':'2026-01-03T00:00:00Z','events':[{'id':'E1','sequence':1,'kind':'GRANT','recorded_at':'2026-01-01T00:00:00Z','effective_at':'2026-01-01T00:00:00Z','expires_at':'2026-01-02T00:00:00Z','actions':['read'],'targets':['synthetic:document'],'conditions':{'mode':'offline'},'evidence':'synthetic:event'}]}],'decisions':[{'id':'SYN-D','action':'read','target':'synthetic:document','approval_ids':['SYN-A'],'proposed_at':'2026-01-01T00:00:00Z','decided_at':'2026-01-01T12:00:00Z','execution_at':None,'completed_at':None,'observed_choice':'HOLD','conditions':{'mode':'offline'},'evidence':'synthetic:decision'}]}


def event(data,kind='REVOKE',when='2026-01-01T11:00:00Z'):
    e=copy.deepcopy(data['approvals'][0]['events'][0]); e.update(id='E2',sequence=2,kind=kind,recorded_at=when,effective_at=when); data['approvals'][0]['events'].append(e); return e


def state(data): return evaluate(data)['results'][0]['decision']['status']


class ApprovalTests(unittest.TestCase):
    def test_valid(self): self.assertEqual(state(fixture()),'VALID')
    def test_no_side_effect_input(self):
        d=fixture(); old=copy.deepcopy(d); evaluate(d); self.assertEqual(d,old)
    def test_no_records(self):
        d=fixture();d['approvals']=[];self.assertEqual(state(d),'NO_RECORD')
    def test_no_references(self):
        d=fixture();d['decisions'][0]['approval_ids']=[];self.assertEqual(state(d),'NO_RECORD')
    def test_scope(self):
        for field in ('action','target'):
            d=fixture();d['decisions'][0][field]='different';self.assertEqual(state(d),'OUT_OF_SCOPE')
    def test_before(self):
        d=fixture();d['decisions'][0].update(proposed_at=None,decided_at='2025-12-31T23:59:59Z');self.assertEqual(state(d),'NOT_YET_EFFECTIVE')
    def test_start_inclusive(self):
        d=fixture();d['decisions'][0]['decided_at']='2026-01-01T00:00:00Z';self.assertEqual(state(d),'VALID')
    def test_end_exclusive(self):
        for t in ('2026-01-02T00:00:00Z','2026-01-02T00:00:00.000001Z'):
            d=fixture();d['decisions'][0]['decided_at']=t;self.assertEqual(state(d),'EXPIRED')
    def test_before_end(self):
        d=fixture();d['decisions'][0]['decided_at']='2026-01-01T23:59:59.999999Z';self.assertEqual(state(d),'VALID')
    def test_no_expiry(self):
        d=fixture();d['approvals'][0]['events'][0]['expires_at']=None;self.assertEqual(state(d),'VALID')
    def test_revoke(self):
        d=fixture();event(d);self.assertEqual(state(d),'REVOKED')
    def test_revoke_boundary(self):
        d=fixture();event(d,when=d['decisions'][0]['decided_at']);self.assertEqual(state(d),'REVOKED')
    def test_before_revoke(self):
        d=fixture();event(d,when='2026-01-01T13:00:00Z');self.assertEqual(state(d),'VALID')
    def test_execution_revalidation(self):
        d=fixture();event(d,when='2026-01-01T13:00:00Z');d['decisions'][0].update(execution_at='2026-01-01T14:00:00Z',observed_choice='EXECUTE');r=evaluate(d)['results'][0];self.assertEqual(r['decision']['status'],'VALID');self.assertEqual(r['execution']['status'],'REVOKED');self.assertEqual(r['consistency'],'MISMATCH')
    def test_shrink(self):
        d=fixture();event(d,'AMEND')['targets']=['other'];self.assertEqual(state(d),'OUT_OF_SCOPE')
    def test_condition(self):
        d=fixture();d['decisions'][0]['conditions']={};self.assertEqual(state(d),'INSUFFICIENT_EVIDENCE');d['decisions'][0]['conditions']={'mode':'online'};self.assertEqual(state(d),'OUT_OF_SCOPE')
    def test_bool_not_integer(self):
        d=fixture();d['approvals'][0]['events'][0]['conditions']={'flag':1};d['decisions'][0]['conditions']={'flag':True};self.assertEqual(state(d),'OUT_OF_SCOPE')
    def test_authority_unknown(self):
        d=fixture();d['approvals'][0]['authority']['status']='UNKNOWN';self.assertEqual(state(d),'INSUFFICIENT_EVIDENCE')
    def test_missing_history(self):
        d=fixture();d['approvals'][0]['events']=[];self.assertEqual(state(d),'INSUFFICIENT_EVIDENCE')
    def test_coverage(self):
        for v in (None,'2026-01-01T11:59:59Z'):
            d=fixture();d['history_complete_through']=v;self.assertEqual(state(d),'INSUFFICIENT_EVIDENCE')
    def test_gap(self):
        d=fixture();event(d)['sequence']=3;self.assertEqual(state(d),'CONFLICT')
    def test_duplicate_sequence(self):
        d=fixture();event(d)['sequence']=1;self.assertEqual(state(d),'CONFLICT')
    def test_reverse_order(self):
        d=fixture();event(d);d['approvals'][0]['events'].reverse();self.assertEqual(state(d),'CONFLICT')
    def test_backdate(self):
        d=fixture();event(d)['effective_at']='2026-01-01T01:00:00Z';self.assertEqual(state(d),'INSUFFICIENT_EVIDENCE')
    def test_correction(self):
        d=fixture();event(d,'CORRECT');self.assertEqual(state(d),'INSUFFICIENT_EVIDENCE')
    def test_after_revoke(self):
        d=fixture();event(d);e=copy.deepcopy(d['approvals'][0]['events'][-1]);e.update(id='E3',sequence=3,kind='AMEND');d['approvals'][0]['events'].append(e);self.assertEqual(state(d),'CONFLICT')
    def test_grant_repeat(self):
        d=fixture();event(d,'GRANT');self.assertEqual(state(d),'CONFLICT')
    def test_multiple_approvals(self):
        d=fixture();a=copy.deepcopy(d['approvals'][0]);a['id']='SYN-B';d['approvals'].append(a);d['decisions'][0]['approval_ids'].append('SYN-B');self.assertEqual(state(d),'VALID');a['events'][0]['targets']=['other'];self.assertEqual(state(d),'CONFLICT')
    def test_timezone(self):
        d=fixture();d['decisions'][0]['decided_at']='2026-01-01T21:00:00+09:00';self.assertEqual(state(d),'VALID')
    def test_invalid_inputs(self):
        mutations=[lambda d:d.update(schema_version='2'),lambda d:d.update(extra=True),lambda d:d.update(observed_at='bad'),lambda d:d.update(history_complete_through='2027-01-01T00:00:00Z'),lambda d:d['approvals'].append(copy.deepcopy(d['approvals'][0])),lambda d:d['approvals'][0]['authority'].update(evidence=''),lambda d:d['approvals'][0]['events'][0].update(actions=['*']),lambda d:d['approvals'][0]['events'][0].update(expires_at='2025-01-01T00:00:00Z'),lambda d:d['decisions'][0].update(decided_at=None),lambda d:d['decisions'][0].update(execution_at='2025-01-01T00:00:00Z'),lambda d:d['decisions'][0].update(completed_at='2026-01-02T00:00:00Z'),lambda d:d['decisions'][0].update(observed_choice='SUCCESS')]
        for n,m in enumerate(mutations):
            with self.subTest(n=n):
                d=fixture();m(d)
                with self.assertRaises(ValueError):evaluate(d)
    def test_timestamp_rejects(self):
        for x in ('2026-01-01','2026-01-01T00:00:00','2026-02-30T00:00:00Z',False):
            with self.assertRaises(ValueError):instant(x)
    def test_explanation(self): self.assertIn('synthetic:grant',explain(evaluate(fixture())))
    def test_stage2_case_ids(self):
        root=Path(__file__).resolve().parents[2];mapping=json.loads((root/'stage3/case-map.json').read_text());text=(root/'stage2/behavior-model.md').read_text();self.assertEqual(len(mapping),6)
        for row in mapping:self.assertIn(row['stage2_case'],text);self.assertEqual(row['kind'],'DESIGN_ONLY')
    def test_fixture_json(self): self.assertEqual(state(json.loads((Path(__file__).parents[1]/'synthetic.json').read_text())),'VALID')
