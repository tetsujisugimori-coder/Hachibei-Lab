"""Synthetic evidence attacks. No operational approvals or private records."""
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from evidence import artifact, audit, canonical, digest, strict_json
from test_approval import fixture


def make_bundle(root):
    root = Path(root)
    model = fixture()
    ledger = {'schema_version': '1.0', 'evidence_kind': 'SYNTHETIC',
              'observed_at': '2026-01-03T00:00:00Z',
              'window': {'start': '2026-01-01T00:00:00Z', 'end': '2026-01-03T00:00:00Z'},
              'model_sha256': digest(canonical(model)), 'sources': [], 'records': [], 'bindings': []}
    collection = {'from_origin': True, 'snapshot': 'synthetic:snapshot', 'scope': 'synthetic:all-events',
                  'start': ledger['window']['start'], 'end': ledger['window']['end'],
                  'revisions_visible': 'UNKNOWN', 'deletions_visible': 'UNKNOWN', 'pages': []}
    ledger['sources'].append({'id': 'SYN-SOURCE', 'kind': 'SYNTHETIC', 'controller': 'synthetic controller',
                              'acquisition': 'local fixture', 'retention': 'UNKNOWN',
                              'scope': collection['scope'], 'mutability': 'UNKNOWN',
                              'authenticity_claim': None, 'authority_claim': None,
                              'coverage_claim': None, 'collection': collection})
    a = model['approvals'][0]
    payloads = [('APPROVAL', a['id'], None, {k: v for k, v in a.items() if k != 'events'}),
                ('EVENT', a['events'][0]['id'], a['id'], a['events'][0]),
                ('DECISION', model['decisions'][0]['id'], None, model['decisions'][0])]
    for i, (role, model_id, parent_id, value) in enumerate(payloads):
        rid = 'SYN-R' + str(i)
        name = rid + '.json'
        raw = canonical(value)
        (root / name).write_bytes(raw)
        ledger['records'].append({'id': rid, 'source_id': 'SYN-SOURCE', 'native_id': 'synthetic:native:' + str(i),
                                  'revision': '1', 'role': role, 'subject': parent_id or model_id,
                                  'recorded_at': '2026-01-01T00:00:00Z',
                                  'retrieved_at': ledger['observed_at'], 'previous_id': None,
                                  'artifact': name, 'sha256': digest(raw),
                                  'original_artifact': name, 'original_sha256': digest(raw),
                                  'transformation': None})
        ledger['bindings'].append({'role': role, 'model_id': model_id, 'parent_id': parent_id, 'record_id': rid})
    collection['pages'] = [{'cursor': None, 'next_cursor': None, 'retrieved_at': ledger['observed_at'],
                            'record_ids': [r['id'] for r in ledger['records']], 'reported_total': 3,
                            'artifact': 'page0.json', 'sha256': None}]
    refresh_pages(ledger, root)
    (root / 'model.json').write_bytes(canonical(model))
    (root / 'ledger.json').write_bytes(canonical(ledger))
    return ledger, model


