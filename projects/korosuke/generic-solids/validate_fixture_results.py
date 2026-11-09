"""Verify measurements against a separately trusted analytic case registry.

The registry must be regenerated from the fixed fixture definition, not loaded
from or inferred from the evidence being checked. Expected fields in evidence
are checked for provenance equality and are never the oracle.
"""
import math

INPUT_KEYS = ('a', 'b', 'size_a', 'size_b')

def validate(rows, trusted_cases):
    if not isinstance(trusted_cases,dict) or not trusted_cases:raise ValueError('trusted input registry required')
    if not isinstance(rows,list) or len(rows)!=len(trusted_cases):raise ValueError('missing or extra rows')
    ids=[r.get('id') for r in rows]
    if len(set(ids))!=len(ids) or set(ids)!=set(trusted_cases):raise ValueError('identity mismatch')
    for r in rows:
        case=trusted_cases[r['id']]
        for key in INPUT_KEYS:
            value=case[key]
            if len(value)!=3 or any(type(x) not in (int,float) or not math.isfinite(x) for x in value):raise ValueError('invalid trusted geometry')
            if 'size' in key and any(x<=0 for x in value):raise ValueError('invalid trusted size')
            if r.get(key)!=value:raise ValueError('input provenance mismatch')
        a,b,sa,sb=(case[key] for key in INPUT_KEYS)
        volume=math.prod(max(0,min(a[j]+sa[j],b[j]+sb[j])-max(a[j],b[j])) for j in range(3))
        distance=math.sqrt(sum(max(0,a[j]-b[j]-sb[j],b[j]-a[j]-sa[j])**2 for j in range(3)))
        for key in ['expected_volume_mm3','expected_distance_mm','measured_volume_mm3','measured_distance_mm']:
            if type(r.get(key)) not in (int,float) or not math.isfinite(r[key]) or r[key]<0:raise ValueError('invalid numeric evidence')
        if r['expected_volume_mm3']!=volume or r['expected_distance_mm']!=distance:raise ValueError('forged expectation')
        if (volume>0)!=(r['measured_volume_mm3']>0):raise ValueError('intersection sign mismatch')
        if abs(volume-r['measured_volume_mm3'])>1e-7:raise ValueError('volume mismatch')
        if abs(distance-r['measured_distance_mm'])>1e-7:raise ValueError('distance mismatch')
        expected=('VOLUME_OVERLAP' if volume>1e-6 else 'MICRO_OVERLAP_REPORTED' if volume>0 else
                  'CONTACT_OR_WITHIN_TOLERANCE' if distance<=1e-6 else 'SEPARATED_AT_POSE')
        measured=('VOLUME_OVERLAP' if r['measured_volume_mm3']>1e-6 else 'MICRO_OVERLAP_REPORTED' if r['measured_volume_mm3']>0 else
                  'CONTACT_OR_WITHIN_TOLERANCE' if r['measured_distance_mm']<=1e-6 else 'SEPARATED_AT_POSE')
        if r['status']!=expected or r['status']!=measured:raise ValueError('classification mismatch')
    return True
