"""Document checker negative controls, not actual B0/B1 inputs."""
import unittest
from pathlib import Path
from verify_plan import CASES, inspect


class PlanContract(unittest.TestCase):
    def test_current_and_each_missing_clause(self):
        root = Path(__file__).parent
        docs = {n: (root / n).read_text(encoding='utf-8') for n in ('PLAN.md', 'RUBRIC.md')}
        self.assertTrue(all(row['passed'] for row in inspect(docs)))
        for i, case in enumerate(CASES):
            for clause in case[4]:
                with self.subTest(case=case[0], clause=clause):
                    changed = dict(docs)
                    changed[case[3]] = changed[case[3]].replace(clause, '[REMOVED]')
                    self.assertFalse(inspect(changed)[i]['passed'])


if __name__ == '__main__':
    unittest.main()
