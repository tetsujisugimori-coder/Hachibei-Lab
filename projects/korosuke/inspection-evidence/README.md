# Stage 3B continuation: sampled-solid inspection

Related #9, merged #8/#10, unmerged Draft #12. Baseline main
`3733a7e757e597d4e00fc636fc36d74b2e8f9c20`, tree
`ce5b0c374f455721cb80f5b94ffb972239e72325` (2026-11-11 JST).
The authenticated repository account was confirmed as tetsujisugimori-coder.
No repository AGENTS.md or local repository skills were present at this baseline.

This continuation **does not replace** the merged 2D or BRep analyzers. It adds an
original neutral fixture exporter and an offline mesh/evidence viewer. Draft #12's
redesign helper is not imported or silently treated as merged. Existing originals,
research, test evidence, and the separate approval-research Stage 3 are untouched.

## Public / private split

The public files contain generic code, self-authored neutral fixture geometry and
tests only. Actual character-specific CAD, coordinates, IDs, measurements, silhouettes,
private storage identities and derived meshes remain outside this repository.
The viewer can open an explicitly selected local JSON without transmitting it.
No new Pages deployment, new private repository, or permission change is made.

## Reproduction

With an installed FreeCAD Python binding:

```
PYTHONPATH=/usr/lib/freecad/lib:/usr/lib/freecad-python3/lib /usr/bin/python3 projects/korosuke/inspection-evidence/export_neutral.py /local/output
node --test projects/korosuke/inspection-viewer/model.test.mjs
```

Open inspection-viewer/index.html through a local static server. Import the generated
viewer.json. The schema uses world-space vertices per measured pose, mm, explicit
source identity, pose ID and angle in every result. Browser rendering is a mesh
projection, **not** a recomputation of the BRep intersection. Clear is only a sampled
geometric result; it does not certify manufacturing or motion safety.

The neutral exporter reopens FCStd and two per-part STEP files, compares volumes,
solid counts and bidirectional boolean differences, and measures four poses with
the existing OCC analyzer including the zero-required-clearance positive-overlap
counterexample. This is empirical OCC checking, not a rigorous numerical bound.

## Scope of actual-design recheck

A separate private copy remeasures the existing five unresolved pairs plus a
separate residual control, preserves originals, and compares the prior redesign
candidate. Existing pairwise interference remains. The earlier subtraction/pose/
STEP numerical discrepancies are investigated without increasing tolerances to
force acceptance. Where consistency fails, acceptance is UNRESOLVED. Private
viewer data supplies actual sampled poses, not interpolated evidence.

Continuous motion, actual support/fastener connectivity, strength, torque, wiring,
manufacturing and physical safety remain UNKNOWN / NOT_TESTED. This continuation
is not a declaration that the mechanism works, nor a general root-cause finding
about the CAD kernel. Source measurements and new measurements are kept separate.

## Verification status

See VERIFICATION.md for final local/CI/review identities and limitations. Failed
runs are retained separately from successful reruns. The new workflow executes
neutral solids plus old regressions, then 16 browser conditions against the
neutral BRep payload. It never receives private input. Artifacts include actual
HEAD/tree and hashes; workflow success must be checked independently of the mere
existence of an artifact.
