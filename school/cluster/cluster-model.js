// The cluster — the model, with its camera. Pure state + functions; runs in the page and under node for QA.
// 25 point masses, G = 1, two dimensions, no collisions. Seeded, deterministic, born bound.
(function (root) {
  'use strict';
  var N = 25, G = 1, SEED = 777;
  var TICK = 1 / 240;            // model seconds per tick; every body's step is TICK / 2^k
  var K = 52;                    // finest subdivision: TICK / 2^52 ≈ 9e-19 s (local times are rebased every tick, so they stay exact integers)
  var UNIT = 4503599627370496;  // 2^52,     // integer time units per tick
  var ETA = (typeof process !== 'undefined' && process.env && +process.env.ETA) || 0.01;                // step = largest TICK/2^k ≤ ETA × the body's tightest pair time scale
  var R0 = 3;                    // every body starts within this radius of the centre of mass
  var Q0 = (typeof process !== 'undefined' && process.env && +process.env.Q0) || 0.48;                 // starting virial ratio K/|U| (0.5 is equilibrium; below it the cluster first falls in)
  var ESCAPE_R = 25;             // escape radius, units from the centre of mass
  var OCC_MIN = 0.35, OCC_MAX = 0.95;   // the framing band (frozen)
  var CONTAIN = 0.92;            // hard containment: bound members never fill more than 92 % of either axis
  var CAM_TAU = 0.6;             // camera easing time constant, model seconds

  // Only + − × ÷ and √ (all correctly rounded in IEEE 754) in the physics: no sin, cos, pow or hypot, whose last bits
  // may differ between JavaScript engines. The same seed then gives the same run in any browser and in node.
  function len(x, y) { return Math.sqrt(x * x + y * y); }

  // mulberry32
  function rng(seed) { var a = seed >>> 0; return function () {
    a = (a + 0x6D2B79F5) >>> 0; var t = a; t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

  // ---- the seeded, born-bound start ----
  function initial(seed) {
    var r = rng(seed), m = [], x = [], v = [], i;
    for (i = 0; i < N; i++) m.push(0.5 + 1.5 * r());                                   // masses in [0.5, 2.0]
    while (x.length < N) { var px = R0 * (2 * r() - 1), py = R0 * (2 * r() - 1);           // uniform over a disc of radius 3
      if (px * px + py * py <= R0 * R0) x.push([px, py]); }                                   // (rejection: no trigonometry)
    var M = 0, cx = 0, cy = 0, px = 0, py = 0;
    for (i = 0; i < N; i++) { M += m[i]; cx += m[i] * x[i][0]; cy += m[i] * x[i][1]; }
    for (i = 0; i < N; i++) { x[i][0] -= cx / M; x[i][1] -= cy / M; }                                    // centre of mass at the origin
    var rmax = 0; for (i = 0; i < N; i++) rmax = Math.max(rmax, len(x[i][0], x[i][1]));
    if (rmax > R0) for (i = 0; i < N; i++) { x[i][0] *= R0 / rmax; x[i][1] *= R0 / rmax; }               // back inside radius 3
    // each body's speed is proportional to √|φ_i| (φ_i = its potential per unit mass), so every body starts at the
    // same fraction of its own escape speed; directions are uniform on the circle
    for (i = 0; i < N; i++) { var phi = 0, ux, uy, uu;
      for (var k = 0; k < N; k++) if (k !== i) phi -= G * m[k] / len(x[k][0] - x[i][0], x[k][1] - x[i][1]);
      do { ux = 2 * r() - 1; uy = 2 * r() - 1; uu = ux * ux + uy * uy; } while (uu > 1 || uu < 1e-6);   // a uniform direction
      uu = Math.sqrt(uu); v.push([Math.sqrt(-phi) * ux / uu, Math.sqrt(-phi) * uy / uu]); }
    for (i = 0; i < N; i++) { px += m[i] * v[i][0]; py += m[i] * v[i][1]; }
    for (i = 0; i < N; i++) { v[i][0] -= px / M; v[i][1] -= py / M; }                                    // total momentum zero
    var Kin = 0, U = potential(m, x);
    for (i = 0; i < N; i++) Kin += 0.5 * m[i] * (v[i][0] * v[i][0] + v[i][1] * v[i][1]);
    var f = Math.sqrt(Q0 * -U / Kin);                                                      // scale speeds: K = Q0 |U|, so E = (Q0 − 1)|U| < 0
    for (i = 0; i < N; i++) { v[i][0] *= f; v[i][1] *= f; }
    return { m: m, x: x, v: v };
  }

  function potential(m, x) { var U = 0;
    for (var i = 0; i < N; i++) for (var j = i + 1; j < N; j++) U -= G * m[i] * m[j] / len(x[j][0] - x[i][0], x[j][1] - x[i][1]);
    return U; }

  // ---- state ----
  // s.x, s.v: the integrated bodies. A close pair under the two-body treatment sits in its first member's slot as one
  // body of the pair's total mass at the pair's centre of mass; its relative orbit lives in s.kep[first].
  // s.X, s.V: all 25 true positions and velocities, rebuilt at every tick end. Everything measured, drawn and
  // exposed reads s.X / s.V.
  function make(seed) {
    var p = initial(seed == null ? SEED : seed), z = function () { return new Float64Array(2 * N); }, s = {
      seed: seed == null ? SEED : seed, N: N, G: G, t: 0, tick: 0, m: p.m.slice(), mf: p.m.slice(),
      x: z(), v: z(), a: z(), j: z(), xp: z(), vp: z(), a1: z(), j1: z(), PX: z(), PV: z(), X: z(), V: z(), td: z(),
      ti: new Float64Array(N), dti: new Float64Array(N), tau: new Float64Array(N), d3: new Float64Array(N),
      inner: new Array(N).fill(false), kep: new Array(N).fill(null), merges: 0, splits: 0,
      escaped: new Array(N).fill(false), escapers: [], evals: 0, view: null };
    for (var i = 0; i < N; i++) { s.x[2 * i] = p.x[i][0]; s.x[2 * i + 1] = p.x[i][1]; s.v[2 * i] = p.v[i][0]; s.v[2 * i + 1] = p.v[i][1]; }
    var all = []; for (i = 0; i < N; i++) all.push(i);
    predict(s, 0); force(s, all, s.a, s.j);
    for (i = 0; i < N; i++) s.dti[i] = quantize(s, i, 0, 0);
    resolve(s); s.E0 = energy(s);
    return s;
  }

  // ---- the two-body orbit, exactly: universal-variable Kepler drift (any eccentricity, bound or not) ----
  // Stumpff functions c0…c3 of z: a short series at z / 4^n (|z / 4^n| ≤ 0.1), then n doublings back up
  function stumpff(z, c) {
    var n = 0; while (z > 0.1 || z < -0.1) { z /= 4; n++; }
    var c3 = (1 - z / 20 * (1 - z / 42 * (1 - z / 72 * (1 - z / 110 * (1 - z / 156 * (1 - z / 210)))))) / 6;
    var c2 = (1 - z / 12 * (1 - z / 30 * (1 - z / 56 * (1 - z / 90 * (1 - z / 132 * (1 - z / 182)))))) / 2;
    var c1 = 1 - z * c3, c0 = 1 - z * c2;
    for (; n > 0; n--) { c3 = (c2 + c0 * c3) / 4; c2 = c1 * c1 / 2; c1 = c0 * c1; c0 = 2 * c0 * c0 - 1; }
    c[0] = c0; c[1] = c1; c[2] = c2; c[3] = c3; return c;
  }
  var SC = [0, 0, 0, 0];
  // advance the relative state r = [rx, ry, vx, vy] under μ for dt (in place)
  function kepDrift(r, mu, dt) {
    if (dt === 0) return r;
    var r0 = len(r[0], r[1]), eta = r[0] * r[2] + r[1] * r[3], beta = 2 * mu / r0 - (r[2] * r[2] + r[3] * r[3]);
    if (beta > 0) { var P = 2 * Math.PI * mu / (beta * Math.sqrt(beta)); if (dt > P) dt -= P * Math.floor(dt / P); if (dt === 0) return r; }
    var T = function (s) { var c = stumpff(beta * s * s, SC); return r0 * s * c[1] + eta * s * s * c[2] + mu * s * s * s * c[3]; };
    var lo = 0, hi = beta > 0 ? 2 * Math.PI / Math.sqrt(beta) : Math.max(dt / r0, 1e-300);
    if (beta <= 0) while (T(hi) < dt) { lo = hi; hi *= 2; }
    var s = Math.min(Math.max(dt / r0, lo), hi), c, R, ds;
    for (var it = 0; it < 200; it++) {
      c = stumpff(beta * s * s, SC);
      var Ts = r0 * s * c[1] + eta * s * s * c[2] + mu * s * s * s * c[3] - dt;
      R = r0 * c[0] + eta * s * c[1] + mu * s * s * c[2];
      if (Ts > 0) hi = s; else lo = s;
      ds = Ts / R; var sn = s - ds;
      if (!(sn > lo && sn < hi)) { sn = (lo + hi) / 2; }
      if (Math.abs(sn - s) <= 1e-16 * Math.abs(sn) || hi - lo <= 1e-16 * hi) { s = sn; break; }
      s = sn;
    }
    c = stumpff(beta * s * s, SC);
    var G1 = s * c[1], G2 = s * s * c[2], G3 = s * s * s * c[3];
    R = r0 * c[0] + eta * G1 + mu * G2;
    var f = 1 - mu * G2 / r0, g = dt - mu * G3, fd = -mu * G1 / (r0 * R), gd = 1 - mu * G2 / R;
    var x = f * r[0] + g * r[2], y = f * r[1] + g * r[3];
    r[2] = fd * r[0] + gd * r[2]; r[3] = fd * r[1] + gd * r[3]; r[0] = x; r[1] = y;
    return r;
  }

  // ---- forces ----
  // predicted positions at local time tn: every integrated body by its Taylor series, then each pair's members
  // by the exact two-body orbit around the pair's predicted centre
  var RT = [0, 0, 0, 0];
  function predict(s, tn) {
    var i, d, c;
    for (i = 0; i < N; i++) { if (s.inner[i]) continue; var h = (tn - s.ti[i]) / UNIT * TICK;
      for (d = 0; d < 2; d++) { c = 2 * i + d;
        if (h === 0) { s.xp[c] = s.x[c]; s.vp[c] = s.v[c]; }
        else { s.xp[c] = s.x[c] + h * s.v[c] + h * h / 2 * s.a[c] + h * h * h / 6 * s.j[c]; s.vp[c] = s.v[c] + h * s.a[c] + h * h / 2 * s.j[c]; }
        s.PX[c] = s.xp[c]; s.PV[c] = s.vp[c]; } }
    for (i = 0; i < N; i++) { var el = s.kep[i]; if (!el) continue;
      RT[0] = el.r[0]; RT[1] = el.r[1]; RT[2] = el.r[2]; RT[3] = el.r[3];
      kepDrift(RT, el.mu, (tn - el.tc) / UNIT * TICK); members(s, i, el, RT, s.xp, s.vp, s.PX, s.PV); }
  }
  function members(s, i, el, r, cx, cv, X, V) {
    var k = el.k, M = el.mi + el.mk, fi = el.mk / M, fk = el.mi / M, c0 = cx[2 * i], c1 = cx[2 * i + 1], u0 = cv[2 * i], u1 = cv[2 * i + 1];
    X[2 * k] = c0 - fk * r[0]; X[2 * k + 1] = c1 - fk * r[1]; V[2 * k] = u0 - fk * r[2]; V[2 * k + 1] = u1 - fk * r[3];
    X[2 * i] = c0 + fi * r[0]; X[2 * i + 1] = c1 + fi * r[1]; V[2 * i] = u0 + fi * r[2]; V[2 * i + 1] = u1 + fi * r[3];
  }
  // pull and jerk on the point at slot p from every body except slots p and q (q = p's partner, or −1); returns tightest τ
  var AJ = [0, 0, 0, 0];
  function pull(s, p, q, mp) {
    var X = s.PX, V = s.PV, m = s.m, ax = 0, ay = 0, jx = 0, jy = 0, tmin = Infinity, xi = X[2 * p], yi = X[2 * p + 1], ui = V[2 * p], wi = V[2 * p + 1];
    for (var k = 0; k < N; k++) { if (k === p || k === q) continue;
      var dx = X[2 * k] - xi, dy = X[2 * k + 1] - yi, du = V[2 * k] - ui, dw = V[2 * k + 1] - wi;
      var r2 = dx * dx + dy * dy, ir2 = 1 / r2, r = Math.sqrt(r2), ir3 = G * m[k] * ir2 / r, rv = 3 * (dx * du + dy * dw) * ir2;
      ax += dx * ir3; ay += dy * ir3; jx += (du - rv * dx) * ir3; jy += (dw - rv * dy) * ir3;
      var ff = r * Math.sqrt(r / (G * (mp + m[k]))), fl = r / Math.sqrt(du * du + dw * dw + 1e-300);
      var tk = ff < fl ? ff : fl; if (tk < tmin) tmin = tk; }
    AJ[0] = ax; AJ[1] = ay; AJ[2] = jx; AJ[3] = jy; return tmin;
  }

  var FREE = 1e-7;   // below this tidal ratio a pair's own orbit sets no limit on its centre's step
  // acceleration and jerk on the listed integrated bodies (into a, j), with each one's step time scale τ
  function force(s, list, a, j) {
    for (var q = 0; q < list.length; q++) {
      var i = list[q], el = s.kep[i];
      if (!el) { s.tau[i] = pull(s, i, -1, s.m[i]); a[2 * i] = AJ[0]; a[2 * i + 1] = AJ[1]; j[2 * i] = AJ[2]; j[2 * i + 1] = AJ[3]; continue; }
      var k = el.k, M = el.mi + el.mk;
      var ti = pull(s, i, k, M), ax = AJ[0], ay = AJ[1], jx = AJ[2], jy = AJ[3];
      var tk = pull(s, k, i, M);
      a[2 * i] = (el.mi * ax + el.mk * AJ[0]) / M; a[2 * i + 1] = (el.mi * ay + el.mk * AJ[1]) / M;
      j[2 * i] = (el.mi * jx + el.mk * AJ[2]) / M; j[2 * i + 1] = (el.mi * jy + el.mk * AJ[3]) / M;
      s.td[2 * i] = ax - AJ[0]; s.td[2 * i + 1] = ay - AJ[1];          // the tide across the pair: pull on i minus pull on k
      // the pair's size, and how hard the rest of the cluster pulls it apart
      var cx = s.xp[2 * i], cy = s.xp[2 * i + 1], rr = el.r, rn = len(rr[0], rr[1]), en = 0.5 * (rr[2] * rr[2] + rr[3] * rr[3]) - el.mu / rn;
      var size = rn, per = Infinity;
      if (en < 0) { var sa = -el.mu / (2 * en), ev = Math.sqrt(Math.max(0, 1 - (rr[0] * rr[3] - rr[1] * rr[2]) * (rr[0] * rr[3] - rr[1] * rr[2]) / (el.mu * sa))); size = Math.max(rn, sa * (1 + ev)); per = 2 * Math.PI * Math.sqrt(sa * sa * sa / el.mu); }
      var g = 0, d3 = Infinity;
      for (var l = 0; l < N; l++) { if (l === i || l === k) continue; var dl = len(s.PX[2 * l] - cx, s.PX[2 * l + 1] - cy);
        if (dl < d3) d3 = dl; var sd = size / dl, gl = 2 * s.m[l] / M * sd * sd * sd; if (gl > g) g = gl; }
      s.d3[i] = d3 / size; el.gamma = g; el.size = size; el.bound = en < 0;
      var tt = Math.min(ti, tk);
      if (en < 0 && g > FREE) tt = Math.min(tt, per / 20 / ETA);     // a disturbed pair: at least 20 kicks per orbit
      s.tau[i] = tt;
    }
    s.evals += list.length; if (s.evalsBy) for (q = 0; q < list.length; q++) s.evalsBy[list[q]]++;
  }

  // a body's next step, in integer time units: the largest UNIT/2^k ≤ ETA·τ, at most double the last, landing on its own grid
  function quantize(s, i, prev, now) {
    var want = ETA * s.tau[i] / TICK * UNIT, d = UNIT;
    while (d > want && d > 1) d /= 2;
    if (prev && d > 2 * prev) d = 2 * prev;
    while (now % d !== 0) d /= 2;
    return d;
  }

  // ---- one tick (TICK model seconds): block-step Hermite for every integrated body, kick–drift–kick for each pair ----
  var R_MERGE = 0.05, CLEAR_IN = 5, CLEAR_OUT = 4, R_SPLIT = 0.1;
  function tick(s) {
    var x = s.x, v = s.v, a = s.a, j = s.j, xp = s.xp, vp = s.vp, a1 = s.a1, j1 = s.j1, i, d, q, act = [];
    for (;;) {
      var tn = Infinity; for (i = 0; i < N; i++) { if (s.inner[i]) continue; var ni = s.ti[i] + s.dti[i]; if (ni < tn) tn = ni; }
      act.length = 0; for (i = 0; i < N; i++) if (!s.inner[i] && s.ti[i] + s.dti[i] === tn) act.push(i);
      predict(s, tn);
      var tdOld = [];
      for (q = 0; q < act.length; q++) { i = act[q]; if (s.kep[i]) tdOld[i] = [s.td[2 * i], s.td[2 * i + 1]]; }
      force(s, act, a1, j1);
      for (q = 0; q < act.length; q++) { i = act[q]; var h = s.dti[i] / UNIT * TICK;
        for (d = 0; d < 2; d++) { var c = 2 * i + d;
          var vn = v[c] + h / 2 * (a[c] + a1[c]) + h * h / 12 * (j[c] - j1[c]);
          x[c] = x[c] + h / 2 * (v[c] + vn) + h * h / 12 * (a[c] - a1[c]); v[c] = vn; a[c] = a1[c]; j[c] = j1[c]; }
        var el = s.kep[i];
        if (el) { var r = el.r;                                       // the pair's own orbit: half tide, exact orbit, half tide
          r[2] += h / 2 * tdOld[i][0]; r[3] += h / 2 * tdOld[i][1];
          kepDrift(r, el.mu, h);
          r[2] += h / 2 * s.td[2 * i]; r[3] += h / 2 * s.td[2 * i + 1]; el.tc = tn; }
        s.ti[i] = tn; }
      for (q = 0; q < act.length; q++) { i = act[q]; s.dti[i] = quantize(s, i, s.dti[i], tn); }
      encounters(s, act, tn);
      if (tn === UNIT) break;
    }
    for (i = 0; i < N; i++) { if (s.inner[i]) continue; s.ti[i] = 0; if (s.kep[i]) s.kep[i].tc = 0; }   // rebase local time
    s.tick++; s.t = s.tick * TICK;
    resolve(s);
    checkEscapes(s);
  }

  // open pairs that a third body has come close to (or that have flown apart); close up new close pairs
  function encounters(s, act, tn) {
    var i, k, q, ch = [];
    for (q = 0; q < act.length; q++) { i = act[q]; var el = s.kep[i]; if (!el) continue;
      var rn = len(el.r[0], el.r[1]);
      if (s.d3[i] < CLEAR_OUT || (!el.bound && rn > R_SPLIT)) { split(s, i, tn); ch.push(i, el.k); } }
    for (q = 0; q < act.length; q++) { i = act[q]; if (s.kep[i] || s.inner[i] || s.ti[i] !== tn) continue;
      var best = -1, bd = Infinity;
      for (k = 0; k < N; k++) { if (k === i || s.inner[k] || s.kep[k]) continue;
        var dd = len(s.x[2 * k] - s.x[2 * i], s.x[2 * k + 1] - s.x[2 * i + 1]); if (dd < bd) { bd = dd; best = k; } }
      if (best < 0 || bd > R_MERGE || s.ti[best] !== tn) continue;
      k = best; var M = s.m[i] + s.m[k], cx = (s.m[i] * s.x[2 * i] + s.m[k] * s.x[2 * k]) / M, cy = (s.m[i] * s.x[2 * i + 1] + s.m[k] * s.x[2 * k + 1]) / M, d3 = Infinity;
      for (var l = 0; l < N; l++) { if (l === i || l === k || s.inner[l]) continue;
        var px = s.ti[l] === tn ? s.x[2 * l] : s.xp[2 * l], py = s.ti[l] === tn ? s.x[2 * l + 1] : s.xp[2 * l + 1];
        d3 = Math.min(d3, len(px - cx, py - cy)); if (s.kep[l]) d3 = Math.min(d3, len(s.PX[2 * s.kep[l].k] - cx, s.PX[2 * s.kep[l].k + 1] - cy)); }
      if (d3 < CLEAR_IN * bd) continue;
      merge(s, i, k, tn); ch.push(i);
    }
    if (ch.length) {   // fresh forces and steps for everything that changed, from the states at tn
      predict(s, tn); var fresh = []; ch.forEach(function (b) { if (!s.inner[b] && fresh.indexOf(b) < 0) fresh.push(b); });
      force(s, fresh, s.a, s.j);
      fresh.forEach(function (b) { s.dti[b] = quantize(s, b, 0, tn); });
    }
  }
  function merge(s, i, k, tn) {
    var M = s.m[i] + s.m[k], r = [s.x[2 * i] - s.x[2 * k], s.x[2 * i + 1] - s.x[2 * k + 1], s.v[2 * i] - s.v[2 * k], s.v[2 * i + 1] - s.v[2 * k + 1]];
    for (var d = 0; d < 2; d++) { s.x[2 * i + d] = (s.m[i] * s.x[2 * i + d] + s.m[k] * s.x[2 * k + d]) / M; s.v[2 * i + d] = (s.m[i] * s.v[2 * i + d] + s.m[k] * s.v[2 * k + d]) / M; }
    s.kep[i] = { k: k, mi: s.m[i], mk: s.m[k], mu: G * M, r: r, tc: tn, gamma: 0, size: len(r[0], r[1]), bound: true };
    s.inner[k] = true; s.mf[i] = M; s.dti[k] = Infinity; s.merges++;
  }
  function split(s, i, tn) {
    var el = s.kep[i], k = el.k; members(s, i, el, el.r, s.x, s.v, s.x, s.v);
    s.mf[i] = el.mi; s.kep[i] = null; s.inner[k] = false; s.ti[k] = tn; s.splits++;
  }

  // the true 25 positions and velocities at the tick boundary
  function resolve(s) {
    s.X.set(s.x); s.V.set(s.v);
    for (var i = 0; i < N; i++) { var el = s.kep[i]; if (el) members(s, i, el, el.r, s.x, s.v, s.X, s.V); }
  }

  // ---- measurements (on the true positions, s.X / s.V) ----
  // total energy; a pair under the two-body treatment contributes its mutual term from its own relative separation,
  // which is exact even when the two are far closer together than their absolute coordinates can resolve
  function energy(s) { var Kin = 0, U = 0, m = s.m, x = s.X, v = s.V, i, k, part = new Array(N).fill(-1);
    for (i = 0; i < N; i++) if (s.kep && s.kep[i]) { part[i] = s.kep[i].k; part[s.kep[i].k] = i; }
    for (i = 0; i < N; i++) Kin += 0.5 * m[i] * (v[2 * i] * v[2 * i] + v[2 * i + 1] * v[2 * i + 1]);
    for (i = 0; i < N; i++) for (k = i + 1; k < N; k++) {
      var r = part[i] === k ? len(s.kep[Math.min(i, k)] ? s.kep[Math.min(i, k)].r[0] : s.kep[Math.max(i, k)].r[0], s.kep[Math.min(i, k)] ? s.kep[Math.min(i, k)].r[1] : s.kep[Math.max(i, k)].r[1])
        : len(x[2 * k] - x[2 * i], x[2 * k + 1] - x[2 * i + 1]);
      U -= G * m[i] * m[k] / r; }
    return Kin + U; }

  function com(s, skip) { var M = 0, X = 0, Y = 0, VX = 0, VY = 0;
    for (var i = 0; i < N; i++) { if (skip && skip(i)) continue; var mi = s.m[i];
      M += mi; X += mi * s.X[2 * i]; Y += mi * s.X[2 * i + 1]; VX += mi * s.V[2 * i]; VY += mi * s.V[2 * i + 1]; }
    return { x: X / M, y: Y / M, vx: VX / M, vy: VY / M, M: M }; }

  // Escape test (frozen): more than 25 units from the centre of mass, moving outward, and the two-body energy
  // against the remaining cluster (every body not yet escaped, less this one), in reduced-mass form, is ≥ 0.
  function escapeTest(s, i) {
    var c = com(s), dx = s.X[2 * i] - c.x, dy = s.X[2 * i + 1] - c.y, r = len(dx, dy);
    var outward = dx * (s.V[2 * i] - c.vx) + dy * (s.V[2 * i + 1] - c.vy) > 0;
    var rest = com(s, function (k) { return k === i || s.escaped[k]; }), mi = s.m[i], Mc = rest.M;
    if (!(Mc > 0)) return { r: r, outward: outward, e2: -Infinity, escaped: false };   // the last member has nothing to escape from
    var rx = s.X[2 * i] - rest.x, ry = s.X[2 * i + 1] - rest.y, ux = s.V[2 * i] - rest.vx, uy = s.V[2 * i + 1] - rest.vy;
    var mu = mi * Mc / (mi + Mc), e2 = 0.5 * mu * (ux * ux + uy * uy) - G * mi * Mc / len(rx, ry);
    return { r: r, outward: outward, e2: e2, escaped: r > ESCAPE_R && outward && e2 >= 0 };
  }

  function checkEscapes(s) {
    for (var i = 0; i < N; i++) { if (s.escaped[i]) continue;
      if (escapeTest(s, i).escaped) { s.escaped[i] = true; s.escapers.push({ body: i, t: s.t }); } }
  }

  function boundList(s) { var b = []; for (var i = 0; i < N; i++) if (!s.escaped[i]) b.push(i); return b; }

  // ---- the camera ----
  // extent of the bound members: bounding box, and span = the larger of its width and height
  function extent(s) {
    var x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    for (var i = 0; i < N; i++) { if (s.escaped[i]) continue; var X = s.X[2 * i], Y = s.X[2 * i + 1];
      if (X < x0) x0 = X; if (X > x1) x1 = X; if (Y < y0) y0 = Y; if (Y > y1) y1 = Y; }
    return { x0: x0, x1: x1, y0: y0, y1: y1, cx: (x0 + x1) / 2, cy: (y0 + y1) / 2, w: x1 - x0, h: y1 - y0, span: Math.max(x1 - x0, y1 - y0) };
  }

  // The width the camera wants: the bound members' span fills `fill` of the view, widened if the view's
  // height (width × aspect) could not contain their y-extent at the containment limit.
  function target(s, o) {
    var e = extent(s), fill = o.fill, asp = o.aspect;
    var w = Math.max(e.span / fill, e.w / CONTAIN, e.h / (CONTAIN * asp), 1e-6);
    return { e: e, w: w, cx: e.cx, cy: e.cy };
  }

  // Clamp any proposed view into the frozen band: width ≥ what containment needs, ≤ span / 0.35 (unless containment
  // itself needs more), centre moved by the least amount that keeps every bound member inside.
  function clampView(e, o, w, cx, cy) {
    var need = Math.max(e.w / CONTAIN, e.h / (CONTAIN * o.aspect), 1e-6), most = Math.max(e.span / OCC_MIN * 0.999, need);
    w = Math.min(Math.max(w, need, e.span / OCC_MAX * 1.001), most);
    var hw = w / 2 * CONTAIN, hh = w * o.aspect / 2 * CONTAIN;   // keep bound members inside the inner 92 %
    cx = Math.min(Math.max(cx, e.x1 - hw), e.x0 + hw);
    cy = Math.min(Math.max(cy, e.y1 - hh), e.y0 + hh);
    return { cx: cx, cy: cy, width: w, height: w * o.aspect };
  }

  function opts(o) { o = o || {}; return { fill: o.fill == null ? 0.7 : o.fill, aspect: o.aspect == null ? 1 : o.aspect }; }

  // camera(state, {fill, aspect}) → {cx, cy, width, height}. A function of the state: the eased view the model carries
  // (state.view, advanced once per tick by followCamera), clamped into the band; with no carried view, the target itself.
  function camera(s, o) {
    o = opts(o); var tg = target(s, o), vw = s.view;
    if (!vw) return clampView(tg.e, o, tg.w, tg.cx, tg.cy);
    return clampView(tg.e, o, vw.w, vw.cx, vw.cy);
  }

  // one tick of easing toward the target: the gap closes by the fraction k = 1 − e^(−TICK/CAM_TAU) each tick
  // (series form, plain arithmetic), starting from where the clamped camera actually is
  var XK = TICK / CAM_TAU, KEASE = XK - XK * XK / 2 + XK * XK * XK / 6 - XK * XK * XK * XK / 24;
  function followCamera(s, o) {
    o = opts(o); var tg = target(s, o);
    if (!s.view) { s.view = { w: tg.w, cx: tg.cx, cy: tg.cy }; return; }
    var k = KEASE, c = clampView(tg.e, o, s.view.w, s.view.cx, s.view.cy);
    s.view = { w: c.width + k * (tg.w - c.width), cx: c.cx + k * (tg.cx - c.cx), cy: c.cy + k * (tg.cy - c.cy) };
  }

  function occupancy(s, cam) { return extent(s).span / cam.width; }
  function inside(s, cam) { var hw = cam.width / 2, hh = cam.height / 2;
    for (var i = 0; i < N; i++) { if (s.escaped[i]) continue;
      if (Math.abs(s.X[2 * i] - cam.cx) > hw || Math.abs(s.X[2 * i + 1] - cam.cy) > hh) return false; }
    return true; }

  // a plain copy for display and QA
  function snapshot(s) {
    var c = com(s), p = [], u = [];
    for (var i = 0; i < N; i++) { p.push([s.X[2 * i], s.X[2 * i + 1]]); u.push([s.V[2 * i], s.V[2 * i + 1]]); }
    return { t: s.t, masses: s.m.slice(), positions: p, velocities: u, energy: energy(s), E0: s.E0,
      com: [c.x, c.y], comVelocity: [c.vx, c.vy], bound: N - s.escapers.length,
      escapers: s.escapers.map(function (e) { return { body: e.body, t: e.t }; }), escaped: s.escaped.slice(),
      view: s.view && { w: s.view.w, cx: s.view.cx, cy: s.view.cy }, pairs: (s.kep || []).map(function (e, i) { return e ? [i, e.k] : null; }).filter(Boolean) };
  }

  // rebuild a model state from a snapshot-shaped object (lets camera() and the escape test run on any state)
  function fromSnapshot(o) {
    var s = { N: N, m: o.masses.slice(), X: new Float64Array(2 * N), V: new Float64Array(2 * N), escaped: (o.escaped || new Array(N).fill(false)).slice(),
      escapers: (o.escapers || []).slice(), view: o.view ? { w: o.view.w, cx: o.view.cx, cy: o.view.cy } : null, t: o.t };
    for (var i = 0; i < N; i++) { s.X[2 * i] = o.positions[i][0]; s.X[2 * i + 1] = o.positions[i][1]; s.V[2 * i] = o.velocities[i][0]; s.V[2 * i + 1] = o.velocities[i][1]; }
    return s;
  }

  var api = { N: N, G: G, SEED: SEED, TICK: TICK, ETA: ETA, R0: R0, Q0: Q0, ESCAPE_R: ESCAPE_R, OCC_MIN: OCC_MIN, OCC_MAX: OCC_MAX,
    CONTAIN: CONTAIN, CAM_TAU: CAM_TAU, rng: rng, initial: initial, make: make, tick: tick, energy: energy, com: com,
    escapeTest: escapeTest, boundList: boundList, extent: extent, camera: camera, followCamera: followCamera,
    occupancy: occupancy, inside: inside, snapshot: snapshot, fromSnapshot: fromSnapshot, kepDrift: kepDrift };
  root.Cluster = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
