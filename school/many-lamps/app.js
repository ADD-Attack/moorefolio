// W-Ex11-X page: draws the lamp room, runs the bounces per colour, exposes everything on window.__ex11x.
(function () {
  'use strict';
  const LM = window.LampsModel, M = LM.room, PRESETS = window.LAMP_PRESETS, sim = LM.create();
  const q = new URLSearchParams(location.search);
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let held = q.has('hold'), playing = !held && !reduced, timer = null, sel = null, hover = -1;
  const MAX_K = 120, BOUNCE_MS = 380, CHN = ['Red', 'Green', 'Blue'], LINE = ['#ff6b5e', '#62dd85', '#6aa8ff'];
  const LUM = [0.2126, 0.7152, 0.0722];
  const $ = id => document.getElementById(id);

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
  const tone = v => 1 - Math.exp(-1.5 * Math.max(0, v));
  const shade = t => Math.round(9 + (255 - 9) * Math.pow(t, 1.25));
  const AIM_R = 0.7;
  function lampPx(L) { return toPx(L.pos); }
  function handlePx(L) { return toPx([L.pos[0] + AIM_R * Math.cos(L.aim), L.pos[1] + AIM_R * Math.sin(L.aim)]); }

  function drawRoom() {
    const X = sim.x;
    // exposure: the picture is scaled by the brightest channel's mean patch value, so a dim bulb and a runaway room both stay readable (picture only)
    let ex = 0; for (let c = 0; c < 3; c++) ex = Math.max(ex, X[c].reduce((s, t) => s + t, 0) / M.N); ex = ex > 0 ? 1 / ex : 1;
    for (let i = 0; i < GW * GH; i++) {
      const o = i * M.N, px = [0, 0, 0];
      for (let c = 0; c < 3; c++) { let s = 0; const x = X[c]; for (let j = 0; j < M.N; j++) s += x[j] * PHI[o + j]; px[c] = shade(tone(s / Math.PI / 2 * ex * 0.9)); }
      img.data[i * 4] = px[0]; img.data[i * 4 + 1] = px[1]; img.data[i * 4 + 2] = px[2]; img.data[i * 4 + 3] = 255;
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
      cx.strokeStyle = `rgb(${[0, 1, 2].map(c => shade(tone(X[c][j] * ex * .6))).join(',')})`; cx.lineWidth = panels.has(j) ? 13 : 9; cx.lineCap = 'butt';
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
    const W = ch.width, H = ch.height, L = 52, R = 12, T = 12, B = 28, hs = sim.history, chans = sim.channels;
    cc.fillStyle = '#1b1e27'; cc.fillRect(0, 0, W, H);
    const lo = -15, hi = 10, X = k => L + (k - 1) / (MAX_K - 1) * (W - L - R), Y = v => T + (hi - v) / (hi - lo) * (H - T - B);
    cc.strokeStyle = '#2c3140'; cc.fillStyle = '#b3ad9f'; cc.font = '12px ui-monospace, Consolas, monospace'; cc.lineWidth = 1; cc.textAlign = 'right';
    for (let e = lo; e <= hi; e += 5) { cc.beginPath(); cc.moveTo(L, Y(e)); cc.lineTo(W - R, Y(e)); cc.stroke(); cc.fillText('1e' + e, L - 6, Y(e) + 4); }
    cc.textAlign = 'center';
    for (let k = 1; k <= MAX_K; k += k === 1 ? 19 : 20) cc.fillText(String(k), X(k), H - 8);
    cc.save(); cc.beginPath(); cc.rect(L, T, W - L - R, H - T - B); cc.clip();
    for (let c = 2; c >= 0; c--) {
      const h = hs[c], anchor = h[Math.min(9, h.length - 1)];
      if (anchor && anchor.inc > 0) { const l = Math.log10(chans[c].spectral.rho), y0 = Math.log10(anchor.inc) - l * anchor.k;
        cc.setLineDash([4, 6]); cc.strokeStyle = LINE[c]; cc.globalAlpha = .55; cc.lineWidth = 1.2; cc.beginPath(); cc.moveTo(X(1), Y(y0 + l)); cc.lineTo(X(MAX_K), Y(y0 + l * MAX_K)); cc.stroke(); cc.setLineDash([]); cc.globalAlpha = 1; }
      cc.strokeStyle = LINE[c]; cc.lineWidth = 2.2; cc.beginPath(); let started = false;
      h.forEach(p => { if (!(p.inc > 0)) { started = false; return; } const y = Y(Math.log10(p.inc)); started ? cc.lineTo(X(p.k), y) : cc.moveTo(X(p.k), y); started = true; }); cc.stroke();
    }
    cc.restore();
  }

  // ---------- readouts ----------
  const fx = (v, d = 4) => v == null || !isFinite(v) ? '—' : v.toFixed(d);
  function verdictA(c) {
    const h = sim.history[c], last = h[h.length - 1];
    if (sim.channels[c].dark) return { s: 'wait', t: 'no light in this colour' };
    if (!last || h.length < 8) return { s: 'wait', t: 'watching… ' + h.length + '/8' };
    if (last.ratio == null) return { s: 'yes', t: 'yes, to round-off' };
    if (last.ratio < 0.9999) return { s: 'yes', t: 'yes' };
    return { s: 'no', t: last.ratio < 1.0001 ? 'no, flat' : 'no, growing' };
  }
  function readouts() {
    const out = { k: String(sim.k), channels: [] };
    let lum = 0;
    for (let c = 0; c < 3; c++) {
      const an = sim.channels[c], h = sim.history[c], last = h[h.length - 1], sp = an.spectral, ce = an.certificate;
      lum += LUM[c] * sim.x[c].reduce((s, t) => s + t, 0);
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
    $('agree').className = 'agree ' + r.agree.s; $('agree').textContent = r.agree.t;
    ['r', 'g', 'b'].forEach((n, c) => { const row = $('v-' + n), d = r.channels[c];
      row.querySelector('.rho').textContent = d.rho; row.querySelector('.ratio').textContent = d.ratio;
      for (const t of ['a', 'b', 'c']) { const td = row.querySelector('.' + t); td.className = t + ' ' + d[t].s; td.querySelector('.t').textContent = d[t].t; } });
    if (hover >= 0) { const P = M.PATCHES[hover]; $('r-patch').textContent = (hover + 1) + ' · ' + P.s;
      $('r-pr').textContent = fx(sim.x[0][hover], 3); $('r-pg').textContent = fx(sim.x[1][hover], 3); $('r-pb').textContent = fx(sim.x[2][hover], 3); }
    const sf = sim.surfaces;
    for (const s of M.SURFACES) { $('s-' + s).value = sf[s].refl; $('c-' + s).value = hex(sf[s].color); $('o-' + s).textContent = sf[s].refl.toFixed(2); }
    renderLamps();
    $('b-play').textContent = playing ? 'Pause' : 'Play';
    drawRoom(); drawChart();
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
  function tick() { if (!playing || held) return; if (sim.k < MAX_K) { sim.bounce(); render(); } else { playing = false; render(); } }
  function startLoop() { clearInterval(timer); timer = setInterval(tick, BOUNCE_MS); }
  function restart(fn) { fn(); if (reduced && !held && sim.k < 40) sim.advanceTo(40); render(); }

  $('b-play').onclick = () => { if (sim.k >= MAX_K) sim.advanceTo(0); playing = !playing; held = false; render(); };
  $('b-step').onclick = () => { playing = false; if (sim.k < MAX_K) sim.bounce(); render(); };
  $('b-reset').onclick = () => restart(() => sim.advanceTo(0));
  for (const s of M.SURFACES) {
    $('s-' + s).oninput = e => restart(() => sim.setSurface(s, { refl: +(+e.target.value).toFixed(2) }));
    $('c-' + s).oninput = e => restart(() => sim.setSurface(s, { color: unhex(e.target.value) }));
  }
  document.querySelectorAll('[data-preset]').forEach(b => b.onclick = () => restart(() => { sim.reset(PRESETS[b.dataset.preset]); sel = null; }));
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
    if (hit) { drag = hit; sel = hit.id; cv.setPointerCapture(ev.pointerId); playing = playing && true; render(); ev.preventDefault(); } });
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
    get lamps() { return sim.lamps.map(L => ({ ...L, pos: L.pos.slice(), color: L.color.slice(), d: L.d.slice(),
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
    advanceTo(k) { sim.advanceTo(Math.min(k, MAX_K)); render(); return sim.state(); },
    advanceFrames(n) { return this.advanceTo(sim.k + n); },
    hold(on = true) { held = on; if (on) playing = false; render(); },
    play() { held = false; playing = true; render(); },
    reset(scene) { sim.reset(scene); sel = null; render(); return sim.state(); },
    preset(name) { sim.reset(PRESETS[name]); sel = null; render(); return sim.state(); },
    addLamp(L) { const id = sim.addLamp(L); render(); return id; },
    removeLamp(id) { sim.removeLamp(id); render(); },
    setLamp(id, patch) { sim.setLamp(id, patch); render(); },
    setSurface(f, patch) { sim.setSurface(f, patch); render(); },
    get reducedMotion() { return reduced; },
  };
  sim.reset(PRESETS.original);
  if (reduced && !held) sim.advanceTo(40);
  render(); startLoop();
})();
