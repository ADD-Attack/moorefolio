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
const LESSON_IDS = ["pawn","rook","bishop","knight","queen","king","capturing","king-safety"];
const LEVEL_THRESHOLDS = [0,50,120,220,350,500,700,950,1250,1600];
function levelFor(points) { let n = 0; for (const t of LEVEL_THRESHOLDS) if (points >= t) n++; return Math.max(1, n); }
function todayStr() { const d = new Date(); return d.getFullYear() + "-" + String(d.getMonth()+1).padStart(2,"0") + "-" + String(d.getDate()).padStart(2,"0"); }
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
function sanitizeDossier(d) {
  const out = { points: 0, lessons: {}, gamesPlayed: 0, gamesFinished: 0, gamesWon: 0,
                lastVisit: null, muted: false, undoRetryPaid: {} };
  for (const id of LESSON_IDS) out.lessons[id] = !!(d && d.lessons && d.lessons[id]);
  if (d) {
    if (Number.isFinite(d.points)) out.points = Math.max(0, Math.floor(d.points));
    for (const k of ["gamesPlayed","gamesFinished","gamesWon"]) if (Number.isFinite(d[k])) out[k] = Math.max(0, Math.floor(d[k]));
    if (typeof d.lastVisit === "string") out.lastVisit = d.lastVisit;
    out.muted = !!d.muted;
    if (d.undoRetryPaid && typeof d.undoRetryPaid === "object") out.undoRetryPaid = d.undoRetryPaid;
  }
  return out;
}
let pendingLevelUp = 0;
function loadDossier() {
  let d = null;
  try { const raw = localStorage.getItem("chessCoachDossier." + BRANCH); if (raw) d = JSON.parse(raw); } catch (_) {}
  const out = sanitizeDossier(d);
  // comeback award: +20 when the last visit was an earlier calendar day
  const today = todayStr();
  if (out.lastVisit && out.lastVisit < today) {
    const before = levelFor(out.points); out.points += 20;
    if (levelFor(out.points) > before) pendingLevelUp = levelFor(out.points);
    try { localStorage.setItem("chessCoachDossier." + BRANCH, JSON.stringify(out)); } catch (_) {}
  }
  out.lastVisit = today;
  // legacy fields the shared adult code paths still read (not persisted schema)
  out.elo = 800; out.calibrated = true; out.games = out.gamesFinished; out.eloHistory = [800];
  out.openings = {}; out.mistake_patterns = []; out.weak_phases = [];
  out.focus_lesson = ""; out.focus_class = ""; out.lastResult = "";
  return out;
}
function saveDossier() {
  try {
    const clean = sanitizeDossier(dossier);
    clean.lastVisit = dossier.lastVisit || todayStr();
    localStorage.setItem("chessCoachDossier." + BRANCH, JSON.stringify(clean));
  } catch (_) {}
}
function replayState() {
  if (!lessonBaseFen) return C.stateFromSans(history.slice());
  const st = stateFromFen(lessonBaseFen);
  for (const san of history.slice()) { // lessons are solo: White moves every ply
    st.turn = "w";
    const m = C.parseSan(st, san);
    if (!m) throw new Error("Unparseable lesson SAN: " + san);
    C.applyMoveState(st, m, m.promoChoice || null);
    st.turn = "w";
  }
  return st;
}
// All coach text reaches the DOM through textContent only — never innerHTML.
// Mirror the latest coach text beside the board so it stays readable
// during play without scrolling; the full log lives in #coachBody.
function setTicker(text) {
  const t = $("coachTicker"); if (!t) return;
  const clean = String(text).replace(/<[^>]*>/g, "").trim();
  if (!clean) return; // a cleared status is not a message — keep the last line
  t.textContent = clean;
}
function coachLine(text, opts) {
  setTicker(text);
  const clean = String(text).replace(/<[^>]*>/g, "");
  const b = $("coachBody"); if (!b) return;
  const stateEl = $("coachState"); if (stateEl) stateEl.remove();
  const p = document.createElement("p"); p.className = "cline";
  p.textContent = clean;
  p.addEventListener("click", () => speak(clean.replace(/^Coach: /, "")));
  b.appendChild(p); b.scrollTop = b.scrollHeight;
  if ((opts && opts.speak) || clean.startsWith("Coach:")) speak(clean.replace(/^Coach: /, ""));
}
// ---------- operator diagnostics (Ticket 005) ----------
// Errors ONLY: normal play writes nothing here. A DIAG line means a
// connection step actually failed, in a terse code an operator can
// read off a screenshot — no kid-facing explanation, ever. Entries
// are timestamped and mirrored into the session record
// (sessionRecord.diag), following the alertLog pattern.
const DIAG_CAP = 300;
let diagEntries = [];
function diag(line) {
  const entry = { t: new Date().toISOString(), line };
  diagEntries.push(entry);
  if (diagEntries.length > DIAG_CAP) diagEntries.splice(0, diagEntries.length - DIAG_CAP);
  if (sessionRecord) {
    const arr = sessionRecord.diag || (sessionRecord.diag = []);
    arr.push(entry);
    if (arr.length > DIAG_CAP) arr.splice(0, arr.length - DIAG_CAP);
  }
  const b = $("coachBody"); if (!b) return;
  const p = document.createElement("p"); p.className = "cline diag";
  p.textContent = line;
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
function updateGameInfo() { // the Coach is always the other side — never "Human vs. Human"
  const t = $("gameInfoTitle"); if (!t) return;
  t.textContent = lessonActive ? "Lesson — the Coach is teaching you" : "You vs. the Coach";
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
  const done = LESSON_IDS.filter((id) => dossier.lessons[id]).length;
  b.textContent = ["Points: " + dossier.points, "Level: " + levelFor(dossier.points),
    "Lessons done: " + done + " / 8", "Games played: " + dossier.gamesPlayed,
    "Games finished: " + dossier.gamesFinished, "Games won: " + dossier.gamesWon].join("\n");
  renderMenu();
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
  const t0 = Date.now();
  try {
    r = await fetch(RELAY_URL + "/v1/session", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ branch: BRANCH, password, game_id: gid }),
    });
  } catch (e) { diag("DIAG AUTH FAIL neterr"); const err = new Error("relay unreachable"); err.offline = true; throw err; }
  if (!r.ok) diag("DIAG AUTH " + r.status + " " + (Date.now() - t0) + "ms");
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
  const t0 = Date.now();
  for (let attempt = 0; attempt < 2; attempt++) {
    let r;
    try {
      r = await fetchWithTimeout(RELAY_URL + "/v1/turn", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": "Bearer " + sessionToken },
        body: JSON.stringify(packet),
      }, 70000);
    } catch (e) { diag("DIAG TURN FAIL neterr"); const err = new Error("relay unreachable"); err.offline = true; throw err; }
    if (r.status === 401) { diag("DIAG TURN 401 " + (Date.now() - t0) + "ms"); handleRegate(); const e = new Error("session rejected"); e.regate = true; throw e; }
    if (r.status === 429 && attempt === 0) { // too fast / caps: one spaced retry
      await new Promise((res) => setTimeout(res, 400));
      continue;
    }
    if (!r.ok) { // 429 exhausted, 503 kill switch/coach down, 504 timeout, 400 packet fault
      diag("DIAG TURN " + r.status + " " + (Date.now() - t0) + "ms");
      const err = new Error("relay HTTP " + r.status); err.offline = true; err.status = r.status; throw err;
    }
    return await r.json();
  }
  diag("DIAG TURN FAIL retry");
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
    let healthFailed = false;
    try {
      const t0 = Date.now();
      const r = await fetchWithTimeout(RELAY_URL + "/v1/health", { method: "GET" }, 10000);
      if (!r.ok) { diag("DIAG HEALTH " + r.status + " " + (Date.now() - t0) + "ms"); healthFailed = true; }
    } catch (e) { diag("DIAG HEALTH FAIL neterr"); healthFailed = true; }
    if (healthFailed) { enterOfflineMode("the relay health check failed"); return; }
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
  hideBigNext();
  reset(); // base page reset
  scoreLog = []; evalTrail = []; lastEval = null; stepMarks = 0;
  lastPlySeen = 0; paused = false; gameActive = true; coachBusy = false;
  offlineMode = false; currentFallback = null;
  mode = "kids";
  gameStartElo = 850;
  targetElo = 850; // kids: gate band is 400..2800; strength comes from the gentle candidate set
  lessonActive = false; currentLesson = null; lessonBaseFen = null; undoPendingRetry = false;
  dossier.gamesPlayed++; saveDossier();
  const km = $("kidsMenu"); if (km) km.style.display = "none";
  updateGameInfo();
  // Fresh game_id per game; reuse the gate session's id only when the
  // token came from storage and no password is in memory to re-bind.
  gameId = (!gatePassword && storedGameId) ? storedGameId : newGameId();
  sessionRecord = { startedAt: new Date().toISOString(), branch: BRANCH, mode, gameId,
                    targetStart: targetElo, alerts: [], diag: [], flagged: false, moves: [], offline: false };
  $("reviewPanel").style.display = "none";
  $("alertBody").textContent = "No alerts.";
  coachLine("New game! You are White — your move. Good luck, champion!");
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
  // Kids offline play picks from the gentle candidate set (median-scored
  // candidate), never the engine's best move.
  if (!m && currentCandidates.length) {
    const pick = C.fallbackCandidate(currentCandidates, currentLines) || currentCandidates[0];
    if (pick) m = C.parseSan(st, pick.san) || C.parseUci(st, pick.uci);
  }
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
    const gentle = await gentleCandidates(st, fen);
    currentLines = gentle.lines;
    currentCandidates = gentle.candidates;
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
    if (resp && resp.annotations) drawAnnotations(resp.annotations);
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
  addP(opts.resultText + " Points: " + dossier.points + " • Level " + levelFor(dossier.points) +
       ". Average centipawn loss — you: " + (review.avgCpl.w ?? "—") + ", coach: " + (review.avgCpl.b ?? "—"));
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
  dossier.gamesFinished++;
  const isWin = score === 1;
  if (isWin) dossier.gamesWon++;
  awardPoints(30, "game finished");
  if (isWin) { awardPoints(70, "game won"); spawnConfetti(150); }
  const review = C.buildReview(scoreLog, plies, PLAYER, resultText, gameStartElo, eloAfter);
  if (onlineReview) { review.eloBefore = onlineReview.elo_before; review.eloAfter = onlineReview.elo_after; }
  dossier.lastResult = resultText;
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
  updateGameInfo();
  showBigNext(isWin ? "You won! 🏆" : "Game over!", isWin ? "You won the game! Tap Next!" : "Good game! You finished! Tap Next!");
  if (sessionRecord) { sessionRecord.review = review; sessionRecord.onlineReview = !!onlineReview;
    sessionRecord.finishedAt = new Date().toISOString();
    try { localStorage.setItem("chessCoachLastSession." + BRANCH, JSON.stringify(sessionRecord)); } catch (_) {} }
}

