# Independent review of PR 8 numerical remediation

## Conclusion

No blocking numerical-soundness defect was found in the reviewed implementation.
The continuous CLEAR argument is supported by the outward integer arithmetic
actually implemented, rather than by an arbitrary epsilon or a high-precision
point estimate. The review is scoped to parsed-input mathematical 2D rectangles.
It is not machine-checked formal verification, real CAD acceptance, or evidence
that the five separately reported dynamic interferences have been resolved.

Reviewed source:

- `certified.py`: SHA-256 `760ec2f4af0a964293fe136e03101374240f6b2a5afc7b1f52fff54eb77da88d`
- `sweep.py`: SHA-256 `706152341bd033feab526a9861c2d96350486739247d8679d634fa67fce8923c`
- `NUMERICS.md`: SHA-256 `c3460555ac99aa35ecf72e505c24cf0675a78a8832de6fdb7857a82dbdb93e9d`

These were initially reviewed as working-tree changes based on
`e5079db255403134d1864fc8b4ed8b3e8418350d`. Final commit identity is recorded
separately when the parent supplies the final HEAD; this review does not silently
claim that the base commit contains the fix.

## Source proof review

1. **Input meaning and coordinate frame.** Accepted floating-point quantities are
   converted to their exact binary64 rational values. Lossy integer conversion is
   rejected. Angle span is checked as an exact rational difference. Fixed-center
   minus pivot and half-dimensions are computed as rational values before any
   finite-grid rounding. Consequently, cancellation of large world translations
   does not erase small local features.

2. **Primitive enclosures.** For scale S=10^60, rational conversion uses floor and
   ceiling; signed Python floor division and its negated counterpart cover both
   signs. Addition and negation are exact on endpoints. Multiplication checks all
   four endpoint products and rounds outward after division by S. Division is only
   by positive integers. Absolute value covers positive, negative, and crossing-zero
   intervals. No fixed-width overflow is present.

3. **Trigonometry.** Machin's identity combines exact rational alternating-series
   bounds for atan(1/5) and atan(1/239). Each omitted tail is bounded by its first
   omitted term. Sample angles are reduced exactly modulo 360, then to a residual
   in [-45,45). Interval conversion to radians therefore encloses the intended
   exact angle, including for huge or negative inputs. The runtime verifies |x|<=1.
   The recurrence encloses the cosine degree-62 and sine degree-63 polynomials;
   equivalently both are degree-63 Taylor polynomials with the appropriate zero
   coefficients. Taylor's theorem bounds either remainder by 1/64! on this domain.
   Its outward ceiling is added. Exact cardinal cases and quadrant swap/negation
   are consistent. Binary64 trigonometric results are not used for certification.

4. **Sampled geometry.** Rotated center and axis extents enclose the true rectangles.
   Each reported positive axis gap is no greater than true separation along that
   axis; their maximum is therefore no greater than true Euclidean separation.
   Overlap uses the actual world and rotated rectangle axes, not rounded edge
   normals. For every one of these four axes, distance.upper <= extent.lower is
   sufficient to prove overlapping projections. Applying the exact rectangle SAT
   then proves intersection. Interval dependence can prevent a proof but does not
   invert these implications.

5. **Continuous clearance.** R=|cx|+|cy|+w/2+h/2 bounds the Euclidean radius of every
   point in the moving rectangle. Exact rational midpoints and endpoint distances
   remain intact throughout subdivision. R*d*pi/180 bounds the travel of every
   moving point, because an arc-length bound dominates chord length. Its computed
   upper endpoint is conservative. The strict test gap.lower > motion.upper +
   tolerance.upper thus proves clearance beyond tolerance at every angle in the
   closed interval, including endpoints. Every leaf must have this proof before
   a pair is CLEAR. Limits or ambiguity produce UNRESOLVED, and any certified
   sample overlap produces OVERLAP.

6. **Output semantics.** An exact rational overlap angle is emitted separately
   from the legacy binary64 display approximation. This is necessary: the
   huge-pivot regression's display angle differs from its certified exact angle
   by -1/281474976710656 degree. The two are now explicitly distinguished.

`NUMERICS.md` accurately describes these obligations, the parsed-binary64 input
contract, possible loss of a proof at fixed precision, runtime/resource limits,
and the distinction between 2D screening and real-world safety. Retained float
helpers are now explicitly marked diagnostic and are absent from the certified
classification path.

## Independent checks

Run `independent_numeric_checks.py --source-dir PATH/TO/generic-kinematics
--output independent-results.json` with Python and mpmath 1.3.0. The script records
source hashes and asserts that the source did not change during the run. It uses
an independent 740-decimal-digit trigonometric/vertex/SAT/distance oracle and exact
Fraction arithmetic for primitive enclosure tests. Seed: 202611090753.

All checks passed:

- 2,500 exact-rational interval-arithmetic cases, including signed interval
  extrema, arbitrary large integers, conversion, absolute value and division.
- A pi enclosure comparison and 1,561 trigonometric/periodicity cases, including
  quadrant-adjacent nextafter values, tiny residuals, huge and negative angles,
  and exact rational angles unavailable as binary64.
- 1,000 independent rotational-motion upper-bound comparisons.
- 720 high-precision pose comparisons across scales from the smallest positive
  subnormal through 10^300. No overstated gap or false overlap was found.
- 360 independently constructed strict corner-overlap witnesses, spanning
  negative/quadrant/huge angles and large translations: **273 OVERLAP,
  87 UNRESOLVED, zero CLEAR**.
- 120 scene-level exact-translation and exact-periodicity checks.
- Ten centered-overlap extreme scenes, all OVERLAP, and ten opposite-max-finite
  coordinate scenes, all safely CLEAR without binary64 subtraction overflow.
- Five ordinary/scaled separated controls remained CLEAR.
- Four explicit invalid-input rejections, including an exact span above 360 that
  binary64 subtraction rounds to 360, a lossy integer, an overflowing integer,
  and an adjacent-float enormous-angle interval wider than 360.
- Sixty independently generated continuous screening scenes: 55 CLEAR, two
  UNRESOLVED, three OVERLAP. At 3,575 exact dyadic angles in the CLEAR scenes, the
  independent polygon oracle found no intersection and its vertex-to-segment
  Euclidean-distance calculation exceeded the requested tolerance.

The reported overlap angles for the original huge-pivot and moderate-tiny-boundary
fixtures were also checked independently against the parent-generated report.
Both have strict interior witnesses at the exact reported sample. The moderate
fixture retains its approximately 5.0811782193e-17 mm positive horizontal
penetration; it has not been dismissed using a contact epsilon. Details are in
`reported-overlap-witnesses.json`.

The parent separately owns the immutable four-case and 18,000-case before/after
runs; this review does not double-count those as independently repeated stress
runs. The two huge-angle fixtures returning UNRESOLVED is appropriate: an
endpoint overlap need not be sampled, but it prevents a continuous CLEAR proof.

## Limits

Finite checks supplement the source proof review. They are neither exhaustive nor
an estimated error rate. The proof assumes correct Python integer/Fraction/runtime
behavior. Parsed decimal intent and measurement uncertainty remain outside the
contract. Fixed precision and conservative axis/L1 bounds can produce UNRESOLVED
for safe inputs, especially tiny features or near-contact. That is permitted and
must not be interpreted as PASS. No private CAD, original character geometry, or
other private originals were read, modified, or copied for this review.
