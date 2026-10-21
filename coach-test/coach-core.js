// coach-core.js — Chess Coach shared logic (Ticket 004).
// Used by the coach page (browser) and the Node test harness.
// Pure chess + coach math; no DOM, no network, no engine binary.
// Board model matches the v1.1 page: array of 64, index 0 = a8,
// piece = {t:'p|n|b|r|q|k', c:'w|b'}.
"use strict";
const CoachCore = (() => {
const VAL = { p: 1, n: 3, b: 3, r: 5, q: 9, k: 0 };
const fileOf = (i) => i % 8, rankOf = (i) => Math.floor(i / 8);
const onBoard = (f, r) => f >= 0 && f < 8 && r >= 0 && r < 8;
const sqName = (i) => "abcdefgh"[fileOf(i)] + (8 - rankOf(i));
const sqIdx = (s) => (8 - Number(s[1])) * 8 + "abcdefgh".indexOf(s[0]);
const opp = (c) => (c === "w" ? "b" : "w");

function startState() {
  const back = ["r","n","b","q","k","b","n","r"], b = new Array(64).fill(null);
  for (let f = 0; f < 8; f++) {
    b[f] = { t: back[f], c: "b" }; b[8 + f] = { t: "p", c: "b" };
    b[48 + f] = { t: "p", c: "w" }; b[56 + f] = { t: back[f], c: "w" };
  }
  return { board: b, turn: "w", castling: { K: true, Q: true, k: true, q: true },
           ep: -1, half: 0, full: 1 };
}
function cloneState(st) {
  return { board: st.board.map((x) => (x ? { t: x.t, c: x.c } : null)),
           turn: st.turn, castling: { ...st.castling }, ep: st.ep,
           half: st.half, full: st.full };
}
function isAttacked(bd, sq, by) {
  const f = fileOf(sq), r = rankOf(sq);
  const pr = by === "w" ? r + 1 : r - 1;
  for (const df of [-1, 1]) { const nf = f + df; if (onBoard(nf, pr)) { const p = bd[pr * 8 + nf]; if (p && p.c === by && p.t === "p") return true; } }
  for (const [df, dr] of [[1,2],[2,1],[-1,2],[-2,1],[1,-2],[2,-1],[-1,-2],[-2,-1]]) {
    const nf = f + df, nr = r + dr; if (onBoard(nf, nr)) { const p = bd[nr * 8 + nf]; if (p && p.c === by && p.t === "n") return true; }
  }
  for (let df = -1; df <= 1; df++) for (let dr = -1; dr <= 1; dr++) { if (!df && !dr) continue;
    const nf = f + df, nr = r + dr; if (onBoard(nf, nr)) { const p = bd[nr * 8 + nf]; if (p && p.c === by && p.t === "k") return true; } }
  const lines = [[1,0,"rq"],[-1,0,"rq"],[0,1,"rq"],[0,-1,"rq"],[1,1,"bq"],[1,-1,"bq"],[-1,1,"bq"],[-1,-1,"bq"]];
  for (const [df, dr, ts] of lines) {
    let nf = f + df, nr = r + dr;
    while (onBoard(nf, nr)) { const p = bd[nr * 8 + nf];
      if (p) { if (p.c === by && ts.includes(p.t)) return true; break; }
      nf += df; nr += dr; }
  }
  return false;
}
function kingSq(bd, c) { for (let i = 0; i < 64; i++) if (bd[i] && bd[i].t === "k" && bd[i].c === c) return i; return -1; }
function pseudoMoves(bd, i, cast, ep) {
  const p = bd[i]; if (!p) return [];
  const f = fileOf(i), r = rankOf(i), out = [];
  const add = (to, flags) => out.push(Object.assign({ from: i, to }, flags || {}));
  if (p.t === "p") {
    const dir = p.c === "w" ? -1 : 1, startRank = p.c === "w" ? 6 : 1, promoRank = p.c === "w" ? 0 : 7;
    const one = (r + dir) * 8 + f;
    if (onBoard(f, r + dir) && !bd[one]) {
      add(one, r + dir === promoRank ? { promo: true } : {});
      const two = (r + 2 * dir) * 8 + f;
      if (r === startRank && !bd[two]) add(two, { double: true });
    }
    for (const df of [-1, 1]) { const nf = f + df, nr = r + dir; if (!onBoard(nf, nr)) continue; const to = nr * 8 + nf;
      if (bd[to] && bd[to].c !== p.c) add(to, nr === promoRank ? { promo: true } : {});
      else if (to === ep) add(to, { epCapture: true });
    }
  } else if (p.t === "n" || p.t === "k") {
    const ds = p.t === "n" ? [[1,2],[2,1],[-1,2],[-2,1],[1,-2],[2,-1],[-1,-2],[-2,-1]]
                           : [[1,0],[-1,0],[0,1],[0,-1],[1,1],[1,-1],[-1,1],[-1,-1]];
    for (const [df, dr] of ds) { const nf = f + df, nr = r + dr; if (!onBoard(nf, nr)) continue; const to = nr * 8 + nf;
      if (!bd[to] || bd[to].c !== p.c) add(to); }
    if (p.t === "k") {
      const home = p.c === "w" ? 60 : 4;
      if (i === home && !isAttacked(bd, i, opp(p.c))) {
        const rights = p.c === "w" ? ["K", "Q"] : ["k", "q"];
        const sides = [{ right: rights[0], rookFrom: home + 3, empty: [home + 1, home + 2], kingTo: home + 2, pass: home + 1 },
                       { right: rights[1], rookFrom: home - 4, empty: [home - 1, home - 2, home - 3], kingTo: home - 2, pass: home - 1 }];
        for (const s of sides) {
          if (!cast[s.right]) continue;
          const rook = bd[s.rookFrom]; if (!rook || rook.t !== "r" || rook.c !== p.c) continue;
          if (s.empty.some((x) => bd[x])) continue;
          if (isAttacked(bd, s.pass, opp(p.c)) || isAttacked(bd, s.kingTo, opp(p.c))) continue;
          add(s.kingTo, { castle: s.right });
        }
      }
    }
  } else {
    let dirs = [];
    if (p.t === "b" || p.t === "q") dirs.push([1,1],[1,-1],[-1,1],[-1,-1]);
    if (p.t === "r" || p.t === "q") dirs.push([1,0],[-1,0],[0,1],[0,-1]);
    for (const [df, dr] of dirs) { let nf = f + df, nr = r + dr;
      while (onBoard(nf, nr)) { const to = nr * 8 + nf;
        if (!bd[to]) add(to); else { if (bd[to].c !== p.c) add(to); break; }
        nf += df; nr += dr; } }
  }
  return out;
}
function applyTo(bd, m, promo) {
  const p = bd[m.from]; bd[m.to] = promo ? { t: promo, c: p.c } : p; bd[m.from] = null;
  if (m.epCapture) { const capSq = rankOf(m.from) * 8 + fileOf(m.to); bd[capSq] = null; }
  if (m.castle) {
    const home = p.c === "w" ? 60 : 4;
    if (m.to === home + 2) { bd[home + 1] = bd[home + 3]; bd[home + 3] = null; }
    if (m.to === home - 2) { bd[home - 1] = bd[home - 4]; bd[home - 4] = null; }
  }
  return bd;
}
function legalMovesC(bd, i, cast, ep) {
  const p = bd[i]; if (!p) return [];
  return pseudoMoves(bd, i, cast, ep).filter((m) => {
    const copy = bd.map((x) => (x ? { t: x.t, c: x.c } : null));
    applyTo(copy, m, m.promo ? "q" : null);
    return !isAttacked(copy, kingSq(copy, p.c), opp(p.c));
  });
}
function allLegalState(st, c) {
  const out = [];
  for (let i = 0; i < 64; i++) if (st.board[i] && st.board[i].c === c) out.push(...legalMovesC(st.board, i, st.castling, st.ep));
  return out;
}
function applyMoveState(st, m, promoChoice) {
  const moving = st.board[m.from];
  let captured = null;
  if (st.board[m.to]) captured = st.board[m.to];
  if (m.epCapture) captured = st.board[rankOf(m.from) * 8 + fileOf(m.to)];
  applyTo(st.board, m, promoChoice || (m.promo ? "q" : null));
  if (moving.t === "k") { if (st.turn === "w") { st.castling.K = st.castling.Q = false; } else { st.castling.k = st.castling.q = false; } }
  const rookHome = { 56: "Q", 63: "K", 0: "q", 7: "k" };
  if (m.from in rookHome) st.castling[rookHome[m.from]] = false;
  if (m.to in rookHome) st.castling[rookHome[m.to]] = false;
  st.ep = m.double ? (m.from + m.to) / 2 : -1;
  st.half = (moving.t === "p" || captured) ? 0 : st.half + 1;
  if (st.turn === "b") st.full++;
  st.turn = opp(st.turn);
  return captured;
}
function sanBase(st, m, legalBefore) {
  const bd = st.board, p = bd[m.from];
  if (m.castle) return fileOf(m.to) === 6 ? "O-O" : "O-O-O";
  let s = "";
  const isCap = !!bd[m.to] || m.epCapture;
  if (p.t === "p") {
    if (isCap) s += "abcdefgh"[fileOf(m.from)] + "x";
    s += sqName(m.to);
    if (m.promo) s += "=" + (m.promoChoice || "q").toUpperCase();
  } else {
    s += p.t.toUpperCase();
    const others = legalBefore.filter((x) => x.to === m.to && x.from !== m.from && bd[x.from] && bd[x.from].t === p.t);
    if (others.length) {
      const sameFile = others.some((x) => fileOf(x.from) === fileOf(m.from));
      const sameRank = others.some((x) => rankOf(x.from) === rankOf(m.from));
      if (!sameFile) s += "abcdefgh"[fileOf(m.from)];
      else if (!sameRank) s += (8 - rankOf(m.from));
      else s += sqName(m.from);
    }
    if (isCap) s += "x";
    s += sqName(m.to);
  }
  return s;
}
function sanWithSuffix(st, m, promoChoice) {
  const legalBefore = allLegalState(st, st.turn);
  const mm = { ...m, promoChoice };
  let s = sanBase(st, mm, legalBefore);
  const after = cloneState(st); applyMoveState(after, mm, promoChoice);
  const replies = allLegalState(after, after.turn);
  const inCheck = isAttacked(after.board, kingSq(after.board, after.turn), opp(after.turn));
  if (replies.length === 0) s += inCheck ? "#" : "";
  else if (inCheck) s += "+";
  return s;
}
function parseSan(st, raw) {
  if (!raw || typeof raw !== "string") return null;
  const want = raw.trim().replace(/[!?]+$/g, "");
  const legal = allLegalState(st, st.turn);
  for (const m of legal) {
    const full = sanWithSuffix(st, m, m.promo ? "q" : null);
    const base = full.replace(/[+#]$/g, "");
    if (want === full || want === base) return m;
    if (m.promo) { // try each promotion piece
      for (const pr of ["q", "r", "b", "n"]) {
        const f2 = sanWithSuffix(st, m, pr).replace(/[+#]$/g, "");
        if (want === f2) { m.promoChoice = pr; return m; }
      }
    }
  }
  return null;
}
function parseUci(st, uci) {
  if (!uci || typeof uci !== "string" || uci.length < 4) return null;
  const from = sqIdx(uci.slice(0, 2)), to = sqIdx(uci.slice(2, 4));
  const legal = allLegalState(st, st.turn);
  const m = legal.find((x) => x.from === from && x.to === to);
  if (!m) return null;
  if (m.promo && uci[4]) m.promoChoice = uci[4].toLowerCase();
  return m;
}
function uciFor(m) { return sqName(m.from) + sqName(m.to) + (m.promo ? (m.promoChoice || "q") : ""); }
function fenFromState(st) {
  const rows = [];
  for (let r = 0; r < 8; r++) {
    let row = "", empty = 0;
    for (let f = 0; f < 8; f++) {
      const p = st.board[r * 8 + f];
      if (!p) { empty++; continue; }
      if (empty) { row += empty; empty = 0; }
      row += p.c === "w" ? p.t.toUpperCase() : p.t;
    }
    if (empty) row += empty;
    rows.push(row);
  }
  let cast = "";
  if (st.castling.K) cast += "K"; if (st.castling.Q) cast += "Q";
  if (st.castling.k) cast += "k"; if (st.castling.q) cast += "q";
  return rows.join("/") + " " + st.turn + " " + (cast || "-") + " " +
         (st.ep >= 0 ? sqName(st.ep) : "-") + " " + st.half + " " + st.full;
}
function stateFromSans(sans) {
  const st = startState();
  for (const s of sans) {
    const m = parseSan(st, s);
    if (!m) throw new Error("Unparseable SAN in line: " + s);
    applyMoveState(st, m, m.promoChoice || null);
  }
  return st;
}
// ---------- Coach math ----------
function windowForElo(elo) {
  if (elo <= 900) return 600;
  if (elo <= 1100) return 400;
  if (elo <= 1300) return 300;
  if (elo <= 1600) return 200;
  if (elo <= 1900) return 120;
  return 60;
}
function lineScore(l) { // side-to-move POV centipawns
  if (l.mate !== null && l.mate !== undefined) return l.mate > 0 ? 100000 - l.mate * 10 : -100000 - l.mate * 10;
  return l.cp || 0;
}
// multipvLines: [{uci, cp, mate}] from Stockfish, side-to-move POV, best first.
// Returns [{san, uci}] — scores stripped by construction.
function pruneCandidates(st, multipvLines, targetElo, cap) {
  cap = cap || 10;
  const win = windowForElo(targetElo);
  const legal = allLegalState(st, st.turn);
  const byUci = new Map(legal.map((m) => [uciFor(m), m]));
  const scored = (multipvLines || []).map((l) => ({ uci: l.uci, score: lineScore(l) }))
    .filter((l) => byUci.has(l.uci));
  const picked = new Map();
  if (scored.length) {
    const best = Math.max(...scored.map((l) => l.score));
    for (const l of scored) if (best - l.score <= win) picked.set(l.uci, l.score);
  }
  // forcing moves are always interesting: checks and captures
  for (const m of legal) {
    const isCap = !!st.board[m.to] || m.epCapture;
    const after = cloneState(st); applyMoveState(after, { ...m }, m.promo ? "q" : null);
    const givesCheck = isAttacked(after.board, kingSq(after.board, after.turn), st.turn);
    if (isCap || givesCheck) {
      const sc = scored.find((l) => l.uci === uciFor(m));
      if (sc) picked.set(uciFor(m), sc.score);
      else if (picked.size < cap) picked.set(uciFor(m), null);
    }
  }
  let arr = [...picked.entries()].map(([uci, score]) => ({ uci, score }));
  arr.sort((a, b) => (b.score ?? -Infinity) - (a.score ?? -Infinity));
  if (arr.length > cap) arr = arr.slice(0, cap);
  if (arr.length < 3 && scored.length) { // never hand the coach a near-empty list
    for (const l of scored) { if (arr.length >= 3) break; if (!arr.some((a) => a.uci === l.uci)) arr.push({ uci: l.uci, score: l.score }); }
  }
  // shuffle deterministically-ish (seeded by FEN) so order carries no ranking signal
  let seed = 0; const fen = fenFromState(st); for (const ch of fen) seed = (seed * 31 + ch.charCodeAt(0)) >>> 0;
  const rnd = () => (seed = (seed * 1103515245 + 12345) >>> 0) / 4294967296;
  for (let i = arr.length - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); [arr[i], arr[j]] = [arr[j], arr[i]]; }
  return arr.map(({ uci }) => {
    const m = byUci.get(uci);
    return { san: sanWithSuffix(st, m, m.promo ? "q" : null), uci };
  });
}
function fallbackCandidate(candidates, multipvLines) {
  // in-band legal fallback: the median-scored candidate (not the best —
  // a fallback should play at band, not at engine strength).
  if (!candidates || !candidates.length) return null;
  const scoreOf = new Map((multipvLines || []).map((l) => [l.uci, lineScore(l)]));
  const withScore = candidates.filter((c) => scoreOf.has(c.uci))
    .sort((a, b) => scoreOf.get(b.uci) - scoreOf.get(a.uci));
  if (!withScore.length) return candidates[0];
  return withScore[Math.floor(withScore.length / 2)];
}
// Failsafe: validate a coach-provided move string. Legal + (optionally)
// inside the candidate list. Returns {ok, move} or {ok:false, reason}.
function validateCoachMove(st, raw, candidates) {
  if (!raw || typeof raw !== "string" || !raw.trim())
    return { ok: false, reason: "empty-move" };
  let m = parseSan(st, raw) || parseUci(st, raw.trim().toLowerCase());
  if (!m) return { ok: false, reason: "illegal-move", detail: raw };
  if (candidates && candidates.length) {
    const u = uciFor(m);
    if (!candidates.some((c) => c.uci === u))
      return { ok: false, reason: "not-in-candidates", detail: raw };
  }
  return { ok: true, move: m, san: sanWithSuffix(st, m, m.promoChoice || null) };
}
function eloUpdate(playerElo, opponentElo, score, k) {
  k = k || 32;
  const expected = 1 / (1 + Math.pow(10, (opponentElo - playerElo) / 400));
  return Math.round(playerElo + k * (score - expected));
}
function eloFromScoreRate(scoreRate) { // rating diff implied by a score rate
  if (scoreRate <= 0) return -800;
  if (scoreRate >= 1) return 800;
  return Math.round(400 * Math.log10(scoreRate / (1 - scoreRate)));
}
// Calibration: step the coach target by +-100 when the player's
// performance (silent-scorer eval, white-POV cp averaged over the
// window, from the player's perspective) leaves the +-100cp band.
function calibrationStep(currentTarget, playerPovCpAvg) {
  let next = currentTarget;
  if (playerPovCpAvg > 100) next += 100;
  else if (playerPovCpAvg < -100) next -= 100;
  return Math.max(400, Math.min(2400, next));
}
// ---------- Review / lesson classification ----------
function pieceEnPrise(st, sq) {
  // Is the piece on sq attacked by the opponent and not adequately defended?
  const p = st.board[sq]; if (!p) return false;
  const enemy = opp(p.c);
  if (!isAttacked(st.board, sq, enemy)) return false;
  // find cheapest attacker value
  let cheapest = 99;
  for (let i = 0; i < 64; i++) {
    const a = st.board[i]; if (!a || a.c !== enemy) continue;
    if (legalMovesC(st.board, i, st.castling, st.ep).some((m) => m.to === sq)) cheapest = Math.min(cheapest, VAL[a.t]);
  }
  if (cheapest === 99) return false;
  if (!isAttacked(st.board, sq, p.c)) return true; // undefended: the capture is free
  return cheapest < VAL[p.t]; // defended, but the cheapest attacker still wins the exchange
}
function freeCaptureExists(st, c) {
  for (const m of allLegalState(st, c)) {
    const target = st.board[m.to];
    if (!target) continue;
    const after = cloneState(st); applyMoveState(after, { ...m }, m.promo ? "q" : null);
    const recap = isAttacked(after.board, m.to, opp(c));
    if (!recap && VAL[target.t] >= 3) return { move: m, value: VAL[target.t] };
    if (recap && VAL[target.t] > VAL[st.board[m.from].t] + 0 && VAL[target.t] >= 5) return { move: m, value: VAL[target.t] };
  }
  return null;
}
function mateInOneExists(st, c) {
  for (const m of allLegalState(st, c)) {
    const after = cloneState(st); applyMoveState(after, { ...m }, m.promo ? "q" : null);
    if (allLegalState(after, after.turn).length === 0 &&
        isAttacked(after.board, kingSq(after.board, after.turn), c)) return m;
  }
  return null;
}
// Classify one ply. stBefore = state before the move, m = the move played.
// Returns a reason class string.
function classifyPly(stBefore, m) {
  const mover = stBefore.turn;
  const after = cloneState(stBefore); applyMoveState(after, { ...m }, m.promoChoice || null);
  if (mateInOneExists(after, opp(mover))) return "allows-mate-threat";
  // Priority, stated plainly: a moved piece left en prise is the most
  // concrete fact about a move, so it outranks the missed mate. (The
  // Scholar's-mate position is both at once: Qxe5+ hangs the queen
  // AND misses Qxf7#. The queen is the lesson a beginner can verify.)
  if (pieceEnPrise(after, m.to) && VAL[stBefore.board[m.from].t] >= 3) return "hangs-piece";
  const mateMove = mateInOneExists(stBefore, mover);
  const playedWasMate = allLegalState(after, after.turn).length === 0 &&
    isAttacked(after.board, kingSq(after.board, after.turn), mover);
  if (mateMove && !playedWasMate && (mateMove.from !== m.from || mateMove.to !== m.to)) return "misses-mate";
  // a piece (not just the moved one) left en prise and capturable for profit
  for (let i = 0; i < 64; i++) {
    const p = after.board[i];
    if (p && p.c === mover && p.t !== "k" && VAL[p.t] >= 3 && pieceEnPrise(after, i)) return "hangs-piece";
  }
  const fc = freeCaptureExists(stBefore, mover);
  if (fc && (fc.move.from !== m.from || fc.move.to !== m.to)) return "misses-capture";
  return "positional-swing";
}
const LESSON_BY_CLASS = {
  "hangs-piece": "Before you move a piece, check its new square: is it attacked, and if so, is it defended for less than it's worth?",
  "misses-capture": "Before quiet moves, scan the whole board for captures you can win for free.",
  "allows-mate-threat": "Keep an eye on your king's escape squares and on enemy pieces aiming at them.",
  "misses-mate": "When your opponent's king looks trapped, spend ten seconds hunting for checkmate before anything else.",
  "positional-swing": "Develop your pieces toward the center and connect your rooks before starting attacks."
};
// scoreLog entries: {ply, san, mover, swing} where swing is cp change
// from the MOVER's perspective (negative = the move hurt the mover).
// plies: [{san, mover, stateBefore, move}] parallel to scoreLog for classes.
function buildReview(scoreLog, plies, playerColor, resultText, eloBefore, eloAfter) {
  const sorted = [...scoreLog].sort((a, b) => a.swing - b.swing);
  const worst = sorted.filter((s) => s.swing <= -80).slice(0, 3);
  const moments = worst.map((s) => {
    const pl = plies[s.ply];
    const cls = pl ? classifyPly(pl.stateBefore, pl.move) : "positional-swing";
    return { ply: s.ply, san: s.san, mover: s.mover, swingCp: s.swing, reasonClass: cls,
             lesson: LESSON_BY_CLASS[cls] };
  });
  const playerMoments = moments.filter((mm) => mm.mover === playerColor);
  const focus = (playerMoments[0] || moments[0] || null);
  // average centipawn loss per side (only negative swings count as loss)
  const cpl = { w: null, b: null };
  for (const c of ["w", "b"]) {
    const mine = scoreLog.filter((s) => s.mover === c);
    if (mine.length) cpl[c] = Math.round(mine.reduce((a, s) => a + Math.max(0, -s.swing), 0) / mine.length);
  }
  return { result: resultText, eloBefore, eloAfter, moments,
           focusLesson: focus ? focus.lesson : "",
           focusClass: focus ? focus.reasonClass : "",
           avgCpl: cpl };
}
// Lesson relevance in the CURRENT position, for the player's focus class.
// Returns {relevant, detail} — detail names the concrete thing, shown only
// when the player asks for the hint.
function lessonRelevance(st, focusClass, playerColor) {
  if (!focusClass || st.turn !== playerColor) return { relevant: false };
  if (focusClass === "hangs-piece") {
    for (let i = 0; i < 64; i++) {
      const p = st.board[i];
      if (p && p.c === playerColor && p.t !== "k" && VAL[p.t] >= 3 && pieceEnPrise(st, i))
        return { relevant: true, detail: "Your " + p.t.toUpperCase() + " on " + sqName(i) + " can be taken for profit right now — that is exactly your focus lesson." };
    }
  }
  if (focusClass === "misses-capture") {
    const fc = freeCaptureExists(st, playerColor);
    if (fc) return { relevant: true, detail: "There is a free capture available — look for the move that takes the " +
      (st.board[fc.move.to] ? st.board[fc.move.to].t.toUpperCase() : "piece") + " on " + sqName(fc.move.to) + "." };
  }
  if (focusClass === "misses-mate") {
    if (mateInOneExists(st, playerColor)) return { relevant: true, detail: "There is a checkmate in one in this position. Find it." };
  }
  if (focusClass === "allows-mate-threat") {
    if (mateInOneExists(st, opp(playerColor)))
      return { relevant: true, detail: "Your king is in real danger here — check what the opponent threatens before anything else." };
  }
  return { relevant: false };
}
return { VAL, startState, cloneState, isAttacked, kingSq, allLegalState, legalMovesC,
  applyMoveState, applyTo, sanBase, sanWithSuffix, parseSan, parseUci, uciFor,
  fenFromState, stateFromSans, windowForElo, pruneCandidates, fallbackCandidate,
  validateCoachMove, eloUpdate, eloFromScoreRate, calibrationStep, classifyPly,
  buildReview, lessonRelevance, LESSON_BY_CLASS, sqName, sqIdx, opp, pieceEnPrise };
})();
if (typeof module !== "undefined" && module.exports) module.exports = CoachCore;