// ---------- KIDS: lessons, annotations, pickup, TTS, undo, points ----------
let lessonActive = false, currentLesson = null, lessonBaseFen = null;
let lessonPrevState = null, lessonHeroCaps = 0, undoPendingRetry = false;
let lastSelectedSeen = -2, pickupTimer = null, pickupPending = null;
const reportedPickups = new Set();

function stateFromFen(fen) {
  const parts = String(fen).trim().split(/\s+/);
  const rows = parts[0].split("/");
  const board = new Array(64).fill(null);
  rows.forEach((row, r) => {
    let f = 0;
    for (const ch of row) {
      if (/\d/.test(ch)) f += Number(ch);
      else { board[r * 8 + f] = { t: ch.toLowerCase(), c: ch === ch.toUpperCase() ? "w" : "b" }; f++; }
    }
  });
  const cast = parts[2] || "-";
  return { board, turn: parts[1] || "w",
           castling: { K: cast.includes("K"), Q: cast.includes("Q"), k: cast.includes("k"), q: cast.includes("q") },
           ep: parts[3] && parts[3] !== "-" ? C.sqIdx(parts[3]) : -1,
           half: Number(parts[4] || 0), full: Number(parts[5] || 1) };
}
function blackCount(st, t) { return st.board.filter((p) => p && p.c === "b" && (!t || p.t === t)).length; }
const capCheck = (t, n) => (st, caps) => caps >= n && blackCount(st, t) <= (t ? blackCount(stateFromFen(currentLesson.fen), t) - n : 0);
// NOTE on adjusted FENs (chain-reachability, verified by hand against legal move gen):
// pawn: knights moved d5+f5 -> d5+e6 (a pawn can only capture diagonally forward; from e4 it
//   can take d5 then e6 in a chain — f5 is unreachable after either first capture).
// bishop: pawns g5+h6 (same long diagonal chain from c1) instead of a3+g5 (unreachable pair).
// knight: pawns a3,c2,e3 (b1->a3->c2->e3 chain) instead of a3,c3,d2 (no chain exists).
const LESSONS = [
  { id: "pawn", title: "Meet the Pawn ♟", hero: "p",
    fen: "4k3/8/4n3/3n4/4P3/8/8/4K3 w - - 0 1",
    goalText: "Your pawn is a hero! Capture BOTH black knights with your pawn.",
    targets: 2, check: (st, caps) => caps >= 2 },
  { id: "rook", title: "Rook ♜", hero: "r",
    fen: "6k1/8/8/p3p3/8/8/8/R6K w - - 0 1",
    goalText: "Zoom your rook around and capture BOTH black pawns!",
    targets: 2, check: (st, caps) => caps >= 2 },
  { id: "bishop", title: "Bishop ♝", hero: "b",
    fen: "6k1/8/7p/6p1/8/8/8/2B4K w - - 0 1",
    goalText: "Your bishop slides on diagonals. Capture BOTH black pawns!",
    targets: 2, check: (st, caps) => caps >= 2 },
  { id: "knight", title: "Knight ♞", hero: "n",
    fen: "6k1/8/8/8/8/p3p3/2p5/1N5K w - - 0 1",
    goalText: "Your knight jumps in an L shape! Capture ALL THREE black pawns.",
    targets: 3, check: (st, caps) => caps >= 3 },
  { id: "queen", title: "Queen ♛", hero: "q",
    fen: "6k1/8/8/3p3p/8/p7/8/3Q3K w - - 0 1",
    goalText: "Your queen goes every direction! Capture ALL THREE black pawns.",
    targets: 3, check: (st, caps) => caps >= 3 },
  { id: "king", title: "King ♚", hero: "k",
    fen: "6k1/8/8/8/8/8/4ppp1/5K2 w - - 0 1",
    goalText: "Your king steps one square at a time. Capture ALL THREE black pawns!",
    targets: 3, check: (st, caps) => caps >= 3 },
  { id: "capturing", title: "Capturing! ⚔", hero: null,
    fen: "6k1/8/8/3n1b1p/4P3/8/5N2/3Q3K w - - 0 1",
    goalText: "Capture ALL THREE black pieces — any of your pieces may capture!",
    targets: 3, check: (st, caps) => caps >= 3 },
  { id: "king-safety", title: "Keep Your King Safe 🛡", hero: "k",
    fen: "4r1k1/8/8/8/8/8/8/4K2R w - - 0 1",
    goalText: "Oh no — your king is in CHECK! Make ONE move so your king is safe.",
    targets: 0, check: (st) => history.length > 0 && !C.isAttacked(st.board, C.kingSq(st.board, "w"), "b") },
];
function lessonById(id) { return LESSONS.find((l) => l.id === id) || null; }

