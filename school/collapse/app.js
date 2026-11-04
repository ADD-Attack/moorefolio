/* Collapse — the instrument around the model in wfc.js. Draws the grid, runs the clock, owns the controls. */
(function () {
  'use strict';
  const { TILES, SETS, Model } = window.WFC;
  const $ = id => document.getElementById(id);
  const q = new URLSearchParams(location.search);
  const HOLD_MS = 2500;                       // the beat a finished or contradicted grid holds before a restart
  const C = { paper: '#fbf8f1', board: '#ebe4d5', rule: '#d3c9b5', ink: '#1c2230', dim: '#5f6574', ink2: '#3b4352', pipeDark: '#5b2810',
    pipe: '#b4562a', sheen: '#e7a173', next: '#a8481c', wave: '180, 86, 42', bad: '#9e1f18', done: '#2f6b46' };

  const freshSeed = () => 1 + Math.floor(Math.random() * 999999);    // New pattern: the browser's own random source
  let model, playing = !q.has('hold'), acc = 0, last = 0, endedAt = 0, stepAt = 0, lastEntry = null;
  let displayed = [];                          // the numbers the last frame actually drew (-1 = a tile was drawn)
  const ctl = { size: $('c-size'), set: $('c-set'), seed: $('c-seed'), speed: $('c-speed'), auto: $('c-auto'), play: $('c-play') };

  // ---------- glyphs ----------
  function pipePath(g, x, y, s, t, w, colour) {
    const e = TILES[t].e, h = s / 2, cx = x + h, cy = y + h, n = e.reduce((a, b) => a + b, 0);
    g.strokeStyle = colour; g.lineWidth = w; g.lineCap = 'butt'; g.beginPath();
    if (n === 2 && !(e[0] && e[2]) && !(e[1] && e[3])) {           // corner: a quarter arc about the shared cell corner
      const ox = e[1] ? x + s : x, oy = e[0] ? y : y + s;
      const start = e[0] ? (e[1] ? Math.PI / 2 : 0) : (e[1] ? Math.PI : Math.PI * 1.5);
      g.arc(ox, oy, h, start, start + Math.PI / 2);
    } else {
      const ends = [[cx, y], [x + s, cy], [cx, y + s], [x, cy]];
      for (let d = 0; d < 4; d++) if (e[d] && !(n === 4 && (d === 1 || d === 3))) { g.moveTo(cx, cy); g.lineTo(ends[d][0], ends[d][1]); }
    }
    g.stroke();
  }
  function drawTile(g, x, y, s, t, ground) {
    if (!(s > 2)) return;
    const e = TILES[t].e, n = e.reduce((a, b) => a + b, 0), h = s / 2, cx = x + h, cy = y + h;
    if (n === 0) {                                                   // blank: a draftsman's registration tick
      g.strokeStyle = C.rule; g.lineWidth = Math.max(1, s * .05); g.beginPath();
      g.moveTo(cx - s * .1, cy); g.lineTo(cx + s * .1, cy); g.moveTo(cx, cy - s * .1); g.lineTo(cx, cy + s * .1); g.stroke(); return;
    }
    const layers = [[s * .34, C.pipeDark], [s * .22, C.pipe], [s * .06, C.sheen]];
    for (const [w, col] of layers) pipePath(g, x, y, s, t, w, col);
    if (n === 4) {                                                  // crossing: the east–west pipe bridges over the north–south one
      g.strokeStyle = ground; g.lineWidth = s * .5; g.beginPath(); g.moveTo(x + s * .18, cy); g.lineTo(x + s * .82, cy); g.stroke();
      for (const [w, col] of layers) { g.strokeStyle = col; g.lineWidth = w; g.beginPath(); g.moveTo(x, cy); g.lineTo(x + s, cy); g.stroke(); }
    }
    if (n === 3) {                                                   // tee: a solder joint where three lines meet
      g.fillStyle = C.pipeDark; g.beginPath(); g.arc(cx, cy, s * .22, 0, 7); g.fill();
      g.fillStyle = C.pipe; g.beginPath(); g.arc(cx, cy, s * .15, 0, 7); g.fill();
      g.fillStyle = C.sheen; g.beginPath(); g.arc(cx - s * .04, cy - s * .04, s * .045, 0, 7); g.fill();
    }
  }

  // ---------- legend ----------
  function buildLegend() {
    const ol = $('legend'); ol.innerHTML = ''; const inSet = new Set(SETS[model.set]); const dpr = window.devicePixelRatio || 1;
    for (const t of TILES) {
      const li = document.createElement('li'); if (!inSet.has(t.id)) li.className = 'out';
      const cv = document.createElement('canvas'); cv.width = cv.height = 28 * dpr; cv.setAttribute('aria-hidden', 'true');
      const g = cv.getContext('2d'); g.scale(dpr, dpr); g.fillStyle = C.paper; g.fillRect(0, 0, 28, 28); drawTile(g, 0, 0, 28, t.id, C.paper);
      g.strokeStyle = C.rule; g.lineWidth = 1; g.strokeRect(.5, .5, 27, 27);
      const label = document.createElement('span'); label.textContent = t.name + (inSet.has(t.id) ? '' : ' — not in Pipes');
      li.append(cv, label); ol.append(li);
    }
    $('legend-count').textContent = SETS[model.set].length;
  }

  // ---------- canvas ----------
  const cv = $('view'), g = cv.getContext('2d'), stage = $('stage');
  let W = 0, H = 0, box = { x: 0, y: 0, s: 0 };
  const wide = matchMedia('(min-width: 1100px)');
  function layout() {
    const dpr = window.devicePixelRatio || 1; W = stage.clientWidth; H = stage.clientHeight;
    cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); g.setTransform(dpr, 0, 0, dpr, 0, 0);
    const st = $('status').parentNode.getBoundingClientRect(), sr = stage.getBoundingClientRect();
    const top = st.bottom - sr.top + 12;
    let left = 16, right = 16, bottom = 16;
    if (wide.matches) { left = document.querySelector('.legend').getBoundingClientRect().right - sr.left + 24;
      right = sr.right - $('stage').querySelector('.readouts').getBoundingClientRect().left + 24; }
    else bottom = sr.bottom - $('stage').querySelector('.readouts').getBoundingClientRect().top + 12;
    const side = Math.floor(Math.min(W - left - right, H - top - bottom));
    const size = model.size, cell = Math.max(1, Math.floor(side / size)), s = cell * size;
    box = { x: Math.round(left + (W - left - right - s) / 2), y: Math.round(top + (H - top - bottom - s) / 2), s, cell };
  }
  function render(now) {
    g.clearRect(0, 0, W, H);
    const { x: X, y: Y, cell } = box, S = model.size, T = SETS[model.set].length;
    g.fillStyle = C.paper; g.fillRect(X, Y, cell * S, cell * S);
    const fontPx = Math.max(9, Math.round(cell * .42));
    g.font = `500 ${fontPx}px ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace`; g.textAlign = 'center'; g.textBaseline = 'middle';
    // pencil rules first; finished tiles are inked over them so the pipes run unbroken
    g.strokeStyle = C.rule; g.lineWidth = 1; g.beginPath();
    for (let k = 0; k <= S; k++) { const p = Math.round(k * cell) + .5; g.moveTo(X + p, Y); g.lineTo(X + p, Y + S * cell); g.moveTo(X, Y + p); g.lineTo(X + S * cell, Y + p); }
    g.stroke();
    displayed = new Array(model.N);
    for (let i = 0; i < model.N; i++) {
      const r = Math.floor(i / S), c = i % S, x = X + c * cell, y = Y + r * cell, t = model.tile[i];
      if (t >= 0) { g.fillStyle = C.paper; g.fillRect(x, y, cell, cell); drawTile(g, x, y, cell, t, C.paper); displayed[i] = -1; continue; }
      const n = model.opts[i].length;
      // colour as data: the fewer options left, the warmer the cell
      g.fillStyle = `rgba(${C.wave}, ${(.04 + .2 * (1 - (n - 1) / (T - 1))).toFixed(3)})`; g.fillRect(x, y, cell, cell);
      g.fillStyle = n === 0 ? C.bad : n === T ? C.dim : C.ink; g.fillText(String(n), x + cell / 2, y + cell / 2 + 1); displayed[i] = n;
    }
    // the wave: cells the last step narrowed, flashing outward by propagation depth
    const age = now - stepAt;
    if (age < 900) for (let i = 0; i < model.N; i++) { const d = model.wave[i]; if (d < 1) continue;
      const a = age - (d - 1) * 120; if (a < 0 || a > 520) continue;
      const k = 1 - a / 520; g.fillStyle = `rgba(${C.wave}, ${(.42 * k).toFixed(3)})`;
      g.fillRect(X + (i % S) * cell + 1, Y + Math.floor(i / S) * cell + 1, cell - 1, cell - 1); }
    // the next cell to collapse
    if (model.next >= 0) { const i = model.next, x = X + (i % S) * cell, y = Y + Math.floor(i / S) * cell, pulse = .65 + .35 * Math.sin(now / 160);
      g.strokeStyle = C.next; g.globalAlpha = pulse; g.lineWidth = Math.max(2, cell * .1); g.strokeRect(x + 1.5, y + 1.5, cell - 3, cell - 3); g.globalAlpha = 1;
      const tk = cell * .35; g.lineWidth = 2; g.beginPath();
      for (const [cx, cy, dx, dy] of [[x - 3, y - 3, 1, 1], [x + cell + 3, y - 3, -1, 1], [x - 3, y + cell + 3, 1, -1], [x + cell + 3, y + cell + 3, -1, -1]]) {
        g.moveTo(cx + dx * tk, cy); g.lineTo(cx, cy); g.lineTo(cx, cy + dy * tk); }
      g.stroke(); }
    if (model.failed >= 0) { const i = model.failed, x = X + (i % S) * cell, y = Y + Math.floor(i / S) * cell;
      g.strokeStyle = C.bad; g.lineWidth = Math.max(2, cell * .12); g.strokeRect(x + 1, y + 1, cell - 2, cell - 2); }
    // frame
    g.strokeStyle = C.ink; g.lineWidth = 1.5; g.strokeRect(X - .75, Y - .75, S * cell + 1.5, S * cell + 1.5);
  }

  // ---------- readouts & status ----------
  const pct = v => v.toFixed(1) + '%', bits = v => v.toFixed(2) + ' bits';
  const where = i => `row ${Math.floor(i / model.size) + 1}, column ${i % model.size + 1}`;
  function readouts() {
    const r = model.readouts();
    $('r-collapsed').textContent = pct(r.collapsedPct); $('r-entropy').textContent = bits(r.entropy);
    $('r-contra').textContent = r.contradictions; $('r-attempts').textContent = `in ${model.attempts} attempt${model.attempts === 1 ? '' : 's'}`;
    $('r-phase').textContent = r.phase; $('phase-tag').textContent = r.phase;
    document.body.dataset.phase = r.phase; ctl.seed.value = model.seed;
    const after = ctl.auto.checked ? 'Holding, then a new pattern.' : 'Holding. Step or Play starts the next one.';
    let s;
    if (r.phase === 'Done') { const m = model.mismatches(); s = `Done — ${model.N} cells, ${m.checked} inner edges, ${m.bad} mismatched. ${after}`; }
    else if (r.phase === 'Contradiction') s = `Contradiction — ${where(model.failed)} has no tile left. Counted. ${ctl.auto.checked ? 'New seed after a beat.' : 'Step or Play starts a new seed.'}`;
    else if (!lastEntry) s = `Every cell can still be any of ${SETS[model.set].length} tiles. The ring marks the first pick, drawn at random from the tie.`;
    else s = `${cap(where(lastEntry.cell))} had ${lastEntry.options} option${lastEntry.options === 1 ? '' : 's'} → ${TILES[lastEntry.tile].name}. ${lastEntry.removed} struck from ${lastEntry.touched} cell${lastEntry.touched === 1 ? '' : 's'}.`;
    $('status').textContent = s;
  }
  const cap = s => s[0].toUpperCase() + s.slice(1);

  // ---------- the clock ----------
  function doStep() {
    if (model.phase !== 'Live') { nextAttempt(); return null; }
    const e = model.step(); lastEntry = e; stepAt = performance.now();
    if (model.phase !== 'Live') endedAt = stepAt;
    return e;
  }
  function nextAttempt() { model.start(model.drawSeed()); lastEntry = null; acc = 0; readouts(); }
  function newSession(seed) {
    model = new Model(+ctl.size.value, seed, ctl.set.value); lastEntry = null; acc = 0; endedAt = 0;
    buildLegend(); layout(); readouts();
  }
  function frame(now) {
    const dt = Math.min(.25, (now - (last || now)) / 1000); last = now;
    if (playing) {
      if (model.phase === 'Live') { acc += dt * +ctl.speed.value; let k = 0;
        while (acc >= 1 && model.phase === 'Live' && k++ < 60) { acc -= 1; doStep(); }
        if (model.phase !== 'Live') acc = 0; readouts(); }
      else if (ctl.auto.checked && now - endedAt > HOLD_MS) nextAttempt();
    }
    render(now); requestAnimationFrame(frame);
  }

  // ---------- controls ----------
  function setPlaying(p) { playing = p; ctl.play.textContent = p ? 'Pause' : 'Play'; ctl.play.setAttribute('aria-pressed', String(!p));
    if (p && model.phase !== 'Live' && !ctl.auto.checked) nextAttempt(); }
  ctl.play.addEventListener('click', () => setPlaying(!playing));
  $('c-step').addEventListener('click', () => { setPlaying(false); doStep(); readouts(); });
  $('c-new').addEventListener('click', () => newSession(freshSeed()));
  ctl.size.addEventListener('change', () => newSession(model.seed));
  ctl.set.addEventListener('change', () => newSession(model.seed));
  ctl.seed.addEventListener('change', () => { const v = Math.max(1, Math.min(999999, Math.round(+ctl.seed.value) || 1)); newSession(v); });
  ctl.speed.addEventListener('input', () => { $('o-speed').textContent = ctl.speed.value; });
  ctl.auto.addEventListener('change', readouts);
  addEventListener('resize', layout);
  wide.addEventListener('change', layout);

  // ---------- start ----------
  ctl.size.value = q.get('size') || (innerWidth < 600 ? '12' : '16');
  newSession(q.has('seed') ? +q.get('seed') : freshSeed());
  setPlaying(playing);
  requestAnimationFrame(frame);

  // ---------- QA handle ----------
  window.__wfc = {
    get model() { return model; },
    box: () => ({ ...box }),
    state: () => ({ size: model.size, set: model.set, seed: model.seed, phase: model.phase, next: model.next, failed: model.failed,
      options: model.opts.map(o => o.slice()), tiles: model.tile.slice(), collapsed: model.collapsedCount, cells: model.N,
      contradictions: model.contradictions, attempts: model.attempts, completed: model.completed, log: model.log.map(e => ({ ...e })) }),
    readouts: () => ({ collapsed: $('r-collapsed').textContent, entropy: $('r-entropy').textContent, contradictions: $('r-contra').textContent,
      phase: $('r-phase').textContent, status: $('status').textContent }),
    displayed: () => { render(performance.now()); return displayed.slice(); },
    step: (n = 1) => { let e; for (let k = 0; k < n; k++) { e = doStep(); } readouts(); render(performance.now()); return e; },
    runToEnd: () => { while (model.phase === 'Live') doStep(); readouts(); render(performance.now()); return model.phase; },
    hold: p => setPlaying(!p),
    newPattern: seed => { newSession(seed ?? freshSeed()); render(performance.now()); },
    tick: ms => { endedAt -= ms; },             // QA: age the end-of-run hold without waiting it out
    // FIXTURE (QA only, never called by the page): hand-places four tiles around row 2, column 2 so that cell would need
    // a dead end (connector north, empty elsewhere). Uses the model's own place() + propagate path, so the Phase readout,
    // counter and red cell are the same code a natural contradiction would run.
    fixtureContradiction: () => { const S = model.size, at = (r, c) => r * S + c; const placed = [[0, 1, 1], [1, 0, 0], [1, 2, 0], [2, 1, 0]];
      let e; for (const [r, c, t] of placed) { if (model.phase !== 'Live') break; e = model.place(at(r, c), t, { fixture: true }); lastEntry = e; stepAt = performance.now(); }
      if (model.phase !== 'Live') endedAt = stepAt; readouts(); render(performance.now()); return model.phase; }
  };
})();
