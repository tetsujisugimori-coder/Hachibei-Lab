"""Bounded in-memory observations, conservative foundation bridge, safe projection.

Reads JSON from stdin, writes fixed-vocabulary judgment only. No network, files,
source mutation, approval issuance, persistence, or operational authorization.
Input is analyst-supplied observations, not an authenticated export. Even a supplied
SOURCE_BYTES digest is only an in-memory comparison against a supplied digest.
"""
import base64
import binascii
import json
import sys

from approval import exact_keys, instant
from evidence import MAX_BYTES, MAX_ITEMS, audit, canonical, digest, nullable_text, sha, strict_json, text

KINDS = ('REVIEW', 'EXECUTION', 'EXPLICIT_APPROVAL', 'AMENDMENT', 'REVOCATION', 'DELETION', 'OTHER')
STATES = ('COMMENTED', 'APPROVED', 'CHANGES_REQUESTED', 'DISMISSED', 'MERGED', 'EXECUTED',
          'EXPLICIT', 'AMENDED', 'REVOKED', 'DELETED', 'UNKNOWN')
REPRESENTATIONS = ('SOURCE_BYTES', 'CONNECTOR_JSON', 'NORMALIZED_OBSERVATION', 'NOT_OBTAINED')
MODEL_STATES = ('VALID', 'OUT_OF_SCOPE', 'NOT_YET_EFFECTIVE', 'EXPIRED', 'REVOKED',
                'NO_RECORD', 'INSUFFICIENT_EVIDENCE', 'CONFLICT')


def sequence(value):
    if not isinstance(value, list) or len(value) > MAX_ITEMS:
        raise ValueError('invalid bounded array')


def validate(snapshot):
    exact_keys(snapshot, 'schema_version evidence_kind observed_at window source records pages expectation model')
    if snapshot['schema_version'] != '1.0' or snapshot['evidence_kind'] not in ('SYNTHETIC', 'OBSERVED'):
        raise ValueError('unsupported snapshot')
    observed = instant(snapshot['observed_at'])
    exact_keys(snapshot['window'], 'start end')
    if not instant(snapshot['window']['start']) < instant(snapshot['window']['end']) <= observed:
        raise ValueError('invalid window')
    source = snapshot['source']
    exact_keys(source, 'controller acquisition access_scope from_origin revisions_visible deletions_visible')
    for key in ('controller', 'acquisition', 'access_scope'):
        text(source[key])
    if source['from_origin'] is not None and type(source['from_origin']) is not bool:
        raise ValueError('invalid origin')
    for key in ('revisions_visible', 'deletions_visible'):
        if source[key] not in ('YES', 'NO', 'UNKNOWN'):
            raise ValueError('invalid visibility')
    exact_keys(snapshot['expectation'], 'approver actor target action')
    for value in snapshot['expectation'].values():
        nullable_text(value)
    sequence(snapshot['records'])
    sequence(snapshot['pages'])
    ids = set()
    for record in snapshot['records']:
        exact_keys(record, 'id native_id revision previous_id kind actor target action state recorded_at retrieved_at representation bytes_base64 sha256')
        for key in ('id', 'native_id', 'revision'):
            text(record[key])
        if record['id'] in ids:
            raise ValueError('duplicate record ID')
        ids.add(record['id'])
        for key in ('previous_id', 'actor', 'target', 'action'):
            nullable_text(record[key])
        if record['kind'] not in KINDS or record['state'] not in STATES or record['representation'] not in REPRESENTATIONS:
            raise ValueError('invalid enum')
        compatible = {'REVIEW': ('COMMENTED', 'APPROVED', 'CHANGES_REQUESTED', 'DISMISSED', 'UNKNOWN'),
                      'EXECUTION': ('MERGED', 'EXECUTED', 'UNKNOWN'), 'EXPLICIT_APPROVAL': ('EXPLICIT', 'UNKNOWN'),
                      'AMENDMENT': ('AMENDED', 'UNKNOWN'), 'REVOCATION': ('REVOKED', 'UNKNOWN'),
                      'DELETION': ('DELETED', 'UNKNOWN'), 'OTHER': ('UNKNOWN',)}
        if record['state'] not in compatible[record['kind']]:
            raise ValueError('incompatible record kind and state')
        if not instant(record['recorded_at']) <= instant(record['retrieved_at']) <= observed:
            raise ValueError('invalid record lifecycle')
        sha(record['sha256'])
        raw = record['bytes_base64']
        if raw is not None:
            if not isinstance(raw, str) or len(raw) > MAX_BYTES:
                raise ValueError('invalid bounded bytes')
            base64.b64decode(raw, validate=True)
        if record['representation'] == 'NOT_OBTAINED' and (raw is not None or record['sha256'] is not None):
            raise ValueError('absent bytes cannot have digest')
    for page in snapshot['pages']:
        exact_keys(page, 'cursor next_cursor retrieved_at record_ids reported_total')
        nullable_text(page['cursor']); nullable_text(page['next_cursor'])
        if instant(page['retrieved_at']) > observed:
            raise ValueError('future page')
        sequence(page['record_ids'])
        for rid in page['record_ids']:
            text(rid)
        total = page['reported_total']
        if total is not None and (type(total) is not int or total < 0):
            raise ValueError('invalid total')


