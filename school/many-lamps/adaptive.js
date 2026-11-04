// W-Ex11-X4 Amendment 1 — the adaptive mesh. Pure functions; the page owns the state.
// Each of the 26 base 1 m patches is a binary tree: node (b, L, i) covers [i/2^L, (i+1)/2^L] of base b, levels 0–4
// (level 4 = 6.25 cm, the finest uniform detent). A mesh is the set of split nodes; its leaves are the patches.
(function (root) {
  'use strict';
  const BASE = (root.RoomModel || require('./room-model.js')).PATCHES, MAXL = 4;
  const JUMP = 2;            // (b) a neighbour pair whose settled density differs by more than ×2 marks a field edge
  const JUMP_L = 2;          //     field-edge splits refine to 25 cm; lasers and cone edges (geometric) go to 6.25 cm
  const HOLD = 4;            // hysteresis: a split stays until it has gone HOLD scene changes without being needed
  const key = (b, L, i) => b + '|' + L + '|' + i;

  // Where a boundary point sits: base patch and fraction t ∈ [0, 1) along it (in walk direction).
  function locate(p) {
    let best = null;
    BASE.forEach((P, b) => { const dx = P.b[0] - P.a[0], dy = P.b[1] - P.a[1], t = ((p[0] - P.a[0]) * dx + (p[1] - P.a[1]) * dy) / (dx * dx + dy * dy);
      const off = Math.abs((p[0] - P.a[0]) * dy - (p[1] - P.a[1]) * dx);
      if (t >= -1e-9 && t < 1 - 1e-12 && off < 1e-6 && !best) best = { b, t: Math.max(0, t) }; });
    return best;
  }
  // All ancestors of the finest node holding a point: splitting them puts that point in a 6.25 cm leaf.
  function pathKeys(p) { const o = locate(p); if (!o) return [];
    const ks = []; for (let L = 0; L < MAXL; L++) ks.push(key(o.b, L, Math.floor(o.t * 2 ** L))); return ks; }

  function leaves(split) {
    const out = [];
    BASE.forEach((P, b) => { (function walk(L, i) {
      if (L < MAXL && split.has(key(b, L, i))) { walk(L + 1, 2 * i); walk(L + 1, 2 * i + 1); return; }
      const t0 = i / 2 ** L, t1 = (i + 1) / 2 ** L, at = t => [P.a[0] + (P.b[0] - P.a[0]) * t, P.a[1] + (P.b[1] - P.a[1]) * t];
      out.push({ a: at(t0), b: at(t1), s: P.s, base: b, level: L, idx: i, u0: b + t0, u1: b + t1 });
    })(0, 0); });
    return out;
  }

  // Geometric needs: every laser's hit point, every spotlight's two cone-edge hit points.
  function geometricKeys(lamps, LM) {
    const ks = [];
    for (const L of lamps) {
      if (L.type === 'laser') ks.push(...pathKeys(LM.beamEnd(L)));
      if (L.type === 'spotlight') for (const s of [-1, 1]) ks.push(...pathKeys(LM.beamEnd({ pos: L.pos, aim: L.aim + s * LM.SPOT_HALF })));
    }
    return ks;
  }
  // Field-edge needs from the settled light on the current mesh: luminance density per leaf, compared with the next leaf
  // on the same surface. Both leaves of a jumping pair split (unless already finest), and their ancestors are held.
  function jumpKeys(mesh, settled) {
    const n = mesh.length, dens = mesh.map((p, j) => (0.2126 * settled[0][j] + 0.7152 * settled[1][j] + 0.0722 * settled[2][j]) / (p.u1 - p.u0)), ks = [];
    const hold = p => { for (let L = 0; L <= Math.min(p.level, JUMP_L - 1); L++) ks.push(key(p.base, L, p.idx >> (p.level - L))); };
    for (let j = 0; j < n; j++) { const k = (j + 1) % n, p = mesh[j], q = mesh[k]; if (p.s !== q.s) continue;
      const lo = Math.min(dens[j], dens[k]), hi = Math.max(dens[j], dens[k]);
      if (hi > 1e-9 && (lo <= 0 || hi / lo > JUMP)) { hold(p); hold(q); } }
    return ks;
  }

  // Density-preserving transfer of a light vector from one mesh to another (warm start survives a re-mesh).
  function transfer(xOld, from, to) {
    return to.map(q => { let s = 0; for (let j = 0; j < from.length; j++) { const p = from[j]; if (p.base !== q.base) continue;
      const o = Math.min(p.u1, q.u1) - Math.max(p.u0, q.u0); if (o > 0) s += o * xOld[j] / (p.u1 - p.u0); } return s; });
  }

  const api = { MAXL, JUMP, HOLD, key, locate, pathKeys, leaves, geometricKeys, jumpKeys, transfer };
  if (typeof module !== 'undefined') module.exports = api; else root.Adaptive = api;
})(typeof window !== 'undefined' ? window : globalThis);
// The controller: holds the split set with its hysteresis clock, and rebuilds the model only when the mesh changes.
(function (root) {
  'use strict';
  const A = root.Adaptive || require('./adaptive.js'), RES = root.Res || require('./res-models.js');
  function controller() {
    const need = new Map(); let gen = 0, sig = '', built = null, mesh = null;
    const meshSig = () => [...need.keys()].sort().join(',');
    function buildFor(scene) { const s = meshSig(); if (s !== sig || !built) { mesh = A.leaves(new Set(need.keys())); built = RES.build(1, mesh); sig = s; }
      const sim = built.LM.create(); sim.reset(scene); return sim; }
    // One scene change: mark geometric needs, then up to 4 passes of field-edge refinement on the settled light, then prune.
    function update(scene, lampsForGeometry, LM, passes = 4) {
      gen++;
      for (const k of A.geometricKeys(lampsForGeometry, LM)) need.set(k, gen);
      let sim = buildFor(scene);
      for (let pass = 0; pass < passes; pass++) {
        const before = meshSig(), settled = sim.channels.map(c => c.exact || c.e);
        for (const k of A.jumpKeys(mesh, settled)) need.set(k, gen);
        if (meshSig() === before) break; sim = buildFor(scene);
      }
      let pruned = false; for (const [k, g] of need) if (gen - g > A.HOLD) { need.delete(k); pruned = true; }
      if (pruned) sim = buildFor(scene);
      return { sim, mesh, built };
    }
    function clear() { need.clear(); gen = 0; sig = ''; built = null; }
    return { update, clear, get mesh() { return mesh; }, get built() { return built; }, get gen() { return gen; } };
  }
  root.Adaptive ? (root.Adaptive.controller = controller) : (module.exports.controller = controller);
})(typeof window !== 'undefined' ? window : globalThis);
