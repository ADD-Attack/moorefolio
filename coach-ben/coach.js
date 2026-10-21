// coach.js — Chess Coach page controller (Ticket 004 beta).
// Hooks the v1.1 board page by polling its move history (the single
// source of truth) and driving coach turns through the relay.
// The coach (LLM via relay) picks its own moves from a Stockfish-
// pruned candidate list; this file validates every move (failsafe),
// scores silently, calibrates, reviews, and remembers (dossier).
"use strict";
const CoachUI = (() => {
const C = CoachCore;
const BRANCH = (typeof window !== "undefined" && window.COACH_BRANCH) || "you";
const GATE_WORD = (typeof window !== "undefined" && window.COACH_GATE) || "brick-beta";
const RELAY_URL = (typeof window !== "undefined" && window.COACH_RELAY) || "http://127.0.0.1:18901";
const SF_URL = (typeof window !== "undefined" && window.COACH_SF_URL) || "stockfish/stockfish-19-lite-single.js";
const PRUNE_DEPTH = 10, SCORE_DEPTH = 10;
const PLAYER = "w", COACH = "b";

let sf = SF;                 // injectable for tests
let responder = null;        // injectable for tests; default = relay fetch
let dossier = loadDossier();
let mode = null;             // 'practice' | 'rated'
let targetElo = 800, gameStartElo = dossier.elo;
let lastPlySeen = 0, coachBusy = false, paused = false, gameActive = false;
let scoreLog = [], evalTrail = [], lastEval = null, stepMarks = 0;
let sessionRecord = null, currentCandidates = [], currentLines = [];
let hintDetail = null;

function $(id) { return document.getElementById(id); }
function loadDossier() {
  try {
    const raw = localStorage.getItem("chessCoachDossier." + BRANCH);
    if (raw) return JSON.parse(raw);
  } catch (_) {}
  return { elo: 800, calibrated: false, games: 0, eloHistory: [800], openings: {},
           mistake_patterns: [], weak_phases: [], focus_lesson: "", focus_class: "", lastResult: "" };
}
function saveDossier() { try { localStorage.setItem("chessCoachDossier." + BRANCH, JSON.stringify(dossier)); } catch (_) {} }
function dossierSummary() {
  return { elo: dossier.elo, games: dossier.games, openings: dossier.openings,
           mistake_patterns: dossier.mistake_patterns, weak_phases: dossier.weak_phases,
           focus_lesson: dossier.focus_lesson };
}
function replayState() { return C.stateFromSans(history.slice()); }
function coachLine(html) {
  const b = $("coachBody"); if (!b) return;
  const stateEl = $("coachState"); if (stateEl) stateEl.remove();
  const p = document.createElement("p"); p.className = "cline"; p.innerHTML = html;
  b.appendChild(p); b.scrollTop = b.scrollHeight;
}
function setCoachState(text) {
  const b = $("coachBody"); if (!b) return;
  let s = $("coachState");
  if (!s) { s = document.createElement("span"); s.id = "coachState"; s.className = "coachstate"; b.appendChild(s); }
  s.textContent = text;
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
  b.innerHTML =
    "Elo: <b>" + dossier.elo + "</b>" + (dossier.calibrated ? "" : " (provisional — play a practice game)") + "<br>" +
    "Games vs coach: " + dossier.games + "<br>" +
    (dossier.lastResult ? "Last game: " + dossier.lastResult + "<br>" : "") +
    (dossier.focus_lesson ? "Focus lesson: " + dossier.focus_lesson + "<br>" : "") +
    (dossier.mistake_patterns.length ? "Patterns seen: " + dossier.mistake_patterns.join(", ") : "");
}
// ---------- relay ----------
async function relayResponder(packet, note) {
  const body = { ...packet, ...(note ? { note } : {}) };
  const ctl = typeof AbortController !== "undefined" ? new AbortController() : null;
  const timer = ctl ? setTimeout(() => ctl.abort(), 150000) : null;
  try {
    const r = await fetch(RELAY_URL + "/coach/move", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body), signal: ctl ? ctl.signal : undefined,
    });
    if (!r.ok) throw new Error("relay HTTP " + r.status);
    return await r.json();
  } finally { if (timer) clearTimeout(timer); }
}
// ---------- game flow ----------
function startGame(kind) {
  reset(); // base page reset
  scoreLog = []; evalTrail = []; lastEval = null; stepMarks = 0;
  lastPlySeen = 0; paused = false; gameActive = true; coachBusy = false;
  mode = kind;
  gameStartElo = dossier.elo;
  targetElo = kind === "practice" ? 800 : dossier.elo + 50;
  sessionRecord = { startedAt: new Date().toISOString(), branch: BRANCH, mode,
                    targetStart: targetElo, alerts: [], flagged: false, moves: [] };
  $("reviewPanel").style.display = "none";
  $("alertBody").textContent = "No alerts.";
  coachLine(kind === "practice"
    ? "<b>Practice game.</b> I'll adjust my strength as we play to find your level. Good luck!"
    : "<b>New game.</b> I'm playing at about " + targetElo + " for this one. Your move.");
  setCoachState("");
  renderDossier();
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
    coachLine("<i>Calibration: I'm adjusting my target to " + targetElo + " based on how this game is going.</i>");
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
async function coachTurn() {
  if (coachBusy || paused || !gameActive || gameOver) return;
  coachBusy = true;
  setCoachState("Coach is thinking…");
  try {
    const st = replayState();
    const fen = C.fenFromState(st);
    const { lines } = await sf.analyze(fen, 10, PRUNE_DEPTH);
    currentLines = lines || [];
    currentCandidates = C.pruneCandidates(st, currentLines, targetElo);
    if (!currentCandidates.length) { pauseGame("no candidate moves available."); return; }
    const packet = { fen, san_history: history.slice(), candidates: currentCandidates,
                     target_elo: targetElo, dossier: dossierSummary(), branch: BRANCH };
    if ("cp" in (packet.candidates[0] || {}) || "score" in (packet.candidates[0] || {}))
      throw new Error("packet leak: scores present in candidates");
    const resp = await (responder || relayResponder)(packet);
    await handleCoachResponse(resp, packet, false);
  } catch (e) {
    pauseGame("the coach could not be reached (" + (e.message || e) + "). Your game is saved.");
  } finally { coachBusy = false; }
}
async function handleCoachResponse(resp, packet, isReprompt) {
  const st = replayState();
  const raw = resp && resp.move;
  const v = C.validateCoachMove(st, raw, currentCandidates);
  if (v.ok) {
    if (resp.coach_line) coachLine("<b>Coach:</b> " + escapeHtml(resp.coach_line));
    applyCoachMove(v.move);
    sessionRecord.moves.push({ ply: history.length, san: v.san, via: isReprompt ? "reprompt" : "coach" });
    return;
  }
  alertLog("FAILSAFE " + v.reason, "coach tried '" + raw + "' at " + packet.fen);
  if (!isReprompt) {
    coachLine("<i>The coach suggested a move that isn't available here — asking again.</i>");
    try {
      const resp2 = await (responder || relayResponder)(packet,
        "Your previous move '" + raw + "' was rejected: " + v.reason + ". Pick exactly one move from the candidate list.");
      await handleCoachResponse(resp2, packet, true);
    } catch (e) { pauseGame("the coach could not be reached on the retry."); }
    return;
  }
  const fb = C.fallbackCandidate(currentCandidates, currentLines);
  sessionRecord.flagged = true;
  // No third alert here: the two attempts already alerted above, and
  // the fallback is recorded in sessionRecord.moves (via:"fallback")
  // plus the flag. One alert per illegal attempt is the counting
  // rule calibration relies on.
  coachLine("<i>Coach stumbled, recovered — a move was played for the coach inside its strength band.</i>");
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
function escapeHtml(s) { const d = document.createElement("div"); d.textContent = s; return d.innerHTML; }
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
  if (hintDetail) { coachLine("<b>Hint:</b> " + escapeHtml(hintDetail)); return; }
  try {
    const st = replayState();
    const { bestmove } = await sf.analyze(C.fenFromState(st), 1, 12);
    const m = bestmove && C.parseUci(st, bestmove);
    coachLine(m ? "<b>Hint:</b> the strongest idea here is " + C.sanWithSuffix(st, m, m.promoChoice || null) + "."
                : "<b>Hint:</b> nothing forcing — develop a piece toward the center.");
  } catch (_) { coachLine("<b>Hint:</b> the scorer is unavailable right now."); }
}
// ---------- game end / review ----------
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
  let eloAfter = dossier.elo;
  if (mode === "practice") {
    eloAfter = targetElo; // the resting calibration target is the estimate (spec s.5)
    dossier.calibrated = true;
  } else if (mode === "rated") {
    eloAfter = C.eloUpdate(dossier.elo, targetElo, score);
  }
  const review = C.buildReview(scoreLog, plies, PLAYER, resultText, dossier.elo, eloAfter);
  dossier.elo = eloAfter; dossier.games++; dossier.lastResult = resultText;
  dossier.eloHistory.push(eloAfter);
  const firstTwo = history.filter((_, i) => i % 2 === 0).slice(0, 2).join(" ");
  if (firstTwo) dossier.openings[firstTwo] = (dossier.openings[firstTwo] || 0) + 1;
  if (review.focusClass && !dossier.mistake_patterns.includes(review.focusClass))
    dossier.mistake_patterns.push(review.focusClass);
  if (review.focusLesson) { dossier.focus_lesson = review.focusLesson; dossier.focus_class = review.focusClass; }
  saveDossier(); renderDossier();
  try { localStorage.removeItem("chessCoachPaused." + BRANCH); } catch (_) {}
  const rp = $("reviewPanel"), rb = $("reviewBody");
  rp.style.display = "";
  let html = "<p><b>" + resultText + "</b><br>Your Elo: " + review.eloBefore + " → <b>" + review.eloAfter + "</b>" +
             (mode === "practice" ? " (calibrated estimate)" : "") + "<br>" +
             "Average centipawn loss — you: " + (review.avgCpl.w ?? "—") + ", coach: " + (review.avgCpl.b ?? "—") + "</p>";
  if (review.moments.length) {
    html += "<p><b>Key moments</b></p><ul>" + review.moments.map((mm) =>
      "<li><b>" + mm.san + "</b> (" + (mm.mover === "w" ? "you" : "coach") + ", " + mm.reasonClass + ") — " + mm.lesson + "</li>").join("") + "</ul>";
  } else html += "<p>No big swings that game — a tight one.</p>";
  if (review.focusLesson) html += "<p><b>Focus lesson for next time:</b> " + review.focusLesson + "</p>";
  rb.innerHTML = html;
  coachLine("<b>Game over.</b> " + resultText + " Your review session is below the board.");
  if (sessionRecord) { sessionRecord.review = review; sessionRecord.finishedAt = new Date().toISOString();
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
      let open = false;
      try { open = sessionStorage.getItem("chessCoachGate." + BRANCH) === "1"; } catch (_) {}
      if (open) gate.style.display = "none";
      const tryGate = () => {
        if ($("gateInput").value === GATE_WORD) {
          gate.style.display = "none";
          try { sessionStorage.setItem("chessCoachGate." + BRANCH, "1"); } catch (_) {}
        } else $("gateMsg").textContent = "That's not it — ask Christopher.";
      };
      $("gateBtn").addEventListener("click", tryGate);
      $("gateInput").addEventListener("keydown", (e) => { if (e.key === "Enter") tryGate(); });
    }
  }
  sf.start(SF_URL).then(() => setCoachState("Coach is ready. Start a new game when you are."))
    .catch(() => setCoachState("The analysis engine did not load — the coach is paused (games need it for move candidates)."));
  setInterval(poll, 300);
}
return { init, startGame, coachTurn, handleCoachResponse, _test: {
  getDossier: () => dossier, getScoreLog: () => scoreLog, getSession: () => sessionRecord,
  getTarget: () => targetElo, setScoreLog: (s) => { scoreLog = s; },
  finishGame, replayState } };
})();
if (typeof window !== "undefined" && !window.__coachManualInit)
  window.addEventListener("DOMContentLoaded", () => CoachUI.init());
if (typeof module !== "undefined" && module.exports) module.exports = CoachUI;
