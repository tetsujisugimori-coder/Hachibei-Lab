"""H04-B preparation-only readiness checker. It cannot send or authorize execution."""
import json
ROUTES=('history','transfer','memory','shared','search','handoff','unidentified')
CONDITIONS=('owner_approval','authorized_new_threads','answer_isolation','preregistered_scoring','contamination_excluded','technical_controls','stop_and_custody','b0_b1_independence','b1_after_b0')
STATES=('PASS','FAIL','UNKNOWN','BLOCKED','NOT_TESTED')
class Invalid(ValueError): pass
def need(x,reason):
    if not x: raise Invalid(reason)
def fields(x,names,reason): need(type(x) is dict and set(x)==set(names.split()),reason)
def evidence(x,kind):
    need(type(x) is list,'EVIDENCE_TYPE')
    for item in x:
        fields(item,'kind reference','EVIDENCE_STRUCTURE')
        need(item['kind']==kind and type(item['reference']) is str and bool(item['reference'].strip()),'EVIDENCE_PROVENANCE')
    return bool(x)
def decide(d):
    out={'contract':'FAIL','logical_gate':'BLOCKED','execution_allowed':False,'actual_experiment':'NOT_TESTED','automatic_sharing':'UNKNOWN','exclusive_route':'UNKNOWN','reasons':[]}
    try:
        fields(d,'schema mode aim conditions routes b0_exposure b0_b1_distinct answer_distinct','STRUCTURE')
        need(d['schema']=='H04B-preparation/1' and d['mode'] in ('synthetic','preparation'),'SCHEMA_MODE')
        need(d['aim']=='exclusive_route','AIM_CHANGE_REQUIRES_REAPPROVAL')
        kind='synthetic' if d['mode']=='synthetic' else 'authorized_record'
        fields(d['conditions'],' '.join(CONDITIONS),'CONDITION_SET')
        blockers=[]
        for name,row in d['conditions'].items():
            fields(row,'status evidence','CONDITION_STRUCTURE')
            need(type(row['status']) is str and row['status'] in STATES,'CONDITION_STATUS')
            has=evidence(row['evidence'],kind)
            need(row['status']!='PASS' or has,'UNSUPPORTED_PASS')
            # References supplied to this offline checker are not authenticated real evidence.
            if d['mode']=='preparation' and row['status']=='PASS': raise Invalid('REAL_PASS_NOT_AUTHENTICATED')
            if row['status']!='PASS':blockers.append(name+':'+row['status'])
        for name in ('b0_exposure','b0_b1_distinct','answer_distinct'):
            need(type(d[name]) is str and d[name] in ('YES','NO','UNKNOWN'),'RELATION_STATUS')
        if d['b0_exposure']!='NO':blockers.append('B0_EXPOSURE_NOT_EXCLUDED')
        if d['b0_b1_distinct']!='YES':blockers.append('THREAD_INDEPENDENCE_UNCONFIRMED')
        if d['answer_distinct']!='YES':blockers.append('ANSWER_REUSE_OR_UNKNOWN')
        rows=d['routes'];need(type(rows) is list and len(rows)==7,'ROUTE_SET');seen=set()
        for r in rows:
            fields(r,'route available authorized requested accepted applied checked measured self_report evidence alternative_excluded','ROUTE_STRUCTURE')
            n=r['route'];need(type(n) is str and n in ROUTES and n not in seen,'ROUTE_ID');seen.add(n)
            for f in ('available','authorized','requested','accepted','applied','checked','measured','alternative_excluded'):
                need(type(r[f]) is str and r[f] in STATES,'ROUTE_STATUS')
            need(type(r['self_report']) is str,'SELF_REPORT_TYPE')
            has=evidence(r['evidence'],kind)
            # Requirement/receipt alone does not establish actual control or observation.
            for f in ('applied','checked','measured','alternative_excluded'):
                need(r[f]!='PASS' or has,'UNSUPPORTED_ROUTE_PASS')
                if r[f]!='PASS':blockers.append(n+':'+f+':'+r[f])
            for f in ('available','authorized','requested','accepted'):
                if r[f]!='PASS':blockers.append(n+':'+f+':'+r[f])
            if d['mode']=='preparation' and any(r[f]=='PASS' for f in ('applied','checked','measured','alternative_excluded')):raise Invalid('REAL_ROUTE_NOT_AUTHENTICATED')
        out.update(contract='PASS',logical_gate='PASS' if not blockers else 'BLOCKED',reasons=blockers)
        # Even a perfect synthetic scenario NEVER grants permission to run.
        if d['mode']=='preparation':out['logical_gate']='BLOCKED'
    except (Invalid,TypeError,ValueError,RecursionError) as e:
        out['reasons']=[str(e) if isinstance(e,Invalid) else type(e).__name__]
    return out

def parse(raw):
    try:
        need(type(raw) is bytes and 0<len(raw)<=1048576,'INPUT_SIZE_TYPE')
        s=raw.decode('utf-8');need('\r' not in s and not s.startswith('\ufeff'),'ENCODING')
        def pairs(items):
            d={}
            for k,v in items:need(k not in d,'DUPLICATE_KEY');d[k]=v
            return d
        return decide(json.loads(s,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(Invalid('JSON_CONSTANT'))))
    except (ValueError,UnicodeError,RecursionError) as e:
        return {'contract':'FAIL','logical_gate':'BLOCKED','execution_allowed':False,'actual_experiment':'NOT_TESTED','automatic_sharing':'UNKNOWN','exclusive_route':'UNKNOWN','reasons':[str(e) if isinstance(e,Invalid) else type(e).__name__]}
if __name__=='__main__':
    import pathlib,sys
    try: result=parse(pathlib.Path(sys.argv[1]).read_bytes())
    except (OSError,IndexError):result={'contract':'FAIL','execution_allowed':False,'reasons':['INPUT_UNAVAILABLE']}
    print(json.dumps(result,ensure_ascii=False,indent=2));sys.exit(0 if result['contract']=='PASS' else 1)