// ---------- TTS ----------
// Voice choice: speechSynthesis voices vary wildly by device and the
// bare default is usually the robotic one, so pick deliberately.
// Ranking (best first, English only): a saved parent choice always
// wins while that voice still exists; otherwise prefer, in order —
// "Google US English" (Chrome's natural US voice), Microsoft Natural
// voices (Aria/Jenny/Guy…), any other "Natural" voice, Samantha
// (macOS/iOS US), Daniel (macOS/iOS UK), other Google English, the
// older Windows US voices (Zira/David/Catherine) — then any English
// voice, then the browser's marked default, then the first voice.
const VOICE_PREFS = [
  /google us english/i,
  /microsoft.*(natural|aria|jenny|guy)/i,
  /natural/i,
  /samantha/i,
  /daniel/i,
  /google.*english/i,
  /zira|david|catherine/i,
];
const VOICE_KEY = "chessCoachVoice." + BRANCH;
function synth() {
  return (typeof window !== "undefined" && window.speechSynthesis) ||
         (typeof speechSynthesis !== "undefined" ? speechSynthesis : null);
}
function voiceList() {
  try { const ss = synth(); return (ss && ss.getVoices && ss.getVoices()) || []; }
  catch (_) { return []; }
}
function savedVoiceName() { try { return localStorage.getItem(VOICE_KEY) || ""; } catch (_) { return ""; } }
function voiceScore(v) { // lower is better; Infinity = not English
  if (!v || !/^en([-_]|$)/i.test(v.lang || "")) return Infinity;
  let r = VOICE_PREFS.findIndex((re) => re.test(v.name || ""));
  if (r === -1) r = VOICE_PREFS.length; // any other English voice
  if (/^en[-_]US/i.test(v.lang || "")) r -= 0.5; // US English wins ties
  return r;
}
function pickVoice() {
  const vs = voiceList();
  if (!vs.length) return null;
  const want = savedVoiceName();
  if (want) {
    const hit = vs.find((v) => (v.voiceURI && v.voiceURI === want) || v.name === want);
    if (hit) return hit;
  }
  let best = null, bestScore = Infinity;
  for (const v of vs) { const s = voiceScore(v); if (s < bestScore) { bestScore = s; best = v; } }
  if (best) return best;
  return vs.find((v) => v.default) || vs[0] || null;
}
function refreshVoicePicker() {
  const sel = $("voiceSelect"); if (!sel) return;
  const vs = voiceList();
  sel.innerHTML = "";
  for (const v of vs) {
    const o = document.createElement("option");
    o.value = v.voiceURI || v.name;
    o.textContent = v.name + (v.lang ? " (" + v.lang + ")" : "");
    sel.appendChild(o);
  }
  const chosen = pickVoice();
  if (chosen) sel.value = chosen.voiceURI || chosen.name;
}
function initVoicePicker() {
  const sel = $("voiceSelect"); if (!sel) return;
  refreshVoicePicker();
  sel.addEventListener("change", () => {
    try { localStorage.setItem(VOICE_KEY, sel.value); } catch (_) {}
  });
  const sb = $("voiceSampleBtn");
  if (sb) sb.addEventListener("click", () => speak("Hello! I am your chess coach. Let's play chess!"));
  const ss = synth(); // voices often arrive async — repopulate when they land
  if (ss && ss.addEventListener) ss.addEventListener("voiceschanged", refreshVoicePicker);
}
let ttsDiagDone = false;
function speak(text) {
  try {
    if (dossier.muted) return;
    const ss = synth();
    if (!ss) return;
    ss.cancel();
    let u;
    const U = (typeof SpeechSynthesisUtterance !== "undefined") ? SpeechSynthesisUtterance
            : (typeof window !== "undefined" ? window.SpeechSynthesisUtterance : null);
    u = U ? new U(String(text)) : { text: String(text) };
    u.rate = 0.92; u.pitch = 1.05;
    const v = pickVoice();
    if (!ttsDiagDone) { // once per page load: flag a device with no voice at all
      ttsDiagDone = true;
      if (!v) diag("DIAG TTS V=" + voiceList().length + " name=NONE");
    }
    if (v) { try { u.voice = v; if (v.lang) u.lang = v.lang; } catch (_) {} }
    ss.speak(u);
  } catch (_) {}
}
// ---------- big Next overlay (lesson done / game over) ----------
// A kid who cannot read the small buttons needs the way forward to
// be one huge, spoken target in the middle of the screen. The light
// backdrop never traps: a plain ✕ closes it and the board (with its
// own Menu button) is right there.
let bigNextEl = null, bigNextMsgEl = null;
function ensureBigNext() {
  if (bigNextEl) return bigNextEl;
  const wrap = document.createElement("div"); wrap.id = "bigNextOverlay";
  const card = document.createElement("div"); card.className = "card";
  const msg = document.createElement("div"); msg.id = "bigNextMsg"; msg.className = "bigmsg";
  const next = document.createElement("button"); next.id = "bigNextBtn"; next.textContent = "Next ▶";
  const close = document.createElement("button"); close.id = "bigNextClose"; close.textContent = "✕";
  next.addEventListener("click", () => { hideBigNext(); showMenu(); });
  close.addEventListener("click", hideBigNext);
  card.appendChild(msg); card.appendChild(next); card.appendChild(close);
  wrap.appendChild(card);
  wrap.style.display = "none";
  document.body.appendChild(wrap);
  bigNextEl = wrap; bigNextMsgEl = msg;
  return wrap;
}
function showBigNext(msgText, speakText) {
  const ov = ensureBigNext();
  if (bigNextMsgEl) bigNextMsgEl.textContent = msgText;
  ov.style.display = "flex";
  speak(speakText || msgText);
}
function hideBigNext() { if (bigNextEl) bigNextEl.style.display = "none"; }
// ---------- confetti (self-written canvas, no external assets) ----------
function spawnConfetti(n) {
  try {
    const cv = document.createElement("canvas");
    cv.id = "confettiCanvas";
    cv.style.position = "fixed"; cv.style.inset = "0"; cv.style.width = "100%"; cv.style.height = "100%";
    cv.style.pointerEvents = "none"; cv.style.zIndex = "99";
    cv.width = 800; cv.height = 600;
    document.body.appendChild(cv);
    const ctx = cv.getContext && cv.getContext("2d");
    const colors = ["#e74c3c","#f1c40f","#2ecc71","#3498db","#9b59b6"];
    const parts = Array.from({ length: n || 40 }, (_, i) => ({
      x: Math.random() * 800, y: -20 - Math.random() * 200, vx: (Math.random() - 0.5) * 2,
      vy: 2 + Math.random() * 3, s: 5 + Math.random() * 6, c: colors[i % colors.length], r: Math.random() * 3 }));
    const t0 = Date.now();
    const frame = () => {
      if (ctx) { ctx.clearRect(0, 0, 800, 600);
        for (const p of parts) { p.x += p.vx; p.y += p.vy; p.vy += 0.05; p.r += 0.1;
          ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.r); ctx.fillStyle = p.c; ctx.fillRect(-p.s/2, -p.s/2, p.s, p.s * 0.6); ctx.restore(); } }
      if (Date.now() - t0 < 2500) { if (typeof requestAnimationFrame !== "undefined") requestAnimationFrame(frame); else setTimeout(frame, 30); }
      else cv.remove();
    };
    frame();
    setTimeout(() => { try { cv.remove(); } catch (_) {} }, 2600);
  } catch (_) {}
}
// ---------- points / levels ----------
function awardPoints(n, why) {
  const before = levelFor(dossier.points);
  dossier.points += n; saveDossier(); renderDossier();
  const after = levelFor(dossier.points);
  if (after > before) {
    coachLine("Level up! You are level " + after + "!", { speak: false });
    speak("Level up! You are level " + after + "!");
    spawnConfetti(40);
  }
  return dossier.points;
}
// ---------- annotations overlay ----------
const ANN_COLORS = { green: "rgba(46,204,113,", yellow: "rgba(241,196,15,", red: "rgba(231,76,60," };
function annXY(sq) { // display coords (flip-aware), viewBox 800x800, 100px squares
  const f = "abcdefgh".indexOf(sq[0]), r = Number(sq[1]) - 1; // r: 0 = rank1
  const flip = (typeof flipped !== "undefined" && flipped);
  return flip ? { x: (7 - f) * 100, y: r * 100 } : { x: f * 100, y: (7 - r) * 100 };
}
function drawAnnotations(ann) {
  const svg = $("annotSvg"); if (!svg) return;
  if (!ann) { svg.innerHTML = ""; return; }
  const col = (c, a) => (ANN_COLORS[c] || ANN_COLORS.green) + a + ")";
  let out = "<defs>";
  for (const c of Object.keys(ANN_COLORS))
    out += '<marker id="ah-' + c + '" markerWidth="6" markerHeight="6" refX="4" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="' + col(c, ".8") + '"/></marker>';
  out += "</defs>";
  for (const hgt of ann.highlights || []) {
    const sq = typeof hgt === "string" ? hgt : hgt.square, c = (typeof hgt === "object" && hgt.color) || "green";
    if (!sq) continue; const { x, y } = annXY(sq);
    out += '<rect x="' + x + '" y="' + y + '" width="100" height="100" fill="' + col(c, ".55") + '"/>';
  }
  for (const ar of ann.arrows || []) {
    const from = ar.from || ar[0], to = ar.to || ar[1], c = ar.color || "green";
    if (!from || !to) continue;
    const a = annXY(from), b = annXY(to);
    out += '<line x1="' + (a.x + 50) + '" y1="' + (a.y + 50) + '" x2="' + (b.x + 50) + '" y2="' + (b.y + 50) +
           '" stroke="' + col(c, ".8") + '" stroke-width="14" marker-end="url(#ah-' + c + ')"/>';
  }
  svg.innerHTML = out;
}
function clearAnnotations() { const svg = $("annotSvg"); if (svg) svg.innerHTML = ""; }
// ---------- pickup reporting ----------
function currentFen() { try { return C.fenFromState(replayState()); } catch (_) { return ""; } }
async function sendPickup(sqIdxNum) {
  pickupPending = null;
  const st = replayState();
  const piece = st.board[sqIdxNum];
  if (!piece || piece.c !== "w") return;
  const fen = C.fenFromState(st);
  const square = C.sqName(sqIdxNum);
  const key = gameId + "|" + fen + "|" + square;
  if (reportedPickups.has(key)) return;
  reportedPickups.add(key);
  clearAnnotations(); // new pickup sent clears old annotations
  const targets = C.legalMovesC(st.board, sqIdxNum, st.castling, st.ep).map((m) => C.sqName(m.to));
  try {
    if (connectionPromise) { const p = connectionPromise; connectionPromise = null; try { await p; } catch (_) {} }
    if (!sessionToken) return;
    let resp;
    const t0 = Date.now();
    try {
      const r = await fetch(RELAY_URL + "/v1/pickup", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": "Bearer " + sessionToken },
        body: JSON.stringify({ game_id: gameId, fen, piece: piece.t.toUpperCase(), square, targets }),
      });
      if (!r.ok) { diag("DIAG PICKUP " + r.status + " " + (Date.now() - t0) + "ms"); return; }
      resp = await r.json();
    } catch (_) { diag("DIAG PICKUP FAIL neterr"); return; }
    if (resp && resp.speak === true && resp.line) {
      coachLine("Coach: " + resp.line); // coachLine speaks Coach: lines
      if (resp.annotations) drawAnnotations(resp.annotations);
    }
  } catch (_) { /* response handling error -> no UI change */ }
}
function pickupSelectionTick() {
  let sel = -1, pc = null;
  try { sel = selected; if (sel >= 0) pc = board[sel]; } catch (_) { return; }
  const active = (gameActive || lessonActive) && !gameOver;
  if (sel !== lastSelectedSeen) {
    const prev = lastSelectedSeen; lastSelectedSeen = sel;
    if (pickupTimer) { clearTimeout(pickupTimer); pickupTimer = null; }
    if (active && sel >= 0 && pc && pc.c === "w") {
      pickupPending = sel;
      pickupTimer = setTimeout(() => { if (pickupPending === sel) sendPickup(sel); }, 1500);
    } else if (pickupPending !== null && sel < 0) {
      // put-down without a move (deselect, same position): send immediately
      const pend = pickupPending; pickupPending = null; sendPickup(pend);
    } else pickupPending = null;
  }
}
// ---------- page state setters (lessons / undo) ----------
function setPageFromState(st, sans, captured) {
  board = st.board.map((p) => (p ? { t: p.t, c: p.c } : null));
  turn = st.turn; castling = { ...st.castling }; epSquare = st.ep;
  halfmove = st.half; fullmove = st.full;
  history.length = 0; for (const s2 of sans) history.push(s2);
  capturedBy = captured || { w: [], b: [] };
  gameOver = false; lastMoveSq = null; pendingAnim = null;
  select(-1); render();
}
function capturedFromSans(baseSt, sans) {
  const st = C.cloneState(baseSt); const cap = { w: [], b: [] };
  for (const san of sans) {
    const m = C.parseSan(st, san); if (!m) break;
    const captured = C.applyMoveState(st, m, m.promoChoice || null);
    if (captured) cap[m ? (sans.indexOf(san) % 2 === 0 ? "w" : "b") : "w"].push(captured.t);
  }
  // mover alternates from the base turn; rebuild precisely:
  const st2 = C.cloneState(baseSt); const cap2 = { w: [], b: [] };
  for (const san of sans) {
    const m = C.parseSan(st2, san); if (!m) break;
    const mover = st2.turn; const captured = C.applyMoveState(st2, m, m.promoChoice || null);
    if (captured) cap2[mover].push(captured.t);
  }
  return cap2;
}
function startLesson(id) {
  const les = lessonById(id); if (!les) return;
  hideBigNext();
  reset();
  currentLesson = les; lessonBaseFen = les.fen; lessonActive = true; gameActive = false;
  gameOver = false; lessonHeroCaps = 0; undoPendingRetry = false;
  const st = stateFromFen(les.fen); lessonPrevState = C.cloneState(st);
  setPageFromState(st, [], { w: [], b: [] });
  lastPlySeen = 0;
  gameId = "lesson-" + id + "-" + Date.now().toString(36);
  sessionRecord = { startedAt: new Date().toISOString(), branch: BRANCH, mode: "lesson", gameId, alerts: [], diag: [], moves: [], offline: false };
  const km = $("kidsMenu"); if (km) km.style.display = "none";
  updateGameInfo();
  coachLine(les.title + " — " + les.goalText);
  setCoachState("");
  connectionPromise = prepareConnection();
  // introduce the hero piece with an immediate pickup report
  const heroSq = st.board.findIndex((p) => p && p.c === "w" && p.t === (les.hero || "q"));
  if (heroSq >= 0) sendPickup(heroSq);
}
function checkLessonProgress() {
  if (!lessonActive || !currentLesson) return;
  const st = replayState();
  // count hero captures from the latest ply
  if (lessonPrevState && history.length) {
    const lastSan = history[history.length - 1];
    const m = C.parseSan(lessonPrevState, lastSan);
    if (m) {
      const wasCapture = !!lessonPrevState.board[m.to] || m.epCapture;
      if (wasCapture && (!currentLesson.hero || (lessonPrevState.board[m.from] && lessonPrevState.board[m.from].t === currentLesson.hero)))
        lessonHeroCaps++;
    }
  }
  lessonPrevState = C.cloneState(st);
  // hand the move back to the kid: page turn flips back to White, and a
  // page-side "game over" (Black has no moves) must not block the lesson
  try { turn = "w"; gameOver = false; render(); } catch (_) {}
  let done = false;
  try { done = currentLesson.check(st, lessonHeroCaps); } catch (_) {}
  if (!done) return;
  lessonActive = false;
  const firstTime = !dossier.lessons[currentLesson.id];
  dossier.lessons[currentLesson.id] = true; saveDossier();
  if (firstTime) awardPoints(50, "lesson complete");
  spawnConfetti(40);
  coachLine("You did it! You finished " + currentLesson.title + "! ⭐");
  showBigNext("You did it! ⭐", "You did it! You finished " + currentLesson.title + "! Tap Next!");
  renderDossier();
  const b = $("coachBody");
  if (b) { const btn = document.createElement("button"); btn.textContent = "🏠 Back to Menu";
    btn.addEventListener("click", showMenu); b.appendChild(btn); }
}
function showMenu() {
  hideBigNext();
  lessonActive = false;
  updateGameInfo();
  renderMenu();
  const km = $("kidsMenu"); if (km) km.style.display = "";
}
function renderMenu() {
  const pl = $("pointsLine");
  if (pl) pl.textContent = "Points: " + dossier.points + " • Level " + levelFor(dossier.points);
  for (const id of LESSON_IDS) {
    const btn = $("lessonBtn-" + id); if (!btn) continue;
    const les = lessonById(id);
    btn.textContent = les.title + (dossier.lessons[id] ? " ✅" : "");
  }
  const unlocked = LESSON_IDS.every((id) => dossier.lessons[id]);
  const nb = $("newGameBtn");
  if (nb) { nb.disabled = !unlocked; nb.classList.toggle("locked", !unlocked); }
  const uh = $("unlockHint");
  if (uh) uh.textContent = unlocked ? "You unlocked real games! 🏆" : "Finish all 8 lessons to unlock!";
}
// ---------- undo ----------
function undoMove() {
  clearAnnotations();
  if (lessonActive && currentLesson) { // lessons: reset to the start position
    const st = stateFromFen(currentLesson.fen);
    lessonHeroCaps = 0; lessonPrevState = C.cloneState(st);
    setPageFromState(st, [], { w: [], b: [] });
    lastPlySeen = 0;
    coachLine("Lesson restarted — try again!");
    return;
  }
  if (!gameActive || coachBusy) return; // ignore while a coach reply is in flight
  if (!history.length) return;
  const keep = history.length % 2 === 0 ? history.slice(0, -2) : history.slice(0, -1);
  const base = C.startState();
  const st = C.stateFromSans(keep.slice());
  setPageFromState(st, keep, capturedFromSans(base, keep));
  lastPlySeen = history.length;
  gameOver = false; undoPendingRetry = true;
  coachLine("Undo! Your move again.");
}
// ---------- gentle candidate set for real games ----------
// Implemented with the sf-adapter's MultiPV analyze() (the same path the
// adult silent scorer uses): best move + every move within a wide cp
// window of best, window/depth shrink as the kid's level rises.
const GENTLE_TABLE = [[4, 400], [6, 300], [8, 250], [10, 200], [12, 150]];
function lineScoreKids(l) {
  if (l.mate !== null && l.mate !== undefined) return l.mate > 0 ? 100000 - l.mate * 10 : -100000 - l.mate * 10;
  return l.cp || 0;
}
async function gentleCandidates(st, fen) {
  const lvl = Math.min(levelFor(dossier.points), 5);
  const [depth, win] = GENTLE_TABLE[lvl - 1];
  let lines = [];
  try { lines = (await sf.analyze(fen, 10, depth)).lines || []; } catch (_) {}
  const legal = C.allLegalState(st, st.turn);
  const byUci = new Map(legal.map((m) => [C.uciFor(m), m]));
  const scored = lines.filter((l) => byUci.has(l.uci)).map((l) => ({ uci: l.uci, score: lineScoreKids(l) }));
  let candidates = [];
  if (scored.length) {
    const best = Math.max(...scored.map((l) => l.score));
    candidates = scored.filter((l) => best - l.score <= win).slice(0, 10)
      .map((l) => { const m = byUci.get(l.uci); return { san: C.sanWithSuffix(st, m, m.promo ? "q" : null), uci: l.uci }; });
  }
  if (!candidates.length && legal.length) { // engine unavailable: legal-move fallback via core pruner
    candidates = C.pruneCandidates(st, [], 850);
    if (!candidates.length) { const m = legal[0]; candidates = [{ san: C.sanWithSuffix(st, m, null), uci: C.uciFor(m) }]; }
  }
  return { lines, candidates };
}

