// Node harness for the Chess Coach KIDS page (Ticket 005).
// Same DOM-stub + mock-relay pattern as coach/test-gate-page.mjs; the mock
// also answers /v1/pickup, and speechSynthesis is stubbed to record utterances.
import fs from "node:fs";
import http from "node:http";
import vm from "node:vm";
import path from "node:path";
import { fileURLToPath } from "node:url";

const dir = path.dirname(fileURLToPath(import.meta.url));
const branchDir = dir;
const html = fs.readFileSync(path.join(branchDir, "index.html"), "utf8");
const inlineScripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
const TEST_PW = "mock-password-for-tests";
const LESSON_IDS = ["pawn","rook","bishop","knight","queen","king","capturing","king-safety"];
const todayStr = () => { const d = new Date(); return d.getFullYear() + "-" + String(d.getMonth()+1).padStart(2,"0") + "-" + String(d.getDate()).padStart(2,"0"); };

const ACCT_PW = "acct-pass-123";
const mock = {
  calls: { session: [], turn: [], review: [], pickup: [], health: 0, billing: [] },
  billingMode: "unconfigured", // "unconfigured" | "ok"
  passkeys: [],
  guest: false, guestExpired: false, // Phase 4 fixtures
  turnHandler: null, pickupHandler: null, healthStatus: 200,
  acct: null,
  resetAcct() {
    this.acct = {
      plan: "coach",
      profiles: [{ id: "srv-luke2", name: "Luke Two", mode: "New Player", coach: "sol" }],
      activeId: "srv-luke2", seq: 0,
      caps: { left: 3, today_new: 3, saved: 0, daily_credit: 3, ready_cap: 8,
              next_credit_at: new Date(Date.now() + 3600e3).toISOString() },
    };
    this.calls.acctAuth = []; this.calls.acctSession = [];
    this.calls.acctProfiles = []; this.calls.acctLogout = 0;
  },
  reset() { this.calls = { session: [], turn: [], review: [], pickup: [], health: 0, billing: [],
    waRegOptions: [], waRegVerify: [], waAuthOptions: [], waAuthVerify: [], waRemove: [], redeem: [], claim: [] };
    this.passkeys = []; this.turnHandler = null; this.pickupHandler = null; this.healthStatus = 200; this.billingMode = "unconfigured"; this.guest = false; this.guestExpired = false; this.resetAcct(); },
};
mock.resetAcct();
let tokenCounter = 0;
function readBody(req) { return new Promise((resolve) => { let s = ""; req.on("data", (c) => { s += c; }); req.on("end", () => { try { resolve(JSON.parse(s || "{}")); } catch (_) { resolve({}); } }); }); }
const server = http.createServer(async (req, res) => {
  const send = (status, obj) => { res.writeHead(status, { "Content-Type": "application/json" }); res.end(JSON.stringify(obj)); };
  const body = await readBody(req);
  if (req.url === "/v1/health") { mock.calls.health++; return send(mock.healthStatus, mock.healthStatus === 200 ? { ok: true, auth_mode: "password" } : { error: "health stubbed " + mock.healthStatus }); }
  if (req.url === "/v1/session") {
    mock.calls.session.push(body);
    if (body.password !== TEST_PW) return send(401, { error: "wrong password" });
    return send(200, { token: "tok-" + (++tokenCounter), exp: Math.floor(Date.now() / 1000) + 3600 });
  }
  if (req.url === "/v1/turn") {
    mock.calls.turn.push({ headers: req.headers, body });
    if (!String(req.headers.authorization || "").startsWith("Bearer tok-")) return send(401, { error: "no token" });
    const out = mock.turnHandler ? mock.turnHandler(mock.calls.turn.length, body)
                                 : { status: 200, json: { move: body.candidates[0].san, coach_line: "Mock coach move." } };
    return send(out.status, out.json || {});
  }
  if (req.url === "/v1/pickup") {
    mock.calls.pickup.push({ headers: req.headers, body });
    if (!String(req.headers.authorization || "").startsWith("Bearer tok-")) return send(401, { error: "no token" });
    const out = mock.pickupHandler ? mock.pickupHandler(mock.calls.pickup.length, body) : { status: 200, json: { speak: false } };
    return send(out.status, out.json || {});
  }
  if (req.url === "/v1/review") { mock.calls.review.push({ headers: req.headers, body }); return send(200, { elo_before: body.elo_before, elo_after: body.elo_before, review_text: "Mock review.", focus_lesson: "x" }); }
  // ---- Phase 2a account routes (mock) ----
  if (req.url === "/v1/login" || req.url === "/v1/signup") {
    mock.calls.acctAuth.push({ url: req.url, body });
    if (req.url === "/v1/signup" && body.email === "taken@example.com") return send(409, { error: "account exists" });
    if (body.password !== ACCT_PW) return send(401, { error: "unauthorized" });
    return send(200, { token: "acct-tok-1", exp: Math.floor(Date.now() / 1000) + 3600,
                       account: { email: body.email, plan: mock.acct.plan },
                       profiles: mock.acct.profiles, active_profile_id: mock.acct.activeId,
                       caps: { ...mock.acct.caps } });
  }
  if (req.url === "/v1/logout") { mock.calls.acctLogout++; return send(200, { ok: true }); }
  if (req.url === "/v1/profiles" && req.method === "GET") {
    return send(200, { profiles: mock.acct.profiles, active_profile_id: mock.acct.activeId, caps: { ...mock.acct.caps } });
  }
  if (req.url === "/v1/profiles" && req.method === "POST") {
    const p = { id: "srv-" + (++mock.acct.seq), name: body.name, mode: body.mode };
    mock.acct.profiles.push(p);
    mock.calls.acctProfiles.push({ op: "create", body });
    return send(200, { profile: p, profiles: mock.acct.profiles, active_profile_id: mock.acct.activeId, caps: { ...mock.acct.caps } });
  }
  if (req.url === "/v1/profiles/switch") { mock.acct.activeId = body.profile_id; mock.calls.acctProfiles.push({ op: "switch", body }); return send(200, { active_profile_id: mock.acct.activeId, profiles: mock.acct.profiles, caps: { ...mock.acct.caps } }); }
  if (req.url === "/v1/profiles/update") { mock.calls.acctProfiles.push({ op: "update", body }); const p = mock.acct.profiles.find((x) => x.id === body.profile_id); if (p && body.name) p.name = body.name; return send(200, { profile: p, profiles: mock.acct.profiles, active_profile_id: mock.acct.activeId, caps: { ...mock.acct.caps } }); }
  if (req.url === "/v1/profiles/delete") { mock.calls.acctProfiles.push({ op: "delete", body }); mock.acct.profiles = mock.acct.profiles.filter((x) => x.id !== body.profile_id); if (mock.acct.activeId === body.profile_id) mock.acct.activeId = mock.acct.profiles.length ? mock.acct.profiles[0].id : null; return send(200, { profiles: mock.acct.profiles, active_profile_id: mock.acct.activeId, caps: { ...mock.acct.caps } }); }
  if (req.url === "/v1/games") { return send(200, { ...mock.acct.caps }); }
  // ---- Phase 2b passkey routes (mock): shape-level only — the real
  // cryptography is proven against the real gate in test-gate.mjs ----
  if (req.url === "/v1/passkeys/register/options") {
    mock.calls.waRegOptions.push(body);
    return send(200, { challenge: "bW9jay1jaGFsbGVuZ2U", rp: { id: "moorefolio.com", name: "Chess Coach" },
                       user: { id: "bW9jay11c2Vy", name: "parent@example.com", displayName: "parent@example.com" },
                       pubKeyCredParams: [{ type: "public-key", alg: -7 }], timeout: 60000, attestation: "none",
                       authenticatorSelection: { residentKey: "preferred", userVerification: "preferred" },
                       excludeCredentials: mock.passkeys.map((p) => ({ type: "public-key", id: p.id, transports: p.transports })) });
  }
  if (req.url === "/v1/passkeys/register/verify") {
    mock.calls.waRegVerify.push(body);
    mock.passkeys.push({ id: body.id, created_at: new Date().toISOString(), last_used_at: null, transports: body.transports || [] });
    return send(200, { ok: true, passkeys: mock.passkeys });
  }
  if (req.url === "/v1/passkeys" && req.method === "GET") { return send(200, { passkeys: mock.passkeys }); }
  if (req.url === "/v1/passkeys/remove") {
    mock.calls.waRemove.push(body);
    mock.passkeys = mock.passkeys.filter((p) => p.id !== body.credential_id);
    return send(200, { ok: true, passkeys: mock.passkeys });
  }
  if (req.url === "/v1/passkeys/auth/options") {
    mock.calls.waAuthOptions.push(body);
    return send(200, { challenge: "bW9jay1jaGFsbGVuZ2U", rpId: "moorefolio.com", timeout: 60000,
                       userVerification: "preferred",
                       allowCredentials: mock.passkeys.map((p) => ({ type: "public-key", id: p.id, transports: p.transports })) });
  }
  if (req.url === "/v1/passkeys/auth/verify") {
    mock.calls.waAuthVerify.push(body);
    return send(200, { token: "acct-tok-1", exp: Math.floor(Date.now() / 1000) + 3600,
                       account: { email: "parent@example.com", plan: mock.acct.plan },
                       profiles: mock.acct.profiles, active_profile_id: mock.acct.activeId,
                       caps: { ...mock.acct.caps } });
  }
  if (req.url === "/v1/billing/portal" || req.url === "/v1/billing/checkout") {
    mock.calls.billing.push({ url: req.url, body });
    if (mock.billingMode === "unconfigured") return send(503, { error: "billing not configured yet", billing_configured: false });
    return send(200, { url: "https://billing.example.test/session" });
  }
  // ---- Phase 4 temp-account routes (mock): shape-level — the
  //      real lifecycle is proven against the real gate ----
  if (req.url === "/v1/redeem") {
    mock.calls.redeem.push(body);
    if (body.code !== "GOOD-CODE-1234") return send(401, { error: "code not recognized" });
    mock.guest = true;
    return send(200, { token: "acct-tok-guest", exp: Math.floor(Date.now() / 1000) + 3600,
                       account: { email: null, plan: "coach", guest: true, guest_days_left: 7,
                                  guest_expires_at: new Date(Date.now() + 7 * 864e5).toISOString() },
                       profiles: [{ id: "srv-guest-kid", name: "Tester", mode: "New Player", coach: "sol" }],
                       active_profile_id: "srv-guest-kid", caps: { ...mock.acct.caps } });
  }
  if (req.url === "/v1/guest/claim") {
    mock.calls.claim.push(body);
    if (!mock.guest) return send(409, { error: "not a guest account" });
    mock.guest = false;
    return send(200, { token: "acct-tok-1", exp: Math.floor(Date.now() / 1000) + 3600,
                       account: { email: body.email, plan: "coach", guest: false },
                       profiles: [{ id: "srv-guest-kid", name: "Tester", mode: "New Player", coach: "sol" }],
                       active_profile_id: "srv-guest-kid", caps: { ...mock.acct.caps } });
  }
  if (req.url === "/v1/account" && req.method === "GET") {
    return send(200, { email: mock.guest ? null : "parent@example.com", plan: mock.acct.plan,
                       guest: !!mock.guest, guest_days_left: mock.guest ? 7 : null,
                       profiles: mock.acct.profiles, active_profile_id: mock.acct.activeId,
                       caps: { ...mock.acct.caps } });
  }
  if (req.url === "/v1/account/session") {
    mock.calls.acctSession.push(body);
    if (mock.guestExpired) return send(403, { error: "guest expired", guest_expired: true });
    if (body.charge && mock.acct.caps.left <= 0) return send(409, { error: "no games left", caps: { ...mock.acct.caps } });
    if (body.charge) { mock.acct.caps.left--; mock.acct.caps.today_new--; }
    const token = "tok-acct-" + (++tokenCounter);
    return send(200, { token, exp: Math.floor(Date.now() / 1000) + 3600, caps: { ...mock.acct.caps }, charged: !!body.charge });
  }
  return send(404, { error: "unknown route" });
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const RELAY = "http://127.0.0.1:" + server.address().port;

const IDS = ["board", "boardWrap", "branchLine", "capturedByWhite", "capturedByBlack",
  "whiteName", "blackName", "turnLine", "newGameBtn", "hintBtn", "menuBtn", "undoBtn", "muteBtn",
  "resetBtn", "flipBtn", "soundBtn", "coachBody", "coachState", "coachTicker", "movesBody",
  "reviewPanel", "reviewBody", "dossierBody", "alertBody", "promoModal", "promoChoices",
  "gate", "gateInput", "gateMsg", "gateBtn", "gateOfflineBtn", "modeLine",
  "kidsMenu", "pointsLine", "unlockHint", "annotSvg",
  "gameInfoTitle", "voiceSelect", "voiceSampleBtn",
  "tickerText", "tickerReplayBtn", "gamesChip", "gamesInfo", "profileChip",
  "optionsDrawer", "optionsClose", "optProfileSelect", "optAddProfile", "optProfileName",
  "optModeTag", "optVoiceSelect", "optSpeedSelect", "optSoundBtn", "optPlanLine", "optPrivacyLine",
  "optLockBtn", "optDeleteProfile", "speedSelect", "levelBar", "levelNextLine", "gameCostLine",
  "optAccountLine", "optAcctForm", "optAcctEmail", "optAcctPw", "optSignInBtn",
  "optSignUpBtn", "optSignOutBtn", "optAcctMsg",
  "optPasskeySignInBtn", "optPasskeyManage", "optPasskeyList", "optAddPasskeyBtn", "optPasskeyNote",
  "optManageBilling", "optBillingNote",
  "guestBanner", "guestBannerText", "guestKeepBtn", "optRedeemCode", "optRedeemBtn",
  "optGuestClaim", "optGuestDays", "optClaimEmail", "optClaimPw", "optClaimBtn", "optClaimMsg",
  "optByokNpLine",
  "continueBtn", "menuSheet", "keepPlayingBtn", "saveToMenuBtn",
  "outOfGames", "outOfGamesMsg", "outOfGamesLessonBtn", "outOfGamesClose",
  ...LESSON_IDS.map((id) => "lessonBtn-" + id)];

function makeStorage() { const m = new Map(); return { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k), _map: m }; }

// A fake WebAuthn platform authenticator for the page wiring tests:
// fixed ceremony payloads with REAL ArrayBuffers, so the page's
// base64url encode/decode paths run exactly as in a browser.
function makeFakeWebAuthn() {
  const enc = (s) => new TextEncoder().encode(s).buffer;
  return {
    create: async (opts) => {
      mock.calls.waCreateOpts = opts;
      return { id: "mock-cred-1", rawId: enc("mock-cred-1"), type: "public-key",
               response: { clientDataJSON: enc("{}"), attestationObject: enc("att-obj"),
                           getTransports: () => ["internal"] },
               getClientExtensionResults: () => ({}) };
    },
    get: async (opts) => {
      mock.calls.waGetOpts = opts;
      return { id: "mock-cred-1", rawId: enc("mock-cred-1"), type: "public-key",
               response: { clientDataJSON: enc("{}"), authenticatorData: enc("auth-data"),
                           signature: enc("sig"), userHandle: null },
               getClientExtensionResults: () => ({}) };
    },
  };
}

function loadCoach(presetDossier, opts) {
  const registry = new Map();
  function makeEl(tag) {
    const el = { tag, children: [], style: {}, listeners: {}, textContent: "", value: "", scrollTop: 0, scrollHeight: 0, offsetWidth: 62, disabled: false, _cls: new Set(), _innerHTML: "", _id: "" };
    el.classList = { add: (c) => el._cls.add(c), remove: (c) => el._cls.delete(c),
      toggle: (c, force) => { const on = force === undefined ? !el._cls.has(c) : !!force; on ? el._cls.add(c) : el._cls.delete(c); },
      contains: (c) => el._cls.has(c) };
    Object.defineProperty(el, "className", { get: () => [...el._cls].join(" "), set: (v) => { el._cls = new Set(String(v).split(/\s+/).filter(Boolean)); } });
    Object.defineProperty(el, "id", { get: () => el._id, set: (v) => { el._id = v; if (v) registry.set(v, el); } });
    Object.defineProperty(el, "innerHTML", { get: () => el._innerHTML, set: (v) => { el._innerHTML = v; if (v === "") el.children = []; } });
    el.appendChild = (c) => { el.children.push(c); if (c._id) registry.set(c._id, c); return c; };
    el.remove = () => {};
    el.addEventListener = (n, f) => { (el.listeners[n] = el.listeners[n] || []).push(f); };
    el.querySelectorAll = () => []; el.querySelector = () => null;
    el.getBoundingClientRect = () => ({ left: 0, top: 0, width: 496, height: 496, right: 496, bottom: 496 });
    el.getContext = () => null;
    return el;
  }
  for (const id of IDS) { const e = makeEl("div"); e._id = id; registry.set(id, e); }
  registry.get("alertBody").textContent = "No alerts.";
  const bodyEl = makeEl("body");

  const localStorage = makeStorage();
  if (presetDossier) localStorage.setItem("chessCoachDossier.beginnertest", JSON.stringify(presetDossier));
  const sessionStorage = makeStorage();
  const utterances = [];
  const voiceObjs = (opts && opts.voices) || [];
  const speechSynthesis = { cancel: () => {}, speak: (u) => utterances.push(u),
    getVoices: () => voiceObjs, addEventListener: () => {} };
  class FakeUtterance { constructor(t) { this.text = t; } }
  let pollFn = null;
  const win = { __coachManualInit: true, _listeners: {}, location: { search: "?relay=" + encodeURIComponent(RELAY) },
                speechSynthesis, SpeechSynthesisUtterance: FakeUtterance,
                addEventListener: (n, f) => { win._listeners[n] = f; } };
  const sandbox = { console, setTimeout, clearTimeout, clearInterval: () => {},
    setInterval: (fn) => { pollFn = fn; return 1; },
    fetch: globalThis.fetch, AbortController: globalThis.AbortController, URLSearchParams: globalThis.URLSearchParams,
    atob: globalThis.atob, btoa: globalThis.btoa,
    speechSynthesis, SpeechSynthesisUtterance: FakeUtterance,
    document: { getElementById: (id) => registry.get(id) || null, createElement: (t) => makeEl(t), body: bodyEl },
    localStorage, sessionStorage, window: win };
  if (opts && opts.webauthn) {
    win.PublicKeyCredential = function PublicKeyCredential() {};
    sandbox.navigator = { credentials: opts.webauthn };
  }
  vm.createContext(sandbox);
  const run = (code) => vm.runInContext(code, sandbox);
  for (const code of inlineScripts) run(code);
  for (const f of ["coach-core.js", "sf-adapter.js", "coach.js"])
    vm.runInContext(fs.readFileSync(path.join(branchDir, f), "utf8"), sandbox, { filename: f });
  const C = run("CoachCore");
  const CoachUI = run("CoachUI");
  const fakeSf = {
    start: async () => { if (opts && opts.sfFail) throw new Error("sf load failed (stub)"); },
    analyze: async (fen, multipv) => {
      const st = CoachUI._test.replayState();
      const legal = C.allLegalState(st, st.turn);
      const PREF = ["e5", "Qh4#", "Qh4", "Nf6", "Nc6", "e6", "d5", "c5", "d6", "c6"];
      const ranked = legal.map((m) => ({ m, san: C.sanWithSuffix(st, m, m.promo ? "q" : null) }))
        .sort((a, b) => { const ia = PREF.indexOf(a.san), ib = PREF.indexOf(b.san); return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib); });
      const lines = ranked.slice(0, multipv || 10).map(({ m }) => ({ uci: C.uciFor(m), cp: 10, mate: null }));
      return { lines, bestmove: lines.length ? lines[0].uci : null };
    },
    evaluateWhite: async () => 10,
    bestmoveAtElo: async () => { const st = CoachUI._test.replayState(); const legal = C.allLegalState(st, st.turn); return legal.length ? C.uciFor(legal[0]) : null; },
  };
  CoachUI.init({ sf: fakeSf });
  return { run, C, CoachUI, fakeSf, registry, sessionStorage, localStorage, utterances, bodyEl,
           poll: () => { if (pollFn) pollFn(); }, history: () => run("history.slice()") };
}
async function pump(env, rounds = 60) { for (let i = 0; i < rounds; i++) { env.poll(); await new Promise((r) => setTimeout(r, 2)); } }
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
function playSan(env, san) {
  const st = env.CoachUI._test.replayState();
  const m = env.C.parseSan(st, san);
  if (!m) throw new Error("scripted move is not legal here: " + san);
  env.run("tryMove(" + m.from + ", " + m.to + ")");
}
async function unlock(env) {
  env.registry.get("gateInput").value = TEST_PW;
  for (const f of env.registry.get("gateBtn").listeners.click || []) await f();
  await pump(env, 10);
}
function baseDossier(over) {
  return Object.assign({ points: 0, lessons: Object.fromEntries(LESSON_IDS.map((i) => [i, false])),
    gamesPlayed: 0, gamesFinished: 0, gamesWon: 0, lastVisit: todayStr(), muted: false, undoRetryPaid: {} }, over || {});
}
function allLessonsDossier(over) { const d = baseDossier(over); for (const i of LESSON_IDS) d.lessons[i] = true; return d; }
function pickTurn(wants) {
  return (n, body) => {
    const want = wants[n - 1];
    const cand = want && body.candidates.find((c) => c.san === want || c.san.startsWith(want));
    return { status: 200, json: { move: (cand || body.candidates[0]).san, coach_line: "Mock coach move." } };
  };
}

