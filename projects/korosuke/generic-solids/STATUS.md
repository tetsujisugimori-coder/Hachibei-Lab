# Stage 3B measurement status

Recorded 2026-11-09. Overall PARTIAL; final independent review and CI acceptance pending.

The private original archive was acquired and all 185 extracted files matched its members byte-for-byte. The recorded five unresolved pairs were identified from the original final-release evidence and remeasured on the original solid geometry, not reconstructed substitutes. A predeclared 5-degree scan, observed-boundary refinement and local sampled-maximum refinement produced 556 pair/pose measurements including a separate micro-residual control. All five interferences were reproduced; zero computation failures occurred. This is successful detection, not design resolution. Two pairs already overlap at the reference pose and all sampled poses, so a simple travel-limit change alone is insufficient for those pairs.

Exact private identities, dimensions, transformed poses, volumes, locations, per-pair CAD snapshots, plots, CSV and improvement proposals remain in the private deliverable. No private archive or document identifiers are published here. No original design was overwritten. Continuous-motion certification, full-body clearance, manufacturing clearance, strength, fastening, wiring and drive loads remain unverified.

Public verification completed locally: 20 solid/runner tests, 120 independent analytic-box cases, 7 intentional-corruption rejections and 20 unchanged Stage 3A regressions. Existing tracked files at baseline were preserved.

Initial CI run [42597382913](https://github.com/tetsujisugimori-coder/Hachibei-Lab/actions/runs/42597382913) failed in dependency installation: Ubuntu has no package named freecad-python3. Its tests were NOT_RUN, not PASS. The workflow was corrected to the distribution's freecad package and explicit pipefail. A successful final run has not yet been confirmed. CI and independent findings will be appended before the final recommendation.
