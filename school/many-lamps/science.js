// W-Ex11-X2 — the radiosity programme's 2026-11-04 findings, as pure functions on one channel's (A, e).
// Additive: lamps-model.js / room-model.js are untouched; nothing here changes what the Jacobi sim computes.
// Arithmetic stays + − × ÷ (plus log only in the a-priori budget, a closed-form count) — lesson 22.
(function (root) {
  'use strict';
  const M = root.RoomModel || (typeof require !== 'undefined' ? require('./room-model.js') : null);
  const { N, PATCHES, SURFACES, mulVec, supNorm } = M;
  const TAU = 1e-3, CAP = 0.9;
  const PAD = 1e-12;                       // round-off pad on certified bounds, relative to the light's size (lesson 24)

  // §A.1 The certificate bracket — from the settled light v = (I − A)⁻¹𝟙. Certifies settling; does not estimate ρ.
  function certificateBracket(cert, A) {
    if (!cert || !cert.v || !cert.exists) return { lo: null, hi: null, theta: cert ? cert.theta : null, exists: false };
    const Av = mulVec(A, cert.v); let lo = Infinity, hi = 0;
    for (let i = 0; i < N; i++) { const q = Av[i] / cert.v[i]; lo = Math.min(lo, q); hi = Math.max(hi, q); }
    return { lo, hi, theta: cert.theta, exists: true };
  }

  // §A.2 + §B. From the latest bounce difference d_k = x_k − x_{k−1} and d_{k+1} = A d_k (one matvec, no advance):
  // m_k = min d_{k+1}/d_k, M_k = max d_{k+1}/d_k — the ρ estimate — and, when M_k < 1, the tail enclosure
  // x_k + m/(1−m)·d_k ≤ x* ≤ x_k + M/(1−M)·d_k (A ≥ 0, so m^j d_k ≤ A^j d_k ≤ M^j d_k).
  function differences(A, x, xPrev) {
    const d = x.map((t, i) => t - xPrev[i]), Ad = mulVec(A, d), scale = Math.max(supNorm(x), 1e-300);
    if (!(supNorm(d) > 1e-13 * scale)) return { lo: null, hi: null, state: 'roundoff', d };
    let lo = Infinity, hi = 0;
    for (let i = 0; i < N; i++) {
      if (d[i] > 0) { const q = Ad[i] / d[i]; lo = Math.min(lo, q); hi = Math.max(hi, q); }
      else if (Ad[i] > 0) hi = Infinity;   // light arriving where none arrived last bounce: no finite upper ratio yet
    }
    return { lo, hi, d };
  }
  function enclosure(A, x, xPrev) {
    const D = differences(A, x, xPrev), total = x.reduce((s, t) => s + t, 0);
    if (D.state === 'roundoff') return { available: true, lo: total, hi: total, width: 0, state: 'roundoff', m: null, M: null };
    const { lo: m, hi: Mx, d } = D;
    if (m >= 1) return { available: false, lo: null, hi: null, width: null, state: 'divergence', m, M: Mx };
    if (!(Mx < 1)) return { available: false, lo: null, hi: null, width: null, state: 'none', m, M: Mx };
    const a = m / (1 - m), b = Mx / (1 - Mx), pad = PAD * Math.max(1, supNorm(x));
    const loV = x.map((t, i) => t + a * d[i] - pad), hiV = x.map((t, i) => t + b * d[i] + pad);
    const lo = loV.reduce((s, t) => s + t, 0), hi = hiV.reduce((s, t) => s + t, 0);
    return { available: true, lo, hi, width: hi - lo, state: 'enclosed', m, M: Mx, loV, hiV };
  }

  // §C. The a-priori budget: rows of F sum to ≤ 1, so 𝟙 certifies with constant p_max and
  // ‖x* − x_k‖ shrinks like p_max^(k+1)/(1 − p_max). Smallest k with that ≤ τ. Any geometry, any coupling.
  function pMaxOf(surf, c) { let p = 0; for (const s of SURFACES) p = Math.max(p, surf[s].refl * surf[s].color[c]); return p; }
  function budget(pMax, tau = TAU) {
    if (!(pMax < 1)) return { pMax, tau, guaranteed: null };
    if (pMax <= 0) return { pMax, tau, guaranteed: 0 };
    let k = 0, t = pMax / (1 - pMax);                // t = p^(k+1)/(1−p), walked up k by k: the formula itself, no logs
    while (t > tau) { k++; t *= pMax; }
    return { pMax, tau, guaranteed: k };
  }
  // Measured: the first Jacobi bounce whose true error, relative to the emission's size, is ≤ τ.
  function needed(A, e, exact, tau = TAU, kmax = 2000) {
    if (!exact) return null;
    const s = Math.max(supNorm(e), 1e-300); let x = new Array(N).fill(0);
    for (let k = 1; k <= kmax; k++) { const Ax = mulVec(A, x); x = e.map((t, i) => t + Ax[i]);
      if (supNorm(x.map((t, i) => t - exact[i])) / s <= tau) return k; }
    return null;
  }

  // §D. Gauss–Seidel from darkness with a certified stop: r = e + A x̃ − x̃ (one extra matvec),
  // ‖x* − x̃‖∞ ≤ ‖r‖∞/(1 − c), c = max(A𝟙). Stop when that bound ≤ τ·‖e‖∞.
  function gsSweep(A, e, x) { for (let i = 0; i < N; i++) { let s = e[i]; const r = A[i]; for (let j = 0; j < N; j++) s += r[j] * x[j]; x[i] = s; } return x; }
  // (x[i] is overwritten in place while row i reads x: entries j < i are this sweep's, j ≥ i last sweep's — Gauss–Seidel.)
  function residualBound(A, e, x, c) {
    const Ax = mulVec(A, x), r = supNorm(x.map((t, i) => e[i] + Ax[i] - t));
    return c < 1 ? r / (1 - c) : null;
  }
  function gsRun(A, e, tau = TAU, maxSweeps = 500) {
    const c = A.reduce((m, row) => Math.max(m, row.reduce((s, t) => s + t, 0)), 0), s = Math.max(supNorm(e), 1e-300);
    if (!(c < 1)) return { sweeps: null, certifiedBound: null, tau, c, x: null, reason: 'c ≥ 1' };
    const x = new Array(N).fill(0);
    for (let k = 1; k <= maxSweeps; k++) { gsSweep(A, e, x); const b = residualBound(A, e, x, c);
      if (b <= tau * s) return { sweeps: k, certifiedBound: b, tau, c, x: x.slice() }; }
    return { sweeps: null, certifiedBound: residualBound(A, e, x, c), tau, c, x: x.slice(), reason: 'cap' };
  }

  // §E. The design-margin clamp: every channel's reflectivity refl × colour_c capped at CAP before the solve.
  // Returned as (refl', colour') with refl' × colour'_c = min(refl × colour_c, CAP).
  function clampSurfaces(surf, cap = CAP) {
    const out = {};
    for (const s of SURFACES) { const g = surf[s], p = [0, 1, 2].map(c => Math.min(g.refl * g.color[c], cap));
      if (p.every((t, c) => t === g.refl * g.color[c])) { out[s] = { refl: g.refl, color: g.color.slice() }; continue; }
      const r = Math.max(...p); out[s] = { refl: r, color: p.map(t => r > 0 ? t / r : 0) }; }
    return out;
  }

  // §F. The cluster certificate: the 4 surfaces as clusters, Q_IJ = max over i in I of Σ_{j in J} A_ij.
  // With x = 𝟙 this is a coarse certificate: ρ(A) ≤ ρ(Q). Q is 4×4 and ≥ 0; Collatz–Wielandt on Q + I.
  function clusterQ(A) {
    const idx = SURFACES.map(s => PATCHES.map((p, i) => p.s === s ? i : -1).filter(i => i >= 0));
    return idx.map(I => idx.map(J => I.reduce((m, i) => Math.max(m, J.reduce((t, j) => t + A[i][j], 0)), 0)));
  }
  function rho4(Q) {
    const n = Q.length; let v = new Array(n).fill(1), lo = 0, hi = 0;
    for (let it = 0; it < 20000; it++) {
      const Qv = Q.map(r => r.reduce((s, t, j) => s + t * v[j], 0)); lo = Infinity; hi = 0;
      for (let i = 0; i < n; i++) { const q = Qv[i] / v[i]; lo = Math.min(lo, q); hi = Math.max(hi, q); }
      if (hi - lo < 1e-14) break;
      const w = Qv.map((t, i) => t + v[i]), m = Math.max(...w); v = w.map(t => t / m);
    }
    return { rho: (lo + hi) / 2, lo, hi };
  }

  const api = { TAU, CAP, certificateBracket, differences, enclosure, pMaxOf, budget, needed, gsSweep, gsRun, residualBound, clampSurfaces, clusterQ, rho4 };
  if (typeof module !== 'undefined') module.exports = api; else root.Science = api;
})(typeof window !== 'undefined' ? window : globalThis);
