// W-Ex11 boundary exhibit: one dial for the whole room. Every surface gets the same reflectivity r,
// so A = rF and, because every row of F sums to 1, the room amplification ρ(A) is r itself.
// Uses the frozen RoomModel only; never touches the main room's sim (window.__ex11.sim).
(function (root) {
  'use strict';
  const M = root.RoomModel || (typeof require !== 'undefined' ? require('./room-model.js') : null);
  const TOL = 1e-3;            // plain-solve target: relative error 10⁻³ (Einstein's L4a demo figure)
  const CAP = 3000;            // bounces the exhibit actually runs before it calls a room unsettled
  const LAMP = M.DEFAULTS.lamp;

  const rooms = r => ({ floor: r, right: r, ceiling: r, left: r });
  const total = x => x.reduce((s, t) => s + t, 0);

  // Everything the exhibit shows for one dial setting, computed from the room model.
  function analyse(r) {
    const an = M.analyse(rooms(r), LAMP), sp = an.spectral, cert = an.certificate;
    const below = sp.below1, at = !below && sp.lo <= 1 + 1e-12;   // bracket straddles 1 → at the line
    const regime = below ? 'settles' : at ? 'line' : 'diverges';
    // predicted plain-solve budget: smallest k with ρ^k ≤ 10⁻³; only meaningful when ρ < 1
    const budget = below ? Math.ceil(Math.log(TOL) / Math.log(sp.hi)) : null;
    const factor = below ? 1 / (1 - sp.rho) : null;               // brightness factor 1/(1 − ρ)
    // the solver's actual behaviour: run the plain bounces and watch the running total
    let x = new Array(M.N).fill(0), k = 0, settledAt = null, deposits = [];
    const exact = an.exact, exactTotal = exact ? total(exact) : null;
    while (k < CAP) {
      const prev = x, Ax = M.mulVec(an.A, prev); x = an.e.map((t, i) => t + Ax[i]); k++;
      const tk = total(x); deposits.push(tk - total(prev));
      if (exact && settledAt == null && M.supNorm(x.map((t, i) => t - exact[i])) <= TOL * M.supNorm(exact)) { settledAt = k; break; }
      if (!isFinite(tk)) break;
    }
    const solverSettled = settledAt != null;
    return {
      r, regime, bracket: [sp.lo, sp.hi], rho: sp.rho, budget, factor,
      exactTotal: solverSettled ? exactTotal : null,              // a field total is shown only when the solver settled
      field: solverSettled ? exact.slice() : null,
      solver: { settled: solverSettled, settledAt, ran: k, runningTotal: total(x), lastDeposit: deposits[deposits.length - 1], firstDeposit: deposits[0] },
      lights: { a: solverSettled, b: below, c: cert.exists },
      cap: CAP, tol: TOL,
    };
  }
  const api = { analyse, CAP, TOL, rooms };
  if (typeof module !== 'undefined') module.exports = api;

  // ---------- page wiring (browser only) ----------
  if (typeof document === 'undefined') return;
  const $ = id => document.getElementById(id);
  const dial = $('bx-r'); if (!dial) return;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const WALK = []; for (let i = 80; i <= 120; i++) WALK.push(i / 100);   // 0.80 … 0.99, 1.00, 1.01 … 1.20
  const cache = new Map(), get = r => { const key = r.toFixed(2); if (!cache.has(key)) cache.set(key, analyse(+key)); return cache.get(key); };
  let walking = false, walkTimer = null, runTimer = null, shown = 0;

  const f4 = v => v.toFixed(4), int = v => v.toLocaleString('en-US');
  function setLight(id, on, text) { const el = $('bx-v-' + id); el.className = 'v ' + (on ? 'yes' : 'no'); $('bx-v-' + id + '-t').textContent = text; }

  function drawStrip(s) {
    const cv = $('bx-strip'), c = cv.getContext('2d'), W = cv.width, H = cv.height;
    c.fillStyle = '#08090c'; c.fillRect(0, 0, W, H);
    if (!s.field) return;
    const peak = Math.max(...s.field), w = W / M.N;
    s.field.forEach((v, i) => { const t = Math.sqrt(v / peak), g = [10 + 245 * t, 11 + 215 * t, 15 + 155 * t].map(Math.round);
      c.fillStyle = `rgb(${g})`; c.fillRect(i * w + 1, 6, w - 2, H - 12); });
  }

  function render() {
    const r = +(+dial.value).toFixed(2), s = get(r);
    $('bx-r-o').textContent = r.toFixed(2);
    const dg = s.regime === 'line' ? 15 : 6;   // at the line, show the round-off width that straddles 1
    $('bx-bracket').textContent = '[' + s.bracket[0].toFixed(dg) + ', ' + s.bracket[1].toFixed(dg) + ']';
    const zone = $('bx-zone'); zone.dataset.regime = s.regime;
    zone.textContent = s.regime === 'settles' ? 'SETTLES' : s.regime === 'line' ? 'AT THE LINE' : 'WILL NOT SETTLE';
    $('bx-budget').textContent = s.budget != null ? int(s.budget) + ' bounces' : 'none: no budget is enough';
    $('bx-factor').textContent = s.factor != null ? '× ' + s.factor.toFixed(2) : 'no finite value';
    $('bx-total').textContent = s.exactTotal != null ? s.exactTotal.toFixed(2) : '—';
    setLight('a', s.lights.a, s.solver.settled ? 'settled within 10⁻³ at bounce ' + int(s.solver.settledAt) : 'not settled after ' + int(s.solver.ran) + ' bounces');
    setLight('b', s.lights.b, s.lights.b ? 'bracket sits below 1' : s.regime === 'line' ? 'bracket straddles 1' : 'bracket sits above 1');
    setLight('c', s.lights.c, s.lights.c ? 'v > 0 with (Av)ᵢ < vᵢ found' : 'no positive v exists');
    const note = $('bx-note'), refuse = $('bx-refuse'), strip = $('bx-strip');
    clearInterval(runTimer); runTimer = null;
    if (s.regime === 'settles') {
      refuse.hidden = true; strip.hidden = false; drawStrip(s);
      note.textContent = 'The settled light on the 26 patches. Total ' + s.exactTotal.toFixed(2) + ', which is 1/(1 − ρ) for one unit from the lamp.';
    } else {
      strip.hidden = true; refuse.hidden = false; drawStrip(s);
      if (s.regime === 'line') runLine(s);
      else { refuse.innerHTML = '<b>No solution to show.</b> Each bounce gives back more than the last (× ' + f4(s.rho) + '). The light grows without limit, so no steady light field exists. So the page draws no light field here.'; note.textContent = ''; }
    }
    $('bx-walk').textContent = walking ? 'Stop the walk' : 'Walk ρ from 0.80 to 1.20';
  }
  // At ρ = 1 the lamp's unit comes back whole every bounce: the running total climbs by the same deposit forever.
  function runLine(s) {
    let k = 0; const step = () => { k++; $('bx-refuse').innerHTML = '<b>No steady state.</b> Running energy total after bounce ' + int(k) + ': <b class="mono">' + k.toFixed(2) + '</b>. Each bounce deposits the same ' + s.solver.firstDeposit.toFixed(2) + ' again.'; };
    step(); $('bx-note').textContent = 'The exhibit ran ' + int(s.solver.ran) + ' bounces: the total was ' + s.solver.runningTotal.toFixed(2) + ', still climbing ' + s.solver.lastDeposit.toFixed(2) + ' per bounce.';
    if (!reduced) runTimer = setInterval(step, 120);
  }
  function walk() {
    walking = !walking; clearTimeout(walkTimer);
    // slow down near the line so 0.99, 1.00 and 1.01 each hold long enough to read
    const next = () => { const i = WALK.findIndex(v => v > +dial.value + 1e-9);
      if (i < 0) { walking = false; render(); return; } dial.value = WALK[i]; render();
      walkTimer = setTimeout(next, Math.abs(WALK[i] - 1) <= 0.015 ? 2600 : 650); };
    if (walking) { if (+dial.value >= 1.2) dial.value = 0.8; render(); walkTimer = setTimeout(next, 650); }
    render();
  }
  dial.oninput = () => { if (walking) { walking = false; clearTimeout(walkTimer); } render(); };
  $('bx-walk').onclick = walk;
  root.__boundary = { analyse, get, WALK, set(r) { dial.value = r; render(); return get(r); }, get shown() { return get(+(+dial.value).toFixed(2)); } };
  render();
})(typeof window !== 'undefined' ? window : globalThis);
