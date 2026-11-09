"""OCC BRep measurements at explicit poses. Never a continuous-clearance proof."""
from __future__ import annotations
import math
from dataclasses import dataclass, asdict
import FreeCAD as App
import Part


@dataclass(frozen=True)
class Policy:
    linear_tolerance_mm: float = 1e-6
    micro_volume_mm3: float = 1e-6
    required_clearance_mm: float | None = None

    def validate(self):
        for name, x in asdict(self).items():
            if x is None and name == 'required_clearance_mm':
                continue
            if type(x) not in (int, float) or not math.isfinite(x) or x < 0:
                raise ValueError('nonnegative finite policy required: ' + name)


def finite_vector(values, name):
    if len(values) != 3 or any(type(x) not in (int, float) or not math.isfinite(x) for x in values):
        raise ValueError('finite three-vector required: ' + name)
    return App.Vector(*values)


def transformed(shape, *, pivot=(0, 0, 0), axis=(0, 0, 1), degrees=0, translation=(0, 0, 0)):
    """World-space axis/pivot, degree rotation then mm translation; copies input."""
    p = finite_vector(pivot, 'pivot')
    a = finite_vector(axis, 'axis')
    t = finite_vector(translation, 'translation')
    if a.Length == 0 or not math.isfinite(a.Length):
        raise ValueError('nonzero finite rotation axis required')
    if type(degrees) not in (int, float) or not math.isfinite(degrees) or abs(degrees) > 360:
        raise ValueError('pose rotation must be finite within [-360,360] degrees')
    out = shape.copy()
    out.rotate(p, a, degrees)
    out.translate(t)
    return out


def shape_record(shape):
    if shape.isNull():
        raise ValueError('null shape')
    def only_solids(s):
        if s.ShapeType == 'Solid':
            return True
        return s.ShapeType == 'Compound' and bool(s.childShapes()) and all(only_solids(c) for c in s.childShapes())
    if not only_solids(shape) or not shape.isValid() or not shape.Solids:
        raise ValueError('non-null valid solid or compound of solids required')
    # Reject face/wire/edge appendages; a compound may contain several solids.
    if sum(len(s.Faces) for s in shape.Solids) != len(shape.Faces):
        raise ValueError('loose or shared faces are not supported')
    if sum(len(s.Edges) for s in shape.Solids) != len(shape.Edges):
        raise ValueError('loose or shared edges are not supported')
    if any(not s.isClosed() or s.Volume <= 0 for s in shape.Solids):
        raise ValueError('closed positive-volume solids required')
    box = shape.BoundBox
    vals = [shape.Volume, shape.Area, shape.getTolerance(1), box.XMin, box.YMin, box.ZMin,
            box.XMax, box.YMax, box.ZMax]
    if any(not math.isfinite(x) for x in vals) or vals[0] <= 0 or vals[2] < 0:
        raise ValueError('invalid shape measurement')
    return {'solids': len(shape.Solids), 'volume_mm3': vals[0], 'max_brep_tolerance_mm': vals[2],
            'bbox_mm': vals[3:], 'placement': list(shape.Placement.Matrix.A)}


def measure_pair(a, b, *, units_a='mm', units_b='mm', policy=Policy()):
    """Direct OCC boolean and distance, no AABB early-clear or mesh substitution.

    Result is an empirical kernel measurement, NOT an outward-rounded bound.
    Tiny positive boolean volumes are retained, never rounded into separation.
    """
    out = {'status': 'UNRESOLVED', 'continuous_motion': 'NOT_PROVEN', 'method': 'OCC_BREP',
           'unit': 'mm', 'volume_unit': 'mm3', 'physical_safety': 'NOT_TESTED',
           'manufacturing_clearance': 'UNRESOLVED'}
    try:
        policy.validate()
        if units_a != 'mm' or units_b != 'mm':
            raise ValueError('explicit matching mm units required; no implicit conversion')
        ar, br = shape_record(a), shape_record(b)
        linear = max(policy.linear_tolerance_mm, ar['max_brep_tolerance_mm'], br['max_brep_tolerance_mm'])
        out.update(a=ar, b=br, policy=asdict(policy), effective_linear_tolerance_mm=linear)
        common = a.common(b)
        distance, points, _ = a.distToShape(b)
        volume = common.Volume
        if not all(math.isfinite(x) and x >= 0 for x in [distance, volume]):
            raise ValueError('negative or nonfinite kernel result')
        if not common.isNull() and not common.isValid():
            raise ValueError('invalid boolean output')
        if volume > min(ar['volume_mm3'], br['volume_mm3']) + max(policy.micro_volume_mm3, 1e-9 * min(ar['volume_mm3'], br['volume_mm3'])):
            raise ValueError('intersection volume exceeds input volume')
        if volume > 0 and distance > linear:
            raise ValueError('contradictory positive intersection and positive separation')
        out.update(intersection_volume_mm3=volume, minimum_distance_mm=distance,
                   nearest_points_mm=[[[v.x, v.y, v.z] for v in pair] for pair in points[:8]])
        if volume > 0:
            box = common.BoundBox
            out['intersection_bbox_mm'] = [box.XMin, box.YMin, box.ZMin, box.XMax, box.YMax, box.ZMax]
            out['intersection_center_mm'] = [sum(getattr(s.CenterOfMass, c)*s.Volume for s in common.Solids)/volume for c in ('x','y','z')]
            out['status'] = 'MICRO_OVERLAP_REPORTED' if volume <= policy.micro_volume_mm3 else 'VOLUME_OVERLAP'
        elif distance <= linear:
            out['status'] = 'CONTACT_OR_WITHIN_TOLERANCE'
        else:
            out['status'] = 'SEPARATED_AT_POSE'
        out['manufacturing_clearance'] = clearance_result(volume, distance, linear, policy.required_clearance_mm)
        out['numerical_guarantee'] = 'NO_CERTIFIED_BOUND; kernel tolerance is not a rigorous error bound'
    except Exception as exc:
        out['status'] = 'UNRESOLVED'
        out['manufacturing_clearance'] = 'UNRESOLVED'
        out['error'] = type(exc).__name__ + ': ' + str(exc)
    return out


