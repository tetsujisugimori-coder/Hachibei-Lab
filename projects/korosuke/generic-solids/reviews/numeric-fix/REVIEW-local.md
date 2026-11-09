# Stage 3B numeric fix: independent local review

Candidate source is a copied workspace snapshot, not yet a final remote commit. Final GitHub HEAD and CI/artifact acceptance are pending.

## Findings

No unresolved P1/P2 was found in the reviewed local numeric change. The previous result for two overlapping 2 mm boxes with required clearance 0 mm was VOLUME_OVERLAP together with MEASURED_AT_OR_ABOVE_REQUIREMENT. The same original input now returns INTERFERENCE. Contact is explicitly distinct from manufacturing clearance. Near-boundary distances remain UNRESOLVED. Positive volumes are preserved, and late exceptions reset both geometry and manufacturing classifications to UNRESOLVED.

The geometric classification continues to be an empirical OCC result, not a rigorous floating-point enclosure or continuous-motion guarantee. The outward-nextafter reporting band does not change this limitation.

## Independent verification

- 132 box/clearance combinations independently predicted using exact Fraction interval geometry. The target classification function was not used as the oracle.
- Five near-requirement cases independently predicted using exact rational values of the input binary64 floats.
- Fixed old/new counterexample, micro-overlap, invalid requirements.
- Existing/new solid suite 38 tests; analytic fixture suite 120 cases / 9 intentional corruption rejections; unchanged Stage 3A 20 tests.
- Existing independently supplied 10 extra geometry controls, 4 evidence attacks, and timeout control rerun.
- 52 files at baseline main 7f0342d39871f3b10717a9a1ac5c52def78d6484 byte-identical.
- Public-source scan found no private Space identifiers or credential patterns. Manual changes contain only generic code, neutral primitives, logs, and documentation. This is not a universal secret-detection guarantee.

## CI review

The exact-workspace safe.directory is supplied on each rev-parse command only, without changing global/system ownership protections. GIT_TEST_ASSUME_DIFFERENT_OWNER=1 produced exit 128 with the original invocation and exit 0 with the new command-local exception. The diagnostic git config query returns 1 for absent entries and is explicitly allowed; it does not prevent binding.

The workflow checks actual checkout HEAD against the requested PR head, records actual tree, test outcome and completion flag. A failed/missing binding or checksum ledger must not be accepted solely because upload-artifact succeeded. Final runtime logs and artifacts still require direct review.

## Scope

No private CAD was modified or transferred. The private 185 originals were read-only SHA-256 checked against the prior original-member ledger: 185 match, zero changed/missing. Only the aggregate count is included in this public report. Five real interference pairs remain unresolved. Physical safety, strength, torque, wiring, manufacturing tolerances and continuous motion remain unverified.
