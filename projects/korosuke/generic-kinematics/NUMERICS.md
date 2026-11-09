# Stage 3A numerical contract and conservative certificate

Status: numerical remediation for PR #8 / Issue #7. This is not a 3D collision,
manufacturing, strength, wiring, or whole-robot acceptance. The five previously
reported dynamic CAD interferences remain unresolved in a separate workstream.

## Decision record: alternatives considered before implementation

| Option | Guarantee and cost | Decision |
|---|---|---|
| binary64 with a derived error envelope | Fastest, but needs correctly bounded argument reduction, libm trig errors, cancellation, subnormals and every intermediate operation. An unexplained fixed epsilon is insufficient. | Not selected; portable libm error assumptions would be the difficult proof boundary. |
| outward interval arithmetic | Every operation encloses exact values; uncertainty can cause UNRESOLVED but cannot justify CLEAR. More arithmetic and conservative bounds. | Selected: Python arbitrary integers on a 10^60 fixed-point grid plus exact Fraction angles. No runtime package dependency. |
| high precision point calculation | Useful independent oracle; many digits alone do not prove rounding direction or continuous separation. External dependency and higher cost. | mpmath 1.3.0 at 100/160 digits only in optional independent checks, not runtime authority. |
| explicit narrow input limits | Simple if accompanied by a derived error envelope; arbitrary angle/coordinate thresholds alone miss moderate tiny boundaries. Limits might discard ordinary uses. | Preserve existing geometric/depth limits, reject lossy integer conversion, and state exact parsed-input semantics. Do not falsely certify out-of-domain input. |

This is a deliberately small certificate implementation, not a universal interval
library. Precision 10^-60 is a computational enclosure grid, **not a contact epsilon**.
All rounding goes outward, including values smaller than that grid. Time/performance
is measured separately; no realtime claim is made.

## Input domain and representation

- Standard Python finite binary64 values after JSON parsing are treated as **exact
  rational input quantities** using Fraction(float). Decimal text-to-binary64
  rounding, measurement uncertainty and manufacturing tolerances are NOT covered.
  For example JSON 0.1 means the parsed binary64 number, not mathematical 1/10.
- JSON integers are accepted only if float conversion is finite and exactly
  preserves the integer. Larger/lossy integers are explicitly rejected. Booleans,
  NaN/infinity, zero/negative sizes and invalid schemas are rejected.
- Finite coordinates of either sign, positive finite dimensions, nonnegative finite
  tolerance and positive finite minimum interval are supported as enclosed values.
  Opposite-sign huge world coordinates are subtracted as rationals, never as floats.
- Both angle endpoints must be finite and strictly increasing, and their **exact
  rational difference** must be at most 360 degrees. No additional arbitrary
  absolute-angle cap is needed: reduction of each exact sample modulo 360 precedes
  any approximation. The original unwrapped interval and width are preserved.
  Where binary64 cannot represent distinct endpoints with that width, input is
  rejected by the ordinary domain rule.
- 1–10 moving and 1–10 fixed axis-aligned neutral rectangles, maximum subdivision
  depth 0–16. moving centers are joint-local; fixed centers and pivot are world
  coordinates. Tolerance is clearance margin, not a change to overlap semantics.
- Integer arithmetic has no fixed-width overflow. Resource exhaustion or an
  exception is a failed run with no certificate, never CLEAR. The worst-case
  subdivision count can be expensive: at most 131071 nodes per pair at depth 16.

## Construction and proof obligations

### 1. Enclosure arithmetic

Interval integers [lo,hi] denote real [lo/S,hi/S], S=10^60. Conversion of rational
p/q uses floor(pS/q) and ceil(pS/q). Addition/subtraction are exact integer bounds.
Multiplication considers all four endpoint products and divides by S outward;
division here is only by a known positive integer and is rounded outward. Signed
Python floor division and ceil(a/b)=-floor(-a/b) also cover negative numbers.
Absolute value encloses both signs. No rounded numerical result is reused as an
exact lower or upper bound.

### 2. pi and trigonometry