def clearance_result(volume, distance, tolerance, required):
    """Conservative reporting band, not a certified OCC error enclosure.

    Intersection always outranks the unsigned minimum distance. Contact does
    not establish manufacturing clearance, even for a zero requirement.
    """
    if any(type(x) not in (int, float) or not math.isfinite(x) or x < 0
           for x in (volume, distance, tolerance)):
        raise ValueError('invalid clearance measurements')
    if required is not None and (type(required) not in (int, float) or
                                not math.isfinite(required) or required < 0):
        raise ValueError('invalid clearance requirement')
    if volume > 0 and distance > tolerance:
        raise ValueError('contradictory intersection and separation')
    if required is None:
        return 'NOT_SPECIFIED'
    if volume > 0:
        return 'INTERFERENCE'
    if distance <= tolerance:
        return 'CONTACT_OR_WITHIN_TOLERANCE'
    # Compare rounded endpoints outwards. Near the requirement, do not promote
    # an uncertain boundary to a successful clearance classification.
    lower = math.nextafter(distance - tolerance, -math.inf)
    upper = math.nextafter(distance + tolerance, math.inf)
    if lower > required:
        return 'MEASURED_AT_OR_ABOVE_REQUIREMENT'
    if upper < required:
        return 'MEASURED_BELOW_REQUIREMENT'
    return 'UNRESOLVED'


def fourbar_pose(input_center, output_center, crank, coupler, rocker, input_degrees, branch=1):
    """Planar circle intersection in x,z; returns points and closure residuals.

    No clipping of impossible square roots; inconsistent closure is rejected.
    Branch +1 selects the clockwise perpendicular of input->output vector.
    """
    values = [*input_center, *output_center, crank, coupler, rocker, input_degrees]
    if len(input_center) != 2 or len(output_center) != 2 or any(type(x) not in (int,float) or not math.isfinite(x) for x in values):
        raise ValueError('finite planar input required')
    if min(crank,coupler,rocker) <= 0 or abs(input_degrees) > 360 or branch not in (-1,1):
        raise ValueError('invalid linkage lengths, angle, or branch')
    t=math.radians(input_degrees)
    p=(input_center[0]+crank*math.cos(t), input_center[1]+crank*math.sin(t))
    dx,dz=output_center[0]-p[0],output_center[1]-p[1]
    d=math.hypot(dx,dz)
    if d == 0 or d > coupler+rocker or d < abs(coupler-rocker):
        raise ValueError('no unique circle closure')
    along=(coupler*coupler-rocker*rocker+d*d)/(2*d)
    height2=coupler*coupler-along*along
    if height2 <= 0:
        raise ValueError('toggle or unresolved circle closure')
    h=math.sqrt(height2)
    q=(p[0]+along*dx/d+branch*h*dz/d, p[1]+along*dz/d-branch*h*dx/d)
    residual=max(abs(math.dist(p,q)-coupler),abs(math.dist(output_center,q)-rocker))
    if not math.isfinite(residual) or residual > 1e-9*max(coupler,rocker,1):
        raise ValueError('closure residual exceeded')
    return {'input_pin':p, 'output_pin':q, 'output_degrees':math.degrees(math.atan2(q[1]-output_center[1],q[0]-output_center[0])), 'closure_residual_mm':residual}
