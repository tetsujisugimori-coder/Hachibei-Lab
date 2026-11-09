# Stage 3B: BRep pose measurements (limited technical acceptance)

Related issue: #9. Baseline main: `7f0342d39871f3b10717a9a1ac5c52def78d6484`, tree `f8e9cfd5dcadbdfcbf5191ad295f9a7401d9c681`. Stage 3A PR #8 was merged before this work; its files remain unchanged. No AGENTS.md or repository-specific skill files were present at this baseline.

This is a **measurement tool**, not a certified collision-free-motion or physical-safety checker. `PROJECTED_CLEAR` is deliberately not a 3D result. No character-specific CAD, coordinates, source URLs, original archive identifiers or derived silhouettes are stored in this directory or CI. Existing Issue #4 / PR #5 and private source originals are not changed.

## Scope

- FreeCAD/OCC valid closed BRep solids, including separated components in compounds.
- Explicit mm units and world-space rotation (degrees) followed by translation (mm). The loader includes ancestor App::Part placements and checks an exact model SHA-256.
- Both boolean common volume and minimum BRep distance are measured. AABB is not used for early-clear decisions; meshes are not substituted for solids.
- The public, dimensionally neutral fixtures use independently calculated box interval intersections / Euclidean gaps, plus rigid-transform invariance and face/edge/point contact.
- The isolated CLI converts Python errors, bad hashes, missing objects, wrong units, subprocess failure or timeout into `UNRESOLVED` and nonzero exit. It writes output atomically.

## Result meanings

| Status | Meaning at the supplied pose |
|---|---|
| VOLUME_OVERLAP | OCC reported a positive intersection greater than the selected micro-volume marker |
| MICRO_OVERLAP_REPORTED | OCC reported a positive intersection at or below the marker; not discarded and not separated |
| CONTACT_OR_WITHIN_TOLERANCE | Zero reported common volume, distance at or below the larger of requested linear tolerance / stored BRep tolerances |
| SEPARATED_AT_POSE | Zero reported common volume and a distance larger than that tolerance |
| UNRESOLVED | Invalid/unsupported input or failed/inconsistent computation |

Default linear tolerance is 1e-6 mm; micro-volume marker is 1e-6 mm³. These are reporting conventions, **not universal error guarantees**. Stored OCC tolerances are not certified numerical error bounds. Tiny features below kernel resolution can be missed; the tool must not be used to certify safety. Manufacturing clearance is a separate optional requirement and never silently equated with geometric tolerance. Every result states `continuous_motion: NOT_PROVEN` and `physical_safety: NOT_TESTED`.

## Reproduce public verification

Use an existing FreeCAD Python interpreter, or your distribution's FreeCAD Python module. No Python bindings or CAD binaries are vendored. CI uses Ubuntu 24.04 distribution packages; local evidence records its actual FreeCAD/OCC versions. The optional 3D tool does not introduce dependencies into the standard-library-only Stage 3A runtime.

```sh
export PYTHONPATH=/usr/lib/freecad/lib:/usr/lib/freecad-python3/lib
/usr/bin/python3 -m unittest discover -s projects/korosuke/generic-solids -v
/usr/bin/python3 projects/korosuke/generic-solids/run_analytic.py solid-results
/usr/bin/python3 -m unittest discover -s projects/korosuke/generic-kinematics -v
```

`run_pose.py REQUEST.json --output RESULT.json --timeout 120` accepts:

```json
{"units":"mm","model":"/local/neutral.FCStd","model_sha256":"<actual SHA-256>","poses":[{"id":"sample-0","a":"BlockA","b":"BlockB","transform_a":{"axis":[0,0,1],"pivot":[0,0,0],"degrees":30,"translation":[0,0,0]}}]}
```

Never send private requests, geometry, output or process stderr to public CI. No automatic discovery, upload or publishing is performed by the checker. The CLI supports FCStd objects; STEP can be imported into a working document separately. A STEP solid or GLB mesh matching a source's count is not evidence of exact shape equivalence.

## Private application and interpretation

The original release's five unresolved pair identities are established from the original recorded analysis, not guessed from screenshots. A separate private execution reopens the original FCStd, applies the recorded linkage pose relation, measures five pairs plus an existing micro-residual control, retains source hashes, and prepares improvement options. Its original-file hash is checked before and after; no CAD design is altered.

The fixed scan uses 73 inclusive input angles at 5° spacing (0° and 360° are the same endpoint, not independent trials). Observed transitions across the 1e-6 mm³ reporting marker are bisected at most seven times; ±5° around each coarse sampled maximum is checked at 1° spacing. Transition brackets do not assert monotonicity or prove absence of additional islands. Maxima are sampled maxima, not continuous extrema. `fourbar_pose` checks circle closure and rejects impossible/toggle cases; it is not a general 3D kinematic solver.

Finite-pose results cannot certify the entire motion. No material removal, joint shift or mechanism revision is accepted by this study. Changes to supports, cover interiors, travel limits or mounting locations remain design proposals requiring new exact-solid sweeps, fastener/strength assessment and visual review.

## Evidence and acceptance

- `evidence/local`: raw local unit logs, analytic case inputs/results, rejection controls, Stage 3A regression log.
- GitHub Actions: separate runner, exact HEAD/tree, original logs and SHA256SUMS artifact.
- Independent reviewer: separate tests/recomputation and final-HEAD review; findings and disposition recorded before recommendation.
- Overall Stage 3B remains PARTIAL because continuous motion and physical engineering are not certified. Five-pair interference detection is separate from interference resolution.

No third-party images/models/materials are added. FreeCAD/OCC are external dependencies and retain their upstream licenses; this repository does not redistribute their binaries. This work does not decide the separate legal status of character-specific assets.
