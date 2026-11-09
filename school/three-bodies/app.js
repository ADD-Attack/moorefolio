// Three bodies — the interface. Reads the model in sim.js; every number drawn here comes from the live state.
(function () {
  'use strict';
  var TB = window.ThreeBody;
  var DEFAULTS = { preset: 'figure8', seed: 1, speed: 1, trail: 7, G: 1, playing: true };
  var NAMES = ['α', 'β', 'γ'];
  var COLOURS = ['#ffb547', '#5cc8ff', '#ff7a8a'];
  var VIEW = { figure8: 1.45, pythagorean: 5.6, random: 5.6 };   // half-height of the view, model units

  var $ = function (id) { return document.getElementById(id); };
  var canvas = $('view'), ctx = canvas.getContext('2d');
  var ui = { preset: $('c-preset'), seed: $('c-seed'), newseed: $('c-newseed'), seedField: $('seed-field'), play: $('c-play'),
    speed: $('c-speed'), trail: $('c-trail'), g: $('c-g'), reset: $('c-reset'),
    oSpeed: $('o-speed'), oTrail: $('o-trail'), oG: $('o-g'),
    energy: $('r-energy'), drift: $('r-drift'), time: $('r-time'), closest: $('r-closest'),
    regime: $('regime'), status: $('status'), statusBox: document.querySelector('.status') };

  var P, sim, E0, trails, ejection, frames;

  function presetFor(p) { return p.preset === 'random' ? TB.randomPreset(p.seed) : TB.PRESETS[p.preset]; }

  // start (or restart) the current arrangement: time, trails, drift baseline and ejection record all go back to zero
  function start() {
    sim = TB.make(presetFor(P), P.G);
    E0 = TB.energy(sim); trails = [[], [], []]; ejection = null; frames = 0;
    for (var i = 0; i < 3; i++) $('m' + i).textContent = 'm ' + sim.m[i].toFixed(2);
    ui.regime.textContent = presetFor(P).name;
    ui.seedField.hidden = P.preset !== 'random';
    record(); render();
  }

  function syncControls() {
    ui.preset.value = P.preset; ui.seed.value = P.seed; ui.speed.value = P.speed; ui.trail.value = P.trail; ui.g.value = P.G;
    ui.oSpeed.textContent = '×' + P.speed.toFixed(2);
    ui.oTrail.textContent = P.trail === 0 ? 'off' : P.trail.toFixed(1) + ' s';
    ui.oG.textContent = 'G = ' + P.G.toFixed(2);
    ui.play.textContent = P.playing ? 'Pause' : 'Play';
    ui.play.setAttribute('aria-pressed', String(!P.playing));
  }

  function reset() { P = Object.assign({}, DEFAULTS); syncControls(); start(); }

  // ---- stepping ----
  function advanceFrames(n) {
    var steps = Math.round(TB.SUBSTEPS * P.speed);
    for (var f = 0; f < n; f++) { for (var k = 0; k < steps; k++) TB.substep(sim); frames++; record(); }
  }

  function record() {
    for (var i = 0; i < 3; i++) trails[i].push([sim.x[i][0], sim.x[i][1], sim.t]);
    var cut = sim.t - P.trail;
    for (i = 0; i < 3; i++) { var tr = trails[i], d = 0; while (d < tr.length - 1 && tr[d][2] < cut) d++; if (d) tr.splice(0, d); }
    if (P.trail === 0) trails = [[], [], []];
    var out = TB.ejected(sim).filter(function (o) { return o.outward && o.unbound; });
    if (out.length && !ejection) {
      out.sort(function (a, b) { return b.r - a.r; });
      ejection = { body: out[0].body, t: sim.t };
    }
  }

  // ---- drawing ----
  var W = 0, Hh = 0, dpr = 1;
  function size() {
    var r = canvas.getBoundingClientRect(); dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = r.width; Hh = r.height; canvas.width = Math.round(W * dpr); canvas.height = Math.round(Hh * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0); render();
  }

  function camera() {
    var narrow = W < 600;
    var usable = narrow ? Hh - 220 : Hh - 150;           // keep the scene clear of the status line and readout pill
    var half = Math.max(120, Math.min(usable, W - 40) / 2);
    return { s: half / VIEW[P.preset], cx: W / 2, cy: (narrow ? 70 : 52) + usable / 2 + (narrow ? 12 : 0) };
  }

  function render() {
    if (!W) return;
    var cam = camera(), c = TB.com(sim);
    var X = function (x) { return cam.cx + (x - c[0]) * cam.s; }, Y = function (y) { return cam.cy - (y - c[1]) * cam.s; };
    ctx.clearRect(0, 0, W, Hh);

    // grid: one line per 0.5 or 1 model unit, whichever is nearer 64 px
    var step = cam.s * 0.5 > 48 ? 0.5 : 1, gx, i;
    ctx.lineWidth = 1;
    var x0 = Math.floor((c[0] - cam.cx / cam.s) / step) * step, x1 = c[0] + (W - cam.cx) / cam.s;
    var y0 = Math.floor((c[1] - (Hh - cam.cy) / cam.s) / step) * step, y1 = c[1] + cam.cy / cam.s;
    ctx.font = '11px ui-monospace, Menlo, monospace'; ctx.fillStyle = '#7d8ca3';
    for (gx = x0; gx <= x1; gx += step) { var px = Math.round(X(gx)) + .5;
      ctx.strokeStyle = Math.abs(gx) < 1e-9 ? '#22314a' : '#141e2d'; ctx.beginPath(); ctx.moveTo(px, 0); ctx.lineTo(px, Hh); ctx.stroke(); }
    for (gx = y0; gx <= y1; gx += step) { var py = Math.round(Y(gx)) + .5;
      ctx.strokeStyle = Math.abs(gx) < 1e-9 ? '#22314a' : '#141e2d'; ctx.beginPath(); ctx.moveTo(0, py); ctx.lineTo(W, py); ctx.stroke(); }
    ctx.fillText(step + ' unit grid', 20, Hh - 18 - (W < 600 ? 110 : 0));

    // view bound: the ejection radius around the centre of mass
    var R = TB.VIEW_BOUND * cam.s;
    if (R < Math.hypot(W, Hh)) {
      ctx.setLineDash([3, 6]); ctx.strokeStyle = '#2c3d58'; ctx.beginPath(); ctx.arc(X(c[0]), Y(c[1]), R, 0, Math.PI * 2); ctx.stroke(); ctx.setLineDash([]);
      ctx.fillStyle = '#6f7f98'; var vb = 'view bound · ' + TB.VIEW_BOUND + ' units'; ctx.fillText(vb, Math.min(X(c[0]) + R * 0.71 + 6, W - ctx.measureText(vb).width - 10), Y(c[1]) - R * 0.71 - 6);
    }
    // centre of mass
    ctx.strokeStyle = '#3a4c69'; ctx.beginPath(); ctx.moveTo(X(c[0]) - 5, Y(c[1])); ctx.lineTo(X(c[0]) + 5, Y(c[1]));
    ctx.moveTo(X(c[0]), Y(c[1]) - 5); ctx.lineTo(X(c[0]), Y(c[1]) + 5); ctx.stroke();

    // trails: each body's own colour, fading with age, drawn in eight bands
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    for (i = 0; i < 3; i++) {
      var tr = trails[i]; if (tr.length < 2) continue;
      var n = tr.length, bands = 8;
      for (var b = 0; b < bands; b++) {
        var a0 = Math.floor(b * (n - 1) / bands), a1 = Math.floor((b + 1) * (n - 1) / bands); if (a1 <= a0) continue;
        ctx.globalAlpha = 0.12 + 0.78 * (b + 1) / bands; ctx.strokeStyle = COLOURS[i]; ctx.lineWidth = 1.2 + 1.2 * (b + 1) / bands;
        ctx.beginPath(); ctx.moveTo(X(tr[a0][0]), Y(tr[a0][1]));
        for (var q = a0 + 1; q <= a1; q++) ctx.lineTo(X(tr[q][0]), Y(tr[q][1]));
        ctx.stroke();
      }
    }
    ctx.globalAlpha = 1;

    // bodies, or an edge marker with the distance when a body is off-screen
    for (i = 0; i < 3; i++) {
      var bx = X(sim.x[i][0]), by = Y(sim.x[i][1]), rad = 4 + 3.2 * Math.cbrt(sim.m[i]);
      if (bx > -rad && bx < W + rad && by > -rad && by < Hh + rad) {
        var g = ctx.createRadialGradient(bx, by, 0, bx, by, rad * 3.2);
        g.addColorStop(0, COLOURS[i] + '66'); g.addColorStop(1, COLOURS[i] + '00');
        ctx.fillStyle = g; ctx.beginPath(); ctx.arc(bx, by, rad * 3.2, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = COLOURS[i]; ctx.beginPath(); ctx.arc(bx, by, rad, 0, Math.PI * 2); ctx.fill();
        ctx.font = '600 13px ui-monospace, Menlo, monospace'; ctx.fillText(NAMES[i], bx + rad + 5, by - rad - 3);
      } else {
        var ang = Math.atan2(by - cam.cy, bx - cam.cx), m = 26;
        var ex = Math.max(m, Math.min(W - m, cam.cx + Math.cos(ang) * W)), ey = Math.max(W < 600 ? 150 : m + 40, Math.min(Hh - m - (W < 600 ? 140 : 70), cam.cy + Math.sin(ang) * Hh));
        ctx.save(); ctx.translate(ex, ey); ctx.rotate(ang); ctx.fillStyle = COLOURS[i];
        ctx.beginPath(); ctx.moveTo(10, 0); ctx.lineTo(-6, -7); ctx.lineTo(-6, 7); ctx.closePath(); ctx.fill(); ctx.restore();
        var dist = Math.hypot(sim.x[i][0] - c[0], sim.x[i][1] - c[1]);
        ctx.font = '600 12px ui-monospace, Menlo, monospace'; ctx.textAlign = ex > W / 2 ? 'right' : 'left';
        ctx.fillText(NAMES[i] + ' ' + dist.toFixed(1), ex + (ex > W / 2 ? -16 : 16), ey + 4); ctx.textAlign = 'left';
      }
    }
    readouts();
  }

  var MINUS = '−';
  function signed(v, d) { return (v < 0 ? MINUS : '') + Math.abs(v).toFixed(d); }

  function readouts() {
    var E = TB.energy(sim), d = (E - E0) / Math.abs(E0);
    ui.energy.textContent = signed(E, 5);
    var pct = Math.abs(d * 100);   // below 0.0001 % the fixed format would print zero, so show the exponent instead
    ui.drift.textContent = (d >= 0 ? '+' : MINUS) + (pct === 0 ? '0' : pct < 1e-4 ? pct.toExponential(1).replace('-', MINUS) : pct.toFixed(4)) + '%';
    ui.drift.className = Math.abs(d) < 1e-4 ? 'ok' : Math.abs(d) < 1e-2 ? 'warn' : 'bad';
    ui.time.textContent = sim.t.toFixed(2) + ' s';
    ui.closest.textContent = TB.closest(sim).toFixed(3);
    statusLine();
  }

  function statusLine() {
    var c = TB.com(sim), box = ui.statusBox, txt, i;
    box.classList.remove('alert', 'ejected');
    if (ejection) {
      i = ejection.body; var j = (i + 1) % 3, k = (i + 2) % 3;
      var r = Math.hypot(sim.x[i][0] - c[0], sim.x[i][1] - c[1]);
      txt = NAMES[i] + ' (mass ' + sim.m[i].toFixed(0) + ') was ejected at t = ' + ejection.t.toFixed(1) + ' s and is ' + r.toFixed(1) + ' units out, unbound and receding.';
      if (P.preset === 'random') txt = txt.replace('(mass ' + sim.m[i].toFixed(0) + ')', '(mass ' + sim.m[i].toFixed(2) + ')');
      txt += TB.pairEnergy(sim, j, k) < 0 ? ' ' + NAMES[j] + ' and ' + NAMES[k] + ' recoil the other way as a bound pair.' : ' ' + NAMES[j] + ' and ' + NAMES[k] + ' are not bound to each other either.';
      box.classList.add('ejected');
    } else {
      var far = TB.ejected(sim);
      if (far.length) {
        var o = far.sort(function (a, b) { return b.r - a.r; })[0];
        txt = NAMES[o.body] + ' is past the view bound (' + o.r.toFixed(1) + ' units out) but still bound, so it will fall back.';
        box.classList.add('alert');
      } else if (TB.closest(sim) < 0.05) {
        txt = 'Close encounter: two bodies are ' + TB.closest(sim).toFixed(3) + ' units apart.'; box.classList.add('alert');
      } else txt = 'All three bodies are inside the view bound.';
    }
    if (!P.playing) txt = 'Paused. ' + txt;
    if (ui.status.textContent !== txt) ui.status.textContent = txt;
  }

  // ---- controls: every change applies on the gesture ----
  ui.preset.addEventListener('change', function () { P.preset = ui.preset.value; syncControls(); start(); });
  ui.seed.addEventListener('change', function () {
    var v = Math.max(1, Math.min(99999, Math.round(+ui.seed.value) || 1)); P.seed = v; syncControls(); start(); });
  ui.newseed.addEventListener('click', function () { P.seed = 1 + Math.floor(Math.random() * 99999); syncControls(); start(); });
  ui.play.addEventListener('click', function () { P.playing = !P.playing; syncControls(); statusLine(); });
  ui.speed.addEventListener('input', function () { P.speed = +ui.speed.value; syncControls(); });
  ui.trail.addEventListener('input', function () { P.trail = +ui.trail.value; syncControls(); record(); render(); });
  ui.g.addEventListener('input', function () {
    P.G = +ui.g.value; sim.G = P.G; TB.accel(sim); E0 = TB.energy(sim); syncControls(); render(); });   // a new G is a new system: drift re-bases
  ui.reset.addEventListener('click', reset);

  var running = !/[?&]hold\b/.test(location.search);   // ?hold loads with the loop stopped, for exact headless QA
  function loop() { if (P.playing && running) { advanceFrames(1); render(); } requestAnimationFrame(loop); }

  // ---- QA handle: the page's own live state ----
  window.__sim = {
    get state() { return { t: sim.t, G: sim.G, m: sim.m.slice(), x: sim.x.map(function (p) { return p.slice(); }),
      v: sim.v.map(function (p) { return p.slice(); }), energy: TB.energy(sim), E0: E0, closest: TB.closest(sim),
      com: TB.com(sim), ejection: ejection && { body: ejection.body, name: NAMES[ejection.body], t: ejection.t },
      frames: frames, substeps: sim.steps }; },
    get params() { return Object.assign({}, P); },
    get readouts() { return { energy: ui.energy.textContent, drift: ui.drift.textContent, time: ui.time.textContent,
      closest: ui.closest.textContent, status: ui.status.textContent }; },
    energy: function () { return TB.energy(sim); },
    // drive headlessly: run whole frames at the current speed until model time ≥ t, then draw once
    advanceTo: function (t) { while (sim.t < t - 1e-12) advanceFrames(1); render(); return this.state; },
    advanceFrames: function (n) { advanceFrames(n); render(); return this.state; },
    hold: function (on) { running = !on; },        // stop the animation loop so headless driving is exact
    reset: reset, model: TB
  };

  P = Object.assign({}, DEFAULTS); syncControls(); start();
  window.addEventListener('resize', size); size(); requestAnimationFrame(loop);
})();
