/* MooreFolio preview — "the roster in 3D".
   The page's background is the Cadre itself: 15 agents (one supervisor, 14
   workers and specialists) on threads to the one gateway they all share.
   Pulses are illustrative, not live traffic. Raw WebGL1, no libraries. */
(function () {
  'use strict';
  var canvas = document.getElementById('stage');
  var root = document.documentElement;
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  var gl = null;
  try {
    gl = canvas.getContext('webgl', { antialias: true, alpha: false, powerPreference: 'low-power' });
  } catch (e) { gl = null; }
  if (!gl || new URLSearchParams(location.search).has('nogl')) {
    root.classList.add('no-webgl');
    return;
  }
  root.classList.add('has-webgl');

  // ---------- the roster (geometry from the page's own facts) ----------
  // index 0 = gateway ("one brain, many jobs"), 1 = supervisor, 2..15 = 14 agents
  var N = 16, nodes = [];
  function rnd(seed) { var x = Math.sin(seed * 127.1) * 43758.5453; return x - Math.floor(x); }
  nodes.push({ p: [0, 0, 0], r: 1.0, kind: 0 });
  nodes.push({ p: [0, 1.55, 0.2], r: 0.62, kind: 1 });
  for (var i = 0; i < 14; i++) {           // golden-angle shell, flattened like a web
    var y = 1 - (i + 0.5) / 14 * 2, rr = Math.sqrt(1 - y * y), th = i * 2.39996;
    var R = 3.1 + rnd(i + 3) * 0.9;
    nodes.push({ p: [Math.cos(th) * rr * R, y * R * 0.55, Math.sin(th) * rr * R], r: 0.38 + rnd(i) * 0.12, kind: 2 });
  }
  nodes.forEach(function (n, k) { n.base = n.p.slice(); n.ph = rnd(k + 11) * 6.28; });

  var edges = [];                            // [a, b, weight]
  for (var a = 1; a < N; a++) edges.push([0, a, 1]);          // every agent -> shared gateway
  for (var b = 2; b < N; b++) edges.push([1, b, 0.45]);       // supervisor -> each worker
  for (var c = 2; c < N; c++) edges.push([c, 2 + ((c - 2 + 3) % 14), 0.28]); // hand-off ring
  // web rings: the "spider" threads, concentric around the gateway
  var RINGS = 3, RSEG = 72, ringPts = [];
  for (var q = 0; q < RINGS; q++) {
    var rad = 1.6 + q * 1.35;
    for (var s = 0; s < RSEG; s++) {
      var t0 = s / RSEG * 6.2832, t1 = (s + 1) / RSEG * 6.2832;
      ringPts.push(Math.cos(t0) * rad, -0.9 - q * 0.08, Math.sin(t0) * rad, Math.cos(t1) * rad, -0.9 - q * 0.08, Math.sin(t1) * rad);
    }
  }
  // floor of dots for depth
  var floor = [];
  for (var fx = -14; fx <= 14; fx++) for (var fz = -14; fz <= 14; fz++) floor.push(fx * 0.9, -3.2, fz * 0.9);

  // ---------- shaders ----------
  function sh(type, src) { var s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); return s; }
  function prog(vs, fs) {
    var p = gl.createProgram();
    gl.attachShader(p, sh(gl.VERTEX_SHADER, vs)); gl.attachShader(p, sh(gl.FRAGMENT_SHADER, fs));
    gl.linkProgram(p); return p;
  }
  var VS_PT = 'attribute vec3 aP;attribute float aS;attribute vec3 aC;uniform mat4 uM;uniform float uPx;varying vec3 vC;varying float vF;' +
    'void main(){vec4 p=uM*vec4(aP,1.);gl_Position=p;gl_PointSize=max(1.,aS*uPx/p.w);vF=clamp(1.15-p.w/16.,0.08,1.);vC=aC;}';
  var FS_PT = 'precision mediump float;varying vec3 vC;varying float vF;void main(){vec2 d=gl_PointCoord-.5;float r=length(d)*2.;' +
    'float core=smoothstep(.34,.0,r);float halo=exp(-r*r*5.)*.55;float a=(core+halo)*vF;if(a<.004)discard;gl_FragColor=vec4(vC*a,a);}';
  var VS_LN = 'attribute vec3 aP;attribute float aA;uniform mat4 uM;varying float vA;void main(){vec4 p=uM*vec4(aP,1.);gl_Position=p;vA=aA*clamp(1.2-p.w/15.,0.05,1.);}';
  var FS_LN = 'precision mediump float;uniform vec3 uC;varying float vA;void main(){gl_FragColor=vec4(uC*vA,vA);}';
  var pPt = prog(VS_PT, FS_PT), pLn = prog(VS_LN, FS_LN);
  if (!gl.getProgramParameter(pPt, gl.LINK_STATUS) || !gl.getProgramParameter(pLn, gl.LINK_STATUS)) {
    root.classList.remove('has-webgl'); root.classList.add('no-webgl'); return;
  }
  var L = {
    pt: { aP: gl.getAttribLocation(pPt, 'aP'), aS: gl.getAttribLocation(pPt, 'aS'), aC: gl.getAttribLocation(pPt, 'aC'), uM: gl.getUniformLocation(pPt, 'uM'), uPx: gl.getUniformLocation(pPt, 'uPx') },
    ln: { aP: gl.getAttribLocation(pLn, 'aP'), aA: gl.getAttribLocation(pLn, 'aA'), uM: gl.getUniformLocation(pLn, 'uM'), uC: gl.getUniformLocation(pLn, 'uC') }
  };
  var MAXP = 64, pulses = [];
  var ptCount = N + MAXP, floorCount = floor.length / 3;
  var ptPos = new Float32Array(ptCount * 3), ptSize = new Float32Array(ptCount), ptCol = new Float32Array(ptCount * 3);
  var lnPos = new Float32Array(edges.length * 6), lnA = new Float32Array(edges.length * 2);
  var ringA = new Float32Array(ringPts.length / 3);
  for (var ra = 0; ra < ringA.length; ra++) ringA[ra] = 0.16;
  var bufPt = gl.createBuffer(), bufPs = gl.createBuffer(), bufPc = gl.createBuffer();
  var bufLn = gl.createBuffer(), bufLa = gl.createBuffer(), bufRing = gl.createBuffer(), bufRa = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, bufRing); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(ringPts), gl.STATIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER, bufRa); gl.bufferData(gl.ARRAY_BUFFER, ringA, gl.STATIC_DRAW);
  // floor dots never move: upload once
  var fS = new Float32Array(floorCount), fC = new Float32Array(floorCount * 3);
  for (var f = 0; f < floorCount; f++) { fS[f] = 0.05; fC.set([0.62, 0.55, 0.45], f * 3); }
  var bufFp = gl.createBuffer(), bufFs = gl.createBuffer(), bufFc = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, bufFp); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(floor), gl.STATIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER, bufFs); gl.bufferData(gl.ARRAY_BUFFER, fS, gl.STATIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER, bufFc); gl.bufferData(gl.ARRAY_BUFFER, fC, gl.STATIC_DRAW);
  [bufPt, bufPs, bufPc].forEach(function (bf, i) { gl.bindBuffer(gl.ARRAY_BUFFER, bf); gl.bufferData(gl.ARRAY_BUFFER, [ptPos, ptSize, ptCol][i].byteLength, gl.DYNAMIC_DRAW); });
  gl.bindBuffer(gl.ARRAY_BUFFER, bufLn); gl.bufferData(gl.ARRAY_BUFFER, lnPos.byteLength, gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER, bufLa); gl.bufferData(gl.ARRAY_BUFFER, lnA.byteLength, gl.DYNAMIC_DRAW);
  var GOLD = [1.0, 0.70, 0.30], RUST = [1.0, 0.48, 0.22], TEAL = [0.56, 0.75, 0.80];

  // ---------- matrices ----------
  function persp(fy, asp, n, fr) { var t = 1 / Math.tan(fy / 2); return [t / asp, 0, 0, 0, 0, t, 0, 0, 0, 0, (fr + n) / (n - fr), -1, 0, 0, 2 * fr * n / (n - fr), 0]; }
  function look(e, c) {
    var z = norm(sub(e, c)), x = norm(cross([0, 1, 0], z)), y = cross(z, x);
    return [x[0], y[0], z[0], 0, x[1], y[1], z[1], 0, x[2], y[2], z[2], 0, -dot(x, e), -dot(y, e), -dot(z, e), 1];
  }
  function mul(a, b) { var r = new Array(16); for (var i = 0; i < 4; i++) for (var j = 0; j < 4; j++) { var s = 0; for (var k = 0; k < 4; k++) s += a[k * 4 + j] * b[i * 4 + k]; r[i * 4 + j] = s; } return r; }
  function sub(a, b) { return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]; }
  function dot(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
  function cross(a, b) { return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]; }
  function norm(a) { var l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; }

  // ---------- sizing (DPR capped) ----------
  var W = 0, H = 0, dpr = 1;
  function resize() {
    dpr = Math.min(window.devicePixelRatio || 1, window.innerWidth < 700 ? 1.25 : 1.5);
    W = Math.round(window.innerWidth * dpr); H = Math.round(window.innerHeight * dpr);
    canvas.width = W; canvas.height = H; gl.viewport(0, 0, W, H);
    if (!running) draw(lastT);
  }

  // ---------- pulses: a ticket goes supervisor -> gateway -> worker -> gateway ----------
  function spawn(worker) {
    if (pulses.length >= MAXP) return;
    var w = worker || 2 + Math.floor(Math.random() * 14);
    pulses.push({ path: [1, 0, w, 0], seg: 0, u: 0, sp: 0.55 + Math.random() * 0.35 });
  }
  window.__dispatch = function () { for (var i = 0; i < 6; i++) spawn(2 + ((i * 5 + Math.floor(Math.random() * 14)) % 14)); flash = 1; };

  var scrollF = 0, px = 0, py = 0, tpx = 0, tpy = 0, flash = 0, lastT = 0, acc = 0;
  function onScroll() { var m = document.documentElement.scrollHeight - innerHeight; scrollF = m > 0 ? scrollY / m : 0; if (!running) draw(lastT); }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('pointermove', function (e) { tpx = e.clientX / innerWidth * 2 - 1; tpy = e.clientY / innerHeight * 2 - 1; }, { passive: true });

  function draw(t) {
    var still = reduce.matches;
    var time = still ? 7.5 : t / 1000;
    px += (tpx - px) * 0.05; py += (tpy - py) * 0.05;
    var sf = still ? 0.12 : scrollF;
    // camera: scroll carries you around and down into the roster
    var ang = 0.6 + sf * 3.6 + time * 0.035 + px * 0.25;
    var dist = 9.2 - Math.sin(sf * 3.1416) * 3.2;
    var eye = [Math.sin(ang) * dist, 2.4 - sf * 2.6 - py * 0.6, Math.cos(ang) * dist];
    var narrow = innerWidth < 900;
    var target = narrow ? [0, 2.2 - Math.min(1, sf * 5) * 2.0, 0] : [-1.6 + sf * 1.6, 0.2, 0];   // narrow: web sits in the window below the hero   // wide screens: web sits right of the hero copy
    var M = mul(persp(narrow ? 1.0 : 0.82, W / H, 0.1, 60), look(eye, target));

    for (var k = 0; k < N; k++) {
      var n = nodes[k], bob = still ? 0 : Math.sin(time * 0.7 + n.ph) * 0.12;
      n.p[0] = n.base[0]; n.p[1] = n.base[1] + bob; n.p[2] = n.base[2];
      ptPos.set(n.p, k * 3);
      ptSize[k] = n.r * (k === 0 ? 1.6 + flash * 0.8 + Math.sin(time * 1.3) * 0.08 : 1);
      ptCol.set(n.kind === 0 ? GOLD : n.kind === 1 ? RUST : TEAL, k * 3);
    }
    for (var e = 0; e < edges.length; e++) {
      var A = nodes[edges[e][0]].p, B = nodes[edges[e][1]].p;
      lnPos.set(A, e * 6); lnPos.set(B, e * 6 + 3);
      lnA[e * 2] = lnA[e * 2 + 1] = edges[e][2] * 0.5;
    }
    for (var p = 0; p < MAXP; p++) { var o = (N + p); ptSize[o] = 0; }
    pulses.forEach(function (q, i) {
      var a = nodes[q.path[q.seg]].p, b = nodes[q.path[q.seg + 1]].p, u = q.u;
      ptPos.set([a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u], (N + i) * 3);
      ptSize[N + i] = 0.2; ptCol.set(q.seg < 2 ? RUST : GOLD, (N + i) * 3);
    });

    gl.clearColor(0.075, 0.066, 0.062, 1); gl.clear(gl.COLOR_BUFFER_BIT);
    gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);

    gl.useProgram(pLn); gl.uniformMatrix4fv(L.ln.uM, false, M);
    gl.enableVertexAttribArray(L.ln.aP); gl.enableVertexAttribArray(L.ln.aA);
    gl.uniform3fv(L.ln.uC, [0.72, 0.62, 0.48]);
    gl.bindBuffer(gl.ARRAY_BUFFER, bufRing); gl.vertexAttribPointer(L.ln.aP, 3, gl.FLOAT, false, 0, 0);
    gl.bindBuffer(gl.ARRAY_BUFFER, bufRa); gl.vertexAttribPointer(L.ln.aA, 1, gl.FLOAT, false, 0, 0);
    gl.drawArrays(gl.LINES, 0, ringPts.length / 3);
    gl.uniform3fv(L.ln.uC, [0.95, 0.62, 0.36]);
    gl.bindBuffer(gl.ARRAY_BUFFER, bufLn); gl.bufferSubData(gl.ARRAY_BUFFER, 0, lnPos); gl.vertexAttribPointer(L.ln.aP, 3, gl.FLOAT, false, 0, 0);
    gl.bindBuffer(gl.ARRAY_BUFFER, bufLa); gl.bufferSubData(gl.ARRAY_BUFFER, 0, lnA); gl.vertexAttribPointer(L.ln.aA, 1, gl.FLOAT, false, 0, 0);
    gl.drawArrays(gl.LINES, 0, edges.length * 2);

    gl.useProgram(pPt); gl.uniformMatrix4fv(L.pt.uM, false, M); gl.uniform1f(L.pt.uPx, H * 0.9);
    [L.pt.aP, L.pt.aS, L.pt.aC].forEach(function (l) { gl.enableVertexAttribArray(l); });
    gl.bindBuffer(gl.ARRAY_BUFFER, bufFp); gl.vertexAttribPointer(L.pt.aP, 3, gl.FLOAT, false, 0, 0);
    gl.bindBuffer(gl.ARRAY_BUFFER, bufFs); gl.vertexAttribPointer(L.pt.aS, 1, gl.FLOAT, false, 0, 0);
    gl.bindBuffer(gl.ARRAY_BUFFER, bufFc); gl.vertexAttribPointer(L.pt.aC, 3, gl.FLOAT, false, 0, 0);
    gl.drawArrays(gl.POINTS, 0, floorCount);
    gl.bindBuffer(gl.ARRAY_BUFFER, bufPt); gl.bufferSubData(gl.ARRAY_BUFFER, 0, ptPos); gl.vertexAttribPointer(L.pt.aP, 3, gl.FLOAT, false, 0, 0);
    gl.bindBuffer(gl.ARRAY_BUFFER, bufPs); gl.bufferSubData(gl.ARRAY_BUFFER, 0, ptSize); gl.vertexAttribPointer(L.pt.aS, 1, gl.FLOAT, false, 0, 0);
    gl.bindBuffer(gl.ARRAY_BUFFER, bufPc); gl.bufferSubData(gl.ARRAY_BUFFER, 0, ptCol); gl.vertexAttribPointer(L.pt.aC, 3, gl.FLOAT, false, 0, 0);
    gl.drawArrays(gl.POINTS, 0, ptCount);
    gl.disableVertexAttribArray(L.pt.aS); gl.disableVertexAttribArray(L.pt.aC);
  }

  // ---------- loop: paused when hidden, single frame under reduced motion ----------
  var running = false, raf = 0, prev = 0, frames = [], work = [];
  window.__perf = { frames: frames, work: work, dpr: function () { return dpr; } };
  function tick(t) {
    raf = requestAnimationFrame(tick);
    var dt = prev ? Math.min(0.1, (t - prev) / 1000) : 0;
    if (prev) frames.push(t - prev);
    if (frames.length > 2000) frames.splice(0, 1000);
    prev = t; lastT = t;
    acc += dt; if (acc > 0.45) { acc = 0; spawn(); }
    flash *= 0.94;
    for (var i = pulses.length - 1; i >= 0; i--) {
      var q = pulses[i]; q.u += dt * q.sp;
      if (q.u >= 1) { q.u = 0; q.seg++; if (q.seg >= q.path.length - 1) pulses.splice(i, 1); }
    }
    var w0 = performance.now(); draw(t); work.push(performance.now() - w0);
    if (work.length > 2000) work.splice(0, 1000);
  }
  function start() { if (running || reduce.matches || document.hidden) return; running = true; prev = 0; raf = requestAnimationFrame(tick); }
  function stop() { running = false; cancelAnimationFrame(raf); }
  document.addEventListener('visibilitychange', function () { document.hidden ? stop() : start(); });
  (reduce.addEventListener ? reduce.addEventListener.bind(reduce, 'change') : reduce.addListener.bind(reduce))(function () { reduce.matches ? (stop(), draw(lastT)) : start(); });
  canvas.addEventListener('webglcontextlost', function (e) { e.preventDefault(); stop(); root.classList.add('no-webgl'); });
  window.addEventListener('resize', resize);
  resize(); onScroll();
  for (var s0 = 0; s0 < 10; s0++) spawn();
  pulses.forEach(function (q, i) { q.seg = i % 3; q.u = (i * 0.37) % 1; });
  draw(0);
  start();
})();
