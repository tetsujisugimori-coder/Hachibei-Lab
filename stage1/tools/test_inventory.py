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
if __name__ == '__main__': unittest.main()
