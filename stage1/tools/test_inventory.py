"""Synthetic negative controls; no private source data is used."""
import copy
import json
from pathlib import Path
import unittest
from jsonschema import ValidationError
from validate_inventory import validate_data

ROOT = Path(__file__).resolve().parents[1]
class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.args = [json.loads((ROOT/p).read_text()) for p in
                     ('public-index.json','ledger.schema.json','evidence/public-issues.json','domain-summary.json')]
    def rejected(self, change):
        args = copy.deepcopy(self.args); change(args)
        with self.assertRaises((ValueError, ValidationError)):
            validate_data(*args)
    def test_valid_fixture(self): self.assertTrue(validate_data(*self.args))
    def test_duplicate_id(self): self.rejected(lambda a: a[0]['sources'].append(copy.deepcopy(a[0]['sources'][0])))
    def test_missing_required(self): self.rejected(lambda a: a[0]['sources'][0].pop('effective_until'))
    def test_private_row(self): self.rejected(lambda a: a[0]['sources'][0].update(publication_status='PRIVATE'))
    def test_unknown_origin(self): self.rejected(lambda a: a[0]['sources'][0].update(original_location='UNKNOWN'))
    def test_forged_hash(self): self.rejected(lambda a: a[2]['records'][0].update(body_sha256='0'*64))
    def test_false_current(self): self.rejected(lambda a: a[0]['sources'][0].update(application_state='CURRENT'))
    def test_timestamp_as_revision(self): self.rejected(lambda a: a[0]['sources'][0].update(service_revision='2026-11-01T00:00:00Z'))
    def test_invented_version(self): self.rejected(lambda a: a[0]['sources'][0].update(document_version='1.0'))
    def test_plan_as_original(self): self.rejected(lambda a: a[3]['domains'][0].update(public_research_originals_verified=2))
    def test_invented_coverage(self): self.rejected(lambda a: a[3]['domains'][0].update(coverage_ratio=1))
    def test_wrong_domain_count(self): self.rejected(lambda a: a[3]['domains'][0].update(public_plan_references=3))
    def test_missing_domain(self): self.rejected(lambda a: a[3]['domains'].pop())
    def test_private_claim_public(self): self.rejected(lambda a: a[3]['domains'][0].update(body_verified=10))

# These cases use synthetic values constructed at runtime, never private data.
import tempfile
from validate_inventory import scan_public_files, validate_scope, validate_immutable_files, PROTECTED_FILES
from unittest.mock import patch

class SafetyTests(unittest.TestCase):
    def sample(self, text, filename='sample.md'):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / 'stage1').mkdir()
            (root / 'stage1' / filename).write_text(text)
            return scan_public_files(root)
    def test_public_text_is_allowed(self):
        self.assertTrue(self.sample('Public synthetic record'))
    def test_code_is_not_exempt_from_scan(self):
        with self.assertRaises(ValueError): self.sample('sk-' + 'x' * 24, 'example.py')
    def test_private_page_url(self):
        with self.assertRaises(ValueError): self.sample('https://' + 'chatgpt.com/space/' + 'page_' + 'a' * 32)
    def test_internal_id(self):
        with self.assertRaises(ValueError): self.sample('libfile_' + 'a' * 32)
    def test_email(self):
        with self.assertRaises(ValueError): self.sample('synthetic' + '@' + 'invalid.example')
    def test_local_path(self):
        with self.assertRaises(ValueError): self.sample('/work' + 'space/' + 'synthetic.txt')
    def test_query_url(self):
        with self.assertRaises(ValueError): self.sample('https://' + 'github.com/example?x=y')
    def test_only_one_ci_path_is_allowed(self):
        validate_scope(['stage1/new.md', '.github/workflows/stage1-inventory.yml'])
        with self.assertRaises(ValueError): validate_scope(['.github/workflows/other.yml'])
    def test_readme_change_outside_scope(self):
        with self.assertRaises(ValueError): validate_scope(['README.md'])
    def test_source_code_change_outside_scope(self):
        with self.assertRaises(ValueError): validate_scope(['projects/synthetic.py'])
    def test_old_evidence_is_immutable(self):
        self.assertEqual(len(validate_immutable_files(ROOT.parent)), 6)

    def test_changed_original_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in PROTECTED_FILES:
                p = root / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b'original')
            (root / 'README.md').write_bytes(b'changed')
            with patch('validate_inventory.subprocess.check_output', return_value=b'original'):
                with self.assertRaises(ValueError): validate_immutable_files(root)
    def test_workflow_is_also_scanned(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / 'stage1').mkdir()
            p = root / '.github/workflows/stage1-inventory.yml'
            p.parent.mkdir(parents=True); p.write_text('sk-' + 'z' * 24)
            with self.assertRaises(ValueError): scan_public_files(root)

if __name__ == '__main__': unittest.main()
