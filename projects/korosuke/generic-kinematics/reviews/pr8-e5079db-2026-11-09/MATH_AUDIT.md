# Independent numeric clearance audit

Target: Hachibei-Lab PR 8, commit `e5079db255403134d1864fc8b4ed8b3e8418350d`.
File: `projects/korosuke/generic-kinematics/sweep.py`.
Source SHA-256: `8f61135bb7feef58519c70e459a260ea9db51865b9245eedf73e5f991ab42833`.

Only neutral synthetic rectangles were used. The numeric experiment did not modify the implementation. These findings concern the advertised 2D clearance classification, not a real robot, private CAD, or 3D safety assessment.

## Result

Four accepted fixtures each return `PROJECTED_CLEAR`, `sample_count=1`, `certified_intervals=1`, `unresolved_intervals=0`, although independently evaluated geometry overlaps inside the tested interval. The primary oracle uses 100-digit arithmetic and repeats at 160 digits; every displayed witness agrees to 60 significant digits. The oracle does not reuse the candidate's corner, SAT, or bounding-box implementations. It transforms one known member of the moving rectangle and proves numerically, with positive coordinate margins, that it lies strictly inside the fixed rectangle.

The exact JSON inputs are the accompanying files. `false-clear-results.json` includes each complete input, candidate result, independent witnesses, and fixture hashes.

## 1. Huge angles invalidate the midpoint-centered motion certificate

Relevant lines: 81–82 (unreduced degree-to-radian conversion), 127 (midpoint), 133–134 (certificate).

`huge-angle-52.json`:
- Pivot `[0,0]`, range `[4503599627370496,4503599627370497]` degrees.
- Moving center `[1,0]`, dimensions `[1e-6,1e-6]`.
- Fixed center `[0.9563047559630354,0.29237170472273677]`, same dimensions.
- The computed midpoint rounds to the lower endpoint. The intended interval midpoint is one-half degree later.
- At the upper endpoint, the exact degree angle modulo 360 is 17 degrees. The moving center is strictly inside the fixed rectangle, with both interior margins approximately `5e-7` mm.
- The candidate nevertheless reports gap `0.01877958244890119` versus motion bound `0.008726650623295869`.

`huge-angle-trig-only.json` isolates a second issue without a degenerate midpoint:
- Same moving part and pivot; range `[4503599627370496,4503599627370498]`.
- Fixed center `[0.9510565162951535,0.3090169943749474]`, dimensions `[1e-6,1e-6]`.
- Midpoint `4503599627370497` is exactly representable and strictly interior. The upper endpoint is exactly 18 degrees modulo 360 and overlaps.
- Converting the unreduced huge angle to radians displaces the sampled geometry. Reported gap `0.02060776731530173` exceeds bound `0.017453301246591738` despite the endpoint overlap.

Reducing these two entire intervals to equivalent small-angle intervals changes the candidate result to `UNRESOLVED_2D`, not `PROJECTED_CLEAR`.

Mathematical reason: `r * (hi-lo)/2` in radians bounds displacement only from the actual exact midpoint orientation. A rounded endpoint midpoint or inaccurate huge-angle orientation is not that midpoint. This is not fixed solely by replacing `(lo+hi)/2` with `lo+(hi-lo)/2`.

## 2. Rounded geometry is not a conservative bounding-box enclosure

Relevant lines: 83–85 (corner arithmetic), 107–109 (claimed lower-bound gap), 133–134 (clearance certificate).

`huge-pivot.json`:
- Pivot `[1e16,0]`, range `[45,45.1]`.
- Moving local center `[1.2,-1.2]`, dimensions `[0.01,0.01]`.
- Fixed center `[10000000000000002,0]`, dimensions `[1,1]`.
- At the actual sampled angle 45.05 degrees, the true moving center is strictly inside the fixed box. Interior margins are approximately `0.1970556286566254` mm horizontally and `0.4985190392085833` mm vertically.
- Sequential `pivot + x*cos - y*sin` rounding collapses every computed moving x coordinate to `1e16`. Fixed x coordinates collapse to `1e16+2`.
- The computed gap is therefore 2 mm, exceeding the bound `0.0014871316501335852` mm, while the actual shapes overlap deeply.
- Translating the exact same scene by `[-1e16,0]` produces `PROJECTED_OVERLAP` immediately.

