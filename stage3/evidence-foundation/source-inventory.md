# Approval evidence source survey
Research snapshot: 2026-11-11, completed by 01:05:49Z. Read-only. Baseline main: 5a6181015ab3d5ea82dd2d065f1179d3b22eedd4. Overall actual-approval authenticity and complete history: UNKNOWN; Stage 3 remains PARTIAL.

## Evidence labels
OBSERVED means a successful connected API response was inspected. A response proves what this service returned at collection time, not personal intent, legal authority, or the absence of withheld/deleted records. CAPABILITY means tool/API documentation, not a mutation tested here. UNKNOWN means not obtained or not established. No permission/rule changes or GitHub writes were performed.

## Public source inventory

| Record family | Controller / method | Actual accessible scope | Retention | Change/deletion and coverage limits |
|---|---|---|---|---|
| Issue and PR current bodies | GitHub service; repository owner/account attribution; connected GitHub GET | OBSERVED Issue #23, PR #19, all-state issues collection pages 1–2, 100/page. Page 1 returned 23 current issue/PR objects; page 2 empty. | UNKNOWN contractual retention | Current bodies and updated_at are not a complete edit log. Issue enumeration includes PRs. Deleted objects, inaccessible objects and concurrent mutations are not excluded by a terminal page. Exact actor rights to edit/delete were not tested: UNKNOWN. |
| PR reviews | GitHub service; attributed reviewer account; GET pulls/19/reviews | OBSERVED two submissions, both state COMMENTED, each tied to commit da3f1b761d04c4dad9a03207e44396eafa69eb71. Page 2 empty with same page size. | UNKNOWN | Review recommendation text is not the API APPROVED state. Account attribution/OWNER association is not proof of a human instruction to an agent. Review edit/dismiss/delete history completeness UNKNOWN. |
| Issue and inline review comments | GitHub service; attributed account; GET issues/19/comments and pulls/19/comments | OBSERVED each page 1 empty at 100/page. | UNKNOWN | Empty visible collections do not prove comments never existed. Historical edits/deletions and omitted pending content UNKNOWN. |
| Issue/PR events | GitHub service; GET issues/19/events | OBSERVED ready_for_review, merged, closed; page 2 empty. Merge at 2026-11-10T21:42:12Z, commit 61f37474cb14ec10b247e05d07a0db8fa4e3bf4b. | UNKNOWN | Event collection is a bounded endpoint, not a universal approval/revocation audit log. It does not establish why the merge was authorized. |
| Git commits and source snapshots | GitHub service hosting Git objects; connected commits/tree/file GET | OBSERVED main tree response truncated=false; commits pinned to baseline pages 1–2 returned 24 then 0. Baseline commit includes verification.verified=true/reason=valid/verified_at, GitHub committer and signed payload. Stage1 source-survey, Stage2 governance-map, Stage3 README read at pinned SHA. | UNKNOWN guaranteed remote retention | A Git object hash identifies content; references/branch heads can change. Reachability of deleted/rewritten history is UNKNOWN. API signature verification is a provider report about this commit, not independent validation of an approval issuer or scope. Author/committer dates are not agent decision times. |
| Existing public evidence and ledgers | Repository contributors; pinned file GET | OBSERVED Stage1 source-survey and Stage3 README explicitly distinguish source claims, synthetic records, UNKNOWN authority and incomplete histories. Tree shows public indexes, public relations, synthetic approvals and observed assessment files. | UNKNOWN beyond currently reachable Git | This survey did not validate every ledger row. Prior ledger conclusions remain attributed claims until original sources are checked. Schema/fixture success is not acceptance of actual approvals. |
| Actions artifacts / execution records | GitHub Actions service; GET run artifacts | OBSERVED run 42889270743 artifact metadata, head SHA, created_at, expires_at, expired=false and provider digest. | Observed artifact expires_at=2027-02-08T19:50:27Z; no general retention guarantee inferred | Artifact expiry is explicit for that item only. This survey did not download artifact bytes or verify its digest. Collection response total_count=1 is not a full execution universe. Logs/artifacts may be unavailable later; decision time and approval content remain UNKNOWN. |
| Non-public document/ledger services | Service and authorized document owners; authenticated read APIs | Private-source observations are held separately. No identifiers, text, links, counts or inferred private inventory are published here. | UNKNOWN unless separately observed for the specific record class | Current document content, revision labels, copied quotations and source hashes do not by themselves prove enactment, authorized authorship or complete replacement/revocation history. |
| Non-public conversation approval records | Conversation service; authenticated visible-message reads | Private observations held separately. | UNKNOWN | Current message/reaction metadata cannot establish complete edit/delete or all-channel history. Approval requires exact content/context, issuer identity, target/scope and subsequent changes. |
| Decision/execution and revocation history as a whole | Potentially multiple controllers | No single complete authoritative collection established. | UNKNOWN | All-source population, missing-source discovery, trusted decision timestamp, full amendment/revocation chain and point-in-time visibility are UNKNOWN. Never substitute GitHub merge, CI start, file update or retrieval time for a decision timestamp. |

