"""Offline research evaluator. Never issues approvals or executes actions."""
import argparse
import json
import re
from datetime import datetime, timezone

STATES = ('VALID', 'OUT_OF_SCOPE', 'NOT_YET_EFFECTIVE', 'EXPIRED', 'REVOKED',
          'NO_RECORD', 'INSUFFICIENT_EVIDENCE', 'CONFLICT')


def instant(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})', value):
        raise ValueError('timestamp requires explicit timezone and seconds')
    if value[-1] != 'Z' and (int(value[-5:-3]) > 23 or int(value[-2:]) > 59):
        raise ValueError('invalid timezone offset components')
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(timezone.utc)
    except OverflowError as error:
        raise ValueError('timestamp outside supported UTC range') from error


def exact_keys(obj, required):
    if not isinstance(obj, dict) or set(obj) != set(required.split()):
        raise ValueError('missing or unknown fields')


def strings(values):
    return isinstance(values, list) and bool(values) and all(isinstance(x, str) and x.strip() and '*' not in x for x in values) and len(values) == len(set(values))


def validate(data):
    exact_keys(data, 'schema_version evidence_kind observed_at history_complete_through approvals decisions')
    if data['schema_version'] != '1.0' or data['evidence_kind'] not in ('SYNTHETIC', 'OBSERVED', 'DESIGN_ONLY'):
        raise ValueError('unsupported schema or evidence kind')
    observed = instant(data['observed_at'])
    through = instant(data['history_complete_through']) if data['history_complete_through'] is not None else None
    if through and through > observed:
        raise ValueError('coverage beyond observation')
    if not isinstance(data['approvals'], list) or not isinstance(data['decisions'], list):
        raise ValueError('collections must be arrays')
    ids = set()
    for a in data['approvals']:
        exact_keys(a, 'id issuer authority source version retrieved_at events')
        if not all(isinstance(a[k], str) and a[k].strip() for k in ('id', 'issuer', 'source', 'version')) or a['id'] in ids:
            raise ValueError('invalid or duplicate approval ID')
        ids.add(a['id'])
        if instant(a['retrieved_at']) > observed:
            raise ValueError('retrieval after observation')
        exact_keys(a['authority'], 'status evidence')
        if a['authority']['status'] not in ('VERIFIED', 'UNKNOWN') or not isinstance(a['authority']['evidence'], str):
            raise ValueError('invalid authority')
        if a['authority']['status'] == 'VERIFIED' and not a['authority']['evidence'].strip():
            raise ValueError('verified authority lacks evidence')
        if not isinstance(a['events'], list):
            raise ValueError('events must be array')
        event_ids = set()
        for e in a['events']:
            exact_keys(e, 'id sequence kind recorded_at effective_at expires_at actions targets conditions evidence')
            if not isinstance(e['id'], str) or not e['id'] or e['id'] in event_ids:
                raise ValueError('duplicate event ID')
            event_ids.add(e['id'])
            if type(e['sequence']) is not int or e['sequence'] < 1 or e['kind'] not in ('GRANT', 'AMEND', 'REVOKE', 'CORRECT'):
                raise ValueError('invalid sequence/kind')
            recorded, effective = instant(e['recorded_at']), instant(e['effective_at'])
            if recorded > observed:
                raise ValueError('future evidence')
            if e['expires_at'] is not None and instant(e['expires_at']) <= effective:
                raise ValueError('nonpositive validity interval')
            if not strings(e['actions']) or not strings(e['targets']) or not isinstance(e['conditions'], dict):
                raise ValueError('scope invalid (exact IDs only)')
            if any(not isinstance(k, str) or not k or type(v) not in (str, bool, int) for k,v in e['conditions'].items()):
                raise ValueError('invalid conditions')
            if not isinstance(e['evidence'], str) or not e['evidence'].strip():
                raise ValueError('event evidence missing')
    decision_ids = set()
    for d in data['decisions']:
        exact_keys(d, 'id action target approval_ids proposed_at decided_at execution_at completed_at observed_choice conditions evidence')
        if not all(isinstance(d[k], str) and d[k] for k in ('id','action','target','evidence')) or d['id'] in decision_ids:
            raise ValueError('invalid/duplicate decision ID')
        decision_ids.add(d['id'])
        if not isinstance(d['approval_ids'], list) or any(not isinstance(x,str) for x in d['approval_ids']) or len(set(d['approval_ids'])) != len(d['approval_ids']):
            raise ValueError('invalid references')
        if d['observed_choice'] not in ('EXECUTE','DECLINE','REFUSE','HOLD','UNKNOWN') or not isinstance(d['conditions'], dict):
            raise ValueError('invalid decision state')
        if any(type(v) not in (str,bool,int) for v in d['conditions'].values()):
            raise ValueError('invalid decision conditions')
        ordered = [instant(d[k]) for k in ('proposed_at','decided_at','execution_at','completed_at') if d[k] is not None]
        if d['decided_at'] is None or ordered != sorted(ordered) or any(t > observed for t in ordered) or (d['completed_at'] and not d['execution_at']):
            raise ValueError('invalid lifecycle ordering')


