# Stage 3B measurement status

Recorded 2026-11-09. Overall PARTIAL; final independent review and CI acceptance pending.

The private original archive was acquired and all 185 extracted files matched its members byte-for-byte. The recorded five unresolved pairs were identified from the original final-release evidence and remeasured on the original solid geometry, not reconstructed substitutes. A predeclared 5-degree scan, observed-boundary refinement and local sampled-maximum refinement produced 556 pair/pose measurements including a separate micro-residual control. All five interferences were reproduced; zero computation failures occurred. This is successful detection, not design resolution. Two pairs already overlap at the reference pose and all sampled poses, so a simple travel-limit change alone is insufficient for those pairs.

Exact private identities, dimensions, transformed poses, volumes, locations, per-pair CAD snapshots, plots, CSV and improvement proposals remain in the private deliverable. No private archive or document identifiers are published here. No original design was overwritten. Continuous-motion certification, full-body clearance, manufacturing clearance, strength, fastening, wiring and drive loads remain unverified.

Public verification completed locally: 20 solid/runner tests, 120 independent analytic-box cases, 7 intentional-corruption rejections and 20 unchanged Stage 3A regressions. Existing tracked files at baseline were preserved.

Initial CI run [42597382913](https://github.com/tetsujisugimori-coder/Hachibei-Lab/actions/runs/42597382913) failed in dependency installation: Ubuntu has no package named freecad-python3. Its tests were NOT_RUN, not PASS. The workflow was corrected to the distribution's freecad package and explicit pipefail. A successful final run has not yet been confirmed. CI and independent findings will be appended before the final recommendation.

## Independent findings and corrections

An independent worker recomputed 56 actual pose/pair measurements with a separately implemented angular closure solution and direct BRep calls, without importing the target measurement functions. Results agree within approximately 4.3e-8 mm³ in common volume and 3.1e-14 mm in distance. This is independent code but the same OCC kernel and shared execution host; it is not an independent mathematical error guarantee. Original archive byte preservation was independently checked.

The reviewer found evidence acceptance defects: self-declared expected values could be forged together with measured values; a positive micro-volume could also be replaced by zero inside an absolute tolerance. The comparator now uses a separately trusted geometry registry, recomputes analytic expectations, checks input provenance, retains intersection sign, and checks measured and expected classifications independently. Fixed pre-/post-rejection evidence is stored under evidence/review-fix. Current local suite is 26 solid/runner/evidence tests, 120 analytic cases, 9 corruption controls, plus 20 unchanged Stage 3A regressions. Independent final retest is pending.

CI run [42598301091](https://github.com/tetsujisugimori-coder/Hachibei-Lab/actions/runs/42598301091) also failed before tests because Ubuntu's freecad package has no installation candidate. These failures remain FAIL/NOT_RUN. CI now uses a Debian 13 container and its official FreeCAD package, whose availability is documented at https://packages.debian.org/trixie/freecad-python3 . Final success is not assumed.
