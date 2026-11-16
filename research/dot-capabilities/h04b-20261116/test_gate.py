import copy,json,pathlib,unittest
from gate import decide,parse,ROUTES,CONDITIONS

def fixture():
    ev=[{'kind':'synthetic','reference':'fixture-only'}]
    return {'schema':'H04B-preparation/1','mode':'synthetic','aim':'exclusive_route','conditions':{n:{'status':'PASS','evidence':copy.deepcopy(ev)} for n in CONDITIONS},'routes':[dict(route=n,available='PASS',authorized='PASS',requested='PASS',accepted='PASS',applied='PASS',checked='PASS',measured='PASS',self_report='',evidence=copy.deepcopy(ev),alternative_excluded='PASS') for n in ROUTES],'b0_exposure':'NO','b0_b1_distinct':'YES','answer_distinct':'YES'}

def cases():
    rows=[('normal_hypothetical',fixture(),'PASS','PASS',None)]
    def add(n,f,c,g,r=None):
        d=fixture();f(d);rows.append((n,d,c,g,r))
    for n in CONDITIONS:
        add('unknown_'+n,lambda d,n=n:d['conditions'][n].update(status='UNKNOWN',evidence=[]),'PASS','BLOCKED')
        add('blocked_'+n,lambda d,n=n:d['conditions'][n].update(status='BLOCKED',evidence=[]),'PASS','BLOCKED')
    for field in ('available','requested','accepted'):
        for state in ('UNKNOWN','FAIL','BLOCKED'):
            add('route_'+field+'_'+state,lambda d,field=field,state=state:d['routes'][0].update({field:state}),'PASS','BLOCKED')
    add('missing',lambda d:d.pop('conditions'),'FAIL','BLOCKED','STRUCTURE')
    add('type',lambda d:d.update(routes=False),'FAIL','BLOCKED','ROUTE_SET')
    add('self_report',lambda d:d['routes'][0].update(evidence=[],self_report='blocked'),'FAIL','BLOCKED','UNSUPPORTED_ROUTE_PASS')
    add('unsupported_condition',lambda d:d['conditions']['owner_approval'].update(evidence=[]),'FAIL','BLOCKED','UNSUPPORTED_PASS')
    add('exposure',lambda d:d.update(b0_exposure='YES'),'PASS','BLOCKED')
    add('same_thread',lambda d:d.update(b0_b1_distinct='NO'),'PASS','BLOCKED')
    add('same_answer',lambda d:d.update(answer_distinct='NO'),'PASS','BLOCKED')
    add('implicit_downgrade',lambda d:d.update(aim='limited_observation'),'FAIL','BLOCKED','AIM_CHANGE_REQUIRES_REAPPROVAL')
    add('duplicate_route',lambda d:d['routes'][1].update(route='history'),'FAIL','BLOCKED','ROUTE_ID')
    add('request_only',lambda d:d['routes'][0].update(applied='UNKNOWN',checked='UNKNOWN',measured='UNKNOWN',alternative_excluded='UNKNOWN'),'PASS','BLOCKED')
    add('actual_mode',lambda d:d.update(mode='real'),'FAIL','BLOCKED','SCHEMA_MODE')
    add('self_report_as_evidence',lambda d:d['conditions']['owner_approval']['evidence'][0].update(kind='self_report'),'FAIL','BLOCKED','EVIDENCE_PROVENANCE')
    return rows
class Tests(unittest.TestCase):
    def test_current_readiness(self):
        r=parse(pathlib.Path(__file__).with_name('READINESS.json').read_bytes());self.assertEqual(r['contract'],'PASS');self.assertEqual(r['logical_gate'],'BLOCKED');self.assertFalse(r['execution_allowed'])
    def test_malformed(self):
        for b in (b'{',b'[]',b'\xff',b'{"a":1,"a":2}',b'{"n":'+b'1'*5000+b'}'):
            self.assertEqual(parse(b)['contract'],'FAIL')
for n,d,c,g,reason in cases():
    def run(self,d=d,c=c,g=g,reason=reason):
        r=decide(d);self.assertEqual(r['contract'],c);self.assertEqual(r['logical_gate'],g);self.assertFalse(r['execution_allowed']);self.assertEqual(r['actual_experiment'],'NOT_TESTED');self.assertEqual(r['exclusive_route'],'UNKNOWN');self.assertEqual(r['automatic_sharing'],'UNKNOWN')
        if reason:self.assertEqual(r['reasons'],[reason])
    setattr(Tests,'test_'+n,run)
if __name__=='__main__':unittest.main()