const perTest = {}; let current = "", pass = 0, fail = 0;
function begin(name) { current = name; perTest[name] = { pass: 0, fail: 0 }; console.log("\nTEST " + name); }
function ok(label, cond, detail) { if (cond) { pass++; perTest[current].pass++; } else { fail++; perTest[current].fail++; } console.log((cond ? "PASS " : "FAIL ") + label + (detail !== undefined ? " | " + detail : "")); }

// ---------- 1 menu / unlock ----------
async function test1() {
  begin("1 menu + locked real-game button");
  ok("HTML has all 8 lesson buttons + play button + hint",
     LESSON_IDS.every((id) => html.includes('id="lessonBtn-' + id + '"')) && html.includes('id="newGameBtn"') && html.includes("Opens after the 8 lessons"));
  mock.reset();
  const env = loadCoach(baseDossier());
  const nb = env.registry.get("newGameBtn");
  ok("menu visible on load", env.registry.get("kidsMenu").style.display !== "none");
  ok("play button present and visible (not display:none)", !!nb && nb.style.display !== "none");
  ok("play button disabled + locked class with lessons incomplete", nb.disabled === true && nb.classList.contains("locked"), "disabled=" + nb.disabled);
  ok("unlock hint text shown", env.registry.get("unlockHint").textContent === "Opens after the 8 lessons, 8 to go", env.registry.get("unlockHint").textContent);
  ok("level line shows Level 1 + points-to-next-level (b7)", env.registry.get("pointsLine").textContent === "Level 1" && env.registry.get("levelNextLine").textContent === "50 points to Level 2", env.registry.get("pointsLine").textContent + " / " + env.registry.get("levelNextLine").textContent);
  const env2 = loadCoach(allLessonsDossier());
  const nb2 = env2.registry.get("newGameBtn");
  ok("play button enabled once all lessons true in dossier", nb2.disabled === false && !nb2.classList.contains("locked"), "disabled=" + nb2.disabled);
  ok("done lessons show ✅ in menu", env2.registry.get("lessonBtn-pawn").textContent.includes("✅"), env2.registry.get("lessonBtn-pawn").textContent);
}
// ---------- 2 pawn lesson completion ----------
async function test2() {
  begin("2 pawn lesson completion +50");
  mock.reset();
  const env = loadCoach(baseDossier());
  await unlock(env);
  env.CoachUI.startLesson("pawn");
  await pump(env, 20);
  ok("lesson session created with lesson game_id", /^lesson-pawn-/.test(env.CoachUI._test.getGameId() || ""), env.CoachUI._test.getGameId());
  ok("session POST used branch kids", mock.calls.session.some((s) => s.branch === "beginnertest"), JSON.stringify(mock.calls.session.map((s) => s.branch)));
  ok("hero pickup reported on lesson start", mock.calls.pickup.some((p) => p.body.piece === "P" && p.body.square === "e4"), JSON.stringify(mock.calls.pickup.map((p) => p.body)));
  playSan(env, "exd5"); await pump(env, 20);
  ok("not complete after first capture", env.CoachUI._test.getDossier().lessons.pawn === false);
  playSan(env, "dxe6"); await pump(env, 20);
  const d = env.CoachUI._test.getDossier();
  ok("pawn lesson marked done after both captures", d.lessons.pawn === true);
  ok("+50 points awarded", d.points === 50, "points=" + d.points);
  ok("dossier persisted under chessCoachDossier.beginnertest", !!env.localStorage.getItem("chessCoachDossier.beginnertest"));
}
// ---------- 3 undo in a stubbed game ----------
async function test3() {
  begin("3 undo removes kid+coach plies");
  mock.reset();
  const env = loadCoach(allLessonsDossier());
  await unlock(env);
  env.CoachUI.startGame("kids");
  playSan(env, "e4"); await pump(env);
  ok("kid+coach plies on the board", env.history().length === 2, JSON.stringify(env.history()));
  const startFen = env.C.fenFromState(env.C.startState ? env.C.startState() : env.CoachUI._test.replayState());
  env.CoachUI.undoMove();
  await pump(env, 10);
  ok("history shrank by 2", env.history().length === 0, JSON.stringify(env.history()));
  ok("board state equals the start position", env.C.fenFromState(env.CoachUI._test.replayState()) === "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", env.C.fenFromState(env.CoachUI._test.replayState()));
  // undo-retry: first kid move after the undo pays +5 once
  playSan(env, "d4"); await pump(env);
  const d = env.CoachUI._test.getDossier();
  ok("retry-after-undo paid +5 once", d.points === 5, "points=" + d.points);
}
// ---------- 4 annotations from a turn reply ----------
async function test4() {
  begin("4 annotations drawn from turn reply");
  mock.reset();
  mock.turnHandler = (n, body) => ({ status: 200, json: { move: body.candidates[0].san, coach_line: "Look here!",
    annotations: { highlights: [{ square: "e4", color: "green" }], arrows: [{ from: "e2", to: "e4", color: "red" }] } } });
  const env = loadCoach(allLessonsDossier());
  await unlock(env);
  env.CoachUI.startGame("kids");
  playSan(env, "e4"); await pump(env);
  const svg = env.registry.get("annotSvg").innerHTML;
  ok("SVG contains a rect at e4 coords (400,400)", svg.includes('<rect x="400" y="400"'), svg.slice(0, 200));
  ok("rect uses the green highlight fill", svg.includes("rgba(46,204,113,.55)"));
  ok("SVG contains an arrow line e2->e4 centers (450,650)->(450,450)", svg.includes('<line x1="450" y1="650" x2="450" y2="450"'), svg.slice(0, 300));
  ok("arrow uses red stroke + arrowhead marker", svg.includes("rgba(231,76,60,.8)") && svg.includes("marker-end"));
}
// ---------- 5 pickup debounce + dedupe ----------
async function test5() {
  begin("5 pickup debounce 1500ms + dedupe");
  mock.reset();
  const env = loadCoach(allLessonsDossier());
  await unlock(env);
  env.CoachUI.startGame("kids");
  await pump(env, 10);
  mock.calls.pickup.length = 0;
  env.run("select(62)"); // Ng1
  env.poll();
  await sleep(300);
  ok("no pickup before 1500ms elapse", mock.calls.pickup.length === 0, "calls=" + mock.calls.pickup.length);
  await sleep(1500); await pump(env, 10);
  ok("exactly ONE /v1/pickup after 1500ms", mock.calls.pickup.length === 1, "calls=" + mock.calls.pickup.length);
  if (mock.calls.pickup.length) {
    const b = mock.calls.pickup[0].body;
    ok("pickup body: piece N, square g1, targets exactly [f3,h3] from startpos",
       b.piece === "N" && b.square === "g1" && Array.isArray(b.targets) && b.targets.includes("f3") && b.targets.includes("h3") && b.targets.length === 2,
       JSON.stringify(b));
    ok("pickup body carries game_id + fen", !!b.game_id && typeof b.fen === "string");
  }
  env.run("select(-1)"); env.poll();
  env.run("select(62)"); env.poll();
  await sleep(1700); await pump(env, 10);
  ok("re-select same piece in same position sends no second pickup", mock.calls.pickup.length === 1, "calls=" + mock.calls.pickup.length);
}
// ---------- 6 points: finish +30, win +70, confetti ----------
async function test6() {
  begin("6 game finish/win points + confetti");
  mock.reset();
  mock.turnHandler = pickTurn(["e5", "Qh4#"]);
  const envL = loadCoach(allLessonsDossier());
  await unlock(envL);
  envL.CoachUI.startGame("kids");
  playSan(envL, "f3"); await pump(envL);
  playSan(envL, "g4"); await pump(envL, 80);
  let d = envL.CoachUI._test.getDossier();
  ok("Fool's-mate loss finished the game", d.gamesFinished === 1, "finished=" + d.gamesFinished);
  ok("finish pays +30 (no win bonus)", d.points === 30 && d.gamesWon === 0, "points=" + d.points);
  mock.reset();
  mock.turnHandler = pickTurn(["e5", "Nc6", "Nf6"]);
  const envW = loadCoach(allLessonsDossier());
  await unlock(envW);
  envW.CoachUI.startGame("kids");
  playSan(envW, "e4"); await pump(envW);
  playSan(envW, "Bc4"); await pump(envW);
  playSan(envW, "Qh5"); await pump(envW);
  playSan(envW, "Qxf7"); await pump(envW, 80);
  d = envW.CoachUI._test.getDossier();
  ok("Scholar's-mate win recorded", envW.run("gameOver") === true && d.gamesWon === 1, "history=" + JSON.stringify(envW.history()));
  ok("win pays +30 finish +70 win = 100", d.points === 100, "points=" + d.points);
  ok("big confetti canvas spawned on win", !!envW.registry.get("confettiCanvas"));
}
// ---------- 7 TTS ----------
async function test7() {
  begin("7 TTS speak + mute");
  mock.reset();
  const env = loadCoach(allLessonsDossier());
  await unlock(env);
  env.CoachUI.startGame("kids");
  playSan(env, "e4"); await pump(env);
  const coachUtt = env.utterances.filter((u) => String(u.text).includes("Mock coach move"));
  ok("coach line was spoken", coachUtt.length >= 1, "utterances=" + env.utterances.map((u) => u.text).join(" / "));
  ok("utterance rate is the Slow default 0.8 (b11) / pitch 1.05", coachUtt.length > 0 && coachUtt[0].rate === 0.8 && coachUtt[0].pitch === 1.05,
     coachUtt.length ? "rate=" + coachUtt[0].rate + " pitch=" + coachUtt[0].pitch : "none");
  mock.reset();
  const envM = loadCoach(allLessonsDossier({ muted: true }));
  await unlock(envM);
  envM.CoachUI.startGame("kids");
  playSan(envM, "e4"); await pump(env);
  ok("muted=true produces no utterances", envM.utterances.length === 0, "n=" + envM.utterances.length);
}

