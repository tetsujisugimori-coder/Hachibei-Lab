"""Conservative planar clearance screening for a generic revolute joint.

Only synthetic, neutral rectangles belong in the public repository. 2D projected
results are not evidence of a collision-free 3D CAD assembly.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


class InputError(ValueError):
    """Raised for invalid mechanical screening input."""


def number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputError(f"{label} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise InputError(f"{label} must be a finite number")
    return result


def pair(value: Any, label: str, *, positive: bool = False) -> tuple[float, float]:
    if not isinstance(value, list) or len(value) != 2:
        raise InputError(f"{label} must be a two-number array")
    result = (number(value[0], label), number(value[1], label))
    if positive and any(v <= 0 for v in result):
        raise InputError(f"{label} must be positive")
    return result


def read_input(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict) or type(raw.get("schema_version")) is not int or raw["schema_version"] != 1:
        raise InputError("schema_version must be 1")
    joint = raw.get("joint")
    if not isinstance(joint, dict):
        raise InputError("joint must be an object")
    pivot = pair(joint.get("pivot_mm"), "joint.pivot_mm")
    begin = number(joint.get("start_deg"), "joint.start_deg")
    end = number(joint.get("end_deg"), "joint.end_deg")
    if end <= begin or end - begin > 360:
        raise InputError("joint angle range must be increasing and at most 360 degrees")
    tolerance = number(raw.get("tolerance_mm", 0), "tolerance_mm")
    min_interval = number(raw.get("min_interval_deg", 0.25), "min_interval_deg")
    depth = raw.get("max_depth", 12)
    if tolerance < 0 or min_interval <= 0:
        raise InputError("tolerance must be nonnegative and min_interval positive")
    if isinstance(depth, bool) or not isinstance(depth, int) or not 0 <= depth <= 16:
        raise InputError("max_depth must be an integer from 0 to 16")
    result: dict[str, Any] = {"pivot": pivot, "start": begin, "end": end,
                              "tolerance": tolerance, "interval": min_interval, "depth": depth}
    for key in ("moving", "fixed"):
        items = raw.get(key)
        if not isinstance(items, list) or not 1 <= len(items) <= 10:
            raise InputError(f"{key} must contain 1 to 10 neutral rectangles")
        processed = []
        seen: set[str] = set()
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                raise InputError(f"{key}[{index}] must be an object")
            name = item.get("id")
            if not isinstance(name, str) or not 1 <= len(name) <= 60 or name in seen:
                raise InputError(f"{key}[{index}].id must be a unique nonempty string")
            seen.add(name)
            processed.append({"id": name,
                              "center": pair(item.get("center_mm"), f"{name}.center_mm"),
                              "size": pair(item.get("size_mm"), f"{name}.size_mm", positive=True)})
        result[key] = processed
    return result


def corners(part: dict[str, Any], angle_deg: float = 0, pivot: tuple[float, float] = (0, 0)) -> list[tuple[float, float]]:
    cx, cy = part["center"]
    w, h = part["size"]
    radians = math.radians(angle_deg)
    co, si = math.cos(radians), math.sin(radians)
    return [(pivot[0] + x * co - y * si, pivot[1] + x * si + y * co)
            for x, y in ((cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
                         (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2))]


def intersects(a: list[tuple[float, float]], b: list[tuple[float, float]]) -> bool:
    """Separating-axis test for convex rectangles; touching counts as overlap."""
    for polygon in (a, b):
        for index, (x, y) in enumerate(polygon):
            nx, ny = polygon[(index + 1) % len(polygon)]
            axis = (-(ny - y), nx - x)
            pa = [p[0] * axis[0] + p[1] * axis[1] for p in a]
            pb = [p[0] * axis[0] + p[1] * axis[1] for p in b]
            if max(pa) < min(pb) or max(pb) < min(pa):
                return False
    return True


def bbox_gap(a: list[tuple[float, float]], b: list[tuple[float, float]]) -> float:
    """Lower bound on Euclidean polygon separation, not actual clearance."""
    ax = [p[0] for p in a]
    ay = [p[1] for p in a]
    bx = [p[0] for p in b]
    by = [p[1] for p in b]
    dx = max(0.0, min(bx) - max(ax), min(ax) - max(bx))
    dy = max(0.0, min(by) - max(ay), min(ay) - max(by))
    return math.hypot(dx, dy)


def screen_pair(cfg: dict[str, Any], moving: dict[str, Any], fixed: dict[str, Any]) -> dict[str, Any]:
    obstacle = corners(fixed)
    # Moving rectangles have joint-local coordinates. Derive their bounding radius
    # in that local frame, not from the world pivot.
    cx, cy = moving["center"]
    w, h = moving["size"]
    radius = max(math.hypot(cx + sx * w / 2, cy + sy * h / 2)
                 for sx in (-1, 1) for sy in (-1, 1))
    stats = {"sample_count": 0, "certified_intervals": 0, "unresolved_intervals": 0}
    first_overlap: float | None = None

    def examine(lo: float, hi: float, level: int) -> None:
        nonlocal first_overlap
        if first_overlap is not None:
            return
        midpoint = (lo + hi) / 2
        moving_poly = corners(moving, midpoint, cfg["pivot"])
        stats["sample_count"] += 1
        if intersects(moving_poly, obstacle):
            first_overlap = midpoint
            return
        conservative_motion = radius * math.radians((hi - lo) / 2)
        if bbox_gap(moving_poly, obstacle) > conservative_motion + cfg["tolerance"]:
            stats["certified_intervals"] += 1
            return
        if level >= cfg["depth"] or hi - lo <= cfg["interval"]:
            stats["unresolved_intervals"] += 1
            return
        examine(lo, midpoint, level + 1)
        examine(midpoint, hi, level + 1)

    examine(cfg["start"], cfg["end"], 0)
    if first_overlap is not None:
        status = "PROJECTED_OVERLAP"
    elif stats["unresolved_intervals"]:
        status = "UNRESOLVED_2D"
    else:
        status = "PROJECTED_CLEAR"
    return {"moving_id": moving["id"], "fixed_id": fixed["id"], "status": status,
            "first_observed_overlap_deg": first_overlap, **stats}


def screen(raw: Any) -> dict[str, Any]:
    cfg = read_input(raw)
    results = [screen_pair(cfg, moving, fixed)
               for moving in cfg["moving"] for fixed in cfg["fixed"]]
    counts = {status: sum(item["status"] == status for item in results)
              for status in ("PROJECTED_OVERLAP", "UNRESOLVED_2D", "PROJECTED_CLEAR")}
    return {"schema_version": 1, "method": "planar_rectangles_conservative_rotation",
            "limitations": "2D synthetic projection only; not a 3D CAD, strength, torque or manufacturing acceptance",
            "pair_count": len(results), "counts": counts, "pairs": results}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON containing neutral rectangular fixtures")
    parser.add_argument("--output", type=Path, help="Optional path for report JSON")
    args = parser.parse_args()
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
        result = screen(data)
    except (InputError, ValueError, OSError) as exc:
        parser.error(str(exc))
    content = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.write_text(content, encoding="utf-8")
    else:
        print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
