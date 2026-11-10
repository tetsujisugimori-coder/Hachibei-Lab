const statuses = new Set(['CLEAR','INTERFERENCE','CONTACT','UNRESOLVED']);
const finite = x => typeof x === 'number' && Number.isFinite(x);
const assert = (ok, message) => { if (!ok) throw new Error(message); };
const label = x => typeof x === 'string' && x.length > 0 && x.length <= 1000;
const hash = x => typeof x === 'string' && /^[a-f0-9]{64}$/i.test(x);
function mesh(m, path) {
  assert(m && Array.isArray(m.vertices) && m.vertices.length >= 3 && m.vertices.length <= 200000, `${path}: invalid vertices`);
  assert(m.vertices.every(v => Array.isArray(v) && v.length === 3 && v.every(x => finite(x) && Math.abs(x) <= 1e9)), `${path}: nonfinite vertex`);
  assert(Array.isArray(m.triangles) && m.triangles.length > 0 && m.triangles.length <= 400000, `${path}: invalid triangles`);
  assert(m.triangles.every(t => Array.isArray(t) && t.length === 3 && new Set(t).size === 3 && t.every(i => Number.isInteger(i) && i >= 0 && i < m.vertices.length)), `${path}: invalid index`);
}
export function validateModel(m) {
  assert(m && m.schema_version === 1 && m.units === 'mm', 'schema v1 and mm units required');
  assert(m.source && hash(m.source.sha256) && label(m.source.description), 'source identity required');
  assert(Array.isArray(m.parts) && m.parts.length > 0 && m.parts.length <= 500, 'invalid parts');
  const ids = new Set();
  for (const p of m.parts) {
    assert(p && label(p.id) && !ids.has(p.id) && label(p.name) && label(p.role), 'invalid/duplicate part ID or description');
    assert(['exterior','internal'].includes(p.category), 'invalid part category');
    assert(Array.isArray(p.drawings) && p.drawings.every(label), 'drawing references must be labels'); ids.add(p.id);
  }
  assert(Array.isArray(m.poses) && m.poses.length > 0 && m.poses.length <= 1000, 'invalid poses');
  const poseIds = new Set(), angles = new Set(); let totalTriangles = 0;
  for (const p of m.poses) {
    assert(p && label(p.id) && !poseIds.has(p.id) && finite(p.angle_deg) && !angles.has(p.angle_deg), 'duplicate/invalid pose ID or angle');
    poseIds.add(p.id); angles.add(p.angle_deg);
    assert(Array.isArray(p.geometry) && p.geometry.length === ids.size, 'pose geometry must include every part');
    const geomIds = new Set();
    for (const g of p.geometry) { assert(ids.has(g.part_id) && !geomIds.has(g.part_id), 'unknown/duplicate geometry ID'); geomIds.add(g.part_id); mesh(g,p.id); totalTriangles += g.triangles.length; }
    assert(totalTriangles <= 2000000, 'model triangle budget exceeded');
    assert(Array.isArray(p.measurements), 'measurements missing');
    const pairs = new Set();
    for (const r of p.measurements) {
      assert(r && ids.has(r.a) && ids.has(r.b) && r.a !== r.b, 'invalid measured pair');
      const key = [r.a,r.b].sort().join('\u0000'); assert(!pairs.has(key), 'duplicate measured pair'); pairs.add(key);
      assert(statuses.has(r.status) && finite(r.tolerance_mm) && r.tolerance_mm >= 0, 'invalid result status/tolerance');
      assert(r.evidence && ['OCC_BREP','ANALYTIC_NEUTRAL_FIXTURE'].includes(r.evidence.method) && r.evidence.source_sha256 === m.source.sha256 && r.evidence.pose_id === p.id && r.evidence.angle_deg === p.angle_deg, 'evidence/pose/source mismatch');
      for (const f of ['volume_mm3','distance_mm']) assert(r[f] === null || (finite(r[f]) && r[f] >= 0), 'invalid measurement number');
      if (r.status !== 'UNRESOLVED') {
        assert(finite(r.volume_mm3) && finite(r.distance_mm), 'resolved result requires measurements');
        if (r.status === 'INTERFERENCE') assert(r.volume_mm3 > 0 && r.distance_mm <= r.tolerance_mm, 'interference must have positive volume and near-zero distance');
        if (r.status === 'CLEAR') assert(r.volume_mm3 === 0 && r.distance_mm > r.tolerance_mm, 'CLEAR contradicts volume/distance');
        if (r.status === 'CONTACT') assert(r.volume_mm3 === 0 && r.distance_mm <= r.tolerance_mm, 'CONTACT contradicts volume/distance');
      }
      assert(r.intersection === null || typeof r.intersection === 'object', 'intersection must be mesh or null');
      if (r.intersection !== null) { mesh(r.intersection, 'intersection'); totalTriangles += r.intersection.triangles.length; assert(totalTriangles <= 2000000, 'model triangle budget exceeded'); assert(r.volume_mm3 > 0, 'intersection without positive volume'); }
    }
  }
  return m;
}
export function selectPose(model, angle) { return finite(angle) ? model.poses.find(p => p.angle_deg === angle) ?? null : null; }
export function pairSummary(pose) { return pose ? Object.fromEntries([...statuses].map(s => [s,pose.measurements.filter(r => r.status === s).length])) : null; }
