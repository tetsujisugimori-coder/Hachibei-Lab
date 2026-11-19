"""Review P2/P3: fail closed on contradictory B0 evidence and custody states.

These tests are synthetic-only and cannot authorize an actual experiment.
"""
import unittest
from check import evaluate


class B0B1ReviewGuardTests(unittest.TestCase):
    def base(self, condition='B0'):
        a1 = '合成試験用の青い輪を高く掲げる。\n'
        return {
            'kind': 'SYNTHETIC', 'condition': condition,
            'thread': 'synthetic-b0' if condition == 'B0' else 'synthetic-b1',
            'other_thread': 'synthetic-b1' if condition == 'B0' else 'synthetic-b0',
            'new_thread': True, 'plan': 'B4-v2', 'input': '非特定の問い',
            'output': '不明' if condition == 'B0' else a1,
            'start': '2026-11-18T00:00:00+00:00',
            'end': '2026-11-18T00:00:01+00:00',
            'settings_changed': False, 'retry': 0, 'interrupted': False,
            'preinfo_exposed': False, 'evidence_complete': True,
            'raw_text': True, 'b0_sealed': True,
            'b0_review': 'NO_SUSPICION_IN_SCOPE', 'b0_custody': 'PASS',
            'human_a0': 'NO_SUSPICION_IN_SCOPE',
            'human_a1': 'NO_SUSPICION_IN_SCOPE',
            'scoring_a0': '合成試験用の赤い箱を静かに置く。\n',
            'scoring_a1': a1, 'integrity': 'PASS', 'retrieval': 'PASS',
            'model_fixed': True, 'authorization': 'SYNTHETIC_ONLY',
            'actor': 'synthetic-review-tester', 'executed': True,
        }

    def verify(self, condition, field, value, expected_status, expected_reason):
        x = self.base(condition)
        x[field] = value
        output = evaluate(x)
        self.assertEqual((output['status'], output['reason']),
                         (expected_status, expected_reason))
        self.assertIs(output['permit'], False)
        self.assertEqual(output['experiment_start'], 'BLOCKED')
        self.assertEqual(output['route_exclusivity'], 'UNKNOWN')

    def test_baseline_b0(self):
        self.verify('B0', 'b0_sealed', True, 'PASS', 'NO_TRIGGER_IN_SCOPE')

    def test_baseline_b1(self):
        self.verify('B1_RESTATE', 'b0_custody', 'PASS', 'PASS', 'TASK_MATCH')

    def test_p3_unsealed_b0_must_not_pass(self):
        self.verify('B0', 'b0_sealed', False, 'BLOCKED', 'B0_NOT_SEALED')

    def test_p3_unverified_custody_must_not_pass(self):
        self.verify('B0', 'b0_custody', 'UNKNOWN', 'BLOCKED', 'B0_CUSTODY')

    def test_p3_unreviewed_b0_must_not_pass(self):
        self.verify('B0', 'b0_review', 'PENDING', 'BLOCKED', 'B0_REVIEW_PENDING')

    def test_p2_a0_suspected_overrides_clear_summary(self):
        self.verify('B1_RESTATE', 'human_a0', 'SUSPECTED', 'STOP_REVIEW', 'B0_A0_SEMANTIC')

    def test_p2_a1_suspected_overrides_clear_summary(self):
        self.verify('B1_RESTATE', 'human_a1', 'SUSPECTED', 'STOP_REVIEW', 'B0_A1_SEMANTIC')

    def test_p2_a0_pending_overrides_clear_summary(self):
        self.verify('B1_RESTATE', 'human_a0', 'PENDING', 'BLOCKED', 'B0_INDIVIDUAL_REVIEW_PENDING')

    def test_p2_a1_unknown_overrides_clear_summary(self):
        self.verify('B1_REVISE', 'human_a1', 'UNKNOWN', 'BLOCKED', 'B0_INDIVIDUAL_REVIEW_PENDING')

    def test_p2_clear_individuals_with_pending_summary_must_not_pass(self):
        self.verify('B1_RESTATE', 'b0_review', 'PENDING', 'BLOCKED', 'B0_REVIEW_PENDING')

    def test_failed_b0_custody_still_blocks_b1(self):
        self.verify('B1_RESTATE', 'b0_custody', 'UNKNOWN', 'BLOCKED', 'B0_CUSTODY')

    def test_failed_b0_seal_still_blocks_b1(self):
        self.verify('B1_RESTATE', 'b0_sealed', False, 'BLOCKED', 'B0_NOT_SEALED')

    def test_real_input_never_permitted(self):
        self.verify('B0', 'kind', 'REAL', 'BLOCKED', 'REAL_FORBIDDEN')


    def test_p2_blank_only_b0_cannot_pass(self):
        for output in (' ', '\t', '\n', '\r\n', ' \t\n', '\u3000', '\u00a0'):
            with self.subTest(output=repr(output)):
                self.verify('B0', 'output', output, 'MISSING', 'OUTPUT_MISSING')

    def test_p2_blank_only_b1_cannot_pass(self):
        for condition in ('B1_RESTATE', 'B1_REVISE'):
            for output in (' ', '\t\n', '\u3000'):
                with self.subTest(condition=condition, output=repr(output)):
                    self.verify(condition, 'output', output, 'MISSING', 'OUTPUT_MISSING')

    def test_p2_nonblank_b0_is_not_normalized(self):
        self.verify('B0', 'output', ' 中身 \t\n', 'PASS', 'NO_TRIGGER_IN_SCOPE')

    def test_p2_nonblank_b1_keeps_exact_matching(self):
        self.verify('B1_RESTATE', 'output', '合成試験用の青い輪を高く掲げる。\n ', 'FAIL', 'TASK_MISMATCH')

    def test_p2_nonstring_remains_schema_rejected(self):
        self.verify('B0', 'output', 23, 'BLOCKED', 'SCHEMA')

if __name__ == '__main__':
    unittest.main()
