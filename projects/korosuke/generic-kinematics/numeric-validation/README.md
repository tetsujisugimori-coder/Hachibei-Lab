# PR #8 numerical validation

The runtime and normal unittest suite use Python standard library only.
For optional independent numerical validation use an isolated environment with
`mpmath==1.3.0`, then:

```sh
python projects/korosuke/generic-kinematics/numeric-validation/run.py --output /tmp/pr8-numeric-results
```

The runner checks hashes before executing. `original/` preserves four input JSONs,
the three independent validation scripts and prior results byte-for-byte from
review commit `1c216907991d86b05b5fcf928de49f989c2104de`. The old implementation is
from evaluated HEAD `e5079db255403134d1864fc8b4ed8b3e8418350d`. `IMMUTABLE.json`
records provenance and byte hashes. No private robot CAD is used.

- The old four-fixture regression gate must exit 1. The current code must exit 0.
  Original input files and independent 100/160-digit witness methods do not change.
- Boundary18000 runs both old and current code on identical independently
  constructed strict overlaps, using the original loop plus input/result hashing.
  Compare `stress_with_hashes.py` with the immutable original: only hashing and
  metadata were added. Canonical input corpus SHA256 must match. Old counts must
  reproduce 17731 OVERLAP / 129 UNRESOLVED / 140 false CLEAR. New false CLEAR must
  be zero; unresolved is reported separately and is not relabelled overlap.
- The original ordinary 240-case independent geometry script is rerun, including
  its 7 examples, mirrors, 12 invalid-input and 4 report-fault controls. Its
  hardcoded historical `evaluated_head` is explicitly renamed in new output;
  current source SHA256 and checkout HEAD are attached. It is a finite binary64
  oracle, NOT the continuous proof or the high-precision extreme-case oracle.
- Additional runner negative controls inject false CLEAR, missing case and absent
  witness claims. They must be rejected. They test the validation gate, not physics.
- `run-metadata.json` records commands, exit status, timings, environment, HEAD/tree,
  dirty state, original hashes, current source hashes and outcomes. A dirty local
  run is identified honestly; final CI checks the pushed source and records its
  event HEAD in the uploaded metadata. `SHA256SUMS.json` covers generated results.

mpmath calculations corroborate the cases, but high precision alone is not formal
proof. The continuous guarantee is the reviewed enclosure argument in NUMERICS.md.
The independently authored reviewer checks are separate from this implementation
runner. All artifacts are neutral synthetic fixtures. No character-specific data,
private source, external image, or private Space reference belongs here.
