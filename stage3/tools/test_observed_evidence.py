"""Synthetic boundary attacks only; never ingest real records into CI."""
import base64
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from evidence import canonical, digest
from observed_evidence import assess, build_ledger
from test_approval import fixture as model_fixture


def fixture():
    now = '2026-01-03T00:00:00Z'
    rows = []
    for i, (kind, state) in enumerate((('REVIEW', 'COMMENTED'), ('EXECUTION', 'MERGED'))):
        raw = canonical({'synthetic': True, 'kind': kind, 'state': state})
        rows.append({'id': 'SYN-' + str(i), 'native_id': 'synthetic:record:' + str(i), 'revision': '1',
                     'previous_id': None, 'kind': kind, 'actor': 'synthetic actor',
                     'target': 'synthetic:target', 'action': 'synthetic:merge', 'state': state,
                     'recorded_at': '2026-01-01T00:00:00Z', 'retrieved_at': now,
                     'representation': 'SOURCE_BYTES', 'bytes_base64': base64.b64encode(raw).decode(),
                     'sha256': digest(raw)})
    return {'schema_version': '1.0', 'evidence_kind': 'SYNTHETIC', 'observed_at': now,
            'window': {'start': '2026-01-01T00:00:00Z', 'end': now},
            'source': {'controller': 'synthetic controller', 'acquisition': 'synthetic offline fixture',
                       'access_scope': 'synthetic query only', 'from_origin': True,
                       'revisions_visible': 'UNKNOWN', 'deletions_visible': 'UNKNOWN'},
            'records': rows,
            'pages': [{'cursor': None, 'next_cursor': 'synthetic:page2', 'retrieved_at': now,
                       'record_ids': ['SYN-0', 'SYN-1'], 'reported_total': None},
                      {'cursor': 'synthetic:page2', 'next_cursor': None, 'retrieved_at': now,
                       'record_ids': [], 'reported_total': None}],
            'expectation': {'approver': 'synthetic actor', 'actor': 'synthetic actor',
                            'target': 'synthetic:target', 'action': 'synthetic:merge'}, 'model': None}


class ObservedEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.data = fixture()

    def result(self):
        return assess(self.data)

    def add_explicit(self):
        row = copy.deepcopy(self.data['records'][0])
        row.update(id='SYN-APPROVAL', native_id='synthetic:approval', kind='EXPLICIT_APPROVAL', state='EXPLICIT')
        self.data['records'].append(row)
        self.data['pages'][0]['record_ids'].append(row['id'])
        return row

    def test_default_hold_and_no_explicit_approval(self):
        r = self.result()
        self.assertEqual(r['explicit_approval'], 'NOT_OBTAINED')
        self.assertEqual(r['review_commented'], 'CLAIMED')
        self.assertEqual(r['review_approved'], 'UNKNOWN')
        self.assertEqual(r['merge_record'], 'CLAIMED')
        self.assertEqual(r['operation'], 'HOLD')
        self.assertEqual(r['status'], 'INSUFFICIENT_EVIDENCE')
        self.assertEqual(r['model_evaluation'], 'NOT_EVALUABLE')
        self.assertEqual(r['preservation'], 'NOT_PRESERVED')
        self.assertEqual(r['limited_technical_acceptance'], 'PARTIAL')

    def test_actual_review_approve_is_not_user_approval(self):
        self.data['records'][0]['state'] = 'APPROVED'
        r = self.result()
        self.assertEqual(r['review_approved'], 'CLAIMED')
        self.assertEqual(r['explicit_approval'], 'NOT_OBTAINED')

    def test_explicit_record_still_not_authenticated(self):
        self.add_explicit()
        r = self.result()
        self.assertEqual(r['explicit_approval'], 'CLAIMED')
        self.assertEqual(r['approval_action_correspondence'], 'CLAIMED')
        for k in ('identity', 'authenticity', 'authority_at_approval', 'validity_period', 'history_coverage'):
            self.assertEqual(r[k], 'UNKNOWN')

    def test_mismatched_approver(self):
        self.add_explicit()['actor'] = 'synthetic other actor'
        self.assertEqual(self.result()['approval_action_correspondence'], 'CONFLICT')

    def test_mismatched_action_actor(self):
        self.data['records'][1]['actor'] = 'synthetic other actor'
        self.assertEqual(self.result()['status'], 'CONFLICT')

    def test_mismatched_target(self):
        self.add_explicit()['target'] = 'synthetic:other'
        self.assertEqual(self.result()['status'], 'CONFLICT')

    def test_mismatched_action(self):
        self.add_explicit()['action'] = 'synthetic:publish'
        self.assertEqual(self.result()['status'], 'CONFLICT')

    def test_unobserved_expectation_not_match(self):
        self.add_explicit()
        self.data['expectation'] = dict.fromkeys(self.data['expectation'])
        self.assertEqual(self.result()['approval_action_correspondence'], 'UNKNOWN')

    def test_partial_approval_cannot_borrow_complete_execution(self):
        self.add_explicit()['actor'] = None
        self.assertEqual(self.result()['approval_action_correspondence'], 'UNKNOWN')

    def test_partial_execution_cannot_borrow_complete_approval(self):
        self.data['records'][1]['action'] = None
        self.add_explicit()
        self.assertEqual(self.result()['approval_action_correspondence'], 'UNKNOWN')

    def test_post_execution_approval_not_retroactive(self):
        self.add_explicit()['recorded_at'] = '2026-01-02T00:00:00Z'
        r = self.result()
        self.assertEqual(r['approval_execution_order'], 'RECORDED_AFTER_EXECUTION')
        self.assertEqual(r['approval_action_correspondence'], 'UNKNOWN')
        self.assertEqual(r['validity_period'], 'UNKNOWN')

    def test_unknown_approval_state_not_correlated(self):
        self.add_explicit()['state'] = 'UNKNOWN'
        self.assertEqual(self.result()['approval_action_correspondence'], 'UNKNOWN')

    def test_unknown_execution_state_not_correlated(self):
        self.add_explicit()
        self.data['records'][1]['state'] = 'UNKNOWN'
        self.assertEqual(self.result()['approval_action_correspondence'], 'UNKNOWN')

    def test_source_digest_match_not_authenticity(self):
        r = self.result()
        self.assertEqual(r['source_original_integrity'], 'MATCH')
        self.assertEqual(r['authenticity'], 'UNKNOWN')
        self.assertEqual(r['preservation'], 'NOT_PRESERVED')

    def test_normalized_digest_not_original_hash(self):
        for row in self.data['records']:
            row['representation'] = 'CONNECTOR_JSON'
        r = self.result()
        self.assertEqual(r['source_original_integrity'], 'NOT_TESTED')
        self.assertEqual(r['supplied_representation_integrity'], 'MATCH')

    def test_missing_one_original_prevents_full_match(self):
        self.data['records'][0]['representation'] = 'NORMALIZED_OBSERVATION'
        self.assertEqual(self.result()['source_original_integrity'], 'NOT_TESTED')

    def test_missing_bytes(self):
        self.data['records'][0]['bytes_base64'] = None
        self.assertEqual(self.result()['source_original_integrity'], 'NOT_TESTED')

    def test_missing_hash(self):
        self.data['records'][0]['sha256'] = None
        self.assertEqual(self.result()['source_original_integrity'], 'NOT_TESTED')

    def test_hash_mismatch(self):
        self.data['records'][0]['sha256'] = '0' * 64
        self.assertEqual(self.result()['status'], 'CONFLICT')

    def test_changed_payload_rehashed_never_semantically_verified(self):
        row = self.data['records'][0]
        raw = b'{"synthetic_changed":true}'
        row.update(bytes_base64=base64.b64encode(raw).decode(), sha256=digest(raw))
        self.assertEqual(self.result()['normalization_fidelity'], 'UNKNOWN')

    def test_changed_same_revision_conflicts(self):
        row = copy.deepcopy(self.data['records'][0]); row['id'] = 'SYN-ALT'; row['state'] = 'APPROVED'
        self.data['records'].append(row)
        self.assertEqual(self.result()['status'], 'CONFLICT')

    def test_missing_predecessor_retains_insufficient(self):
        self.data['records'][0]['previous_id'] = 'synthetic:missing'
        self.assertEqual(self.result()['foundation_status'], 'INSUFFICIENT_EVIDENCE')

    def test_history_cycle(self):
        self.data['records'][0]['previous_id'] = self.data['records'][0]['id']
        self.assertEqual(self.result()['foundation_status'], 'CONFLICT')

    def test_amend_revoke_delete_never_promote(self):
        for kind, state in (('AMENDMENT', 'AMENDED'), ('REVOCATION', 'REVOKED'), ('DELETION', 'DELETED')):
            with self.subTest(kind=kind):
                self.data = fixture(); self.add_explicit().update(kind=kind, state=state)
                r = self.result()
                self.assertEqual(r['change_signal'], 'CLAIMED')
                self.assertEqual(r['explicit_approval'], 'NOT_OBTAINED')
                self.assertEqual(r['status'], 'INSUFFICIENT_EVIDENCE')

    def test_pages_contiguous_but_missing_receipts_incomplete(self):
        self.assertEqual(self.result()['page_traversal'], 'INCOMPLETE')
        self.assertEqual(self.result()['history_coverage'], 'UNKNOWN')

    def test_missing_middle_page(self):
        self.data['pages'][1]['cursor'] = 'synthetic:page3'
        self.assertEqual(self.result()['page_traversal'], 'CONFLICT')

    def test_cursor_loop(self):
        self.data['pages'].append(copy.deepcopy(self.data['pages'][0]))
        self.assertEqual(self.result()['page_traversal'], 'CONFLICT')

    def test_empty_nonterminal_not_complete(self):
        self.data['pages'][1]['next_cursor'] = 'synthetic:more'
        self.assertEqual(self.result()['page_traversal'], 'INCOMPLETE')

    def test_changed_total(self):
        self.data['pages'][0]['reported_total'] = 2
        self.data['pages'][1]['reported_total'] = 3
        self.assertEqual(self.result()['page_traversal'], 'CONFLICT')

    def test_no_records_not_obtained(self):
        self.data['records'] = []; self.data['pages'] = []
        self.assertEqual(self.result()['acquisition'], 'NOT_OBTAINED')

    def test_visibility_claims_do_not_prove_history(self):
        self.data['source'].update(revisions_visible='YES', deletions_visible='YES')
        self.assertEqual(self.result()['history_coverage'], 'UNKNOWN')

    def test_model_conditional_valid_not_accepted(self):
        self.data['model'] = model_fixture()
        r = self.result()
        self.assertIn('VALID', r['conditional_model_states'])
        self.assertEqual(r['model_evaluation'], 'CONDITIONAL_ONLY')
        self.assertEqual(r['foundation_status'], 'INSUFFICIENT_EVIDENCE')
        self.assertEqual(r['model_mapping'], 'NO_SEMANTIC_BINDINGS')
        self.assertEqual(r['operation'], 'HOLD')

    def test_other_mapping_does_not_fabricate_approval_or_decision(self):
        ledger, model = build_ledger(self.data)
        self.assertEqual({r['role'] for r in ledger['records']}, {'OTHER'})
        self.assertEqual(model['approvals'], []); self.assertEqual(model['decisions'], [])
        self.assertEqual(ledger['bindings'], [])
        self.assertTrue(all(r['original_artifact'] is None for r in ledger['records']))

    def test_memory_only_no_filesystem_reader(self):
        with patch('evidence.artifact', side_effect=AssertionError('no filesystem')):
            self.assertEqual(self.result()['operation'], 'HOLD')

    def test_no_mutation(self):
        before = copy.deepcopy(self.data)
        self.result()
        self.assertEqual(self.data, before)

    def test_private_canary_does_not_escape(self):
        private = 'synthetic-private-canary@example.invalid/query?record=opaque'
        self.data['source']['access_scope'] = private
        self.data['source']['controller'] = private
        self.data['records'][0]['native_id'] = private
        self.data['records'][0]['actor'] = private
        out = json.dumps(self.result())
        self.assertNotIn(private, out)
        self.assertNotIn('synthetic:record', out)
        self.assertNotIn('2026-', out)
        self.assertNotIn('reported_total', out)

    def test_invalid_enums(self):
        self.data['records'][0]['state'] = 'EXPLICIT'
        with self.assertRaises(ValueError): self.result()

    def test_bool_total_rejected(self):
        self.data['pages'][0]['reported_total'] = True
        with self.assertRaises(ValueError): self.result()

    def test_absent_bytes_cannot_claim_hash(self):
        self.data['records'][0]['representation'] = 'NOT_OBTAINED'
        with self.assertRaises(ValueError): self.result()

    def test_naive_and_future_timestamps_rejected(self):
        for value in ('2026-01-01T00:00:00', '2027-01-01T00:00:00Z'):
            self.data = fixture(); self.data['records'][0]['retrieved_at'] = value
            with self.assertRaises(ValueError): self.result()

    def test_cli_safe_errors(self):
        path = Path(__file__).with_name('observed_evidence.py')
        for raw in (b'{"private-canary":', b'{"x":1,"x":2}', b'1e999', b'"\\ud800"', b'[' * 1200):
            p = subprocess.run([sys.executable, str(path)], input=raw, capture_output=True)
            self.assertEqual(p.returncode, 2)
            self.assertEqual(p.stderr, b'')
            self.assertNotIn(b'private-canary', p.stdout)
            self.assertEqual(json.loads(p.stdout)['operation'], 'HOLD')

    def test_cli_size_bound(self):
        p = subprocess.run([sys.executable, str(Path(__file__).with_name('observed_evidence.py'))],
                           input=b' ' * (4 * 1024 * 1024 + 1), capture_output=True)
        self.assertEqual(p.returncode, 2); self.assertEqual(p.stderr, b'')

    def test_cli_success_projection(self):
        p = subprocess.run([sys.executable, str(Path(__file__).with_name('observed_evidence.py'))],
                           input=canonical(self.data), capture_output=True)
        self.assertEqual(p.returncode, 0); self.assertEqual(p.stderr, b'')
        self.assertEqual(json.loads(p.stdout), self.result())


if __name__ == '__main__':
    unittest.main()
