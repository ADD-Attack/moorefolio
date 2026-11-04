// W-Ex12 page. All numbers on screen are read from the model (ring-model.js); the closed form appears only as "predicts".
(function () {
  const $ = id => document.getElementById(id);
  const M = RingModel, model = M.create({ beta: 1, W: 4, c: 1 });
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const hold0 = /[?&]hold\b/.test(location.search);
  let running = false, probe = 0, buildMs = 0, acc = 0, last = 0;
  let shown = null;                         // displayed (tweened) beam state
  const fmt = (x, d = 4) => x === 0 ? '0' : Math.abs(x) >= 1e-3 && Math.abs(x) < 1e4 ? x.toFixed(d + 2).replace(/0+$/, '').replace(/\.$/, '') : x.toExponential(d).replace('e', '×10^').replace(/\^\+?(-?\d+)/, (_, e) => sup(e));
  const sup = e => [...e].map(ch => '⁰¹²³⁴⁵⁶⁷⁸⁹'['0123456789'.indexOf(ch)] ?? (ch === '-' ? '⁻' : ch)).join('');
  const cfgName = (s, W) => Array.from({ length: W }, (_, x) => (s >> x) & 1 ? 'T' : 'H').join('');

  function rebuild(p) { const t0 = performance.now(); model.set(p); buildMs = performance.now() - t0; probe &= model.n - 1; shown = null; render(); }

  // ---------- beam scene ----------
  const cv = $('beam'), g = cv.getContext('2d');
  function coinPos(W) { const cx = 480, cy = 160, R = W === 1 ? 0 : 92; return Array.from({ length: W }, (_, x) => { const a = -Math.PI / 2 + 2 * Math.PI * x / W; return [cx + R * Math.cos(a), cy + R * Math.sin(a)]; }); }
  function target() {
    const s = model.state(), v = s.v, n = model.n, par = model.parity; let E = 0, O = 0;
    for (let i = 0; i < n; i++) par[i] > 0 ? E += v[i] : O += v[i];
    return { q: s.q[s.t], bars: v.slice(), E: E / (E + O), O: O / (E + O) };
  }
  function drawBeam() {
    const tg = target();
    if (!shown || reduce || shown.bars.length !== tg.bars.length) shown = { q: tg.q, bars: tg.bars.slice() };
    else { shown.q += (tg.q - shown.q) * .25; shown.bars = shown.bars.map((b, i) => b + (tg.bars[i] - b) * .25); }
    const { W } = model.params, n = model.n, par = model.parity;
    g.clearRect(0, 0, 960, 560);
    // hidden ring τ: the variables summed over in the definition
    const P = coinPos(W);
    g.strokeStyle = '#3d4a46'; g.lineWidth = 2; g.setLineDash([5, 6]);
    g.beginPath(); if (W === 1) g.arc(480, 114, 26, .25 * Math.PI, .75 * Math.PI, true); else g.arc(480, 160, 92, 0, 2 * Math.PI); g.stroke(); g.setLineDash([]);
    g.fillStyle = '#aea999'; g.font = '14px ui-monospace, Consolas, monospace'; g.textAlign = 'center';
    g.fillText(W === 1 ? 'one coin, bonded to itself' : 'bonds between neighbours, summed over a hidden ring τ', 480, 296);
    P.forEach(([x, y], i) => {
      const tails = (probe >> i) & 1;
      g.beginPath(); g.arc(x, y, 25, 0, 2 * Math.PI); g.fillStyle = tails ? '#2c6f62' : '#a87d2c'; g.fill();
      g.lineWidth = 3; g.strokeStyle = tails ? '#5cc8b0' : '#e2b45a'; g.stroke();
      g.fillStyle = '#101413'; g.font = '700 20px Inter, system-ui, sans-serif'; g.textAlign = 'center'; g.fillText(tails ? 'T' : 'H', x, y + 7);
    });
    // beam
    const cx = 480, cy = 338, L = 300, ang = -shown.q * 0.30;   // even heavier → left end down
    const ex = Math.cos(ang) * L, ey = Math.sin(ang) * L;
    g.strokeStyle = '#ebe6da'; g.lineWidth = 5; g.beginPath(); g.moveTo(cx - ex, cy - ey); g.lineTo(cx + ex, cy + ey); g.stroke();
    g.fillStyle = '#ebe6da'; g.beginPath(); g.moveTo(cx, cy - 4); g.lineTo(cx - 16, cy + 26); g.lineTo(cx + 16, cy + 26); g.fill();
    const maxBar = Math.max(...shown.bars, 1e-300), half = n / 2;
    [[-1, 1, '#e2b45a', '#f3d796', 'EVEN', tg.E], [1, -1, '#5cc8b0', '#a6e6d6', 'ODD', tg.O]].forEach(([side, pv, col, col2, name, share]) => {
      const hx = cx + side * ex, hy = cy + side * ey, top = hy + 34, w = 250;
      g.strokeStyle = '#6d746f'; g.lineWidth = 1.5; g.beginPath(); g.moveTo(hx, hy); g.lineTo(hx - w / 2, top); g.moveTo(hx, hy); g.lineTo(hx + w / 2, top); g.stroke();
      g.fillStyle = col; g.fillRect(hx - w / 2, top, w, 4);
      const idx = []; for (let i = 0; i < n; i++) if (par[i] === pv) idx.push(i);
      const bw = w / half;
      idx.forEach((i, k) => { const h = 104 * shown.bars[i] / maxBar; g.fillStyle = i === probe ? '#ffffff' : col; g.fillRect(hx - w / 2 + k * bw + (bw > 3 ? 1 : 0), top + 4, Math.max(1, bw - (bw > 3 ? 2 : 0)), h); });
      g.fillStyle = col2; g.font = '600 15px ui-monospace, Consolas, monospace'; g.textAlign = 'center';
      g.fillText(`${name} · ${(share * 100).toFixed(share > .9995 || share < .0005 ? 0 : 1)}% of weight`, hx, top + 132);
    });
  }
  cv.addEventListener('click', e => {
    const r = cv.getBoundingClientRect(), x = (e.clientX - r.left) * 960 / r.width, y = (e.clientY - r.top) * 560 / r.height;
    coinPos(model.params.W).forEach(([px, py], i) => { if (Math.hypot(x - px, y - py) < 30) probe ^= 1 << i; });
    render();
  });

  // ---------- trace ----------
  const tc = $('trace'), h = tc.getContext('2d');
  function drawTrace() {
    const s = model.state(), pr = model.predicted, Wd = 620, Hd = 330, l0 = 52, r0 = 12, t0 = 12, b0 = 30;
    const cross = pr.crossing ? pr.crossing.step : 0;
    const xMax = Math.max(12, s.t + 1, cross <= 60 ? cross + 2 : 0), yMin = -16, yMax = 0.5;
    const X = t => l0 + (Wd - l0 - r0) * t / xMax, Y = lg => t0 + (Hd - t0 - b0) * (yMax - lg) / (yMax - yMin);
    h.clearRect(0, 0, Wd, Hd);
    h.fillStyle = '#26292e'; h.fillRect(l0, Y(-13), Wd - l0 - r0, Y(yMin) - Y(-13));
    h.fillStyle = '#1d2422'; h.fillRect(l0, Y(-8), Wd - l0 - r0, Y(-13) - Y(-8));
    h.font = '12px ui-monospace, Consolas, monospace'; h.textAlign = 'left';
    h.fillStyle = '#b9bcc1'; h.fillText('round-off floor · not physics', l0 + 8, Y(-14.2));
    h.fillStyle = '#aea999'; h.fillText('lean measured; shrink factor noisy here', l0 + 8, Y(-10.8));
    h.strokeStyle = '#2b3633'; h.lineWidth = 1; h.textAlign = 'right';
    for (let e = 0; e >= yMin; e -= 3) { h.beginPath(); h.moveTo(l0, Y(e)); h.lineTo(Wd - r0, Y(e)); h.stroke(); h.fillStyle = '#aea999'; h.fillText(e === 0 ? '1' : '10' + sup(String(e)), l0 - 6, Y(e) + 4); }
    h.strokeStyle = '#ebe6da'; h.setLineDash([3, 4]); h.beginPath(); h.moveTo(l0, Y(-3)); h.lineTo(Wd - r0, Y(-3)); h.stroke(); h.setLineDash([]);
    h.textAlign = 'right'; h.fillStyle = '#ebe6da'; h.fillText('threshold 10⁻³', Wd - r0 - 4, Y(-3) - 6);
    h.textAlign = 'center'; h.fillStyle = '#aea999'; const tick = Math.max(1, Math.ceil(xMax / 10 / 5) * 5 >= 5 && xMax > 30 ? Math.ceil(xMax / 10 / 5) * 5 : 2);
    for (let t = 0; t <= xMax; t += tick) h.fillText(t, X(t), Hd - b0 + 16);
    h.fillText('step', Wd - r0 - 16, Hd - 2); h.save(); h.translate(12, Hd / 2); h.rotate(-Math.PI / 2); h.fillText('|parity lean|', 0, 0); h.restore();
    if (model.params.c !== 0 && pr.ratio > 0) {             // the theorem's line: prediction only
      const lc = Math.log10(Math.abs(model.params.c)), lr = Math.log10(pr.ratio);
      const tEnd = Math.min(xMax, (yMin - lc) / lr);
      h.strokeStyle = '#5cc8b0'; h.lineWidth = 2; h.setLineDash([7, 5]); h.beginPath(); h.moveTo(X(0), Y(lc)); h.lineTo(X(tEnd), Y(lc + lr * tEnd)); h.stroke(); h.setLineDash([]);
    }
    const every = Math.max(1, Math.ceil(s.q.length / 300));
    s.q.forEach((q, t) => { if (t % every && t !== s.t) return; const a = Math.abs(q); if (!(a > 0)) return; const lg = Math.max(yMin, Math.log10(a));
      h.fillStyle = s.floor[t] ? '#7d8086' : '#e2b45a'; h.beginPath(); h.arc(X(t), Y(lg), t === s.t ? 5 : 3.5, 0, 2 * Math.PI); h.fill(); });
    if (s.measuredCrossing !== null) { h.strokeStyle = '#f3d796'; h.lineWidth = 2; h.beginPath(); h.arc(X(s.measuredCrossing), Y(Math.log10(Math.abs(s.q[s.measuredCrossing]))), 9, 0, 2 * Math.PI); h.stroke(); }
  }

  // ---------- readouts ----------
  const ro = {};
  function readouts() {
    const s = model.state(), pr = model.predicted, ch = model.checks, { beta, W, c } = model.params, i = s.t;
    ro.t = String(i); ro.q = s.floor[i] ? 'below 10⁻¹³ (round-off)' : fmt(s.q[i], 6);
    ro.meas = i === 0 ? '— step to measure' : s.trust[i] === 'exact' ? s.ratio[i].toFixed(12) : s.trust[i] === 'noisy' ? s.ratio[i].toFixed(6) + ' · noisy' : '— at the floor';
    ro.measTrust = s.trust[i] || 'none';
    ro.pred = pr.ratio.toFixed(12);
    ro.cross = c === 0 ? 'never: no lean' : s.measuredCrossing !== null ? 'step ' + s.measuredCrossing : `not yet (step ${i})`;
    ro.crossP = !pr.crossing ? '—' : pr.crossing.step > M.STEP_CAP ? `step ${pr.crossing.step.toLocaleString('en-US')} · past the ${M.STEP_CAP.toLocaleString('en-US')}-step cap` : 'step ' + pr.crossing.step;
    ro.floor = s.atFloor ? 'Below 10⁻¹³ the lean is round-off. The run stops here; further steps are greyed.' : s.capped ? `Step cap reached (${M.STEP_CAP}).` : pr.floorStep && pr.floorStep <= M.STEP_CAP ? `Round-off floor expected near step ${pr.floorStep}.` : '';
    const n = model.n; ro.build = `${n} × ${n} entries · ${(n * n * n).toLocaleString('en-US')} τ-terms · ${buildMs < 1 ? '<1' : buildMs.toFixed(0)} ms`;
    ro.closed = `${ch.closedMaxRelDiff.toExponential(1)} relative (${ch.closedMaxAbsDiff.toExponential(1)} absolute)`;
    ro.one = ch.residualOne.toExponential(1); ro.par = ch.residualPar.toExponential(1);
    ro.rl = `${fmt(pr.r, 4)} · ${fmt(pr.l, 4)}`;
    ro.note = W === 1 ? 'W = 1: a single coin whose neighbour is itself, a self-bond. The formula still holds.' : c === 0 ? 'c = 0: no starting lean, so there is nothing to forget. q stays 0.' : beta >= 2.5 ? 'Large β: each step keeps almost all of the lean, so this runs long.' : '';
    const pv = model.v, sum = pv.reduce((a, b) => a + b, 0);
    ro.probe = `Configuration ${cfgName(probe, W)} · ${model.parity[probe] > 0 ? 'even' : 'odd'} · ${(100 * pv[probe] / sum).toFixed(3)}% of the weight now (white bar). Click a coin to flip it.`;
  }
  function render() {
    readouts();
    $('r-t').textContent = ro.t; $('r-q').textContent = ro.q; $('r-meas').textContent = ro.meas; $('r-pred').textContent = ro.pred;
    $('r-meas').className = ro.measTrust === 'exact' ? '' : 'noisy';
    $('r-cross').textContent = ro.cross; $('r-cross-p').textContent = ro.crossP; $('r-floor').textContent = ro.floor;
    $('c-build').textContent = ro.build; $('c-closed').textContent = ro.closed; $('c-one').textContent = ro.one; $('c-par').textContent = ro.par; $('c-rl').textContent = ro.rl;
    $('note').textContent = ro.note; $('probe').textContent = ro.probe;
    document.querySelectorAll('.W').forEach(e => e.textContent = model.params.W);
    $('b-run').textContent = running ? 'Pause' : 'Run';
    drawBeam(); drawTrace();
  }

  // ---------- run loop ----------
  function rate() { const f = model.predicted.floorStep; return f && f > 40 ? Math.min(400, f / 20) : 2.5; }   // steps per second
  function frame(now) {
    if (running) {
      acc += Math.min(.25, (now - (last || now)) / 1000) * rate(); last = now;
      let k = 0; while (acc >= 1 && k < 50) { acc--; k++; if (model.state().atFloor || !model.step()) { running = false; break; } }
      if (model.state().atFloor) running = false;
      render();
    } else if (shown && !reduce) drawBeam();
    requestAnimationFrame(frame);
  }
  function setRun(on) { running = on && !model.state().atFloor; acc = 0; last = 0; render(); }

  // ---------- controls ----------
  const sync = () => { const { beta, W, c } = model.params; $('s-beta').value = beta; $('s-W').value = W; $('s-c').value = c;
    $('o-beta').textContent = beta.toFixed(2); $('o-W').textContent = W; $('o-c').textContent = c.toFixed(2); };
  let pend = null;
  const queue = p => { pend = { ...(pend || {}), ...p }; requestAnimationFrame(() => { if (pend) { const q = pend; pend = null; rebuild(q); sync(); } }); };
  $('s-beta').addEventListener('input', e => { $('o-beta').textContent = (+e.target.value).toFixed(2); queue({ beta: +e.target.value }); });
  $('s-c').addEventListener('input', e => { $('o-c').textContent = (+e.target.value).toFixed(2); queue({ c: +e.target.value }); });
  $('s-W').addEventListener('input', e => { $('o-W').textContent = e.target.value; queue({ W: +e.target.value }); });
  $('b-step').addEventListener('click', () => { running = false; model.step(); render(); });
  $('b-run').addEventListener('click', () => setRun(!running));
  $('b-reset').addEventListener('click', () => { running = false; model.reset(); shown = null; render(); });
  document.querySelectorAll('[data-p]').forEach(b => b.addEventListener('click', () => { const [beta, W, c] = b.dataset.p.split(',').map(Number); running = false; rebuild({ beta, W, c }); sync(); }));

  window.__ex12 = {
    model, get T() { return model.T; }, get v() { return model.v; }, get n() { return model.n; }, get parity() { return model.parity; },
    get params() { return model.params; }, get predicted() { return model.predicted; }, get checks() { return model.checks; },
    get state() { return model.state(); }, get history() { const s = model.state(); return { q: s.q, ratio: s.ratio, trust: s.trust, floor: s.floor }; },
    get readouts() { readouts(); return { ...ro }; },
    step() { running = false; const ok = model.step(); render(); return ok; },
    advanceTo(k) { running = false; const s = model.advanceTo(k); shown = null; render(); return s; },
    reset() { running = false; model.reset(); shown = null; render(); return model.state(); },
    set(p) { running = false; rebuild(p); sync(); return model.params; },
    hold(on = true) { if (on) running = false; render(); }, run() { setRun(true); },
    FLOOR: M.FLOOR, RATIO_TRUST: M.RATIO_TRUST, THRESHOLD: M.THRESHOLD, STEP_CAP: M.STEP_CAP
  };
  rebuild({}); sync();
  if (!hold0 && !reduce) setRun(true);
  requestAnimationFrame(frame);
})();
