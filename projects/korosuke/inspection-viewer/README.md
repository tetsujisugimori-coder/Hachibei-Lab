# Solid Inspection Studio

Dependency-free, local-input 3D triangle viewer for pose-bound solid measurement records. No upload, remote resources, storage, analytics or animation loops. It does not calculate intersections: the source's FreeCAD/OCC evidence and a display mesh are separate. Drawing references are inert text labels, not embedded CAD drawings. Canvas uses a painter-sorted orthographic projection, so complex transparency/occlusion is approximate; inspect the CAD for precision. No WebGL requirement. Keyboard camera, per-part selection, sample controls and textual results remain available.

Serve this directory with a local HTTP server (ES modules require an HTTP origin), then open index.html. Import a local JSON payload. The default is an original analytic box fixture, not the private character or a FreeCAD measurement. Every supplied angle is a measured sample; any other exact numeric angle displays UNKNOWN and clears geometry/results. Angle labels in the synthetic fixture are identifiers, not proof of rotary mechanics.

## v1 input

- schema_version: 1; units: `mm`
- source: `{sha256: 64-hex-string, description: string}`. The source hash binds evidence, not the import file's bytes; the viewer does not authenticate provenance.
- parts: `[{id, name, role, category: 'exterior'|'internal', drawings: [text]}]`
- poses: `[{id, angle_deg, geometry, measurements}]`
- geometry: `[{part_id, vertices: [[x,y,z]], triangles: [[i,j,k]]}]`. All parts at every pose, world-space coordinates. Triangles are display tessellation, not BRep solids.
- measurements: `[{a,b,status,volume_mm3,distance_mm,tolerance_mm,evidence,intersection}]`
- status: CLEAR / INTERFERENCE / CONTACT / UNRESOLVED. Null measurements only in UNRESOLVED; positive volume cannot be CLEAR even at zero required gap. CLEAR requires zero volume and distance larger than tolerance. Manufacturing clearance is not certified.
- evidence: `{method:'OCC_BREP'|'ANALYTIC_NEUTRAL_FIXTURE',source_sha256,pose_id,angle_deg}` exactly matching source and containing pose.
- intersection: null, or `{vertices,triangles}` from the actual common shape. Missing mesh is explicitly shown, not fabricated.

File size limit: 50 MiB. Vertex coordinates must be finite and within ±1e9 mm; total part and intersection triangles are capped at 2,000,000. These practical display limits prevent nonfinite projected bounds and protect basic processing budgets. Parsed JSON is validated before replacing the model. A failed import clears displayed measurements and pose, retaining an explicit error; it never reports the old result as the new file's result. Newest-file generation checks prevent delayed reads from replacing Reset or a newer input. Text is inserted using textContent. No content is interpreted as HTML or executable URLs.

## Checks

`node --test model.test.mjs` checks the input/pose contract and failure controls.

`node browser-check.cjs` runs Chromium/WebKit × four widths × two motion preferences with screenshots, traces and JSON. Playwright is a test-only external dependency, not viewer runtime. `PLAYWRIGHT_MODULE`, `CHROMIUM_EXECUTABLE`, `WEBKIT_EXECUTABLE` allow installed environment paths. `VIEWER_INPUT` optionally supplies a local FreeCAD payload; `VIEWER_EVIDENCE` selects evidence output. The runner closes server, contexts and browser after failure. Original failed results are kept. Native device, VoiceOver, physical input, mechanical safety and interval-continuous collision freedom remain NOT_TESTED/UNKNOWN.

Private originals and actual character geometry must remain outside the public repository. The importer deliberately does not copy selected files into this directory.

`BROWSERS=webkit` (or `chromium`) is a targeted eight-condition debug run, never a full-16 result. A browser launch failure records eight NOT_TESTED results with the exact launch error and continues the other browser. The process exits nonzero unless every requested condition passes. Dense datasets can exceed browser/process resources despite passing the structural schema; a target crash is a failed run, not a geometry verdict. Tessellation may be reduced upstream for display with its tolerance recorded, without altering solid measurements.
