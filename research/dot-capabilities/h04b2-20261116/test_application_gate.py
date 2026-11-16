import copy
import unittest
from application_gate import evaluate,ROUTES,DIMENSIONS,CONDITIONS

def good():
    return dict(schema='H04B2/1',mode='synthetic',routes={r:{d:dict(status='PASS',kind='synthetic_technical',reference='synthetic:fixture') for d in DIMENSIONS} for r in ROUTES},conditions={c:'PASS' for c in CONDITIONS},sequence=dict(b0_thread='synthetic:b0',b1_thread='synthetic:b1',b0_frozen=1,b1_delivered=2))
class GateTests(unittest.TestCase):
    def check(self,data,contract='PASS',gate='BLOCKED'):
        out=evaluate(data)
        self.assertEqual(out['contract'],contract);self.assertEqual(out['synthetic_gate'],gate)
        self.assertIs(out['execution_allowed'],False);self.assertEqual(out['experiment_start'],'BLOCKED');self.assertEqual(out['exclusivity'],'UNKNOWN')
    def test_normal_synthetic_never_authorizes(self):self.check(good(),gate='PASS')
    def test_all_route_nonpass(self):
        for r in ROUTES:
            for d in DIMENSIONS:
                for state in ('FAIL','UNKNOWN','BLOCKED'):
                    with self.subTest(route=r,dimension=d,state=state):
                        x=good();x['routes'][r][d]['status']=state;self.check(x)
    def test_instructions_not_technical(self):
        for r in ROUTES:
            for d in DIMENSIONS:
                x=good();x['routes'][r][d]['kind']='instruction_only';self.check(x)
    def test_missing_cell(self):
        for r in ROUTES:
            for d in DIMENSIONS:
                x=good();del x['routes'][r][d];self.check(x,'FAIL')
    def test_unsupported_pass(self):
        for kind,ref in [('missing',''),('synthetic_technical',''),('synthetic_technical','synthetic:'),('synthetic_technical','synthetic:  '),('synthetic_technical','real://unknown')]:
            x=good();x['routes']['history']['applied'].update(kind=kind,reference=ref);self.check(x,'FAIL')
    def test_conditions(self):
        for c in CONDITIONS:
            for state in ('FAIL','UNKNOWN','BLOCKED'):
                x=good();x['conditions'][c]=state;self.check(x)
    def test_thread_reuse(self):
        x=good();x['sequence']['b1_thread']='synthetic:b0';self.check(x)
    def test_wrong_order(self):
        for order in (0,1):
            x=good();x['sequence']['b1_delivered']=order;self.check(x)
    def test_invalid(self):
        for x in (None,[],True,1,'text',{},dict(good(),mode='real')):self.check(x,'FAIL')
    def test_bad_types(self):
        for value in (True,None,1.5,-1,'2'):
            x=good();x['sequence']['b0_frozen']=value;self.check(x,'FAIL')
    def test_extra_route(self):
        x=good();x['routes']['other']={};self.check(x,'FAIL')
    def test_missing_condition(self):
        for c in CONDITIONS:
            x=good();del x['conditions'][c];self.check(x,'FAIL')
if __name__=='__main__':unittest.main()
