/* Wave function collapse — the model. No DOM in here; app.js draws it, qa/ drives it headlessly.
   Every claim in section 02 of index.html points at a line in this file (see METHOD-CHECK.md). */
(function (root) {
  'use strict';
  // Edges in the order N, E, S, W. 1 = connector, 0 = empty.
  // The 16 four-bit edge patterns, minus the four with exactly one connector (dead ends): 12 tiles.
  const LIST = [['0000', 'Blank'], ['1010', 'Straight ↕'], ['0101', 'Straight ↔'], ['1100', 'Corner N–E'], ['0110', 'Corner E–S'],
    ['0011', 'Corner S–W'], ['1001', 'Corner W–N'], ['0111', 'Tee, no N'], ['1011', 'Tee, no E'], ['1101', 'Tee, no S'], ['1110', 'Tee, no W'], ['1111', 'Crossing']];
  const TILES = LIST.map(([k, name], id) => ({ id, key: k, name, e: k.split('').map(Number) }));
  // Two tile sets: the full twelve, and 'Pipes' — the same minus the blank (eleven), so empty space must still carry a line.
  const SETS = { full: TILES.map(t => t.id), pipes: TILES.filter(t => t.key !== '0000').map(t => t.id) };
  const OPP = [2, 3, 0, 1];
  const DR = [-1, 0, 1, 0], DC = [0, 1, 0, -1];
  // fits(a, b, d): tile a may sit with tile b on its side d — the facing edges are equal. The only rule.
  const fits = (a, b, d) => TILES[a].e[d] === TILES[b].e[OPP[d]];

  // mulberry32: a small seeded 32-bit generator. Same seed, same pattern.
  function rng(seed) { let a = seed >>> 0; return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

  function Model(size, seed, set) {
    this.set = SETS[set] ? set : 'full'; this.size = size; this.N = size * size;
    this.contradictions = 0; this.attempts = 0; this.completed = 0;
    this.start(seed);
  }
  Model.prototype.start = function (seed) {
    this.seed = seed >>> 0; this.rand = rng(this.seed); this.attempts++;
    // every cell starts with every tile possible
    this.opts = Array.from({ length: this.N }, () => SETS[this.set].slice());
    this.tile = new Array(this.N).fill(-1);           // collapsed tile id, or -1
    this.collapsedCount = 0; this.phase = 'Live'; this.failed = -1;
    this.log = []; this.wave = new Array(this.N).fill(-1); this.waveStep = 0;
    this.next = this.pick();
  };
  // Selection: among cells not yet collapsed, those with the fewest remaining options; ties broken
  // uniformly at random by the seeded generator.
  Model.prototype.pick = function () {
    let min = Infinity, tied = [];
    for (let i = 0; i < this.N; i++) { if (this.tile[i] >= 0) continue; const n = this.opts[i].length;
      if (n < min) { min = n; tied = [i]; } else if (n === min) tied.push(i); }
    if (!tied.length) return -1;
    return tied[Math.floor(this.rand() * tied.length)];
  };
  // One step: collapse the highlighted cell to one of its options, uniformly at random, then propagate.
  Model.prototype.step = function () {
    if (this.phase !== 'Live') return null;
    const i = this.next, o = this.opts[i];
    let minOther = Infinity; for (let j = 0; j < this.N; j++) if (this.tile[j] < 0) minOther = Math.min(minOther, this.opts[j].length);
    const t = o[Math.floor(this.rand() * o.length)];
    return this.place(i, t, { options: o.length, minUncollapsed: minOther });
  };
  // Settle cell i on tile t and propagate. step() is the only caller in the running page; the QA fixture
  // (app.js, __wfc.fixtureContradiction) calls it directly and its log entries are marked fixture: true.
  Model.prototype.place = function (i, t, meta) {
    this.opts[i] = [t]; this.tile[i] = t; this.collapsedCount++;
    this.waveStep++; this.wave.fill(-1); this.wave[i] = 0;
    const entry = Object.assign({ k: this.log.length, cell: i, r: Math.floor(i / this.size), c: i % this.size, tile: t, removed: 0, touched: 0, depth: 0 }, meta);
    this.log.push(entry);
    const res = this.propagate(i);
    entry.removed = res.removed; entry.depth = res.depth; entry.touched = res.touched;
    if (res.contradiction >= 0) { this.phase = 'Contradiction'; this.failed = res.contradiction; this.contradictions++; this.next = -1; return entry; }
    if (this.collapsedCount === this.N) { this.phase = 'Done'; this.completed++; this.next = -1; return entry; }
    this.next = this.pick();
    return entry;
  };
  // Propagation: a stack of changed cells. For each neighbour of a changed cell, remove every tile that has
  // no compatible partner left in the changed cell; if the neighbour lost anything, it is pushed in turn.
  // Runs until stable, or until some cell's option set is empty (a contradiction).
  Model.prototype.propagate = function (start) {
    const S = this.size, stack = [start]; let removed = 0, depth = 0, touched = 0;
    while (stack.length) {
      const i = stack.pop(), r = Math.floor(i / S), c = i % S, here = this.opts[i];
      for (let d = 0; d < 4; d++) {
        const rr = r + DR[d], cc = c + DC[d]; if (rr < 0 || cc < 0 || rr >= S || cc >= S) continue;
        const j = rr * S + cc, before = this.opts[j];
        const kept = before.filter(b => here.some(a => fits(a, b, d)));
        if (kept.length === before.length) continue;
        removed += before.length - kept.length; this.opts[j] = kept;
        const dj = this.wave[i] + 1; if (this.wave[j] < 0) touched++; if (this.wave[j] < 0 || dj < this.wave[j]) this.wave[j] = dj; depth = Math.max(depth, this.wave[j]);
        if (!kept.length) return { removed, depth, touched, contradiction: j };
        stack.push(j);
      }
    }
    return { removed, depth, touched, contradiction: -1 };
  };
  // Readouts, computed from the live state.
  Model.prototype.readouts = function () {
    let sum = 0, n = 0;
    for (let i = 0; i < this.N; i++) if (this.tile[i] < 0) { sum += Math.log2(Math.max(1, this.opts[i].length)); n++; }
    return { collapsedPct: 100 * this.collapsedCount / this.N, entropy: n ? sum / n : 0, contradictions: this.contradictions, phase: this.phase };
  };
  // Mismatched internal edges in the collapsed tiles (0 on every finished grid).
  Model.prototype.mismatches = function () {
    const S = this.size; let bad = 0, checked = 0;
    for (let r = 0; r < S; r++) for (let c = 0; c < S; c++) { const a = this.tile[r * S + c];
      if (c + 1 < S) { const b = this.tile[r * S + c + 1]; if (a >= 0 && b >= 0) { checked++; if (!fits(a, b, 1)) bad++; } }
      if (r + 1 < S) { const b = this.tile[(r + 1) * S + c]; if (a >= 0 && b >= 0) { checked++; if (!fits(a, b, 2)) bad++; } } }
    return { bad, checked };
  };
  // A fresh seed, drawn from the run's own generator (used after a contradiction or a finished pattern).
  Model.prototype.drawSeed = function () { return 1 + Math.floor(this.rand() * 999998); };

  root.WFC = { TILES, SETS, fits, rng, Model, OPP };
  if (typeof module !== 'undefined') module.exports = root.WFC;
})(typeof window !== 'undefined' ? window : globalThis);
