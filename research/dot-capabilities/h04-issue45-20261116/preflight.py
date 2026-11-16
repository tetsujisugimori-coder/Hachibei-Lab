"""Issue #45: deterministic, *synthetic-only* exposure screening. No IO or access control."""
import hashlib
SCHEMA = "H04-45-synthetic/1"
SURFACES = (
    "b0_prompt", "b0_history", "memory", "space", "search",
    "shared_files", "handoff", "public_git",
)
STATES = ("CAPTURED", "UNKNOWN", "NOT_TESTED")

def _failed(reason):
    return dict(contract="FAIL", exposure="UNKNOWN", isolation="UNKNOWN",
                execution_allowed=False, findings=[], reasons=[reason])

def evaluate(value):
    """Detect literal synthetic exposures, never attest real exclusion or execution."""
    try:
        if type(value) is not dict or set(value) != {"schema","mode","canary","locator","captures"}:
            return _failed("STRUCTURE")
        if value["schema"] != SCHEMA or value["mode"] != "synthetic":
            return _failed("SYNTHETIC_ONLY")
        canary, locator = value["canary"], value["locator"]
        if (type(canary) is not str or not canary.startswith("SYNTHETIC-")
                or not 16 <= len(canary) <= 100 or type(locator) is not str
                or not locator.startswith("synthetic://") or not 12 <= len(locator) <= 200):
            return _failed("CANARY_TYPE_SCOPE")
        captures = value["captures"]
        if type(captures) is not dict or set(captures) != set(SURFACES):
            return _failed("CAPTURE_SET")
        markers = {"body": canary, "digest": hashlib.sha256(canary.encode("utf-8")).hexdigest(),
                   "locator": locator}
        findings, missing = [], []
        for name in SURFACES:
            row = captures[name]
            if type(row) is not dict or set(row) != {"status","text"}:
                return _failed("CAPTURE_STRUCTURE")
            if type(row["status"]) is not str or row["status"] not in STATES:
                return _failed("CAPTURE_STATUS")
            if type(row["text"]) is not str or len(row["text"]) > 65536:
                return _failed("CAPTURE_TEXT")
            if row["status"] != "CAPTURED":
                missing.append(name)
                if row["text"]:
                    return _failed("UNVERIFIED_CAPTURE_CONTENT")
            else:
                for marker, needle in markers.items():
                    if needle in row["text"]:
                        findings.append({"surface":name,"kind":marker})
        return dict(contract="PASS",
                    exposure="DETECTED_IN_SYNTHETIC_CAPTURE" if findings else "NOT_DETECTED_IN_SUPPLIED_SYNTHETIC_CAPTURES",
                    isolation="UNKNOWN", execution_allowed=False,
                    findings=findings, missing_surfaces=missing, checked_surfaces=len(SURFACES)-len(missing),
                    reasons=[])
    except (TypeError, ValueError, UnicodeError, RecursionError):
        return _failed("INVALID_INPUT")
