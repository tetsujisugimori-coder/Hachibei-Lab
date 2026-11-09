"""Independent 100-digit geometric witnesses for candidate e5079db PR8.

The oracle never calls candidate corners(), intersects() or bbox_gap():
a high-precision point contained in both rectangles proves actual overlap.
Candidate helpers are used only to explain its (incorrect) certification.

Run: python reproduce_false_clear.py --source path/to/sweep.py --output results.json
Requires mpmath 1.3.0. All fixture geometry is public synthetic data.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
import mpmath as mp

mp.mp.dps = 100
ROOT = Path(__file__).parent
parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--regression-gate', action='store_true',
                    help='Exit 1 if any proven-overlap input is CLEAR or has an unexpected status; exit 0 only for OVERLAP, UNRESOLVED, or explicit InputError.')
args = parser.parse_args()
SOURCE = args.source
spec = importlib.util.spec_from_file_location('candidate', SOURCE)
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


def witness(raw, angle, use_corner=False):
    # mp.mpf(float) preserves each exact binary64 input. There is no favorable
    # decimal reinterpretation of the candidate's already-parsed numeric input.
    px, py = map(mp.mpf, raw['joint']['pivot_mm'])
    mx, my = map(mp.mpf, raw['moving'][0]['center_mm'])
    mw, mh = map(mp.mpf, raw['moving'][0]['size_mm'])
    fx, fy = map(mp.mpf, raw['fixed'][0]['center_mm'])
    fw, fh = map(mp.mpf, raw['fixed'][0]['size_mm'])
    # For the boundary fixture take the moving bottom-right corner; otherwise
    # take its center. Both are provably members of the closed moving rectangle.
    local_x, local_y = (mx + mw/2, my - mh/2) if use_corner else (mx, my)
    radians = mp.mpf(angle) * mp.pi / 180
    x = px + local_x * mp.cos(radians) - local_y * mp.sin(radians)
    y = py + local_x * mp.sin(radians) + local_y * mp.cos(radians)
    xmargin = fw / 2 - abs(x - fx)
    ymargin = fh / 2 - abs(y - fy)
    assert xmargin > 0 and ymargin > 0
    return {
        'angle_deg_exact': mp.nstr(mp.mpf(angle), 60),
        'moving_local_witness': [mp.nstr(local_x,60), mp.nstr(local_y,60)],
        'witness_relative_to_fixed': [mp.nstr(x-fx, 60), mp.nstr(y-fy, 60)],
        'strict_fixed_interior_margins_mm': [mp.nstr(xmargin, 60), mp.nstr(ymargin, 60)],
        'proof': 'Witness belongs to moving rectangle and lies strictly inside fixed rectangle.',
    }

def run_candidate(raw):
    try:
        result=candidate.screen(copy.deepcopy(raw))
    except candidate.InputError as exc:
        return {'status':'INPUT_REJECTED', 'exception_type':'InputError', 'message':str(exc)}
    assert len(result['pairs']) == 1
    return result['pairs'][0]


reports=[]
for name in ('huge-angle-52', 'huge-angle-trig-only', 'huge-pivot', 'moderate-tiny-boundary'):
    path=ROOT / f'{name}.json'
    raw = json.loads(path.read_text())
    result = run_candidate(raw)
    lo, hi = raw['joint']['start_deg'], raw['joint']['end_deg']
    midpoint = (float(lo) + float(hi)) / 2
    angle = hi if name.startswith('huge-angle') else midpoint
    report = {'fixture': name, 'fixture_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
              'input':raw, 'candidate': result,
              'computed_midpoint': midpoint, 'midpoint_is_strict_interior':lo<midpoint<hi,
              'independent_overlap_witness':witness(raw, angle, name=='moderate-tiny-boundary')}
    # Optional diagnostics explain the old implementation. They do not affect
    # the oracle or regression result and can disappear after a refactor.
    if result['status'] != 'INPUT_REJECTED' and all(hasattr(candidate, n) for n in ('read_input','corners','bbox_gap')):
        try:
            cfg=candidate.read_input(copy.deepcopy(raw))
            moving,fixed=cfg['moving'][0],cfg['fixed'][0]
            radius=max(math.hypot(moving['center'][0]+sx*moving['size'][0]/2,
                                  moving['center'][1]+sy*moving['size'][1]/2)
                       for sx in (-1,1) for sy in (-1,1))
            report['computed_gap_mm']=candidate.bbox_gap(candidate.corners(moving,midpoint,cfg['pivot']),candidate.corners(fixed))
            report['computed_motion_bound_mm']=radius*math.radians((hi-lo)/2)
        except Exception as exc:
            report['optional_diagnostics_unavailable']=type(exc).__name__
    with mp.workdps(160):
        second=witness(raw, angle, name=='moderate-tiny-boundary')
    report['independent_overlap_witness_at_160_digits']=second
    report['100_and_160_digit_runs_agree_to_60_significant_digits']=(second==report['independent_overlap_witness'])
    assert report['100_and_160_digit_runs_agree_to_60_significant_digits']
    normalized=copy.deepcopy(raw)
    if name.startswith('huge-angle'):
        normalized['joint']['start_deg']=lo%360
        normalized['joint']['end_deg']=lo%360+(hi-lo)
        report['equivalent_small_angle_candidate']=run_candidate(normalized)
    if name=='huge-pivot':
        normalized['joint']['pivot_mm']=[0,0]
        normalized['fixed'][0]['center_mm']=[2,0]
        report['equivalent_translated_candidate']=run_candidate(normalized)
    reports.append(report)
safe_statuses={'PROJECTED_OVERLAP','UNRESOLVED_2D','INPUT_REJECTED'}
false_clear_count=sum(v['candidate']['status']=='PROJECTED_CLEAR' for v in reports)
gate_failures=[v['fixture'] for v in reports if v['candidate']['status'] not in safe_statuses]
aggregate={'regression_gate_requested':args.regression_gate,
           'regression_gate_passed':not gate_failures,
           'regression_gate_failures':gate_failures,
           'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
           'mpmath_version':mp.__version__, 'mpmath_decimal_digits':[100,160],
           'reports':reports}
args.output.write_text(json.dumps(aggregate, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'source_sha256':aggregate['source_sha256'],
                  'fixtures_checked':len(reports),
                  'false_clear_witnesses':false_clear_count,
                  'regression_gate_passed':not gate_failures,
                  'mode':'regression_gate' if args.regression_gate else 'diagnostic_report_only',
                  'precision_agreement':all(v['100_and_160_digit_runs_agree_to_60_significant_digits'] for v in reports)}))

if args.regression_gate and gate_failures:
    sys.exit(1)
