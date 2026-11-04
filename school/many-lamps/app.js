// W-Ex11-X page: draws the lamp room, runs the bounces per colour, exposes everything on window.__ex11x.
(function () {
  'use strict';
  const LM = window.LampsModel, M = LM.room, PRESETS = window.LAMP_PRESETS, SC = window.Science, MO = window.Motion, sim = LM.create();
  const q = new URLSearchParams(location.search);
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let scene = 'extravaganza', held = q.has('hold'), playing = !held && !reduced, timer = null, sel = null, hover = -1;
  const MAX_K = 120, BOUNCE_MS = 380, CHN = ['Red', 'Green', 'Blue'], LINE = ['#ff6b5e', '#62dd85', '#6aa8ff'];
  const LUM = [0.2126, 0.7152, 0.0722];
  const $ = id => document.getElementById(id);

  // ---------- X2 state: solver, clamp, Gauss–Seidel run (all app-layer; the Jacobi sim is untouched) ----------
  let solver = 'jacobi', clampOn = false, userSurf = null, gs = null, gsSig = '', certResult = null;
  const clone = o => JSON.parse(JSON.stringify(o));
  // With the clamp off the sim receives exactly the surfaces the visitor set (the graded path).
  function pushSurfaces() { const eff = clampOn ? SC.clampSurfaces(userSurf) : userSurf; for (const f of M.SURFACES) sim.setSurface(f, eff[f]); }
  function sceneSig() { return JSON.stringify(sim.scene()); }
  function gsReset() { gs = { k: 0, x: [0, 1, 2].map(() => new Array(M.N).fill(0)), hist: [[], [], []], bound: [null, null, null] }; gsSig = sceneSig(); certResult = null; }
  function gsStep() {
    for (let c = 0; c < 3; c++) { const an = sim.channels[c], prev = gs.x[c].slice();
      SC.gsSweep(an.A, an.e, gs.x[c]);
      const inc = M.supNorm(gs.x[c].map((t, i) => t - prev[i])), h = gs.hist[c][gs.hist[c].length - 1];
      const cc = an.maxRowSum; gs.bound[c] = SC.residualBound(an.A, an.e, gs.x[c], cc);
      gs.hist[c].push({ k: gs.k + 1, inc, ratio: h && h.inc > 1e-12 && inc > 1e-12 ? inc / h.inc : null, total: gs.x[c].reduce((s, t) => s + t, 0), bound: gs.bound[c] }); }
    gs.k++;
  }
  // Run to certified τ: from darkness, sweep until every lit colour's residual bound is ≤ τ·‖e‖ (or that colour cannot certify: c ≥ 1).
  function runCertified() {
    gsReset(); const done = c => { const an = sim.channels[c]; if (an.dark) return true; if (!(an.maxRowSum < 1)) return true;
      return gs.bound[c] != null && gs.bound[c] <= SC.TAU * M.supNorm(an.e); };
    while (gs.k < 500 && !(gs.k > 0 && [0, 1, 2].every(done))) gsStep();
    certResult = [0, 1, 2].map(c => { const an = sim.channels[c];
      if (an.dark) return { state: 'dark' }; if (!(an.maxRowSum < 1)) return { state: 'nocert', c: an.maxRowSum };
      let sw = null; for (const h of gs.hist[c]) if (h.bound <= SC.TAU * M.supNorm(an.e)) { sw = h.k; break; }
      return { state: 'ok', sweeps: sw, bound: gs.bound[c], c: an.maxRowSum }; });
    gsSig = sceneSig(); return certResult;
  }
  // ---------- §K: Live mode and lamp motion (app layer; lamps move through sim.setLamp, poses from the tick alone) ----------
  let mode = 'dark', motionOn = true, tick = 0, motions = new Map(), live = null;
  const CAP = MO.CAP_PER_FRAME;
  function liveReset() { live = { x: [0, 1, 2].map(() => new Array(M.N).fill(0)), d: [null, null, null], hist: [[], [], []], iters: 0, bound: [null, null, null] }; }
  const hasMotion = () => motions.size > 0;
  function applyTick() { for (const [id, m] of motions) if (sim.lamps.find(L => L.id === id)) sim.setLamp(id, MO.poseAt(m, tick)); }
  function liveIterate() {   // one warm-started iteration on the scene as it stands: a Jacobi bounce or a GS sweep
    for (let c = 0; c < 3; c++) { const an = sim.channels[c], before = live.x[c].slice();
      if (solver === 'gs') SC.gsSweep(an.A, an.e, live.x[c]); else { const Ax = M.mulVec(an.A, before); live.x[c] = an.e.map((t, i) => t + Ax[i]); }
      live.d[c] = live.x[c].map((t, i) => t - before[i]);
      live.bound[c] = SC.residualBound(an.A, an.e, live.x[c], an.maxRowSum);
      const h = live.hist[c]; h.push({ k: 0, inc: M.supNorm(live.d[c]), ratio: null, total: live.x[c].reduce((a, t) => a + t, 0), bound: live.bound[c] });
      if (h.length > MAX_K) h.shift(); h.forEach((e, i) => e.k = i + 1); }
    live.iters++;
  }
  function liveFrame(forceMotion) { if ((motionOn || forceMotion) && hasMotion()) { tick++; applyTick(); } for (let i = 0; i < CAP; i++) liveIterate(); }
  function loadMotions(name) { motions = new Map(); const P = PRESETS[name]; if (!P) return;
    sim.lamps.forEach((L, i) => { const m = P.lamps[i] && P.lamps[i].motion; if (m) motions.set(L.id, { ...m }); }); }
  // tickTo(T): Live from darkness at tick 0, then T frames (tick + 1 and CAP iterations each). Same T → same state, bit for bit.
  function tickTo(T) { tick = 0; applyTick(); liveReset(); mode = 'live'; for (let t = 0; t < T; t++) liveFrame(true); }
  const viewX = () => mode === 'live' ? live.x : solver === 'gs' ? gs.x : sim.x;
  const viewHist = () => mode === 'live' ? live.hist : solver === 'gs' ? gs.hist : sim.history;
  const viewK = () => mode === 'live' ? tick : solver === 'gs' ? gs.k : sim.k;

  // ---------- colour helpers ----------
  const hex = c => '#' + c.map(v => Math.round(Math.min(1, Math.max(0, v)) * 255).toString(16).padStart(2, '0')).join('');
  const unhex = h => [1, 3, 5].map(i => +(parseInt(h.slice(i, i + 2), 16) / 255).toFixed(4));
  const rgbCss = (c, a = 1) => `rgba(${c.map(v => Math.round(Math.min(1, Math.max(0, v)) * 255)).join(',')},${a})`;

  // ---------- room drawing ----------
  const cv = $('room'), cx = cv.getContext('2d');
  const S = 108, OX = 48, OY = 30;
  const toPx = p => [OX + p[0] * S, OY + (M.H - p[1]) * S];
  const toM = (px, py) => [(px - OX) / S, M.H - (py - OY) / S];
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
  // Display mapping (picture only; the model and every readout stay exact):
  // white point W = brightest non-lamp patch value in any colour this bounce; a value x is drawn at log(1 + K·x/W) / log(1 + K) of full brightness.
  // The interior glow uses the same curve against its own brightest point, capped at GLOW_CAP so walls stay brightest.
  const K = 8, LK = Math.log1p(K), GLOW_CAP = 0.4;
  const curve = t => Math.log1p(K * Math.min(1, Math.max(0, t))) / LK;
  const shade = t => Math.round(9 + (255 - 9) * curve(t));
  let white = 0;
  const AIM_R = 0.7;
  function lampPx(L) { return toPx(L.pos); }
  function handlePx(L) { return toPx([L.pos[0] + AIM_R * Math.cos(L.aim), L.pos[1] + AIM_R * Math.sin(L.aim)]); }

  function drawRoom() {
    const X = viewX();
    // white point: the brightest patch in any colour that is not itself a lamp (a ceiling panel may draw past white; no other patch clips)
    const lampPatch = new Set(sim.lamps.filter(L => L.type === 'panel').map(L => L.patch));
    white = 0; for (let c = 0; c < 3; c++) for (let j = 0; j < M.N; j++) if (!lampPatch.has(j)) white = Math.max(white, X[c][j]);
    if (!(white > 0)) for (let c = 0; c < 3; c++) for (let j = 0; j < M.N; j++) white = Math.max(white, X[c][j]);
    const ex = white > 0 ? 1 / white : 1;
    const F = new Float32Array(GW * GH * 3); let fmax = 0;
    for (let i = 0; i < GW * GH; i++) { const o = i * M.N;
      for (let c = 0; c < 3; c++) { let s = 0; const x = X[c]; for (let j = 0; j < M.N; j++) s += x[j] * PHI[o + j]; F[i * 3 + c] = s; if (s > fmax) fmax = s; } }
    const gk = fmax > 0 ? 1 / fmax : 1;
    for (let i = 0; i < GW * GH; i++) {
      for (let c = 0; c < 3; c++) img.data[i * 4 + c] = Math.round(9 + (255 - 9) * GLOW_CAP * curve(F[i * 3 + c] * gk));
      img.data[i * 4 + 3] = 255;
    }
    off.getContext('2d').putImageData(img, 0, 0);
    cx.fillStyle = '#08090c'; cx.fillRect(0, 0, cv.width, cv.height);
    cx.imageSmoothingEnabled = true; cx.drawImage(off, OX, OY, M.W * S, M.H * S);
    // first-flight pictures: cones and beams
    for (const L of sim.lamps) {
      const P = lampPx(L);
      if (L.type === 'spotlight') {
        cx.fillStyle = rgbCss(L.color, 0.16); cx.beginPath(); cx.moveTo(...P);
        cx.arc(P[0], P[1], 2.2 * S, -(L.aim + LM.SPOT_HALF), -(L.aim - LM.SPOT_HALF)); cx.closePath(); cx.fill();
      } else if (L.type === 'laser') {
        const E = toPx(LM.beamEnd(L)); cx.strokeStyle = rgbCss(L.color, 0.9); cx.lineWidth = 2.5;
        cx.beginPath(); cx.moveTo(...P); cx.lineTo(...E); cx.stroke();
        cx.fillStyle = rgbCss(L.color, 1); cx.beginPath(); cx.arc(...E, 5, 0, 7); cx.fill();
      }
    }
    // patches, coloured by the light they carry
    const panels = new Set(sim.lamps.filter(L => L.type === 'panel').map(L => L.patch));
    for (let j = 0; j < M.N; j++) { const { a, b } = M.PATCHES[j], A = toPx(a), B = toPx(b);
      cx.strokeStyle = `rgb(${[0, 1, 2].map(c => shade(X[c][j] * ex)).join(',')})`; cx.lineWidth = panels.has(j) ? 20 : 15; cx.lineCap = 'butt';
      cx.beginPath(); cx.moveTo(...A); cx.lineTo(...B); cx.stroke();
      if (j === hover) { cx.strokeStyle = '#ece7dc'; cx.lineWidth = 2; cx.strokeRect(Math.min(A[0], B[0]) - 7, Math.min(A[1], B[1]) - 7, Math.abs(A[0] - B[0]) + 14, Math.abs(A[1] - B[1]) + 14); }
      cx.strokeStyle = '#08090c'; cx.lineWidth = 2; cx.beginPath(); cx.arc(...A, .5, 0, 7); cx.stroke(); }
    // lamp bodies
    for (const L of sim.lamps) {
      const P = lampPx(L), on = sel === L.id;
      if (L.type === 'panel') {
        if (on) { const { a, b } = M.PATCHES[L.patch], A = toPx(a), B = toPx(b); cx.strokeStyle = '#ece7dc'; cx.lineWidth = 2; cx.strokeRect(Math.min(A[0], B[0]) - 9, Math.min(A[1], B[1]) - 9, Math.abs(A[0] - B[0]) + 18, Math.abs(A[1] - B[1]) + 18); }
        continue;
      }
      const g = cx.createRadialGradient(P[0], P[1], 2, P[0], P[1], 26); g.addColorStop(0, rgbCss(L.color, .9)); g.addColorStop(1, rgbCss(L.color, 0));
      cx.fillStyle = g; cx.beginPath(); cx.arc(P[0], P[1], 26, 0, 7); cx.fill();
      cx.fillStyle = rgbCss(L.color); cx.strokeStyle = on ? '#ffffff' : '#08090c'; cx.lineWidth = on ? 3 : 2;
      cx.beginPath();
      if (L.type === 'bulb') cx.arc(P[0], P[1], 9, 0, 7);
      else if (L.type === 'spotlight') { const a = -L.aim; cx.moveTo(P[0] + 12 * Math.cos(a), P[1] + 12 * Math.sin(a)); cx.lineTo(P[0] + 9 * Math.cos(a + 2.3), P[1] + 9 * Math.sin(a + 2.3)); cx.lineTo(P[0] + 9 * Math.cos(a - 2.3), P[1] + 9 * Math.sin(a - 2.3)); cx.closePath(); }
      else cx.rect(P[0] - 7, P[1] - 7, 14, 14);
      cx.fill(); cx.stroke();
      if (L.type !== 'bulb') { const Hd = handlePx(L); cx.strokeStyle = on ? '#ffffff' : 'rgba(236,231,220,.7)'; cx.lineWidth = 2; cx.beginPath(); cx.arc(...Hd, 6, 0, 7); cx.stroke(); }
    }
  }

  // ---------- chart ----------
  const ch = $('chart'), cc = ch.getContext('2d');
  function drawChart() {
    const W = ch.width, H = ch.height, L = 52, R = 12, T = 12, B = 28, hs = viewHist(), chans = sim.channels;
    cc.fillStyle = '#1b1e27'; cc.fillRect(0, 0, W, H);
    const lo = -15, hi = 10, X = k => L + (k - 1) / (MAX_K - 1) * (W - L - R), Y = v => T + (hi - v) / (hi - lo) * (H - T - B);
    cc.strokeStyle = '#2c3140'; cc.fillStyle = '#b3ad9f'; cc.font = '12px ui-monospace, Consolas, monospace'; cc.lineWidth = 1; cc.textAlign = 'right';
    for (let e = lo; e <= hi; e += 5) { cc.beginPath(); cc.moveTo(L, Y(e)); cc.lineTo(W - R, Y(e)); cc.stroke(); cc.fillText('1e' + e, L - 6, Y(e) + 4); }
    cc.textAlign = 'center';
    for (let k = 1; k <= MAX_K; k += k === 1 ? 19 : 20) cc.fillText(String(k), X(k), H - 8);
    cc.save(); cc.beginPath(); cc.rect(L, T, W - L - R, H - T - B); cc.clip();
    for (let c = 2; c >= 0; c--) {
      const h = hs[c], anchor = h[Math.min(9, h.length - 1)];
      if (mode === 'dark' && solver === 'jacobi' && anchor && anchor.inc > 0) { const l = Math.log10(chans[c].spectral.rho), y0 = Math.log10(anchor.inc) - l * anchor.k;
        cc.setLineDash([4, 6]); cc.strokeStyle = LINE[c]; cc.globalAlpha = .55; cc.lineWidth = 1.2; cc.beginPath(); cc.moveTo(X(1), Y(y0 + l)); cc.lineTo(X(MAX_K), Y(y0 + l * MAX_K)); cc.stroke(); cc.setLineDash([]); cc.globalAlpha = 1; }
      cc.strokeStyle = LINE[c]; cc.lineWidth = 2.2; cc.beginPath(); let started = false;
      h.forEach(p => { if (!(p.inc > 0)) { started = false; return; } const y = Y(Math.log10(p.inc)); started ? cc.lineTo(X(p.k), y) : cc.moveTo(X(p.k), y); started = true; }); cc.stroke();
    }
    cc.restore();
  }

  // ---------- readouts ----------
  const fx = (v, d = 4) => v == null || !isFinite(v) ? '—' : v.toFixed(d);
  function verdictA(c) {
    const h = viewHist()[c], last = h[h.length - 1];
    if (sim.channels[c].dark) return { s: 'wait', t: 'no light in this colour' };
    if (mode === 'live') { const an = sim.channels[c];
      if (!an.spectral.below1) return { s: 'no', t: 'no, growing' };
      const b = live.bound[c]; if (b == null) return { s: 'wait', t: 'chasing…' };
      return b <= SC.TAU * M.supNorm(an.e) ? { s: 'yes', t: 'caught up (≤ τ)' } : { s: 'wait', t: 'chasing' }; }
    if (!last || h.length < 8) return { s: 'wait', t: 'watching… ' + h.length + '/8' };
    if (last.ratio == null) return { s: 'yes', t: 'yes, to round-off' };
    if (last.ratio < 0.9999) return { s: 'yes', t: 'yes' };
    return { s: 'no', t: last.ratio < 1.0001 ? 'no, flat' : 'no, growing' };
  }
  function readouts() {
    const out = { k: String(viewK()), channels: [] };
    let lum = 0;
    for (let c = 0; c < 3; c++) {
      const an = sim.channels[c], h = viewHist()[c], last = h[h.length - 1], sp = an.spectral, ce = an.certificate;
      lum += LUM[c] * viewX()[c].reduce((s, t) => s + t, 0);
      out.channels.push({ name: CHN[c], rho: fx(sp.rho), ratio: last && last.ratio != null ? fx(last.ratio) : '—', a: verdictA(c),
        b: { s: sp.below1 ? 'yes' : 'no', t: sp.below1 ? 'yes' : Math.abs(sp.rho - 1) < 1e-9 ? 'no, exactly 1' : 'no' },
        c: ce.exists ? { s: 'yes', t: 'yes' } : { s: 'no', t: 'none' } });
    }
    out.lum = fx(lum, 3);
    const bs = out.channels.map(c => c.b.s), split = bs.some(s => s === 'yes') && bs.some(s => s === 'no');
    const runs = out.channels.filter(c => c.b.s === 'no').map(c => c.name.toLowerCase()), sets = out.channels.filter(c => c.b.s === 'yes').map(c => c.name.toLowerCase());
    const list = a => a.length === 1 ? a[0] : a.slice(0, -1).join(', ') + ' and ' + a[a.length - 1];
    out.agree = split ? { s: 'split', t: `Channels disagree: ${list(runs)} ${runs.length === 1 ? 'runs' : 'run'} away while ${list(sets)} ${sets.length === 1 ? 'settles' : 'settle'}.` }
      : bs[0] === 'yes' ? { s: 'yes', t: 'All three colours settle.' } : { s: 'no', t: 'No colour settles: all three run away.' };
    return out;
  }
  function render() {
    const r = readouts();
    $('r-k').textContent = r.k; $('r-lum').textContent = r.lum;
    $('verdict').className = 'verdict ' + r.agree.s; $('agree').textContent = r.agree.t;
    ['r', 'g', 'b'].forEach((n, c) => { const row = $('v-' + n), d = r.channels[c];
      row.querySelector('.rho').textContent = d.rho; row.querySelector('.ratio').textContent = d.ratio;
      for (const t of ['a', 'b', 'c']) { const td = row.querySelector('.' + t); td.className = t + ' ' + d[t].s; td.querySelector('.t').textContent = d[t].t; }
      const pill = $('p-' + n); pill.className = d.b.s; pill.querySelector('.t').textContent = d.b.s === 'yes' ? 'settles' : 'runs away'; });
    $('patch-hud').hidden = hover < 0;
    if (hover >= 0) { const P = M.PATCHES[hover]; $('r-patch').textContent = (hover + 1) + ' · ' + P.s;
      const X = viewX(); $('r-pr').textContent = fx(X[0][hover], 3); $('r-pg').textContent = fx(X[1][hover], 3); $('r-pb').textContent = fx(X[2][hover], 3); }
    if (!clampOn) userSurf = clone(sim.surfaces);       // clamp off: the sim's surfaces are the visitor's surfaces
    if (sceneSig() !== gsSig) gsReset();                 // any scene edit restarts the GS run from darkness
    const sf = userSurf;
    for (const s of M.SURFACES) { $('s-' + s).value = sf[s].refl; $('c-' + s).value = hex(sf[s].color); $('o-' + s).textContent = sf[s].refl.toFixed(2); }
    renderLamps();
    const pb = $('b-play'); pb.classList.toggle('on', playing); pb.querySelector('.lbl').textContent = playing ? 'Pause' : (mode === 'dark' && viewK() >= MAX_K ? 'Replay' : 'Play');
    pb.setAttribute('aria-label', (playing ? 'Pause' : 'Play') + ' the bounces');
    document.querySelectorAll('[data-preset]').forEach(b => b.setAttribute('aria-pressed', b.dataset.preset === scene));
    $('b-step').setAttribute('aria-label', solver === 'gs' ? 'Advance one sweep' : 'Advance one bounce');
    document.querySelector('.count span').textContent = mode === 'live' ? 'Tick' : solver === 'gs' ? 'Sweep' : 'Bounce';
    document.querySelectorAll('[data-mode]').forEach(b => b.setAttribute('aria-pressed', b.dataset.mode === mode));
    $('motion').checked = motionOn; $('motion').disabled = !hasMotion();
    $('live-note').innerHTML = mode === 'live'
      ? `Live: every frame the lamps move one tick${hasMotion() ? '' : ' (no moving lamps in this scene)'}, then the solver runs at most <b>${CAP} ${solver === 'gs' ? 'sweeps' : 'bounces'}</b>, warm-started from the light already on the walls. The light chases the lamps; the certified bound below says how close it is.`
      : 'From dark: the theorem’s run. Every Play starts with the room dark and counts bounces; lamps hold still.';
    renderX2();
    drawRoom(); drawChart(); $('r-white').textContent = fx(white, 4);
  }

  // ---------- X2 readouts: the science object (also window.__ex11x) and its display ----------
  let prevCache = { key: '', x: null };
  function prevX() {   // x_{k−1} of the Jacobi sim, by replaying the same scene from darkness (same arithmetic as the sim)
    const key = sceneSig() + '|' + sim.k; if (prevCache.key === key) return prevCache.x;
    const m = LM.create(); m.reset(sim.scene()); m.advanceTo(Math.max(0, sim.k - 1));
    prevCache = { key, x: m.x.map(v => v.slice()) }; return prevCache.x;
  }
  let roomCache = { key: '', v: null };
  function roomScience() {   // depends on the scene only, not the bounce: cached
    const key = sceneSig(); if (roomCache.key === key) return roomCache.v;
    const v = sim.channels.map((an, c) => ({ needed: an.dark ? null : SC.needed(an.A, an.e, an.exact), rhoQ: SC.rho4(SC.clusterQ(an.A)).rho,
      budget: SC.budget(SC.pMaxOf(sim.surfaces, c)), cb: SC.certificateBracket(an.certificate, an.A) }));
    roomCache = { key, v }; return v;
  }
  function science() {
    if (mode === 'live') return scienceLive();
    const P = prevX(), R = roomScience(), o = { k: sim.k, rhoEstimate: [], certificateBracket: [], enclosure: [], budget: [], cluster: { rhoQ: [] }, needed: [] };
    for (let c = 0; c < 3; c++) {
      const an = sim.channels[c];
      const D = sim.k > 0 && !an.dark ? SC.differences(an.A, sim.x[c], P[c]) : { lo: null, hi: null, state: an.dark ? 'dark' : 'start' };
      o.rhoEstimate.push({ channel: LM.CH[c], lo: D.lo, hi: D.hi, state: D.state || 'measured' });
      const cb = R[c].cb;
      o.certificateBracket.push({ channel: LM.CH[c], lo: cb.lo, hi: cb.hi, theta: cb.exists ? cb.theta : null });
      let en;
      if (an.dark) en = { available: false, lo: null, hi: null, width: null, state: 'dark' };
      else if (sim.k === 0) en = { available: false, lo: null, hi: null, width: null, state: 'start' };
      else en = SC.enclosure(an.A, sim.x[c], P[c]);
      o.enclosure.push({ channel: LM.CH[c], available: en.available, lo: en.lo, hi: en.hi, width: en.width, state: en.state, divergenceCertified: en.state === 'divergence' });
      o.budget.push({ channel: LM.CH[c], ...R[c].budget });
      o.needed.push(R[c].needed);
      o.cluster.rhoQ.push(R[c].rhoQ);
    }
    o.enclosure.divergenceCertified = o.enclosure.some(e => e.divergenceCertified);
    return o;
  }
  // Live: the latest iteration's difference d (fixed e within the frame). Jacobi: x* − x = Σ_{j≥1} Aʲd holds whatever came before,
  // so the m/M enclosure stands whenever d ≥ 0; while chasing d can change sign, and then only the residual bound certifies.
  function scienceLive() {
    const R = roomScience(), o = { k: tick, live: true, rhoEstimate: [], certificateBracket: [], enclosure: [], budget: [], cluster: { rhoQ: [] }, needed: [], residual: live.bound.slice() };
    for (let c = 0; c < 3; c++) { const an = sim.channels[c], d = live.d[c];
      let D = { lo: null, hi: null, state: an.dark ? 'dark' : 'start' }, en = { available: false, lo: null, hi: null, width: null, state: D.state };
      if (!an.dark && d && solver === 'jacobi') {
        if (d.some(t => t < 0)) { D.state = 'mixed'; en.state = 'mixed'; }
        else { const xPrev = live.x[c].map((t, i) => t - d[i]); D = SC.differences(an.A, live.x[c], xPrev); en = SC.enclosure(an.A, live.x[c], xPrev); }
      } else if (!an.dark && solver === 'gs') { D.state = 'gs'; en.state = 'gs'; }
      o.rhoEstimate.push({ channel: LM.CH[c], lo: D.lo, hi: D.hi, state: D.state || 'measured' });
      o.certificateBracket.push({ channel: LM.CH[c], lo: R[c].cb.lo, hi: R[c].cb.hi, theta: R[c].cb.exists ? R[c].cb.theta : null });
      o.enclosure.push({ channel: LM.CH[c], available: en.available, lo: en.lo, hi: en.hi, width: en.width, state: en.state, divergenceCertified: en.state === 'divergence' });
      o.budget.push({ channel: LM.CH[c], ...R[c].budget }); o.needed.push(R[c].needed); o.cluster.rhoQ.push(R[c].rhoQ); }
    o.enclosure.divergenceCertified = o.enclosure.some(e => e.divergenceCertified);
    return o;
  }
  const f6 = v => v == null || !isFinite(v) ? '—' : v.toFixed(6), f4 = v => v == null || !isFinite(v) ? '—' : v.toFixed(4);
  const sci3 = v => v == null || !isFinite(v) ? '—' : v === 0 ? '0' : v.toExponential(1).replace('e', '×10^').replace(/\^\+?(-?\d+)/, (m, e) => '<sup>' + e + '</sup>');
  function renderX2() {
    const S = science();
    document.querySelectorAll('.sci-card').forEach(card => { const c = +card.dataset.c, an = sim.channels[c];
      const re = S.rhoEstimate[c], cb = S.certificateBracket[c], en = S.enclosure[c], bu = S.budget[c];
      const est = re.state === 'mixed' ? 'chasing: the last change has mixed sign, so no ratio bracket this frame' : re.state === 'gs' ? 'Jacobi instrument (switch solver to read it)' : re.state === 'dark' ? 'no light in this colour' : re.state === 'start' ? 'needs one bounce' : re.state === 'roundoff' ? 'differences at round-off' :
        `${f6(re.lo)} – ${re.hi === Infinity ? '∞ (light still arriving)' : f6(re.hi)}`;
      const cert = cb.theta == null ? 'none: no positive settled light' : `${f4(cb.lo)} – <b>θ ${f4(cb.theta)}</b>`;
      const encl = en.state === 'divergence' ? '<b class="no">divergence certified</b> (smallest ratio ≥ 1)'
        : en.state === 'mixed' ? 'chasing: no enclosure this frame. The residual bound below still certifies.' : en.state === 'gs' ? 'Jacobi instrument' : en.state === 'none' ? 'no enclosure yet (a ratio is still ≥ 1)' : en.state === 'dark' ? '—' : en.state === 'start' ? 'needs one bounce'
        : `${f6(en.lo)} – ${f6(en.hi)}<br><span class="w">width ${sci3(en.width)}</span>`;
      const bud = bu.guaranteed == null ? `p<sub>max</sub> ${f4(bu.pMax)} ≥ 1: no guarantee` : `<b>${bu.guaranteed}</b> guaranteed (p<sub>max</sub> ${bu.pMax.toFixed(3)}) · ${S.needed[c] == null ? '—' : S.needed[c]} measured`;
      const liveRow = mode === 'live' ? `<dt>Live certified error <span>‖x* − x‖ ≤ ‖e + Ax − x‖/(1 − c), against the scene at tick ${tick}</span></dt><dd>${live.bound[c] == null ? (an.maxRowSum < 1 ? 'needs one frame' : 'c = ' + f4(an.maxRowSum) + ' ≥ 1: no certified bound') : '≤ ' + sci3(live.bound[c])}</dd>` : '';
      const solverRow = mode === 'live' ? liveRow : solver === 'gs' ? `<dt>GS certified error bound</dt><dd>${gs.bound[c] == null ? (an.maxRowSum < 1 ? 'needs one sweep' : 'c = ' + f4(an.maxRowSum) + ' ≥ 1: no certified stop') : '≤ ' + sci3(gs.bound[c])}</dd>` : '';
      card.querySelector('dl').innerHTML =
        `<dt>The estimate <span>from the bounce differences${mode === 'live' ? ' (latest live bounce)' : solver === 'gs' ? ' (Jacobi run)' : ''}</span></dt><dd>${est}</dd>` +
        `<dt>Certificate bracket <span>certifies settling; does not estimate ρ</span></dt><dd>${cert}</dd>` +
        `<dt>Settled total light, fenced <span>certified enclosure, ${mode === 'live' ? 'tick ' + tick + ', live' : 'bounce ' + sim.k + (solver === 'gs' ? ', Jacobi run' : '')}</span></dt><dd>${encl}</dd>` +
        `<dt>Bounces to τ <span>guaranteed from p<sub>max</sub> alone · measured here</span></dt><dd>${bud}</dd>` +
        `<dt>Cluster certificate ρ(Q) <span>4 surfaces as 4 patches; true ρ ${f4(an.spectral.rho)}</span></dt><dd>${f6(S.cluster.rhoQ[c])}${S.cluster.rhoQ[c] < 1 ? ' &lt; 1: certifies' : ' ≥ 1: too coarse to certify'}</dd>` + solverRow; });
    // controls group
    document.querySelectorAll('[data-solver]').forEach(b => b.setAttribute('aria-pressed', b.dataset.solver === solver));
    $('sv-note').innerHTML = solver === 'gs'
      ? 'Gauss–Seidel: each patch uses light already updated this sweep. Usually faster: ρ<sub>GS</sub> ≈ ρ² is a measurement, not a promise. Stein–Rosenberg guarantees only that it is no slower.'
      : "Jacobi: every patch updates from last bounce's light. This is the theorem's iteration, and the default.";
    $('certrun').hidden = solver !== 'gs';
    if (certResult) { $('cert-out').innerHTML = certResult.map((r, c) => `<span class="${['cr', 'cg', 'cb'][c]}">${CHN[c]}</span> ` +
      (r.state === 'dark' ? 'no light' : r.state === 'nocert' ? `c = ${f4(r.c)} ≥ 1: cannot certify` : `${r.sweeps} sweeps, error ≤ ${sci3(r.bound)}`)).join(' · ') + ' (τ = 10<sup>−3</sup>)'; }
    else $('cert-out').innerHTML = 'Sweeps until the residual proves the error is at most τ = 10<sup>−3</sup> (relative to the strongest lamp’s share). Costs one extra pass per sweep.';
    $('clamp').checked = clampOn;
    const pm = [0, 1, 2].map(c => SC.pMaxOf(sim.surfaces, c));
    $('clamp-out').innerHTML = clampOn
      ? `On. Effective p<sub>max</sub> after clamp: <span class="cr">${pm[0].toFixed(3)}</span> / <span class="cg">${pm[1].toFixed(3)}</span> / <span class="cb">${pm[2].toFixed(3)}</span>. Brightness ceiling 1/(1 − 0.9) = <b>10×</b> the direct light.`
      : `Off. Surfaces used as set: p<sub>max</sub> <span class="cr">${pm[0].toFixed(3)}</span> / <span class="cg">${pm[1].toFixed(3)}</span> / <span class="cb">${pm[2].toFixed(3)}</span>.`;
  }
  const TNAME = { bulb: 'Bulb', spotlight: 'Spotlight', laser: 'Laser', panel: 'Ceiling panel' };
  function renderLamps() {
    const lamps = sim.lamps; if (!lamps.find(L => L.id === sel)) sel = lamps.length ? lamps[0].id : null;
    const chips = $('chips'), sig = lamps.map(L => L.id + L.type + hex(L.color)).join('|') + '/' + sel;
    if (chips.dataset.sig !== sig) {
      chips.dataset.sig = sig; chips.textContent = '';
      lamps.forEach((L, i) => { const b = document.createElement('button'); b.type = 'button'; b.className = 'chip' + (L.id === sel ? ' on' : ''); b.setAttribute('role', 'listitem');
        b.setAttribute('aria-pressed', L.id === sel); b.innerHTML = `<i style="background:${hex(L.color)}"></i>${TNAME[L.type]} ${i + 1}`; b.onclick = () => { sel = L.id; render(); }; chips.appendChild(b); });
      if (!lamps.length) chips.textContent = 'No lamps. The room is dark; add one above.';
    }
    const L = lamps.find(l => l.id === sel), ed = $('editor'); ed.hidden = !L; if (!L) return;
    $('l-type').value = L.type; $('l-color').value = hex(L.color); $('o-color').textContent = hex(L.color);
    $('l-bright').value = L.brightness; $('o-bright').textContent = L.brightness.toFixed(2);
    const deg = Math.round(((L.aim * 180 / Math.PI) % 360 + 360) % 360) % 360;
    $('l-aim').value = deg; $('o-aim').textContent = L.type === 'bulb' || L.type === 'panel' ? '—' : deg + '°'; $('l-aim').disabled = L.type === 'bulb' || L.type === 'panel';
  }

  // ---------- loop ----------
  function advance1() { if (mode === 'live') liveFrame(); else if (solver === 'gs') gsStep(); else sim.bounce(); }
  function stepTimer() { if (mode === 'live' || !playing || held) return; if (viewK() < MAX_K) { advance1(); render(); } else { playing = false; render(); } }
  function startLoop() { clearInterval(timer); timer = setInterval(stepTimer, BOUNCE_MS); requestAnimationFrame(frame); }
  function frame() { if (mode === 'live' && playing && !held) { liveFrame(); render(); } requestAnimationFrame(frame); }
  function restart(fn) { fn(); if (reduced && !held && sim.k < 40) sim.advanceTo(40); if (solver === 'gs' && sceneSig() !== gsSig) { gsReset(); if (reduced && !held) runCertified(); } render(); }

  $('b-play').onclick = () => { if (mode === 'dark' && viewK() >= MAX_K) { if (solver === 'gs') gsReset(); else sim.advanceTo(0); } playing = !playing; held = false; render(); };
  $('b-step').onclick = () => { playing = false; if (mode === 'live' || viewK() < MAX_K) advance1(); render(); };
  $('b-reset').onclick = () => restart(() => { if (mode === 'live') { tick = 0; applyTick(); liveReset(); } else sim.advanceTo(0); gsReset(); });
  for (const s of M.SURFACES) {
    $('s-' + s).oninput = e => restart(() => clampOn ? (userSurf[s].refl = +(+e.target.value).toFixed(2), pushSurfaces()) : sim.setSurface(s, { refl: +(+e.target.value).toFixed(2) }));
    $('c-' + s).oninput = e => restart(() => clampOn ? (userSurf[s].color = unhex(e.target.value), pushSurfaces()) : sim.setSurface(s, { color: unhex(e.target.value) }));
  }
  function loadPreset(name) { sim.reset(PRESETS[name]); userSurf = clone(sim.surfaces); if (clampOn) pushSurfaces(); scene = name; sel = null;
    loadMotions(name); tick = 0; liveReset();
    // The show opens in Live; the theorem rooms open in From dark, exactly as graded.
    mode = name === 'extravaganza' && !reduced ? 'live' : 'dark'; }
  function setMode(m) { m = m === 'live' ? 'live' : 'dark'; if (m === mode) return; mode = m; sim.advanceTo(0); if (m === 'live') applyTick(); }
  document.querySelectorAll('[data-mode]').forEach(b => b.onclick = () => { setMode(b.dataset.mode); render(); });
  $('motion').onchange = e => { motionOn = e.target.checked; render(); };
  document.querySelectorAll('[data-preset]').forEach(b => b.onclick = () => restart(() => loadPreset(b.dataset.preset)));
  function setClamp(on) { on = !!on; if (on === clampOn) return; if (!clampOn) userSurf = clone(sim.surfaces); clampOn = on; pushSurfaces(); }
  function setSolver(v) { solver = v === 'gs' ? 'gs' : 'jacobi'; gsReset(); if (reduced && solver === 'gs') runCertified(); }
  $('clamp').onchange = e => restart(() => setClamp(e.target.checked));
  document.querySelectorAll('[data-solver]').forEach(b => b.onclick = () => { playing = false; setSolver(b.dataset.solver); render(); });
  $('b-cert').onclick = () => { playing = false; runCertified(); render(); };
  const ADD = { bulb: { type: 'bulb', pos: [4, 2.5], color: [1, 0.85, 0.6] }, spotlight: { type: 'spotlight', pos: [2, 1.2], aim: Math.PI / 4, color: [0.5, 0.8, 1] }, laser: { type: 'laser', pos: [6, 3.8], aim: Math.PI * 1.15, color: [1, 0.3, 0.3] } };
  document.querySelectorAll('[data-add]').forEach(b => b.onclick = () => restart(() => { sel = sim.addLamp(ADD[b.dataset.add]); }));
  const setSel = patch => sel != null && restart(() => sim.setLamp(sel, patch));
  $('l-type').onchange = e => { const L = sim.lamps.find(l => l.id === sel); if (!L) return;
    const t = e.target.value, p = { type: t };
    if (t === 'panel') { let best = 0, bd = Infinity; M.PATCHES.forEach((P, j) => { const d = Math.hypot((P.a[0] + P.b[0]) / 2 - L.pos[0], (P.a[1] + P.b[1]) / 2 - L.pos[1]); if (d < bd) { bd = d; best = j; } }); p.patch = best; }
    else if (L.type === 'panel') { const P = M.PATCHES[L.patch]; p.pos = [(P.a[0] + P.b[0]) / 2 + (P.s === 'left' ? .6 : P.s === 'right' ? -.6 : 0), (P.a[1] + P.b[1]) / 2 + (P.s === 'floor' ? .6 : P.s === 'ceiling' ? -.6 : 0)]; }
    setSel(p); };
  $('l-color').oninput = e => setSel({ color: unhex(e.target.value) });
  $('l-bright').oninput = e => setSel({ brightness: +(+e.target.value).toFixed(2) });
  $('l-aim').oninput = e => setSel({ aim: +e.target.value * Math.PI / 180 });
  $('l-remove').onclick = () => { const id = sel; sel = null; restart(() => sim.removeLamp(id)); };

  // ---------- dragging ----------
  let drag = null;
  const evM = ev => { const r = cv.getBoundingClientRect(); const px = (ev.clientX - r.left) * cv.width / r.width, py = (ev.clientY - r.top) * cv.height / r.height; return { px, py, m: toM(px, py) }; };
  const nearPatch = m => { let best = -1, bd = 0.45; M.PATCHES.forEach((p, j) => { const c = [(p.a[0] + p.b[0]) / 2, (p.a[1] + p.b[1]) / 2], d = Math.max(Math.abs(c[0] - m[0]), Math.abs(c[1] - m[1])); if (d < bd) { bd = d; best = j; } }); return best; };
  function pick(px, py, m) {
    const r = cv.getBoundingClientRect(), tol = 16 * cv.width / Math.max(1, r.width) / 1.6 + 6;
    for (const L of [...sim.lamps].reverse()) {
      if (L.type === 'spotlight' || L.type === 'laser') { const H = handlePx(L); if (Math.hypot(H[0] - px, H[1] - py) < tol) return { id: L.id, mode: 'aim' }; }
      if (L.type !== 'panel') { const P = lampPx(L); if (Math.hypot(P[0] - px, P[1] - py) < tol + 4) return { id: L.id, mode: 'move' }; }
    }
    const pj = nearPatch(m), pl = sim.lamps.find(L => L.type === 'panel' && L.patch === pj);
    return pl ? { id: pl.id, mode: 'panel' } : null;
  }
  cv.addEventListener('pointerdown', ev => { const { px, py, m } = evM(ev); const hit = pick(px, py, m);
    if (hit) { drag = hit; sel = hit.id; motions.delete(hit.id); cv.setPointerCapture(ev.pointerId); playing = playing && true; render(); ev.preventDefault(); } });
  cv.addEventListener('pointermove', ev => { const { px, py, m } = evM(ev);
    if (drag) {
      const L = sim.lamps.find(l => l.id === drag.id); if (!L) return;
      if (drag.mode === 'move') sim.setLamp(drag.id, { pos: m });
      else if (drag.mode === 'aim') sim.setLamp(drag.id, { aim: Math.atan2(m[1] - L.pos[1], m[0] - L.pos[0]) });
      else { const pj = nearPatch(m); if (pj >= 0 && pj !== L.patch) sim.setLamp(drag.id, { patch: pj }); }
      render(); return;
    }
    const h = nearPatch(m); if (h !== hover) { hover = h; render(); }
    cv.style.cursor = pick(px, py, m) ? 'grab' : 'default';
  });
  const end = () => { drag = null; }; cv.addEventListener('pointerup', end); cv.addEventListener('pointercancel', end);
  cv.addEventListener('keydown', ev => { const L = sim.lamps.find(l => l.id === sel); if (!L || L.type === 'panel') return;
    const d = { ArrowLeft: [-.1, 0], ArrowRight: [.1, 0], ArrowUp: [0, .1], ArrowDown: [0, -.1] }[ev.key]; if (!d) return;
    ev.preventDefault(); restart(() => sim.setLamp(sel, { pos: [L.pos[0] + d[0], L.pos[1] + d[1]] })); });

  window.__ex11x = {
    model: LM, sim, PRESETS,
    get lamps() { return sim.lamps.map(L => ({ ...L, motion: motions.has(L.id) ? { ...motions.get(L.id) } : null, pos: L.pos.slice(), color: L.color.slice(), d: L.d.slice(),
      cone: L.type === 'spotlight' ? { aim: L.aim, halfWidth: LM.SPOT_HALF } : null, support: L.d.map((t, j) => t > 0 ? j : -1).filter(j => j >= 0) })); },
    get state() { return sim.state(); },
    get scene() { return sim.scene(); },
    get channels() { return sim.channels.map((an, c) => ({ channel: LM.CH[c], rho: an.spectral.rho, lo: an.spectral.lo, hi: an.spectral.hi, below1: an.spectral.below1,
      certificate: { exists: an.certificate.exists, theta: an.certificate.theta }, maxRowSum: an.maxRowSum, e: an.e.slice(), A: an.A })); },
    get rho() { return sim.channels.map(an => an.spectral.rho); },
    get verdicts() { const r = readouts(); return { channels: r.channels.map((c, i) => ({ channel: LM.CH[i], a: c.a.s, b: c.b.s, c: c.c.s })), agree: r.agree.s }; },
    get readouts() { return readouts(); },
    headline() { const m = LM.create(); m.reset(PRESETS.original); m.advanceTo(30);
      return LM.CH.map((n, c) => ({ channel: n, bounce: 30, ratio: m.history[c][29].ratio, rho: m.channels[c].spectral.rho })); },
    advanceTo(k) { if (mode === 'live') { mode = 'dark'; }
      sim.advanceTo(Math.min(k, MAX_K)); render(); return sim.state(); },
    advanceFrames(n) { return this.advanceTo(sim.k + n); },
    hold(on = true) { held = on; if (on) playing = false; render(); },
    play() { held = false; playing = true; render(); },
    reset(s) { mode = 'dark'; motions = new Map(); sim.reset(s); userSurf = clone(sim.surfaces); if (clampOn) pushSurfaces(); scene = null; sel = null; render(); return sim.state(); },
    preset(name) { loadPreset(name); if (held) playing = false; render(); return sim.state(); },
    addLamp(L) { const id = sim.addLamp(L); render(); return id; },
    removeLamp(id) { sim.removeLamp(id); render(); },
    setLamp(id, patch) { sim.setLamp(id, patch); render(); },
    setSurface(f, patch) { if (clampOn) { userSurf[f] = { ...userSurf[f], ...patch }; pushSurfaces(); } else sim.setSurface(f, patch); render(); },
    get reducedMotion() { return reduced; },
    // ---- W-Ex11-X2 additions (Jacobi-sim readouts at the sim's current bounce; GS run is its own) ----
    get rhoEstimate() { return science().rhoEstimate.map(({ lo, hi }) => ({ lo, hi })); },
    get certificateBracket() { return science().certificateBracket.map(({ lo, hi, theta }) => ({ lo, hi, theta })); },
    get enclosure() { const e = science().enclosure; const a = e.map(({ available, lo, hi, width, state, divergenceCertified }) => ({ available, lo, hi, width, state, divergenceCertified }));
      a.divergenceCertified = e.divergenceCertified; return a; },
    get budget() { return science().budget.map(({ pMax, tau, guaranteed }) => ({ pMax, tau, guaranteed })); },
    get neededBounces() { return science().needed; },
    get gs() { const per = sim.channels.map((an, c) => { const r = an.dark ? null : SC.gsRun(an.A, an.e);
        const trueError = r && r.x && an.exact ? M.supNorm(r.x.map((t, i) => t - an.exact[i])) : null;
        const jacobiAgree = r && r.x && an.exact ? trueError <= r.certifiedBound : null;
        return { channel: LM.CH[c], sweeps: r ? r.sweeps : null, certifiedBound: r ? r.certifiedBound : null, c: an.maxRowSum, trueError, agreesWithSettled: jacobiAgree }; });
      const ok = per.filter(p => p.sweeps != null);
      return { solver, tau: SC.TAU, sweeps: ok.length ? Math.max(...ok.map(p => p.sweeps)) : null, certifiedBound: ok.length ? Math.max(...ok.map(p => p.certifiedBound)) : null, perChannel: per,
        page: { k: gs.k, bound: gs.bound.slice(), cert: certResult } }; },
    get clamp() { return { on: clampOn, cap: SC.CAP, pMaxAfter: [0, 1, 2].map(c => SC.pMaxOf(sim.surfaces, c)), ceiling: 1 / (1 - SC.CAP) }; },
    get cluster() { const r = science().cluster.rhoQ; return { rhoQ: Math.max(...r), perChannel: r }; },   // rhoQ: the binding (largest) colour
    setClamp(on) { setClamp(on); render(); return this.clamp; },
    setSolver(v) { setSolver(v); render(); return solver; },
    runCertified() { if (solver !== 'gs') setSolver('gs'); const r = runCertified(); render(); return r; },
    get live() { return { on: mode === 'live', playing: playing && !held, capPerFrame: CAP, iterations: live.iters, x: live.x.map(v => v.slice()), bound: live.bound.slice() }; },
    get motion() { return { on: motionOn, tick, moving: [...motions.keys()] }; },
    get tick() { return tick; },
    tickTo(T) { tickTo(T); render(); return { tick, lamps: sim.lamps.map(L => ({ id: L.id, pos: L.pos.slice(), aim: L.aim })), x: live.x.map(v => v.slice()) }; },
    stepTick(n = 1) { mode = 'live'; for (let i = 0; i < n; i++) liveFrame(); render(); return tick; },
    liveIterate(n = 1) { mode = 'live'; for (let i = 0; i < n; i++) liveIterate(); render(); return live.bound.slice(); },
    setMotion(on) { motionOn = !!on; render(); return motionOn; },
    setMode(m) { setMode(m); render(); return mode; },
    gsStep(n = 1) { for (let i = 0; i < n; i++) gsStep(); render(); return { k: gs.k, bound: gs.bound.slice() }; },
  };
  loadPreset('extravaganza'); if (reduced) motionOn = false; gsReset();
  if (reduced && !held) sim.advanceTo(40);
  render(); startLoop();
})();