Machin's identity pi=16 atan(1/5)-4 atan(1/239) is evaluated with exact Fraction
alternating sums of 80 terms; the first omitted term bounds each remainder.
The resulting pi interval is converted outward. A sample angle is reduced exactly
modulo 360 and shifted by integer multiples of 90 to [-45,45). Conversion to radians
uses that pi interval and guarantees |x| <= 1 (checked at runtime).

sin and cos use Taylor polynomials through degree 63, including zero coefficients.
The recurrence uses outward interval operations. Since all derivatives of sin/cos
have magnitude <=1 on the real line, the remainder for every x in the enclosed
[-1,1] domain is <=1/64!. The ceiling of this bound in grid units is added to each
side. Quadrant changes use exact swap/negation. Cardinal angles use exact 0 and 1.
The implementation does not trust math.sin/cos or the platform's argument reducer.

### 3. Common frame and sampled pose

fixed.center minus pivot, and size/2, are calculated as exact rationals **before**
interval conversion. Moving geometry stays in its joint-local frame. Rotation and
AABB extents are interval expressions. The lower bound g on separation is the
maximum of 0 and the four conservative axis gaps between enclosed AABBs. Any
positive such gap is <= true Euclidean rectangle separation; no square root or
rounded bbox distance enters the certificate.

PROJECTED_OVERLAP uses the true separating axes of the two rectangles: world x/y
and the rotated moving x/y axes. For each axis, interval distance upper <= extent
sum lower proves overlapping projections. All four must hold. Exact closed-set
contact counts as overlap when certifiable. Ambiguous contact stays UNRESOLVED,
not CLEAR. Dependency loss can only weaken the proof.

### 4. Continuous-angle certificate

lo/hi and midpoint=(lo+hi)/2 remain exact Fractions at every subdivision. The
midpoint can be nonrepresentable in binary64; it is not rounded for geometry.
Use d=max(midpoint-lo,hi-midpoint), exactly. For any point in the moving rectangle,
R=|cx|+|cy|+w/2+h/2 bounds its Euclidean radius. Its travel from sample to any angle
in this subinterval is at most R*d*pi/180 (arc length dominates chord length).
Every factor is outward-enclosed, yielding upper bound M. Any moving point's
distance to the fixed rectangle decreases by no more than its travel. Thus
**g > M + tolerance_upper** proves strict clearance beyond the configured margin
throughout the closed interval, including endpoints. Equality is not accepted.

Uncertified intervals are subdivided until depth/minimum-width limit, then marked
UNRESOLVED_2D. Exact rational subdivision cannot collapse to an endpoint, but an
explicit strict-interior guard also fails closed. A pair is CLEAR only when every
leaf is certified and none unresolved. A certified overlap at any sample yields
OVERLAP. This certificate is the continuous argument; dense sampling is a separate
regression heuristic, not its proof.

### 5. Report semantics and retained legacy helpers

`first_observed_overlap_deg_exact` is the certified rational angle; the older
`first_observed_overlap_deg` is only its binary64 display approximation. It may
round to a different angle at large magnitudes. Consumers requiring a witness
must use the exact field. Method identifies the new interval path.

`corners`, `intersects`, `bbox_gap` remain for historical diagnostic/test
compatibility. They are unbounded binary64 approximations, NOT safety evidence,
and are not called by `screen_pair`'s decision path. Old tests using them are
explicitly not independent mathematical validation.

## Validation and limits

The immutable four review fixtures and original scripts are preserved under
`numeric-validation/original/`, with original source commit and SHA-256 manifest.
The validation runner executes old and new code on identical files, verifies a
negative-control exit, and gates the 18000 independently constructed strict
corner overlaps (not a statistical accuracy estimate). Independent high-precision
point checks and independent implementation review complement the argument above.

No finite test suite proves this code free of defects; this is a reviewed,
mathematically derived enclosure method, not machine-checked formal verification.
The guarantee assumes Python integer/Fraction semantics and correct execution.
It is only about the mathematical 2D rectangles represented by parsed inputs,
not unknown real shapes, decimal intent, 3D collisions, CAD projection accuracy,
material strength, manufacturing tolerances, or operational robot safety.