// ---------- 8 big Next overlay on lesson completion ----------
function fireClick(env, id) { for (const f of env.registry.get(id).listeners.click || []) f(); }
function collectText(el) { let t = el.textContent || ""; for (const ch of el.children || []) t += "\n" + collectText(ch); return t; }
async function test8() {
  begin("8 big Next overlay: lesson completion -> Next -> menu");
  mock.reset();
  const env = loadCoach(baseDossier());
  await unlock(env);
  env.CoachUI.startLesson("pawn");
  await pump(env, 20);
  playSan(env, "exd5"); await pump(env, 20);
  ok("no overlay before the lesson is complete", !env.registry.get("bigNextOverlay") || env.registry.get("bigNextOverlay").style.display === "none");
  playSan(env, "dxe6"); await pump(env, 20);
  const ov = env.registry.get("bigNextOverlay");
  ok("overlay appears on lesson completion", !!ov && ov.style.display === "flex", ov ? "display=" + ov.style.display : "missing");
  ok("overlay shows the big celebration text", !!env.registry.get("bigNextMsg") && env.registry.get("bigNextMsg").textContent.includes("You did it!"),
     env.registry.get("bigNextMsg") ? env.registry.get("bigNextMsg").textContent : "missing");
  ok("celebration + 'Tap Next' spoken via TTS", env.utterances.some((u) => String(u.text).includes("Tap Next")),
     env.utterances.map((u) => u.text).join(" / "));
  fireClick(env, "bigNextBtn");
  ok("Next dismisses the overlay", ov.style.display === "none", "display=" + ov.style.display);
  ok("Next returns to the menu", env.registry.get("kidsMenu").style.display !== "none");
  // the ✕ affordance: complete another lesson, close without going to menu
  env.CoachUI.startLesson("rook");
  await pump(env, 20);
  playSan(env, "Rxa5"); await pump(env, 20);
  playSan(env, "Rxe5"); await pump(env, 20);
  ok("overlay appears again for the second lesson", ov.style.display === "flex", "display=" + ov.style.display);
  fireClick(env, "bigNextClose");
  ok("✕ closes the overlay", ov.style.display === "none", "display=" + ov.style.display);
  ok("✕ does NOT force the menu open (board stays)", env.registry.get("kidsMenu").style.display === "none");
}
// ---------- 9 game-info label ----------
async function test9() {
  begin("9 game info label: no 'Human vs. Human'");
  ok("page HTML contains no 'Human vs. Human' anywhere", !html.includes("Human vs. Human"));
  mock.reset();
  const env = loadCoach(baseDossier());
  await unlock(env);
  ok("default label is 'You vs. the Coach'", env.registry.get("gameInfoTitle").textContent === "You vs. the Coach",
     env.registry.get("gameInfoTitle").textContent);
  env.CoachUI.startLesson("bishop");
  await pump(env, 10);
  ok("lesson label says the Coach is teaching", env.registry.get("gameInfoTitle").textContent === "Lesson — the Coach is teaching you",
     env.registry.get("gameInfoTitle").textContent);
  env.CoachUI.showMenu();
  ok("back at menu the label is 'You vs. the Coach' again", env.registry.get("gameInfoTitle").textContent === "You vs. the Coach",
     env.registry.get("gameInfoTitle").textContent);
  const env2 = loadCoach(allLessonsDossier());
  await unlock(env2);
  env2.CoachUI.startGame("kids");
  await pump(env2, 10);
  ok("real-game label is 'You vs. the Coach'", env2.registry.get("gameInfoTitle").textContent === "You vs. the Coach",
     env2.registry.get("gameInfoTitle").textContent);
}
// ---------- 10 voice selection ----------
async function test10() {
  begin("10 voice ranking + picker + fallback");
  mock.reset();
  const voices = [
    { name: "Microsoft David", lang: "en-US", voiceURI: "urn:david" },
    { name: "Voz Espanola", lang: "es-ES", voiceURI: "urn:es" },
    { name: "Google US English", lang: "en-US", voiceURI: "urn:google-us" },
    { name: "Samantha", lang: "en-US", voiceURI: "urn:samantha" },
  ];
  const env = loadCoach(baseDossier(), { voices });
  const picked = env.CoachUI.pickVoice();
  ok("ranking picks Google US English over David/Samantha/non-English", !!picked && picked.name === "Google US English",
     picked ? picked.name : "null");
  env.CoachUI.speak("Hello there");
  const u1 = env.utterances[env.utterances.length - 1];
  ok("utterance carries the picked voice", !!u1 && !!u1.voice && u1.voice.name === "Google US English",
     u1 && u1.voice ? u1.voice.name : "none");
  ok("picker lists every voice as an option", env.registry.get("voiceSelect").children.length === voices.length,
     "options=" + env.registry.get("voiceSelect").children.length);
  ok("picker shows the current best voice selected", env.registry.get("voiceSelect").value === "urn:google-us",
     env.registry.get("voiceSelect").value);
  // parent picks a different voice -> persisted and wins over ranking
  const sel = env.registry.get("voiceSelect");
  sel.value = "urn:samantha";
  for (const f of sel.listeners.change || []) f();
  ok("picker change persists to localStorage", env.localStorage.getItem("chessCoachVoice.beginnertest") === "urn:samantha",
     env.localStorage.getItem("chessCoachVoice.beginnertest"));
  const picked2 = env.CoachUI.pickVoice();
  ok("saved parent choice beats the ranking", !!picked2 && picked2.name === "Samantha", picked2 ? picked2.name : "null");
  fireClick(env, "voiceSampleBtn");
  const u2 = env.utterances[env.utterances.length - 1];
  ok("'Hear it' speaks the sample line with the chosen voice",
     !!u2 && String(u2.text).includes("chess coach") && !!u2.voice && u2.voice.name === "Samantha",
     u2 ? String(u2.text) : "none");
  // fallback: only a plain default voice exists
  const envD = loadCoach(baseDossier(), { voices: [{ name: "Plain Robotic", lang: "en-US", voiceURI: "urn:plain", default: true }] });
  const pd = envD.CoachUI.pickVoice();
  ok("fallback picks the lone English default voice", !!pd && pd.name === "Plain Robotic", pd ? pd.name : "null");
  envD.CoachUI.speak("Hi");
  const u3 = envD.utterances[envD.utterances.length - 1];
  ok("fallback utterance still gets that voice", !!u3 && !!u3.voice && u3.voice.name === "Plain Robotic");
  // no voices at all: sane null, speech still works voiceless
  const envN = loadCoach(baseDossier(), { voices: [] });
  ok("no voices -> pickVoice is null", envN.CoachUI.pickVoice() === null);
  envN.CoachUI.speak("Hi");
  const u4 = envN.utterances[envN.utterances.length - 1];
  ok("no voices -> utterance spoken without a voice", !!u4 && !u4.voice, u4 ? String(u4.text) : "none");
}

