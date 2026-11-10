# Verification record — 2026-11-11 JST

## Scope and baseline

Base main 3733a7e757e597d4e00fc636fc36d74b2e8f9c20; existing files preserved.
New code only: inspection-viewer/, inspection-evidence/, korosuke-inspection.yml.
Draft PR #18, related Issue #9. No private design data in this repository.

## Local checks

- Existing solid analyzer: 38 tests PASS; Stage 3A: 20 tests PASS.
- Analytic boxes: 120 cases PASS; 9 corruption controls rejected.
- Viewer validator: 26 tests PASS, including positive-overlap zero-clearance,
  missing/nonfinite data, source/pose mismatch, geometry IDs and triangle budgets.
- Independent reviewer reproduced the existing zero-required-clearance counterexample
  and neutral FCStd/two STEP roundtrip comparisons.
- Neutral actual OCC payload: local WebKit 8 conditions PASS (4 widths × two motion
  settings), including data import, input identity, every displayed result,
  sampled/unknown angles, visibility, keyboard camera, resize, 200% text,
  malformed input and reset/reload. Images and traces retained outside repository.
- Local Chromium: NOT_TESTED. Browser startup failed with socket EPERM; an explicit
  elevated execution request did not make startup succeed. No security setting
  changes or timeout relaxation. CI bundled Chromium is a different environment.

## Findings and corrections

1. Independent finite ±1e308 vertex input overflowed view arithmetic. Rejected by
   documented ±1e9 mm practical display coordinate bound; exact counterexample
   is now a regression. Intersection meshes also count toward global triangle cap.
2. WebKit small-width 200% text overflow: intrinsic controls and camera layout fixed;
   the same conditions rerun successfully. Initial failed matrix retained.
3. Dense private display input crashed the WebKit target and the runner later
   exited 137. Resource pressure is a hypothesis, not a demonstrated root cause.
   Renderer temporary allocations reduced using typed arrays. Original dense input
   and failure logs retained. Display tessellation and exact BRep values are distinct.
4. Import test initially used a descriptive string heuristic. Replaced by exact
   source SHA and input-pose result comparison. Reset while an older File.text read
   is pending is an explicit stale-result counterexample.

## Actual-design findings (private evidence)

Independent actual-shape remeasurement and before/after candidate comparison remain
separate from neutral fixture success. Original files and prior candidate unchanged.
All five target pairs still have unresolved mechanical acceptance; initial overlaps
remain. Existing numeric inconsistencies were reproduced, not hidden by tolerance
changes. Some STEP comparisons remain UNRESOLVED despite successful file reopening.
Actual-model meshes carry sampled measurements only. Display curve tessellation is
not exact geometry and its setting is not a certified maximum-error measurement.

## CI and final acceptance

The first remote HEAD f82c60bd started run42881381020. Its solid job succeeded;
subsequent source fixes require a new exact-HEAD CI run. Consult PR #18 final report
and formal review for the final commit/tree, CI URLs and raw artifact hashes.
An artifact's existence is not a successful test result. Browser16 formal acceptance
must refer to all 16 completed records at that final HEAD.

Until final CI and independent review complete, limited merge recommendation is NO.
Even a later generic viewer acceptance does not approve the private mechanism,
continuous path, torque, wiring, strength or physical safety. Windows actual PC,
physical iPhone Safari, physical input, CAD GUI manipulation and manufacture are
NOT_TESTED here. No merge, Draft release or production deployment performed.
