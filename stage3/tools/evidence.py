"""Read-only evidence ledger audit. Hashes and input claims never grant authority.

Only local, bounded, regular artifacts under the explicit evidence root are read.
No network access, signature trust provisioning, source mutation or execution.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

from approval import evaluate, exact_keys, instant

MAX_BYTES = 4 * 1024 * 1024
MAX_ITEMS = 1000


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(value).hexdigest()


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    def constant(_):
        raise ValueError('nonfinite JSON value')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def text(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 4096:
        raise ValueError('expected bounded nonempty text')


def array(value):
    if not isinstance(value, list) or len(value) > MAX_ITEMS:
        raise ValueError('expected bounded array')


def sha(value):
    if value is not None and (not isinstance(value, str) or
                              not re.fullmatch('[0-9a-f]{64}', value)):
        raise ValueError('expected SHA256 or null')


def nullable_text(value):
    if value is not None:
        text(value)


def unique(values):
    return len(values) == len(set(values))


def artifact(root, name):
    """Never follow an absolute path, traversal, symlink or special file."""
    text(name)
    path = Path(name)
    if path.is_absolute() or '..' in path.parts or '\\' in name:
        raise ValueError('unsafe artifact path')
    root = Path(root).resolve(strict=True)
    candidate = root
    for component in path.parts:
        candidate = candidate / component
        if candidate.is_symlink():
            raise ValueError('symlink artifact forbidden')
    resolved = candidate.resolve(strict=True)
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError('artifact must be a regular file inside evidence root')
    with resolved.open('rb') as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError('artifact too large')
    return data


def validate(ledger):
    exact_keys(ledger, 'schema_version evidence_kind observed_at window sources records bindings model_sha256')
    if ledger['schema_version'] != '1.0' or ledger['evidence_kind'] not in ('SYNTHETIC', 'OBSERVED', 'DESIGN_ONLY'):
        raise ValueError('unsupported ledger schema or evidence kind')
    observed = instant(ledger['observed_at'])
    exact_keys(ledger['window'], 'start end')
    start, end = (instant(ledger['window'][key]) for key in ('start', 'end'))
    if not start < end <= observed:
        raise ValueError('window must be nonempty, half-open and observed')
    sha(ledger['model_sha256'])
    for key in ('sources', 'records', 'bindings'):
        array(ledger[key])
    for source in ledger['sources']:
        exact_keys(source, 'id kind controller acquisition retention scope mutability authenticity_claim authority_claim coverage_claim collection')
        for key in ('id', 'kind', 'controller', 'acquisition', 'retention', 'scope', 'mutability'):
            text(source[key])
        for key in ('authenticity_claim', 'authority_claim', 'coverage_claim'):
            nullable_text(source[key])
        c = source['collection']
        exact_keys(c, 'from_origin snapshot scope start end revisions_visible deletions_visible pages')
        if c['from_origin'] not in (True, False, None) or (c['from_origin'] is not None and type(c['from_origin']) is not bool):
            raise ValueError('from_origin must be boolean or null')
        for key in ('snapshot', 'scope'):
            nullable_text(c[key])
        for key in ('revisions_visible', 'deletions_visible'):
            if c[key] not in ('YES', 'NO', 'UNKNOWN'):
                raise ValueError('invalid visibility')
        for key in ('start', 'end'):
            if c[key] is not None:
                instant(c[key])
        if c['start'] is not None and c['end'] is not None and not instant(c['start']) < instant(c['end']) <= observed:
            raise ValueError('invalid collection interval')
        array(c['pages'])
        for page in c['pages']:
            exact_keys(page, 'cursor next_cursor retrieved_at record_ids reported_total artifact sha256')
            for key in ('cursor', 'next_cursor', 'artifact'):
                nullable_text(page[key])
            if instant(page['retrieved_at']) > observed:
                raise ValueError('page retrieval beyond observation')
            array(page['record_ids'])
            for record_id in page['record_ids']:
                text(record_id)
            total = page['reported_total']
            if total is not None and (type(total) is not int or total < 0):
                raise ValueError('invalid reported total')
            sha(page['sha256'])
    ids = [source['id'] for source in ledger['sources']]
    if not unique(ids):
        raise ValueError('duplicate source ID')
    for record in ledger['records']:
        exact_keys(record, 'id source_id native_id revision role subject recorded_at retrieved_at previous_id artifact sha256 original_artifact original_sha256 transformation')
        for key in ('id', 'source_id', 'native_id', 'revision', 'subject'):
            text(record[key])
        if record['role'] not in ('APPROVAL', 'EVENT', 'DECISION', 'OTHER'):
            raise ValueError('invalid record role')
        for key in ('previous_id', 'artifact', 'original_artifact', 'transformation'):
            nullable_text(record[key])
        recorded, retrieved = instant(record['recorded_at']), instant(record['retrieved_at'])
        if not recorded <= retrieved <= observed:
            raise ValueError('invalid record lifecycle')
        sha(record['sha256'])
        sha(record['original_sha256'])
    if not unique([record['id'] for record in ledger['records']]):
        raise ValueError('duplicate ledger record ID')
    for binding in ledger['bindings']:
        exact_keys(binding, 'role model_id parent_id record_id')
        if binding['role'] not in ('APPROVAL', 'EVENT', 'DECISION'):
            raise ValueError('invalid binding role')
        for key in ('model_id', 'record_id'):
            text(binding[key])
        nullable_text(binding['parent_id'])


def audit(ledger, root, model=None):
    """Audit supplied receipts; even complete receipts are not a trusted export."""
    validate(ledger)
    findings = []
    def flag(level, code, ref):
        findings.append({'level': level, 'code': code, 'ref': ref})
    def inspect(name, expected, ref):
        if name is None or expected is None:
            flag('UNKNOWN', 'MISSING_ARTIFACT_OR_HASH', ref)
            return 'UNKNOWN', None
        try:
            raw = artifact(root, name)
        except FileNotFoundError:
            flag('UNKNOWN', 'ARTIFACT_UNAVAILABLE', ref)
            return 'UNKNOWN', None
        except (OSError, ValueError):
            flag('CONFLICT', 'ARTIFACT_UNSAFE_OR_UNREADABLE', ref)
            return 'CONFLICT', None
        if digest(raw) != expected:
            flag('CONFLICT', 'HASH_MISMATCH', ref)
            return 'CONFLICT', None
        return 'MATCH', raw

    sources = {s['id']: s for s in ledger['sources']}
    records = {r['id']: r for r in ledger['records']}
    record_results, payloads, identities, event_claims = [], {}, {}, {}
    for r in ledger['records']:
        ref = r['id']
        if r['source_id'] not in sources:
            flag('UNKNOWN', 'SOURCE_NOT_IN_INVENTORY', ref)
        integrity, raw = inspect(r['artifact'], r['sha256'], ref)
        original_integrity, original = inspect(r['original_artifact'], r['original_sha256'], ref + '/original')
        derivation = 'UNKNOWN'
        if raw is not None and original is not None:
            if raw == original:
                derivation = 'IDENTICAL_BYTES'
            elif r['transformation'] is not None:
                derivation = 'DESCRIBED_NOT_VERIFIED'
                flag('UNKNOWN', 'TRANSFORMATION_NOT_VERIFIED', ref)
            else:
                flag('UNKNOWN', 'TRANSFORMATION_UNDOCUMENTED', ref)
        if raw is not None:
            try:
                payloads[ref] = strict_json(raw)
            except (ValueError, UnicodeError, RecursionError):
                flag('CONFLICT', 'INVALID_RECORD_JSON', ref)
        if r['role'] == 'EVENT' and isinstance(payloads.get(ref), dict):
            event_id = payloads[ref].get('id')
            if isinstance(event_id, str):
                key = (r['subject'], event_id, r['revision'])
                encoded = canonical(payloads[ref])
                if key in event_claims and event_claims[key] != encoded:
                    flag('CONFLICT', 'CONTRADICTORY_EVENT_CONTENT', ref)
                event_claims[key] = encoded
        key = (r['source_id'], r['native_id'], r['revision'])
        if key in identities:
            prior = identities[key]
            flag('CONFLICT', 'DUPLICATE_SOURCE_REVISION' if prior['sha256'] == r['sha256'] else 'CONTRADICTORY_SOURCE_REVISION', ref)
        identities[key] = r
        previous = r['previous_id']
        if previous is not None:
            p = records.get(previous)
            if p is None:
                flag('UNKNOWN', 'MISSING_HISTORY_PREDECESSOR', ref)
            elif (p['source_id'], p['subject']) != (r['source_id'], r['subject']):
                flag('CONFLICT', 'HISTORY_SUBJECT_MISMATCH', ref)
            elif instant(p['recorded_at']) > instant(r['recorded_at']):
                flag('CONFLICT', 'HISTORY_TIME_REVERSED', ref)
        seen, current = set(), ref
        while current in records:
            if current in seen:
                flag('CONFLICT', 'HISTORY_CYCLE', ref)
                break
            seen.add(current)
            current = records[current]['previous_id']
        record_results.append({'record_id': ref, 'byte_integrity': integrity,
                               'original_byte_integrity': original_integrity,
                               'content_derivation': derivation,
                               'authenticity': 'UNKNOWN', 'authority': 'UNKNOWN'})

    source_results = []
    for s in ledger['sources']:
        ref, c = s['id'], s['collection']
        before = len(findings)
        pages = c['pages']
        if not pages or c['from_origin'] is not True:
            flag('UNKNOWN', 'COLLECTION_ORIGIN_UNPROVEN', ref)
        if not c['snapshot']:
            flag('UNKNOWN', 'SNAPSHOT_UNBOUND', ref)
        if c['scope'] != s['scope']:
            flag('UNKNOWN', 'COLLECTION_SCOPE_UNBOUND', ref)
        if c['start'] is None or c['end'] is None or instant(c['start']) > instant(ledger['window']['start']) or instant(c['end']) < instant(ledger['window']['end']):
            flag('UNKNOWN', 'COLLECTION_WINDOW_INCOMPLETE', ref)
        cursors, received, totals = set(), [], set()
        expected_cursor = None
        previous_time = None
        for i, page in enumerate(pages):
            page_ref = ref + '/page/' + str(i)
            if page['cursor'] != expected_cursor or (i and expected_cursor is None):
                flag('CONFLICT', 'PAGE_CHAIN_DISCONNECTED', page_ref)
            if page['cursor'] in cursors:
                flag('CONFLICT', 'CURSOR_LOOP', page_ref)
            cursors.add(page['cursor'])
            expected_cursor = page['next_cursor']
            now = instant(page['retrieved_at'])
            if previous_time is not None and now < previous_time:
                flag('CONFLICT', 'PAGE_RETRIEVAL_REVERSED', page_ref)
            previous_time = now
            if page['reported_total'] is not None:
                totals.add(page['reported_total'])
            received.extend(page['record_ids'])
            _, raw = inspect(page['artifact'], page['sha256'], page_ref)
            if raw is not None:
                try:
                    receipt = strict_json(raw)
                    exact_keys(receipt, 'cursor next_cursor record_ids reported_total snapshot scope start end')
                    expected = {key: page[key] for key in ('cursor', 'next_cursor', 'record_ids', 'reported_total')}
                    expected.update({key: c[key] for key in ('snapshot', 'scope', 'start', 'end')})
                    if canonical(receipt) != canonical(expected):
                        flag('CONFLICT', 'PAGE_RECEIPT_MISMATCH', page_ref)
                except (ValueError, UnicodeError, TypeError, RecursionError):
                    flag('CONFLICT', 'INVALID_PAGE_RECEIPT', page_ref)
        if pages and pages[-1]['next_cursor'] is not None:
            flag('UNKNOWN', 'PAGINATION_NOT_FINISHED', ref)
        if not unique(received):
            flag('CONFLICT', 'DUPLICATE_PAGE_RECORD', ref)
        expected_records = {r['id'] for r in ledger['records'] if r['source_id'] == ref}
        if set(received) != expected_records:
            flag('UNKNOWN', 'PAGE_RECORD_SET_MISMATCH', ref)
        if len(totals) > 1:
            flag('CONFLICT', 'TOTAL_CHANGED_DURING_COLLECTION', ref)
        elif totals and next(iter(totals)) != len(set(received)):
            flag('UNKNOWN', 'REPORTED_TOTAL_MISMATCH', ref)
        page_findings = findings[before:]
        traversal = 'CONFLICT' if any(f['level'] == 'CONFLICT' for f in page_findings) else 'INCOMPLETE' if page_findings else 'CONSISTENT_RECEIPTS'
        # Neither a claimed final cursor nor a reported total proves that the
        # source exposed deleted, withheld, mutable or out-of-scope records.
        source_results.append({'source_id': ref, 'page_traversal': traversal,
                               'provenance': 'DESCRIBED_NOT_AUTHENTICATED',
                               'authenticity': 'UNKNOWN', 'authority': 'UNKNOWN',
                               'history_coverage': 'UNKNOWN',
                               'revisions_visible_claim': c['revisions_visible'],
                               'deletions_visible_claim': c['deletions_visible']})
        flag('UNKNOWN', 'TRUSTED_AUTHENTICATION_NOT_AVAILABLE', ref)
        flag('UNKNOWN', 'EXHAUSTIVE_HISTORY_NOT_PROVEN', ref)
    if not sources:
        flag('UNKNOWN', 'NO_SOURCES', 'ledger')
    if not records:
        flag('UNKNOWN', 'NO_RECORDS', 'ledger')

    model_result = None
    binding_status = 'NOT_TESTED'
    if model is not None:
        model_result = evaluate(model)  # Existing model remains entirely unchanged.
        if model['evidence_kind'] != ledger['evidence_kind']:
            flag('CONFLICT', 'EVIDENCE_KIND_MISMATCH', 'model')
        if digest(canonical(model)) != ledger['model_sha256']:
            flag('CONFLICT', 'MODEL_HASH_MISMATCH', 'model')
        if instant(model['observed_at']) > instant(ledger['observed_at']):
            flag('UNKNOWN', 'MODEL_AFTER_EVIDENCE_OBSERVATION', 'model')
        expected = {}
        for a in model['approvals']:
            expected[('APPROVAL', a['id'], None)] = {key: value for key, value in a.items() if key != 'events'}
            for event in a['events']:
                expected[('EVENT', event['id'], a['id'])] = event
        for decision in model['decisions']:
            expected[('DECISION', decision['id'], None)] = decision
            for key in ('decided_at', 'execution_at'):
                at = decision[key]
                if at is not None and not instant(ledger['window']['start']) <= instant(at) < instant(ledger['window']['end']):
                    flag('UNKNOWN', 'EVALUATION_OUTSIDE_EVIDENCE_WINDOW', decision['id'])
        bound, used = set(), set()
        binding_start = len(findings)
        for b in ledger['bindings']:
            key = (b['role'], b['model_id'], b['parent_id'])
            ref = b['record_id']
            if key in bound or ref in used:
                flag('CONFLICT', 'DUPLICATE_BINDING', ref)
            bound.add(key)
            used.add(ref)
            if key not in expected:
                flag('CONFLICT', 'UNKNOWN_MODEL_BINDING', ref)
                continue
            r = records.get(ref)
            if r is None or ref not in payloads:
                flag('UNKNOWN', 'UNAVAILABLE_BOUND_RECORD', ref)
            elif r['role'] != b['role'] or r['subject'] != (b['parent_id'] or b['model_id']):
                flag('CONFLICT', 'BINDING_SUBJECT_MISMATCH', ref)
            elif canonical(payloads[ref]) != canonical(expected[key]):
                flag('CONFLICT', 'BOUND_PAYLOAD_MISMATCH', ref)
        if bound != set(expected):
            flag('UNKNOWN', 'INCOMPLETE_MODEL_BINDINGS', 'model')
        binding_findings = findings[binding_start:]
        binding_status = 'CONFLICT' if any(f['level'] == 'CONFLICT' for f in binding_findings) else 'INCOMPLETE' if binding_findings else 'MATCH'
    else:
        flag('UNKNOWN', 'MODEL_NOT_PROVIDED', 'model')

    conflict = any(f['level'] == 'CONFLICT' for f in findings)
    return {'schema_version': '1.0', 'evidence_kind': ledger['evidence_kind'],
            'status': 'CONFLICT' if conflict else 'INSUFFICIENT_EVIDENCE',
            'overall': 'PARTIAL', 'operational_authorization': 'NOT_GRANTED_BY_THIS_TOOL',
            'authenticity': 'UNKNOWN', 'authority': 'UNKNOWN', 'history_coverage': 'UNKNOWN',
            'sources': source_results, 'records': record_results, 'model_bindings': binding_status,
            'model_assessment': model_result, 'findings': findings,
            'limits': ['Byte equality is not proof of authorship or authority.',
                       'Receipt consistency does not prove source completeness.',
                       'No trusted signature, identity or exhaustive-history verifier is configured.',
                       'Model temporal validity remains conditional on supplied evidence claims.',
                       'Local reports may contain private identifiers; do not publish observed inputs or outputs.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ledger')
    parser.add_argument('--root', required=True)
    parser.add_argument('--model')
    args = parser.parse_args()
    try:
        ledger = strict_json(artifact(args.root, args.ledger))
        model = strict_json(artifact(args.root, args.model)) if args.model else None
        result = audit(ledger, args.root, model)
    except (ValueError, TypeError, KeyError, OSError, UnicodeError, RecursionError):
        # Do not echo file paths or source text in public CI error messages.
        print(json.dumps({'status': 'INSUFFICIENT_EVIDENCE', 'input_error': 'INVALID_OR_UNREADABLE_INPUT',
                          'operational_authorization': 'NOT_GRANTED_BY_THIS_TOOL'}))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0  # Process success is not evidence acceptance.


if __name__ == '__main__':
    raise SystemExit(main())
