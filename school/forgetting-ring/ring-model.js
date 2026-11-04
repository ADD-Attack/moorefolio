// W-Ex12 ring model. T is built by brute force from its DEFINITION (the τ-sum, Einstein's
// Lean def YM.Z2.T). q_t and every measured ratio come from iterating that T.
// The closed form (T_closed) and the spectrum (T_spectrum) are used for PREDICTIONS and CHECKS only.
// Encoding: configuration index s, bit x = 1 means coin x is tails (σ_x = −1).
(function (root) {
  const FLOOR = 1e-13;          // below this |q_t| is round-off, not the theorem (his construction note)
  const RATIO_TRUST = 1e-8;     // below this |q_t| the ratio can drift > 1e-6 by round-off (sweep, 2000 steps: worst 3.8e-7 above it); shown as noisy
  const THRESHOLD = 1e-3;       // crossing threshold (his instance)
  const STEP_CAP = 5000;        // large β decays very slowly; the run stops here
  const popcount = n => { let k = 0; for (; n; n &= n - 1) k++; return k; };

  // T(σ,σ') = Σ_τ exp(β · Σ_x σ_x σ'_x τ_x τ_{x+1}), x+1 mod W. Every entry, every τ.
  function buildT(beta, W) {
    const n = 1 << W, T = new Float64Array(n * n), mask = n - 1;
    const expOf = new Float64Array(2 * W + 1);           // exp(β·k) for the integer exponent sum k ∈ [−W, W]
    for (let k = -W; k <= W; k++) expOf[k + W] = Math.exp(beta * k);
    for (let s = 0; s < n; s++) for (let s2 = 0; s2 < n; s2++) {
      const u = s ^ s2;                                  // bit x set ⇔ σ_x σ'_x = −1
      let sum = 0;
      for (let t = 0; t < n; t++) {
        const tNext = ((t >>> 1) | ((t & 1) << (W - 1))) & mask;   // bit x = τ_{x+1}; W = 1 gives τ_0 (self-bond)
        const minus = popcount(u ^ t ^ tNext);           // sites where σσ'ττ' = −1
        sum += expOf[(W - 2 * minus) + W];
      }
      T[s * n + s2] = sum;
    }
    return T;
  }

  const closedEntry = (beta, W, s, s2) =>
    Math.pow(2 * Math.cosh(beta), W) + Math.pow(2 * Math.sinh(beta), W) * (popcount(s ^ s2) & 1 ? -1 : 1);

  function create(opts = {}) {
    let beta = opts.beta ?? 1, W = opts.W ?? 4, c = opts.c ?? 1;
    let n, T, par, v, t, q, ratio, checks, pred;

    const mul = x => { const y = new Float64Array(n); for (let i = 0; i < n; i++) { let s = 0; const o = i * n; for (let j = 0; j < n; j++) s += T[o + j] * x[j]; y[i] = s; } return y; };
    const qOf = x => { let a = 0, b = 0; for (let i = 0; i < n; i++) { a += par[i] * x[i]; b += x[i]; } return a / b; };

    function rebuild() {
      if (!(beta > 0)) throw new Error('β must be > 0 (theorem hypothesis)');
      n = 1 << W; T = buildT(beta, W);
      par = new Float64Array(n); for (let i = 0; i < n; i++) par[i] = popcount(i) & 1 ? -1 : 1;
      const r = Math.pow(4 * Math.cosh(beta), W), l = Math.pow(4 * Math.sinh(beta), W);
      const tw = Math.pow(Math.tanh(beta), W);
      // predictions (closed form), never fed back into the iteration
      const tStar = predictCrossing(c, tw);
      pred = { r, l, ratio: tw, mass: W * Math.log(1 / Math.tanh(beta)), crossing: tStar,
        floorStep: tw < 1 && c !== 0 ? Math.ceil(Math.log(FLOOR / Math.abs(c)) / Math.log(tw)) : null };
      // checks: brute-force T vs closed form; eigen-residuals of 𝟙 and p
      let maxAbs = 0, maxEntry = 0;
      for (let s = 0; s < n; s++) for (let s2 = 0; s2 < n; s2++) {
        const e = T[s * n + s2]; maxEntry = Math.max(maxEntry, Math.abs(e));
        maxAbs = Math.max(maxAbs, Math.abs(e - closedEntry(beta, W, s, s2))); }
      const one = new Float64Array(n).fill(1), T1 = mul(one), Tp = mul(par);
      let res1 = 0, resP = 0;
      for (let i = 0; i < n; i++) { res1 = Math.max(res1, Math.abs(T1[i] - r)); resP = Math.max(resP, Math.abs(Tp[i] - l * par[i])); }
      // residuals relative to ‖T‖∞ = r (gated); resP / l also kept: it grows when l ≪ r (small β, wide ring)
      checks = { closedMaxAbsDiff: maxAbs, closedMaxRelDiff: maxAbs / maxEntry, maxEntry,
        residualOne: res1 / r, residualPar: resP / r, residualParOverL: resP / l };
      reset();
    }
    function predictCrossing(c, tw) {
      if (c === 0 || !(tw < 1)) return null;
      if (Math.abs(c) < THRESHOLD) return 0;
      // smallest t with |c|·tw^t < thr, in log space; bracket against the knife-edge (W-Ex11 lesson 24)
      const x = Math.log(THRESHOLD / Math.abs(c)) / Math.log(tw);
      let k = Math.ceil(x); if (Math.abs(x - Math.round(x)) < 1e-9) k = Math.round(x) + (Math.abs(c) * Math.pow(tw, Math.round(x)) < THRESHOLD ? 0 : 1);
      return { step: k, knifeEdge: Math.abs(x - Math.round(x)) < 1e-9 };
    }
    function reset() {
      v = new Float64Array(n); for (let i = 0; i < n; i++) v[i] = 1 + c * par[i];
      t = 0; q = [qOf(v)]; ratio = [null];
    }
    function step() {
      if (t >= STEP_CAP) return false;
      const w = mul(v); let m = 0; for (let i = 0; i < n; i++) m = Math.max(m, Math.abs(w[i]));
      for (let i = 0; i < n; i++) w[i] /= m;
      v = w; t++; const qt = qOf(v); q.push(qt);
      const prev = q[t - 1];
      ratio.push(prev !== 0 && Math.abs(prev) >= FLOOR && Math.abs(qt) >= FLOOR ? qt / prev : null);  // no ratio is read off the floor
      return true;
    }
    const advanceTo = k => { if (k < t) reset(); while (t < k && step()); return state(); };
    const measuredCrossing = () => { for (let i = 0; i < q.length; i++) if (Math.abs(q[i]) < THRESHOLD) return i; return null; };
    const belowFloor = i => Math.abs(q[i]) < FLOOR;
    function state() {
      const trust = ratio.map((x, i) => x === null ? (i && belowFloor(i) ? 'floor' : null) : Math.abs(q[i]) >= RATIO_TRUST && Math.abs(q[i - 1]) >= RATIO_TRUST ? 'exact' : 'noisy');
      return { beta, W, c, t, v: Array.from(v), q: q.slice(), ratio: ratio.slice(), trust,
        floor: q.map((_, i) => belowFloor(i)), measuredCrossing: measuredCrossing(), atFloor: belowFloor(t), capped: t >= STEP_CAP };
    }
    function set(p) {
      if (p.beta !== undefined) beta = Math.min(5, Math.max(0.05, +p.beta));
      if (p.W !== undefined) W = Math.min(8, Math.max(1, Math.round(+p.W)));
      if (p.c !== undefined) c = Math.min(1, Math.max(-1, +p.c));
      rebuild();
    }
    rebuild();
    return { step, advanceTo, reset, set, state,
      get T() { return T; }, get n() { return n; }, get v() { return v; }, get parity() { return par; },
      get params() { return { beta, W, c }; }, get predicted() { return pred; }, get checks() { return checks; },
      mul: x => mul(Float64Array.from(x)), FLOOR, RATIO_TRUST, THRESHOLD, STEP_CAP };
  }
  const api = { create, buildT, closedEntry, popcount, FLOOR, RATIO_TRUST, THRESHOLD, STEP_CAP };
  if (typeof module !== 'undefined') module.exports = api; else root.RingModel = api;
})(typeof window !== 'undefined' ? window : globalThis);