def approval_at(a, d, when, coverage):
    reasons = []
    events = a['events']
    # The caller attests authority/coverage. This engine cannot authenticate them.
    if a['authority']['status'] != 'VERIFIED':
        return 'INSUFFICIENT_EVIDENCE', ['authority not verified']
    if not coverage or coverage < when:
        return 'INSUFFICIENT_EVIDENCE', ['history coverage does not reach evaluation time']
    if not events:
        return 'INSUFFICIENT_EVIDENCE', ['history missing']
    seq = [e['sequence'] for e in events]
    if seq != list(range(1,len(events)+1)):
        return 'CONFLICT', ['history order/gap/duplicate sequence']
    if events[0]['kind'] != 'GRANT' or any(e['kind']=='GRANT' for e in events[1:]):
        return 'CONFLICT', ['invalid grant history']
    if any(instant(events[i]['recorded_at']) > instant(events[i+1]['recorded_at']) or instant(events[i]['effective_at']) > instant(events[i+1]['effective_at']) for i in range(len(events)-1)):
        return 'CONFLICT', ['nonmonotonic history']
    # No retroactive semantics are invented. Even a correction logged later can
    # challenge a historical conclusion; expose it rather than silently replaying.
    if any(e['kind']=='CORRECT' or instant(e['effective_at']) < instant(e['recorded_at']) for e in events):
        return 'INSUFFICIENT_EVIDENCE', ['correction or backdated event needs explicit interpretation']
    if any(e['kind']=='REVOKE' for e in events[:-1]):
        return 'CONFLICT', ['events after revocation need new approval ID']
    applicable = [e for e in events if instant(e['effective_at']) <= when]
    if not applicable:
        return 'NOT_YET_EFFECTIVE', ['grant not effective']
    # AMEND cannot revive an expired chain. A separate GRANT ID is required.
    for previous, current in zip(applicable, applicable[1:]):
        if current['kind'] == 'AMEND' and previous['expires_at'] is not None and instant(current['effective_at']) >= instant(previous['expires_at']):
            return 'INSUFFICIENT_EVIDENCE', ['AMEND_AT_OR_AFTER_EXPIRY: extension versus new grant unresolved; events '+previous['id']+' -> '+current['id']]
    e = applicable[-1]
    if e['kind']=='REVOKE':
        return 'REVOKED', ['revocation effective at or before evaluation']
    if e['expires_at'] is not None and when >= instant(e['expires_at']):
        return 'EXPIRED', ['half-open validity interval ended']
    if d['action'] not in e['actions'] or d['target'] not in e['targets']:
        return 'OUT_OF_SCOPE', ['exact action/target mismatch']
    for k,v in e['conditions'].items():
        if k not in d['conditions']:
            return 'INSUFFICIENT_EVIDENCE', ['required condition not evidenced: '+k]
        if type(v) != type(d['conditions'][k]) or v != d['conditions'][k]:
            return 'OUT_OF_SCOPE', ['condition mismatch: '+k]
    return 'VALID', ['explicit scope, authority evidence and complete ordered history match']


