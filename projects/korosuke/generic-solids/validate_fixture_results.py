"""Acceptance checker for independent analytic box fixture outputs."""
import math

def validate(rows, expected_ids):
    if not isinstance(rows,list) or len(rows)!=len(expected_ids):raise ValueError('missing or extra rows')
    ids=[r.get('id') for r in rows]
    if len(set(ids))!=len(ids) or set(ids)!=set(expected_ids):raise ValueError('identity mismatch')
    for r in rows:
        for key in ['expected_volume_mm3','expected_distance_mm','measured_volume_mm3','measured_distance_mm']:
            if type(r.get(key)) not in (int,float) or not math.isfinite(r[key]) or r[key]<0:raise ValueError('invalid numeric evidence')
        if abs(r['expected_volume_mm3']-r['measured_volume_mm3'])>1e-7:raise ValueError('volume mismatch')
        if abs(r['expected_distance_mm']-r['measured_distance_mm'])>1e-7:raise ValueError('distance mismatch')
        expected='VOLUME_OVERLAP' if r['expected_volume_mm3']>1e-6 else 'CONTACT_OR_WITHIN_TOLERANCE' if r['expected_distance_mm']<=1e-6 else 'SEPARATED_AT_POSE'
        if r['status']!=expected:raise ValueError('classification mismatch')
    return True
