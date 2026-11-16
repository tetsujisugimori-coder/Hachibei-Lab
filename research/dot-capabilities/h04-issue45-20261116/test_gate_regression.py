"""Expanded H04-B fail-closed route-state contract, synthetic only."""
import copy, importlib.util, pathlib, unittest
from test_preflight import fixture as canary_fixture

PARENT=pathlib.Path(__file__).resolve().parents[1]/"h04b-20261116"/"gate.py"
spec=importlib.util.spec_from_file_location("h04b_gate_issue45",PARENT)
gate=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

def ready_fixture():
    evidence=[{"kind":"synthetic","reference":"fake-evidence"}]
    return {"schema":"H04B-preparation/1","mode":"synthetic","aim":"exclusive_route",
      "conditions":{name:{"status":"PASS","evidence":copy.deepcopy(evidence)} for name in gate.CONDITIONS},
      "routes":[{"route":name,"available":"PASS","authorized":"PASS","requested":"PASS",
                 "accepted":"PASS","applied":"PASS","checked":"PASS","measured":"PASS",
                 "self_report":"","evidence":copy.deepcopy(evidence),
                 "alternative_excluded":"PASS"} for name in gate.ROUTES],
      "b0_exposure":"NO","b0_b1_distinct":"YES","answer_distinct":"YES"}

class Regression(unittest.TestCase):
    def test_hypothetical_pass_never_enables_execution(self):
        r=gate.decide(ready_fixture())
        self.assertEqual((r["contract"],r["logical_gate"]),("PASS","PASS"))
        self.assertFalse(r["execution_allowed"])

    def test_every_route_field_nonpass_blocks(self):
        fields=("available","authorized","requested","accepted","applied","checked","measured","alternative_excluded")
        states=("UNKNOWN","FAIL","BLOCKED","NOT_TESTED")
        for route in gate.ROUTES:
            for field in fields:
                for state in states:
                    with self.subTest(route=route,field=field,state=state):
                        d=ready_fixture()
                        next(r for r in d["routes"] if r["route"]==route)[field]=state
                        out=gate.decide(d)
                        self.assertEqual(out["contract"],"PASS")
                        self.assertEqual(out["logical_gate"],"BLOCKED")
                        self.assertFalse(out["execution_allowed"])
                        self.assertEqual(out["exclusive_route"],"UNKNOWN")

    def test_every_condition_nonpass_blocks(self):
        for name in gate.CONDITIONS:
            for state in ("UNKNOWN","FAIL","BLOCKED","NOT_TESTED"):
                with self.subTest(name=name,state=state):
                    d=ready_fixture()
                    d["conditions"][name]={"status":state,"evidence":[]}
                    out=gate.decide(d)
                    self.assertEqual(out["logical_gate"],"BLOCKED")
                    self.assertFalse(out["execution_allowed"])

    def test_preparation_mode_cannot_claim_real_pass(self):
        d=ready_fixture();d["mode"]="preparation"
        result=gate.decide(d)
        self.assertEqual(result["contract"],"FAIL")
        self.assertEqual(result["logical_gate"],"BLOCKED")
        self.assertFalse(result["execution_allowed"])

if __name__=="__main__": unittest.main()
