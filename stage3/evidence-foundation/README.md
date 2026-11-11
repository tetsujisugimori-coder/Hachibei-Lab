# Stage 3 evidence foundation v1

Issue #23 follows merged PR #19. Fixed start: `5a6181015ab3d5ea82dd2d065f1179d3b22eedd4`.
This is an offline, read-only research tool. It neither issues approvals nor
changes source records, formal rules, permissions, schedules or operational behavior.

## What this implementation establishes

The ledger records acquisition provenance, original and normalized artifact hashes,
source capabilities, revisions, history predecessors, bounded page receipts, and
exact bindings into the existing Stage 3 model. These are distinct from identity,
issuer authority, temporal validity and complete history. The existing evaluator
and its input/output contracts remain unchanged. Its conditional results appear
under `model_assessment`; no `VALID` result is copied into evidence acceptance.

Run from the repository root with Python 3.12 or later:

```sh
python -m unittest discover -s stage3/tools -v
python stage3/tools/evidence.py ledger.json --root stage3/evidence-foundation/synthetic --model model.json
python stage3/tools/check_repository.py
python stage3/tools/compare_evidence_reviews.py
```

Only synthetic fixtures enter CI. `--root` is the explicit local evidence directory;
ledger, model and artifact paths are relative to it. For private investigation,
use a separate private root outside the public checkout. Do not commit its inputs,
outputs, identifiers, body text, source locations or counts. CLI output can contain
private model data, so never send an observed report to public CI or logs.

## Independent judgments and conservative outcomes

| Field | What it means | What it does not establish |
| --- | --- | --- |
| `byte_integrity` | SHA256 of the acquired normalized bytes matches the ledger | Authorship, originality, authority |
| `original_byte_integrity` | Separately supplied original/export bytes match their hash | Service authenticity or exhaustive export |
| `content_derivation` | Bytes identical, or a transformation was described | Semantic fidelity of a differing normalization |
| `provenance` | Controller/acquisition/scope are documented claims | Authenticated identity |
| `page_traversal` | Receipts form a consistent chain, or are incomplete/conflicting | Deleted/hidden records or unqueried sources are covered |
| `authenticity`, `authority`, `history_coverage` | `UNKNOWN` in this implementation | No trust anchor, signature or complete-history verifier exists here |
| `model_assessment` | Prior Stage 3 conditional scope/time evaluation | An actual right to act |
| `model_bindings` | All expected model values match bound, hashed payloads | Truth of those payloads |

`status` is `CONFLICT` when observed inputs contradict one another and otherwise
`INSUFFICIENT_EVIDENCE`. `overall` stays `PARTIAL`; operational authorization is
always `NOT_GRANTED_BY_THIS_TOOL`. Input `VERIFIED`, signature text, a final cursor,
reported totals, a successful API call or a successful hash comparison never promote
these judgments. An exit code of zero means the audit ran, not that approval passed.
Malformed/unreadable inputs give a structured result and exit 2 without echoing paths.

## Ledger and artifact contract

`ledger.schema.json` documents structural v1.0. `evidence.py:validate` adds bounded
sizes, unique IDs, timestamps and lifecycle constraints. The supplied evaluation
window is half-open `[start,end)`; receipt intervals must cover it and model decision
and execution times must lie inside it. Observation, source-record and retrieval
times are separate. They do not prove the historical moment of an actor's decision.

- Source inventory includes controller, acquisition method, retention, scope and
  mutability, with explicit `UNKNOWN` where not known. Identity/authority/coverage
  claims remain untrusted text. Revision/deletion visibility is an explicit claim.
- Each record has a stable ledger ID, native source ID, revision, role, subject,
  recorded/retrieval timestamps, predecessor, original artifact/hash and normalized
  artifact/hash. `transformation` describes conversion without certifying it. Keep
  originals unchanged; append a new acquisition/revision instead of overwriting old
  evidence. A missing original is not replaced by a matching normalized hash.
- Each page receipt has request cursor, returned next cursor, retrieval timestamp,
  record IDs and optional reported total. An empty page with a cursor is not terminal.
  The hashed JSON receipt binds these to collection scope, interval and snapshot.
  Receipts are normalized acquisition records, not authenticated provider responses.
  Preserve provider originals separately and retain their relation to these receipts.
- Binding roles `APPROVAL`, `EVENT`, `DECISION` map to an exact model value. Approval
  payload excludes its `events` array because each event has its own binding. Event
  `parent_id` is its approval ID; other parent IDs are null. Record subject must match.
- `model_sha256` hashes `canonical(model)`: UTF-8, JSON keys sorted, compact separators,
  unescaped Unicode, no nonfinite numbers. This is a specified Python serialization,
  not a claim of RFC 8785 or a digital signature. Original-byte hashes use raw bytes.
- Unknown keys, duplicate JSON keys, invalid hashes, naive/impossible timestamps and
  booleans masquerading as totals are rejected. Arrays are limited to 1,000 entries
  and each artifact to 4 MiB. A larger investigation needs explicit bounded batches;
  do not truncate silently or mark a batch as complete global history.
- Artifact access rejects absolute/traversal paths, symlinks and non-regular files.
  The evidence directory must be stable and trusted against concurrent hostile
  mutation. This is not an adversarial multi-user filesystem sandbox.

## Detection and known limits

Tests cover hash tampering, rehashed changed payloads, missing originals/bindings,
contradictory source revisions and event content, missing predecessors, history
cycles, reversed timestamps, missing middle pages, repeated cursors, duplicate page
records, changing totals, incomplete windows and detached model hashes. A discrepancy
does not establish which source is correct. Do not silently choose one side.

This version does not implement signature verification, user identity proof,
authority delegation certification, service-specific history export, semantic
interpretation of natural-language approvals, or retroactive legal rules. Missing
trust anchors and complete revision/deletion access therefore remain UNKNOWN.
It does not poll, write to services, operate an approval system or implement Stage 4.

## Existing regressions and baseline preservation

The original 158-file preservation check is retained. A second fixed baseline
captures all 190 files at the start of this change, allowing only the repository
checker and Stage 3 workflow to change. The old checker compared against an earlier
Stage 3 base and incorrectly rejected unrelated already-merged research paths.
The new diff gate compares against this task's start while checking both sets of
protected hashes. Existing approval evaluator files and fixtures stay unchanged.

CI executes all Stage 3, Stage 2 and Stage 1 regressions; prior Issue #17 counterexamples;
the new synthetic ledger/expected result; preservation and bounded public scans.
The artifact manifest binds results to HEAD, tree and workflow hash. A bounded scan
is not proof that every possible secret is absent. Final independent review and CI
must be reported for the actual final commit, separately from actual-evidence acceptance.

## Independent review corrections

The initial published HEAD `e2a58d1` missed semantic conflicts in unbound alternate
APPROVAL and DECISION records, although its overall result still withheld authority.
It also leaked a Python traceback for an escaped unpaired surrogate and accepted
overflowing JSON exponents as infinity in an unbound OTHER payload. These were
independently reproduced, then fixed without changing the original approval model.
`compare_evidence_reviews.py` recreates the four exact synthetic attacks against the
fixed initial commit and current code. `review-counterexamples.json` retains their
before/after results. The original review evidence is retained separately; corrected
tests do not erase the initial defects or assert the absence of every other defect.
