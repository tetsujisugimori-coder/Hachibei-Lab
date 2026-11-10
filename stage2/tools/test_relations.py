import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from validate_relations import ROOT, validate_data, validate_scope, scan
class RelationTests(unittest.TestCase):
    def setUp(self):
        load=lambda p:json.loads((ROOT/p).read_text())
        self.d=load('stage2/public-relations.json');self.s=load('stage2/relations.schema.json');self.i=load('stage1/public-index.json');self.p=load('stage1/evidence/public-issues.json')
    def check(self): return validate_data(self.d,self.s,self.i,self.p)
    def bad(self, mutate):
        mutate()
        with self.assertRaises(Exception): self.check()
    def test_valid(self):self.check()
    def test_rules_emptied(self):self.bad(lambda:self.d.update(rules=[]))
    def test_relations_emptied(self):self.bad(lambda:self.d.update(relations=[]))
    def test_conflicts_emptied(self):self.bad(lambda:self.d.update(conflicts=[]))
    def test_proposals_emptied(self):self.bad(lambda:self.d.update(proposals=[]))
    def test_duplicate_source(self):self.bad(lambda:self.d['sources'].append(self.d['sources'][0]))
    def test_duplicate_rule(self):self.bad(lambda:self.d['rules'].append(self.d['rules'][0]))
    def test_duplicate_relation_id(self):self.bad(lambda:self.d['relations'].append(self.d['relations'][0]))
    def test_duplicate_relation_semantics(self):
        r=copy.deepcopy(self.d['relations'][0]);r['relation_id']='OTHER';self.bad(lambda:self.d['relations'].append(r))
    def test_duplicate_conflict(self):self.bad(lambda:self.d['conflicts'].append(self.d['conflicts'][0]))
    def test_duplicate_proposal(self):self.bad(lambda:self.d['proposals'].append(self.d['proposals'][0]))
    def test_missing_field(self):self.bad(lambda:self.d['relations'][0].pop('limitations'))
    def test_extra_field(self):self.bad(lambda:self.d.update(secret='hidden'))
    def test_private_dataset(self):self.bad(lambda:self.d.update(visibility='PRIVATE'))
    def test_private_source(self):self.bad(lambda:self.d['sources'][0].update(publication_status='PRIVATE'))
    def test_new_source(self):self.bad(lambda:self.d['sources'][0].update(source_id='NEW'))
    def test_title_changed(self):self.bad(lambda:self.d['sources'][0].update(title='changed'))
    def test_location_changed(self):self.bad(lambda:self.d['sources'][0].update(location='elsewhere'))
    def test_stage1_pointer_changed(self):self.bad(lambda:self.d['sources'][0].update(stage1_ref='wrong'))
    def test_edition_invented(self):self.bad(lambda:self.d['sources'][0].update(edition='v1'))
    def test_unverified_promoted(self):self.bad(lambda:self.i['sources'][0].update(body_check_status='NOT_TESTED'))
    def test_plan_as_research(self):self.bad(lambda:self.d['sources'][0].update(classification='ORIGINAL'))
    def test_dangling_rule_source(self):self.bad(lambda:self.d['rules'][0].update(source_id='MISSING'))
    def test_wrong_citation_source(self):self.bad(lambda:self.d['rules'][0]['citation'].update(source_id='PUB-002'))
    def test_quote_fabricated(self):self.bad(lambda:self.d['rules'][0]['citation'].update(quote='not quoted'))
    def test_quote_position_wrong(self):self.bad(lambda:self.d['rules'][0]['citation'].update(start_line=1,end_line=1))
    def test_quote_range_inflated(self):self.bad(lambda:self.d['rules'][0]['citation'].update(end_line=999999))
    def test_snapshot_changed(self):self.bad(lambda:self.p['records'][0].update(body='changed'))
    def test_hash_forged(self):self.bad(lambda:self.d['rules'][0]['citation'].update(body_sha256='0'*64))
    def test_current_rule_false(self):self.bad(lambda:self.d['rules'][0].update(application_state='CURRENT_WITHIN_SCOPE'))
    def test_adopted_false(self):self.bad(lambda:self.d['rules'][0].update(document_status='ADOPTED'))
    def test_approval_invented(self):self.bad(lambda:self.d['rules'][0].update(approval_evidence='claimed'))
    def test_effective_date_invented(self):self.bad(lambda:self.d['rules'][0].update(effective_from='2026-01-01'))
    def test_authority_expanded(self):self.bad(lambda:self.d['rules'][0].update(authority_category='USER_APPROVED'))
    def test_stage2_adoption(self):self.bad(lambda:self.d['rules'][0].update(adopted_by_stage2=True))
    def test_dangling_relation(self):self.bad(lambda:self.d['relations'][0].update(rule_id='MISSING'))
    def test_claim_interpretation_mixed(self):self.bad(lambda:self.d['relations'][0].update(source_claim='interpretation'))
    def test_no_limits(self):self.bad(lambda:self.d['relations'][0].update(limitations=[]))
    def test_automatic_effect(self):self.bad(lambda:self.d['relations'][0].update(normative_effect='APPLY'))
    def test_dangling_proposal(self):self.bad(lambda:self.d['relations'][0].update(proposal_id='MISSING'))
    def test_proposal_without_link(self):self.bad(lambda:self.d['relations'][0].update(kind='PROPOSAL'))
    def test_unknown_overstated(self):self.bad(lambda:self.d['relations'][0].update(kind='UNKNOWN'))
    def test_direct_overstated(self):self.bad(lambda:self.d['relations'][0].update(kind='DIRECT'))
    def test_conflict_auto_resolve(self):self.bad(lambda:self.d['conflicts'][0].update(auto_resolved=True))
    def test_conflict_dangling(self):self.bad(lambda:self.d['conflicts'][0].update(rule_ids=['MISSING']))
    def test_proposal_approved(self):self.bad(lambda:self.d['proposals'][0].update(status='APPROVED'))
    def test_proposal_adopted(self):self.bad(lambda:self.d['proposals'][0].update(adoption=True))
    def test_scenario_missing(self):self.bad(lambda:self.d['scenarios'].pop())
    def test_scenario_implementation_false(self):self.bad(lambda:self.d['scenarios'][0].update(status='OBSERVED_BOUNDED'))
    def test_runtime_unproved(self):self.bad(lambda:self.d['rules'][0].update(runtime_verification='OBSERVED'))
    def test_coverage_invented(self):self.bad(lambda:self.d.update(coverage_ratio='100%'))
    def test_allowed_scope(self):validate_scope(['stage2/x.json','.github/workflows/stage2-relations.yml'])
    def test_rule_file_protected(self):
        with self.assertRaises(ValueError):validate_scope(['README.md'])
    def test_other_project_protected(self):
        with self.assertRaises(ValueError):validate_scope(['projects/other/file'])
    def test_source_history_protected(self):
        with self.assertRaises(ValueError):validate_scope(['stage1/public-index.json'])
    def test_public_scan(self):scan(ROOT)
    def test_secret_negative_control(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'stage2').mkdir();(root/'.github/workflows').mkdir(parents=True)
            (root/'.github/workflows/stage2-relations.yml').write_text('name: test')
            (root/'stage2/test.md').write_text('page_'+'a'*32)
            with self.assertRaises(ValueError):scan(root)
    def test_broken_local_link(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'stage2').mkdir();(root/'.github/workflows').mkdir(parents=True)
            (root/'.github/workflows/stage2-relations.yml').write_text('name: test')
            (root/'stage2/test.md').write_text('[missing](no-file.md)')
            with self.assertRaises(ValueError):scan(root)
if __name__=='__main__':unittest.main()