`moderate-tiny-boundary.json` shows that simply restricting huge coordinates and huge angles is insufficient:
- Pivot `[0,0]`, range `[0.3,0.300000000000005]`.
- Moving center `[1,0]`, dimensions `[1,1]`.
- Fixed center `[1.5025978971240082,-0.492139200376584]`, dimensions `[9.5367431640625e-7,1]`.
- The sampled midpoint is strictly interior, so midpoint degeneration is not involved.
- At that exact float midpoint, the independently rotated moving local corner `[1.5,-0.5]` lies strictly inside the fixed box. Its horizontal penetration is `5.08117821930717607021879184278984541701674468898715380100322e-17` mm.
- The candidate's claimed gap is `2.220446049250313e-16` mm, greater than its motion bound `6.893505395536085e-17` mm.

The exact-real bounding-box theorem is sound, but rounded polygon coordinates need not enclose the true polygons. A strict `>` comparison does not compensate for the preceding roundoff.

## Adversarial moderate-angle boundary sweep

`stress_tiny_boundaries.py` independently constructs 18,000 strict corner-overlap cases. Angles are 0.01 through 60 degrees in 0.01 increments; interval widths are 2, 4, or 90 angle ULPs. Every midpoint is strictly interior, and every fixed rectangle independently contains the true moving corner at that midpoint.

Results:
- `PROJECTED_OVERLAP`: 17,731
- `UNRESOLVED_2D`: 129
- False `PROJECTED_CLEAR`: 140

This is deliberately adversarial near-boundary coverage, not a random sample or an accuracy estimate. Complete counts and five examples are in `tiny-boundary-stress-results.json`.

## Suggested fail-closed correction

1. Define and validate the supported numerical domain, including coordinate scale, dimensions, angle representation, and resolution. Finite input alone is not sufficient. Unsupported or numerically uncertifiable geometry should reject input or return `UNRESOLVED_2D`, never clear.
2. Normalize the unwrapped angular interval to a small canonical range before evaluating midpoints and trigonometric functions, preserving its full span and wrap direction. For a rounded sampling angle, bound motion using the maximum distance to either interval endpoint, plus the orientation error. If splitting cannot produce a new representable sample, stop unresolved rather than pretending a half-interval bound still applies.
3. Work in a common local frame to reduce translation-induced cancellation. Still account for subtraction, size, trigonometric, and rotation errors; translation alone does not repair the ordinary-coordinate fixture.
4. Use outward-rounded interval enclosures or a justified error bound for rotated corners and the bounding radius. Certify only when a proven lower bound on separation exceeds a proven upper bound on motion plus the requested tolerance. Include every rounding term. A fixed arbitrary epsilon, normalized angles alone, or coordinate magnitude limits alone do not establish this property.
5. Preserve all four regressions and add translation/360-degree periodicity metamorphic tests. The appropriate result may be overlap, unresolved, or explicit input rejection according to the supported domain, but cannot be clear for these accepted inputs.

## Reproduction

Requires Python and `mpmath` 1.3.0. Place scripts and the four JSON fixtures together.

```sh
python reproduce_false_clear.py --source path/to/sweep.py --output false-clear-results.json --regression-gate
python stress_tiny_boundaries.py --source path/to/sweep.py --output tiny-boundary-stress-results.json
```

These scripts contain no absolute local paths. The first emits a short verification summary and writes the complete aggregate to the requested output path.

The regression gate exits **1** on this target because all four fixtures are false clear. It exits 0 only when every fixture returns `PROJECTED_OVERLAP`, `UNRESOLVED_2D`, or explicit `InputError`. Unexpected statuses fail, and unexpected exceptions fail rather than being accepted. The independent geometric witnesses remain the same after a candidate fix. The gate's three safe paths were verified with a separate synthetic test double, not by modifying the implementation. Without `--regression-gate`, exit 0 means only that a diagnostic report was written, not that the target passes. Passing these four regressions is not a proof of general numerical soundness.
