# Independent follow-up review

Reviewed executable HEAD `5c428a0ab131827d01e4234902a56091c6fc46e8`, tree `9c064973849ae894aa0fcd5351bdc1e47a1e5b9a`.
Runner SHA-256 `b3181cc613a2b60ef1f540ae12d5c5b3339377e575271ad5e3d2f455dc50837f`; probe SHA-256 `386a977d41c84f54147e96ce6cb1d0c68096f2497159fa69479f692e007da43e`.

Decision: limited code/evidence review PASS; overall acceptance remains PARTIAL, merge recommendation NO while browser/Windows outcomes remain incomplete. This is not an approval or browser acceptance.

- Independently read the final runner and tests. Ran 33 tests with the unchanged one-second fixture deadline: PASS.
- Seven independent real-subprocess cases: normal completed PASS; post-write result readback failure, candidate receipt readback failure, excess stdout, scan file-size excess, missing protocol/evidence, and SIGTERM-resistant descendant each returned BLOCKED. The evidence consumer also rejected every adverse case. Parent environment unchanged.
- The original post-write false PASS counterexample is closed for the reviewed protocol: result.json is provisional PENDING and a validated completion receipt is required. Saved failed attempts are retained.
- Prior 33-test run had two failures. Its raw records show timeout before the probe/conflict was created; the save-conflict injection was not reached. New attempts do not erase that run or prove its timing cause. Root cause remains UNKNOWN.
- Read the one final browser attempt's original stdout/stderr and result/receipt directly; confirmed Node exit 2, Chromium SIGABRT and socket EPERM, no DOM event, and no no-sandbox flag. The reviewer did not launch a browser.
- Recomputed the original stdout/stderr hashes and all seven dedicated Temp file hashes; sizes and hashes match the sanitized summary. Completion receipt hashes match the saved records. Browser BLOCKED, DOM NOT_TESTED, Windows PENDING, quota/external backup UNKNOWN are not upgraded.
- FOLLOWUP.md and followup-summary.json do not expose private absolute paths or authentication values. Raw records remain private. Two documentation clarifications were requested before submission: describe the observed OWNED_GROUP_ABSENT result rather than an 'absent check', and only claim a prepared transfer ZIP after creation/verification.

No additional blocking code findings in the bounded cooperative-fixture scope. Escaped/daemonized descendants, host-wide residual absence, all internal browser Temp writes, durability across machine failure, final GitHub CI and Windows archive are outside this review's successful scope.

The independent harness initially used an incorrect repository path and failed before invoking the runner; this failed harness and log were retained. Its corrected path-only revision performed the seven cases above.

Reviewed 2026-11-12 21:11–21:13 UTC. Later documentation-only commits must retain these executable hashes; code changes require renewed review.

Readback of the two documentation corrections: confirmed. ZIP preparation is PENDING and the residual observation is explicitly restricted to the current PID namespace. Runner/probe SHA-256 remained unchanged.
