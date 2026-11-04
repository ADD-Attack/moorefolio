// The cluster — the interface. Every number drawn here is read from the live model state in cluster-model.js,
// and the view on screen is exactly Cluster.camera(state) for the page's own framing options.
(function () {
  'use strict';
  var C = window.Cluster, N = C.N;
  var NAMES = ['α', 'β', 'γ', 'δ', 'ε', 'ζ', 'η', 'θ', 'ι', 'κ', 'λ', 'μ', 'ν', 'ξ', 'ο', 'π', 'ρ', 'σ', 'τ', 'υ', 'φ', 'χ', 'ψ', 'ω', 'ϝ'];
  var SPEEDS = [0.25, 0.5, 1, 2, 4];                       // ×speed → ticks per animation frame = speed × 4
  var DEFAULTS = { speed: 2, trail: 3, room: 30, playing: true };
  var EXCURSION_R = 10;                                     // a bound member this far from the centre is "on a wide excursion"
  var MIN_ASPECT = 0.55;                                    // the camera's frame is at least this tall per unit of width
  var NEWS = 4;                                             // an escape stays the headline for this many model seconds

  var $ = function (id) { return document.getElementById(id); };
  var canvas = $('view'), ctx = canvas.getContext('2d'), rail = $('rail'), rctx = rail.getContext('2d');
  var ui = { play: $('c-play'), speed: $('c-speed'), trail: $('c-trail'), room: $('c-room'), reset: $('c-reset'),
    oSpeed: $('o-speed'), oTrail: $('o-trail'), oRoom: $('o-room'),
    time: $('r-time'), energy: $('r-energy'), drift: $('r-drift'), bound: $('r-bound'), view: $('r-view'),
    regime: $('regime'), status: $('status'), statusBox: document.querySelector('.status'), card: $('card'),
    pill: document.querySelector('.pill'), stage: $('stage') };
  var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var P, S, trails, history, frames, picked, debt;

  // ---- framing options: the share of the view the bound members fill, and the view's own shape ----
  var frame = { x: 0, y: 0, w: 1, h: 1 };                  // the camera's rectangle on screen, px (clear of the overlays)
  function camOpts() { return { fill: 1 - P.room / 100, aspect: frame.h / frame.w }; }
  function cam() { return C.camera(S, camOpts()); }

  function start() {
    S = C.make(C.SEED); trails = []; for (var i = 0; i < N; i++) trails.push([]);
    history = []; frames = 0; picked = -1; debt = 0; ui.card.hidden = true;
    C.followCamera(S, camOpts()); record(true); render();
  }

  function syncControls() {
    ui.speed.value = P.speed; ui.trail.value = P.trail; ui.room.value = P.room;
    var sp = SPEEDS[P.speed]; ui.oSpeed.textContent = '×' + (sp < 1 ? sp.toFixed(2) : sp);
    ui.oTrail.textContent = P.trail === 0 ? 'off' : P.trail.toFixed(1) + ' s';
    ui.oRoom.textContent = P.room + '%';
    ui.play.textContent = P.playing ? 'Pause' : 'Play';
    ui.play.setAttribute('aria-pressed', String(!P.playing));
  }
  function reset() { P = Object.assign({}, DEFAULTS); if (reduced) P.playing = false; syncControls(); start(); }

  // ---- stepping: one tick is 1/240 model second; the camera eases once per tick ----
  function oneTick() {
    var before = S.escapers.length;
    C.tick(S); C.followCamera(S, camOpts());
    if (S.tick % 4 === 0) record(false);
    if (S.escapers.length !== before && picked >= 0) showCard();
  }
  function advanceFrames(n) {
    var per = SPEEDS[P.speed] * 4;
    for (var f = 0; f < n; f++) { for (var q = 0; q < per; q++) oneTick(); frames++; }
  }
  function record(first) {
    var cut = S.t - P.trail;
    for (var i = 0; i < N; i++) { var tr = trails[i];
      if (P.trail > 0) tr.push([S.X[2 * i], S.X[2 * i + 1], S.t]);
      var d = 0; while (d < tr.length && tr[d][2] < cut - 1e-9) d++; if (d) tr.splice(0, d);
      if (P.trail === 0) tr.length = 0; }
    if (first || S.tick % 60 === 0) history.push([S.t, cam().width]);
  }

  // ---- drawing ----
  var W = 0, H = 0, dpr = 1, RW = 0, RH = 0;
  function layout() {
    var r = canvas.getBoundingClientRect(); dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = r.width; H = r.height; canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    var st = ui.statusBox.getBoundingClientRect(), pl = ui.pill.getBoundingClientRect(), side = W < 600 ? 14 : 28;
    var top = st.bottom - r.top + 14, bottom = pl.top - r.top - 14;
    var fh = Math.max(80, bottom - top), fw = Math.min(W - 2 * side, fh / MIN_ASPECT);   // never flatter than 0.55 tall per unit wide
    frame = { x: (W - fw) / 2, y: top, w: fw, h: fh };
    var rr = rail.getBoundingClientRect(); RW = rr.width; RH = rr.height;
    rail.width = Math.round(RW * dpr); rail.height = Math.round(RH * dpr); rctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    if (S) render();
  }

  function massColour(m, a) {   // amber (0.5) → blue-white (2.0)
    var f = Math.max(0, Math.min(1, (m - 0.5) / 1.5)), A = [255, 179, 92], B = [207, 225, 255];
    return 'rgba(' + Math.round(A[0] + (B[0] - A[0]) * f) + ',' + Math.round(A[1] + (B[1] - A[1]) * f) + ',' + Math.round(A[2] + (B[2] - A[2]) * f) + ',' + a + ')';
  }
  function niceStep(span) { var p = Math.pow(10, Math.floor(Math.log10(span))), m = span / p; return (m < 2 ? 1 : m < 5 ? 2 : 5) * p; }
  function fmtUnits(v) { return v >= 100 ? v.toFixed(0) : v >= 10 ? v.toFixed(1) : v >= 1 ? v.toFixed(2) : v.toPrecision(3); }

  function render() {
    if (!W) return;
    var c = cam(), s = frame.w / c.width, i;
    var X = function (x) { return frame.x + frame.w / 2 + (x - c.cx) * s; }, Y = function (y) { return frame.y + frame.h / 2 - (y - c.cy) * s; };
    ctx.clearRect(0, 0, W, H);

    // grid in model units, re-stepped to the zoom (1, 2 or 5 × a power of ten, about 90 px apart)
    var step = niceStep(90 / s), gx;
    ctx.lineWidth = 1; ctx.strokeStyle = '#121b29';
    var x0 = Math.floor((c.cx - (frame.x + frame.w / 2) / s) / step) * step, x1 = c.cx + (W - frame.x - frame.w / 2) / s;
    var y0 = Math.floor((c.cy - (H - frame.y - frame.h / 2) / s) / step) * step, y1 = c.cy + (frame.y + frame.h / 2) / s;
    ctx.beginPath();
    for (gx = x0; gx <= x1; gx += step) { var px = Math.round(X(gx)) + .5; ctx.moveTo(px, 0); ctx.lineTo(px, H); }
    for (gx = y0; gx <= y1; gx += step) { var py = Math.round(Y(gx)) + .5; ctx.moveTo(0, py); ctx.lineTo(W, py); }
    ctx.stroke();

    // the escape radius: 25 units around the centre of mass
    var cm = C.com(S), R = C.ESCAPE_R * s;
    if (R < 4 * Math.hypot(W, H)) {
      ctx.setLineDash([3, 6]); ctx.strokeStyle = '#3a2f3a'; ctx.beginPath(); ctx.arc(X(cm.x), Y(cm.y), R, 0, Math.PI * 2); ctx.stroke(); ctx.setLineDash([]);
      var la = -Math.PI / 4, lx = X(cm.x) + R * Math.cos(la) + 8, ly = Y(cm.y) + R * Math.sin(la) - 6;
      if (lx > 10 && lx < W - 150 && ly > frame.y && ly < frame.y + frame.h) { ctx.font = '12px ui-monospace, Menlo, monospace'; ctx.fillStyle = '#a58f9e'; ctx.fillText('escape radius · 25 units', lx, ly); }
    }
    // centre of mass
    ctx.strokeStyle = '#4a5d7c'; ctx.beginPath(); ctx.moveTo(X(cm.x) - 5, Y(cm.y)); ctx.lineTo(X(cm.x) + 5, Y(cm.y));
    ctx.moveTo(X(cm.x), Y(cm.y) - 5); ctx.lineTo(X(cm.x), Y(cm.y) + 5); ctx.stroke();

    // trails, fading with age
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    for (i = 0; i < N; i++) { var tr = trails[i]; if (tr.length < 2) continue;
      var n = tr.length, bands = 6;
      for (var b = 0; b < bands; b++) { var a0 = Math.floor(b * (n - 1) / bands), a1 = Math.floor((b + 1) * (n - 1) / bands); if (a1 <= a0) continue;
        ctx.strokeStyle = massColour(S.m[i], (S.escaped[i] ? 0.25 : 0.12) + (S.escaped[i] ? 0.2 : 0.5) * (b + 1) / bands); ctx.lineWidth = 1 + (b + 1) / bands;
        ctx.beginPath(); ctx.moveTo(X(tr[a0][0]), Y(tr[a0][1])); for (var q = a0 + 1; q <= a1; q++) ctx.lineTo(X(tr[q][0]), Y(tr[q][1])); ctx.stroke(); } }

    // the camera's frame: crop marks and its width
    var fx = frame.x, fy = frame.y, fw = frame.w, fh = frame.h, L = Math.min(22, fw / 8);
    ctx.strokeStyle = 'rgba(142,227,200,.75)'; ctx.lineWidth = 1.5; ctx.beginPath();
    [[fx, fy, 1, 1], [fx + fw, fy, -1, 1], [fx, fy + fh, 1, -1], [fx + fw, fy + fh, -1, -1]].forEach(function (k) {
      ctx.moveTo(k[0] + k[2] * L, k[1]); ctx.lineTo(k[0], k[1]); ctx.lineTo(k[0], k[1] + k[3] * L); });
    ctx.stroke();
    // scale bar: one grid step, bottom-left inside the frame
    var sb = step * s; ctx.strokeStyle = '#8ee3c8'; ctx.lineWidth = 1.5; ctx.beginPath();
    ctx.moveTo(fx + 12, fy + fh - 12); ctx.lineTo(fx + 12 + sb, fy + fh - 12);
    ctx.moveTo(fx + 12, fy + fh - 16); ctx.lineTo(fx + 12, fy + fh - 8); ctx.moveTo(fx + 12 + sb, fy + fh - 16); ctx.lineTo(fx + 12 + sb, fy + fh - 8); ctx.stroke();
    ctx.font = '12px ui-monospace, Menlo, monospace'; ctx.fillStyle = '#8ee3c8';
    ctx.fillText(fmtUnits(step) + (step === 1 ? ' unit' : ' units'), fx + 18 + sb, fy + fh - 8);

    // bodies: bound members bright and named; escaped members hollow, or an edge tick when off screen
    var big = s * 0.02;
    for (i = 0; i < N; i++) {
      var bx = X(S.X[2 * i]), by = Y(S.X[2 * i + 1]), rad = 2 + 2.6 * Math.cbrt(S.m[i]), esc = S.escaped[i];
      if (bx > -10 && bx < W + 10 && by > -10 && by < H + 10) {
        if (!esc) { var g = ctx.createRadialGradient(bx, by, 0, bx, by, rad * 3.4); g.addColorStop(0, massColour(S.m[i], .45)); g.addColorStop(1, massColour(S.m[i], 0));
          ctx.fillStyle = g; ctx.beginPath(); ctx.arc(bx, by, rad * 3.4, 0, Math.PI * 2); ctx.fill();
          ctx.fillStyle = massColour(S.m[i], 1); ctx.beginPath(); ctx.arc(bx, by, rad, 0, Math.PI * 2); ctx.fill(); }
        else { ctx.strokeStyle = massColour(S.m[i], .7); ctx.lineWidth = 1.2; ctx.beginPath(); ctx.arc(bx, by, rad, 0, Math.PI * 2); ctx.stroke(); }
        ctx.font = (i === picked ? '600 14px ' : '12px ') + 'ui-monospace, Menlo, monospace';
        ctx.fillStyle = esc ? '#9d8f99' : i === picked ? '#ffffff' : '#b7c2d3';
        ctx.fillText(NAMES[i], bx + rad + 3, by - rad - 1);
        if (i === picked) { ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 1; ctx.beginPath(); ctx.arc(bx, by, rad + 5, 0, Math.PI * 2); ctx.stroke(); }
      } else if (esc) {
        var ang = Math.atan2(by - (fy + fh / 2), bx - (fx + fw / 2)), ex = Math.max(6, Math.min(W - 6, fx + fw / 2 + Math.cos(ang) * W)), ey = Math.max(6, Math.min(H - 6, fy + fh / 2 + Math.sin(ang) * H));
        ctx.save(); ctx.translate(ex, ey); ctx.rotate(ang); ctx.fillStyle = 'rgba(157,143,153,.8)'; ctx.fillRect(-6, -1, 7, 2); ctx.restore();
      }
    }
    readouts(c); drawRail(c);
    if (picked >= 0) showCard();
  }

  function drawRail(c) {
    if (!RW) return;
    var T = Math.max(180, S.t), pad = 30, w = RW - pad - 8, h = RH - 18;
    rctx.clearRect(0, 0, RW, RH);
    var lo = Infinity, hi = -Infinity; history.forEach(function (p) { lo = Math.min(lo, p[1]); hi = Math.max(hi, p[1]); });
    lo = Math.min(lo, c.width); hi = Math.max(hi, c.width);
    var l0 = Math.floor(Math.log10(lo)), l1 = Math.max(l0 + 1, Math.ceil(Math.log10(hi)));
    var xs = function (t) { return pad + t / T * w; }, ys = function (v) { return 4 + h - (Math.log10(v) - l0) / (l1 - l0) * h; };
    rctx.font = '11px ui-monospace, Menlo, monospace'; rctx.fillStyle = '#8f9db2'; rctx.strokeStyle = '#1c2738'; rctx.lineWidth = 1;
    for (var d = l0; d <= l1; d++) { var yy = Math.round(ys(Math.pow(10, d))) + .5; rctx.beginPath(); rctx.moveTo(pad, yy); rctx.lineTo(pad + w, yy); rctx.stroke();
      rctx.fillText(d >= 0 ? String(Math.pow(10, d)) : Math.pow(10, d).toFixed(-d), 0, yy + 4); }
    for (var tt = 0, dt = RW < 600 ? 60 : 30; tt <= T; tt += dt) rctx.fillText(tt + ' s', Math.min(xs(tt) - (tt ? 10 : 0), pad + w - 34), RH - 2);
    S.escapers.forEach(function (e) { rctx.fillStyle = '#ff9a8f'; rctx.fillRect(Math.round(xs(e.t)), 4, 2, h); });
    rctx.strokeStyle = '#8ee3c8'; rctx.lineWidth = 1.5; rctx.beginPath();
    history.forEach(function (p, k) { var X = xs(p[0]), Y = ys(p[1]); if (k) rctx.lineTo(X, Y); else rctx.moveTo(X, Y); });
    rctx.lineTo(xs(S.t), ys(c.width)); rctx.stroke();
    rctx.fillStyle = '#8ee3c8'; rctx.beginPath(); rctx.arc(xs(S.t), ys(c.width), 3, 0, Math.PI * 2); rctx.fill();
  }

  var MINUS = '−';
  function signed(v, d) { return (v < 0 ? MINUS : '') + Math.abs(v).toFixed(d); }
  function readouts(c) {
    var E = C.energy(S), d = (E - S.E0) / Math.abs(S.E0), pct = Math.abs(d * 100);
    ui.time.textContent = S.t.toFixed(1) + ' s';
    ui.energy.textContent = signed(E, 3);
    ui.drift.textContent = (d >= 0 ? '+' : MINUS) + pct.toFixed(4) + '%';
    ui.drift.className = Math.abs(d) < 1e-3 ? 'ok' : Math.abs(d) < 1e-2 ? 'warn' : 'bad';
    ui.bound.textContent = (N - S.escapers.length) + '/' + N;
    ui.view.textContent = fmtUnits(c.width) + ' units wide';
    statusLine();
  }

  function statusLine() {
    var box = ui.statusBox, txt, reg, cls = '', cm = C.com(S), last = S.escapers[S.escapers.length - 1], left = S.escapers.length;
    if (last && S.t - last.t < NEWS) {
      reg = 'Escape'; cls = 'escaped';
      txt = NAMES[last.body] + ' has escaped at t = ' + last.t.toFixed(1) + ' s. ' + (left === 1 ? 'The first to leave.' : left + ' have left so far.');
    } else {
      // distances from the centre of mass of the members still bound (the escapers carry the whole system's centre with them)
      var bc = C.com(S, function (k) { return S.escaped[k]; }), far = -1, fr = 0, b = C.boundList(S);
      for (var i = 0; i < N; i++) { if (S.escaped[i]) continue; var r = Math.hypot(S.X[2 * i] - bc.x, S.X[2 * i + 1] - bc.y); if (r > fr) { fr = r; far = i; } }
      if (b.length === 2) { reg = 'Bound pair';
        txt = 'Only ' + NAMES[b[0]] + ' and ' + NAMES[b[1]] + ' remain, ' + fmtUnits(Math.hypot(S.X[2 * b[0]] - S.X[2 * b[1]], S.X[2 * b[0] + 1] - S.X[2 * b[1] + 1])) + ' units apart, bound to each other. ' + left + ' have escaped.'; }
      else if (fr > EXCURSION_R && b.length > 2) {
        var e = C.escapeTest(S, far); reg = 'Excursion'; cls = 'alert';
        txt = NAMES[far] + ' is on a wide excursion, ' + fr.toFixed(1) + ' units out, ' +
          (e.e2 < 0 ? 'still bound to the rest.' : (e.outward ? 'moving out, and for now unbound from the rest.' : 'for now unbound from the rest, but moving back in.'));
      } else if (!left) { reg = 'Intact'; txt = 'All 25 members are bound, none more than ' + fr.toFixed(1) + ' units from the centre.'; }
      else { reg = 'Bound core'; txt = (N - left) + ' still bound, ' + left + ' escaped. The latest was ' + NAMES[last.body] + ' at t = ' + last.t.toFixed(1) + ' s.'; }
    }
    if (!P.playing) txt = (reduced && S.t === 0 ? 'Reduced motion: this is the start, drawn once. Press Play to run it. ' : 'Paused. ') + txt;
    box.classList.remove('alert', 'escaped'); if (cls) box.classList.add(cls);
    if (ui.regime.textContent !== reg) ui.regime.textContent = reg;
    if (ui.status.textContent !== txt) ui.status.textContent = txt;
  }

  // ---- reading one star ----
  function showCard() {
    var i = picked, c = cam(), s = frame.w / c.width, cm = C.com(S);
    var bx = frame.x + frame.w / 2 + (S.X[2 * i] - c.cx) * s, by = frame.y + frame.h / 2 - (S.X[2 * i + 1] - c.cy) * s;
    var e = C.escapeTest(S, i), esc = S.escapers.filter(function (q) { return q.body === i; })[0];
    var bc = esc ? cm : C.com(S, function (k) { return S.escaped[k]; }), r = Math.hypot(S.X[2 * i] - bc.x, S.X[2 * i + 1] - bc.y);
    var html = '<b>' + NAMES[i] + '</b> · mass ' + S.m[i].toFixed(2) + '<br>' + fmtUnits(r) + (esc ? ' units from the centre of mass' : ' units from the bound centre') + '<br>';
    html += esc ? '<span class="pos">escaped at t = ' + esc.t.toFixed(1) + ' s</span>'
      : 'energy vs the rest: <span class="' + (e.e2 < 0 ? 'neg' : 'pos') + '">' + signed(e.e2, 2) + '</span><br>' + (e.e2 < 0 ? 'bound' : 'unbound, ' + (e.outward ? 'moving out' : 'moving in'));
    if (ui.card.innerHTML !== html) ui.card.innerHTML = html;
    ui.card.hidden = false;
    var cw = ui.card.offsetWidth, ch = ui.card.offsetHeight;
    var left = Math.max(8, Math.min(W - cw - 8, bx + 16)), top = Math.max(frame.y, Math.min(frame.y + frame.h - ch, by + 16));
    if (bx < -10 || bx > W + 10 || by < -10 || by > H + 10) { left = W - cw - 16; top = frame.y; }
    ui.card.style.left = left + 'px'; ui.card.style.top = top + 'px';
  }
  canvas.addEventListener('click', function (ev) {
    var r = canvas.getBoundingClientRect(), mx = ev.clientX - r.left, my = ev.clientY - r.top, c = cam(), s = frame.w / c.width, best = -1, bd = 22;
    for (var i = 0; i < N; i++) { var bx = frame.x + frame.w / 2 + (S.X[2 * i] - c.cx) * s, by = frame.y + frame.h / 2 - (S.X[2 * i + 1] - c.cy) * s, d = Math.hypot(bx - mx, by - my); if (d < bd) { bd = d; best = i; } }
    picked = best; if (best < 0) ui.card.hidden = true; render();
  });

  // ---- controls: every change applies on the gesture ----
  ui.play.addEventListener('click', function () { P.playing = !P.playing; syncControls(); statusLine(); if (P.playing) startLoop(); });
  ui.speed.addEventListener('input', function () { P.speed = +ui.speed.value; syncControls(); });
  ui.trail.addEventListener('input', function () { P.trail = +ui.trail.value; syncControls(); record(false); render(); });
  ui.room.addEventListener('input', function () { P.room = +ui.room.value; syncControls(); render(); });
  ui.reset.addEventListener('click', reset);

  var running = !/[?&]hold\b/.test(location.search);       // ?hold loads with the loop stopped, for exact headless QA
  function loop() {
    if (P.playing && running) {
      var per = SPEEDS[P.speed] * 4, want = per + debt, t0 = performance.now(), done = 0;
      while (done < want && performance.now() - t0 < 28) { oneTick(); done++; }
      debt = Math.min(want - done, 16); frames++;              // a heavy stretch (a tight pass) may fall behind; it never skips physics
      render();
    }
    requestAnimationFrame(loop);
  }

  // ---- QA handle: the page's own live state ----
  function names(list) { return list.map(function (e) { return { body: e.body, name: NAMES[e.body], t: e.t }; }); }
  window.__cluster = {
    get state() { var p = C.snapshot(S); p.names = NAMES.slice(); p.escapers = names(S.escapers); p.boundCount = p.bound; p.camera = cam(); p.tick = S.tick; return p; },
    get params() { return Object.assign({ fill: camOpts().fill, aspect: camOpts().aspect }, P); },
    get readouts() { return { time: ui.time.textContent, energy: ui.energy.textContent, drift: ui.drift.textContent, bound: ui.bound.textContent,
      view: ui.view.textContent, regime: ui.regime.textContent, status: ui.status.textContent }; },
    // camera(state): the shipped camera with this page's framing options; any snapshot-shaped state, or the live one
    camera: function (state) { return C.camera(state ? (state.positions ? C.fromSnapshot(state) : state) : S, camOpts()); },
    advanceTo: function (t) { while (S.t < t - 1e-12) oneTick(); render(); return this.state; },
    advanceFrames: function (n) { advanceFrames(n); render(); return this.state; },
    hold: function (on) { running = on === false; },
    reset: reset, model: C, names: NAMES
  };

  P = Object.assign({}, DEFAULTS); if (reduced) P.playing = false;
  syncControls(); window.addEventListener('resize', layout); layout(); start();
  // under prefers-reduced-motion the start is drawn once and nothing runs until the visitor presses Play
  var looping = false;
  function startLoop() { if (!looping) { looping = true; requestAnimationFrame(loop); } }
  if (!reduced) startLoop();
})();
