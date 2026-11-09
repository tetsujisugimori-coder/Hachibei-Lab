"""Original neutral block fixture, unrelated to any character geometry.

A central relief opens clearance around a moving block while retaining two
mounting lands and the base web. Dimensions are arbitrary test parameters, not
manufacturing recommendations. No load/fastener/wiring assessment is implied.
"""
import json
import pathlib
import sys
import FreeCAD as App
import Part
from solid_check import Policy
from redesign_check import compare_redesign


def fixture(relief_depth=4.0):
    bracket = Part.makeBox(12, 8, 8)
    tool = Part.makeBox(6, 10, relief_depth, App.Vector(3, -1, 8-relief_depth))
    before = {'bracket': bracket, 'slider': Part.makeBox(4, 4, 2, App.Vector(4, 2, 6)),
              'neighbor': Part.makeBox(2, 2, 2, App.Vector(15, 0, 0))}
    after = dict(before, bracket=bracket.cut(tool))
    protected = {'bracket': [Part.makeBox(12, 8, 2), Part.makeBox(2, 8, 8),
                             Part.makeBox(2, 8, 8, App.Vector(10, 0, 0))]}
    return before, after, dict(targets=[('bracket','slider')], protected=protected,
        poses=[{}, {'slider': {'translation': (0, 0, 0.5)}},
               {'slider': {'translation': (0, 0, -0.5)}}],
        policy=Policy(required_clearance_mm=0.25))


def main(folder):
    folder = pathlib.Path(folder); folder.mkdir(parents=True, exist_ok=True)
    before, after, kwargs = fixture()
    report = compare_redesign(before, after, **kwargs)
    report['fixture_only'] = True
    report['FreeCAD'] = list(App.Version())
    report['OCC'] = Part.OCC_VERSION
    # Save/reload original neutral solids only; verify volume and BRep difference.
    reloads = {}
    for label, assembly in [('before', before), ('after', after)]:
        doc = App.newDocument('neutral_'+label)
        for name, shape in assembly.items():
            obj = doc.addObject('Part::Feature', name); obj.Shape = shape
        doc.recompute(); path = folder / (label+'.FCStd'); doc.saveAs(str(path))
        Part.export(doc.Objects, str(folder / (label+'.step')))
        App.closeDocument(doc.Name)
        loaded = App.openDocument(str(path))
        fc_ok = all(loaded.getObject(n).Shape.isValid() and
                    abs(s.Volume-loaded.getObject(n).Shape.Volume) < 1e-8 and
                    s.cut(loaded.getObject(n).Shape).Volume + loaded.getObject(n).Shape.cut(s).Volume < 1e-8
                    for n,s in assembly.items())
        App.closeDocument(loaded.Name)
        step = Part.read(str(folder / (label+'.step')))
        expected = Part.makeCompound(list(assembly.values()))
        step_ok = step.isValid() and len(step.Solids) == len(assembly) and abs(step.Volume-expected.Volume) < 1e-8 and step.cut(expected).Volume+expected.cut(step).Volume < 1e-8
        reloads[label] = {'FCStd': fc_ok, 'STEP': step_ok}
    report['neutral_roundtrip'] = reloads
    (folder/'redesign.json').write_text(json.dumps(report, indent=2)+'\n')
    if report['status'] != 'PASS' or not all(all(r.values()) for r in reloads.values()):
        raise SystemExit(1)


if __name__ == '__main__':
    main(sys.argv[1])
