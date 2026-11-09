import copy
import unittest

from sweep import InputError, intersects, corners, read_input, screen


def fixture():
    return {
        "schema_version": 1,
        "joint": {"pivot_mm": [0, 0], "start_deg": -60, "end_deg": 60},
        "moving": [{"id": "link", "center_mm": [30, 0], "size_mm": [50, 8]}],
        "fixed": [{"id": "guard", "center_mm": [0, 100], "size_mm": [12, 12]}],
        "tolerance_mm": 0.5,
        "min_interval_deg": 0.25,
        "max_depth": 12,
    }


class ScreeningTests(unittest.TestCase):
    def test_clear(self):
        output = screen(fixture())
        self.assertEqual(output["counts"]["PROJECTED_CLEAR"], 1)
        self.assertEqual(output["pairs"][0]["unresolved_intervals"], 0)

    def test_obvious_overlap(self):
        raw = fixture()
        raw["fixed"][0]["center_mm"] = [30, 0]
        outcome = screen(raw)
        self.assertEqual(outcome["counts"]["PROJECTED_OVERLAP"], 1)
        self.assertEqual(outcome["pairs"][0]["first_observed_overlap_deg"], 0)

    def test_hidden_midrange_overlap_detected(self):
        raw = fixture()
        raw["fixed"][0]["center_mm"] = [30, 30]
        outcome = screen(raw)
        self.assertEqual(outcome["counts"]["PROJECTED_OVERLAP"], 1)

    def test_unresolved_is_not_pass(self):
        raw = fixture()
        raw["fixed"][0]["center_mm"] = [30, 12]
        raw["joint"].update(start_deg=0, end_deg=2)
        raw["max_depth"] = 0
        result = screen(raw)["pairs"][0]
        self.assertEqual(result["status"], "UNRESOLVED_2D")

    def test_overlap_on_touch(self):
        square = {"center": (0, 0), "size": (2, 2)}
        touching = {"center": (2, 0), "size": (2, 2)}
        self.assertTrue(intersects(corners(square), corners(touching)))

    def test_strict_validation(self):
        bad = fixture()
        bad["moving"][0]["size_mm"] = [0, 8]
        with self.assertRaises(InputError):
            read_input(bad)
        bad = fixture()
        bad["max_depth"] = True
        with self.assertRaises(InputError):
            read_input(bad)
        bad = fixture()
        bad["joint"]["start_deg"] = float("nan")
        with self.assertRaises(InputError):
            read_input(bad)

    def test_deterministic_and_no_mutation(self):
        raw = fixture()
        original = copy.deepcopy(raw)
        self.assertEqual(screen(raw), screen(raw))
        self.assertEqual(raw, original)

    def test_many_pairs(self):
        raw = fixture()
        raw["moving"].append({"id": "bracket", "center_mm": [15, 0], "size_mm": [8, 8]})
        raw["fixed"].append({"id": "body", "center_mm": [-90, 90], "size_mm": [10, 10]})
        self.assertEqual(screen(raw)["pair_count"], 4)


if __name__ == "__main__":
    unittest.main()