// ---------- 11 operator DIAG codes: errors only ----------
async function test11() {
  begin("11 DIAG codes: failures only, silent on success");
  const diagOf = (env) => env.CoachUI._test.getDiag();
  const has = (env, re) => diagOf(env).some((l) => re.test(l));

  // (a) all-success path: auth 200, health 200, turn 200, pickup speak
  // true AND false, a voice available -> ZERO diag lines anywhere.
  mock.reset();
  const voices = [{ name: "Google US English", lang: "en-US", voiceURI: "urn:g" }];
  const envOK = loadCoach(allLessonsDossier(), { voices });
  await unlock(envOK);
  envOK.CoachUI.startGame("kids");
  playSan(envOK, "e4"); await pump(envOK);
  mock.pickupHandler = () => ({ status: 200, json: { speak: true, line: "Nice pawn!" } });
  envOK.CoachUI.startLesson("pawn"); await pump(envOK, 20); // hero pickup, speak:true
  mock.pickupHandler = () => ({ status: 200, json: { speak: false } });
  envOK.CoachUI.startLesson("rook"); await pump(envOK, 20); // hero pickup, speak:false
  ok("success path emits NO diag lines", diagOf(envOK).length === 0, JSON.stringify(diagOf(envOK)));
  ok("no DIAG text in the on-screen coach log on success",
     !envOK.registry.get("coachBody").children.some((c) => String(c.textContent).includes("DIAG")));

  // (b) AUTH 401 at the gate
  mock.reset();
  const env401 = loadCoach(baseDossier());
  env401.registry.get("gateInput").value = "not-the-password";
  for (const f of env401.registry.get("gateBtn").listeners.click || []) await f();
  await pump(env401, 10); await sleep(30);
  ok("wrong password -> DIAG AUTH 401 <ms>", has(env401, /^DIAG AUTH 401 \d+ms$/), JSON.stringify(diagOf(env401)));

  // (c) HEALTH 503 at game start -> offline mode
  mock.reset(); mock.healthStatus = 503;
  const envH = loadCoach(allLessonsDossier());
  await unlock(envH);
  envH.CoachUI.startGame("kids"); await pump(envH, 10); await sleep(20);
  ok("health 503 -> DIAG HEALTH 503 <ms>", has(envH, /^DIAG HEALTH 503 \d+ms$/), JSON.stringify(diagOf(envH)));
  ok("health 503 put the game in offline mode", envH.CoachUI._test.getOffline() === true);

  // (d) HEALTH neterr (fetch rejects for /v1/health only)
  mock.reset();
  const realFetch = globalThis.fetch;
  globalThis.fetch = (u, o) => String(u).includes("/v1/health") ? Promise.reject(new Error("down")) : realFetch(u, o);
  const envHN = loadCoach(allLessonsDossier());
  globalThis.fetch = realFetch; // the sandbox already captured the stub
  await unlock(envHN);
  envHN.CoachUI.startGame("kids"); await pump(envHN, 10); await sleep(20);
  ok("health neterr -> DIAG HEALTH FAIL neterr", diagOf(envHN).includes("DIAG HEALTH FAIL neterr"), JSON.stringify(diagOf(envHN)));

  // (e) PICKUP 500 on the lesson hero pickup
  mock.reset();
  mock.pickupHandler = () => ({ status: 500, json: { error: "boom" } });
  const envP = loadCoach(baseDossier());
  await unlock(envP);
  envP.CoachUI.startLesson("pawn"); await pump(envP, 20); await sleep(20);
  ok("pickup 500 -> DIAG PICKUP 500 <ms>", has(envP, /^DIAG PICKUP 500 \d+ms$/), JSON.stringify(diagOf(envP)));

  // (f) PICKUP neterr (fetch rejects for /v1/pickup only)
  mock.reset();
  globalThis.fetch = (u, o) => String(u).includes("/v1/pickup") ? Promise.reject(new Error("down")) : realFetch(u, o);
  const envPN = loadCoach(baseDossier());
  globalThis.fetch = realFetch;
  await unlock(envPN);
  envPN.CoachUI.startLesson("pawn"); await pump(envPN, 20); await sleep(20);
  ok("pickup neterr -> DIAG PICKUP FAIL neterr", diagOf(envPN).includes("DIAG PICKUP FAIL neterr"), JSON.stringify(diagOf(envPN)));

  // (g) TURN 503 + mirror into the session record (timestamped)
  mock.reset();
  mock.turnHandler = () => ({ status: 503, json: { error: "coach down" } });
  const envT = loadCoach(allLessonsDossier());
  await unlock(envT);
  envT.CoachUI.startGame("kids");
  playSan(envT, "e4"); await pump(envT); await sleep(20);
  ok("turn 503 -> DIAG TURN 503 <ms>", has(envT, /^DIAG TURN 503 \d+ms$/), JSON.stringify(diagOf(envT)));
  const sess = envT.CoachUI._test.getSession();
  ok("failure mirrored into sessionRecord.diag with an ISO timestamp",
     !!sess && Array.isArray(sess.diag) && sess.diag.some((e) => /^DIAG TURN 503 \d+ms$/.test(e.line) && !isNaN(Date.parse(e.t))),
     sess && sess.diag ? JSON.stringify(sess.diag) : "no session diag");

  // (h) SF load failure
  mock.reset();
  const envSF = loadCoach(baseDossier(), { sfFail: true });
  await sleep(30);
  ok("SF load failure -> DIAG SF FAIL", diagOf(envSF).includes("DIAG SF FAIL"), JSON.stringify(diagOf(envSF)));

  // (i) TTS with zero voices: exactly one NONE line, however often it speaks
  mock.reset();
  const envTTS = loadCoach(baseDossier(), { voices: [] });
  envTTS.CoachUI.speak("Hello");
  envTTS.CoachUI.speak("Hello again");
  const ttsLines = diagOf(envTTS).filter((l) => l.startsWith("DIAG TTS"));
  ok("zero voices -> DIAG TTS V=0 name=NONE exactly once",
     ttsLines.length === 1 && ttsLines[0] === "DIAG TTS V=0 name=NONE", JSON.stringify(ttsLines));
}