// ---------- wiring ----------
function poll() {
  pickupSelectionTick();
  if (history.length !== lastPlySeen) {
    const grew = history.length > lastPlySeen;
    lastPlySeen = history.length;
    // a move ON THE BOARD clears annotations: the kid's own moves (odd
    // history length after the ply, or any lesson move) — not the coach
    // ply that may have just delivered fresh annotations
    if (grew && (lessonActive || history.length % 2 === 1)) clearAnnotations();
    if (lessonActive) { checkLessonProgress(); return; }
    if (grew && undoPendingRetry && gameActive && gameId && !dossier.undoRetryPaid[gameId]) {
      dossier.undoRetryPaid[gameId] = true; undoPendingRetry = false;
      awardPoints(5, "retry after undo");
    }
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
    const nb = $("newGameBtn"); if (nb) nb.addEventListener("click", () => { if (!nb.disabled) startGame("kids"); });
    const hb = $("hintBtn"); if (hb) hb.addEventListener("click", onHint);
    const mb = $("menuBtn"); if (mb) mb.addEventListener("click", showMenu);
    const ub = $("undoBtn"); if (ub) ub.addEventListener("click", undoMove);
    const mub = $("muteBtn"); if (mub) { mub.textContent = dossier.muted ? "🔇" : "🔊";
      mub.addEventListener("click", () => { dossier.muted = !dossier.muted; saveDossier(); mub.textContent = dossier.muted ? "🔇" : "🔊"; }); }
    for (const id of LESSON_IDS) { const lb = $("lessonBtn-" + id); if (lb) lb.addEventListener("click", () => startLesson(id)); }
    initVoicePicker();
    updateGameInfo();
    renderMenu();
    if (pendingLevelUp) { coachLine("Level up! You are level " + pendingLevelUp + "!", { speak: false }); speak("Level up! You are level " + pendingLevelUp + "!"); pendingLevelUp = 0; }
    const gate = $("gate");
    if (gate) {
      if (loadStoredToken()) gate.style.display = "none";
      const gb = $("gateBtn"); if (gb) gb.addEventListener("click", () => { tryGate(); });
      const gi = $("gateInput"); if (gi) gi.addEventListener("keydown", (e) => { if (e.key === "Enter") tryGate(); });
      const ob = $("gateOfflineBtn"); if (ob) ob.addEventListener("click", () => enterOfflineFromGate());
    }
  }
  sf.start(SF_URL).then(() => setCoachState("Coach is ready. Start a new game when you are."))
    .catch(() => { diag("DIAG SF FAIL"); setCoachState("The analysis engine did not load — games need it for move candidates."); });
  setInterval(poll, 300);
}
return { init, startGame, coachTurn, handleCoachResponse, tryGate, startLesson, undoMove, showMenu,
  drawAnnotations, clearAnnotations, speak, spawnConfetti, showBigNext, hideBigNext, pickVoice, voiceScore, _test: {
  getDossier: () => dossier, getScoreLog: () => scoreLog, getSession: () => sessionRecord,
  getTarget: () => targetElo, setScoreLog: (s) => { scoreLog = s; },
  getOffline: () => offlineMode, getGameId: () => gameId, hasToken: () => !!sessionToken,
  getDiag: () => diagEntries.map((e) => e.line),
  getLesson: () => currentLesson, isLessonActive: () => lessonActive, levelFor,
  gentleCandidates, awardPoints, LESSONS, stateFromFen,
  finishGame, replayState } };
})();
if (typeof window !== "undefined" && !window.__coachManualInit)
  window.addEventListener("DOMContentLoaded", () => CoachUI.init());
if (typeof module !== "undefined" && module.exports) module.exports = CoachUI;