def build_ledger(snapshot):
    """Map observations to OTHER, never infer GRANT, expiry, or decided_at.

    No artifact is invented or written. The foundation therefore explicitly sees
    missing persisted originals/receipts. Caller must keep this intermediate private.
    Optional model is separate, conditional input; no semantic bindings are invented.
    """
    validate(snapshot)
    model = snapshot['model']
    if model is None:
        model = {'schema_version': '1.0', 'evidence_kind': snapshot['evidence_kind'],
                 'observed_at': snapshot['observed_at'], 'history_complete_through': None,
                 'approvals': [], 'decisions': []}
    source = snapshot['source']
    collection = {'from_origin': source['from_origin'], 'snapshot': None,
                  'scope': source['access_scope'], 'start': snapshot['window']['start'],
                  'end': snapshot['window']['end'], 'revisions_visible': source['revisions_visible'],
                  'deletions_visible': source['deletions_visible'],
                  'pages': [dict(p, artifact=None, sha256=None) for p in snapshot['pages']]}
    ledger = {'schema_version': '1.0', 'evidence_kind': snapshot['evidence_kind'],
              'observed_at': snapshot['observed_at'], 'window': dict(snapshot['window']),
              'sources': [{'id': 'OBS-SOURCE', 'kind': 'OBSERVATION', 'controller': source['controller'],
                           'acquisition': source['acquisition'], 'retention': 'UNKNOWN',
                           'scope': source['access_scope'], 'mutability': 'UNKNOWN',
                           'authenticity_claim': None, 'authority_claim': None, 'coverage_claim': None,
                           'collection': collection}], 'records': [], 'bindings': [],
              'model_sha256': digest(canonical(model))}
    for record in snapshot['records']:
        # The normalized record is a claim about a source, not the source bytes.
        normalized_hash = digest(canonical(record))
        ledger['records'].append({'id': record['id'], 'source_id': 'OBS-SOURCE',
                                 'native_id': record['native_id'], 'revision': record['revision'],
                                 'role': 'OTHER', 'subject': record['target'] or 'UNKNOWN',
                                 'recorded_at': record['recorded_at'], 'retrieved_at': record['retrieved_at'],
                                 'previous_id': record['previous_id'], 'artifact': None,
                                 'sha256': normalized_hash, 'original_artifact': None,
                                 'original_sha256': record['sha256'] if record['representation'] == 'SOURCE_BYTES' else None,
                                 'transformation': 'ANALYST_OBSERVATION_NOT_VERIFIED'})
    return ledger, model