// ---------- 12 Phase 1 (Ticket 006): New Player UI deltas ----------
async function test12() {
  begin("12 Phase 1 New Player deltas");
  // (b1) typeface + no italics on play surfaces
  ok("page loads Atkinson Hyperlegible / Lexend", html.includes("Atkinson+Hyperlegible") && html.includes("family=Lexend"));
  ok("body font stack is the new typeface at 20px/1.5", html.includes("'Atkinson Hyperlegible','Lexend'") && html.includes("font-size:20px;line-height:1.5"));
  ok("ticker is 22px and not italic", html.includes("font-size:22px;line-height:1.5") && !/#coachTicker\{[^}]*italic/.test(html));
  ok("turn line is not italic", !/#turnLine\{[^}]*italic/.test(html));
  // (b6) de-kidded copy
  ok("title is 'Chess Coach: New Player'", html.includes("<title>Chess Coach: New Player"));
  ok("menu heading is 'Let's learn chess'", html.includes("Let's learn chess") && !html.includes("Chess Coach for Kids"));
  ok("full-game button wording", html.includes("Play a full game 🏆") && !html.includes("Play a Real Game!"));
  ok("no 'grown-up' copy anywhere in the page", !/grown[- ]up/i.test(html));
  ok("adult instruments removed from the play screen (no Moves/Dossier/Failsafe panels)",
     !html.includes("<h3>Moves</h3>") && !html.includes("<h3>Your Dossier</h3>") && !html.includes("Failsafe Log"));
  ok("no Reset/Flip/Sound row in this mode", !html.includes('id="resetBtn"') && !html.includes('id="flipBtn"') && !html.includes('id="soundBtn"'));
  // (b3) undo renamed
  ok("undo button reads '↩ Try again'", html.includes("↩ Try again"));
  // (b7) level as progress
  mock.reset();
  const env = loadCoach(baseDossier({ points: 80 }));
  ok("menu shows 'Level 2' as the headline", env.registry.get("pointsLine").textContent === "Level 2",
     env.registry.get("pointsLine").textContent);
  ok("progress line counts points to the next level", env.registry.get("levelNextLine").textContent === "40 points to Level 3",
     env.registry.get("levelNextLine").textContent);
  ok("progress bar width is proportional (80 of 50..120 = 43%)", env.registry.get("levelBar").style.width === "43%",
     env.registry.get("levelBar").style.width);
  // (b6) unlock copy counts remaining lessons live
  ok("unlock hint counts lessons to go", env.registry.get("unlockHint").textContent === "Opens after the 8 lessons, 8 to go",
     env.registry.get("unlockHint").textContent);
  // (b8) annotation shape marks ride alongside colour
  env.CoachUI.drawAnnotations({ highlights: [{ square: "e4", color: "green" }, { square: "d5", color: "red" }, { square: "c3", color: "yellow" }], arrows: [] });
  const svg = env.registry.get("annotSvg").innerHTML;
  ok("green highlight carries a ✓ mark", svg.includes("✓"), svg.slice(0, 300));
  ok("red highlight carries an ✕ mark", svg.includes("✕"));
  ok("yellow highlight carries a ring", svg.includes("<circle") && svg.includes('r="30"'));
  // (b4) visible replay controls
  ok("ticker has a 44px replay button", html.includes('id="tickerReplayBtn"') && html.includes("#tickerReplayBtn{min-width:44px;min-height:44px"));
  await unlock(env);
  env.CoachUI.startLesson("pawn"); await pump(env, 20);
  const withReplay = env.registry.get("coachBody").children.filter((c) => (c.children || []).some((k) => k.className === "replayBtn"));
  ok("coach history lines carry their own replay buttons", withReplay.length >= 1, "lines=" + withReplay.length);
  // (b10) celebration overlay
  ok("celebration close target is at least 48px", html.includes("#bigNextClose") && html.includes("min-width:48px;min-height:48px"));
  ok("reduced-motion confetti path exists", typeof env.CoachUI._test.reducedMotion === "function" && env.CoachUI._test.reducedMotion() === false);
  // (b11) voice speed: Slow default, persisted, drives the rate
  ok("speed defaults to Slow (0.8) for New Player profiles", env.CoachUI._test.speedName() === "slow" && env.CoachUI._test.speechRate() === 0.8);
  const spd = env.registry.get("speedSelect");
  spd.value = "quick";
  for (const f of spd.listeners.change || []) f();
  ok("speed choice persists like the voice picker", env.localStorage.getItem("chessCoachSpeed.beginnertest") === "quick",
     env.localStorage.getItem("chessCoachSpeed.beginnertest"));
  ok("rate follows the speed setting", env.CoachUI._test.speechRate() === 1.05);
  ok("Options mirror shows the same speed", env.registry.get("optSpeedSelect").value === "quick");
  env.CoachUI.speak("Speed check");
  const u = env.utterances[env.utterances.length - 1];
  ok("utterances use the chosen speed", !!u && u.rate === 1.05, u ? "rate=" + u.rate : "none");
}

// ---------- 13 Phase 1: profiles, Options shell, games wallet, out-of-games, menu save ----------
async function test13() {
  begin("13 Phase 1 profiles + wallet + Options");
  mock.reset();
  const env = loadCoach(allLessonsDossier());
  await unlock(env);
  // header chips
  ok("games chip shows the local counter", env.registry.get("gamesChip").textContent === "3 games",
     env.registry.get("gamesChip").textContent);
  ok("profile chip shows the seeded profile (Luke)", env.registry.get("profileChip").textContent === "B Beginner Test",
     env.registry.get("profileChip").textContent);
  ok("pre-game line shows cost + remaining", env.registry.get("gameCostLine").textContent === "Uses 1 game · 3 left",
     env.registry.get("gameCostLine").textContent);
  // games chip popover copy never uses the forbidden words
  for (const f of env.registry.get("gamesChip").listeners.click || []) f();
  const gi = env.registry.get("gamesInfo").textContent;
  ok("games popover explains the counter", gi.includes("Today: 3 new") && gi.includes("Shared by this account"), gi);
  ok("games popover never says 'bank' or 'in hand'", !/bank|in hand/i.test(gi), gi);
  // starting a game spends one
  env.CoachUI.startGame("kids");
  ok("chip drops after a game starts", env.registry.get("gamesChip").textContent === "2 games",
     env.registry.get("gamesChip").textContent);
  ok("wallet persisted locally", !!env.localStorage.getItem("chessCoachWallet.beginnertest"));
  // Menu mid-game opens the save sheet, not the menu (b9)
  fireClick(env, "menuBtn");
  ok("Menu during a game opens the save sheet", env.registry.get("menuSheet").style.display === "flex",
     env.registry.get("menuSheet").style.display);
  ok("menu itself is not open yet", env.registry.get("kidsMenu").style.display === "none");
  fireClick(env, "keepPlayingBtn");
  ok("Keep playing closes the sheet", env.registry.get("menuSheet").style.display === "none");
  fireClick(env, "menuBtn");
  fireClick(env, "saveToMenuBtn");
  ok("Save and go to menu opens the menu", env.registry.get("kidsMenu").style.display !== "none");
  ok("menu offers Continue for the saved game", env.registry.get("continueBtn").style.display !== "none");
  fireClick(env, "continueBtn");
  ok("Continue returns to the board", env.registry.get("kidsMenu").style.display === "none");
  // profiles: add a second profile; dossiers stay separate
  fireClick(env, "profileChip");
  ok("profile chip opens the Options drawer", env.registry.get("optionsDrawer").style.display === "flex");
  ok("Options has no 'grown-up' labeling", !/grown[- ]up/i.test(env.registry.get("optionsDrawer").textContent || ""));
  fireClick(env, "optAddProfile");
  ok("a second profile was added and became active", env.CoachUI._test.getProfiles().profiles.length === 2 &&
     env.CoachUI._test.getActiveProfileId() !== "default",
     JSON.stringify(env.CoachUI._test.getProfiles().profiles.map((p) => p.name)));
  ok("new profile starts with its own empty dossier", env.CoachUI._test.getDossier().points === 0,
     "points=" + env.CoachUI._test.getDossier().points);
  ok("drawer closed after switching", env.registry.get("optionsDrawer").style.display === "none");
  // rename via the Options name field
  fireClick(env, "profileChip");
  const nameIn = env.registry.get("optProfileName");
  nameIn.value = "Sam";
  for (const f of nameIn.listeners.change || []) f();
  ok("rename updates the profile chip", env.registry.get("profileChip").textContent === "S Sam",
     env.registry.get("profileChip").textContent);
  ok("privacy line names the profile", env.registry.get("optPrivacyLine").textContent === "Sam's profile stores: display name only",
     env.registry.get("optPrivacyLine").textContent);
  // switch back to Luke: his points survived
  const sel = env.registry.get("optProfileSelect");
  sel.value = "default";
  for (const f of sel.listeners.change || []) f();
  ok("switching back restores Luke's dossier", env.CoachUI._test.getActiveProfileId() === "default" &&
     env.CoachUI._test.getDossier().gamesPlayed >= 1, "gamesPlayed=" + env.CoachUI._test.getDossier().gamesPlayed);
  // out of games: drain the wallet, then a game start shows the no-commerce screen
  env.localStorage.setItem("chessCoachWallet.beginnertest", JSON.stringify({ day: todayStr(), credited: 3, used: 3, saved: 0 }));
  env.CoachUI._test.renderWallet();
  ok("chip reads 0 games when drained", env.registry.get("gamesChip").textContent === "0 games",
     env.registry.get("gamesChip").textContent);
  env.CoachUI.startGame("kids");
  const og = env.registry.get("outOfGames");
  ok("out-of-games screen appears", og.style.display === "flex", "display=" + og.style.display);
  const ogBlock = (html.match(/<div id="outOfGames"[\s\S]*?<\/div><\/div>/) || [""])[0];
  ok("out-of-games copy is the spec line", ogBlock.includes("That's all the games for today. More tomorrow! Try a lesson again?"), ogBlock.slice(0, 120));
  ok("out-of-games screen has NO price and NO upgrade wording", !/\$|price|upgrade|buy/i.test(ogBlock), ogBlock.slice(0, 120));
  ok("no game was started while out of games", env.CoachUI._test.getDossier().gamesPlayed === 1,
     "gamesPlayed=" + env.CoachUI._test.getDossier().gamesPlayed);
}

// ---------- Test 14: Phase 2a (Ticket 006) signed-in wiring ----------
async function test14() {
  begin("14 Phase 2a accounts wiring (New Player)");
  mock.reset();
  const env = loadCoach(baseDossier());
  await unlock(env);
  ok("signed out at start: local profile (Luke) + local wallet drive the page",
     env.registry.get("optAccountLine").textContent === "Not signed in" &&
     env.registry.get("profileChip").textContent === "B Beginner Test" &&
     env.registry.get("gamesChip").textContent === "3 games",
     env.registry.get("optAccountLine").textContent + " / " + env.registry.get("profileChip").textContent);
  // sign in from Options
  env.registry.get("optAcctEmail").value = "parent@example.com";
  env.registry.get("optAcctPw").value = ACCT_PW;
  fireClick(env, "optSignInBtn");
  await pump(env, 10); await sleep(20);
  ok("sign-in succeeds and the server profile takes over the chip (Luke Two)",
     env.CoachUI._test.signedIn() === true &&
     env.registry.get("optAccountLine").textContent === "Signed in as parent@example.com" &&
     env.registry.get("profileChip").textContent === "L Luke Two",
     env.registry.get("profileChip").textContent);
  ok("games chip shows the server caps (3)", env.registry.get("gamesChip").textContent === "3 games");
  const branchSessionsBefore = mock.calls.session.length;
  // a full game opens a CHARGED account session; the local wallet is untouched
  env.CoachUI.startGame("kids");
  await pump(env, 10); await sleep(20);
  const as = mock.calls.acctSession[mock.calls.acctSession.length - 1];
  ok("full game opened an account session for the server profile, charge:true",
     !!as && as.profile_id === "srv-luke2" && as.charge === true,
     "acctSession=" + JSON.stringify(mock.calls.acctSession));
  ok("no new branch session for the game", mock.calls.session.length === branchSessionsBefore);
  ok("server caps decremented (chip 2 games) and the LOCAL wallet was NOT spent",
     env.registry.get("gamesChip").textContent === "2 games" &&
     env.CoachUI._test.getWallet().used === 0,
     env.registry.get("gamesChip").textContent + " used=" + env.CoachUI._test.getWallet().used);
  // a lesson opens an UNCHARGED account session (lessons are free)
  env.CoachUI.startLesson("pawn");
  await pump(env, 20); await sleep(20);
  const ls = mock.calls.acctSession[mock.calls.acctSession.length - 1];
  ok("lesson session is uncharged and carries the lesson game_id",
     !!ls && ls.charge === false && /^lesson-pawn-/.test(ls.game_id || ""),
     "lessonSession=" + JSON.stringify(ls));
  ok("caps unchanged by the lesson (still 2)", env.registry.get("gamesChip").textContent === "2 games");
  const pk = mock.calls.pickup[mock.calls.pickup.length - 1];
  ok("the lesson pickup rode the account game token", !!pk && /^Bearer tok-acct-/.test(pk.headers.authorization || ""),
     "pickupAuth=" + (pk && pk.headers.authorization));
  // sign out -> local mode returns
  fireClick(env, "optSignOutBtn");
  await pump(env, 10); await sleep(20);
  ok("sign-out returns to local profiles + wallet (Luke, local 3 games)",
     env.CoachUI._test.signedIn() === false && mock.calls.acctLogout === 1 &&
     env.registry.get("profileChip").textContent === "B Beginner Test" &&
     env.registry.get("gamesChip").textContent === "3 games",
     env.registry.get("profileChip").textContent + " / " + env.registry.get("gamesChip").textContent);
}

// ---------- Test 15: Phase 2b (Ticket 006) passkey surface + wiring ----------
async function test15() {
  begin("15 Phase 2b passkeys wiring (New Player)");
  ok("login form offers passkey sign-in", html.includes('id="optPasskeySignInBtn"') && html.includes("Sign in with a passkey"));
  ok("account block has the passkey manage section + fallback note slot",
     html.includes('id="optPasskeyManage"') && html.includes('id="optPasskeyList"') &&
     html.includes('id="optAddPasskeyBtn"') && html.includes("Add a passkey") && html.includes('id="optPasskeyNote"'));
  ok("no 'grown-up' copy in the new surface", !/grown[- ]up/i.test(html));
  mock.reset();
  const env = loadCoach(baseDossier()); // no WebAuthn injected -> fallback path
  await unlock(env);
  ok("without WebAuthn: fallback note explains, passkey button hidden, waSupported() false",
     env.registry.get("optPasskeyNote").textContent.includes("aren't available in this browser") &&
     env.registry.get("optPasskeyNote").textContent.includes("your password still works") &&
     env.registry.get("optPasskeySignInBtn").style.display === "none" &&
     env.CoachUI._test.waSupported() === false,
     env.registry.get("optPasskeyNote").textContent);
  const env2 = loadCoach(baseDossier(), { webauthn: makeFakeWebAuthn() });
  await unlock(env2);
  env2.registry.get("optAcctEmail").value = "parent@example.com";
  fireClick(env2, "optPasskeySignInBtn");
  await pump(env2, 10); await sleep(20);
  ok("passkey sign-in: options + verify called, signed in, server profile on the chip",
     mock.calls.waAuthOptions.length === 1 && mock.calls.waAuthVerify.length === 1 &&
     env2.CoachUI._test.signedIn() === true &&
     env2.registry.get("optAccountLine").textContent === "Signed in as parent@example.com" &&
     env2.registry.get("profileChip").textContent === "L Luke Two",
     env2.registry.get("optAccountLine").textContent + " / " + env2.registry.get("profileChip").textContent);
  ok("the email from the form rode along to auth options",
     (mock.calls.waAuthOptions[0] || {}).email === "parent@example.com",
     JSON.stringify(mock.calls.waAuthOptions[0]));
  fireClick(env2, "optAddPasskeyBtn");
  await pump(env2, 10); await sleep(20);
  const listText = collectText(env2.registry.get("optPasskeyList"));
  ok("add passkey: register options + verify called, list shows the key with a Remove button",
     mock.calls.waRegOptions.length === 1 && mock.calls.waRegVerify.length === 1 &&
     env2.CoachUI._test.getPasskeys().length === 1 &&
     listText.includes("Passkey") && listText.includes("Remove"),
     listText);
  const span = env2.registry.get("optPasskeyList").children[0];
  const rmBtn = span.children[span.children.length - 1];
  for (const f of rmBtn.listeners.click || []) await f();
  await pump(env2, 10); await sleep(20);
  ok("remove: endpoint called with the credential id, list back to 'None yet'",
     mock.calls.waRemove.length === 1 && mock.calls.waRemove[0].credential_id === "mock-cred-1" &&
     env2.CoachUI._test.getPasskeys().length === 0 &&
     env2.registry.get("optPasskeyList").textContent === "None yet",
     env2.registry.get("optPasskeyList").textContent);
}

// ---------- Test 16: Phase 3 (Ticket 006) plan display + billing on the New Player pages ----------
async function test16() {
  begin("16 Phase 3 plans + billing");
  ok("drawer has Manage billing; the coach picker is NOT on New Player pages",
     html.includes('id="optManageBilling"') && html.includes("Manage billing") &&
     !html.includes('id="optCoachRow"') && !html.includes('id="optCoachAstraBtn"'));
  ok("no 'grown-up' copy on the page", !/grown[- ]up/i.test(html));
  mock.reset();
  const env = loadCoach(RELAY);
  await unlock(env);
  const signIn = async () => {
    env.registry.get("optAcctEmail").value = "parent@example.com";
    env.registry.get("optAcctPw").value = ACCT_PW;
    for (const f of env.registry.get("optSignInBtn").listeners.click || []) await f();
    await pump(env, 10);
  };
  const signOut = async () => {
    for (const f of env.registry.get("optSignOutBtn").listeners.click || []) await f();
    await pump(env, 10);
  };
  await signIn();
  ok("plan line shows the display name (Coach)", env.registry.get("optPlanLine").textContent === "Plan: Coach · parent@example.com",
     env.registry.get("optPlanLine").textContent);
  ok("Manage billing shows when signed in", env.registry.get("optManageBilling").style.display === "");
  for (const f of env.registry.get("optManageBilling").listeners.click || []) await f();
  await pump(env, 10);
  ok("portal endpoint was called", mock.calls.billing.some((c) => c.url === "/v1/billing/portal"));
  ok("unconfigured billing reads gracefully", env.registry.get("optBillingNote").textContent === "Billing isn't open yet — it arrives with the full launch.",
     env.registry.get("optBillingNote").textContent);
  mock.acct.plan = "byok_weekly";
  mock.acct.caps = { plan: "byok_weekly", unlimited: true, left: null, today_new: 0, saved: 0,
                     daily_credit: 0, ready_cap: 0, next_credit_at: null };
  await signOut();
  await signIn();
  ok("plan line shows BYOK", env.registry.get("optPlanLine").textContent === "Plan: BYOK · parent@example.com",
     env.registry.get("optPlanLine").textContent);
  ok("chip reads '∞ your key' on the unlimited posture", env.registry.get("gamesChip").textContent === "∞ your key",
     env.registry.get("gamesChip").textContent);
  mock.acct.plan = "lapsed";
  mock.acct.caps = { left: 0, today_new: 0, saved: 3, daily_credit: 0, ready_cap: 0,
                     next_credit_at: new Date(Date.now() + 3600e3).toISOString() };
  await signOut();
  await signIn();
  env.CoachUI._test.renderWallet();
  ok("plan line shows Paused", env.registry.get("optPlanLine").textContent === "Plan: Paused · parent@example.com",
     env.registry.get("optPlanLine").textContent);
  ok("zero-credit cost line is honest", env.registry.get("gameCostLine").textContent === "No plan right now — lessons are still free",
     env.registry.get("gameCostLine").textContent);
}

// ---------- Test 17: Phase 4 (Ticket 006) temp accounts on New Player pages ----------
async function test17() {
  begin("17 Phase 4 temp accounts + New Player key line");
  ok("Settings carries the built-in-coach line and NO key field anywhere",
     html.includes('id="optByokNpLine"') && html.includes("New Player always plays with the built-in coach") &&
     !html.includes("optByokKey") && !html.includes("optByokSection"));
  const coachJs = fs.readFileSync(path.join(branchDir, "coach.js"), "utf8");
  ok("the controller never calls a BYOK endpoint (New Player exclusion at page level)",
     !coachJs.includes("/v1/byok") && !coachJs.includes("optByok"));
  ok("guest banner + claim form + redeem entry exist; no 'grown-up' copy",
     html.includes('id="guestBanner"') && html.includes("Keep my progress") &&
     html.includes('id="optGuestClaim"') && html.includes('id="optRedeemCode"') && html.includes('id="optRedeemBtn"') &&
     !/grown[- ]up/i.test(html));
  mock.reset();
  const env = loadCoach(baseDossier());
  await unlock(env);
  env.registry.get("optRedeemCode").value = "WRONG-CODE";
  fireClick(env, "optRedeemBtn");
  await pump(env, 10); await sleep(20);
  ok("a bad code is refused with plain copy, still signed out",
     env.registry.get("optAcctMsg").textContent.includes("That code wasn't recognized") &&
     env.CoachUI._test.signedIn() === false, env.registry.get("optAcctMsg").textContent);
  env.registry.get("optRedeemCode").value = "GOOD-CODE-1234";
  fireClick(env, "optRedeemBtn");
  await pump(env, 10); await sleep(20);
  ok("a good code signs in as a guest on the New Player profile",
     env.CoachUI._test.signedIn() === true && env.CoachUI._test.getAccount().guest === true &&
     env.CoachUI._test.getActiveProfileId() === "srv-guest-kid",
     JSON.stringify(env.CoachUI._test.getAccount()));
  ok("banner + account lines name the test account with its days left",
     env.registry.get("guestBanner").style.display === "" &&
     env.registry.get("guestBannerText").textContent.includes("7 days left") &&
     env.registry.get("optAccountLine").textContent === "Test account — 7 days left" &&
     env.registry.get("optGuestClaim").style.display === "",
     env.registry.get("optAccountLine").textContent);
  env.CoachUI.startGame("kids");
  await pump(env, 10); await sleep(20);
  const gs = mock.calls.acctSession[mock.calls.acctSession.length - 1];
  ok("the guest's game opens a charged account session for the guest profile",
     !!gs && gs.profile_id === "srv-guest-kid" && gs.charge === true, JSON.stringify(gs));
  env.registry.get("optClaimEmail").value = "parent-claimed@example.com";
  env.registry.get("optClaimPw").value = "claimed-pass-1";
  fireClick(env, "optClaimBtn");
  await pump(env, 10); await sleep(20);
  ok("claim converts the guest: banner hides, account line shows the email",
     env.CoachUI._test.getAccount().guest === false &&
     env.registry.get("guestBanner").style.display === "none" &&
     env.registry.get("optAccountLine").textContent === "Signed in as parent-claimed@example.com" &&
     env.registry.get("optAcctMsg").textContent.includes("this account is yours now"),
     env.registry.get("optAccountLine").textContent);
}

const tests = [test1, test2, test3, test4, test5, test6, test7, test8, test9, test10, test11, test12, test13, test14, test15, test16, test17];
for (const t of tests) { try { await t(); } catch (e) { fail++; if (perTest[current]) perTest[current].fail++; console.log("FAIL test threw: " + (e && e.stack || e)); } }
console.log("\nSUMMARY");
for (const [name, r] of Object.entries(perTest)) console.log(name + ": " + r.pass + " passed, " + r.fail + " failed");
console.log("TOTAL: " + pass + " passed, " + fail + " failed");
server.close();
process.exit(fail ? 1 : 0);
