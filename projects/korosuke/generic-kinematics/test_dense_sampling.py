"""Additional reproducible dense-angle checks for conservatively clear fixtures."""

import random
import unittest

from sweep import corners, intersects, read_input, screen
from test_sweep import fixture


class DenseSamplingTest(unittest.TestCase):
    def test_certified_clear_has_no_sampled_overlap(self):
        generator = random.Random(20261109)
        certified = 0
        for _ in range(120):
            raw = fixture()
            raw["moving"][0]["center_mm"] = [generator.uniform(2, 50), generator.uniform(-15, 15)]
            raw["moving"][0]["size_mm"] = [generator.uniform(4, 45), generator.uniform(3, 15)]
            raw["fixed"][0]["center_mm"] = [generator.uniform(-65, 65), generator.uniform(-65, 65)]
            raw["fixed"][0]["size_mm"] = [generator.uniform(2, 35), generator.uniform(2, 35)]
            raw["joint"].update(start_deg=-70, end_deg=70)
            raw["min_interval_deg"] = 0.1
            if screen(raw)["pairs"][0]["status"] != "PROJECTED_CLEAR":
                continue
            certified += 1
            cfg = read_input(raw)
            for step in range(501):
                angle = cfg["start"] + (cfg["end"] - cfg["start"]) * step / 500
                moving = corners(cfg["moving"][0], angle, cfg["pivot"])
                fixed = corners(cfg["fixed"][0])
                self.assertFalse(intersects(moving, fixed), f"sampled overlap at {angle}")
        self.assertGreater(certified, 20)


if __name__ == "__main__":
    unittest.main()
