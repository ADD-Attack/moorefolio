// W-Ex11-X3 — Side by side: the traditional engine way vs the theorem-guided way, on the same room and lamps.
// Additive: room-model.js / lamps-model.js / science.js / motion.js / presets.js are the X2 files, byte-identical.
// Every number this module returns is counted while it is computed. Nothing here is typed in.
//
// Counting rule (frozen in the brief): one bounce or sweep of one channel on the dense N × N model = N² multiply-adds.
// Every N × N product is a call through mv(), gs() or res() below, and each of those adds exactly N² to its side's counter.
// Work both sides share (building the scene, the lamps' first-bounce distributions) is not counted for either.
// The direct solve (N³ by the rule) is the error reference only; it is counted separately and never added to a side.
(function (root) {
  'use strict';
  const LM = root.LampsModel || require('./lamps-model.js');
  const SC = root.Science || require('./science.js');
  const MO = root.Motion || require('./motion.js');
  const M = LM.room, N = M.N, PER = N * N;
  const now = () => (typeof performance !== 'undefined' ? performance.now() : Number(process.hrtime.bigint()) / 1e6);
  const DEF = { budget: 100, tau: 1e-3, ticks: 240, cap: MO.CAP_PER_FRAME, maxSweeps: 500 };

  function counter() { return { ops: 0 }; }
  const mv = (C, A, x) => { C.ops += PER; return M.mulVec(A, x); };                              // one Jacobi bounce's product
  const gs = (C, A, e, x) => { C.ops += PER; return SC.gsSweep(A, e, x); };                       // one Gauss–Seidel sweep
  const res = (C, A, e, x, c) => { C.ops += PER; return SC.residualBound(A, e, x, c); };          // the certificate: one product

  // Relative true error of one channel: ‖x − x*‖∞ / ‖e‖∞ (dark channels: 0 when x is dark too).
  function relErr(x, exact, e) { const s = M.supNorm(e); const d = M.supNorm(x.map((t, i) => t - exact[i])); return s > 0 ? d / s : d; }

  // ---- LEFT: traditional. Fixed budget, Jacobi, cold from darkness, stops when the budget runs out. ----
  function traditional(chans, budget, C, trace) {
    let xs = chans.map(() => new Array(N).fill(0)), prev = xs;
    for (let k = 0; k < budget; k++) {                     // bounce-major so a trace can record every bounce; same arithmetic per channel
      prev = xs; xs = chans.map((ch, c) => { const Ax = mv(C, ch.A, prev[c]); return ch.e.map((t, i) => t + Ax[i]); });
      if (trace) trace.push({ ops: C.ops, k: k + 1, x: xs });
    }
    // the only stop information it has: the last change (a subtraction, no product, no guarantee)
    const raw = budget > 0 ? Math.max(...xs.map((x, c) => M.supNorm(x.map((t, i) => t - prev[c][i])))) : null;
    return { x: xs, iters: budget, rawResidual: raw };
  }

  // ---- RIGHT: theorem-guided. Gauss–Seidel, warm start, certified stop: ‖r‖∞/(1 − c) ≤ τ‖e‖∞, c = max row sum of A. ----
  // Checks the certificate before the first sweep (a warm start may already be inside τ), then after every sweep.
  function guided(chans, x0, tau, cap, C, trace) {
    const xs = chans.map((ch, c) => x0 ? x0[c].slice() : new Array(N).fill(0)), sweeps = [], bounds = [];
    const snap = (c, k, b) => trace && trace.push({ ops: C.ops, c, k, bound: b, x: xs.map(v => v.slice()) });
    chans.forEach((ch, c) => {
      const x = xs[c], s = M.supNorm(ch.e), cc = ch.maxRowSum;
      let k = 0, b = res(C, ch.A, ch.e, x, cc);
      while (b != null && b > tau * s && k < cap) { gs(C, ch.A, ch.e, x); k++; b = res(C, ch.A, ch.e, x, cc); snap(c, k, s > 0 ? b / s : b); }
      sweeps.push(k); bounds.push(b == null ? null : s > 0 ? b / s : b);
    });
    return { x: xs, iters: Math.max(...sweeps), sweeps, bound: bounds.some(b => b == null) ? null : Math.max(...bounds) };
  }

  function errOf(chans, x) { return Math.max(...chans.map((ch, c) => ch.exact ? relErr(x[c], ch.exact, ch.e) : Infinity)); }
  function settledOK(chans) { return chans.every(ch => ch.exact && ch.maxRowSum < 1); }
  // Browsers round performance.now() (often to 0.1 ms), so time a batch: repeat until ≥ 25 ms have passed, report the mean per solve.
  function timeIt(fn) { let n = 0; const t0 = now(); do { fn(); n++; } while (now() - t0 < 25); return (now() - t0) / n; }

  // ---------------- Stationary: one scene edit, both sides solve the new scene to τ. ----------------
  // before / after: scenes (lamps-model scene objects). The guided side starts from ITS settled state of `before`
  // (certified to τ, that is what it had on screen). The traditional side starts from darkness, as engines do on any change.
  function stationary(before, after, o = {}) {
    const p = { ...DEF, ...o };
    const simB = LM.create(); simB.reset(before); const chB = simB.channels;
    const sim = LM.create(); sim.reset(after); const ch = sim.channels;
    if (!settledOK(ch)) return { ok: false, reason: 'a channel of this room has c ≥ 1 — no settled state to compare against' };
    const warm = guided(chB, null, p.tau, p.maxSweeps, counter()).x;            // the state the right side already shows
    const CL = counter(), CR = counter();
    const traceL = o.trace ? [] : null, traceR = o.trace ? [] : null;
    const L = traditional(ch, p.budget, CL, traceL);
    const R = guided(ch, warm, p.tau, p.maxSweeps, CR, traceR);
    // ρ and c per channel, as the shared model computed them for this room (Collatz–Wielandt bracket; cached per colouring,
    // built for both sides alike, so in neither total). The certified stop itself uses only c = max row sum.
    const rho = ch.map(c => c.spectral.rho), cmax = ch.map(c => c.maxRowSum);
    // Reference only, not a side: the budget Jacobi from darkness actually needed to reach τ (needs the exact answer to know).
    const needed = Math.max(...ch.map(c => SC.needed(c.A, c.e, c.exact, p.tau) || Infinity));
        const msL = timeIt(() => traditional(ch, p.budget, counter())), msR = timeIt(() => guided(ch, warm, p.tau, p.maxSweeps, counter()));
    const left = { iters: L.iters, ops: CL.ops, ms: msL, err: errOf(ch, L.x), rawResidual: L.rawResidual, x: L.x };
    const right = { iters: R.iters, sweeps: R.sweeps, ops: CR.ops, ms: msR, err: errOf(ch, R.x), bound: R.bound, rho, c: cmax, x: R.x };
    return { ok: true, left, right, warm, traceL, traceR, exact: ch.map(c => c.exact), scene: sim.scene(), lamps: sim.lamps, surfaces: sim.surfaces,
      pctIters: (left.iters - right.iters) / left.iters * 100, pctOps: (left.ops - right.ops) / left.ops * 100,
      jacobiNeeded: needed, neededOps: needed * PER * ch.length, bothWithinTau: left.err <= p.tau && right.err <= p.tau, tau: p.tau, budget: p.budget, directOps: N * N * N * ch.length };
  }

  // ---------------- Moving: T ticks of a preset's lamp motion. ----------------
  // LEFT re-solves every tick cold at the full budget. RIGHT warm-chases: at most `cap` GS sweeps per tick, certified stop.
  // Right enters the run settled at tick 0 (that solve is counted into its total). Errors are vs each tick's exact settled state.
  function moving(preset, o = {}) {
    const p = { ...DEF, ...o };
    const sim = LM.create(); sim.reset(preset);
    const motions = new Map(); sim.lamps.forEach((L, i) => { const m = preset.lamps[i] && preset.lamps[i].motion; if (m) motions.set(L.id, m); });
    const apply = t => { for (const [id, m] of motions) sim.setLamp(id, MO.poseAt(m, t)); };
    apply(0);
    if (!settledOK(sim.channels)) return { ok: false, reason: 'c ≥ 1' };
    const CL = counter(), CR = counter();
    let xr = guided(sim.channels, null, p.tau, p.maxSweeps, CR).x;
    const setupOps = CR.ops;
    const perTick = [];
    let msL = 0, msR = 0;
    for (let t = 1; t <= p.ticks; t++) {
      apply(t); const ch = sim.channels;
      let t0 = now(); const L = traditional(ch, p.budget, CL); msL += now() - t0;
      t0 = now(); const R = guided(ch, xr, p.tau, p.cap, CR); msR += now() - t0; xr = R.x;
      perTick.push({ t, errL: errOf(ch, L.x), errR: errOf(ch, R.x), boundR: R.bound, sweepsR: R.iters, opsL: CL.ops, opsR: CR.ops,
        xL: o.keepX ? L.x : null, xR: o.keepX ? R.x.map(v => v.slice()) : null, exact: o.keepX ? ch.map(c => c.exact) : null,
        lamps: o.keepX ? sim.lamps.map(Lp => ({ ...Lp })) : null });
    }
    const st = k => { const v = perTick.map(r => r[k]); return { max: Math.max(...v), mean: v.reduce((s, q) => s + q, 0) / v.length }; };
    const eL = st('errL'), eR = st('errR'), bR = st('boundR');
    const left = { opsTotal: CL.ops, errMax: eL.max, errMean: eL.mean, ms: msL, itersPerTick: p.budget };
    const right = { opsTotal: CR.ops, errMax: eR.max, errMean: eR.mean, ms: msR, setupOps, boundMax: bR.max, boundMean: bR.mean,
      sweepsMean: perTick.reduce((s, r) => s + r.sweepsR, 0) / perTick.length, ticksWithinTau: perTick.filter(r => r.boundR <= p.tau).length };
    return { ok: true, left, right, perTick, ticks: p.ticks, cap: p.cap, tau: p.tau, budget: p.budget,
      pctOps: (left.opsTotal - right.opsTotal) / left.opsTotal * 100 };
  }

  const api = { DEF, N, PER, traditional, guided, stationary, moving, relErr, counter };
  if (typeof module !== 'undefined') module.exports = api; else root.X3 = api;
})(typeof window !== 'undefined' ? window : globalThis);
