// W-Ex11 model — the sharp radiosity theorem (Einstein, DISCOVERY-1 S4) in a flatland room.
// A = diag(ρ)·F, Jacobi from darkness: x0 = 0, x_{k+1} = e + A x_k.
// Model arithmetic is + − × ÷ √ only, so Chrome and node agree bit for bit (lesson 22).
(function (root) {
  'use strict';
  const W = 8, H = 5, SEG = 1;                 // room 8 m × 5 m, 1 m patches
  const SURFACES = ['floor', 'right', 'ceiling', 'left'];

  // Patches walk the room's boundary anticlockwise: floor (y=0) → right wall → ceiling → left wall.
  function buildPatches() {
    const P = [];
    for (let i = 0; i < W; i++) P.push({ a: [i, 0], b: [i + 1, 0], s: 'floor' });
    for (let i = 0; i < H; i++) P.push({ a: [W, i], b: [W, i + 1], s: 'right' });
    for (let i = 0; i < W; i++) P.push({ a: [W - i, H], b: [W - i - 1, H], s: 'ceiling' });
    for (let i = 0; i < H; i++) P.push({ a: [0, H - i], b: [0, H - i - 1], s: 'left' });
    return P;
  }
  const dist = (p, q) => Math.sqrt((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2);
  // Hottel's crossed-strings rule: the exact form factor between two segments in a 2D enclosure
  // that see each other unobstructed (true for every pair in a convex room; collinear pairs get 0).
  function formFactors(P) {
    const n = P.length, F = [];
    for (let i = 0; i < n; i++) { F.push(new Array(n).fill(0));
      for (let j = 0; j < n; j++) { if (P[i].s === P[j].s) continue;
        const L = dist(P[i].a, P[i].b);
        F[i][j] = (dist(P[i].a, P[j].b) + dist(P[i].b, P[j].a) - dist(P[i].a, P[j].a) - dist(P[i].b, P[j].b)) / (2 * L);
        if (F[i][j] < 0) F[i][j] = -F[i][j];   // orientation: the anticlockwise walk crosses the strings the other way
      } }
    return F;
  }
  const PATCHES = buildPatches(), N = PATCHES.length, FF = formFactors(PATCHES);

  const DEFAULTS = { refl: { floor: 0.45, right: 0.8, ceiling: 0.85, left: 0.8 }, lamp: 16 };   // ceiling patch spanning x = 4–5 m, centre of the ceiling

  function matA(refl) { return FF.map((row, i) => row.map(f => refl[PATCHES[i].s] * f)); }
  function mulVec(A, x) { const y = new Array(A.length).fill(0);
    for (let i = 0; i < A.length; i++) { let s = 0; for (let j = 0; j < x.length; j++) s += A[i][j] * x[j]; y[i] = s; } return y; }
  const supNorm = v => v.reduce((m, t) => Math.max(m, Math.abs(t)), 0);
  function emission(lamp) { const e = new Array(N).fill(0); e[lamp] = 1; return e; }

  // Gaussian elimination with partial pivoting: solve (I − A) x = b. Returns null when singular to working precision.
  function solve(A, b) {
    const n = b.length, M = A.map((r, i) => r.map((a, j) => (i === j ? 1 : 0) - a).concat([b[i]]));
    for (let c = 0; c < n; c++) {
      let p = c; for (let r = c + 1; r < n; r++) if (Math.abs(M[r][c]) > Math.abs(M[p][c])) p = r;
      if (Math.abs(M[p][c]) < 1e-12) return null;
      [M[c], M[p]] = [M[p], M[c]];
      for (let r = c + 1; r < n; r++) { const f = M[r][c] / M[c][c]; for (let k = c; k <= n; k++) M[r][k] -= f * M[c][k]; }
    }
    const x = new Array(n).fill(0);
    for (let r = n - 1; r >= 0; r--) { let s = M[r][n]; for (let k = r + 1; k < n; k++) s -= M[r][k] * x[k]; x[r] = s / M[r][r]; }
    return x;
  }

  // Spectral radius by Collatz–Wielandt: for any positive v, min (Av)_i/v_i ≤ ρ(A) ≤ max (Av)_i/v_i.
  // Power iteration on A + I (same Perron vector, no oscillation) tightens the bracket.
  function spectral(A) {
    let v = new Array(N).fill(1), lo = 0, hi = Infinity;
    for (let it = 0; it < 5000; it++) {
      const Av = mulVec(A, v); lo = Infinity; hi = 0;
      for (let i = 0; i < N; i++) { const q = Av[i] / v[i]; lo = Math.min(lo, q); hi = Math.max(hi, q); }
      if (hi - lo < 1e-13) break;
      const w = Av.map((t, i) => t + v[i]), m = supNorm(w); v = w.map(t => t / m);
    }
    // (b) is decided by the bracket: ρ < 1 only when the whole bracket, padded by 1e-12 for round-off, sits below 1.
    // The all-1.00 room has ρ = 1 exactly (rows of F sum to 1); in floating point its bracket straddles 1.
    return { rho: (lo + hi) / 2, lo, hi, below1: hi < 1 - 1e-12 };
  }

  // Condition (c): a vector v > 0 with (Av)_i < v_i for every i. Einstein's (a)⇒(c) step:
  // "the certificate is the radiosity solution" — v solves v = 1 + Av.
  function certificate(A) {
    const v = solve(A, new Array(N).fill(1));
    if (!v || v.some(t => !(t > 0))) return { exists: false, v, theta: null };
    const Av = mulVec(A, v); let theta = 0; for (let i = 0; i < N; i++) theta = Math.max(theta, Av[i] / v[i]);
    return { exists: theta < 1, v, theta };
  }

  function analyse(refl, lamp) {
    const A = matA(refl), e = emission(lamp), sp = spectral(A), cert = certificate(A);
    const rowMax = A.reduce((m, r) => Math.max(m, r.reduce((s, t) => s + t, 0)), 0);
    const exact = sp.below1 ? solve(A, e) : null;
    return { A, e, spectral: sp, certificate: cert, maxRowSum: rowMax, exact };
  }

  function create() {
    let refl, lamp, an, x, prev, k, history;
    function reset(scene) {
      refl = { ...DEFAULTS.refl, ...(scene && scene.refl) }; lamp = scene && scene.lamp != null ? scene.lamp : DEFAULTS.lamp;
      an = analyse(refl, lamp); x = new Array(N).fill(0); prev = null; k = 0; history = [];
    }
    function bounce() {
      prev = x; x = an.e.map((t, i) => t + mulVec(an.A, prev)[i]); k++;
      const inc = supNorm(x.map((t, i) => t - prev[i]));
      const err = an.exact ? supNorm(x.map((t, i) => t - an.exact[i])) : null;
      const h = history[history.length - 1];
      // ratio is null once increments fall below 1e-12: that is round-off, not light
      history.push({ k, inc, err, ratio: h && h.inc > 1e-12 && inc > 1e-12 ? inc / h.inc : null, total: x.reduce((s, t) => s + t, 0) });
    }
    function advanceTo(K) { if (K < k) { const s = { refl, lamp }; reset(s); } while (k < K) bounce(); return state(); }
    function state() { return { k, refl: { ...refl }, lamp, x: x.slice(), history: history.map(h => ({ ...h })) }; }
    reset();
    return {
      reset, bounce, advanceTo, state,
      setRefl(s, v) { const sc = { refl: { ...refl, [s]: v }, lamp }; reset(sc); },
      setLamp(i) { reset({ refl, lamp: i }); },
      get analysis() { return an; }, get k() { return k; }, get x() { return x; }, get history() { return history; },
    };
  }

  const api = { W, H, SEG, N, SURFACES, PATCHES, FF, DEFAULTS, matA, mulVec, supNorm, solve, spectral, certificate, analyse, create, emission };
  if (typeof module !== 'undefined') module.exports = api; else root.RoomModel = api;
})(typeof window !== 'undefined' ? window : globalThis);
