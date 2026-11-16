"""Validate a preparation audit; never certify evidence truth or authorize execution."""
from datetime import datetime
ROUTES=('history','transfer','memory','shared','search','handoff','unidentified')
DIMENSIONS=('available','authorized','requested','accepted','applied','verified','measured','alternative_excluded')

def evaluate(value):
    out=dict(contract='FAIL',evidence_authenticity='UNKNOWN',route_exclusivity='UNKNOWN',experiment_start='BLOCKED',execution_allowed=False,method_adopted=None,reasons=[])
    def need(condition, code):
        if not condition: raise ValueError(code)
    try:
        need(type(value) is dict and set(value)=={'schema','scope','routes'},'STRUCTURE')
        need(value['schema']=='H04B3-audit/1' and value['scope']=='preparation','SCOPE')
        need(type(value['routes']) is dict and set(value['routes'])==set(ROUTES),'ROUTES')
        for row in value['routes'].values():
            need(type(row) is dict and set(row)==set(DIMENSIONS),'DIMENSIONS')
            for cell in row.values():
                need(type(cell) is dict and set(cell)=={'status','observed_at','actor','environment','evidence','reason'},'CELL')
                need(type(cell['status']) is str and cell['status'] in ('PASS','FAIL','UNKNOWN','BLOCKED'),'STATUS')
                for k in ('observed_at','actor','environment','reason'):
                    need(type(cell[k]) is str and 0<len(cell[k])<=1024 and bool(cell[k].strip()),'PROVENANCE')
                try:
                    parsed=datetime.fromisoformat(cell['observed_at'])
                except ValueError:
                    raise ValueError('DATE_FORMAT') from None
                need(parsed.utcoffset() is not None,'TIMEZONE')
                ev=cell['evidence'];need(type(ev) is list and 0<len(ev)<=16,'EVIDENCE')
                need(all(type(e) is str and bool(e.strip()) and len(e)<=256 for e in ev),'EVIDENCE_REFERENCE')
        out['contract']='PASS'
    except (ValueError,TypeError,OverflowError,RecursionError) as e:
        out['reasons']=[str(e) if isinstance(e,ValueError) else 'INVALID_INPUT']
    return out