## Concrete public observations versus claims
- PR19 is merged in the API even though its editable body still says Draft would be maintained. This is not evidence of an unauthorized merge: a historical body statement and later state change are different evidence types. Preserve both rather than using the stale body as current status.
- Both review submissions are COMMENTED. Their bodies recommend a limited research merge and retain Stage3 PARTIAL; the provider did not return an APPROVED review in this collection.
- Commit signature verification is observable provider data. This research did not independently verify a signing key trust chain or bind it to any private approval.
- An authenticated app acting under an account may create content attributed to that account. Account attribution alone must not be treated as independent human authorship.
- A successful terminal page proves only collection exhaustion for those parameters during that non-atomic observation. It does not prove universal history coverage or no later revocation.

## Collection limits and recommended receipts
Retain endpoint, repo/ref and filters, page size, page/cursor identity, ordered record IDs, collection start/end times, exact acquired representation hash, item count, terminal marker and errors. Store provider timestamps separately. Keep each response and fetched source version; do not recompute an old snapshot hash from current data.

GitHub fetch returns response body but these inspected responses did not expose HTTP Link/ETag/rate-limit headers. Numbered page2 probes were used for nonempty review/event/issues/commit samples. No lock or snapshot consistency across mutable endpoints was established. No audit-log endpoint or deleted-object archive was acquired. Never label a page receipt as an authoritative coverage attestation.

The available specialized issue-comments wrapper advertises all-page traversal. Some specialized Actions wrappers advertise first-page-only behavior. These are tool capability descriptions, not proof this survey exercised those wrappers. Prefer explicit page receipts when claiming bounded collection coverage.

## Public evidence URLs
- https://github.com/tetsujisugimori-coder/Hachibei-Lab/issues/23
- https://github.com/tetsujisugimori-coder/Hachibei-Lab/pull/19
- https://github.com/tetsujisugimori-coder/Hachibei-Lab/pull/19#pullrequestreview-5848381933
- https://github.com/tetsujisugimori-coder/Hachibei-Lab/pull/19#pullrequestreview-5849893506
- https://api.github.com/repos/tetsujisugimori-coder/Hachibei-Lab/issues/19/events?per_page=100&page=1
- https://api.github.com/repos/tetsujisugimori-coder/Hachibei-Lab/pulls/19/reviews?per_page=100&page=1
- https://api.github.com/repos/tetsujisugimori-coder/Hachibei-Lab/commits/5a6181015ab3d5ea82dd2d065f1179d3b22eedd4
- https://api.github.com/repos/tetsujisugimori-coder/Hachibei-Lab/git/trees/main?recursive=1
- https://api.github.com/repos/tetsujisugimori-coder/Hachibei-Lab/actions/runs/42889270743/artifacts?per_page=100&page=1
- https://github.com/tetsujisugimori-coder/Hachibei-Lab/blob/5a6181015ab3d5ea82dd2d065f1179d3b22eedd4/stage1/source-survey.md
- https://github.com/tetsujisugimori-coder/Hachibei-Lab/blob/5a6181015ab3d5ea82dd2d065f1179d3b22eedd4/stage2/governance-map.md
- https://github.com/tetsujisugimori-coder/Hachibei-Lab/blob/5a6181015ab3d5ea82dd2d065f1179d3b22eedd4/stage3/README.md
