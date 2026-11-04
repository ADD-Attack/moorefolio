/* Console — W-Ex5. Every visual below is drawn by this script; no image files are loaded. Nothing is sent anywhere. */
(function () {
  'use strict';
  var RM = window.matchMedia('(prefers-reduced-motion: reduce)');
  var reduced = RM.matches;
  var TAU = Math.PI * 2;
  var CY = '111,220,255', OK = '124,240,196', AMB = '255,191,107';

  // ---------- helpers ----------
  function rng(seed) { var s = seed >>> 0; return function () { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }
  function hash3(x, y, z) { var h = Math.sin(x * 127.1 + y * 311.7 + z * 74.7) * 43758.5453; return h - Math.floor(h); }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function sm(t) { return t * t * (3 - 2 * t); }
  function noise3(x, y, z) {
    var xi = Math.floor(x), yi = Math.floor(y), zi = Math.floor(z), xf = sm(x - xi), yf = sm(y - yi), zf = sm(z - zi);
    function c(a, b, d) { return hash3(xi + a, yi + b, zi + d); }
    return lerp(lerp(lerp(c(0,0,0), c(1,0,0), xf), lerp(c(0,1,0), c(1,1,0), xf), yf),
                lerp(lerp(c(0,0,1), c(1,0,1), xf), lerp(c(0,1,1), c(1,1,1), xf), yf), zf);
  }
  function fbm(x, y, z) { var v = 0, a = .5, f = 1; for (var i = 0; i < 4; i++) { v += a * noise3(x * f, y * f, z * f); a *= .5; f *= 2.03; } return v; }

  var views = [];
  function view(id, draw) {
    var cv = document.getElementById(id); if (!cv) return null;
    var v = { cv: cv, ctx: cv.getContext('2d'), w: 0, h: 0, draw: draw, yaw: 0, drag: 0 };
    function size() {
      var r = cv.getBoundingClientRect(), d = Math.min(window.devicePixelRatio || 1, 2);
      v.w = Math.max(1, r.width); v.h = Math.max(1, r.height);
      cv.width = Math.round(v.w * d); cv.height = Math.round(v.h * d);
      v.ctx.setTransform(d, 0, 0, d, 0, 0);
      if (v.resize) v.resize();
      if (reduced) v.draw(v, 0);
    }
    v.size = size;
    if ('ResizeObserver' in window) new ResizeObserver(size).observe(cv); else window.addEventListener('resize', size);
    size(); views.push(v); return v;
  }
  function draggable(v) {
    var down = false, lx = 0;
    v.cv.style.cursor = 'grab'; v.cv.style.touchAction = 'pan-y';
    v.cv.addEventListener('pointerdown', function (e) { down = true; lx = e.clientX; v.cv.setPointerCapture(e.pointerId); v.cv.style.cursor = 'grabbing'; });
    v.cv.addEventListener('pointermove', function (e) { if (!down) return; v.drag += (e.clientX - lx) * 0.01; lx = e.clientX; if (reduced) v.draw(v, 0); });
    function up() { down = false; v.cv.style.cursor = 'grab'; }
    v.cv.addEventListener('pointerup', up); v.cv.addEventListener('pointercancel', up);
  }
  function glow(ctx, x, y, r, rgb, a) {
    var g = ctx.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, 'rgba(' + rgb + ',' + a + ')'); g.addColorStop(1, 'rgba(' + rgb + ',0)');
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill();
  }

  // ---------- 1. orbital system ----------
  var planets = [
    { a: .30, sp: .55, r: 6,  col: '#c9a27a', ph: 1.2 },
    { a: .44, sp: .38, r: 9,  col: '#4aa8e8', ph: 3.9, earth: true },
    { a: .58, sp: .26, r: 8,  col: '#d0603c', ph: 5.4, mars: true },
    { a: .76, sp: .16, r: 12, col: '#b98a5e', ph: 2.3 },
    { a: .92, sp: .10, r: 7,  col: '#8fb8c8', ph: .4 }
  ];
  view('cv-orbit', function (v, t) {
    var c = v.ctx, w = v.w, h = v.h, cx = w / 2, cy = h * .45, R = Math.min(w * .48, h * .5), tilt = .32;
    c.clearRect(0, 0, w, h);
    glow(c, cx, cy, R * 1.05, '40,120,220', .22);
    // wireframe globe around the star
    var gR = R * .42, spin = t * .00012;
    c.lineWidth = 1;
    for (var i = 1; i < 9; i++) {
      var lat = -Math.PI / 2 + i * Math.PI / 9, yy = Math.sin(lat) * gR, rr = Math.cos(lat) * gR;
      c.strokeStyle = 'rgba(' + CY + ',.22)'; c.beginPath(); c.ellipse(cx, cy + yy, rr, rr * .28, 0, 0, TAU); c.stroke();
    }
    for (var m = 0; m < 12; m++) {
      var lo = m * Math.PI / 12 + spin, sx = Math.cos(lo);
      c.strokeStyle = 'rgba(' + CY + ',' + (.1 + .25 * Math.abs(Math.sin(lo))) + ')';
      c.beginPath(); c.ellipse(cx, cy, Math.abs(sx) * gR, gR, 0, 0, TAU); c.stroke();
    }
    c.strokeStyle = 'rgba(' + CY + ',.6)'; c.lineWidth = 1.5; c.beginPath(); c.arc(cx, cy, gR, 0, TAU); c.stroke();
    // orbits, back halves first
    var ps = planets.map(function (p) {
      var ang = p.ph + (reduced ? 0 : t * .0004 * p.sp), ax = p.a * R * 1.05;
      return { p: p, x: cx + Math.cos(ang) * ax, y: cy + Math.sin(ang) * ax * tilt, z: Math.sin(ang), ax: ax };
    });
    ps.forEach(function (q) {
      c.strokeStyle = 'rgba(' + CY + ',.38)'; c.lineWidth = 1;
      c.beginPath(); c.ellipse(cx, cy, q.ax, q.ax * tilt, 0, 0, TAU); c.stroke();
      c.strokeStyle = 'rgba(' + CY + ',.12)'; c.beginPath(); c.ellipse(cx, cy, q.ax + 4, q.ax * tilt + 1.5, 0, 0, TAU); c.stroke();
    });
    function planet(q) {
      var s = q.p.r * (1 + q.z * .18);
      glow(c, q.x, q.y, s * 3, q.p.mars ? AMB : CY, .25);
      var g = c.createRadialGradient(q.x - s * .4, q.y - s * .4, s * .1, q.x, q.y, s);
      g.addColorStop(0, '#fff'); g.addColorStop(.25, q.p.col); g.addColorStop(1, '#050a10');
      c.fillStyle = g; c.beginPath(); c.arc(q.x, q.y, s, 0, TAU); c.fill();
      if (q.p.earth || q.p.mars) { // leader lines towards their tags
        c.strokeStyle = 'rgba(' + (q.p.mars ? AMB : CY) + ',.6)'; c.setLineDash([3, 3]);
        c.beginPath(); c.moveTo(q.x, q.y); c.lineTo(q.p.mars ? w - 70 : 70, h - 52); c.stroke(); c.setLineDash([]);
      }
    }
    ps.filter(function (q) { return q.z < 0; }).forEach(planet);
    // star core
    var pulse = reduced ? 1 : 1 + .06 * Math.sin(t * .003);
    glow(c, cx, cy, R * .3 * pulse, '255,170,80', .55);
    c.strokeStyle = 'rgba(255,190,110,.95)'; c.lineWidth = 3; c.beginPath(); c.arc(cx, cy, R * .1 * pulse, 0, TAU); c.stroke();
    c.strokeStyle = 'rgba(255,150,60,.5)'; c.lineWidth = 1; c.beginPath(); c.arc(cx, cy, R * .14, 0, TAU); c.stroke();
    glow(c, cx, cy, R * .07, '160,230,255', .95);
    ps.filter(function (q) { return q.z >= 0; }).forEach(planet);
  });

  // ---------- 2. star map ----------
  var stars = (function () {
    var r = rng(9), a = [];
    for (var i = 0; i < 150; i++) {
      var th = r() * TAU, ph = Math.acos(2 * r() - 1), rad = .6 + r() * .4;
      a.push({ x: Math.sin(ph) * Math.cos(th) * rad * 1.6, y: Math.cos(ph) * rad * .55, z: Math.sin(ph) * Math.sin(th) * rad, b: r(), tw: r() * TAU });
    }
    a[0] = { x: -1.25, y: .3, z: .2, b: 1, tw: 0, name: 'Proxima Centauri', sub: '4.24 LY' };
    a[1] = { x: 1.2, y: -.3, z: .2, b: 1, tw: 1, name: 'Kepler-442b', sub: 'Habitable zone' };
    a.forEach(function (s, i) { // two nearest neighbours
      var d = a.map(function (o, j) { return [j, (o.x-s.x)*(o.x-s.x)+(o.y-s.y)*(o.y-s.y)+(o.z-s.z)*(o.z-s.z)]; }).filter(function (p) { return p[0] !== i; }).sort(function (p, q) { return p[1] - q[1]; });
      s.n = [d[0][0], d[1][0]];
    });
    return a;
  })();
  var sv = view('cv-star', function (v, t) {
    var c = v.ctx, w = v.w, h = v.h, cx = w / 2, cy = h / 2, S = Math.min(w / 3.6, h / 1.3);
    var yaw = (reduced ? 0 : Math.sin(t * .00008) * .5) + v.drag, cs = Math.cos(yaw), sn = Math.sin(yaw);
    c.clearRect(0, 0, w, h);
    glow(c, cx, cy, S * .5, '150,110,255', .25); glow(c, cx, cy, S * .18, '230,200,255', .5);
    var P = stars.map(function (s) {
      var x = s.x * cs - s.z * sn, z = s.x * sn + s.z * cs, k = 2.6 / (2.6 + z);
      return { x: cx + x * S * k, y: cy + s.y * S * k * 1.6, z: z, k: k };
    });
    c.lineWidth = .8;
    stars.forEach(function (s, i) {
      s.n.forEach(function (j) {
        if (j < i) return;
        var a = P[i], b = P[j];
        c.strokeStyle = 'rgba(' + CY + ',' + (.12 + .2 * (1 - (a.z + 1) / 2)) + ')';
        c.beginPath(); c.moveTo(a.x, a.y); c.lineTo(b.x, b.y); c.stroke();
      });
    });
    stars.forEach(function (s, i) {
      var p = P[i], tw = reduced ? .8 : .55 + .45 * Math.sin(t * .002 + s.tw * 7);
      var r = (.6 + s.b * 1.4) * p.k;
      c.fillStyle = 'rgba(220,240,255,' + (.35 + .65 * tw * s.b) + ')'; c.beginPath(); c.arc(p.x, p.y, r, 0, TAU); c.fill();
      if (s.name) {
        glow(c, p.x, p.y, 14, s.sub === '4.24 LY' ? AMB : OK, .6);
        c.strokeStyle = 'rgba(' + CY + ',.9)'; c.beginPath(); c.arc(p.x, p.y, 7, 0, TAU); c.stroke();
        var lx = p.x + (p.x < cx ? 12 : -12), al = p.x < cx ? 'left' : 'right';
        c.font = '600 12px ui-monospace, DejaVu Sans Mono, monospace'; c.textAlign = al;
        var tw1 = Math.max(c.measureText(s.name.toUpperCase()).width, c.measureText(s.sub.toUpperCase()).width) + 10;
        c.fillStyle = 'rgba(4,12,22,.9)'; c.fillRect(al === 'left' ? lx - 5 : lx - tw1 + 5, p.y - 26, tw1, 34);
        c.fillStyle = '#e4f4ff'; c.fillText(s.name.toUpperCase(), lx, p.y - 12);
        c.fillStyle = s.sub === '4.24 LY' ? '#ffbf6b' : '#7cf0c4'; c.fillText(s.sub.toUpperCase(), lx, p.y + 3);
      }
    });
  });
  if (sv) draggable(sv);

  // ---------- 3. Earth & LEO ----------
  var landPts = (function () {
    var a = [];
    for (var la = -84; la <= 84; la += 2.4) {
      var n = Math.max(6, Math.round(150 * Math.cos(la * Math.PI / 180)));
      for (var k = 0; k < n; k++) {
        var lo = k / n * TAU, lr = la * Math.PI / 180;
        var x = Math.cos(lr) * Math.cos(lo), y = Math.sin(lr), z = Math.cos(lr) * Math.sin(lo);
        var v = fbm(x * 1.6 + 3, y * 1.6, z * 1.6);
        if (v > .47 || Math.abs(la) > 72) a.push({ lr: lr, lo: lo, ice: Math.abs(la) > 70 });
      }
    }
    return a;
  })();
  var sats = [], leo = [];
  (function () {
    var r = rng(42);
    for (var i = 0; i < 6; i++) sats.push({ inc: (r() - .5) * 1.4, node: r() * TAU, rad: 1.38 + r() * .3, sp: .5 + r() * .5, ph: r() * TAU });
    for (var j = 0; j < 142; j++) leo.push({ inc: (r() - .5) * 2.2, node: r() * TAU, rad: 1.1 + r() * .05, ph: r() * TAU, sp: .8 + r() * .6 });
  })();
  function orbitPt(o, a) { // circle in plane with inclination inc and node angle
    var x = Math.cos(a) * o.rad, z = Math.sin(a) * o.rad, y = z * Math.sin(o.inc); z = z * Math.cos(o.inc);
    var cn = Math.cos(o.node), sn = Math.sin(o.node);
    return { x: x * cn - z * sn, y: y, z: x * sn + z * cn };
  }
  var ev = view('cv-earth', function (v, t) {
    var c = v.ctx, w = v.w, h = v.h, cx = w / 2, cy = h / 2, R = Math.min(w, h) * .3;
    var rot = (reduced ? 0 : t * .00012) + v.drag, tilt = .35, ct = Math.cos(tilt), st = Math.sin(tilt);
    c.clearRect(0, 0, w, h);
    glow(c, cx, cy, R * 1.6, '60,150,240', .3);
    var g = c.createRadialGradient(cx - R * .35, cy - R * .35, R * .1, cx, cy, R);
    g.addColorStop(0, '#1d4f7e'); g.addColorStop(.7, '#0b2742'); g.addColorStop(1, '#04111e');
    c.fillStyle = g; c.beginPath(); c.arc(cx, cy, R, 0, TAU); c.fill();
    // graticule
    c.lineWidth = .7; c.strokeStyle = 'rgba(' + CY + ',.18)';
    for (var i = -2; i <= 2; i++) { var yy = Math.sin(i * .5) * R, rr = Math.cos(i * .5) * R; c.beginPath(); c.ellipse(cx, cy + yy * ct, rr, rr * st, 0, 0, TAU); c.stroke(); }
    // land dots
    landPts.forEach(function (p) {
      var lo = p.lo + rot, x = Math.cos(p.lr) * Math.cos(lo), y = Math.sin(p.lr), z = Math.cos(p.lr) * Math.sin(lo);
      var y2 = y * ct - z * st, z2 = y * st + z * ct;
      if (z2 < 0) return;
      c.fillStyle = p.ice ? 'rgba(235,248,255,' + (.4 + .6 * z2) + ')' : 'rgba(150,230,200,' + (.25 + .7 * z2) + ')';
      c.fillRect(cx + x * R - 1, cy - y2 * R - 1, 1.8, 1.8);
    });
    c.strokeStyle = 'rgba(' + CY + ',.75)'; c.lineWidth = 1.5; c.beginPath(); c.arc(cx, cy, R, 0, TAU); c.stroke();
    glow(c, cx, cy, R * 1.12, '120,200,255', .0);
    var ta = reduced ? 0 : t * .00035;
    function proj(p) { var y2 = p.y * ct - p.z * st, z2 = p.y * st + p.z * ct; return { x: cx + p.x * R, y: cy - y2 * R, z: z2 }; }
    function hidden(q) { var dx = q.x - cx, dy = q.y - cy; return q.z < 0 && dx * dx + dy * dy < R * R; }
    // LEO shell: 142 active
    leo.forEach(function (o) { var q = proj(orbitPt(o, o.ph + ta * o.sp)); if (hidden(q)) return; c.fillStyle = 'rgba(' + OK + ',.85)'; c.fillRect(q.x - 1, q.y - 1, 2, 2); });
    // big satellites with orbit paths
    sats.forEach(function (o, i) {
      c.strokeStyle = 'rgba(' + CY + ',.28)'; c.lineWidth = 1; c.beginPath();
      for (var k = 0; k <= 64; k++) { var q = proj(orbitPt(o, k / 64 * TAU)); if (k) c.lineTo(q.x, q.y); else c.moveTo(q.x, q.y); }
      c.stroke();
      var s = proj(orbitPt(o, o.ph + ta * o.sp)); if (hidden(s)) return;
      var sc = .8 + .3 * s.z;
      c.save(); c.translate(s.x, s.y); c.rotate(i);
      c.fillStyle = '#cfe6f5'; c.fillRect(-3 * sc, -4 * sc, 6 * sc, 8 * sc);
      c.fillStyle = 'rgba(70,140,220,.95)'; c.strokeStyle = 'rgba(' + CY + ',.9)';
      c.fillRect(-15 * sc, -3 * sc, 10 * sc, 6 * sc); c.strokeRect(-15 * sc, -3 * sc, 10 * sc, 6 * sc);
      c.fillRect(5 * sc, -3 * sc, 10 * sc, 6 * sc); c.strokeRect(5 * sc, -3 * sc, 10 * sc, 6 * sc);
      c.restore(); glow(c, s.x, s.y, 10, CY, .35);
      // comm link to the globe
      c.strokeStyle = 'rgba(' + OK + ',.25)'; c.setLineDash([2, 4]); c.beginPath(); c.moveTo(s.x, s.y); c.lineTo(cx, cy); c.stroke(); c.setLineDash([]);
    });
  });
  if (ev) draggable(ev);

  // ---------- 4. vessel wireframe ----------
  var ship = (function () {
    var V = [], E = [], prof = [[-1.6, .05], [-1.3, .16], [-.8, .24], [-.2, .28], [.5, .3], [1.0, .34], [1.3, .3], [1.45, .22]], seg = 8;
    prof.forEach(function (p, i) {
      for (var k = 0; k < seg; k++) { var a = k / seg * TAU; V.push([p[0], Math.cos(a) * p[1], Math.sin(a) * p[1] * .8]);
        var id = i * seg + k; E.push([id, i * seg + (k + 1) % seg]); if (i) E.push([id, id - seg]); }
    });
    function add(pts, edges) { var b = V.length; pts.forEach(function (p) { V.push(p); }); edges.forEach(function (e) { E.push([e[0] + b, e[1] + b]); }); }
    // wings
    add([[-.2, 0, .25], [.9, 0, .3], [1.1, 0, .95], [.5, 0, .95]], [[0,1],[1,2],[2,3],[3,0]]);
    add([[-.2, 0, -.25], [.9, 0, -.3], [1.1, 0, -.95], [.5, 0, -.95]], [[0,1],[1,2],[2,3],[3,0]]);
    // fins
    add([[.6, .28, 0], [1.3, .7, 0], [1.4, .3, 0]], [[0,1],[1,2],[2,0]]);
    // engine pods
    [-1, 1].forEach(function (s) {
      add([[.7, -.1, .55 * s], [1.5, -.1, .55 * s], [1.5, .05, .55 * s], [.7, .05, .55 * s]], [[0,1],[1,2],[2,3],[3,0]]);
    });
    return { V: V, E: E };
  })();
  view('cv-vessel', function (v, t) {
    var c = v.ctx, w = v.w, h = v.h, cx = w / 2, cy = h / 2, S = Math.min(w / 3.6, h / 1.2);
    var yaw = reduced ? .6 : .6 + Math.sin(t * .0004) * .5, pitch = .35, cy1 = Math.cos(yaw), sy = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch);
    c.clearRect(0, 0, w, h);
    // blueprint grid
    c.strokeStyle = 'rgba(' + CY + ',.07)'; c.lineWidth = 1;
    for (var gx = 0; gx < w; gx += 20) { c.beginPath(); c.moveTo(gx, 0); c.lineTo(gx, h); c.stroke(); }
    for (var gy = 0; gy < h; gy += 20) { c.beginPath(); c.moveTo(0, gy); c.lineTo(w, gy); c.stroke(); }
    var P = ship.V.map(function (p) {
      var x = p[0] * cy1 - p[2] * sy, z = p[0] * sy + p[2] * cy1, y = p[1] * cp - z * sp; z = p[1] * sp + z * cp;
      var k = 4 / (4 + z); return { x: cx + x * S * k, y: cy - y * S * k, z: z };
    });
    // ion plume from the stern (profile index 7 centre)
    var stern = ship.V.reduce(function (a, p, i) { return p[0] > 1.4 ? i : a; }, 0), sp0 = P[stern];
    var fl = reduced ? 1 : .85 + .15 * Math.sin(t * .02);
    glow(c, sp0.x, sp0.y, 40 * fl, '120,200,255', .5);
    ship.E.forEach(function (e) {
      var a = P[e[0]], b = P[e[1]], d = (a.z + b.z) / 2;
      c.strokeStyle = 'rgba(' + CY + ',' + Math.max(.15, .8 - d * .35) + ')';
      c.beginPath(); c.moveTo(a.x, a.y); c.lineTo(b.x, b.y); c.stroke();
    });
  });

  // ---------- 5. asteroid scan ----------
  function height(x, y, peak) { var d = Math.sqrt(x * x + y * y); return Math.max(0, fbm(x * 2.2 + 5, y * 2.2, 1.3) * .9 + peak * Math.max(0, 1 - d * 1.6) * .9 - .25); }
  var asterCache = null;
  var av = view('cv-aster', function (v, t) {
    var c = v.ctx, w = v.w, h = v.h;
    if (!asterCache || asterCache.w !== w) {
      var o = document.createElement('canvas'); o.width = w * 2; o.height = h * 2; var oc = o.getContext('2d'); oc.scale(2, 2);
      var N = 56, S = w * .7, cxx = w / 2, base = h * .98, cell = [];
      for (var j = 0; j < N; j++) for (var i = 0; i < N; i++) {
        var u = i / (N - 1) - .5, vv = j / (N - 1) - .5;
        cell.push(height(u, vv, 1));
      }
      function pr(i, j) { var u = i / (N - 1) - .5, vv = j / (N - 1) - .5, k = 1.5 / (1.5 - vv); return [cxx + u * S * k * 1.5, base - (.5 - vv) * h * .42 - cell[j * N + i] * h * .42 * k]; }
      for (j = 0; j < N - 1; j++) for (i = 0; i < N - 1; i++) {
        var a = pr(i, j), b = pr(i + 1, j), d = pr(i + 1, j + 1), e = pr(i, j + 1);
        var sl = (cell[j * N + i + 1] - cell[j * N + i]) * 5 - (cell[(j + 1) * N + i] - cell[j * N + i]) * 3, hh = cell[j * N + i];
        var L = Math.max(.12, Math.min(1, .5 - sl * 2.2)), fog = j / N;
        oc.fillStyle = 'rgb(' + Math.round((30 + 150 * L) * (.55 + fog * .45)) + ',' + Math.round((44 + 160 * L) * (.55 + fog * .45)) + ',' + Math.round((70 + 170 * L) * (.6 + fog * .4)) + ')';
        oc.beginPath(); oc.moveTo(a[0], a[1]); oc.lineTo(b[0], b[1]); oc.lineTo(d[0], d[1]); oc.lineTo(e[0], e[1]); oc.closePath(); oc.fill();
        if (hh > .55) { oc.fillStyle = 'rgba(230,244,255,' + Math.min(.7, (hh - .55) * 2) * L + ')'; oc.fill(); }
        if (i % 6 === 0 || j % 6 === 0) { oc.strokeStyle = 'rgba(' + CY + ',.22)'; oc.lineWidth = .6; oc.stroke(); }
      }
      asterCache = { c: o, w: w };
    }
    c.clearRect(0, 0, w, h);
    var bgd = c.createLinearGradient(0, 0, 0, h); bgd.addColorStop(0, '#071423'); bgd.addColorStop(1, '#030810');
    c.fillStyle = bgd; c.fillRect(0, 0, w, h);
    c.drawImage(asterCache.c, 0, 0, w, h);
    var sx = reduced ? w * .62 : (t * .05) % (w + 40) - 20;
    var sg = c.createLinearGradient(sx - 30, 0, sx + 2, 0); sg.addColorStop(0, 'rgba(' + CY + ',0)'); sg.addColorStop(1, 'rgba(' + CY + ',.35)');
    c.fillStyle = sg; c.fillRect(sx - 30, 0, 32, h);
    c.strokeStyle = 'rgba(' + CY + ',.9)'; c.beginPath(); c.moveTo(sx, 0); c.lineTo(sx, h); c.stroke();
    c.strokeStyle = 'rgba(' + CY + ',.5)'; c.strokeRect(6.5, 6.5, w - 13, h - 13);
    [[6, 6], [w - 6, 6], [6, h - 6], [w - 6, h - 6]].forEach(function (p, i) { c.fillStyle = 'rgba(' + CY + ',1)'; c.fillRect(p[0] - (i % 2) * 14, p[1] - (i > 1) * 2, 14, 2); });
  });

  // ---------- 6. surface analysis (terrain on the table) ----------
  view('cv-surface', function (v, t) {
    var c = v.ctx, w = v.w, h = v.h, cx = w / 2, cy = h * .64, R = Math.min(w * .46, h * 1.1), rot = reduced ? .4 : t * .00008;
    c.clearRect(0, 0, w, h);
    glow(c, cx, cy, R, '60,160,240', .28);
    for (var k = 1; k <= 3; k++) { c.strokeStyle = 'rgba(' + CY + ',' + (.55 - k * .12) + ')'; c.lineWidth = k === 1 ? 2 : 1;
      c.beginPath(); c.ellipse(cx, cy, R * (1 + k * .06), R * .3 * (1 + k * .06), 0, 0, TAU); c.stroke(); }
    var N = 34, cr = Math.cos(rot), sr = Math.sin(rot);
    for (var j = 0; j < N; j++) {
      c.beginPath(); var started = false;
      for (var i = 0; i < N; i++) {
        var u = i / (N - 1) * 2 - 1, vv = j / (N - 1) * 2 - 1;
        if (u * u + vv * vv > 1) { started = false; continue; }
        var x = u * cr - vv * sr, z = u * sr + vv * cr;
        var hh = height(u * .6, vv * .6, 1.1);
        var px = cx + x * R, py = cy + z * R * .3 - hh * h * .55;
        var ice = hh > .78;
        c.strokeStyle = ice ? 'rgba(235,248,255,.9)' : 'rgba(' + CY + ',' + (.25 + hh * .6) + ')';
        if (!started) { c.moveTo(px, py); started = true; } else c.lineTo(px, py);
      }
      c.stroke();
    }
    // rising beam
    var bm = c.createLinearGradient(0, cy, 0, cy - h * .6); bm.addColorStop(0, 'rgba(' + CY + ',.18)'); bm.addColorStop(1, 'rgba(' + CY + ',0)');
    c.fillStyle = bm; c.beginPath(); c.moveTo(cx - R, cy); c.lineTo(cx - R * .7, 0); c.lineTo(cx + R * .7, 0); c.lineTo(cx + R, cy); c.fill();
  });

  // ---------- 7b. quantum node lattice ----------
  view('cv-quantum', function (v, t) {
    var c = v.ctx, w = v.w, h = v.h, n = 12; c.clearRect(0, 0, w, h);
    var pts = []; for (var i = 0; i < n; i++) { var a = i / n * TAU + (reduced ? 0 : t * .0003); pts.push([w / 2 + Math.cos(a) * w * .42, h / 2 + Math.sin(a) * h * .32 * Math.cos(i)]); }
    c.strokeStyle = 'rgba(' + CY + ',.25)'; c.lineWidth = .8;
    for (i = 0; i < n; i++) for (var j = i + 2; j < n; j += 3) { c.beginPath(); c.moveTo(pts[i][0], pts[i][1]); c.lineTo(pts[j][0], pts[j][1]); c.stroke(); }
    pts.forEach(function (p, i) { c.fillStyle = i === 0 ? 'rgba(' + AMB + ',1)' : 'rgba(' + CY + ',.9)'; c.beginPath(); c.arc(p[0], p[1], 2.4, 0, TAU); c.fill(); });
  });

  // ---------- dust around the empty seat ----------
  var motes = (function () { var r = rng(7), a = []; for (var i = 0; i < 90; i++) a.push([r(), r(), r(), r()]); return a; })();
  view('cv-dust', function (v, t) {
    var c = v.ctx, w = v.w, h = v.h; c.clearRect(0, 0, w, h);
    motes.forEach(function (m) {
      var y = ((m[1] - (reduced ? 0 : t * .00002 * (1 + m[2]))) % 1 + 1) % 1, x = m[0] + Math.sin(t * .0005 + m[3] * 9) * .01;
      c.fillStyle = 'rgba(' + CY + ',' + (.2 + m[2] * .5) + ')'; c.beginPath(); c.arc(x * w * .7 + w * .15, y * h * .8, .6 + m[2] * 1.6, 0, TAU); c.fill();
    });
  });

  // ---------- 10. monitor graph ----------
  var hist = []; (function () { var r = rng(3); for (var i = 0; i < 40; i++) hist.push(.4 + r() * .5); })();
  view('cv-graph', function (v, t) {
    var c = v.ctx, w = v.w, h = v.h; c.clearRect(0, 0, w, h);
    c.fillStyle = '#040b13'; c.fillRect(0, 0, w, h);
    var bw = w / hist.length;
    hist.forEach(function (x, i) { c.fillStyle = 'rgba(' + CY + ',' + (.3 + x * .5) + ')'; c.fillRect(i * bw + 1, h - x * h * .7, bw - 2, x * h * .7); });
    c.strokeStyle = 'rgba(' + AMB + ',.9)'; c.lineWidth = 1.5; c.beginPath();
    for (var i = 0; i <= 60; i++) { var x = i / 60 * w, y = h * .35 + Math.sin(i * .35 + t * .002) * h * .12 + Math.sin(i * .9) * h * .04; if (i) c.lineTo(x, y); else c.moveTo(x, y); }
    c.stroke();
  });

  // ---------- background: server columns + fog stars ----------
  view('bg', function (v, t) {
    var c = v.ctx, w = v.w, h = v.h; c.clearRect(0, 0, w, h);
    var r = rng(11);
    for (var col = 0; col < 2; col++) {
      var x0 = col ? w - 70 : 16;
      for (var k = 0; k < 120; k++) {
        var y = 80 + r() * (h - 160), on = reduced ? r() > .4 : Math.sin(t * .002 * (r() + .3) + k) > -.2;
        c.fillStyle = 'rgba(' + CY + ',' + (on ? .35 : .08) + ')'; c.fillRect(x0 + r() * 54, y, 3, 2);
      }
    }
  });

  // ---------- DOM: nodes, code text, ticks, clock ----------
  var nodes = document.getElementById('nodes');
  for (var n = 1; n <= 24; n++) { var s = document.createElement('span'); s.textContent = (n < 10 ? '0' : '') + n; if (n === 12) s.className = 'sel'; s.style.setProperty('--d', (1.1 + (n * 37 % 17) / 10) + 's'); nodes.appendChild(s); }

  var codeLines = ['sched q12  ok', 'mem  3f2a  ok', 'sync [###-]', 'buf  flush 0', 'loop idle', 'chk  crc ok', 'io   ring 7', 'heap gc ok', 'ctl  ack 01', 'reg  clean', 'tmr  tick +1', 'lnk  hb ok'];
  function fill(el, off) { if (!el) return; var out = []; for (var i = 0; i < 9; i++) out.push(codeLines[(i + off) % codeLines.length]); el.textContent = out.join('\n'); }
  var c1 = document.getElementById('code1'), c2 = document.getElementById('code2'), off = 0;
  fill(c1, 0); fill(c2, 5);

  // ticks: frozen value shown on load, then varies plausibly around it
  var tx = document.getElementById('tick-tx'), pr = document.getElementById('tick-proc'), co = document.getElementById('tick-core'), qc = document.getElementById('tick-qcore');
  var bp = document.getElementById('bar-proc'), bc = document.getElementById('bar-core');
  function tick() {
    off++; fill(c1, off); fill(c2, off + 5);
    tx.textContent = (1.2 + (Math.random() - .5) * .06).toFixed(2);
    var p = 92 + Math.round((Math.random() - .5) * 4), k = 89 + Math.round((Math.random() - .5) * 4);
    pr.textContent = p; co.textContent = k; qc.textContent = k; bp.style.width = p + '%'; bc.style.width = k + '%';
    hist.shift(); hist.push(.4 + Math.random() * .5);
  }
  var clock = document.getElementById('clock'), t0 = Date.now();
  function clk() { var s = Math.floor((Date.now() - t0) / 1000); clock.textContent = [Math.floor(s / 3600), Math.floor(s / 60) % 60, s % 60].map(function (x) { return (x < 10 ? '0' : '') + x; }).join(':'); }

  // pointer parallax: the room leans with you
  var stage = document.getElementById('stage');
  if (!reduced && window.matchMedia('(pointer:fine)').matches) {
    window.addEventListener('pointermove', function (e) {
      stage.style.setProperty('--ry', ((e.clientX / innerWidth - .5) * 4).toFixed(2) + 'deg');
      stage.style.setProperty('--rx', ((.5 - e.clientY / innerHeight) * 2).toFixed(2) + 'deg');
    });
  }

  var timer = null, raf = 0;
  function frame(t) { views.forEach(function (v) { v.draw(v, t); }); raf = requestAnimationFrame(frame); }
  function start() {
    if (reduced) { views.forEach(function (v) { v.draw(v, 0); }); return; }
    raf = requestAnimationFrame(frame);
    setTimeout(function () { timer = setInterval(function () { tick(); clk(); }, 1600); }, 1800);
  }
  function stop() { cancelAnimationFrame(raf); clearInterval(timer); }
  RM.addEventListener && RM.addEventListener('change', function (e) { reduced = e.matches; stop(); start(); });
  start();
})();