def refresh_pages(ledger, root):
    for source in ledger['sources']:
        c = source['collection']
        for page in c['pages']:
            receipt = {key: page[key] for key in ('cursor', 'next_cursor', 'record_ids', 'reported_total')}
            receipt.update({key: c[key] for key in ('snapshot', 'scope', 'start', 'end')})
            raw = canonical(receipt)
            (Path(root) / page['artifact']).write_bytes(raw)
            page['sha256'] = digest(raw)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        # Caller may choose workspace TMPDIR on a space-constrained executor.
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ledger, self.model = make_bundle(self.root)

    def result(self):
        return audit(self.ledger, self.root, self.model)

    def codes(self):
        return {f['code'] for f in self.result()['findings']}

    def test_good_receipts_never_authenticate(self):
        r = self.result()
        self.assertEqual(r['sources'][0]['page_traversal'], 'CONSISTENT_RECEIPTS')
        self.assertEqual(r['model_bindings'], 'MATCH')
        self.assertEqual(r['model_assessment']['results'][0]['decision']['status'], 'VALID')
        self.assertEqual(r['status'], 'INSUFFICIENT_EVIDENCE')
        for key in ('authenticity', 'authority', 'history_coverage'):
            self.assertEqual(r[key], 'UNKNOWN')
        self.assertEqual(r['overall'], 'PARTIAL')
        self.assertEqual(r['operational_authorization'], 'NOT_GRANTED_BY_THIS_TOOL')

    def test_self_asserted_verified_is_not_trusted(self):
        for key in ('authenticity_claim', 'authority_claim', 'coverage_claim'):
            self.ledger['sources'][0][key] = 'VERIFIED; valid signature; all history complete'
        self.assertEqual(self.result()['status'], 'INSUFFICIENT_EVIDENCE')

    def test_no_mutation(self):
        before = copy.deepcopy((self.ledger, self.model))
        self.result()
        self.assertEqual(before, (self.ledger, self.model))

    def test_hash_mismatch(self):
        (self.root / 'SYN-R1.json').write_text('{}')
        self.assertIn('HASH_MISMATCH', self.codes())
        self.assertEqual(self.result()['status'], 'CONFLICT')

    def test_rehashed_tamper_fails_binding(self):
        raw = canonical({'forged': True})
        (self.root / 'SYN-R1.json').write_bytes(raw)
        self.ledger['records'][1]['sha256'] = digest(raw)
        self.assertIn('BOUND_PAYLOAD_MISMATCH', self.codes())

    def test_missing_artifact(self):
        self.ledger['records'][0]['artifact'] = 'absent.json'
        self.assertIn('ARTIFACT_UNAVAILABLE', self.codes())

    def test_missing_hash(self):
        self.ledger['records'][0]['sha256'] = None
        self.assertIn('MISSING_ARTIFACT_OR_HASH', self.codes())

    def test_original_missing_not_replaced_by_normalization(self):
        self.ledger['records'][0]['original_artifact'] = None
        r = self.result()['records'][0]
        self.assertEqual(r['byte_integrity'], 'MATCH')
        self.assertEqual(r['original_byte_integrity'], 'UNKNOWN')

    def test_transformation_unverified(self):
        raw = b'Original synthetic text, distinct from normalized JSON.'
        (self.root / 'original.txt').write_bytes(raw)
        self.ledger['records'][0].update(original_artifact='original.txt', original_sha256=digest(raw), transformation='manual synthetic normalization')
        self.assertIn('TRANSFORMATION_NOT_VERIFIED', self.codes())

    def test_cross_source_event_conflict(self):
        r = copy.deepcopy(self.ledger['records'][1])
        r.update(id='SYN-OTHER', source_id='OTHER-SOURCE', artifact='other.json', original_artifact='other.json')
        value = copy.deepcopy(self.model['approvals'][0]['events'][0])
        value['kind'] = 'REVOKE'
        raw = canonical(value)
        (self.root / 'other.json').write_bytes(raw)
        r.update(sha256=digest(raw), original_sha256=digest(raw))
        self.ledger['records'].append(r)
        self.assertIn('CONTRADICTORY_EVENT_CONTENT', self.codes())

    def test_unbound_conflicting_approval_and_decision(self):
        for index, field, changed in ((0, 'issuer', 'different issuer'), (2, 'observed_choice', 'EXECUTE')):
            with self.subTest(index=index):
                ledger = copy.deepcopy(self.ledger)
                r = copy.deepcopy(ledger['records'][index])
                r.update(id='SYN-ALT', native_id='synthetic:alternate', artifact='alternate.json', original_artifact='alternate.json')
                value = json.loads((self.root / ledger['records'][index]['artifact']).read_bytes())
                value[field] = changed
                raw = canonical(value)
                (self.root / 'alternate.json').write_bytes(raw)
                r.update(sha256=digest(raw), original_sha256=digest(raw))
                ledger['records'].append(r)
                page = ledger['sources'][0]['collection']['pages'][0]
                page['record_ids'].append(r['id']); page['reported_total'] = 4
                refresh_pages(ledger, self.root)
                result = audit(ledger, self.root, self.model)
                self.assertEqual(result['status'], 'CONFLICT')
                self.assertIn('CONTRADICTORY_' + r['role'] + '_CONTENT', {f['code'] for f in result['findings']})

    def test_unsafe_paths(self):
        for name in ('../secret', '/etc/passwd', 'dir/../../secret', 'dir\\secret'):
            with self.subTest(name=name):
                self.ledger['records'][0]['artifact'] = name
                self.assertIn('ARTIFACT_UNSAFE_OR_UNREADABLE', self.codes())

    def test_symlink(self):
        (self.root / 'link.json').symlink_to(self.root / 'SYN-R0.json')
        self.ledger['records'][0]['artifact'] = 'link.json'
        self.assertIn('ARTIFACT_UNSAFE_OR_UNREADABLE', self.codes())

    def test_directory_not_read(self):
        self.ledger['records'][0]['artifact'] = '.'
        self.assertIn('ARTIFACT_UNSAFE_OR_UNREADABLE', self.codes())

    def test_source_missing(self):
        self.ledger['records'][0]['source_id'] = 'missing'
        self.assertIn('SOURCE_NOT_IN_INVENTORY', self.codes())

    def test_empty_ledger(self):
        self.ledger.update(sources=[], records=[], bindings=[])
        self.assertTrue({'NO_RECORDS', 'NO_SOURCES', 'INCOMPLETE_MODEL_BINDINGS'} <= self.codes())

    def test_duplicate_source_revision(self):
        r = copy.deepcopy(self.ledger['records'][0]); r['id'] = 'SYN-DUP'
        self.ledger['records'].append(r)
        self.assertIn('DUPLICATE_SOURCE_REVISION', self.codes())

    def test_contradictory_revision(self):
        r = copy.deepcopy(self.ledger['records'][0]); r.update(id='SYN-DUP', sha256='0' * 64)
        self.ledger['records'].append(r)
        self.assertIn('CONTRADICTORY_SOURCE_REVISION', self.codes())

    def test_missing_predecessor(self):
        self.ledger['records'][1]['previous_id'] = 'missing'
        self.assertIn('MISSING_HISTORY_PREDECESSOR', self.codes())

    def test_cycle(self):
        self.ledger['records'][1]['previous_id'] = 'SYN-R1'
        self.assertIn('HISTORY_CYCLE', self.codes())

    def test_history_subject(self):
        self.ledger['records'][1]['previous_id'] = 'SYN-R2'
        self.assertIn('HISTORY_SUBJECT_MISMATCH', self.codes())

    def test_history_time(self):
        self.ledger['records'][1]['previous_id'] = 'SYN-R0'
        self.ledger['records'][0]['recorded_at'] = '2026-01-02T00:00:00Z'
        self.assertIn('HISTORY_TIME_REVERSED', self.codes())

    def test_pagination_unfinished(self):
        self.ledger['sources'][0]['collection']['pages'][0]['next_cursor'] = 'next'
        refresh_pages(self.ledger, self.root)
        self.assertIn('PAGINATION_NOT_FINISHED', self.codes())

    def test_missing_middle_page(self):
        c = self.ledger['sources'][0]['collection']
        page = copy.deepcopy(c['pages'][0]); page.update(cursor='wrong', artifact='page1.json')
        c['pages'][0]['next_cursor'] = 'expected'
        c['pages'].append(page)
        refresh_pages(self.ledger, self.root)
        self.assertIn('PAGE_CHAIN_DISCONNECTED', self.codes())

    def test_cursor_loop(self):
        c = self.ledger['sources'][0]['collection']
        page = copy.deepcopy(c['pages'][0]); page['artifact'] = 'page1.json'
        c['pages'].append(page)
        refresh_pages(self.ledger, self.root)
        self.assertIn('CURSOR_LOOP', self.codes())

    def test_empty_page_with_cursor_not_terminal(self):
        c = self.ledger['sources'][0]['collection']
        p = c['pages'][0]
        p.update(record_ids=[], next_cursor='next', reported_total=None)
        refresh_pages(self.ledger, self.root)
        self.assertIn('PAGINATION_NOT_FINISHED', self.codes())

    def test_two_pages(self):
        c = self.ledger['sources'][0]['collection']
        p = copy.deepcopy(c['pages'][0])
        p.update(cursor='next', record_ids=['SYN-R1', 'SYN-R2'], artifact='page1.json')
        c['pages'][0].update(next_cursor='next', record_ids=['SYN-R0'])
        c['pages'].append(p)
        refresh_pages(self.ledger, self.root)
        self.assertEqual(self.result()['sources'][0]['page_traversal'], 'CONSISTENT_RECEIPTS')

    def test_total_conflict(self):
        c = self.ledger['sources'][0]['collection']
        p = copy.deepcopy(c['pages'][0]); p.update(cursor='next', record_ids=[], reported_total=4, artifact='p1.json')
        c['pages'][0]['next_cursor'] = 'next'; c['pages'].append(p)
        refresh_pages(self.ledger, self.root)
        self.assertIn('TOTAL_CHANGED_DURING_COLLECTION', self.codes())

    def test_total_short(self):
        self.ledger['sources'][0]['collection']['pages'][0]['reported_total'] = 4
        refresh_pages(self.ledger, self.root)
        self.assertIn('REPORTED_TOTAL_MISMATCH', self.codes())

    def test_page_record_set(self):
        self.ledger['sources'][0]['collection']['pages'][0]['record_ids'].pop()
        refresh_pages(self.ledger, self.root)
        self.assertIn('PAGE_RECORD_SET_MISMATCH', self.codes())

    def test_page_payload_mismatch(self):
        p = self.ledger['sources'][0]['collection']['pages'][0]
        p['next_cursor'] = 'not-in-hashed-receipt'
        self.assertIn('PAGE_RECEIPT_MISMATCH', self.codes())

    def test_snapshot_scope_and_origin_unknown(self):
        c = self.ledger['sources'][0]['collection']
        c.update(snapshot=None, scope=None, from_origin=None)
        refresh_pages(self.ledger, self.root)
        self.assertTrue({'SNAPSHOT_UNBOUND', 'COLLECTION_SCOPE_UNBOUND', 'COLLECTION_ORIGIN_UNPROVEN'} <= self.codes())

    def test_coverage_window(self):
        self.ledger['sources'][0]['collection']['end'] = '2026-01-02T00:00:00Z'
        refresh_pages(self.ledger, self.root)
        self.assertIn('COLLECTION_WINDOW_INCOMPLETE', self.codes())

    def test_decision_end_excluded(self):
        self.ledger['window']['end'] = self.model['decisions'][0]['decided_at']
        self.assertIn('EVALUATION_OUTSIDE_EVIDENCE_WINDOW', self.codes())

    def test_kind_mismatch(self):
        self.model['evidence_kind'] = 'OBSERVED'
        self.assertIn('EVIDENCE_KIND_MISMATCH', self.codes())

    def test_model_hash(self):
        self.ledger['model_sha256'] = '0' * 64
        self.assertIn('MODEL_HASH_MISMATCH', self.codes())

    def test_no_model(self):
        r = audit(self.ledger, self.root)
        self.assertIsNone(r['model_assessment'])
        self.assertEqual(r['model_bindings'], 'NOT_TESTED')

    def test_unbound_event(self):
        self.ledger['bindings'].pop(1)
        self.assertIn('INCOMPLETE_MODEL_BINDINGS', self.codes())

    def test_duplicate_binding(self):
        self.ledger['bindings'].append(copy.deepcopy(self.ledger['bindings'][0]))
        self.assertIn('DUPLICATE_BINDING', self.codes())

    def test_binding_wrong_subject(self):
        self.ledger['records'][1]['subject'] = 'wrong'
        self.assertIn('BINDING_SUBJECT_MISMATCH', self.codes())

    def test_unknown_field_rejected(self):
        self.ledger['verified'] = True
        with self.assertRaises(ValueError):
            self.result()

    def test_invalid_timestamps(self):
        for value in (None, False, '', '2026-01-01', '9999-12-31T23:59:59-01:00'):
            self.ledger['observed_at'] = value
            with self.assertRaises(ValueError):
                self.result()

    def test_boolean_total_rejected(self):
        self.ledger['sources'][0]['collection']['pages'][0]['reported_total'] = True
        with self.assertRaises(ValueError):
            self.result()

    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(ValueError):
            strict_json('{"id":1,"id":2}')

    def test_nonfinite_json_rejected(self):
        for value in ('NaN', 'Infinity', '-Infinity', '1e999', '-1e999'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                strict_json('{"id":' + value + '}')

    def test_surrogate_json_rejected(self):
        for raw in ('{"id":"\\ud800"}', '{"\\udfff":0}', '["\\ud800"]'):
            with self.subTest(raw=raw), self.assertRaises(UnicodeError):
                strict_json(raw)
        self.assertEqual(strict_json('"\\ud83d\\ude00"'), '\U0001f600')

    def test_cli_surrogate_sanitized(self):
        tool = Path(__file__).with_name('evidence.py')
        self.ledger['sources'][0]['id'] = '\ud800'
        (self.root / 'ledger.json').write_text(json.dumps(self.ledger))
        p = subprocess.run([sys.executable, str(tool), 'ledger.json', '--root', str(self.root)], capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)
        self.assertEqual(p.stderr, '')
        self.assertEqual(json.loads(p.stdout)['input_error'], 'INVALID_OR_UNREADABLE_INPUT')

    def test_cli_output(self):
        tool = Path(__file__).with_name('evidence.py')
        p = subprocess.run([sys.executable, str(tool), 'ledger.json', '--root', str(self.root), '--model', 'model.json'], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout)['status'], 'INSUFFICIENT_EVIDENCE')

    def test_cli_invalid_does_not_leak(self):
        tool = Path(__file__).with_name('evidence.py')
        p = subprocess.run([sys.executable, str(tool), '../private.json', '--root', str(self.root)], capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)
        self.assertNotIn('private', p.stdout)
        self.assertEqual(p.stderr, '')


if __name__ == '__main__':
    unittest.main()
