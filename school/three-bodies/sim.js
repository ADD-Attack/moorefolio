// Three bodies — the model. Pure functions plus one state object; runs in the page and under node for QA.
(function (root) {
  'use strict';
  var H = 1 / 1200;          // substep length, model time units
  var SUBSTEPS = 20;         // substeps per frame at speed ×1  →  20 × 1/1200 = 1/60 time unit per frame
  var VIEW_BOUND = 5;        // distance from the centre of mass beyond which a body is "out of view"

  var PRESETS = {
    figure8: { name: 'Figure-8', m: [1, 1, 1],
      x: [[0.97000436, -0.24308753], [-0.97000436, 0.24308753], [0, 0]],
      v: [[0.4662036850, 0.4323657300], [0.4662036850, 0.4323657300], [-0.9324073700, -0.8647314600]] },
    pythagorean: { name: 'Pythagorean', m: [3, 4, 5],
      x: [[1, 3], [-2, -1], [1, -1]], v: [[0, 0], [0, 0], [0, 0]] }
  };

  // mulberry32 — the seeded generator behind the Random preset
  function rng(seed) { var a = seed >>> 0; return function () {
    a = (a + 0x6D2B79F5) >>> 0; var t = a; t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

  function randomPreset(seed) {
    var r = rng(seed), u = function (lo, hi) { return lo + (hi - lo) * r(); };
    var m = [], x = [], v = [], i;
    for (i = 0; i < 3; i++) { m.push(u(0.5, 1.5)); x.push([u(-1.5, 1.5), u(-1.5, 1.5)]); v.push([u(-0.5, 0.5), u(-0.5, 0.5)]); }
    // remove the centre-of-mass drift so the system stays in frame
    var M = m[0] + m[1] + m[2], px = 0, py = 0;
    for (i = 0; i < 3; i++) { px += m[i] * v[i][0]; py += m[i] * v[i][1]; }
    for (i = 0; i < 3; i++) { v[i][0] -= px / M; v[i][1] -= py / M; }
    return { name: 'Random', m: m, x: x, v: v };
  }

  function make(preset, G) {
    return { G: G, m: preset.m.slice(), x: preset.x.map(function (p) { return p.slice(); }),
      v: preset.v.map(function (p) { return p.slice(); }), a: [[0, 0], [0, 0], [0, 0]], t: 0, steps: 0 };
  }

  // pairwise inverse-square: a_i = Σ_j G m_j (x_j − x_i) / |x_j − x_i|³
  function accel(s) {
    var a = s.a, x = s.x, m = s.m, i, j;
    for (i = 0; i < 3; i++) { a[i][0] = 0; a[i][1] = 0; }
    for (i = 0; i < 3; i++) for (j = i + 1; j < 3; j++) {
      var dx = x[j][0] - x[i][0], dy = x[j][1] - x[i][1];
      var r2 = dx * dx + dy * dy, inv3 = s.G / (r2 * Math.sqrt(r2));
      a[i][0] += m[j] * dx * inv3; a[i][1] += m[j] * dy * inv3;
      a[j][0] -= m[i] * dx * inv3; a[j][1] -= m[i] * dy * inv3;
    }
  }

  // one velocity-Verlet (kick–drift–kick) substep of length h
  function verlet(s, h) {
    var i, x = s.x, v = s.v, a = s.a;
    for (i = 0; i < 3; i++) { v[i][0] += 0.5 * h * a[i][0]; v[i][1] += 0.5 * h * a[i][1];
      x[i][0] += h * v[i][0]; x[i][1] += h * v[i][1]; }
    accel(s);
    for (i = 0; i < 3; i++) { v[i][0] += 0.5 * h * a[i][0]; v[i][1] += 0.5 * h * a[i][1]; }
  }

  // Close-encounter refinement: inside each substep, every Verlet step is capped at
  // ETA × the tightest pair's free-fall time scale  τ = r^1.5 / sqrt(G (m_i + m_j)),
  // re-measured before every step. Wide orbits take the whole substep H in one Verlet step.
  var ETA = 0.0001;
  function tau(s) { var t = Infinity;
    for (var i = 0; i < 3; i++) for (var j = i + 1; j < 3; j++) {
      var r = Math.hypot(s.x[j][0] - s.x[i][0], s.x[j][1] - s.x[i][1]);
      t = Math.min(t, Math.pow(r, 1.5) / Math.sqrt(s.G * (s.m[i] + s.m[j])));
    } return t; }
  function substep(s) {
    var left = H, n = 0;
    while (left > 1e-15) { var h = Math.min(left, ETA * tau(s)); verlet(s, h); left -= h; n++; }
    s.t += H; s.steps++; s.lastSplit = n;
  }

  function closest(s) { var best = Infinity;
    for (var i = 0; i < 3; i++) for (var j = i + 1; j < 3; j++)
      best = Math.min(best, Math.hypot(s.x[j][0] - s.x[i][0], s.x[j][1] - s.x[i][1]));
    return best; }

  // E = Σ ½ m v²  −  Σ_{i<j} G m_i m_j / r_ij
  function energy(s) { var K = 0, U = 0, i, j;
    for (i = 0; i < 3; i++) K += 0.5 * s.m[i] * (s.v[i][0] * s.v[i][0] + s.v[i][1] * s.v[i][1]);
    for (i = 0; i < 3; i++) for (j = i + 1; j < 3; j++)
      U -= s.G * s.m[i] * s.m[j] / Math.hypot(s.x[j][0] - s.x[i][0], s.x[j][1] - s.x[i][1]);
    return K + U; }

  function fastest(s) { var b = 0; for (var i = 0; i < 3; i++) b = Math.max(b, Math.hypot(s.v[i][0], s.v[i][1])); return b; }

  function com(s) { var M = 0, X = 0, Y = 0;
    for (var i = 0; i < 3; i++) { M += s.m[i]; X += s.m[i] * s.x[i][0]; Y += s.m[i] * s.x[i][1]; }
    return [X / M, Y / M]; }

  // Ejection test: body i is beyond VIEW_BOUND from the centre of mass, moving outward,
  // and unbound from the pair left behind (its two-body energy relative to their centre of mass is ≥ 0).
  function ejected(s) {
    var c = com(s), out = [];
    for (var i = 0; i < 3; i++) {
      var dx = s.x[i][0] - c[0], dy = s.x[i][1] - c[1], r = Math.hypot(dx, dy);
      if (r <= VIEW_BOUND) continue;
      var j = (i + 1) % 3, k = (i + 2) % 3, mp = s.m[j] + s.m[k];
      var px = (s.m[j] * s.x[j][0] + s.m[k] * s.x[k][0]) / mp, py = (s.m[j] * s.x[j][1] + s.m[k] * s.x[k][1]) / mp;
      var qx = (s.m[j] * s.v[j][0] + s.m[k] * s.v[k][0]) / mp, qy = (s.m[j] * s.v[j][1] + s.m[k] * s.v[k][1]) / mp;
      var rx = s.x[i][0] - px, ry = s.x[i][1] - py, ux = s.v[i][0] - qx, uy = s.v[i][1] - qy;
      var mu = s.m[i] * mp / (s.m[i] + mp);
      var e2 = 0.5 * mu * (ux * ux + uy * uy) - s.G * s.m[i] * mp / Math.hypot(rx, ry);
      var outward = dx * (s.v[i][0]) + dy * (s.v[i][1]) > 0;
      out.push({ body: i, r: r, outward: outward, unbound: e2 >= 0 });
    }
    return out;
  }

  // two-body energy of the pair (j, k) in their own centre-of-mass frame; < 0 means they are bound to each other
  function pairEnergy(s, j, k) { var mu = s.m[j] * s.m[k] / (s.m[j] + s.m[k]);
    var ux = s.v[j][0] - s.v[k][0], uy = s.v[j][1] - s.v[k][1];
    return 0.5 * mu * (ux * ux + uy * uy) - s.G * s.m[j] * s.m[k] / Math.hypot(s.x[j][0] - s.x[k][0], s.x[j][1] - s.x[k][1]); }

  root.ThreeBody = { pairEnergy: pairEnergy, H: H, ETA: ETA, SUBSTEPS: SUBSTEPS, VIEW_BOUND: VIEW_BOUND, PRESETS: PRESETS, randomPreset: randomPreset,
    make: function (p, G) { var s = make(p, G); accel(s); return s; }, accel: accel, substep: substep,
    energy: energy, closest: closest, fastest: fastest, com: com, ejected: ejected };
})(typeof window !== 'undefined' ? window : globalThis);