def assess(snapshot):
    ledger, model = build_ledger(snapshot)
    # Every artifact path is None: audit cannot open any filesystem object.
    foundation = audit(ledger, None, model)
    conflicts = foundation['status'] == 'CONFLICT'
    records = snapshot['records']
    expected = snapshot['expectation']
    correspondence = 'UNKNOWN'
    relevant_complete = []
    original_checks, representation_checks = [], []
    revision_values = {}
    for record in records:
        raw, claimed = record['bytes_base64'], record['sha256']
        check = 'NOT_TESTED' if raw is None or claimed is None else (
            'MATCH' if digest(base64.b64decode(raw, validate=True)) == claimed else 'CONFLICT')
        representation_checks.append(check)
        original_checks.append(check if record['representation'] == 'SOURCE_BYTES' else 'NOT_TESTED')
        conflicts |= check == 'CONFLICT'
        if record['kind'] in ('EXPLICIT_APPROVAL', 'EXECUTION'):
            actor = expected['approver' if record['kind'] == 'EXPLICIT_APPROVAL' else 'actor']
            pairs = [(record['actor'], actor), (record['target'], expected['target']),
                     (record['action'], expected['action'])]
            states_known = record['state'] in ('EXPLICIT', 'MERGED', 'EXECUTED')
            relevant_complete.append(states_known and all(a is not None and b is not None for a, b in pairs))
            if any(a is not None and b is not None and a != b for a, b in pairs):
                correspondence = 'CONFLICT'; conflicts = True
            elif all(a is not None and b is not None for a, b in pairs) and correspondence != 'CONFLICT':
                correspondence = 'CLAIMED'
        key = (record['native_id'], record['revision'])
        semantic = tuple(record[k] for k in ('kind', 'actor', 'target', 'action', 'state', 'recorded_at'))
        if key in revision_values and revision_values[key] != semantic:
            conflicts = True
        revision_values[key] = semantic
    # A partial approval or lone execution cannot establish correspondence.
    approvals = [r for r in records if r['kind'] == 'EXPLICIT_APPROVAL']
    executions = [r for r in records if r['kind'] == 'EXECUTION']
    order = 'UNKNOWN'
    if approvals and executions:
        order = 'CLAIMED'
        if any(instant(a['recorded_at']) > instant(e['recorded_at']) for a in approvals for e in executions):
            order = 'RECORDED_AFTER_EXECUTION'
    if correspondence == 'CLAIMED' and (not approvals or not executions or not all(relevant_complete)
                                        or order == 'RECORDED_AFTER_EXECUTION'):
        correspondence = 'UNKNOWN'
    def combined(checks):
        return 'CONFLICT' if 'CONFLICT' in checks else 'MATCH' if checks and all(c == 'MATCH' for c in checks) else 'NOT_TESTED'
    def present(kind, state=None):
        return any(r['kind'] == kind and (state is None or r['state'] == state) for r in records)
    states = set()
    if snapshot['model'] is not None:
        for result in foundation['model_assessment']['results']:
            for phase in ('decision', 'execution'):
                if result[phase] is not None:
                    states.add(result[phase]['status'])
    # Explicit allowlist projection, not redaction of private free text.
    return {
        'schema_version': '1.0', 'evidence_kind': snapshot['evidence_kind'],
        'status': 'CONFLICT' if conflicts else 'INSUFFICIENT_EVIDENCE',
        'overall': 'PARTIAL', 'limited_technical_acceptance': 'PARTIAL',
        'operational_authorization': 'NOT_GRANTED_BY_THIS_TOOL', 'operation': 'HOLD',
        'acquisition': 'PARTIAL' if records else 'NOT_OBTAINED',
        'source_metadata': 'CLAIMED', 'authenticated_access_scope': 'UNKNOWN',
        'authenticity': 'UNKNOWN', 'identity': 'UNKNOWN', 'authority_at_approval': 'UNKNOWN',
        'source_original_integrity': combined(original_checks),
        'supplied_representation_integrity': combined(representation_checks),
        'normalization_fidelity': 'UNKNOWN',
        'review_commented': 'CLAIMED' if present('REVIEW', 'COMMENTED') else 'UNKNOWN',
        'review_approved': 'CLAIMED' if present('REVIEW', 'APPROVED') else 'UNKNOWN',
        'merge_record': 'CLAIMED' if present('EXECUTION', 'MERGED') else 'UNKNOWN',
        'explicit_approval': 'CLAIMED' if present('EXPLICIT_APPROVAL', 'EXPLICIT') else 'NOT_OBTAINED',
        'validity_period': 'UNKNOWN', 'revision_history': 'UNKNOWN', 'revocation_history': 'UNKNOWN',
        'deletion_history': 'UNKNOWN', 'history_coverage': 'UNKNOWN',
        'change_signal': 'CLAIMED' if any(present(k) for k in ('AMENDMENT', 'REVOCATION', 'DELETION')) else 'UNKNOWN',
        'page_traversal': foundation['sources'][0]['page_traversal'],
        'approval_action_correspondence': correspondence, 'approval_execution_order': order,
        'foundation_status': foundation['status'],
        'model_mapping': 'NO_SEMANTIC_BINDINGS',
        'model_evaluation': 'NOT_EVALUABLE' if snapshot['model'] is None else 'CONDITIONAL_ONLY',
        'conditional_model_states': sorted(states.intersection(MODEL_STATES)),
        'preservation': 'NOT_PRESERVED', 'preservation_gate': 'HOLD',
        'public_projection': 'FIXED_VOCABULARY_ONLY',
    }


def main():
    try:
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError('input too large')
        result = assess(strict_json(raw))
    except (ValueError, TypeError, KeyError, OSError, UnicodeError, RecursionError, binascii.Error, OverflowError):
        # No source values, paths, exception text, tracebacks, or data counts.
        result = {'status': 'INSUFFICIENT_EVIDENCE', 'input_error': 'INVALID_OR_UNREADABLE_INPUT',
                  'overall': 'PARTIAL', 'operation': 'HOLD', 'preservation': 'NOT_PRESERVED',
                  'operational_authorization': 'NOT_GRANTED_BY_THIS_TOOL'}
        print(json.dumps(result, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
