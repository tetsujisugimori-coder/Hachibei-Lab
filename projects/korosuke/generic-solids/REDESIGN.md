# Stage 3C-1: generic redesign checks (Issue #11)

This public contribution contains only original neutral blocks and generic code.
Its fixture dimensions are arbitrary test values, not assembly dimensions or
manufacturing recommendations. No private CAD or derived assets are included.

## Before/after contract

`compare_redesign` accepts two named shape mappings, target pairs, protected
material regions, a single shared `Policy`, and one shared pose list beginning
with `{}` (the initial pose). All unordered pairs are measured at every sample
with the unchanged Stage 3B `measure_pair`. It retains raw overlap, distance,
contact, clearance and unresolved statuses. Shape BRep SHA256 and measurements
bind the in-memory inputs; these hashes are serialization-specific, not proofs
of shape equivalence. CI independently records checkout HEAD/tree and artifact
SHA256. Never publish this function's results for private inputs without review.

Each named part must be one valid closed solid, with the same inventory before
and after. This deliberately excludes multi-solid compound parts. A nonzero
symmetric difference must exist for a member of every target pair. Every changed
part needs caller-selected protected solid regions that remain contained in
both designs. Missing/deleted parts, invalid shapes, no-op redesigns, absent
clearance requirements, missing initial pose and removed protection fail closed.
These protections can detect an obviously destructive cut but cannot establish
that the caller selected adequate regions or that the support is strong enough.
The helper is not a general assembly/constraint or engineering acceptance engine.

Target initial-pose resolution, sampled target clearance, new neighboring
positive-volume overlaps, and all neighboring clearance are separate fields.
A PASS requires all four checks; contact never passes clearance, including a
zero requirement. Existing neighboring overlaps are still reported and prevent
overall PASS. Changed policies or a reduced sample list cannot be supplied
separately for the before/after comparison. The caller must still justify the
chosen policy, pose coverage and complete assembly inventory.

## Neutral fixture and alternatives

An unrelieved rectangular bracket intersects a small slider. The chosen central
relief retains its base web and two mounting lands as protected volumes; its
remaining body must stay connected. The initial intersection is analytically
4 × 4 × 2 = 32 mm³. The relief removes this intersection and produces a nearest
side-wall gap of 1 mm. Three identical before/after poses exercise the slider's
vertical motion. The provisional test clearance is 0.25 mm, without a claim of
manufacturability. An unchanged nearby block exercises pair coverage.

Alternatives tested: no-op (rejected), insufficient-depth relief (contact and
sample interference), excessive-depth relief (protected web removed), adding
material that creates a new neighbor collision (rejected). Deletion, missing
poses, invalid topology and artificially enlarged micro-volume reporting
threshold also cannot turn these negative controls into PASS.

`neutral_redesign.py OUTPUT_DIR` writes neutral before/after FCStd and STEP,
reopens each, and compares validity, volume and bidirectional geometric difference;
STEP also checks solid count. The JSON result contains measurements and actual
FreeCAD/OCC versions. These are empirical tolerance checks, not exact equivalence
proofs. No GLB, visual display or private-original roundtrip is claimed by this
public fixture.

## Reproduce

Use the same FreeCAD Python environment as README.md:

```sh
/usr/bin/python3 -m unittest discover -s projects/korosuke/generic-solids -v
/usr/bin/python3 projects/korosuke/generic-solids/neutral_redesign.py /tmp/neutral-results
/usr/bin/python3 -m unittest discover -s projects/korosuke/generic-kinematics -v
```

The existing solid CI runs all of the above plus Stage 3B analytic and independent
regressions. Its artifact includes neutral FCStd/STEP, reports, logs, exact
checkout identity and SHA256 hashes, all generated from this repository only.

## Acceptance boundary

Neutral fixture success is NOT evidence that a private assembly was redesigned.
Continuous full motion remains NOT_PROVEN; strength, wear, torque, wiring,
manufacturing tolerances and physical safety are NOT_TESTED. Private assembly
acceptance is separate. Independent review and final-HEAD evidence must be
completed before a limited generic merge recommendation. No automatic merge.