def at(data, d, when):
    refs = d['approval_ids']
    by_id = {a['id']:a for a in data['approvals']}
    coverage = instant(data['history_complete_through']) if data['history_complete_through'] is not None else None
    results=[]
    for ref in refs:
        a=by_id.get(ref)
        state, reasons = approval_at(a,d,when,coverage) if a else ('NO_RECORD',['referenced approval missing'])
        results.append({'approval_id':ref,'status':state,'reasons':reasons,'source':a['source'] if a else None})
    states={r['status'] for r in results}
    # No inferred priority or OR across mixed permissions. Uniform valid is valid;
    # ambiguous multi-approval sets require explicit resolution by a human.
    state = 'NO_RECORD' if not states else next(iter(states)) if len(states)==1 else 'CONFLICT'
    return {'status':state,'evaluated_at':when.isoformat(),'approvals':results,
            'reason':'mixed approval outcomes: priority not established' if len(states)>1 else 'see individual evidence'}


def evaluate(data):
    validate(data)
    rows=[]
    for d in data['decisions']:
        decision=at(data,d,instant(d['decided_at']))
        execution=at(data,d,instant(d['execution_at'])) if d['execution_at'] else None
        missing = []
        if d['observed_choice'] == 'EXECUTE' and execution is None:
            missing.append('execution_at')
            execution = {'status':'INSUFFICIENT_EVIDENCE', 'evaluated_at':None,
                         'approvals':[], 'reason':'MISSING_EXECUTION_AT: execution-time validity cannot be evaluated'}
        evaluated = [decision] + ([execution] if execution is not None else [])
        if any(x['status'] in ('INSUFFICIENT_EVIDENCE','NO_RECORD','CONFLICT') for x in evaluated):
            missing.append('resolvable_approval_evidence')
        recorded_execution = d['execution_at'] is not None
        consistency = ('MISMATCH' if (d['observed_choice']=='EXECUTE' and
                       (decision['status']!='VALID' or recorded_execution and execution['status']!='VALID')) or
                       (recorded_execution and d['observed_choice'] in ('DECLINE','REFUSE','HOLD')) else
                       'UNKNOWN' if d['observed_choice']=='UNKNOWN' else 'NO_MISMATCH_IN_RECORDED_FIELDS')
        completeness = 'INSUFFICIENT_EVIDENCE' if missing or d['observed_choice']=='UNKNOWN' else 'SUFFICIENT_FOR_MODEL_EVALUATION'
        rows.append({'decision_id':d['id'],'action':d['action'],'target':d['target'],
                     'evidence_kind':data['evidence_kind'],'observed_choice':d['observed_choice'],
                     'decision':decision,'execution':execution,'completed_at':d['completed_at'],
                     'evidence':d['evidence'], 'operational_authorization':'NOT_GRANTED_BY_THIS_TOOL',
                     'consistency':consistency,
                     'evidence_completeness':{'status':completeness,'missing':missing},
                     'history_authenticity':{'status':'UNKNOWN','reason':'Supplied claims are not independently authenticated by this tool'},
                     'history_coverage':{'claimed_complete_through':data['history_complete_through'],'verification':'NOT_PERFORMED_BY_THIS_TOOL'},
                     'overall':{'status':'PARTIAL','reason':'MODEL_ONLY: authentic and exhaustive operational history remains unverified'}})

    return {'schema_version':'1.1','input_schema_version':'1.0','results':rows,'limits':['Authority and history completeness are supplied evidence claims, not authenticated by this engine.','No external operations performed.','A valid decision does not imply valid authority at later execution.']}


def explain(result):
    lines=[]
    for r in result['results']:
        lines.append(f"{r['decision_id']} {r['action']} {r['target']}: choice={r['observed_choice']}; consistency={r['consistency']}; evidence={r['evidence']}")
        for phase in ('decision', 'execution'):
            item=r[phase]
            if not item:
                lines.append(f"  {phase}: NOT_OBSERVED")
                continue
            lines.append(f"  {phase}: {item['status']} at {item['evaluated_at']}; {item['reason']}")
            lines.extend(f"    {a['approval_id']}: {a['status']} ({'; '.join(a['reasons'])}); source={a['source']}" for a in item['approvals'])
    return '\n'.join(lines)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('input'); p.add_argument('--explain',action='store_true'); args=p.parse_args()
    try:
        with open(args.input,encoding='utf-8') as f: result=evaluate(json.load(f))
    except (ValueError,TypeError,KeyError) as error:
        print(json.dumps({'status':'INSUFFICIENT_EVIDENCE','input_error':str(error)})); raise SystemExit(2)
    print(explain(result) if args.explain else json.dumps(result,ensure_ascii=False,indent=2))
