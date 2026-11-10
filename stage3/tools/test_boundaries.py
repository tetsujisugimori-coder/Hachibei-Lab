"""Issue 17 synthetic boundary regressions; no operational evidence."""
import copy
import json
import unittest
from pathlib import Path
from approval import evaluate
from test_approval import fixture, event, state

class BoundaryTests(unittest.TestCase):
    def test_missing_execution(self):
        d=fixture();d['decisions'][0]['observed_choice']='EXECUTE'
        r=evaluate(d)['results'][0]
        self.assertEqual(r['decision']['status'],'VALID')
        self.assertEqual(r['execution']['status'],'INSUFFICIENT_EVIDENCE')
        self.assertIsNone(r['execution']['evaluated_at'])
        self.assertIn('execution_at',r['evidence_completeness']['missing'])
        self.assertEqual(r['consistency'],'NO_MISMATCH_IN_RECORDED_FIELDS')
        self.assertEqual(r['history_authenticity']['status'],'UNKNOWN')
        self.assertEqual(r['overall']['status'],'PARTIAL')

    def test_case001(self):
        rows=json.loads((Path(__file__).parents[1]/'synthetic-case-scenarios.json').read_text())
        d=rows[0]['input'];r=evaluate(d)['results'][0]
        self.assertEqual(r['decision']['status'],'VALID')
        self.assertEqual(r['execution']['status'],'INSUFFICIENT_EVIDENCE')

    def test_known_execution(self):
        for choice,consistency in [('EXECUTE','NO_MISMATCH_IN_RECORDED_FIELDS'),('HOLD','MISMATCH')]:
            d=fixture();d['decisions'][0].update(observed_choice=choice,execution_at='2026-01-01T13:00:00Z')
            r=evaluate(d)['results'][0]
            self.assertEqual(r['execution']['status'],'VALID');self.assertEqual(r['consistency'],consistency)

    def test_amend_expiry_matrix(self):
        for at,expected in [('2026-01-01T23:59:59.999999Z','VALID'),('2026-01-02T00:00:00Z','INSUFFICIENT_EVIDENCE'),('2026-01-02T00:00:00.000001Z','INSUFFICIENT_EVIDENCE')]:
            with self.subTest(at=at):
                d=fixture();event(d,'AMEND',at)['expires_at']='2026-01-03T00:00:00Z';d['decisions'][0]['decided_at']='2026-01-02T12:00:00Z'
                self.assertEqual(state(d),expected)

    def test_late_amend_does_not_rewrite_past(self):
        d=fixture();event(d,'AMEND','2026-01-02T01:00:00Z')['expires_at']='2026-01-03T00:00:00Z'
        self.assertEqual(state(d),'VALID')
        d['decisions'][0]['decided_at']='2026-01-02T00:30:00Z';self.assertEqual(state(d),'EXPIRED')

    def test_invalid_chain_cannot_be_repaired_by_amend(self):
        d=fixture();e=event(d,'AMEND','2026-01-02T00:00:00Z');e['expires_at']='2026-01-03T00:00:00Z'
        e=copy.deepcopy(e);e.update(id='E3',sequence=3,recorded_at='2026-01-02T01:00:00Z',effective_at='2026-01-02T01:00:00Z');d['approvals'][0]['events'].append(e)
        d['decisions'][0]['decided_at']='2026-01-02T12:00:00Z';self.assertEqual(state(d),'INSUFFICIENT_EVIDENCE')

    def test_recorded_before_but_effective_at_expiry(self):
        d=fixture();e=event(d,'AMEND','2026-01-01T23:00:00Z');e.update(effective_at='2026-01-02T00:00:00Z',expires_at=None)
        d['decisions'][0]['decided_at']='2026-01-02T12:00:00Z';self.assertEqual(state(d),'INSUFFICIENT_EVIDENCE')

    def test_backdated_extension(self):
        d=fixture();e=event(d,'AMEND','2026-01-02T01:00:00Z');e.update(effective_at='2026-01-01T23:00:00Z',expires_at=None)
        self.assertEqual(state(d),'INSUFFICIENT_EVIDENCE')

    def test_missing_period_vs_explicit_unbounded(self):
        for key in ('effective_at','expires_at'):
            d=fixture();del d['approvals'][0]['events'][0][key]
            with self.assertRaises(ValueError):evaluate(d)
        d=fixture();d['approvals'][0]['events'][0]['expires_at']=None;event(d,'AMEND')['expires_at']=None
        self.assertEqual(state(d),'VALID')

    def test_regrant_new_identity(self):
        d=fixture();a=copy.deepcopy(d['approvals'][0]);a['id']='SYN-NEW';a['events'][0].update(recorded_at='2026-01-02T00:00:00Z',effective_at='2026-01-02T00:00:00Z',expires_at=None)
        d['approvals'].append(a);d['decisions'][0].update(approval_ids=['SYN-NEW'],decided_at='2026-01-02T12:00:00Z');self.assertEqual(state(d),'VALID')

    def test_timezone_boundary(self):
        d=fixture();event(d,'AMEND','2026-01-02T09:00:00+09:00')['expires_at']=None;d['decisions'][0]['decided_at']='2026-01-02T12:00:00Z';self.assertEqual(state(d),'INSUFFICIENT_EVIDENCE')

    def test_no_execution_claim(self):
        r=evaluate(fixture())['results'][0];self.assertIsNone(r['execution']);self.assertEqual(r['overall']['status'],'PARTIAL')

    def test_utc_range_overflow(self):
        for value in ('0001-01-01T00:00:00+01:00', '9999-12-31T23:59:59-01:00'):
            d=fixture();d['decisions'][0]['execution_at']=value
            with self.assertRaisesRegex(ValueError, 'supported UTC range'):
                evaluate(d)
