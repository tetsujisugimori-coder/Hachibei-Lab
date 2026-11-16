"""Synthetic-only negative controls; real identifiers must never be used here."""
import copy, hashlib, unittest
from preflight import evaluate, SURFACES, SCHEMA

CANARY="SYNTHETIC-H04-45-NEVER-REAL"
LOCATOR="synthetic://not-a-real-place/case45"

def fixture():
    return dict(schema=SCHEMA,mode="synthetic",canary=CANARY,locator=LOCATOR,
                captures={k:{"status":"CAPTURED","text":"harmless"} for k in SURFACES})

class PreflightTests(unittest.TestCase):
    def test_clean_does_not_prove_isolation(self):
        r=evaluate(fixture())
        self.assertEqual(r["contract"],"PASS")
        self.assertEqual(r["exposure"],"NOT_DETECTED_IN_SUPPLIED_SYNTHETIC_CAPTURES")
        self.assertEqual(r["isolation"],"UNKNOWN")
        self.assertFalse(r["execution_allowed"])
        self.assertEqual(r["checked_surfaces"],8)

    def test_all_surfaces_detect_raw(self):
        for name in SURFACES:
            with self.subTest(name=name):
                d=fixture();d["captures"][name]["text"]=CANARY
                r=evaluate(d)
                self.assertEqual(r["findings"],[{"surface":name,"kind":"body"}])
                self.assertFalse(r["execution_allowed"])

    def test_each_marker_is_detected(self):
        marks={"body":CANARY,"digest":hashlib.sha256(CANARY.encode()).hexdigest(),"locator":LOCATOR}
        for kind,marker in marks.items():
            with self.subTest(kind=kind):
                d=fixture();d["captures"]["b0_prompt"]["text"]=marker
                self.assertEqual(evaluate(d)["findings"],[{"surface":"b0_prompt","kind":kind}])

    def test_missing_capture_never_proves_exclusion(self):
        for name in SURFACES:
            with self.subTest(name=name):
                d=fixture();d["captures"][name]={"status":"UNKNOWN","text":""}
                r=evaluate(d)
                self.assertEqual(r["isolation"],"UNKNOWN")
                self.assertEqual(r["missing_surfaces"],[name])
                self.assertFalse(r["execution_allowed"])

    def test_invalid_inputs_fail_closed(self):
        mutations=[
            lambda d:d.update(mode="real"),
            lambda d:d.update(mode="preparation"),
            lambda d:d.pop("captures"),
            lambda d:d["captures"].pop("memory"),
            lambda d:d["captures"].update(unexpected={"status":"CAPTURED","text":""}),
            lambda d:d["captures"]["search"].update(status="PASS"),
            lambda d:d["captures"]["space"].update(text=42),
            lambda d:d["captures"]["memory"].update(status="UNKNOWN",text=CANARY),
            lambda d:d.update(canary="ACTUAL-SECRET"),
            lambda d:d.update(canary="SYNTHETIC-BUT-NOT-APPROVED"),
            lambda d:d.update(locator="synthetic://different-place"),
            lambda d:d.update(locator="https://example.com/private"),
            lambda d:d.update(captures=False),
        ]
        for index,change in enumerate(mutations):
            with self.subTest(case=index):
                d=fixture();change(d);r=evaluate(d)
                self.assertEqual(r["contract"],"FAIL")
                self.assertEqual(r["isolation"],"UNKNOWN")
                self.assertFalse(r["execution_allowed"])

    def test_no_secret_value_in_results(self):
        d=fixture();d["captures"]["public_git"]["text"]=CANARY+LOCATOR
        r=evaluate(d)
        self.assertNotIn(CANARY,str(r))
        self.assertNotIn(LOCATOR,str(r))
        self.assertEqual({x["kind"] for x in r["findings"]},{"body","locator"})

if __name__=="__main__":
    unittest.main()
