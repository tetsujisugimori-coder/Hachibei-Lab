# Independent Stage 3B generic-solid review

Reviewed source candidate: `7611be01a3246757ca1769fb435ccdd94d69c346`, tree `3bc045abcb94cbd6381ad7f1bc2b25086d365e7f`. Fetched into a separate checkout; reviewer did not edit implementation. The final publication commit will additionally contain these review artifacts. Final commit/CI verification belongs in the anchored GitHub review rather than a self-referential commit hash here.

## Results

- All 26 current unit/process/acceptance tests passed.
- Reexecuted 120 independently calculated analytic box fixtures and all nine intentional corruption rejections.
- All 20 predecessor-stage regressions passed; implementation remains unchanged there.
- Ten reviewer-authored geometry/error controls passed: face, edge and vertex contact; diagonal Euclidean gap; real positive micro-volume below the default marker; quarter turn about a non-origin pivot followed by translation; unit rejection; injected shape exception; analytic sphere separation and containment volume.
- Reviewer-authored subprocess timeout control returned nonzero and UNRESOLVED.
- Four reviewer-authored acceptance controls now reject forged expectations/results, forged fixture geometry, erased positive micro-volume and invented positive micro-volume.

The independent geometric oracles are elementary interval/Euclidean, sphere-volume and rigid-transform formulas, not target implementation outputs. The direct CAD computations share FreeCAD/OCC, so these tests do not provide independent numerical certification.

## Findings and disposition

1. The initial validator trusted expected volume/distance contained in the evidence being checked. An overlapping synthetic fixture was falsely accepted as separated when both expected and measured values were forged. `false_accept-prefixed.json` preserves the pre-fix accepted input. Fixed by a separate trusted geometry registry, independent formula recomputation and input provenance validation. The same attack is now rejected.
2. The initial validator lacked micro-positive classification. The first correction still allowed an analytic positive micro-volume to be replaced with measured zero within absolute tolerance. `micro-erasure-prefix.json` preserves that intermediate acceptance. Fixed by exact intersection-sign consistency and both expected/measured classification checks. Both micro-erasure and false micro-invention are now rejected.

No remaining blocking defect found in the reviewed limited measurement/fixture-validation scope. Final remote CI acceptance is not claimed by this report. Keep the PR Draft and do not merge as part of this review.

## Confidentiality and limits

Reviewed new tracked source/docs/logs and these supplemental files for private shape identifiers, dimensions, CAD files, source archive identifiers and silhouettes; none are included. All geometry in these review artifacts is synthetic neutral test geometry. Private reexecution evidence is intentionally separate.

This is a finite-pose BRep measurement tool, not a continuous-motion clearance proof, certified numerical bound, full-assembly clearance check, manufacturing approval, or physical-safety certification. Successful detection does not mean a mechanical interference was resolved.

## Reproduce supplemental controls

From repository root, using the same FreeCAD module configuration as the main README:

```sh
export PYTHONPATH=/usr/lib/freecad/lib:/usr/lib/freecad-python3/lib
P=projects/korosuke/generic-solids/reviews/stage3b
/usr/bin/python3 "$P/independent_cases.py"
/usr/bin/python3 "$P/acceptance_retest.py"
/usr/bin/python3 "$P/runner_timeout.py"
```

The adjacent JSON files are actual outputs of those portable scripts. `source-identity.json` records the checked source hashes and runtime. `SHA256SUMS.json` binds the supplemental artifacts. Historical pre-fix accepted JSON is deliberately retained as failure evidence, not current passing output.
