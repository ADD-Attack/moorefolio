// W-Ex11-X model — many lamps, in colour, in the W-Ex11 room.
// The room (patches, F, spectral, certificate, solve) is W-Ex11's room-model.js, copied unchanged.
// Per channel c: A_c = diag(ρ_c)·F with ρ_c = reflectivity × surface colour_c; x0 = 0, x_{k+1} = e_c + A_c x_k.
// Lamps live only in e: e_c = Σ_lamps brightness × colour_c × d, where d is the lamp's first-bounce distribution.
(function (root) {
  'use strict';
  const M = root.RoomModel || (typeof require !== 'undefined' ? require('./room-model.js') : null);
  const { N, W, H, PATCHES, FF } = M;
  const CH = ['r', 'g', 'b'];
  const TAU = 2 * Math.PI;
  const SPOT_HALF = Math.PI / 9;          // spotlight cone: 40° full width (±20° about the aim)
  const MARGIN = 0.1;                      // lamps stay at least 10 cm inside the walls
  const TYPES = ['bulb', 'spotlight', 'laser', 'panel'];

  const clampPos = p => [Math.min(W - MARGIN, Math.max(MARGIN, p[0])), Math.min(H - MARGIN, Math.max(MARGIN, p[1]))];
  const mod = (a, m) => ((a % m) + m) % m;

  // From an interior point p, the 26 patches partition the full circle of directions (the room is convex):
  // patch j owns the anticlockwise arc [α_j, α_j + φ_j]. The boundary walk is anticlockwise, so φ_j > 0.
  function arcs(p) {
    return PATCHES.map(({ a, b }) => {
      const ux = a[0] - p[0], uy = a[1] - p[1], vx = b[0] - p[0], vy = b[1] - p[1];
      return { start: Math.atan2(uy, ux), width: Math.atan2(ux * vy - uy * vx, ux * vx + uy * vy) };
    });
  }
  // Length of the overlap between arc [s, s+w] and the cone [c0, c0+cw] on the circle.
  function overlap(s, w, c0, cw) {
    const o = mod(s - c0, TAU); let t = Math.max(0, Math.min(o + w, cw) - o);
    if (o + w > TAU) t += Math.min(o + w - TAU, cw);
    return t;
  }
  // First-bounce distribution d (Σd = 1, d ≥ 0).
  //   bulb      — equal output in every direction: d_j = φ_j / 2π (every patch, from anywhere inside).
  //   spotlight — equal output across a 40° cone: d_j = (part of patch j's arc inside the cone) / 40°.
  //   laser     — one ray: d = 1 on the first patch the beam meets.
  //   panel     — W-Ex11's lamp: a glowing patch; its own light is the first bounce, d = 1 on that patch.
  function distribution(L) {
    const d = new Array(N).fill(0);
    if (L.type === 'panel') { d[L.patch] = 1; return d; }
    const A = arcs(L.pos);
    if (L.type === 'laser') {
      let hit = -1;
      for (let j = 0; j < N && hit < 0; j++) if (mod(L.aim - A[j].start, TAU) < A[j].width) hit = j;
      if (hit < 0) hit = 0;                // unreachable for interior points; a fixed fallback keeps runs deterministic
      d[hit] = 1; return d;
    }
    let raw, s = 0;
    if (L.type === 'bulb') raw = A.map(a => a.width);
    else raw = A.map(a => overlap(a.start, a.width, L.aim - SPOT_HALF, 2 * SPOT_HALF));
    for (const t of raw) s += t;
    for (let j = 0; j < N; j++) d[j] = raw[j] / s;   // normalise: Σd = 1 to round-off
    return d;
  }
  // Where a laser's beam lands (for drawing only).
  function beamEnd(L) {
    const dx = Math.cos(L.aim), dy = Math.sin(L.aim); let best = Infinity;
    if (dx > 1e-12) best = Math.min(best, (W - L.pos[0]) / dx); if (dx < -1e-12) best = Math.min(best, -L.pos[0] / dx);
    if (dy > 1e-12) best = Math.min(best, (H - L.pos[1]) / dy); if (dy < -1e-12) best = Math.min(best, -L.pos[1] / dy);
    return [L.pos[0] + dx * best, L.pos[1] + dy * best];
  }

  function normLamp(L, id) {
    const o = { id, type: TYPES.includes(L.type) ? L.type : 'bulb', color: (L.color || [1, 1, 1]).slice(0, 3),
      brightness: L.brightness == null ? 1 : L.brightness, aim: L.aim == null ? -Math.PI / 2 : L.aim, label: L.label || null };
    if (o.type === 'panel') { o.patch = L.patch == null ? 16 : L.patch; const P = PATCHES[o.patch]; o.pos = [(P.a[0] + P.b[0]) / 2, (P.a[1] + P.b[1]) / 2]; }
    else o.pos = clampPos(L.pos || [W / 2, H / 2]);
    o.d = distribution(o);
    return o;
  }

  const GREY = { floor: { refl: 0.45, color: [1, 1, 1] }, right: { refl: 0.8, color: [1, 1, 1] }, ceiling: { refl: 0.85, color: [1, 1, 1] }, left: { refl: 0.8, color: [1, 1, 1] } };

  function matAc(surf, c) { return FF.map((row, i) => { const s = surf[PATCHES[i].s], r = s.refl * s.color[c]; return row.map(f => r * f); }); }
  function emissionC(lamps, c) {
    const e = new Array(N).fill(0);
    for (const L of lamps) { const w = L.brightness * L.color[c]; for (let j = 0; j < N; j++) e[j] += w * L.d[j]; }
    return e;
  }
  function analyseChannel(A) {
    const sp = M.spectral(A), cert = M.certificate(A);
    const rowMax = A.reduce((m, r) => Math.max(m, r.reduce((s, t) => s + t, 0)), 0);
    return { A, spectral: sp, certificate: cert, maxRowSum: rowMax };
  }

  function create() {
    let surf, lamps, nextId, chans, x, k, hist;
    const roomCache = new Map();
    function roomAnalysis() {
      const key = JSON.stringify(surf);
      if (!roomCache.has(key)) { if (roomCache.size > 40) roomCache.clear(); roomCache.set(key, [0, 1, 2].map(c => analyseChannel(matAc(surf, c)))); }
      return roomCache.get(key);
    }
    function rebuild() {
      const rooms = roomAnalysis();
      chans = rooms.map((an, c) => { const e = emissionC(lamps, c); return { ...an, e, dark: e.every(t => t === 0), exact: an.spectral.below1 ? M.solve(an.A, e) : null }; });
      x = [0, 1, 2].map(() => new Array(N).fill(0)); k = 0; hist = [[], [], []];
    }
    function reset(scene) {
      const s = scene || {};
      surf = {}; for (const f of M.SURFACES) { const g = (s.surfaces && s.surfaces[f]) || GREY[f]; surf[f] = { refl: g.refl, color: g.color.slice(0, 3) }; }
      nextId = 1; lamps = (s.lamps || [{ type: 'panel', patch: 16 }]).map(L => normLamp(L, nextId++));
      rebuild();
    }
    function bounce() {
      for (let c = 0; c < 3; c++) {
        const an = chans[c], prev = x[c];
        x[c] = an.e.map((t, i) => t + M.mulVec(an.A, prev)[i]);   // same expression as W-Ex11's bounce()
        const inc = M.supNorm(x[c].map((t, i) => t - prev[i]));
        const err = an.exact ? M.supNorm(x[c].map((t, i) => t - an.exact[i])) : null;
        const h = hist[c][hist[c].length - 1];
        hist[c].push({ k: k + 1, inc, err, ratio: h && h.inc > 1e-12 && inc > 1e-12 ? inc / h.inc : null, total: x[c].reduce((s, t) => s + t, 0) });
      }
      k++;
    }
    function advanceTo(K) { if (K < k) { const keep = scene(); reset(keep); } while (k < K) bounce(); return state(); }
    function scene() { return { surfaces: JSON.parse(JSON.stringify(surf)), lamps: lamps.map(L => ({ type: L.type, pos: L.pos.slice(), aim: L.aim, color: L.color.slice(), brightness: L.brightness, patch: L.patch, label: L.label })) }; }
    function state() {
      const o = { k, x: {}, history: {} };
      CH.forEach((n, c) => { o.x[n] = x[c].slice(); o.history[n] = hist[c].map(h => ({ ...h })); });
      return o;
    }
    // Edits keep the bounce count: the scene is rebuilt from darkness and replayed to the same k.
    function edit(fn) { const K = k; fn(); rebuild(); while (k < K) bounce(); }
    reset();
    return {
      reset, bounce, advanceTo, state, scene,
      addLamp(L) { let id; edit(() => { id = nextId++; lamps.push(normLamp(L || {}, id)); }); return id; },
      removeLamp(id) { edit(() => { lamps = lamps.filter(L => L.id !== id); }); },
      setLamp(id, patch) { edit(() => { lamps = lamps.map(L => L.id === id ? normLamp({ ...L, ...patch }, id) : L); }); },
      setSurface(f, patch) { edit(() => { surf[f] = { ...surf[f], ...patch }; if (patch.color) surf[f].color = patch.color.slice(0, 3); }); },
      get lamps() { return lamps; }, get channels() { return chans; }, get surfaces() { return surf; },
      get k() { return k; }, get x() { return x; }, get history() { return hist; },
    };
  }

  const api = { CH, TYPES, SPOT_HALF, MARGIN, GREY, arcs, overlap, distribution, beamEnd, matAc, emissionC, create, room: M };
  if (typeof module !== 'undefined') module.exports = api; else root.LampsModel = api;
})(typeof window !== 'undefined' ? window : globalThis);
