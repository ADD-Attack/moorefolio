// W-Ex11 page: draws the room model, runs the bounces, exposes everything on window.__ex11.
(function () {
  'use strict';
  const M = window.RoomModel, sim = M.create();
  const q = new URLSearchParams(location.search);
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let held = q.has('hold'), playing = !held && !reduced, timer = null;
  const MAX_K = 120, BOUNCE_MS = 380;

  const PRESETS = {
    default: { ...M.DEFAULTS.refl },
    edge: { floor: 1, right: 1, ceiling: 1, left: 1 },
    lopsided: { floor: 0.1, right: 1.45, ceiling: 0.1, left: 0.1 },
    runaway: { floor: 1.2, right: 1.2, ceiling: 1.2, left: 1.2 },
  };

  // ---------- room drawing ----------
  const cv = document.getElementById('room'), cx = cv.getContext('2d');
  const S = 108, OX = 48, OY = 30;
  const toPx = p => [OX + p[0] * S, OY + (M.H - p[1]) * S];
  const GW = 96, GH = 60, img = new ImageData(GW, GH), off = document.createElement('canvas');
  off.width = GW; off.height = GH;
  // angle each patch subtends at each interior sample point (picture only; not part of the model)
  const PHI = new Float32Array(GW * GH * M.N);
  for (let gy = 0; gy < GH; gy++) for (let gx = 0; gx < GW; gx++) {
    const px = (gx + .5) / GW * M.W, py = M.H - (gy + .5) / GH * M.H;
    for (let j = 0; j < M.N; j++) { const { a, b } = M.PATCHES[j];
      const ux = a[0] - px, uy = a[1] - py, vx = b[0] - px, vy = b[1] - py;
      PHI[(gy * GW + gx) * M.N + j] = Math.abs(Math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)); }
  }
  const tone = v => 1 - Math.exp(-2.2 * v);
  function warm(t) { // dark ink → amber → cream
    const c0 = [10, 11, 15], c1 = [190, 110, 30], c2 = [255, 226, 170];
    const m = t < .6 ? [c0, c1, t / .6] : [c1, c2, (t - .6) / .4];
    return m[0].map((c, i) => Math.round(c + (m[1][i] - c) * m[2]));
  }
  function drawRoom() {
    const x = sim.x, lamp = sim.state().lamp;
    let peak = 1;
    for (let i = 0; i < GW * GH; i++) { let s = 0; for (let j = 0; j < M.N; j++) s += x[j] * PHI[i * M.N + j];
      const c = warm(tone(s / Math.PI / 2 * 1.1 / peak)); img.data.set([c[0], c[1], c[2], 255], i * 4); }
    off.getContext('2d').putImageData(img, 0, 0);
    cx.fillStyle = '#08090c'; cx.fillRect(0, 0, cv.width, cv.height);
    cx.imageSmoothingEnabled = true; cx.drawImage(off, OX, OY, M.W * S, M.H * S);
    for (let j = 0; j < M.N; j++) { const { a, b } = M.PATCHES[j], A = toPx(a), B = toPx(b);
      const c = warm(tone(x[j] * .7)); cx.strokeStyle = `rgb(${c})`; cx.lineWidth = j === lamp ? 12 : 9; cx.lineCap = 'butt';
      cx.beginPath(); cx.moveTo(...A); cx.lineTo(...B); cx.stroke();
      cx.strokeStyle = '#08090c'; cx.lineWidth = 2; cx.beginPath(); cx.arc(...A, .5, 0, 7); cx.stroke(); }
    const { a, b } = M.PATCHES[lamp], A = toPx(a), B = toPx(b);
    cx.font = '600 14px ui-monospace, Consolas, monospace'; cx.textAlign = 'center';
    const LX = (A[0] + B[0]) / 2, LY = (A[1] + B[1]) / 2 + (M.PATCHES[lamp].s === 'floor' ? -12 : 22);
    cx.fillStyle = 'rgba(8,9,12,.85)'; cx.fillRect(LX - 24, LY - 14, 48, 20); cx.fillStyle = '#ffe9c2';
    cx.fillText('lamp', (A[0] + B[0]) / 2 + (lamp >= 13 && lamp < 21 ? 0 : 0), (A[1] + B[1]) / 2 + (M.PATCHES[lamp].s === 'floor' ? -12 : 22));
    cx.fillStyle = '#b3ad9f'; cx.font = '13px ui-monospace, Consolas, monospace';
    const rf = sim.state().refl;
    cx.fillText('floor ρ ' + rf.floor.toFixed(2), OX + M.W * S / 2, OY + M.H * S + 22);
    cx.fillText('ceiling ρ ' + rf.ceiling.toFixed(2), OX + M.W * S / 2, OY - 10);
    cx.save(); cx.translate(OX - 16, OY + M.H * S / 2); cx.rotate(-Math.PI / 2); cx.fillText('left ρ ' + rf.left.toFixed(2), 0, 0); cx.restore();
    cx.save(); cx.translate(OX + M.W * S + 22, OY + M.H * S / 2); cx.rotate(Math.PI / 2); cx.fillText('right ρ ' + rf.right.toFixed(2), 0, 0); cx.restore();
  }

  // ---------- chart ----------
  const ch = document.getElementById('chart'), cc = ch.getContext('2d');
  function drawChart() {
    const W = ch.width, H = ch.height, L = 52, R = 12, T = 12, B = 30, h = sim.history, an = sim.analysis;
    cc.fillStyle = '#1b1e27'; cc.fillRect(0, 0, W, H);
    const lo = -15, hi = 10, X = k => L + (k - 1) / (MAX_K - 1) * (W - L - R), Y = v => T + (hi - v) / (hi - lo) * (H - T - B);
    cc.strokeStyle = '#2c3140'; cc.fillStyle = '#b3ad9f'; cc.font = '12px ui-monospace, Consolas, monospace'; cc.lineWidth = 1;
    cc.textAlign = 'right';
    for (let e = lo; e <= hi; e += 5) { cc.beginPath(); cc.moveTo(L, Y(e)); cc.lineTo(W - R, Y(e)); cc.stroke(); cc.fillText('1e' + e, L - 6, Y(e) + 4); }
    cc.textAlign = 'center';
    for (let k = 1; k <= MAX_K; k += k === 1 ? 19 : 20) cc.fillText(k === 1 ? '1' : String(k), X(k), H - 10);
    // reference: slope log10 ρ per bounce, anchored at the measured value at bounce 10 (or the latest one)
    const anchor = h[Math.min(9, h.length - 1)];
    if (anchor && anchor.inc > 0) {
      const l = Math.log10(an.spectral.rho), y0 = Math.log10(anchor.inc) - l * (anchor.k);
      cc.setLineDash([5, 5]); cc.strokeStyle = '#ece7dc'; cc.beginPath();
      cc.moveTo(X(1), Y(y0 + l)); cc.lineTo(X(MAX_K), Y(y0 + l * MAX_K)); cc.stroke(); cc.setLineDash([]);
    }
    cc.save(); cc.beginPath(); cc.rect(L, T, W - L - R, H - T - B); cc.clip();
    cc.strokeStyle = '#ffb44a'; cc.lineWidth = 2.5; cc.beginPath();
    h.forEach((p, i) => { const y = Y(Math.log10(Math.max(p.inc, 1e-300))); i ? cc.lineTo(X(p.k), y) : cc.moveTo(X(p.k), y); }); cc.stroke();
    cc.restore();
  }

  // ---------- readouts ----------
  const $ = id => document.getElementById(id);
  const fx = (v, d = 4) => v == null || !isFinite(v) ? '—' : v.toFixed(d);
  const sci = v => v == null ? '—' : v === 0 ? '0' : v >= 1e4 || v < 1e-3 ? v.toExponential(2).replace('e', '×10^').replace('+', '') : v.toPrecision(3);
  function verdictA() {
    const h = sim.history, last = h[h.length - 1];
    if (!last || h.length < 8) return { s: 'wait', t: 'watching… (' + h.length + ' of 8 bounces)' };
    if (last.ratio == null) return { s: 'yes', t: 'settled to round-off at bounce ' + last.k };
    if (last.ratio < 0.9999) return { s: 'yes', t: 'each bounce adds ×' + last.ratio.toFixed(4) + ' of the last' };
    return { s: 'no', t: last.ratio < 1.0001 ? 'not shrinking: ×' + last.ratio.toFixed(4) + ' per bounce' : 'growing: ×' + last.ratio.toFixed(4) + ' per bounce' };
  }
  function readouts() {
    const st = sim.state(), h = st.history, last = h[h.length - 1], an = sim.analysis, c = an.certificate;
    const a = verdictA();
    return {
      k: String(st.k), inc: last ? sci(last.inc) : '—', ratio: last && last.ratio != null ? fx(last.ratio) : '—',
      rho: fx(an.spectral.rho), row: fx(an.maxRowSum, 2),
      a, b: { s: an.spectral.below1 ? 'yes' : 'no', t: 'ρ(A) = ' + fx(an.spectral.rho) + (an.spectral.below1 ? ' < 1' : Math.abs(an.spectral.rho - 1) < 1e-9 ? ', exactly the boundary' : ' > 1') },
      c: c.exists ? { s: 'yes', t: 'v = (I − A)⁻¹1 > 0, θ = ' + fx(c.theta) + ' < 1' } : { s: 'no', t: c.v ? 'no positive v: (I − A)⁻¹1 has a negative entry' : 'none: I − A cannot be inverted' },
    };
  }
  function render() {
    const r = readouts();
    $('r-k').textContent = r.k; $('r-inc').textContent = r.inc; $('r-ratio').textContent = r.ratio; $('r-rho').textContent = r.rho; $('r-row').textContent = r.row;
    for (const id of ['a', 'b', 'c']) { const el = $('v-' + id); el.className = 'v ' + r[id].s; $('v-' + id + '-t').textContent = r[id].t; }
    const rf = sim.state().refl;
    for (const s of M.SURFACES) { $('s-' + s).value = rf[s]; $('o-' + s).textContent = rf[s].toFixed(2); }
    $('b-play').textContent = playing ? 'Pause' : 'Play';
    drawRoom(); drawChart();
  }

  // ---------- loop ----------
  function tick() { if (!playing || held) return; if (sim.k < MAX_K) { sim.bounce(); render(); } else { playing = false; render(); } }
  function startLoop() { clearInterval(timer); timer = setInterval(tick, BOUNCE_MS); }
  function restart(fn) { fn(); if (reduced && !held) sim.advanceTo(40); render(); }

  $('b-play').onclick = () => { if (sim.k >= MAX_K) sim.advanceTo(0); playing = !playing; held = false; render(); };
  $('b-step').onclick = () => { playing = false; if (sim.k < MAX_K) sim.bounce(); render(); };
  $('b-reset').onclick = () => { restart(() => sim.reset()); };
  for (const s of M.SURFACES) $('s-' + s).oninput = e => restart(() => sim.setRefl(s, +(+e.target.value).toFixed(2)));
  document.querySelectorAll('[data-preset]').forEach(b => b.onclick = () => restart(() => sim.reset({ refl: PRESETS[b.dataset.preset], lamp: sim.state().lamp })));
  cv.addEventListener('click', ev => {
    const r = cv.getBoundingClientRect(), px = (ev.clientX - r.left) * cv.width / r.width, py = (ev.clientY - r.top) * cv.height / r.height;
    const mx = (px - OX) / S, my = M.H - (py - OY) / S; let best = -1, bd = 0.45;
    M.PATCHES.forEach((p, j) => { const c = [(p.a[0] + p.b[0]) / 2, (p.a[1] + p.b[1]) / 2], d = Math.max(Math.abs(c[0] - mx), Math.abs(c[1] - my)); if (d < bd) { bd = d; best = j; } });
    if (best >= 0) restart(() => sim.setLamp(best));
  });

  window.__ex11 = {
    model: M, sim, PRESETS,
    get state() { return sim.state(); }, get analysis() { const a = sim.analysis; return { spectral: a.spectral, certificate: { exists: a.certificate.exists, theta: a.certificate.theta, v: a.certificate.v }, maxRowSum: a.maxRowSum, exact: a.exact, A: a.A, e: a.e }; },
    get readouts() { return readouts(); },
    headline() { const m = M.create(); m.reset(); m.advanceTo(30); const r = m.history[29].ratio, rho = m.analysis.spectral.rho; return { bounce: 30, ratio: r, rho, gap: Math.abs(r - rho), tolerance: 1e-4, holds: Math.abs(r - rho) <= 1e-4 }; },
    advanceTo(k) { sim.advanceTo(Math.min(k, MAX_K)); render(); return sim.state(); },
    advanceFrames(n) { return this.advanceTo(sim.k + n); },
    hold(on = true) { held = on; if (on) playing = false; render(); },
    play() { held = false; playing = true; render(); },
    reset(scene) { sim.reset(scene); render(); return sim.state(); },
    preset(name) { sim.reset({ refl: PRESETS[name], lamp: sim.state().lamp }); render(); return sim.state(); },
    get reducedMotion() { return reduced; },
  };
  if (reduced && !held) sim.advanceTo(40);
  render(); startLoop();
})();
