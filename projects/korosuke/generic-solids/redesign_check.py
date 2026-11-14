"""Empirical before/after validation; caller owns private-data handling.

One policy and one explicit pose list are applied to both assemblies. Protected
material regions are necessary geometric checks, NOT strength/assembly proofs.
"""
from dataclasses import asdict
from hashlib import sha256
from itertools import combinations
import math
from solid_check import Policy, measure_pair, shape_record, transformed


def compare_redesign(before, after, *, targets, protected, poses, policy=Policy()):
    result = {'status': 'UNRESOLVED', 'continuous_motion': 'NOT_PROVEN',
              'physical_safety': 'NOT_TESTED', 'support_strength': 'NOT_TESTED',
              'targets': [], 'neighbors': [], 'parts': {}, 'errors': []}
    try:
        policy.validate()
        if policy.required_clearance_mm is None:
            raise ValueError('explicit provisional or justified clearance required')
        if not before or set(before) != set(after) or len(before) < 2:
            raise ValueError('same nonempty part inventory required')
        if any(not isinstance(k, str) or not k for k in before):
            raise ValueError('nonempty string part IDs required')
        pairs = set(combinations(sorted(before), 2))
        targets = {tuple(sorted(p)) for p in targets}
        if not targets or not targets <= pairs:
            raise ValueError('target pairs must exist')
        changed = set()
        for name in sorted(before):
            a, b = before[name], after[name]
            ar, br = shape_record(a), shape_record(b)
            if ar['solids'] != 1 or br['solids'] != 1:
                raise ValueError('each part must remain one connected solid')
            # Symmetric difference detects actual world-space geometry changes.
            delta = a.cut(b).Volume + b.cut(a).Volume
            if not math.isfinite(delta) or delta < 0:
                raise ValueError('invalid shape difference')
            if delta > 0:
                changed.add(name)
            result['parts'][name] = {'before': ar, 'after': br,
                'symmetric_difference_mm3': delta,
                'before_brep_sha256': sha256(a.exportBrepToString().encode()).hexdigest(),
                'after_brep_sha256': sha256(b.exportBrepToString().encode()).hexdigest()}
        if not changed or any(not changed.intersection(p) for p in targets):
            raise ValueError('each target requires a real geometry change')
        if not changed <= set(protected):
            raise ValueError('each changed part requires protected material regions')
        for name, regions in protected.items():
            if name not in before or not regions:
                raise ValueError('nonempty protected regions required for existing parts')
            for region in regions:
                shape_record(region)
                for assembly in (before, after):
                    lost = region.cut(assembly[name])
                    if not lost.isNull() and (not lost.isValid() or lost.Volume > 0):
                        raise ValueError('protected material removed or invalid')
        if not isinstance(poses, list) or not poses or poses[0] != {}:
            raise ValueError('poses must begin with explicit initial identity pose {}')
        for pose in poses:
            if not isinstance(pose, dict) or not set(pose) <= set(before):
                raise ValueError('pose refers to unknown parts')
        result['policy'] = asdict(policy)
        result['sample_count'] = len(poses)
        for index, pose in enumerate(poses):
            assemblies = [{name: transformed(shape, **pose.get(name, {}))
                           for name, shape in assembly.items()} for assembly in (before, after)]
            for pair in sorted(pairs):
                values = [measure_pair(assembly[pair[0]], assembly[pair[1]], policy=policy)
                          for assembly in assemblies]
                old, new = values
                entry = {'pose_index': index, 'pair': list(pair), 'before': old, 'after': new}
                result['targets' if pair in targets else 'neighbors'].append(entry)
        all_entries = result['targets'] + result['neighbors']
        if any(v['status'] == 'UNRESOLVED' for e in all_entries for v in (e['before'], e['after'])):
            raise ValueError('unresolved pair measurement')
        initial = [e for e in result['targets'] if e['pose_index'] == 0]
        result['initial_targets'] = 'PASS' if all(
            e['before']['intersection_volume_mm3'] > 0 and
            e['after']['manufacturing_clearance'] == 'MEASURED_AT_OR_ABOVE_REQUIREMENT'
            for e in initial) else 'FAIL'
        if any(e['after']['manufacturing_clearance'] == 'UNRESOLVED' for e in initial):
            result['initial_targets'] = 'UNRESOLVED'
        result['sampled_targets'] = 'PASS' if all(
            e['after']['manufacturing_clearance'] == 'MEASURED_AT_OR_ABOVE_REQUIREMENT'
            for e in result['targets']) else 'FAIL'
        if any(e['after']['manufacturing_clearance'] == 'UNRESOLVED' for e in result['targets']):
            result['sampled_targets'] = 'UNRESOLVED'
        # Compare every other pair, including unchanged parts and existing overlaps.
        result['new_neighbor_overlap'] = 'FAIL' if any(
            e['before']['intersection_volume_mm3'] == 0 and e['after']['intersection_volume_mm3'] > 0
            for e in result['neighbors']) else 'PASS'
        result['neighbor_clearance'] = 'PASS' if all(
            e['after']['manufacturing_clearance'] == 'MEASURED_AT_OR_ABOVE_REQUIREMENT'
            for e in result['neighbors']) else 'UNRESOLVED'
        result['status'] = 'PASS' if all(result[k] == 'PASS' for k in (
            'initial_targets', 'sampled_targets', 'new_neighbor_overlap', 'neighbor_clearance')) else 'FAIL'
        if any(e['after']['manufacturing_clearance'] == 'UNRESOLVED' for e in all_entries):
            result['status'] = 'UNRESOLVED'
    except Exception as exc:
        result['status'] = 'UNRESOLVED'
        result['errors'].append(type(exc).__name__ + ': ' + str(exc))
    return result
