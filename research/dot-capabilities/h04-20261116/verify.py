"""H04/1 synthetic envelope validator. No connector, network or runtime control."""
import hashlib
import json
import re

ROUTES = ('history', 'transfer', 'memory', 'shared', 'search', 'handoff', 'unidentified')
ID = re.compile(r'[A-Za-z][A-Za-z0-9_-]{2,63}\Z')

class Invalid(ValueError):
    pass

def require(value, reason):
    if not value:
        raise Invalid(reason)

def keys(value, expected, reason):
    require(type(value) is dict and set(value) == set(expected.split()), reason)

def identifier(value):
    return type(value) is str and ID.fullmatch(value) is not None

def text_bytes(value):
    require(type(value) is str and value and value.endswith('\n') and '\r' not in value and '\ufeff' not in value, 'TEXT_FORMAT')
    return value.encode('utf-8', errors='strict')

def pairs(items):
    out = {}
    for key, value in items:
        require(key not in out, 'DUPLICATE_JSON_KEY')
        out[key] = value
    return out

def route_judgment(rows):
    require(type(rows) is list and len(rows) == 7, 'ROUTE_SET')
    seen = set()
    results = {}
    for row in rows:
        keys(row, 'route requested accepted applied self_report evidence claim', 'ROUTE_STRUCTURE')
        name = row['route']
        require(type(name) is str and name in ROUTES and name not in seen, 'ROUTE_ID')
        seen.add(name)
        for field in ('requested', 'accepted', 'applied'):
            require(row[field] in ('UNKNOWN', 'NOT_TESTED', 'NO', 'YES') and type(row[field]) is str, 'CONTROL_STATE')
        require(type(row['self_report']) is str, 'SELF_REPORT_TYPE')
        require(type(row['evidence']) is list, 'EVIDENCE_TYPE')
        for ev in row['evidence']:
            keys(ev, 'id origin scope sha256', 'EVIDENCE_STRUCTURE')
            require(identifier(ev['id']) and ev['origin'] in ('synthetic', 'self_report', 'authorized_record'), 'EVIDENCE_ORIGIN')
            require(type(ev['scope']) is str and bool(ev['scope']), 'EVIDENCE_SCOPE')
            require(type(ev['sha256']) is str and re.fullmatch('[a-f0-9]{64}', ev['sha256']), 'EVIDENCE_HASH')
        # H04 is an offline format checker, not an authority for access enforcement.
        require(row['applied'] != 'YES', 'UNVERIFIED_CONTROL_APPLICATION')
        require(row['claim'] == 'UNKNOWN', 'UNSUPPORTED_ROUTE_CLAIM')
        results[name] = 'UNKNOWN'
    return results

def validate(raw):
    result = {'format': 'FAIL', 'content': 'NOT_TESTED', 'revision': 'NOT_TESTED',
              'acquisition_route': 'UNKNOWN', 'automatic_sharing': 'UNKNOWN',
              'real_experiment': 'NOT_TESTED', 'reasons': []}
    try:
        require(type(raw) is bytes and 0 < len(raw) <= 1048576, 'INPUT_SIZE_TYPE')
        value = raw.decode('utf-8', errors='strict')
        require('\r' not in value and not value.startswith('\ufeff') and value.endswith('\n'), 'JSON_ENCODING')
        data = json.loads(value, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(Invalid('JSON_CONSTANT')))
        keys(data, 'schema mode document restatement revision threads observations independent_trials routes automatic_sharing', 'ENVELOPE_STRUCTURE')
        require(data['schema'] == 'H04/1' and data['mode'] == 'synthetic', 'SCHEMA_MODE')
        d = data['document']
        keys(d, 'id version body sha256', 'DOCUMENT_STRUCTURE')
        require(identifier(d['id']) and d['version'] == 'v1', 'DOCUMENT_ID_VERSION')
        body = text_bytes(d['body'])
        require(re.fullmatch(r'架空H04\n識別子:[a-f0-9]{32}\n説明:[^\n]+\n', d['body']), 'DOCUMENT_FORMAT')
        require(type(d['sha256']) is str and hashlib.sha256(body).hexdigest() == d['sha256'], 'BODY_HASH')
        require(text_bytes(data['restatement']) == body, 'RESTATEMENT_MISMATCH')
        require(text_bytes(data['revision']) == body + '確認済み\n'.encode(), 'REVISION_MISMATCH')
        t = data['threads']
        keys(t, 'A B', 'THREAD_STRUCTURE')
        require(all(identifier(x) for x in t.values()) and t['A'] != t['B'], 'THREAD_IDENTITY')
        obs = data['observations']
        require(type(obs) is list and len(obs) == 4, 'RECORD_COUNT')
        expected = [('created',t['A']), ('before',t['B']), ('transfer',t['B']), ('after',t['B'])]
        ids = set()
        for index, (row, (kind, thread)) in enumerate(zip(obs, expected)):
            keys(row, 'id kind thread sequence complete truncated trial', 'OBSERVATION_STRUCTURE')
            require(identifier(row['id']) and row['id'] not in ids, 'OBSERVATION_ID')
            ids.add(row['id'])
            require(row['kind'] == kind and row['thread'] == thread, 'OBSERVATION_IDENTITY_ORDER')
            require(type(row['sequence']) is int and row['sequence'] == index, 'SEQUENCE')
            require(row['complete'] is True and row['truncated'] is False, 'INCOMPLETE_RECORD')
            require(row['trial'] == 'paired-001', 'TRIAL_ID')
        require(type(data['independent_trials']) is int and data['independent_trials'] == 1, 'INDEPENDENCE_OVERCOUNT')
        result['routes'] = route_judgment(data['routes'])
        require(data['automatic_sharing'] == 'UNKNOWN', 'AUTOMATIC_SHARING_INFERENCE')
        result.update(format='PASS', content='PASS', revision='PASS')
    except (Invalid, UnicodeError, json.JSONDecodeError, RecursionError, ValueError) as error:
        result['reasons'] = [str(error) if isinstance(error, Invalid) else type(error).__name__]
    return result

if __name__ == '__main__':
    import pathlib, sys
    try:
        raw = pathlib.Path(sys.argv[1]).read_bytes()
        answer = validate(raw)
    except (OSError, IndexError):
        answer = {'format': 'FAIL', 'reasons': ['INPUT_UNAVAILABLE']}
    print(json.dumps(answer, ensure_ascii=False, sort_keys=True))
    sys.exit(0 if answer['format'] == 'PASS' else 1)
