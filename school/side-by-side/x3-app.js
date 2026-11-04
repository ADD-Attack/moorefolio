// W-Ex11-X3 page: two rooms, one race. All numbers come from x3-engine.js counters; window.__x3 exposes them raw.
(function () {
  'use strict';
  const X3 = window.X3, LM = window.LampsModel, M = LM.room, MO = window.Motion, PRESETS = window.LAMP_PRESETS;
  const $ = id => document.getElementById(id);
  const q = new URLSearchParams(location.search);
  const still = q.has('qa') || matchMedia('(prefers-reduced-motion: reduce)').matches;
  const clone = o => JSON.parse(JSON.stringify(o));
  const fmt = n => Math.round(n).toLocaleString('en-US');
  const sci = v => v == null ? '—' : v === 0 ? '0' : !isFinite(v) ? '∞' : v.toExponential(1).replace(/e([+-])(\d+)/, (m, s, d) => ' × 10' + sup((s === '-' ? '-' : '') + d));
  const sup = s => s.split('').map(ch => '⁰¹²³⁴⁵⁶⁷⁸⁹'['0123456789'.indexOf(ch)] || (ch === '-' ? '⁻' : ch)).join('');
  const pct = v => (v >= 0 ? '' : '+') + Math.abs(v).toFixed(1) + '%';

  // ---------------- drawing (picture only; the log mapping of many-lamps, white point shared by both rooms) ----------------
  const S = 72, OX = 32, OY = 20, GW = 64, GH = 40, K = 8, LK = Math.log1p(K), GLOW_CAP = 0.4;
  const toPx = p => [OX + p[0] * S, OY + (M.H - p[1]) * S];
  const toM = (px, py) => [(px - OX) / S, M.H - (py - OY) / S];
  const curve = t => Math.log1p(K * Math.min(1, Math.max(0, t))) / LK;
  const shade = t => Math.round(9 + (255 - 9) * curve(t));
  const rgbCss = (c, a = 1) => `rgba(${c.map(v => Math.round(Math.min(1, Math.max(0, v)) * 255)).join(',')},${a})`;
  const PHI = new Float32Array(GW * GH * M.N);
  for (let gy = 0; gy < GH; gy++) for (let gx = 0; gx < GW; gx++) {
    const px = (gx + .5) / GW * M.W, py = M.H - (gy + .5) / GH * M.H;
    for (let j = 0; j < M.N; j++) { const { a, b } = M.PATCHES[j], ux = a[0] - px, uy = a[1] - py, vx = b[0] - px, vy = b[1] - py;
      PHI[(gy * GW + gx) * M.N + j] = Math.abs(Math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)); }
  }
  function whiteOf(X, lamps) {
    const lp = new Set(lamps.filter(L => L.type === 'panel').map(L => L.patch)); let w = 0;
    for (let c = 0; c < 3; c++) for (let j = 0; j < M.N; j++) if (!lp.has(j)) w = Math.max(w, X[c][j]);
    return w > 0 ? w : 1;
  }
  const rooms = ['l', 'r'].map(s => { const cv = $('room-' + s), off = document.createElement('canvas'); off.width = GW; off.height = GH;
    return { cv, cx: cv.getContext('2d'), off, img: new ImageData(GW, GH) }; });
  function draw(R, X, lamps, white, glowMax) {
    const { cx, off, img } = R, ex = 1 / white, gk = 1 / glowMax;
    for (let i = 0; i < GW * GH; i++) { const o = i * M.N;
      for (let c = 0; c < 3; c++) { let s = 0; const x = X[c]; for (let j = 0; j < M.N; j++) s += x[j] * PHI[o + j];
        img.data[i * 4 + c] = Math.round(9 + (255 - 9) * GLOW_CAP * curve(s * gk)); }
      img.data[i * 4 + 3] = 255; }
    off.getContext('2d').putImageData(img, 0, 0);
    cx.fillStyle = '#08090c'; cx.fillRect(0, 0, R.cv.width, R.cv.height);
    cx.imageSmoothingEnabled = true; cx.drawImage(off, OX, OY, M.W * S, M.H * S);
    for (const L of lamps) { const P = toPx(L.pos);
      if (L.type === 'spotlight') { cx.fillStyle = rgbCss(L.color, 0.14); cx.beginPath(); cx.moveTo(...P); cx.arc(P[0], P[1], 1.6 * S, -(L.aim + LM.SPOT_HALF), -(L.aim - LM.SPOT_HALF)); cx.closePath(); cx.fill(); }
      else if (L.type === 'laser') { const E = toPx(LM.beamEnd(L)); cx.strokeStyle = rgbCss(L.color, 0.9); cx.lineWidth = 2; cx.beginPath(); cx.moveTo(...P); cx.lineTo(...E); cx.stroke(); } }
    const panels = new Set(lamps.filter(L => L.type === 'panel').map(L => L.patch));
    for (let j = 0; j < M.N; j++) { const { a, b } = M.PATCHES[j];
      cx.strokeStyle = `rgb(${[0, 1, 2].map(c => shade(X[c][j] * ex)).join(',')})`; cx.lineWidth = panels.has(j) ? 15 : 11; cx.lineCap = 'butt';
      cx.beginPath(); cx.moveTo(...toPx(a)); cx.lineTo(...toPx(b)); cx.stroke(); }
    for (const L of lamps) { if (L.type === 'panel') continue; const P = toPx(L.pos);
      cx.fillStyle = rgbCss(L.color); cx.strokeStyle = '#08090c'; cx.lineWidth = 2; cx.beginPath();
      if (L.type === 'bulb') cx.arc(P[0], P[1], 7, 0, 7); else cx.rect(P[0] - 5, P[1] - 5, 10, 10); cx.fill(); cx.stroke(); }
  }
  function glowMaxOf(X) { let m = 0; for (let i = 0; i < GW * GH; i += 7) { const o = i * M.N; for (let c = 0; c < 3; c++) { let s = 0; for (let j = 0; j < M.N; j++) s += X[c][j] * PHI[o + j]; m = Math.max(m, s); } } return m || 1; }
  function stamp(R, text, ok) { const { cx } = R; cx.font = '600 22px Inter, Segoe UI, system-ui, sans-serif';
    const w = cx.measureText(text).width + 24; cx.fillStyle = ok ? 'rgba(18,40,26,.92)' : 'rgba(40,24,18,.92)';
    cx.fillRect(OX + 12, OY + 12, w, 36); cx.fillStyle = ok ? '#7fd99a' : '#ffcf8a'; cx.fillText(text, OX + 24, OY + 37); }

  // ---------------- state ----------------
  const P = { budget: 100, ticks: 240, cap: MO.CAP_PER_FRAME, tau: X3.DEF.tau };
  let scenario = 'still', editKind = 'move', cur = clone(MO.EXTRAVAGANZA), lastStill = null, lastMove = null, anim = null, lastBefore = null;
  const sceneOf = s => { const sim = LM.create(); sim.reset(s); return sim.scene(); };
  cur = sceneOf(cur);

  function nextScene(kind, from) {
    const s = clone(from);
    if (kind === 'original') return sceneOf(PRESETS.original);
    if (kind === 'extravaganza') return sceneOf(MO.EXTRAVAGANZA);
    if (kind === 'paint') { const g = s.surfaces.left, green = g.color[1] > 0.9; s.surfaces.left = green ? { refl: 0.9, color: [1, 0.12, 0.3] } : { refl: 0.9, color: [0.2, 1, 0.4] }; return s; }
    const L = s.lamps[0];
    if (L.type === 'panel') L.patch = L.patch === 16 ? 13 : 16;
    else L.pos = Math.abs(L.pos[0] - 5) < 1e-9 && Math.abs(L.pos[1] - 3.4) < 1e-9 ? [6.6, 2.5] : [5, 3.4];
    return s;
  }

  // ---------------- runs ----------------
  function runStill(next, before = cur) {
    const r = X3.stationary(before, next, { budget: P.budget, tau: P.tau, trace: true });
    if (!r.ok) { $('why').textContent = r.reason; return; }
    lastBefore = before; cur = next; lastStill = r; scenario = 'still'; expose(); tables(); headline();
    const white = whiteOf(r.exact, r.lamps), gm = glowMaxOf(r.exact);
    const total = r.left.ops, F = still ? 1 : 150; let f = 0;
    const pick = (tr, clock) => { let e = null; for (const t of tr) { if (t.ops <= clock) e = t; else break; } return e; };
    cancelAnim();
    const step = () => {
      f++; const clock = total * Math.min(1, f / F);
      const eL = pick(r.traceL, clock), eR = pick(r.traceR, clock), doneR = clock >= r.right.ops, doneL = f >= F;
      draw(rooms[0], eL ? eL.x : [0, 1, 2].map(() => new Array(M.N).fill(0)), r.lamps, white, gm);
      draw(rooms[1], doneR ? r.right.x : eR ? eR.x : r.warm, r.lamps, white, gm);
      const opsL = eL ? eL.ops : 0, opsR = doneR ? r.right.ops : eR ? eR.ops : 0;
      meters(opsL, opsR, total);
      $('state-l').innerHTML = doneL ? `Budget spent: <b>${r.left.iters}</b> bounces. Last change ${sci(r.left.rawResidual)}. No guarantee attached.` : `Bounce <b>${eL ? eL.k : 0}</b> of ${r.left.iters}, from darkness`;
      $('state-r').innerHTML = doneR ? `<span class="ok">Certified ✓</span> error ≤ ${sci(r.right.bound)} after <b>${r.right.iters}</b> sweeps, from the light already there` : `Sweeping colour ${eR ? 'RGB'[eR.c] : 'R'}, from the light already there`;
      if (doneR) stamp(rooms[1], 'Certified ✓  done', true);
      if (doneL) stamp(rooms[0], 'Budget spent', false);
      if (!doneL) anim = requestAnimationFrame(step); else anim = null;
    };
    step();
  }

  function runMove() {
    cancelAnim();
    const t0 = performance.now();
    const r = X3.moving(MO.EXTRAVAGANZA, { budget: P.budget, ticks: P.ticks, cap: P.cap, tau: P.tau, keepX: true });
    r.wallMs = performance.now() - t0;
    lastMove = r; scenario = 'move'; expose(); tables(); headline();
    const T = r.perTick.length; let i = still ? T - 1 : 0;
    const step = () => {
      const row = r.perTick[i], white = whiteOf(row.exact, row.lamps), gm = glowMaxOf(row.exact);
      draw(rooms[0], row.xL, row.lamps, white, gm); draw(rooms[1], row.xR, row.lamps, white, gm);
      meters(row.opsL, row.opsR, r.left.opsTotal);
      $('state-l').innerHTML = `Tick <b>${row.t}</b>/${T}: cold re-solve, ${r.budget} bounces. Error ${sci(row.errL)}`;
      $('state-r').innerHTML = `Tick <b>${row.t}</b>/${T}: ${row.sweepsR} warm sweep${row.sweepsR === 1 ? '' : 's'}. <span class="${row.boundR <= r.tau ? 'ok' : 'warn'}">Certified ≤ ${sci(row.boundR)}</span>`;
      chart(r, i);
      if (++i < T) anim = requestAnimationFrame(step); else anim = null;
    };
    step();
  }
  function cancelAnim() { if (anim) cancelAnimationFrame(anim); anim = null; }
  function meters(a, b, total) { $('ops-l').textContent = fmt(a); $('ops-r').textContent = fmt(b);
    $('bar-l').style.width = (100 * a / total) + '%'; $('bar-r').style.width = (100 * b / total) + '%'; }

  // ---------------- headline + receipts ----------------
  function headline() {
    if (scenario === 'still' && lastStill) { const r = lastStill;
      $('pct-ops').textContent = pct(r.pctOps); $('pct-ops-l').textContent = r.pctOps >= 0 ? 'fewer calculations' : 'more calculations';
      $('pct-it').textContent = pct(r.pctIters); $('pct-it-l').textContent = (r.pctIters >= 0 ? 'fewer' : 'more') + ` iterations (${r.left.iters} vs ${r.right.iters})`;
      $('why').innerHTML = `Both end inside τ = 10⁻³: traditional at error ${sci(r.left.err)}, guided at ${sci(r.right.err)}. ${fmt(r.left.ops)} vs ${fmt(r.right.ops)} multiply-adds.`;
      $('honest-needed').innerHTML = `The honest catch: on this edit Jacobi from darkness actually needed only <b>${r.jacobiNeeded}</b> bounces (${fmt(r.neededOps)} calcs) to reach τ, measured against the exact answer. Against that perfectly-tuned budget the guided side is ${pct((r.neededOps - r.right.ops) / r.neededOps * 100)} ${r.neededOps >= r.right.ops ? 'cheaper' : 'dearer'}. Most of the win is knowing when to stop, which an engine can't know without the theorem.`;
    } else if (lastMove) { const r = lastMove, it = (r.budget * r.ticks - r.right.sweepsMean * r.ticks) / (r.budget * r.ticks) * 100;
      $('pct-ops').textContent = pct(r.pctOps); $('pct-ops-l').textContent = r.pctOps >= 0 ? 'fewer calculations' : 'more calculations';
      $('pct-it').textContent = pct(it); $('pct-it-l').textContent = `fewer iterations per tick (${r.budget} vs ${r.right.sweepsMean.toFixed(2)} on average)`;
      $('why').innerHTML = `${r.ticks} ticks. Worst error, traditional ${sci(r.left.errMax)}, guided ${sci(r.right.errMax)}. Guided certified inside τ on <b>${r.right.ticksWithinTau}</b> of ${r.ticks} ticks${r.right.ticksWithinTau < r.ticks ? `; on the others its bound was at most ${sci(r.right.boundMax)}, and it says so` : ''}.`;
    }
    document.querySelectorAll('[data-sc]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.sc === scenario)));
    $('edits').hidden = scenario !== 'still'; $('hint').hidden = scenario !== 'still';
    $('run').textContent = scenario === 'still' ? 'Run the race' : `Run ${P.ticks} ticks`;
  }
  function tables() {
    const row = (k, a, b) => `<tr><th scope="row">${k}</th><td>${a}</td><td>${b}</td></tr>`;
    if (lastStill) { const r = lastStill;
      $('t-still').tBodies[0].innerHTML = row('Start', 'darkness', 'the light already there') + row('Iterations', `${r.left.iters} bounces`, `${r.right.iters} sweeps (R/G/B ${r.right.sweeps.join('/')})`)
        + row('Calculations', fmt(r.left.ops), fmt(r.right.ops)) + row('Time in this browser', r.left.ms.toFixed(2) + ' ms', r.right.ms.toFixed(2) + ' ms')
        + row('True error', sci(r.left.err), sci(r.right.err)) + row('Stop information', `last change ${sci(r.left.rawResidual)}, no guarantee`, `certified ≤ ${sci(r.right.bound)}`)
        + row('ρ / c per colour', '—', r.right.rho.map((v, c) => v.toFixed(2) + ' / ' + r.right.c[c].toFixed(2)).join(', '))
        + row('Improvement', `<b>${pct(r.pctOps)}</b> calcs`, `<b>${pct(r.pctIters)}</b> iterations`); }
    if (lastMove) { const r = lastMove;
      $('t-move').tBodies[0].innerHTML = row('Each tick', `cold, ${r.budget} bounces`, `warm, ≤ ${r.cap} sweeps`) + row('Calculations, total', fmt(r.left.opsTotal), fmt(r.right.opsTotal) + ` <span class="sm">(incl. ${fmt(r.right.setupOps)} to settle tick 0)</span>`)
        + row('Time in this browser', r.left.ms.toFixed(0) + ' ms', r.right.ms.toFixed(0) + ' ms') + row('Error, worst tick', sci(r.left.errMax), sci(r.right.errMax))
        + row('Error, mean', sci(r.left.errMean), sci(r.right.errMean)) + row('Certified bound', 'none', `≤ ${sci(r.right.boundMax)} worst, inside τ on ${r.right.ticksWithinTau}/${r.ticks}`)
        + row('Improvement', `<b>${pct(r.pctOps)}</b> calcs`, ''); }
  }
  const ccv = $('chart'), cc = ccv.getContext('2d');
  function chart(r, upto) {
    const Wd = ccv.width, Ht = ccv.height, L = 64, Rm = 16, T = 16, B = 34, lo = -17, hi = 0;
    const X = t => L + (Wd - L - Rm) * (t - 1) / Math.max(1, r.ticks - 1), Y = v => T + (Ht - T - B) * (hi - Math.log10(Math.max(v, 1e-17))) / (hi - lo);
    cc.fillStyle = '#1b1e27'; cc.fillRect(0, 0, Wd, Ht); cc.font = '16px ui-monospace, Consolas, monospace'; cc.fillStyle = '#b3ad9f';
    for (let e = lo + 1; e <= hi; e += 4) { cc.strokeStyle = '#2c3140'; cc.lineWidth = 1; cc.beginPath(); cc.moveTo(L, Y(10 ** e)); cc.lineTo(Wd - Rm, Y(10 ** e)); cc.stroke(); cc.fillText('1e' + e, 4, Y(10 ** e) + 6); }
    cc.fillText('tick', Wd - 64, Ht - 8);
    cc.setLineDash([8, 6]); cc.strokeStyle = '#ece7dc'; cc.beginPath(); cc.moveTo(L, Y(r.tau)); cc.lineTo(Wd - Rm, Y(r.tau)); cc.stroke(); cc.setLineDash([]);
    const line = (k, col) => { cc.strokeStyle = col; cc.lineWidth = 3; cc.beginPath(); r.perTick.slice(0, upto + 1).forEach((p, i) => i ? cc.lineTo(X(p.t), Y(p[k])) : cc.moveTo(X(p.t), Y(p[k]))); cc.stroke(); };
    line('errL', '#ffb44a'); line('boundR', '#6aa8ff'); line('errR', '#7fd99a');
  }

  // ---------------- exposure (raw counts; Gate 1 recomputes the percents) ----------------
  function expose() {
    const s = lastStill, m = lastMove, pick = o => o && { iters: o.iters, ops: o.ops, ms: o.ms, err: o.err };
    const mv = o => o && { opsTotal: o.opsTotal, errMax: o.errMax, errMean: o.errMean };
    window.__x3 = {
      stationary: s ? { left: pick(s.left), right: { ...pick(s.right), sweeps: s.right.sweeps, bound: s.right.bound }, pctIters: s.pctIters, pctOps: s.pctOps,
        tau: s.tau, budget: s.budget, bothWithinTau: s.bothWithinTau, jacobiNeeded: s.jacobiNeeded, neededOps: s.neededOps, scene: s.scene } : null,
      moving: m ? { left: mv(m.left), right: { ...mv(m.right), setupOps: m.right.setupOps, boundMax: m.right.boundMax, ticksWithinTau: m.right.ticksWithinTau, sweepsMean: m.right.sweepsMean },
        pctOps: m.pctOps, ticks: m.ticks, cap: m.cap, budget: m.budget, tau: m.tau } : null,
      counting: { n: M.N, perBounce: X3.PER, channels: 3, directPerChannel: M.N ** 3, rule: 'one bounce or sweep of one channel = N×N multiply-adds; the certificate check = one more N×N product' },
      defaults: window.__x3 && window.__x3.defaults,
    };
  }

  // ---------------- wiring ----------------
  document.querySelectorAll('[data-sc]').forEach(b => b.onclick = () => { scenario = b.dataset.sc; headline(); if (scenario === 'move') runMove(); else if (lastStill) runStill(nextScene(editKind, cur)); });
  document.querySelectorAll('[data-edit]').forEach(b => b.onclick = () => { editKind = b.dataset.edit;
    document.querySelectorAll('[data-edit]').forEach(o => o.setAttribute('aria-pressed', String(o === b))); runStill(nextScene(editKind, cur)); });
  $('run').onclick = () => scenario === 'still' ? runStill(nextScene(editKind, cur)) : runMove();
  rooms.forEach(R => R.cv.addEventListener('click', ev => {
    const s = clone(cur); if (s.lamps[0].type === 'panel') { $('hint').textContent = 'This room\'s lamp is a ceiling panel. Load Extravaganza to place a lamp by clicking.'; return; }
    const r = R.cv.getBoundingClientRect(), m = toM((ev.clientX - r.left) * R.cv.width / r.width, (ev.clientY - r.top) * R.cv.height / r.height);
    if (m[0] < 0 || m[0] > M.W || m[1] < 0 || m[1] > M.H) return;
    s.lamps[0].pos = [Math.round(m[0] * 100) / 100, Math.round(m[1] * 100) / 100]; scenario = 'still'; runStill(sceneOf(s)); }));
  const knob = (id, key, after) => $(id).addEventListener('input', e => { P[key] = +e.target.value; $('o-' + id).textContent = e.target.value; after && after(); });
  knob('budget', 'budget'); knob('ticks', 'ticks', headline); knob('cap', 'cap');
  ['budget', 'ticks', 'cap'].forEach(id => $(id).addEventListener('change', () => scenario === 'still' ? runStill(cur, lastBefore) : runMove()));

  // ---------------- default runs at load: both scenarios, measured now ----------------
  const d0 = X3.stationary(cur, nextScene('move', cur), { budget: 100, tau: P.tau });
  const m0 = X3.moving(MO.EXTRAVAGANZA, { budget: 100, ticks: 240, cap: P.cap, tau: P.tau });
  window.__x3 = { defaults: { stationary: { edit: 'move a lamp: magenta bulb (6.6, 2.5) → (5, 3.4), Extravaganza', left: { iters: d0.left.iters, ops: d0.left.ops, ms: d0.left.ms, err: d0.left.err },
      right: { iters: d0.right.iters, ops: d0.right.ops, ms: d0.right.ms, err: d0.right.err }, pctIters: d0.pctIters, pctOps: d0.pctOps },
    moving: { left: { opsTotal: m0.left.opsTotal, errMax: m0.left.errMax, errMean: m0.left.errMean }, right: { opsTotal: m0.right.opsTotal, errMax: m0.right.errMax, errMean: m0.right.errMean }, pctOps: m0.pctOps } } };
  lastMove = m0; tables(); chart(m0, m0.perTick.length - 1);
  runStill(nextScene('move', cur));
})();
