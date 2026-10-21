// coach.js — Chess Coach page controller (Ticket 004, relay-gate build).
// Hooks the v1.1 board page by polling its move history (the single
// source of truth) and driving coach turns through the hardened relay
// gate (/v1/session, /v1/turn, /v1/review — see BEN-ACCESS-ASTRA.md).
// The page holds NO password material: the branch password the player
// types at the gate is checked server-side by the relay, which returns
// a short-lived bearer token kept in sessionStorage.
// Amendment A1 fallbacks: if the coach/relay is down (health check
// fails, network error, 503/504, exhausted retries) the game switches
// to a visibly labeled Stockfish-only mode for the rest of the game;
// after a failed reprompt the recovery move is Stockfish's top
// candidate (the packet's fallback), not an in-band engine move.
"use strict";
const CoachUI = (() => {
const C = CoachCore;
// ---------- per-branch config ----------
const COACH_CONFIG = (() => {
  const cfg = { branch: "you", relayUrl: "https://abraham-1.tail629694.ts.net" };
  if (typeof window !== "undefined" && window.COACH_CONFIG) Object.assign(cfg, window.COACH_CONFIG);
  if (typeof window !== "undefined" && window.COACH_BRANCH && !window.COACH_CONFIG) cfg.branch = window.COACH_BRANCH;
  try { // ?relay= override for local testing (stored nowhere)
    const loc = (typeof window !== "undefined" && window.location) ||
                (typeof location !== "undefined" ? location : null);
    if (loc && loc.search) {
      const r = new URLSearchParams(loc.search).get("relay");
      if (r) cfg.relayUrl = r;
    }
  } catch (_) {}
  cfg.relayUrl = String(cfg.relayUrl || "").replace(/\/+$/, "");
  return cfg;
})();
const BRANCH = COACH_CONFIG.branch;
const RELAY_URL = COACH_CONFIG.relayUrl;
const SF_URL = (typeof window !== "undefined" && window.COACH_SF_URL) || "stockfish/stockfish-19-lite-single.js";
const PRUNE_DEPTH = 10, SCORE_DEPTH = 10;
const PLAYER = "w", COACH = "b";
const TOKEN_KEY = "chessCoachToken." + BRANCH;

let sf = SF;                 // injectable for tests
let responder = null;        // injectable for tests; default = relay fetch
let dossier = loadDossier();
let mode = null;             // 'practice' | 'rated'
let targetElo = 800, gameStartElo = dossier.elo;
let lastPlySeen = 0, coachBusy = false, paused = false, gameActive = false;
let scoreLog = [], evalTrail = [], lastEval = null, stepMarks = 0;
let sessionRecord = null, currentCandidates = [], currentLines = [], currentFallback = null;
let hintDetail = null;
// relay-gate state
let sessionToken = null, storedGameId = null;
let gatePassword = null;     // memory only, never stored — lets a fresh
                             // game_id get its own session token per game
let gameId = null, offlineMode = false, offlineEntry = false, regated = false;
let connectionPromise = null;

function $(id) { return document.getElementById(id); }
function newGameId() {
  return Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 10) +
         Math.random().toString(36).slice(2, 6);
}
function loadDossier() {
  try {
    const raw = localStorage.getItem("chessCoachDossier." + BRANCH);
    if (raw) return JSON.parse(raw);
  } catch (_) {}
  return { elo: 800, calibrated: false, games: 0, eloHistory: [800], openings: {},
           mistake_patterns: [], weak_phases: [], focus_lesson: "", focus_class: "", lastResult: "" };
}
function saveDossier() { try { localStorage.setItem("chessCoachDossier." + BRANCH, JSON.stringify(dossier)); } catch (_) {} }
function replayState() { return C.stateFromSans(history.slice()); }
// All coach text reaches the DOM through textContent only — never innerHTML.
// Mirror the latest coach text beside the board so it stays readable
// during play without scrolling; the full log lives in #coachBody.
function setTicker(text) {
  const t = $("coachTicker"); if (!t) return;
  const clean = String(text).replace(/<[^>]*>/g, "").trim();
  if (!clean) return; // a cleared status is not a message — keep the last line
  t.textContent = clean;
}
function coachLine(text) {
  setTicker(text);
  const b = $("coachBody"); if (!b) return;
  const stateEl = $("coachState"); if (stateEl) stateEl.remove();
  const p = document.createElement("p"); p.className = "cline";
  p.textContent = String(text).replace(/<[^>]*>/g, "");
  b.appendChild(p); b.scrollTop = b.scrollHeight;
}
function setCoachState(text) {
  setTicker(text);
  const b = $("coachBody"); if (!b) return;
  let s = $("coachState");
  if (!s) { s = document.createElement("span"); s.id = "coachState"; s.className = "coachstate"; b.appendChild(s); }
  s.textContent = text;
}
function setModeLabel() {
  const ml = $("modeLine"); if (!ml) return;
  ml.textContent = offlineMode ? "Coach offline — playing Stockfish at your level" : "";
}
function alertLog(kind, detail) {
  const entry = { t: new Date().toISOString(), kind, detail, ply: history.length, branch: BRANCH };
  if (sessionRecord) sessionRecord.alerts.push(entry);
  try {
    const key = "chessCoachFailsafe." + BRANCH;
    const all = JSON.parse(localStorage.getItem(key) || "[]"); all.push(entry);
    localStorage.setItem(key, JSON.stringify(all));
  } catch (_) {}
  const b = $("alertBody"); if (!b) return;
  if (b.textContent.trim() === "No alerts.") b.textContent = "";
  const d = document.createElement("div");
  d.textContent = "⚠ " + kind + " — " + detail + " (ply " + entry.ply + ")";
  b.appendChild(d);
}
function renderDossier() {
  const b = $("dossierBody"); if (!b) return;
  const lines = [
    "Elo: " + dossier.elo + (dossier.calibrated ? "" : " (provisional — play a practice game)"),
    "Games vs coach: " + dossier.games,
  ];
  if (dossier.lastResult) lines.push("Last game: " + dossier.lastResult);
  if (dossier.focus_lesson) lines.push("Focus lesson: " + dossier.focus_lesson);
  if (dossier.mistake_patterns.length) lines.push("Patterns seen: " + dossier.mistake_patterns.join(", "));
  b.textContent = lines.join("\n");
}
// ---------- relay gate: session ----------
function expIsFuture(exp) {
  if (exp === null || exp === undefined) return true;
  const n = Number(exp); if (!isFinite(n)) return true;
  const ms = n > 1e12 ? n : n * 1000; // accept seconds or ms epochs
  return ms > Date.now();
}
function storeToken(token, exp, gid) {
  sessionToken = token; storedGameId = gid || null;
  try { sessionStorage.setItem(TOKEN_KEY, JSON.stringify({ token, exp, game_id: gid })); } catch (_) {}
}
function loadStoredToken() {
  try {
    const raw = sessionStorage.getItem(TOKEN_KEY);
    if (!raw) return false;
    const d = JSON.parse(raw);
    if (d && d.token && expIsFuture(d.exp)) { sessionToken = d.token; storedGameId = d.game_id || null; return true; }
  } catch (_) {}
  return false;
}
async function requestSession(password, gid) {
  let r;
  try {
    r = await fetch(RELAY_URL + "/v1/session", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ branch: BRANCH, password, game_id: gid }),
    });
  } catch (e) { const err = new Error("relay unreachable"); err.offline = true; throw err; }
  if (r.status === 401) { const err = new Error("wrong password"); err.status = 401; throw err; }
  if (!r.ok) { const err = new Error("relay HTTP " + r.status); err.status = r.status; throw err; }
  const data = await r.json();
  storeToken(data.token, data.exp, gid);
  return data;
}
function handleRegate() {
  regated = true; sessionToken = null;
  try { sessionStorage.removeItem(TOKEN_KEY); } catch (_) {}
  const gate = $("gate"); if (gate) gate.style.display = "";
  const gm = $("gateMsg"); if (gm) gm.textContent = "Your session expired — enter the password again.";
  setCoachState("Session expired — re-enter the password to continue.");
}
// Gate submit: password is checked by the relay, never by this page.
async function tryGate() {
  const input = $("gateInput"), gm = $("gateMsg");
  const pw = input ? input.value : "";
  if (gm) gm.textContent = "Checking…";
  const gid = newGameId();
  try {
    await requestSession(pw, gid);
  } catch (e) {
    if (e && e.status === 401) { if (gm) gm.textContent = "Wrong password — try again."; return false; }
    if (gm) gm.textContent = "Can't reach the coach relay right now.";
    const ob = $("gateOfflineBtn"); if (ob) ob.style.display = "";
    return false;
  }
  gatePassword = pw; gameId = gid; regated = false;
  const gate = $("gate"); if (gate) gate.style.display = "none";
  if (gm) gm.textContent = "";
  if (gameActive && !gameOver && turn === COACH) coachTurn();
  return true;
}
function enterOfflineFromGate() {
  offlineEntry = true;
  const gate = $("gate"); if (gate) gate.style.display = "none";
  const ml = $("modeLine"); if (ml) ml.textContent = "Coach offline — playing Stockfish at your level";
  coachLine("Coach offline — playing Stockfish at your level. Start a game whenever you're ready.");
}
// ---------- relay: turn / review ----------
async function fetchWithTimeout(url, opts, ms) {
  const ctl = typeof AbortController !== "undefined" ? new AbortController() : null;
  const timer = ctl ? setTimeout(() => ctl.abort(), ms) : null;
  try { return await fetch(url, { ...opts, signal: ctl ? ctl.signal : undefined }); }
  finally { if (timer) clearTimeout(timer); }
}
async function relayTurn(packet, _note) {
  // _note (reprompt reason) is a test-responder seam only; the /v1/turn
  // contract body is fixed, so a reprompt simply re-sends the packet.
  if (!sessionToken) { handleRegate(); const e = new Error("no session token"); e.regate = true; throw e; }
  for (let attempt = 0; attempt < 2; attempt++) {
    let r;
    try {
      r = await fetchWithTimeout(RELAY_URL + "/v1/turn", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": "Bearer " + sessionToken },
        body: JSON.stringify(packet),
      }, 70000);
    } catch (e) { const err = new Error("relay unreachable"); err.offline = true; throw err; }
    if (r.status === 401) { handleRegate(); const e = new Error("session rejected"); e.regate = true; throw e; }
    if (r.status === 429 && attempt === 0) { // too fast / caps: one spaced retry
      await new Promise((res) => setTimeout(res, 400));
      continue;
    }
    if (!r.ok) { // 429 exhausted, 503 kill switch/coach down, 504 timeout, 400 packet fault
      const err = new Error("relay HTTP " + r.status); err.offline = true; err.status = r.status; throw err;
    }
    return await r.json();
  }
  const err = new Error("relay retries exhausted"); err.offline = true; throw err;
}
async function relayReview(body) {
  let r;
  try {
    r = await fetchWithTimeout(RELAY_URL + "/v1/review", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": "Bearer " + sessionToken },
      body: JSON.stringify(body),
    }, 70000);
  } catch (e) { const err = new Error("relay unreachable"); err.offline = true; throw err; }
  if (r.status === 401) { handleRegate(); const e = new Error("session rejected"); e.regate = true; throw e; }
  if (!r.ok) { const err = new Error("relay HTTP " + r.status); err.status = r.status; throw err; }
  return await r.json();
}
// Per-game connection setup: health check first (A1: a failed health
// check means this game is Stockfish-only), then a session token bound
// to this game's fresh game_id when the password is in memory.
function prepareConnection() {
  if (responder) return Promise.resolve(); // injected test responder replaces the relay
  if (offlineEntry) { enterOfflineMode("chosen at the gate"); return Promise.resolve(); }
  return (async () => {
    try {
      const r = await fetchWithTimeout(RELAY_URL + "/v1/health", { method: "GET" }, 10000);
      if (!r.ok) throw new Error("health HTTP " + r.status);
    } catch (e) { enterOfflineMode("the relay health check failed"); return; }
    if (gatePassword) {
      try { await requestSession(gatePassword, gameId); }
      catch (e) {
        if (e && e.status === 401) handleRegate();
        else enterOfflineMode("the relay session could not be opened");
      }
    }
  })();
}
function enterOfflineMode(why) {
  if (offlineMode) return;
  offlineMode = true;
  if (sessionRecord) sessionRecord.offline = true;
  setModeLabel();
  coachLine("Coach offline — playing Stockfish at your level (" + why + "). No more coach calls this game.");
}
// ---------- game flow ----------
function startGame(kind) {
  reset(); // base page reset
  scoreLog = []; evalTrail = []; lastEval = null; stepMarks = 0;
  lastPlySeen = 0; paused = false; gameActive = true; coachBusy = false;
  offlineMode = false; currentFallback = null;
  mode = kind;
  gameStartElo = dossier.elo;
  targetElo = kind === "practice" ? 800 : dossier.elo + 50;
  // Fresh game_id per game; reuse the gate session's id only when the
  // token came from storage and no password is in memory to re-bind.
  gameId = (!gatePassword && storedGameId) ? storedGameId : newGameId();
  sessionRecord = { startedAt: new Date().toISOString(), branch: BRANCH, mode, gameId,
                    targetStart: targetElo, alerts: [], flagged: false, moves: [], offline: false };
  $("reviewPanel").style.display = "none";
  $("alertBody").textContent = "No alerts.";
  coachLine(kind === "practice"
    ? "Practice game. I'll adjust my strength as we play to find your level. Good luck!"
    : "New game. I'm playing at about " + targetElo + " for this one. Your move.");
  setCoachState("");
  renderDossier();
  setModeLabel();
  connectionPromise = prepareConnection();
  scorePosition(); // baseline eval of startpos
}
async function scorePosition() {
  try {
    const st = replayState();
    const ev = await sf.evaluateWhite(C.fenFromState(st), SCORE_DEPTH);
    if (ev === null || ev === undefined) return;
    if (lastEval !== null && history.length > 0) {
      const plyIdx = history.length - 1;
      if (!scoreLog.some((s) => s.ply === plyIdx)) {
        const mover = plyIdx % 2 === 0 ? "w" : "b";
        const swing = (ev - lastEval) * (mover === "w" ? 1 : -1);
        scoreLog.push({ ply: plyIdx, san: history[plyIdx], mover, swing: Math.round(swing) });
      }
    }
    lastEval = ev; evalTrail.push(ev);
  } catch (_) { /* scorer is silent; failures never touch the game */ }
}
async function maybeCalibrate() {
  if (mode !== "practice" || !gameActive) return;
  const marks = Math.floor(history.length / 10);
  if (marks <= stepMarks || history.length === 0) return;
  stepMarks = marks;
  const windowEvals = evalTrail.slice(-10);
  if (!windowEvals.length) return;
  const avg = windowEvals.reduce((a, b) => a + b, 0) / windowEvals.length;
  const next = C.calibrationStep(targetElo, avg);
  if (next !== targetElo) {
    targetElo = next;
    coachLine("Calibration: I'm adjusting my target to " + targetElo + " based on how this game is going.");
  }
}
function pauseGame(why) {
  paused = true; coachBusy = false;
  try { localStorage.setItem("chessCoachPaused." + BRANCH, JSON.stringify({
    history: history.slice(), mode, targetElo, at: new Date().toISOString(), why })); } catch (_) {}
  setCoachState("Paused — " + why + " ");
  const b = $("coachBody"); if (!b) return;
  const btn = document.createElement("button"); btn.textContent = "Resume";
  btn.addEventListener("click", () => { paused = false; setCoachState("Coach is thinking…"); coachTurn(); });
  b.appendChild(btn);
}
// Stockfish's top candidate, captured from the ranked lines BEFORE
// pruneCandidates shuffles the packet list: the first ranked line that
// survived pruning. Page and relay agree on this as the fallback move.
function computeTopCandidate() {
  for (const l of currentLines) {
    const c = currentCandidates.find((x) => x.uci === l.uci);
    if (c) return { san: c.san, uci: c.uci };
  }
  return currentCandidates.length ? { san: currentCandidates[0].san, uci: currentCandidates[0].uci } : null;
}
async function offlineCoachMove(st) {
  const fen = C.fenFromState(st);
  let m = null;
  try { // in-page Stockfish at the game's target Elo (adapter UCI_Elo/skill)
    if (sf && sf.bestmoveAtElo) {
      const uci = await sf.bestmoveAtElo(fen, targetElo, 12);
      if (uci) m = C.parseUci(st, uci);
    }
  } catch (_) {}
  if (!m && currentFallback) m = C.parseSan(st, currentFallback.san) || C.parseUci(st, currentFallback.uci);
  if (!m && currentCandidates.length) {
    const c0 = currentCandidates[0];
    m = C.parseSan(st, c0.san) || C.parseUci(st, c0.uci);
  }
  if (m) {
    applyCoachMove(m);
    sessionRecord.moves.push({ ply: history.length, san: C.sanWithSuffix(st, m, m.promoChoice || null), via: "stockfish-offline" });
    return;
  }
  pauseGame("no offline move available.");
}
async function coachTurn() {
  if (coachBusy || paused || !gameActive || gameOver || regated) return;
  coachBusy = true;
  setCoachState("Coach is thinking…");
  try {
    if (connectionPromise) { const p = connectionPromise; connectionPromise = null; try { await p; } catch (_) {} }
    if (regated) return;
    const st = replayState();
    const fen = C.fenFromState(st);
    const { lines } = await sf.analyze(fen, 10, PRUNE_DEPTH);
    currentLines = lines || [];
    currentCandidates = C.pruneCandidates(st, currentLines, targetElo);
    if (!currentCandidates.length) { pauseGame("no candidate moves available."); return; }
    currentFallback = computeTopCandidate();
    if (offlineMode) { await offlineCoachMove(st); return; }
    const packet = { game_id: gameId, fen, moves: history.slice(),
                     candidates: currentCandidates.map((c) => ({ san: c.san, uci: c.uci })),
                     fallback: currentFallback ? { san: currentFallback.san, uci: currentFallback.uci } : null,
                     target_elo: targetElo };
    if ("cp" in (packet.candidates[0] || {}) || "score" in (packet.candidates[0] || {}))
      throw new Error("packet leak: scores present in candidates");
    const resp = await (responder || relayTurn)(packet);
    await handleCoachResponse(resp, packet, false);
  } catch (e) {
    if (e && e.regate) { /* gate is showing again; the game waits for re-entry */ }
    else if (!offlineMode) {
      // A1 coach-down fallback: switch this game to Stockfish-only.
      enterOfflineMode("the coach could not be reached (" + (e.message || e) + ")");
      try { await offlineCoachMove(replayState()); }
      catch (_) { pauseGame("the coach and the offline engine are both unavailable."); }
    } else {
      pauseGame("the offline engine could not move (" + (e.message || e) + ").");
    }
  } finally { coachBusy = false; }
}
async function handleCoachResponse(resp, packet, isReprompt) {
  const st = replayState();
  const raw = resp && resp.move;
  const v = C.validateCoachMove(st, raw, currentCandidates);
  if (v.ok) {
    if (resp.coach_line) coachLine("Coach: " + resp.coach_line);
    applyCoachMove(v.move);
    sessionRecord.moves.push({ ply: history.length, san: v.san, via: isReprompt ? "reprompt" : "coach" });
    return;
  }
  alertLog("FAILSAFE " + v.reason, "coach tried '" + raw + "' at " + packet.fen);
  if (!isReprompt) {
    coachLine("The coach suggested a move that isn't available here — asking again.");
    const resp2 = await (responder || relayTurn)(packet,
      "Your previous move '" + raw + "' was rejected: " + v.reason + ". Pick exactly one move from the candidate list.");
    await handleCoachResponse(resp2, packet, true);
    return;
  }
  // A1: after a failed reprompt, play the packet's fallback move —
  // Stockfish's top candidate — the same move the relay falls back to.
  const fb = packet.fallback || currentFallback || C.fallbackCandidate(currentCandidates, currentLines);
  sessionRecord.flagged = true;
  // No third alert here: the two attempts already alerted above, and
  // the fallback is recorded in sessionRecord.moves (via:"fallback")
  // plus the flag. One alert per illegal attempt is the counting
  // rule calibration relies on.
  coachLine("Coach stumbled, recovered — Stockfish's top candidate was played for the coach.");
  if (fb) {
    const m2 = C.parseSan(st, fb.san) || C.parseUci(st, fb.uci);
    if (m2) { applyCoachMove(m2); sessionRecord.moves.push({ ply: history.length, san: fb.san, via: "fallback" }); }
  }
}
function applyCoachMove(coreMove) {
  const pageMoves = legalMoves(board, coreMove.from, castling, epSquare).filter((m) => m.to === coreMove.to);
  if (!pageMoves.length) { alertLog("FAILSAFE internal", "validated move not found in page engine"); return; }
  doMove(pageMoves[0], coreMove.promoChoice || null);
}
// ---------- hints ----------
async function checkLessonHint() {
  hintDetail = null;
  if (!gameActive || gameOver || turn !== PLAYER || coachBusy || paused) return;
  const rel = C.lessonRelevance(replayState(), dossier.focus_class, PLAYER);
  if (rel.relevant) {
    hintDetail = rel.detail;
    setCoachState("Your focus lesson is relevant in this position — press Hint if you want it.");
  }
}
async function onHint() {
  if (hintDetail) { coachLine("Hint: " + hintDetail); return; }
  try {
    const st = replayState();
    const { bestmove } = await sf.analyze(C.fenFromState(st), 1, 12);
    const m = bestmove && C.parseUci(st, bestmove);
    coachLine(m ? "Hint: the strongest idea here is " + C.sanWithSuffix(st, m, m.promoChoice || null) + "."
                : "Hint: nothing forcing — develop a piece toward the center.");
  } catch (_) { coachLine("Hint: the scorer is unavailable right now."); }
}
// ---------- game end / review ----------
function renderReview(review, opts) {
  const rp = $("reviewPanel"), rb = $("reviewBody");
  if (!rp || !rb) return;
  rp.style.display = "";
  rb.innerHTML = "";
  const addP = (text) => { const p = document.createElement("p"); p.textContent = text; rb.appendChild(p); return p; };
  addP(opts.resultText + " Your Elo: " + review.eloBefore + " → " + review.eloAfter +
       (opts.mode === "practice" ? " (calibrated estimate)" : "") +
       " Average centipawn loss — you: " + (review.avgCpl.w ?? "—") + ", coach: " + (review.avgCpl.b ?? "—"));
  if (opts.onlineReview && opts.onlineReview.review_text) {
    addP(opts.onlineReview.review_text);
    if (opts.onlineReview.focus_lesson)
      addP("Focus lesson for next time: " + opts.onlineReview.focus_lesson);
  } else {
    if (review.moments.length) {
      addP("Key moments");
      const ul = document.createElement("ul");
      for (const mm of review.moments) {
        const li = document.createElement("li");
        li.textContent = mm.san + " (" + (mm.mover === "w" ? "you" : "coach") + ", " + mm.reasonClass + ") — " + mm.lesson;
        ul.appendChild(li);
      }
      rb.appendChild(ul);
    } else addP("No big swings that game — a tight one.");
    if (review.focusLesson) addP("Focus lesson for next time: " + review.focusLesson);
  }
  if (offlineMode) addP("Offline review — computed on this page (the coach was offline).");
  else if (opts.reviewNote) addP(opts.reviewNote);
}
async function finishGame() {
  gameActive = false;
  await scorePosition();
  const st = replayState();
  const replies = C.allLegalState(st, st.turn);
  const inCheck = C.isAttacked(st.board, C.kingSq(st.board, st.turn), C.opp(st.turn));
  let resultText, score;
  if (replies.length === 0 && inCheck) {
    const winner = C.opp(st.turn);
    resultText = winner === PLAYER ? "You won — checkmate!" : "Coach wins — checkmate.";
    score = winner === PLAYER ? 1 : 0;
  } else { resultText = "Draw — stalemate."; score = 0.5; }
  const plies = [];
  for (let i = 0; i < history.length; i++) {
    const before = C.stateFromSans(history.slice(0, i));
    plies.push({ san: history[i], mover: i % 2 === 0 ? "w" : "b", stateBefore: before, move: C.parseSan(before, history[i]) });
  }
  let eloAfter = dossier.elo, onlineReview = null, reviewNote = "";
  if (mode === "practice") {
    eloAfter = targetElo; // the resting calibration target is the estimate (spec s.5)
    dossier.calibrated = true;
  } else if (mode === "rated" && !offlineMode && sessionToken && !responder) {
    // Online review: the relay's dossier is authoritative for elo/focus.
    const prelim = C.buildReview(scoreLog, plies, PLAYER, resultText, gameStartElo, gameStartElo);
    const body = { game_id: gameId,
                   result: score === 1 ? "1-0" : score === 0 ? "0-1" : "1/2-1/2",
                   moves: history.slice(),
                   key_moments: prelim.moments.map((mm) => ({ ply: mm.ply, san: mm.san,
                     swing_cp: mm.swingCp, reason_class: mm.reasonClass })),
                   elo_before: gameStartElo };
    try { onlineReview = await relayReview(body); }
    catch (e) { if (e && e.regate) { /* re-gate shown; local review still renders below */ } onlineReview = null; }
    if (onlineReview) eloAfter = onlineReview.elo_after;
    else { eloAfter = C.eloUpdate(dossier.elo, targetElo, score); reviewNote = "Relay review unavailable — this review was computed on this page."; }
  } else if (mode === "rated") {
    eloAfter = C.eloUpdate(dossier.elo, targetElo, score);
  }
  const review = C.buildReview(scoreLog, plies, PLAYER, resultText, gameStartElo, eloAfter);
  if (onlineReview) { review.eloBefore = onlineReview.elo_before; review.eloAfter = onlineReview.elo_after; }
  dossier.elo = eloAfter; dossier.games++; dossier.lastResult = resultText;
  dossier.eloHistory.push(eloAfter);
  const firstTwo = history.filter((_, i) => i % 2 === 0).slice(0, 2).join(" ");
  if (firstTwo) dossier.openings[firstTwo] = (dossier.openings[firstTwo] || 0) + 1;
  if (review.focusClass && !dossier.mistake_patterns.includes(review.focusClass))
    dossier.mistake_patterns.push(review.focusClass);
  if (onlineReview && onlineReview.focus_lesson) {
    dossier.focus_lesson = onlineReview.focus_lesson;
    if (review.focusClass) dossier.focus_class = review.focusClass;
  } else if (review.focusLesson) { dossier.focus_lesson = review.focusLesson; dossier.focus_class = review.focusClass; }
  saveDossier(); renderDossier();
  try { localStorage.removeItem("chessCoachPaused." + BRANCH); } catch (_) {}
  renderReview(review, { resultText, mode, onlineReview, reviewNote });
  coachLine("Game over. " + resultText + " Your review session is below the board.");
  if (sessionRecord) { sessionRecord.review = review; sessionRecord.onlineReview = !!onlineReview;
    sessionRecord.finishedAt = new Date().toISOString();
    try { localStorage.setItem("chessCoachLastSession." + BRANCH, JSON.stringify(sessionRecord)); } catch (_) {} }
}
// ---------- wiring ----------
function poll() {
  if (history.length !== lastPlySeen) {
    lastPlySeen = history.length;
    scorePosition();
    maybeCalibrate();
    if (gameOver && gameActive) { finishGame(); return; }
    if (gameActive && !gameOver && turn === COACH) coachTurn();
    if (gameActive && !gameOver && turn === PLAYER) checkLessonHint();
  }
  if (gameOver && gameActive) finishGame();
}
function init(opts) {
  opts = opts || {};
  if (opts.sf) sf = opts.sf;
  if (opts.responder) responder = opts.responder;
  if (typeof document !== "undefined" && document.body) {
    const bl = $("branchLine"); if (bl) bl.textContent = "Branch: " + BRANCH + ".";
    renderDossier();
    const nb = $("newGameBtn"); if (nb) nb.addEventListener("click", () => startGame(dossier.calibrated ? "rated" : "practice"));
    const pb = $("practiceBtn"); if (pb) pb.addEventListener("click", () => startGame("practice"));
    const hb = $("hintBtn"); if (hb) hb.addEventListener("click", onHint);
    const gate = $("gate");
    if (gate) {
      if (loadStoredToken()) gate.style.display = "none";
      const gb = $("gateBtn"); if (gb) gb.addEventListener("click", () => { tryGate(); });
      const gi = $("gateInput"); if (gi) gi.addEventListener("keydown", (e) => { if (e.key === "Enter") tryGate(); });
      const ob = $("gateOfflineBtn"); if (ob) ob.addEventListener("click", () => enterOfflineFromGate());
    }
  }
  sf.start(SF_URL).then(() => setCoachState("Coach is ready. Start a new game when you are."))
    .catch(() => setCoachState("The analysis engine did not load — games need it for move candidates."));
  setInterval(poll, 300);
}
return { init, startGame, coachTurn, handleCoachResponse, tryGate, _test: {
  getDossier: () => dossier, getScoreLog: () => scoreLog, getSession: () => sessionRecord,
  getTarget: () => targetElo, setScoreLog: (s) => { scoreLog = s; },
  getOffline: () => offlineMode, getGameId: () => gameId, hasToken: () => !!sessionToken,
  finishGame, replayState } };
})();
if (typeof window !== "undefined" && !window.__coachManualInit)
  window.addEventListener("DOMContentLoaded", () => CoachUI.init());
if (typeof module !== "undefined" && module.exports) module.exports = CoachUI;
