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
// ---------- accounts (Ticket 006 Phase 2a) ----------
// DUAL-MODE: signed OUT, this page behaves exactly as it always has —
// branch password at the gate, local profiles, local games wallet.
// Signed IN (Options → Account), profiles and the games counter come
// from the gate's account store, and each game opens an account
// session against the active server profile instead of a branch
// session. The account token lives in sessionStorage only.
const ACCOUNT_KEY = "chessCoachAccount." + BRANCH;
let accountState = null; // {token, exp, email, plan, guest?, guest_days_left?, guest_expires_at?}
try {
  const rawAcct = sessionStorage.getItem(ACCOUNT_KEY);
  // Guests (Phase 4 temp accounts) have no email; the token + guest
  // flag is what restores them (e.g. arriving from the plans page).
  if (rawAcct) { const d = JSON.parse(rawAcct); if (d && d.token && (d.email || d.guest)) accountState = d; }
} catch (_) {}
let serverCaps = null;     // last caps view from the gate (signed in only)
// Phase 3: plan display names for the Options account block. The
// account holder manages billing; the names stay plain (no signage
// about who a plan is "for").
const PLAN_NAMES = { coach: "Coach", pro: "Pro", byok_weekly: "BYOK", lapsed: "Paused", none: "No plan" };
function planName(id) { return PLAN_NAMES[id] || "Coach"; }
let acctBillingNote = "";  // last billing action's plain-language result
let acctCoachSeat = null;  // seat of the current account game ("sol"|"astra"|"kids"|"byok"), from /v1/account/session
let byokState = null;      // BYOK summary from the gate (never the key itself)
let byokModels = null;     // curated model lists from the gate
let pendingCharge = false; // the next account session spends a game
function signedIn() { return !!accountState; }
// ---------- local profiles (Ticket 006 Phase 1) ----------
// Profiles are LOCAL this phase: a per-branch profile list in
// localStorage; each profile's dossier lives under its own key (the
// seeded default profile keeps the legacy key, so existing progress
// is untouched). Modes are per-page this phase (this page is
// Standard); the merged shell is Phase 2. The games wallet is
// account-level (shared by every profile on this branch).
const MODE_LABEL = "Standard";
const DEFAULT_PROFILE_NAME = { you: "You", ben: "Ben", test: "Test" }[BRANCH] || "Player";
const PROFILES_KEY = "chessCoachProfiles." + BRANCH;
const SERVER_PROFILES_KEY = "chessCoachServerProfiles." + BRANCH;
// Signed in, the profile list is the server's; it is cached under its
// own key so the signed-out local list is never overwritten.
function profilesStorageKey() { return signedIn() ? SERVER_PROFILES_KEY : PROFILES_KEY; }
function profileDossierKey(id) {
  return id === "default" ? "chessCoachDossier." + BRANCH
                          : "chessCoachDossier." + BRANCH + "." + id;
}
function loadProfilesState() {
  let s = null;
  try { s = JSON.parse(localStorage.getItem(profilesStorageKey()) || "null"); } catch (_) {}
  if (!s || !Array.isArray(s.profiles) || !s.profiles.length)
    s = { activeId: "default", profiles: [{ id: "default", name: DEFAULT_PROFILE_NAME, mode: MODE_LABEL, coach: "sol" }] };
  if (!s.profiles.some((p) => p.id === s.activeId)) s.activeId = s.profiles[0].id;
  return s;
}
function saveProfilesState() { try { localStorage.setItem(profilesStorageKey(), JSON.stringify(profilesState)); } catch (_) {} }
let profilesState = loadProfilesState();
let activeProfileId = profilesState.activeId;
let DOSSIER_KEY = profileDossierKey(activeProfileId);
function activeProfile() { return profilesState.profiles.find((p) => p.id === activeProfileId) || profilesState.profiles[0]; }
function renderProfiles() {
  const p = activeProfile(); if (!p) return;
  const chip = $("profileChip");
  if (chip) chip.textContent = (p.name || "P").slice(0, 1).toUpperCase() + " " + p.name;
  const sel = $("optProfileSelect");
  if (sel) {
    sel.innerHTML = "";
    for (const pr of profilesState.profiles) {
      const o = document.createElement("option");
      o.value = pr.id; o.textContent = pr.name + " · " + (pr.mode || MODE_LABEL);
      sel.appendChild(o);
    }
    sel.value = activeProfileId;
  }
  const nm = $("optProfileName"); if (nm) nm.value = p.name;
  const mt = $("optModeTag"); if (mt) mt.textContent = p.mode || MODE_LABEL;
  const pv = $("optPrivacyLine"); if (pv) pv.textContent = p.name + "'s profile stores: display name only";
}
function openOptions() { renderProfiles(); const d = $("optionsDrawer"); if (d) d.style.display = "flex"; }
function closeOptions() { const d = $("optionsDrawer"); if (d) d.style.display = "none"; }
function saveCurrentGameRecord() {
  try { localStorage.setItem("chessCoachPaused." + BRANCH + "." + activeProfileId,
    JSON.stringify({ history: history.slice(), mode, targetElo, at: new Date().toISOString(), why: "profile switch" })); } catch (_) {}
}
function switchProfile(id) {
  if (!id || id === activeProfileId) { renderProfiles(); return; }
  if (gameActive && !gameOver) {
    const target = profilesState.profiles.find((p) => p.id === id);
    const okc = (typeof confirm === "function")
      ? confirm("Switch to " + (target ? target.name : "the other profile") + "? Your current game is saved.") : true;
    if (!okc) { renderProfiles(); return; }
    saveCurrentGameRecord();
  }
  saveDossier();
  activeProfileId = id; profilesState.activeId = id; saveProfilesState();
  DOSSIER_KEY = profileDossierKey(id);
  dossier = loadDossier();
  gameActive = false;
  reset();
  renderDossier(); renderProfiles(); renderWallet();
  if (signedIn()) {
    acctApi("/v1/profiles/switch", { method: "POST", headers: acctAuthHeaders(),
      body: JSON.stringify({ profile_id: id }) }).catch(() => {});
  }
  closeOptions();
}
function addProfile() {
  if (signedIn()) { addProfileSignedIn(); return; }
  const p = { id: "p" + Date.now().toString(36), name: "Player " + (profilesState.profiles.length + 1), mode: MODE_LABEL, coach: "sol" };
  profilesState.profiles.push(p); saveProfilesState();
  switchProfile(p.id);
}
async function addProfileSignedIn() {
  try {
    const made = await acctApi("/v1/profiles", { method: "POST", headers: acctAuthHeaders(),
      body: JSON.stringify({ name: "Player " + (profilesState.profiles.length + 1), mode: MODE_LABEL }) });
    profilesState.profiles = made.profiles.map((p) => ({ id: p.id, name: p.name, mode: p.mode, coach: p.coach === "astra" ? "astra" : "sol" }));
    saveProfilesState();
    switchProfile(made.profile.id);
  } catch (_) { /* stay on the current profile; a later sync repairs the list */ }
}
function deleteProfile() {
  if (profilesState.profiles.length <= 1) return;
  const okc = (typeof confirm === "function")
    ? confirm("Delete this profile? Its progress on this device is removed.") : true;
  if (!okc) return;
  if (signedIn()) { deleteProfileSignedIn(); return; }
  try { localStorage.removeItem(profileDossierKey(activeProfileId)); } catch (_) {}
  profilesState.profiles = profilesState.profiles.filter((p) => p.id !== activeProfileId);
  activeProfileId = profilesState.profiles[0].id; profilesState.activeId = activeProfileId;
  saveProfilesState();
  DOSSIER_KEY = profileDossierKey(activeProfileId);
  dossier = loadDossier();
  gameActive = false;
  reset();
  renderDossier(); renderProfiles(); renderWallet();
  closeOptions();
}
async function deleteProfileSignedIn() {
  const victim = activeProfileId;
  try {
    const data = await acctApi("/v1/profiles/delete", { method: "POST", headers: acctAuthHeaders(),
      body: JSON.stringify({ profile_id: victim }) });
    try { localStorage.removeItem(profileDossierKey(victim)); } catch (_) {}
    profilesState.profiles = data.profiles.map((p) => ({ id: p.id, name: p.name, mode: p.mode, coach: p.coach === "astra" ? "astra" : "sol" }));
    activeProfileId = data.active_profile_id || (profilesState.profiles[0] && profilesState.profiles[0].id);
    profilesState.activeId = activeProfileId;
    saveProfilesState();
    DOSSIER_KEY = profileDossierKey(activeProfileId);
    dossier = loadDossier();
    gameActive = false;
    reset();
    renderDossier(); renderProfiles(); renderWallet();
    closeOptions();
  } catch (_) { /* keep the profile locally on failure */ }
}
function lockDevice() {
  sessionToken = null;
  try { sessionStorage.removeItem(TOKEN_KEY); } catch (_) {}
  closeOptions();
  const gate = $("gate"); if (gate) gate.style.display = "";
}
function clickEl(el) {
  if (!el) return;
  if (typeof el.click === "function") { el.click(); return; }
  for (const f of (el.listeners && el.listeners.click) || []) f.call(el);
}
// ---------- games wallet (local counters; server caps engine is Phase 2) ----------
const WALLET_KEY = "chessCoachWallet." + BRANCH;
const DAILY_NEW = 3, SAVE_CAP = 5, READY_CAP = 8;
function todayStr() { const d = new Date(); return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"); }
function saveWallet(w) { try { localStorage.setItem(WALLET_KEY, JSON.stringify(w)); } catch (_) {} }
function loadWallet() {
  let w = null;
  try { w = JSON.parse(localStorage.getItem(WALLET_KEY) || "null"); } catch (_) {}
  if (!w || typeof w !== "object") w = { day: todayStr(), credited: DAILY_NEW, used: 0, saved: 0 };
  if (w.day !== todayStr()) { // a new day: unspent games roll into the saved pile
    const leftover = Math.max(0, (w.credited || 0) - (w.used || 0));
    w.saved = Math.min(SAVE_CAP, (w.saved || 0) + leftover);
    w.credited = DAILY_NEW; w.used = 0; w.day = todayStr();
    saveWallet(w);
  }
  return w;
}
function gamesLeft() {
  if (signedIn() && serverCaps) return serverCaps.left; // server caps engine (Phase 2a)
  const w = loadWallet(); return Math.max(0, Math.min(READY_CAP, (w.saved || 0) + ((w.credited || 0) - (w.used || 0))));
}
function fmtNextCredit() {
  if (!serverCaps || !serverCaps.next_credit_at) return "midnight";
  try {
    return new Date(serverCaps.next_credit_at).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  } catch (_) { return "midnight"; }
}
function walletBreakdown() { const w = loadWallet(); return { todayNew: Math.max(0, (w.credited || 0) - (w.used || 0)), saved: w.saved || 0, left: gamesLeft() }; }
function consumeGame() {
  const w = loadWallet();
  if (gamesLeft() <= 0) return false;
  if ((w.used || 0) < (w.credited || 0)) w.used = (w.used || 0) + 1; else w.saved = (w.saved || 0) - 1;
  saveWallet(w); renderWallet();
  return true;
}
function renderWallet() {
  if (signedIn() && serverCaps) {
    const chipS = $("gamesChip"), clS = $("gameCostLine"), giS = $("gamesInfo"), nbS = $("newGameBtn");
    if (serverCaps.unlimited) {
      // BYOK posture (Phase 3): games run on the account's own key —
      // no daily counter at all. (Key handling itself is Phase 4.)
      if (chipS) chipS.textContent = "∞ your key";
      if (clS) clS.textContent = !dossier.calibrated ? "First game is calibration · free" : "Your key · no daily limit";
      if (nbS) nbS.disabled = false;
      if (giS) giS.textContent = "Games on this account run on your own key — no daily limit. " +
        "Platform safety limits still apply. · Shared by this account.";
      return;
    }
    const left = serverCaps.left;
    const noPlan = (serverCaps.daily_credit || 0) === 0;
    if (chipS) chipS.textContent = left + " games";
    if (clS) clS.textContent = noPlan
      ? (!dossier.calibrated ? "First game is calibration · free" : "No plan right now — lessons are still free")
      : !dossier.calibrated ? "First game is calibration · free"
      : left > 0 ? "Uses 1 game · " + left + " left" : "No games left — more arrive at " + fmtNextCredit() + ".";
    if (nbS) nbS.disabled = dossier.calibrated ? left <= 0 : false;
    if (giS) giS.textContent = noPlan
      ? "No active plan on this account right now. Lessons are still free, always."
      : "Today: " + serverCaps.today_new + " new · Saved: " + serverCaps.saved +
        " · Ready: up to " + serverCaps.ready_cap + " · Next " + serverCaps.daily_credit + " at " +
        fmtNextCredit() + " · Shared by this account.";
    return;
  }
  const left = gamesLeft();
  const chip = $("gamesChip"); if (chip) chip.textContent = left + " games";
  const cl = $("gameCostLine");
  if (cl) cl.textContent = !dossier.calibrated ? "First game is calibration · free"
    : left > 0 ? "Uses 1 game · " + left + " left" : "Next games arrive at midnight.";
  const nb = $("newGameBtn"); if (nb) nb.disabled = dossier.calibrated ? left <= 0 : false;
  const gi = $("gamesInfo");
  if (gi) { const b = walletBreakdown();
    gi.textContent = "Today: " + b.todayNew + " new · Saved: " + b.saved + " · Ready: up to " + READY_CAP +
                     " · Next " + DAILY_NEW + " at midnight · Shared by this account."; }
}
function updateGameInfo() {
  const t = $("gameInfoTitle"); if (t) t.textContent = "You vs. the Coach (" + (acctCoachSeat === "astra" ? "Astra" : acctCoachSeat === "byok" ? "your model" : "Sol") + ")";
  const k = $("gameInfoKind");
  if (k) k.textContent = mode === "practice" ? "Calibration game" : mode === "rated" ? "Rated game"
    : (dossier.calibrated ? "Rated game" : "Calibration game");
  const p = $("gameInfoProfile"); if (p) { const pr = activeProfile(); p.textContent = pr ? pr.name : ""; }
}
let coachLineCount = 0;


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
    const raw = localStorage.getItem(DOSSIER_KEY);
    if (raw) return JSON.parse(raw);
  } catch (_) {}
  return { elo: 800, calibrated: false, games: 0, eloHistory: [800], openings: {},
           mistake_patterns: [], weak_phases: [], focus_lesson: "", focus_class: "", lastResult: "" };
}
function saveDossier() { try { localStorage.setItem(DOSSIER_KEY, JSON.stringify(dossier)); } catch (_) {} }
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
  coachLineCount++;
  const tg = $("coachHistToggle"); if (tg) tg.textContent = "Coach history (" + coachLineCount + ")";
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
  const pb = $("practiceBtn"); if (pb) pb.style.display = dossier.calibrated ? "none" : "";
  updateGameInfo();
  renderWallet();
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
// ---------- accounts: API + sign-in state (Phase 2a) ----------
async function acctApi(path, opts) {
  const r = await fetch(RELAY_URL + path, opts || {});
  let data = null;
  try { data = await r.json(); } catch (_) {}
  if (!r.ok) { const e = new Error("account HTTP " + r.status); e.status = r.status; e.data = data; throw e; }
  return data;
}
function acctAuthHeaders() { return { "Content-Type": "application/json", "Authorization": "Bearer " + accountState.token }; }
function storeAccount() { try { sessionStorage.setItem(ACCOUNT_KEY, JSON.stringify(accountState)); } catch (_) {} }
function clearAccount() {
  accountState = null; serverCaps = null; acctBillingNote = ""; acctCoachSeat = null;
  byokState = null; byokModels = null;
  try { sessionStorage.removeItem(ACCOUNT_KEY); } catch (_) {}
}
// Phase 4: one adoption path for every way an account session
// arrives — password, passkey, test-code redemption, guest claim.
// The gate's payload is the same shape for all of them.
function adoptAccount(data) {
  const a = data.account || {};
  accountState = { token: data.token, exp: data.exp, email: a.email || null, plan: a.plan,
    guest: !!a.guest, guest_days_left: (typeof a.guest_days_left === "number" ? a.guest_days_left : null),
    guest_expires_at: a.guest_expires_at || null };
  storeAccount();
  serverCaps = data.caps || null;
}
async function refreshCaps() {
  if (!accountState) return;
  try { serverCaps = await acctApi("/v1/games", { headers: acctAuthHeaders() }); renderWallet(); }
  catch (_) { /* keep the last known numbers */ }
}
async function requestAccountSession(gid, charge) {
  const data = await acctApi("/v1/account/session", {
    method: "POST", headers: acctAuthHeaders(),
    body: JSON.stringify({ profile_id: activeProfileId, game_id: gid, charge: !!charge }),
  });
  if (data.caps) { serverCaps = data.caps; renderWallet(); }
  if (typeof data.coach_seat === "string") { acctCoachSeat = data.coach_seat; updateGameInfo(); }
  storeToken(data.token, data.exp, gid);
  return data;
}
function onAccountNoGames() {
  // Race-only backstop: the pre-start check uses the same server
  // numbers, so a 409 here means another tab spent the last game.
  if (signedIn() && serverCaps && (serverCaps.daily_credit || 0) === 0) {
    coachLine("This account has no plan right now — lessons are still free.");
    setCoachState("No plan right now.");
  } else {
    coachLine("That's all the games for today — more arrive at " + fmtNextCredit() + ".");
    setCoachState("No games left today.");
  }
  gameActive = false;
}
async function syncProfilesOnSignIn(serverProfiles, activeId) {
  let list = Array.isArray(serverProfiles) ? serverProfiles.slice() : [];
  if (!list.length) {
    // First sign-in on this account: lift this device's local
    // profiles up to the server, carrying each profile's on-device
    // progress over to its new dossier key.
    for (const lp of profilesState.profiles) {
      try {
        const made = await acctApi("/v1/profiles", { method: "POST", headers: acctAuthHeaders(),
          body: JSON.stringify({ name: lp.name, mode: lp.mode || MODE_LABEL, coach: lp.coach === "astra" ? "astra" : "sol" }) });
        try {
          const rawD = localStorage.getItem(profileDossierKey(lp.id));
          if (rawD && !localStorage.getItem(profileDossierKey(made.profile.id)))
            localStorage.setItem(profileDossierKey(made.profile.id), rawD);
        } catch (_) {}
        list.push(made.profile);
      } catch (_) {}
    }
  }
  if (!list.length) list = [{ id: "default", name: DEFAULT_PROFILE_NAME, mode: MODE_LABEL }];
  const keep = list.some((p) => p.id === activeProfileId) ? activeProfileId
    : (activeId && list.some((p) => p.id === activeId) ? activeId : list[0].id);
  profilesState = { activeId: keep, profiles: list.map((p) => ({ id: p.id, name: p.name, mode: p.mode, coach: p.coach === "astra" ? "astra" : "sol" })) };
  activeProfileId = keep;
  saveProfilesState();
  DOSSIER_KEY = profileDossierKey(keep);
  dossier = loadDossier();
  gameActive = false;
  renderDossier(); renderProfiles(); renderWallet();
}
async function accountAuth(kind) { // "login" | "signup"
  const em = $("optAcctEmail"), pw = $("optAcctPw"), msg = $("optAcctMsg");
  const email = em ? String(em.value || "").trim() : "";
  const password = pw ? String(pw.value || "") : "";
  if (!email || !password) { if (msg) msg.textContent = "Enter an email and a password."; return; }
  if (msg) msg.textContent = "Checking…";
  try {
    const data = await acctApi(kind === "signup" ? "/v1/signup" : "/v1/login", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    adoptAccount(data);
    await syncProfilesOnSignIn(data.profiles || [], data.active_profile_id);
    if (msg) msg.textContent = "";
    if (pw) pw.value = "";
    await refreshPasskeys();
    renderAccount(); renderWallet();
  } catch (e) {
    if (msg) msg.textContent = e && e.status === 401 ? "Wrong email or password."
      : e && e.status === 409 ? "That email already has an account — sign in instead."
      : e && e.status === 400 ? "Use a valid email and a password of 8+ characters."
      : "Can't reach the coach relay right now.";
  }
}
async function accountSignOut() {
  try { await acctApi("/v1/logout", { method: "POST", headers: acctAuthHeaders() }); } catch (_) {}
  clearAccount();
  passkeyList = [];
  profilesState = loadProfilesState(); // signed out again -> the local list
  activeProfileId = profilesState.activeId;
  DOSSIER_KEY = profileDossierKey(activeProfileId);
  dossier = loadDossier();
  gameActive = false;
  reset();
  renderDossier(); renderProfiles(); renderWallet(); renderAccount();
  closeOptions();
}
// ---------- passkeys (Ticket 006 Phase 2b) ----------
// WebAuthn on top of the Phase 2a accounts: the gate holds the
// credentials, the password stays as the fallback, and a passkey
// sign-in lands in exactly the same session state as a password
// sign-in. Everything here feature-detects: no WebAuthn, no buttons,
// just the fallback note.
function waSupported() {
  try {
    return typeof navigator !== "undefined" && !!navigator.credentials &&
      typeof navigator.credentials.create === "function" &&
      typeof navigator.credentials.get === "function" &&
      typeof window !== "undefined" && !!window.PublicKeyCredential;
  } catch (_) { return false; }
}
function b64uEncode(buf) {
  const bytes = new Uint8Array(buf);
  let s = "";
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}
function b64uDecode(str) {
  let s = String(str).replace(/-/g, "+").replace(/_/g, "/");
  while (s.length % 4) s += "=";
  const bin = atob(s);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out.buffer;
}
let passkeyList = [];
function renderPasskeys() {
  const list = $("optPasskeyList");
  if (list) {
    list.textContent = "";
    if (!passkeyList.length) list.textContent = "None yet";
    for (const pk of passkeyList) {
      const span = document.createElement("span");
      const when = pk.created_at ? String(pk.created_at).slice(0, 10) : "";
      span.textContent = "Passkey" + (when ? " · added " + when : "") + " ";
      const btn = document.createElement("button");
      btn.type = "button"; btn.className = "ghost"; btn.textContent = "Remove";
      btn.addEventListener("click", () => { removePasskey(pk.id); });
      span.appendChild(btn);
      list.appendChild(span);
    }
  }
  const mg = $("optPasskeyManage");
  if (mg) mg.style.display = accountState && waSupported() ? "" : "none";
}
async function refreshPasskeys() {
  if (!accountState) { passkeyList = []; renderPasskeys(); return; }
  try {
    const data = await acctApi("/v1/passkeys", { headers: acctAuthHeaders() });
    passkeyList = Array.isArray(data.passkeys) ? data.passkeys : [];
  } catch (_) { /* keep the last known list */ }
  renderPasskeys();
}
async function addPasskey() {
  const msg = $("optAcctMsg");
  if (!accountState) return;
  if (!waSupported()) { if (msg) msg.textContent = "Passkeys aren't available in this browser."; return; }
  if (msg) msg.textContent = "Follow your device's prompt to save a passkey…";
  try {
    const opts = await acctApi("/v1/passkeys/register/options", { method: "POST", headers: acctAuthHeaders(), body: "{}" });
    const cred = await navigator.credentials.create({ publicKey: {
      challenge: b64uDecode(opts.challenge),
      rp: opts.rp,
      user: { id: b64uDecode(opts.user.id), name: opts.user.name, displayName: opts.user.displayName },
      pubKeyCredParams: opts.pubKeyCredParams,
      timeout: opts.timeout,
      attestation: opts.attestation,
      authenticatorSelection: opts.authenticatorSelection,
      excludeCredentials: (opts.excludeCredentials || []).map((c) => ({ type: c.type, id: b64uDecode(c.id), transports: c.transports })),
    } });
    if (!cred) throw new Error("no credential");
    const data = await acctApi("/v1/passkeys/register/verify", { method: "POST", headers: acctAuthHeaders(), body: JSON.stringify({
      id: cred.id, rawId: b64uEncode(cred.rawId), type: cred.type,
      response: { clientDataJSON: b64uEncode(cred.response.clientDataJSON),
                  attestationObject: b64uEncode(cred.response.attestationObject) },
      transports: (cred.response.getTransports ? cred.response.getTransports() : []),
    }) });
    passkeyList = Array.isArray(data.passkeys) ? data.passkeys : passkeyList;
    renderPasskeys();
    if (msg) msg.textContent = "Passkey added.";
  } catch (e) {
    if (msg) msg.textContent = e && e.status ? "The relay couldn't add that passkey — try again."
      : "Passkey setup was cancelled or didn't finish.";
  }
}
async function removePasskey(credId) {
  const msg = $("optAcctMsg");
  try {
    const data = await acctApi("/v1/passkeys/remove", { method: "POST", headers: acctAuthHeaders(),
      body: JSON.stringify({ credential_id: credId }) });
    passkeyList = Array.isArray(data.passkeys) ? data.passkeys : [];
    renderPasskeys();
    if (msg) msg.textContent = "Passkey removed.";
  } catch (_) { if (msg) msg.textContent = "Couldn't remove that passkey — try again."; }
}
async function passkeySignIn() {
  const em = $("optAcctEmail"), msg = $("optAcctMsg");
  if (!waSupported()) { if (msg) msg.textContent = "Passkeys aren't available in this browser."; return; }
  const email = em ? String(em.value || "").trim() : "";
  if (msg) msg.textContent = "Waiting for your passkey…";
  try {
    const opts = await acctApi("/v1/passkeys/auth/options", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(email ? { email } : {}) });
    const cred = await navigator.credentials.get({ publicKey: {
      challenge: b64uDecode(opts.challenge),
      rpId: opts.rpId,
      timeout: opts.timeout,
      userVerification: opts.userVerification,
      allowCredentials: (opts.allowCredentials || []).map((c) => ({ type: c.type, id: b64uDecode(c.id), transports: c.transports })),
    } });
    if (!cred) throw new Error("no credential");
    const data = await acctApi("/v1/passkeys/auth/verify", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({
      id: cred.id, rawId: b64uEncode(cred.rawId), type: cred.type,
      response: { clientDataJSON: b64uEncode(cred.response.clientDataJSON),
                  authenticatorData: b64uEncode(cred.response.authenticatorData),
                  signature: b64uEncode(cred.response.signature),
                  userHandle: cred.response.userHandle ? b64uEncode(cred.response.userHandle) : null },
    }) });
    adoptAccount(data);
    await syncProfilesOnSignIn(data.profiles || [], data.active_profile_id);
    if (msg) msg.textContent = "";
    await refreshPasskeys();
    renderAccount(); renderWallet();
  } catch (e) {
    if (msg) msg.textContent = e && e.status === 401 ? "That passkey didn't sign you in."
      : e && e.status === 429 ? "Too many tries — wait a bit and try again."
      : "Passkey sign-in was cancelled or didn't finish.";
  }
}
async function bootAccountSync() {
  // A tab that restored a signed-in account re-reads the server's
  // profile list + caps; a dead token quietly reverts to local mode.
  try {
    const data = await acctApi("/v1/profiles", { headers: acctAuthHeaders() });
    serverCaps = data.caps || serverCaps;
    if (Array.isArray(data.profiles) && data.profiles.length) {
      profilesState = { activeId: data.active_profile_id || data.profiles[0].id,
        profiles: data.profiles.map((p) => ({ id: p.id, name: p.name, mode: p.mode, coach: p.coach === "astra" ? "astra" : "sol" })) };
      if (!profilesState.profiles.some((p) => p.id === profilesState.activeId))
        profilesState.activeId = profilesState.profiles[0].id;
      activeProfileId = profilesState.activeId;
      saveProfilesState();
      DOSSIER_KEY = profileDossierKey(activeProfileId);
      dossier = loadDossier();
      renderDossier(); renderProfiles(); renderWallet();
    }
    // Phase 4: refresh the guest countdown from the account record
    // (the stored blob's days-left is only as fresh as sign-in).
    try {
      const me = await acctApi("/v1/account", { headers: acctAuthHeaders() });
      if (me && accountState) {
        accountState.guest = !!me.guest;
        accountState.guest_days_left = (typeof me.guest_days_left === "number" ? me.guest_days_left : null);
        accountState.guest_expires_at = me.guest_expires_at || null;
        storeAccount();
      }
    } catch (_) {}
    renderAccount();
  } catch (e) {
    if (e && e.status === 401) {
      clearAccount();
      profilesState = loadProfilesState();
      activeProfileId = profilesState.activeId;
      DOSSIER_KEY = profileDossierKey(activeProfileId);
      dossier = loadDossier();
      renderDossier(); renderProfiles(); renderWallet(); renderAccount();
    }
  }
}
const PLAN_LINE_SIGNED_OUT = "Plan: Beta — accounts and billing arrive with the full launch.";
function guestDaysText() {
  const n = accountState && typeof accountState.guest_days_left === "number" ? accountState.guest_days_left : null;
  if (n === null) return "";
  return n <= 0 ? "last day" : n === 1 ? "1 day left" : n + " days left";
}
function renderAccount() {
  const line = $("optAccountLine");
  if (line) line.textContent = !accountState ? "Not signed in"
    : accountState.guest ? "Test account — " + guestDaysText()
    : "Signed in as " + accountState.email;
  const form = $("optAcctForm"); if (form) form.style.display = accountState ? "none" : "";
  const so = $("optSignOutBtn"); if (so) so.style.display = accountState ? "" : "none";
  const pl = $("optPlanLine");
  if (pl) pl.textContent = !accountState ? PLAN_LINE_SIGNED_OUT
    : accountState.guest ? "Plan: " + planName(accountState.plan) + " (test code) · " + guestDaysText()
    : "Plan: " + planName(accountState.plan) + " · " + accountState.email;
  const mb = $("optManageBilling"); if (mb) mb.style.display = accountState && !accountState.guest ? "" : "none";
  const bn = $("optBillingNote"); if (bn) bn.textContent = acctBillingNote;
  // Phase 4 guest surfaces: the banner over the board and the claim
  // form in this drawer. Both exist only while the account is a guest.
  const banner = $("guestBanner");
  if (banner) {
    banner.style.display = accountState && accountState.guest ? "" : "none";
    const bt = $("guestBannerText");
    if (bt && accountState && accountState.guest)
      bt.textContent = "You're on a test account — " + guestDaysText() + ". Keep your progress to make it yours.";
  }
  const claim = $("optGuestClaim"); if (claim) claim.style.display = accountState && accountState.guest ? "" : "none";
  const gd = $("optGuestDays"); if (gd) gd.textContent = accountState && accountState.guest ? guestDaysText() : "";
  renderCoachPicker();
  refreshByok();
  // Phase 2b: passkey controls appear only when this browser can do
  // WebAuthn; otherwise one plain line explains why, and the password
  // form carries on alone.
  const supported = waSupported();
  const note = $("optPasskeyNote");
  if (note) note.textContent = supported ? "" : "Passkeys aren't available in this browser — your password still works.";
  const psb = $("optPasskeySignInBtn"); if (psb) psb.style.display = supported ? "" : "none";
  renderPasskeys();
}
// ---------- Phase 3: per-profile coach picker (Pro) + billing ----------
// The picker shows ONLY on a Pro account, for a Standard profile —
// the gate still enforces the rule (seat resolution is server-side);
// this is presentation. No rating copy anywhere near it (UI pass c7).
function renderCoachPicker() {
  const row = $("optCoachRow"); if (!row) return;
  const p = activeProfile();
  const isPro = !!(accountState && accountState.plan === "pro");
  const show = !!(p && p.mode !== "New Player" && isPro);
  row.style.display = show ? "" : "none";
  const note = $("optCoachNote");
  if (note) note.textContent = (!show && accountState && p && p.mode !== "New Player" && !isPro)
    ? "The Pro plan adds a second coach (Astra) for this profile." : "";
  if (!show) return;
  const sol = $("optCoachSolBtn"), ast = $("optCoachAstraBtn");
  if (sol) sol.classList.toggle("sel", p.coach !== "astra");
  if (ast) ast.classList.toggle("sel", p.coach === "astra");
}
function setProfileCoach(which) {
  const p = activeProfile(); if (!p || !signedIn()) return;
  p.coach = which; saveProfilesState(); renderCoachPicker();
  acctApi("/v1/profiles/update", { method: "POST", headers: acctAuthHeaders(),
    body: JSON.stringify({ profile_id: p.id, coach: which }) }).catch(() => {});
}
async function manageBilling() {
  try {
    const data = await acctApi("/v1/billing/portal", { method: "POST", headers: acctAuthHeaders(), body: "{}" });
    if (data && data.url) {
      if (typeof window !== "undefined" && typeof window.open === "function") window.open(data.url, "_blank");
      acctBillingNote = "Billing opened in a new tab.";
    }
  } catch (e) {
    acctBillingNote = e && e.status === 503 ? "Billing isn't open yet — it arrives with the full launch."
      : e && e.status === 409 ? "No billing account yet — billing starts with your first plan."
      : "Billing didn't open just now — try again in a bit.";
  }
  renderAccount();
}
// ---------- Phase 4: BYOK key + test-code redemption + guest claim ----------
// The key field is write-only in both directions: the page sends a
// key once and never reads one back; the gate answers with a summary
// (provider, model, last-4 tail, added date) and nothing more.
const BYOK_MODELS_FALLBACK = {
  openai: [{ id: "gpt-6-sol", label: "GPT-6 Sol" }, { id: "gpt-6-luna", label: "GPT-6 Luna" }],
  anthropic: [{ id: "claude-opus-5-5", label: "Claude Opus 5.5" }, { id: "claude-sonnet-5", label: "Claude Sonnet 5" }],
};
function byokNote(text) { const n = $("optByokNote"); if (n) n.textContent = text; }
function renderByok() {
  const state = $("optByokState");
  if (state) state.textContent = byokState
    ? "····" + String(byokState.tail || "").replace(/^·+/, "") + " · added " + String(byokState.added_at || "").slice(0, 10)
    : "No key saved";
  const rm = $("optByokRemoveBtn"); if (rm) rm.style.display = byokState ? "" : "none";
  const prov = $("optByokProvider");
  const model = $("optByokModel");
  if (prov && byokState && byokState.provider) prov.value = byokState.provider;
  if (prov && !prov.value) prov.value = "openai"; // the picker's first option, stated explicitly
  if (model) {
    const lists = byokModels || BYOK_MODELS_FALLBACK;
    const list = lists[prov ? prov.value : "openai"] || [];
    model.innerHTML = "";
    for (const m of list) {
      const o = document.createElement("option");
      o.value = m.id; o.textContent = m.label || m.id;
      model.appendChild(o);
    }
    if (byokState && byokState.model && list.some((m) => m.id === byokState.model)) model.value = byokState.model;
    else if (!list.some((m) => m.id === model.value)) model.value = list.length ? list[0].id : "";
  }
}
async function refreshByok() {
  if (!accountState) { byokState = null; renderByok(); return; }
  try {
    const data = await acctApi("/v1/byok", { headers: acctAuthHeaders() });
    byokState = data.byok || null;
    if (data.models) byokModels = data.models;
  } catch (_) { /* keep the last known summary */ }
  renderByok();
}
async function saveByokKey() {
  const prov = $("optByokProvider"), model = $("optByokModel"), keyEl = $("optByokKey");
  const key = keyEl ? String(keyEl.value || "").trim() : "";
  if (!accountState) { byokNote("Sign in first — the key is stored on your account."); return; }
  if (!key) { byokNote("Paste your key first — the field is never filled back in for you."); return; }
  byokNote("Saving…");
  try {
    const data = await acctApi("/v1/byok", { method: "POST", headers: acctAuthHeaders(),
      body: JSON.stringify({ provider: prov ? prov.value : "openai", model: model ? model.value : "", key }) });
    byokState = data.byok || null;
    if (keyEl) keyEl.value = "";
    renderByok();
    byokNote("Key saved. Your games now run on your own model — they don't use your plan's games.");
    refreshCaps();
  } catch (e) {
    byokNote(e && e.status === 400 ? "That key or model pick didn't look right — check and try again."
      : "Couldn't save the key just now — try again in a bit.");
  }
}
async function testByokKey() {
  if (!accountState || !byokState) { byokNote("Save a key first, then test it."); return; }
  byokNote("Testing — one small call to your provider…");
  try {
    const data = await acctApi("/v1/byok/test", { method: "POST", headers: acctAuthHeaders(), body: "{}" });
    byokNote(data && data.ok ? "Your key works — " + byokState.provider + " answered."
      : "Your provider rejected that key. Check it on your provider account, then save it again.");
  } catch (_) { byokNote("Couldn't reach your provider just now — try again in a bit."); }
}
async function removeByokKey() {
  if (!accountState) return;
  try {
    await acctApi("/v1/byok/remove", { method: "POST", headers: acctAuthHeaders(), body: "{}" });
    byokState = null;
    renderByok();
    byokNote("Key removed. Your games use your plan again.");
    refreshCaps();
  } catch (_) { byokNote("Couldn't remove the key just now — try again in a bit."); }
}
async function redeemTestCode() {
  const codeEl = $("optRedeemCode"), msg = $("optAcctMsg");
  const code = codeEl ? String(codeEl.value || "").trim() : "";
  if (!code) { if (msg) msg.textContent = "Enter your test code first."; return; }
  if (msg) msg.textContent = "Checking your code…";
  try {
    const data = await acctApi("/v1/redeem", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code }) });
    adoptAccount(data);
    await syncProfilesOnSignIn(data.profiles || [], data.active_profile_id);
    if (codeEl) codeEl.value = "";
    if (msg) msg.textContent = "You're in — this test account lasts 7 days. Use “Keep my progress” any time to make it yours.";
    renderAccount(); renderWallet();
  } catch (e) {
    if (msg) msg.textContent = e && e.status === 401 ? "That code wasn't recognized — check it and try again."
      : e && e.status === 429 ? "Too many tries — wait a bit and try again."
      : "Can't reach the coach relay right now.";
  }
}
async function claimGuestAccount() {
  const em = $("optClaimEmail"), pw = $("optClaimPw"), msg = $("optClaimMsg");
  const email = em ? String(em.value || "").trim() : "";
  const password = pw ? String(pw.value || "") : "";
  if (!email || !password) { if (msg) msg.textContent = "Enter an email and a password."; return; }
  if (msg) msg.textContent = "Saving your account…";
  try {
    const data = await acctApi("/v1/guest/claim", { method: "POST", headers: acctAuthHeaders(),
      body: JSON.stringify({ email, password }) });
    adoptAccount(data);
    if (pw) pw.value = "";
    if (msg) msg.textContent = "";
    const note = $("optAcctMsg");
    if (note) note.textContent = "Done — this account is yours now, progress and all.";
    renderAccount(); renderWallet();
  } catch (e) {
    if (msg) msg.textContent = e && e.status === 409 ? "That email already has an account — sign in with it instead."
      : e && e.status === 400 ? "Use a valid email and a password of 8+ characters."
      : "Couldn't save the account just now — try again in a bit.";
  }
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
      const err = new Error("relay HTTP " + r.status); err.offline = true; err.status = r.status;
      // Phase 4 honesty: a rejected BYOK key is its own failure, not
      // a generic outage — coachTurn names it plainly.
      try { const d = await r.json(); if (d && d.error === "byok_key_rejected") err.byokRejected = true; } catch (_) {}
      throw err;
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
  if (!r.ok) {
    const err = new Error("relay HTTP " + r.status); err.status = r.status;
    try { const d = await r.json(); if (d && d.error === "byok_key_rejected") err.byokRejected = true; } catch (_) {}
    throw err;
  }
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
    if (accountState) {
      const charge = pendingCharge; pendingCharge = false;
      try { await requestAccountSession(gameId, charge); return; }
      catch (e) {
        if (e && e.data && e.data.caps) { serverCaps = e.data.caps; renderWallet(); }
        if (e && e.status === 409) { onAccountNoGames(); return; }
        if (e && e.status === 403 && e.data && e.data.guest_expired) {
          // The 7 days ran out; the claim window is still open, and
          // the drawer carries the form. Say it plainly.
          coachLine("Your test account's 7 days are up. Open Options and choose “Keep my progress” to keep playing with your coach — this game runs on Stockfish only.");
          enterOfflineMode("your test account ended");
          return;
        }
        if (!(e && e.status === 401)) { enterOfflineMode("the account session could not be opened"); return; }
        clearAccount(); renderAccount(); // dead account token: fall through to the branch session
      }
    }
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
  if (kind === "rated" && gamesLeft() <= 0) {
    if (signedIn() && serverCaps && (serverCaps.daily_credit || 0) === 0) {
      coachLine("This account has no plan right now — lessons are still free.");
      setCoachState("No plan right now.");
    } else {
      coachLine("That's all the games for today — next games arrive at midnight.");
      setCoachState("No games left today.");
    }
    return;
  }
  if (kind === "rated") {
    // Signed in, the server charges the account when this game's
    // account session opens (see prepareConnection) — the local
    // wallet is not touched. Signed out, the local wallet spends.
    if (signedIn()) pendingCharge = true; else consumeGame();
  }
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
  const ab = $("alertBody"); if (ab) ab.textContent = "No alerts.";
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
    else if (e && e.byokRejected && !offlineMode) {
      // The customer's own key was rejected: say exactly that, then
      // finish THIS game on Stockfish (visibly offline). The relay
      // never falls back to a platform seat behind the key's back.
      coachLine("Your API key was rejected by your provider, so your coach couldn't move. This game continues with Stockfish only — check the key in Options → Settings.");
      enterOfflineMode("your API key was rejected");
      try { await offlineCoachMove(replayState()); }
      catch (_) { pauseGame("the coach and the offline engine are both unavailable."); }
    }
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
  const hb = $("reviewByLine"); if (hb) hb.textContent = "Review by " + (acctCoachSeat === "astra" ? "Astra" : acctCoachSeat === "byok" ? "your model" : "Sol");
  const cc = $("centerCol"); if (cc && cc.appendChild) cc.appendChild(rp);
  if (rp.classList && rp.classList.add) rp.classList.add("takeover");
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
    let byokReviewRejected = false;
    try { onlineReview = await relayReview(body); }
    catch (e) { if (e && e.regate) { /* re-gate shown; local review still renders below */ } if (e && e.byokRejected) byokReviewRejected = true; onlineReview = null; }
    if (onlineReview) eloAfter = onlineReview.elo_after;
    else { eloAfter = C.eloUpdate(dossier.elo, targetElo, score); reviewNote = byokReviewRejected
      ? "Your API key was rejected by your provider, so this review was computed on this page. Check the key in Options → Settings."
      : "Relay review unavailable — this review was computed on this page."; }
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
    const fp = $("failsafePanel");
    if (fp && fp.remove) {
      let dbg = false;
      try { dbg = new URLSearchParams((window.location && window.location.search) || "").get("debug") === "1"; } catch (_) {}
      if (!dbg) fp.remove();
    }
    if (typeof window !== "undefined") window.__coachReset = () => {
      if (gameActive && !gameOver) {
        const okc = (typeof confirm === "function") ? confirm("Abandon this game? It still counts as used.") : true;
        if (!okc) return;
      }
      gameActive = false; reset(); renderDossier();
    };
    const cht = $("coachHistToggle");
    if (cht) cht.addEventListener("click", () => { const cb = $("coachBody"); if (cb) cb.style.display = cb.style.display === "none" ? "" : "none"; });
    const pc = $("profileChip"); if (pc) pc.addEventListener("click", openOptions);
    const oc = $("optionsClose"); if (oc) oc.addEventListener("click", closeOptions);
    const ps = $("optProfileSelect"); if (ps) ps.addEventListener("change", () => switchProfile(ps.value));
    const ap = $("optAddProfile"); if (ap) ap.addEventListener("click", addProfile);
    const pn = $("optProfileName"); if (pn) pn.addEventListener("change", () => { const p = activeProfile(); const v = String(pn.value || "").trim(); if (p && v) { p.name = v; saveProfilesState(); renderProfiles();
      if (signedIn()) acctApi("/v1/profiles/update", { method: "POST", headers: acctAuthHeaders(), body: JSON.stringify({ profile_id: p.id, name: v }) }).catch(() => {}); } });
    const sib = $("optSignInBtn"); if (sib) sib.addEventListener("click", () => { accountAuth("login"); });
    const sub = $("optSignUpBtn"); if (sub) sub.addEventListener("click", () => { accountAuth("signup"); });
    const sob = $("optSignOutBtn"); if (sob) sob.addEventListener("click", () => { accountSignOut(); });
    const mbb = $("optManageBilling"); if (mbb) mbb.addEventListener("click", () => { manageBilling(); });
    const csb = $("optCoachSolBtn"); if (csb) csb.addEventListener("click", () => { setProfileCoach("sol"); });
    const cab = $("optCoachAstraBtn"); if (cab) cab.addEventListener("click", () => { setProfileCoach("astra"); });
    const pkb = $("optPasskeySignInBtn"); if (pkb) pkb.addEventListener("click", () => { passkeySignIn(); });
    const apb = $("optAddPasskeyBtn"); if (apb) apb.addEventListener("click", () => { addPasskey(); });
    const rdb = $("optRedeemBtn"); if (rdb) rdb.addEventListener("click", () => { redeemTestCode(); });
    const clb = $("optClaimBtn"); if (clb) clb.addEventListener("click", () => { claimGuestAccount(); });
    const gkb = $("guestKeepBtn"); if (gkb) gkb.addEventListener("click", () => { openOptions(); });
    const bsv = $("optByokSaveBtn"); if (bsv) bsv.addEventListener("click", () => { saveByokKey(); });
    const bte = $("optByokTestBtn"); if (bte) bte.addEventListener("click", () => { testByokKey(); });
    const brm = $("optByokRemoveBtn"); if (brm) brm.addEventListener("click", () => { removeByokKey(); });
    const bpv = $("optByokProvider"); if (bpv) bpv.addEventListener("change", () => { renderByok(); });
    renderAccount();
    if (accountState) { bootAccountSync(); refreshPasskeys(); }
    const dp = $("optDeleteProfile"); if (dp) dp.addEventListener("click", deleteProfile);
    const lk = $("optLockBtn"); if (lk) lk.addEventListener("click", lockDevice);
    const rc = $("optRecalibrate"); if (rc) rc.addEventListener("click", () => { closeOptions(); startGame("practice"); });
    const osb = $("optSoundBtn"); if (osb) osb.addEventListener("click", () => { clickEl($("soundBtn")); const sb2 = $("soundBtn"); if (sb2) osb.textContent = sb2.textContent; });
    const gc = $("gamesChip"); if (gc) gc.addEventListener("click", () => { const gi = $("gamesInfo"); if (gi) { renderWallet(); gi.style.display = gi.style.display === "none" ? "" : "none"; } });
    renderProfiles();
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
  finishGame, replayState,
  getWallet: () => loadWallet(), gamesLeft, renderWallet,
  getProfiles: () => profilesState, getActiveProfileId: () => activeProfileId,
  switchProfile, addProfile,
  getAccount: () => accountState, getServerCaps: () => serverCaps,
  accountAuth, accountSignOut, signedIn,
  passkeySignIn, addPasskey, removePasskey, waSupported,
  getPasskeys: () => passkeyList,
  getAcctPlan: () => (accountState ? accountState.plan : null), getAcctCoachSeat: () => acctCoachSeat,
  getBillingNote: () => acctBillingNote,
  getByok: () => byokState } };
})();
if (typeof window !== "undefined" && !window.__coachManualInit)
  window.addEventListener("DOMContentLoaded", () => CoachUI.init());
if (typeof module !== "undefined" && module.exports) module.exports = CoachUI;
