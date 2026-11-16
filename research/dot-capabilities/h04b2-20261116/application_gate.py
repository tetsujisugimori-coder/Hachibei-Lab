"""Offline synthetic application-evidence gate. No experiment launcher or IO."""
ROUTES = ('history','transfer','memory','shared','search','handoff','unidentified')
DIMENSIONS = ('available','authorized','requested','accepted','applied','verified','measured','alternative_excluded')
STATES = ('PASS','FAIL','UNKNOWN','BLOCKED')
KINDS = ('synthetic_technical','instruction_only','missing')
CONDITIONS = ('separate_approval','distinct_new_threads','b0_record_frozen','b1_explicit_delivery','scoring_frozen','stop_custody_ready')

def evaluate(data):
    out = dict(contract='FAIL', synthetic_gate='BLOCKED', experiment_start='BLOCKED', execution_allowed=False, exclusivity='UNKNOWN', reasons=[])
    def need(ok, code):
        if not ok: raise ValueError(code)
    try:
        need(type(data) is dict and set(data)=={'schema','mode','routes','conditions','sequence'}, 'STRUCTURE')
        need(data['schema']=='H04B2/1' and data['mode']=='synthetic','SYNTHETIC_ONLY')
        need(type(data['routes']) is dict and set(data['routes'])==set(ROUTES),'ROUTES')
        blockers=[]
        for route in ROUTES:
            row=data['routes'][route]
            need(type(row) is dict and set(row)==set(DIMENSIONS),'DIMENSIONS')
            for dim in DIMENSIONS:
                cell=row[dim]
                need(type(cell) is dict and set(cell)=={'status','kind','reference'},'CELL')
                need(type(cell['status']) is str and cell['status'] in STATES,'STATUS')
                need(type(cell['kind']) is str and cell['kind'] in KINDS,'KIND')
                need(type(cell['reference']) is str and len(cell['reference'])<=128,'REFERENCE')
                if cell['status']=='PASS':
                    need(cell['kind']!='missing' and cell['reference'].startswith('synthetic:') and bool(cell['reference'][10:].strip()),'UNSUPPORTED_PASS')
                    if cell['kind']!='synthetic_technical': blockers.append(route+':'+dim+':INSTRUCTION_NOT_CONTROL')
                else: blockers.append(route+':'+dim+':'+cell['status'])
        need(type(data['conditions']) is dict and set(data['conditions'])==set(CONDITIONS),'CONDITIONS')
        for name, state in data['conditions'].items():
            need(type(state) is str and state in STATES,'CONDITION_STATUS')
            if state!='PASS': blockers.append(name+':'+state)
        seq=data['sequence']
        need(type(seq) is dict and set(seq)=={'b0_thread','b1_thread','b0_frozen','b1_delivered'},'SEQUENCE')
        for name in ('b0_thread','b1_thread'):
            need(type(seq[name]) is str and seq[name] in ('synthetic:b0','synthetic:b1'),'THREAD_SCOPE')
        for name in ('b0_frozen','b1_delivered'):
            need(type(seq[name]) is int and seq[name]>=0,'ORDER_TYPE')
        if seq['b0_thread']==seq['b1_thread']: blockers.append('THREAD_REUSE')
        if seq['b0_frozen']>=seq['b1_delivered']: blockers.append('B0_NOT_FROZEN_BEFORE_B1')
        out.update(contract='PASS',synthetic_gate='BLOCKED' if blockers else 'PASS',reasons=blockers)
    except (ValueError,TypeError,RecursionError) as error:
        out['reasons']=[str(error) if isinstance(error,ValueError) else 'INVALID_INPUT']
    return out
