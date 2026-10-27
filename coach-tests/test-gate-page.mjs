// Node harness for the Chess Coach relay-gate page (Ticket 004, workstream B).
// Stands up a tiny mock /v1 relay (node http) implementing the gate
// contract with scripted behaviors, loads the coach-you branch page
// scripts into a DOM stub (same pattern as test-page.mjs), points the
// page at the mock via the ?relay= override, and drives the gate,
// turn, fallback and review flows end to end.
import fs from "node:fs";
import http from "node:http";
import vm from "node:vm";
import path from "node:path";
import { fileURLToPath } from "node:url";

const dir = path.dirname(fileURLToPath(import.meta.url));
const branchDir = path.join(dir, "..", "coach-you");
const html = fs.readFileSync(path.join(branchDir, "index.html"), "utf8");
const inlineScripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);

const TEST_PW = "mock-password-for-tests"; // the mock's password, not any real gate word

// ---------- mock /v1 relay ----------
const ACCT_PW = "acct-pass-123";
const mock = {
  calls: { session: [], turn: [], review: [], health: 0, billing: [],
           waRegOptions: [], waRegVerify: [], waAuthOptions: [], waAuthVerify: [], waRemove: [],
           byok: [], redeem: [], claim: [] },
  billingMode: "unconfigured", // "unconfigured" | "ok" | "nocustomer"
  passkeys: [],
  healthStatus: 200,
  turnHandler: null, // (callNo, body) => {status, json}
  byok: null, byokTestMode: "ok", // Phase 4 fixtures
  guest: false, guestExpired: false,
  acct: null,
  resetAcct() {
    this.acct = {
      plan: "coach",
      profiles: [{ id: "srv-dad", name: "Dad", mode: "Standard", coach: "sol" }],
      activeId: "srv-dad", seq: 0,
      caps: { left: 3, today_new: 3, saved: 0, daily_credit: 3, ready_cap: 8,
              next_credit_at: new Date(Date.now() + 3600e3).toISOString() },
    };
    this.calls.acctAuth = []; this.calls.acctSession = [];
    this.calls.acctProfiles = []; this.calls.acctLogout = 0;
  },
  reset() {
    this.calls = { session: [], turn: [], review: [], health: 0, billing: [],
                   waRegOptions: [], waRegVerify: [], waAuthOptions: [], waAuthVerify: [], waRemove: [],
                   byok: [], redeem: [], claim: [] };
    this.passkeys = [];
    this.healthStatus = 200;
    this.turnHandler = null;
    this.billingMode = "unconfigured";
    this.byok = null; this.byokTestMode = "ok";
    this.guest = false; this.guestExpired = false;
    this.resetAcct();
  },
};
mock.resetAcct();
let tokenCounter = 0;
function readBody(req) {
  return new Promise((resolve) => {
    let s = "";
    req.on("data", (c) => { s += c; });
    req.on("end", () => { try { resolve(JSON.parse(s || "{}")); } catch (_) { resolve({}); } });
  });
}
const server = http.createServer(async (req, res) => {
  const send = (status, obj) => { res.writeHead(status, { "Content-Type": "application/json" }); res.end(JSON.stringify(obj)); };
  const body = await readBody(req);
  const url0 = req.url;
  if (req.url === "/v1/health") { mock.calls.health++; return send(mock.healthStatus, mock.healthStatus === 200 ? { ok: true, auth_mode: "password" } : { ok: false }); }
  if (req.url === "/v1/session") {
    mock.calls.session.push(body);
    if (body.password !== TEST_PW) return send(401, { error: "wrong password" });
    const token = "tok-" + (++tokenCounter);
    return send(200, { token, exp: Math.floor(Date.now() / 1000) + 3600 });
  }
  if (req.url === "/v1/turn") {
    mock.calls.turn.push({ headers: req.headers, body });
    if (!String(req.headers.authorization || "").startsWith("Bearer tok-")) return send(401, { error: "no token" });
    const out = mock.turnHandler ? mock.turnHandler(mock.calls.turn.length, body)
                                 : { status: 200, json: { move: body.candidates[0].san, coach_line: "Mock coach move." } };
    return send(out.status, out.json || {});
  }
  if (req.url === "/v1/review") {
    mock.calls.review.push({ headers: req.headers, body });
    return send(200, { elo_before: body.elo_before, elo_after: body.elo_before + 14,
                       review_text: "Mock review: a solid game — watch your queen's defenders.",
                       focus_lesson: "Before you move a piece, check its new square." });
  }
  // ---- Phase 2a account routes (mock) ----
  if (url0 === "/v1/login" || url0 === "/v1/signup") {
    mock.calls.acctAuth.push({ url: url0, body });
    if (url0 === "/v1/signup" && body.email === "taken@example.com") return send(409, { error: "account exists" });
    if (body.password !== ACCT_PW) return send(401, { error: "unauthorized" });
    return send(200, { token: "acct-tok-1", exp: Math.floor(Date.now() / 1000) + 3600,
                       account: { email: body.email, plan: mock.acct.plan },
                       profiles: mock.acct.profiles, active_profile_id: mock.acct.activeId,
                       caps: { ...mock.acct.caps } });
  }
  if (url0 === "/v1/logout") { mock.calls.acctLogout++; return send(200, { ok: true }); }
  if (url0 === "/v1/profiles" && req.method === "GET") {
    return send(200, { profiles: mock.acct.profiles, active_profile_id: mock.acct.activeId, caps: { ...mock.acct.caps } });
  }
  if (url0 === "/v1/profiles" && req.method === "POST") {
    const p = { id: "srv-" + (++mock.acct.seq), name: body.name, mode: body.mode, coach: body.coach === "astra" ? "astra" : "sol" };
    mock.acct.profiles.push(p);
    mock.calls.acctProfiles.push({ op: "create", body });
    return send(200, { profile: p, profiles: mock.acct.profiles, active_profile_id: mock.acct.activeId, caps: { ...mock.acct.caps } });
  }
  if (url0 === "/v1/profiles/switch") { mock.acct.activeId = body.profile_id; mock.calls.acctProfiles.push({ op: "switch", body }); return send(200, { active_profile_id: mock.acct.activeId, profiles: mock.acct.profiles, caps: { ...mock.acct.caps } }); }
  if (url0 === "/v1/profiles/update") { mock.calls.acctProfiles.push({ op: "update", body }); const p = mock.acct.profiles.find((x) => x.id === body.profile_id); if (p && body.name) p.name = body.name; if (p && body.coach) p.coach = body.coach; return send(200, { profile: p, profiles: mock.acct.profiles, active_profile_id: mock.acct.activeId, caps: { ...mock.acct.caps } }); }
  if (url0 === "/v1/profiles/delete") { mock.calls.acctProfiles.push({ op: "delete", body }); mock.acct.profiles = mock.acct.profiles.filter((x) => x.id !== body.profile_id); if (mock.acct.activeId === body.profile_id) mock.acct.activeId = mock.acct.profiles.length ? mock.acct.profiles[0].id : null; return send(200, { profiles: mock.acct.profiles, active_profile_id: mock.acct.activeId, caps: { ...mock.acct.caps } }); }
  if (url0 === "/v1/games") { return send(200, { ...mock.acct.caps }); }
  // ---- Phase 2b passkey routes (mock): shape-level only — the real
  // cryptography is proven against the real gate in test-gate.mjs ----
  if (url0 === "/v1/passkeys/register/options") {
    mock.calls.waRegOptions.push(body);
    return send(200, { challenge: "bW9jay1jaGFsbGVuZ2U", rp: { id: "moorefolio.com", name: "Chess Coach" },
                       user: { id: "bW9jay11c2Vy", name: "tester@example.com", displayName: "tester@example.com" },
                       pubKeyCredParams: [{ type: "public-key", alg: -7 }], timeout: 60000, attestation: "none",
                       authenticatorSelection: { residentKey: "preferred", userVerification: "preferred" },
                       excludeCredentials: mock.passkeys.map((p) => ({ type: "public-key", id: p.id, transports: p.transports })) });
  }
  if (url0 === "/v1/passkeys/register/verify") {
    mock.calls.waRegVerify.push(body);
    mock.passkeys.push({ id: body.id, created_at: new Date().toISOString(), last_used_at: null, transports: body.transports || [] });
    return send(200, { ok: true, passkeys: mock.passkeys });
  }
  if (url0 === "/v1/passkeys" && req.method === "GET") { return send(200, { passkeys: mock.passkeys }); }
  if (url0 === "/v1/passkeys/remove") {
    mock.calls.waRemove.push(body);
    mock.passkeys = mock.passkeys.filter((p) => p.id !== body.credential_id);
    return send(200, { ok: true, passkeys: mock.passkeys });
  }
  if (url0 === "/v1/passkeys/auth/options") {
    mock.calls.waAuthOptions.push(body);
    return send(200, { challenge: "bW9jay1jaGFsbGVuZ2U", rpId: "moorefolio.com", timeout: 60000,
                       userVerification: "preferred",
                       allowCredentials: mock.passkeys.map((p) => ({ type: "public-key", id: p.id, transports: p.transports })) });
  }
  if (url0 === "/v1/passkeys/auth/verify") {
    mock.calls.waAuthVerify.push(body);
    return send(200, { token: "acct-tok-1", exp: Math.floor(Date.now() / 1000) + 3600,
                       account: { email: "tester@example.com", plan: mock.acct.plan },
                       profiles: mock.acct.profiles, active_profile_id: mock.acct.activeId,
                       caps: { ...mock.acct.caps } });
  }
  if (url0 === "/v1/billing/portal" || url0 === "/v1/billing/checkout") {
    mock.calls.billing.push({ url: url0, body });
    if (mock.billingMode === "unconfigured") return send(503, { error: "billing not configured yet", billing_configured: false });
    if (url0 === "/v1/billing/portal" && mock.billingMode === "nocustomer") return send(409, { error: "no billing account yet" });
    return send(200, { url: "https://billing.example.test/session" });
  }
  // ---- Phase 4 BYOK + temp-account routes (mock): shape-level —
  //      the real crypto/routing/lifecycle are proven in test-gate.mjs
  if (url0 === "/v1/byok" && req.method === "GET") {
    mock.calls.byok.push({ op: "get" });
    return send(200, { byok: mock.byok, models: {
      openai: [{ id: "gpt-6-sol", label: "GPT-6 Sol" }, { id: "gpt-6-luna", label: "GPT-6 Luna" }],
      anthropic: [{ id: "claude-opus-5-5", label: "Claude Opus 5.5" }, { id: "claude-sonnet-5", label: "Claude Sonnet 5" }] } });
  }
  if (url0 === "/v1/byok" && req.method === "POST") {
    mock.calls.byok.push({ op: "set", body });
    mock.byok = { provider: body.provider, model: body.model,
                  tail: "····" + String(body.key).slice(-4), added_at: new Date().toISOString() };
    return send(200, { byok: mock.byok });
  }
  if (url0 === "/v1/byok/remove") { mock.calls.byok.push({ op: "remove" }); mock.byok = null; return send(200, { byok: null }); }
  if (url0 === "/v1/byok/test") {
    mock.calls.byok.push({ op: "test" });
    if (!mock.byok) return send(409, { error: "no key saved" });
    return send(200, mock.byokTestMode === "reject" ? { ok: false, error: "key rejected" }
      : { ok: true, provider: mock.byok.provider, model: mock.byok.model });
  }
  if (url0 === "/v1/redeem") {
    mock.calls.redeem.push(body);
    if (body.code !== "GOOD-CODE-1234") return send(401, { error: "code not recognized" });
    mock.guest = true;
    return send(200, { token: "acct-tok-guest", exp: Math.floor(Date.now() / 1000) + 3600,
                       account: { email: null, plan: "coach", guest: true, guest_days_left: 7,
                                  guest_expires_at: new Date(Date.now() + 7 * 864e5).toISOString() },
                       profiles: [{ id: "srv-guest", name: "Tester", mode: "Standard", coach: "sol" }],
                       active_profile_id: "srv-guest", caps: { ...mock.acct.caps } });
  }
  if (url0 === "/v1/guest/claim") {
    mock.calls.claim.push(body);
    if (!mock.guest) return send(409, { error: "not a guest account" });
    if (body.email === "taken@example.com") return send(409, { error: "account exists" });
    mock.guest = false;
    return send(200, { token: "acct-tok-1", exp: Math.floor(Date.now() / 1000) + 3600,
                       account: { email: body.email, plan: "coach", guest: false },
                       profiles: [{ id: "srv-guest", name: "Tester", mode: "Standard", coach: "sol" }],
                       active_profile_id: "srv-guest", caps: { ...mock.acct.caps } });
  }
  if (url0 === "/v1/account" && req.method === "GET") {
    return send(200, { email: mock.guest ? null : "tester@example.com", plan: mock.acct.plan,
                       guest: !!mock.guest, guest_days_left: mock.guest ? 7 : null,
                       guest_expires_at: mock.guest ? new Date(Date.now() + 7 * 864e5).toISOString() : null,
                       byok: mock.byok,
                       profiles: mock.acct.profiles, active_profile_id: mock.acct.activeId,
                       caps: { ...mock.acct.caps } });
  }
  if (url0 === "/v1/account/session") {
    mock.calls.acctSession.push(body);
    if (mock.guestExpired) return send(403, { error: "guest expired", guest_expired: true });
    if (body.charge && mock.acct.caps.left <= 0) return send(409, { error: "no games left", caps: { ...mock.acct.caps } });
    if (body.charge) { mock.acct.caps.left--; mock.acct.caps.today_new--; }
    const token = "tok-acct-" + (++tokenCounter);
    const prof = mock.acct.profiles.find((x) => x.id === body.profile_id) ||
                 (body.profile_id === "srv-guest" ? { id: "srv-guest", mode: "Standard", coach: "sol" } : null);
    const seat = !prof ? "sol" : prof.mode === "New Player" ? "kids"
      : (mock.byok ? "byok" : (mock.acct.plan === "pro" && prof.coach === "astra" ? "astra" : "sol"));
    return send(200, { token, exp: Math.floor(Date.now() / 1000) + 3600, caps: { ...mock.acct.caps }, charged: !!body.charge, coach_seat: seat });
  }
  return send(404, { error: "unknown route" });
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const RELAY = "http://127.0.0.1:" + server.address().port;
// a guaranteed-dead port for the unreachable test
const deadServer = http.createServer(() => {});
await new Promise((r) => deadServer.listen(0, "127.0.0.1", r));
const DEAD_RELAY = "http://127.0.0.1:" + deadServer.address().port;
await new Promise((r) => deadServer.close(r));

// ---------- DOM stub (pattern follows test-page.mjs) ----------
const IDS = ["board", "boardWrap", "branchLine", "capturedByWhite", "capturedByBlack",
  "whiteName", "blackName", "turnLine", "newGameBtn", "practiceBtn", "hintBtn",
  "resetBtn", "flipBtn", "soundBtn", "coachBody", "coachState", "coachTicker", "movesBody",
  "reviewPanel", "reviewBody", "dossierBody", "alertBody", "promoModal",
  "promoChoices", "gate", "gateInput", "gateMsg", "gateBtn", "gateOfflineBtn", "modeLine",
  "centerCol", "capStripTop", "capStripBottom", "gameInfoTitle", "gameInfoKind", "gameInfoProfile",
  "gameCostLine", "gamesChip", "gamesInfo", "profileChip", "optionsDrawer", "optionsClose",
  "optProfileSelect", "optAddProfile", "optProfileName", "optModeTag", "optRecalibrate",
  "optSoundBtn", "optPlanLine", "optPrivacyLine", "optLockBtn", "optDeleteProfile",
  "coachHistToggle", "reviewByLine", "failsafePanel",
  "optAccountLine", "optAcctForm", "optAcctEmail", "optAcctPw", "optSignInBtn",
  "optSignUpBtn", "optSignOutBtn", "optAcctMsg",
  "optPasskeySignInBtn", "optPasskeyManage", "optPasskeyList", "optAddPasskeyBtn", "optPasskeyNote",
  "optManageBilling", "optBillingNote", "optCoachRow", "optCoachSolBtn", "optCoachAstraBtn", "optCoachNote",
  "guestBanner", "guestBannerText", "guestKeepBtn", "optRedeemCode", "optRedeemBtn",
  "optGuestClaim", "optGuestDays", "optClaimEmail", "optClaimPw", "optClaimBtn", "optClaimMsg",
  "optByokSection", "optByokState", "optByokProvider", "optByokModel", "optByokKey",
  "optByokSaveBtn", "optByokTestBtn", "optByokRemoveBtn", "optByokNote"];

function makeStorage() {
  const m = new Map();
  return { getItem: (k) => (m.has(k) ? m.get(k) : null),
           setItem: (k, v) => m.set(k, String(v)),
           removeItem: (k) => m.delete(k),
           _map: m };
}

// A fake WebAuthn platform authenticator for the page wiring tests:
// returns fixed ceremony payloads with REAL ArrayBuffers so the page's
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

function loadCoach(relayUrl, opts = {}) {
  const registry = new Map();
  function makeEl(tag) {
    const el = { tag, children: [], style: {}, listeners: {}, textContent: "",
                 value: "", scrollTop: 0, scrollHeight: 0, offsetWidth: 62,
                 _cls: new Set(), _innerHTML: "", _id: "" };
    el.classList = {
      add: (c) => el._cls.add(c),
      remove: (c) => el._cls.delete(c),
      toggle: (c, force) => { const on = force === undefined ? !el._cls.has(c) : !!force;
                               on ? el._cls.add(c) : el._cls.delete(c); },
      contains: (c) => el._cls.has(c),
    };
    Object.defineProperty(el, "className", {
      get: () => [...el._cls].join(" "),
      set: (v) => { el._cls = new Set(String(v).split(/\s+/).filter(Boolean)); },
    });
    Object.defineProperty(el, "id", {
      get: () => el._id,
      set: (v) => { el._id = v; if (v) registry.set(v, el); },
    });
    Object.defineProperty(el, "innerHTML", {
      get: () => el._innerHTML,
      set: (v) => { el._innerHTML = v; if (v === "") el.children = []; },
    });
    el.appendChild = (c) => { el.children.push(c); if (c._id) registry.set(c._id, c); return c; };
    el.remove = () => {};
    el.addEventListener = (n, f) => { (el.listeners[n] = el.listeners[n] || []).push(f); };
    el.querySelectorAll = () => [];
    el.querySelector = () => null;
    el.getBoundingClientRect = () => ({ left: 0, top: 0, width: 496, height: 496, right: 496, bottom: 496 });
    return el;
  }
  for (const id of IDS) { const e = makeEl("div"); e._id = id; registry.set(id, e); }
  registry.get("alertBody").textContent = "No alerts.";

  let pollFn = null;
  const sessionStorage = makeStorage();
  const win = { __coachManualInit: true, _listeners: {},
                location: { search: "?relay=" + encodeURIComponent(relayUrl) },
                addEventListener: (n, f) => { win._listeners[n] = f; } };
  const sandbox = {
    console, setTimeout, clearTimeout, clearInterval: () => {},
    setInterval: (fn) => { pollFn = fn; return 1; },
    fetch: globalThis.fetch, AbortController: globalThis.AbortController,
    atob: globalThis.atob, btoa: globalThis.btoa,
    URLSearchParams: globalThis.URLSearchParams,
    document: { getElementById: (id) => registry.get(id) || null,
                createElement: (t) => makeEl(t), body: makeEl("body") },
    localStorage: makeStorage(), sessionStorage,
    window: win,
  };
  if (opts.webauthn) {
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
    start: async () => {},
    analyze: async (fen, multipv) => {
      const st = C.stateFromSans(run("history.slice()"));
      const legal = C.allLegalState(st, st.turn);
      // Rank like a real engine would (sensible moves first), not in
      // raw square order — otherwise the pruned candidate list would
      // never contain the moves the scripted games need.
      const PREF = ["e5", "Qh4#", "Qh4", "Nf6", "e6", "d5", "c5", "Nc6", "d6", "c6"];
      const ranked = legal.map((m) => ({ m, san: C.sanWithSuffix(st, m, m.promo ? "q" : null) }))
        .sort((a, b) => {
          const ia = PREF.indexOf(a.san), ib = PREF.indexOf(b.san);
          return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
        });
      const lines = ranked.slice(0, multipv || 10).map(({ m }) => ({ uci: C.uciFor(m), cp: 10, mate: null }));
      return { lines, bestmove: lines.length ? lines[0].uci : null };
    },
    evaluateWhite: async () => {
      // a real swing after g4 so the silent scorer produces key moments
      const h = run("history.slice()");
      return h.includes("g4") ? -600 : 10;
    },
    bestmoveAtElo: async () => {
      const st = C.stateFromSans(run("history.slice()"));
      for (const san of ["e5", "Qh4#", "Qh4", "e6"]) {
        const m = C.parseSan(st, san);
        if (m) return C.uciFor(m);
      }
      const legal = C.allLegalState(st, st.turn);
      return legal.length ? C.uciFor(legal[0]) : null;
    },
  };
  CoachUI.init({ sf: fakeSf });
  return { run, C, CoachUI, fakeSf, registry, sessionStorage, localStorage: sandbox.localStorage,
           poll: () => { if (pollFn) pollFn(); },
           history: () => run("history.slice()") };
}

async function pump(env, rounds = 100) {
  for (let i = 0; i < rounds; i++) {
    env.poll();
    await new Promise((r) => setTimeout(r, 2));
  }
}
function playSan(env, san) {
  const st = env.C.stateFromSans(env.history());
  const m = env.C.parseSan(st, san);
  if (!m) throw new Error("scripted move is not legal here: " + san);
  env.run("tryMove(" + m.from + ", " + m.to + ")");
}
function collectText(el) {
  let t = el.textContent || "";
  for (const ch of el.children || []) t += "\n" + collectText(ch);
  return t;
}
async function clickGate(env) {
  const fns = env.registry.get("gateBtn").listeners.click || [];
  for (const f of fns) await f();
  await pump(env, 10);
}
async function unlock(env) {
  env.registry.get("gateInput").value = TEST_PW;
  await clickGate(env);
}

// ---------- result bookkeeping ----------
const perTest = {};
let current = "", pass = 0, fail = 0;
function begin(name) { current = name; perTest[name] = { pass: 0, fail: 0 }; console.log("\nTEST " + name); }
function ok(label, cond, detail) {
  if (cond) { pass++; perTest[current].pass++; }
  else { fail++; perTest[current].fail++; }
  console.log((cond ? "PASS " : "FAIL ") + label + (detail !== undefined ? " | " + detail : ""));
}
function info(text) { console.log("INFO " + text); }

// ---------- Test 1: gate — wrong password stays locked, right unlocks ----------
async function test1() {
  begin("1 gate session flow");
  mock.reset();
  const env = loadCoach(RELAY);
  const gate = env.registry.get("gate");
  ok("gate is visible before entry", gate.style.display !== "none");
  env.registry.get("gateInput").value = "definitely-wrong";
  await clickGate(env);
  ok("wrong password (401) keeps the gate up", gate.style.display !== "none",
     "display=" + gate.style.display);
  ok("wrong password shows the wrong-password message",
     env.registry.get("gateMsg").textContent.includes("Wrong password"),
     "msg=" + env.registry.get("gateMsg").textContent);
  ok("no token after wrong password", env.CoachUI._test.hasToken() === false &&
     env.sessionStorage.getItem("chessCoachToken.you") === null);
  env.registry.get("gateInput").value = TEST_PW;
  await clickGate(env);
  ok("right password hides the gate", gate.style.display === "none", "display=" + gate.style.display);
  ok("token kept in sessionStorage under the branch key",
     !!env.sessionStorage.getItem("chessCoachToken.you"));
  const s = mock.calls.session[mock.calls.session.length - 1];
  ok("session POST carried {branch, password, game_id}",
     s.branch === "you" && s.password === TEST_PW && /^[A-Za-z0-9_-]+$/.test(s.game_id),
     "keys=" + Object.keys(s).sort().join(",") + " game_id=" + s.game_id);
}

// ---------- Test 2: turn packet shape + bearer + fallback = top candidate ----------
async function test2() {
  begin("2 turn packet");
  mock.reset();
  const env = loadCoach(RELAY);
  await unlock(env);
  env.CoachUI.startGame("rated");
  playSan(env, "e4"); await pump(env);
  ok("one /v1/turn call was made", mock.calls.turn.length === 1, "calls=" + mock.calls.turn.length);
  const call = mock.calls.turn[0];
  const stored = JSON.parse(env.sessionStorage.getItem("chessCoachToken.you"));
  ok("turn sent the bearer token", call.headers.authorization === "Bearer " + stored.token,
     "auth=" + call.headers.authorization);
  const b = call.body;
  ok("packet carries game_id/fen/moves/candidates/fallback/target_elo",
     !!b.game_id && typeof b.fen === "string" && Array.isArray(b.moves) &&
     Array.isArray(b.candidates) && !!b.fallback && b.target_elo === 850,
     "keys=" + Object.keys(b).sort().join(","));
  ok("moves are the SAN history", JSON.stringify(b.moves) === JSON.stringify(["e4"]),
     "moves=" + JSON.stringify(b.moves));
  ok("every candidate has ONLY {san, uci} keys",
     b.candidates.every((c) => Object.keys(c).sort().join(",") === "san,uci"));
  // the fake engine ranks e5 first after 1.e4, so the fallback must be
  // exactly that candidate (captured before the packet shuffle).
  ok("fallback equals the top Stockfish candidate (e5 / e7e5)",
     b.fallback.uci === "e7e5" && b.fallback.san === "e5",
     "fallback=" + JSON.stringify(b.fallback));
  ok("fallback is one of the packet candidates",
     b.candidates.some((c) => c.uci === b.fallback.uci));
  ok("coach reply was applied", env.history().length === 2, "history=" + JSON.stringify(env.history()));
}

// ---------- Test 3: relay unreachable -> Stockfish-only labeled game completes ----------
async function test3() {
  begin("3 relay unreachable offline game");
  mock.reset();
  const env = loadCoach(DEAD_RELAY);
  env.registry.get("gateInput").value = TEST_PW;
  await clickGate(env);
  ok("gate stays up when the relay is unreachable", env.registry.get("gate").style.display !== "none");
  ok("offline entry is offered at the gate",
     env.registry.get("gateOfflineBtn").style.display !== "none",
     "display=" + env.registry.get("gateOfflineBtn").style.display);
  for (const f of env.registry.get("gateOfflineBtn").listeners.click || []) await f();
  ok("offline entry hides the gate", env.registry.get("gate").style.display === "none");
  env.CoachUI.startGame("rated");
  ok("game is in offline mode", env.CoachUI._test.getOffline() === true);
  ok("offline mode is visibly labeled",
     env.registry.get("modeLine").textContent.includes("Coach offline — playing Stockfish at your level"),
     "modeLine=" + env.registry.get("modeLine").textContent);
  playSan(env, "f3"); await pump(env);
  playSan(env, "g4"); await pump(env);
  const hist = env.history();
  info("offline history: " + JSON.stringify(hist));
  ok("short game completed offline (Fool's mate line)", env.run("gameOver") === true && hist.length === 4,
     "history=" + JSON.stringify(hist));
  await pump(env, 40);
  const session = env.CoachUI._test.getSession();
  ok("session record flags the game offline", session.offline === true);
  ok("no /v1/review call in offline mode", mock.calls.review.length === 0,
     "reviewCalls=" + mock.calls.review.length);
  ok("offline review is labeled as offline",
     collectText(env.registry.get("reviewBody")).includes("Offline review"),
     "review=" + collectText(env.registry.get("reviewBody")).split("\n")[0]);
}

// ---------- Test 4: illegal reply twice -> packet fallback played, alerts counted ----------
async function test4() {
  begin("4 illegal reply recovery");
  mock.reset();
  mock.turnHandler = () => ({ status: 200, json: { move: "Qh5", coach_line: null } });
  const env = loadCoach(RELAY);
  await unlock(env);
  env.CoachUI.startGame("rated");
  playSan(env, "e4"); await pump(env);
  const hist = env.history();
  const session = env.CoachUI._test.getSession();
  info("history: " + JSON.stringify(hist) + " alerts: " + JSON.stringify(session.alerts.map((a) => a.kind)));
  ok("illegal Qh5 never entered history", !hist.includes("Qh5"), "history=" + JSON.stringify(hist));
  ok("the packet fallback (e5) was played instead", hist.length === 2 && hist[1] === "e5",
     "history=" + JSON.stringify(hist));
  ok("relay was asked exactly twice (attempt + one reprompt)", mock.calls.turn.length === 2,
     "turnCalls=" + mock.calls.turn.length);
  ok("exactly two failsafe alerts logged", session.alerts.length === 2, "alerts=" + session.alerts.length);
  ok("session flagged", session.flagged === true, "flagged=" + session.flagged);
  const fbMove = session.moves.find((m) => m.via === "fallback");
  ok("fallback recorded in the session record", !!fbMove && fbMove.san === "e5",
     "moves=" + JSON.stringify(session.moves));
}

// ---------- Test 5: 503 mid-game -> offline from that point, no more relay turns ----------
async function test5() {
  begin("5 mid-game 503 switch");
  mock.reset();
  mock.turnHandler = (n, body) => n === 1
    ? { status: 200, json: { move: body.candidates[0].san, coach_line: "First move, online." } }
    : { status: 503, json: { error: "kill switch" } };
  const env = loadCoach(RELAY);
  await unlock(env);
  env.CoachUI.startGame("rated");
  playSan(env, "e4"); await pump(env);
  ok("first turn was online", env.CoachUI._test.getOffline() === false && mock.calls.turn.length === 1,
     "turnCalls=" + mock.calls.turn.length);
  playSan(env, "Nf3"); await pump(env);
  ok("503 switched the game to offline mode", env.CoachUI._test.getOffline() === true);
  ok("offline label is showing",
     env.registry.get("modeLine").textContent.includes("Coach offline"),
     "modeLine=" + env.registry.get("modeLine").textContent);
  ok("the 503 turn still produced a Stockfish move", env.history().length === 4,
     "history=" + JSON.stringify(env.history()));
  playSan(env, "Bc4"); await pump(env);
  ok("later turns make no more relay calls", mock.calls.turn.length === 2,
     "turnCalls=" + mock.calls.turn.length);
  ok("game continued offline", env.history().length === 6, "history=" + JSON.stringify(env.history()));
}

// ---------- Test 6: online game end -> one /v1/review, dossier elo from response ----------
async function test6() {
  begin("6 online review");
  mock.reset();
  mock.turnHandler = (n, body) => {
    const want = n === 1 ? "e5" : "Qh4";
    const cand = body.candidates.find((c) => c.san === want || c.san.startsWith(want));
    return { status: 200, json: { move: (cand || body.candidates[0]).san, coach_line: "Mock line." } };
  };
  const env = loadCoach(RELAY);
  await unlock(env);
  const eloBefore = env.CoachUI._test.getDossier().elo;
  env.CoachUI.startGame("rated");
  playSan(env, "f3"); await pump(env);
  playSan(env, "g4"); await pump(env);
  info("history: " + JSON.stringify(env.history()) + " gameOver=" + env.run("gameOver"));
  ok("scripted mate completed the game", env.run("gameOver") === true && env.history().length === 4,
     "history=" + JSON.stringify(env.history()));
  await pump(env, 60);
  ok("/v1/review called exactly once", mock.calls.review.length === 1,
     "reviewCalls=" + mock.calls.review.length);
  if (mock.calls.review.length) {
    const rb = mock.calls.review[0].body;
    ok("review body carried game_id/result/moves/key_moments/elo_before",
       !!rb.game_id && rb.result === "0-1" && Array.isArray(rb.moves) && Array.isArray(rb.key_moments) &&
       rb.elo_before === eloBefore,
       "keys=" + Object.keys(rb).sort().join(",") + " elo_before=" + rb.elo_before);
    ok("key_moments use the contract field names",
       rb.key_moments.every((k) => "ply" in k && "san" in k && "swing_cp" in k && "reason_class" in k),
       "key_moments=" + JSON.stringify(rb.key_moments));
    ok("at least one key moment was derived from the silent scorer",
       rb.key_moments.length >= 1 && rb.key_moments.some((k) => k.san === "g4"),
       "key_moments=" + JSON.stringify(rb.key_moments));
  }
  const dossier = env.CoachUI._test.getDossier();
  ok("dossier elo updated from the review response (server authoritative)",
     dossier.elo === eloBefore + 14, "elo=" + dossier.elo + " expected=" + (eloBefore + 14));
  ok("dossier focus lesson came from the review response",
     dossier.focus_lesson === "Before you move a piece, check its new square.",
     "focus=" + dossier.focus_lesson);
  ok("relay review text is displayed",
     collectText(env.registry.get("reviewBody")).includes("Mock review: a solid game"),
     "review shown");
}

// ---------- Test 7: coach ticker at the board + Coach panel placement ----------
async function test7() {
  begin("7 coach ticker");
  ok("page has a #coachTicker element", html.includes('id="coachTicker"'));
  ok("ticker sits between the board and the control buttons",
     html.indexOf('id="coachTicker"') > html.indexOf('id="boardWrap"') &&
     html.indexOf('id="coachTicker"') < html.indexOf('id="newGameBtn"'));
  ok("Coach panel sits after the control buttons (not buried with the side panels)",
     html.indexOf("<h3>Coach</h3>") > html.indexOf('id="soundBtn"'));
  mock.reset();
  const env = loadCoach(RELAY);
  await unlock(env);
  const ticker = () => env.registry.get("coachTicker").textContent;
  ok("setCoachState mirrors into the ticker",
     ticker() === "Coach is ready. Start a new game when you are.", "ticker=" + ticker());
  env.CoachUI.startGame("rated");
  ok("coachLine mirrors into the ticker (game start)",
     ticker().includes("New game.") && ticker().includes("Your move."), "ticker=" + ticker());
  playSan(env, "f3");
  await pump(env);
  ok("coach reply line wins the ticker",
     ticker() === "Coach: Mock coach move.", "ticker=" + ticker());
}


// ---------- Test 8: Phase 1 (Ticket 006) Standard UI deltas ----------
async function test8() {
  begin("8 Phase 1 Standard deltas");
  // (a2) Game Information is truthful now
  ok("page has no 'Human vs. Human' text", !html.includes("Human vs. Human"));
  ok("Game Information shows the coach + kind + profile slots",
     html.includes('id="gameInfoTitle"') && html.includes('id="gameInfoKind"') && html.includes('id="gameInfoProfile"'));
  // (a3) failsafe panel is debug-gated in code, footer nostalgia is gone
  const coachJs = fs.readFileSync(path.join(branchDir, "coach.js"), "utf8");
  ok("failsafe panel leaves the layout unless ?debug=1", coachJs.includes('get("debug")') && coachJs.includes("fp.remove()"));
  ok("footer nostalgia line removed", !html.includes("Brasee"));
  // (a5) calibration naming
  ok("practice button is the calibration game", html.includes("Calibration game (sets your starting rating)"));
  // (a6) reset hook + ghost placement at the end of row 2
  ok("Reset sits after Flip/Sound and is a ghost button",
     html.indexOf('id="resetBtn"') > html.indexOf('id="soundBtn"') && html.includes('<button id="resetBtn" class="ghost">Reset Game</button>'));
  ok("reset asks before abandoning a counted game", coachJs.includes("Abandon this game? It still counts as used."));
  // (a9) captured strips flank the board
  ok("captured strips sit above and below the board",
     html.indexOf('id="capStripTop"') > html.indexOf('id="turnLine"') &&
     html.indexOf('id="capStripTop"') < html.indexOf('id="boardWrap"') &&
     html.indexOf('id="capStripBottom"') > html.indexOf('id="boardWrap"'));
  ok("moves table uses tabular numbers", html.includes("font-variant-numeric:tabular-nums"));
  // (c) no 'grown-up' labeling anywhere
  ok("no 'grown-up' copy in page or controller", !/grown[- ]up/i.test(html) && !/grown[- ]up/i.test(coachJs));

  mock.reset();
  const env = loadCoach(RELAY);
  await unlock(env);
  ok("profile chip shows the seeded profile", env.registry.get("profileChip").textContent === "Y You",
     env.registry.get("profileChip").textContent);
  ok("games chip shows the local counter", env.registry.get("gamesChip").textContent === "3 games",
     env.registry.get("gamesChip").textContent);
  ok("cost line offers the free calibration first", env.registry.get("gameCostLine").textContent === "First game is calibration · free",
     env.registry.get("gameCostLine").textContent);
  ok("game info names the profile", env.registry.get("gameInfoProfile").textContent === "You",
     env.registry.get("gameInfoProfile").textContent);
  ok("reset confirm hook installed", env.run("typeof window.__coachReset") === "function");
  // calibration flow: practice button visible before a rating exists,
  // hidden after; kind line follows the mode
  ok("calibration button visible while unrated", env.registry.get("practiceBtn").style.display !== "none");
  env.CoachUI._test.getDossier().calibrated = true;
  env.CoachUI.startGame("rated");
  ok("calibration button hidden once rated", env.registry.get("practiceBtn").style.display === "none");
  ok("kind line reads 'Rated game'", env.registry.get("gameInfoKind").textContent === "Rated game",
     env.registry.get("gameInfoKind").textContent);
  ok("title line reads 'You vs. the Coach (Sol)'", env.registry.get("gameInfoTitle").textContent === "You vs. the Coach (Sol)",
     env.registry.get("gameInfoTitle").textContent);
  // (a4) the rated game spent from the wallet
  ok("cost line shows 'Uses 1 game · 2 left' after starting", env.registry.get("gameCostLine").textContent === "Uses 1 game · 2 left",
     env.registry.get("gameCostLine").textContent);
  ok("games chip drops to 2", env.registry.get("gamesChip").textContent === "2 games");
  // games popover copy, forbidden words absent
  for (const f of env.registry.get("gamesChip").listeners.click || []) f();
  const gi = env.registry.get("gamesInfo").textContent;
  ok("games popover explains the counter", gi.includes("Today: 2 new") && gi.includes("Shared by this account"), gi);
  ok("games popover never says 'bank' or 'in hand'", !/bank|in hand/i.test(gi), gi);
  // (a7) coach history disclosure counts lines
  playSan(env, "e4"); await pump(env);
  const tg = env.registry.get("coachHistToggle");
  ok("history toggle counts coach lines", /^Coach history \(\d+\)$/.test(tg.textContent) && tg.textContent !== "Coach history (0)",
     tg.textContent);
  ok("coach log starts collapsed (display:none in the markup)", html.includes('id="coachBody" style="display:none"'));
  for (const f of tg.listeners.click || []) f();
  ok("toggle collapses the coach log", env.registry.get("coachBody").style.display === "none");
  for (const f of tg.listeners.click || []) f();
  ok("toggle expands the coach log", env.registry.get("coachBody").style.display === "");
  // (a8) review takeover: after the scripted mate the panel sits in the center column with a byline
  mock.turnHandler = (n, body) => {
    const want = body.moves.includes("g4") ? "Qh4" : "e5";
    const cand = body.candidates.find((c) => c.san === want || c.san.startsWith(want));
    return { status: 200, json: { move: (cand || body.candidates[0]).san, coach_line: "Mock line." } };
  };
  const env2 = loadCoach(RELAY);
  await unlock(env2);
  env2.CoachUI.startGame("rated");
  playSan(env2, "f3"); await pump(env2);
  playSan(env2, "g4"); await pump(env2);
  ok("review byline names the reviewer", env2.registry.get("reviewByLine").textContent === "Review by Sol",
     env2.registry.get("reviewByLine").textContent);
  ok("review panel moved into the center column as a takeover",
     env2.registry.get("centerCol").children.includes(env2.registry.get("reviewPanel")) &&
     env2.registry.get("reviewPanel").classList.contains("takeover"));
  // profiles: add + switch keeps dossiers separate (c1)
  const env3 = loadCoach(RELAY);
  await unlock(env3);
  for (const f of env3.registry.get("profileChip").listeners.click || []) f();
  ok("profile chip opens Options", env3.registry.get("optionsDrawer").style.display === "flex");
  for (const f of env3.registry.get("optAddProfile").listeners.click || []) f();
  ok("second profile added + active", env3.CoachUI._test.getProfiles().profiles.length === 2 &&
     env3.CoachUI._test.getActiveProfileId() !== "default");
  ok("new profile has a fresh dossier (elo 800)", env3.CoachUI._test.getDossier().elo === 800);
  // out of games: a drained wallet blocks a rated start with honest copy
  const today = () => { const d = new Date(); return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"); };
  env3.localStorage.setItem("chessCoachWallet.you", JSON.stringify({ day: today(), credited: 3, used: 3, saved: 0 }));
  env3.CoachUI._test.renderWallet();
  ok("chip reads 0 games when drained", env3.registry.get("gamesChip").textContent === "0 games");
  env3.CoachUI._test.getDossier().calibrated = true;
  env3.CoachUI.startGame("rated");
  ok("rated start blocked at zero games", env3.CoachUI._test.getSession() === null &&
     collectText(env3.registry.get("coachBody")).includes("next games arrive at midnight"),
     env3.registry.get("coachTicker").textContent);
}

// ---------- Test 9: Phase 2a (Ticket 006) signed-in wiring ----------
async function test9() {
  begin("9 Phase 2a accounts wiring");
  mock.reset();
  const env = loadCoach(RELAY);
  await unlock(env);
  ok("signed out at start: account line says so, local profile + wallet drive the chips",
     env.registry.get("optAccountLine").textContent === "Not signed in" &&
     env.registry.get("profileChip").textContent === "Y You" &&
     env.registry.get("gamesChip").textContent === "3 games",
     env.registry.get("optAccountLine").textContent + " / " + env.registry.get("profileChip").textContent);
  // wrong account password -> honest message, still signed out
  env.registry.get("optAcctEmail").value = "tester@example.com";
  env.registry.get("optAcctPw").value = "not-the-password";
  for (const f of env.registry.get("optSignInBtn").listeners.click || []) await f();
  await pump(env, 10);
  ok("wrong account password shows the sign-in error and stays signed out",
     env.registry.get("optAcctMsg").textContent === "Wrong email or password." &&
     env.CoachUI._test.signedIn() === false,
     env.registry.get("optAcctMsg").textContent);
  // right account password -> server profiles + caps take over
  env.registry.get("optAcctPw").value = ACCT_PW;
  for (const f of env.registry.get("optSignInBtn").listeners.click || []) await f();
  await pump(env, 10);
  ok("sign-in succeeds: account line names the email", env.registry.get("optAccountLine").textContent === "Signed in as tester@example.com",
     env.registry.get("optAccountLine").textContent);
  ok("sign-in form hides, sign-out shows",
     env.registry.get("optAcctForm").style.display === "none" && env.registry.get("optSignOutBtn").style.display === "");
  ok("profiles are the server's now (chip = Dad, the mock account's profile)",
     env.registry.get("profileChip").textContent === "D Dad", env.registry.get("profileChip").textContent);
  ok("plan line names the account", env.registry.get("optPlanLine").textContent === "Plan: Coach · tester@example.com",
     env.registry.get("optPlanLine").textContent);
  ok("games chip shows the server caps (3)", env.registry.get("gamesChip").textContent === "3 games");
  const branchSessionsBefore = mock.calls.session.length;
  // a rated game opens an ACCOUNT session (charged) instead of a branch session
  env.CoachUI._test.getDossier().calibrated = true;
  env.CoachUI.startGame("rated");
  await pump(env, 10);
  const as = mock.calls.acctSession[mock.calls.acctSession.length - 1];
  ok("rated start opened an account session for the active server profile, charge:true",
     !!as && as.profile_id === "srv-dad" && as.charge === true && !!as.game_id,
     "acctSession=" + JSON.stringify(mock.calls.acctSession));
  ok("no new branch session was opened for the game", mock.calls.session.length === branchSessionsBefore,
     "branchSessions=" + mock.calls.session.length + " before=" + branchSessionsBefore);
  ok("server caps decremented: chip + cost line agree (2 left)",
     env.registry.get("gamesChip").textContent === "2 games" &&
     env.registry.get("gameCostLine").textContent === "Uses 1 game · 2 left",
     env.registry.get("gamesChip").textContent + " / " + env.registry.get("gameCostLine").textContent);
  playSan(env, "e4"); await pump(env);
  const turnCall = mock.calls.turn[mock.calls.turn.length - 1];
  ok("the coach turn rode the account game token", /^Bearer tok-acct-/.test(turnCall.headers.authorization || ""),
     "auth=" + turnCall.headers.authorization);
  // games popover from server numbers; forbidden words absent
  for (const f of env.registry.get("gamesChip").listeners.click || []) f();
  const gi = env.registry.get("gamesInfo").textContent;
  ok("games popover shows server breakdown", gi.includes("Today: 2 new") && gi.includes("Saved: 0") && gi.includes("Shared by this account"), gi);
  ok("games popover never says 'bank' or 'in hand'", !/bank|in hand/i.test(gi), gi);
  // add a profile -> server create + switch
  for (const f of env.registry.get("optAddProfile").listeners.click || []) await f();
  await pump(env, 10);
  ok("add profile went to the server and switched to it",
     mock.calls.acctProfiles.some((c) => c.op === "create") &&
     mock.calls.acctProfiles.some((c) => c.op === "switch") &&
     env.CoachUI._test.getProfiles().profiles.length === 2 &&
     env.CoachUI._test.getActiveProfileId() !== "srv-dad",
     JSON.stringify(env.CoachUI._test.getProfiles()));
  // sign out -> local profiles + local wallet return, logout was called
  for (const f of env.registry.get("optSignOutBtn").listeners.click || []) await f();
  await pump(env, 10);
  ok("sign-out returns the page to local mode (profile You, local wallet 3 games)",
     env.CoachUI._test.signedIn() === false && mock.calls.acctLogout === 1 &&
     env.registry.get("profileChip").textContent === "Y You" &&
     env.registry.get("gamesChip").textContent === "3 games",
     env.registry.get("profileChip").textContent + " / " + env.registry.get("gamesChip").textContent);
  ok("account line back to signed-out, plan line restored",
     env.registry.get("optAccountLine").textContent === "Not signed in" &&
     env.registry.get("optPlanLine").textContent.includes("accounts and billing arrive"));
}

// ---------- Test 10: Phase 2b (Ticket 006) passkey surface + wiring ----------
async function test10() {
  begin("10 Phase 2b passkeys wiring");
  ok("login form offers passkey sign-in", html.includes('id="optPasskeySignInBtn"') && html.includes("Sign in with a passkey"));
  ok("account block has the passkey manage section + fallback note slot",
     html.includes('id="optPasskeyManage"') && html.includes('id="optPasskeyList"') &&
     html.includes('id="optAddPasskeyBtn"') && html.includes("Add a passkey") && html.includes('id="optPasskeyNote"'));
  ok("no 'grown-up' copy in the new surface", !/grown[- ]up/i.test(html));
  mock.reset();
  const env = loadCoach(RELAY); // no WebAuthn injected -> feature detection must fall back
  await unlock(env);
  ok("without WebAuthn: fallback note explains, passkey buttons hidden, waSupported() false",
     env.registry.get("optPasskeyNote").textContent.includes("aren't available in this browser") &&
     env.registry.get("optPasskeyNote").textContent.includes("your password still works") &&
     env.registry.get("optPasskeySignInBtn").style.display === "none" &&
     env.CoachUI._test.waSupported() === false,
     env.registry.get("optPasskeyNote").textContent);
  ok("without WebAuthn: zero passkey endpoint calls", mock.calls.waAuthOptions.length === 0 && mock.calls.waRegOptions.length === 0);
  // with a fake authenticator the ceremonies run end to end (mock relay)
  const env2 = loadCoach(RELAY, { webauthn: makeFakeWebAuthn() });
  await unlock(env2);
  ok("with WebAuthn: fallback note empty, passkey sign-in offered, waSupported() true",
     env2.registry.get("optPasskeyNote").textContent === "" &&
     env2.registry.get("optPasskeySignInBtn").style.display !== "none" &&
     env2.CoachUI._test.waSupported() === true);
  for (const f of env2.registry.get("optPasskeySignInBtn").listeners.click || []) await f();
  await pump(env2, 10);
  ok("passkey sign-in: auth options + verify called, page signed in as the account",
     mock.calls.waAuthOptions.length === 1 && mock.calls.waAuthVerify.length === 1 &&
     env2.CoachUI._test.signedIn() === true &&
     env2.registry.get("optAccountLine").textContent === "Signed in as tester@example.com",
     env2.registry.get("optAccountLine").textContent);
  const vb = mock.calls.waAuthVerify[0] || {};
  ok("verify body carries the ceremony fields as base64url strings",
     vb.id === "mock-cred-1" && typeof vb.rawId === "string" &&
     typeof (vb.response || {}).clientDataJSON === "string" &&
     typeof (vb.response || {}).authenticatorData === "string" &&
     typeof (vb.response || {}).signature === "string",
     JSON.stringify(vb));
  ok("navigator.credentials.get was handed the relay challenge (decoded bytes)",
     !!mock.calls.waGetOpts && mock.calls.waGetOpts.publicKey.rpId === "moorefolio.com" &&
     Object.prototype.toString.call(mock.calls.waGetOpts.publicKey.challenge) === "[object ArrayBuffer]" &&
     mock.calls.waGetOpts.publicKey.challenge.byteLength === 14); // "mock-challenge"
  ok("manage section visible once signed in", env2.registry.get("optPasskeyManage").style.display === "");
  for (const f of env2.registry.get("optAddPasskeyBtn").listeners.click || []) await f();
  await pump(env2, 10);
  const listText = collectText(env2.registry.get("optPasskeyList"));
  ok("add passkey: register options + verify called, list shows the key with a Remove button",
     mock.calls.waRegOptions.length === 1 && mock.calls.waRegVerify.length === 1 &&
     env2.CoachUI._test.getPasskeys().length === 1 &&
     listText.includes("Passkey") && listText.includes("Remove"),
     listText);
  const span = env2.registry.get("optPasskeyList").children[0];
  const rmBtn = span.children[span.children.length - 1];
  for (const f of rmBtn.listeners.click || []) await f();
  await pump(env2, 10);
  ok("remove: endpoint called with the credential id, list back to 'None yet'",
     mock.calls.waRemove.length === 1 && mock.calls.waRemove[0].credential_id === "mock-cred-1" &&
     env2.CoachUI._test.getPasskeys().length === 0 &&
     env2.registry.get("optPasskeyList").textContent === "None yet",
     env2.registry.get("optPasskeyList").textContent);
}

// ---------- Test 11: Phase 3 (Ticket 006) plans, billing, coach picker ----------
async function signIn(env) {
  env.registry.get("optAcctEmail").value = "tester@example.com";
  env.registry.get("optAcctPw").value = ACCT_PW;
  for (const f of env.registry.get("optSignInBtn").listeners.click || []) await f();
  await pump(env, 10);
}
async function signOut(env) {
  for (const f of env.registry.get("optSignOutBtn").listeners.click || []) await f();
  await pump(env, 10);
}
async function test11() {
  begin("11 Phase 3 plans + billing + coach picker");
  ok("drawer has Manage billing + the coach picker rows",
     html.includes('id="optManageBilling"') && html.includes("Manage billing") &&
     html.includes('id="optCoachRow"') && html.includes('id="optCoachSolBtn"') && html.includes('id="optCoachAstraBtn"') &&
     html.includes('id="optBillingNote"') && html.includes('id="optCoachNote"'));
  const coachJs = fs.readFileSync(path.join(branchDir, "coach.js"), "utf8");
  ok("no Elo-gate copy anywhere in the controller", !/1900|eligible|unlock/i.test(coachJs));
  mock.reset();
  const env = loadCoach(RELAY);
  await unlock(env);
  await signIn(env);
  ok("plan line shows the display name (Coach)", env.registry.get("optPlanLine").textContent === "Plan: Coach · tester@example.com",
     env.registry.get("optPlanLine").textContent);
  ok("Manage billing shows when signed in", env.registry.get("optManageBilling").style.display === "");
  ok("coach picker hidden on the Coach plan", env.registry.get("optCoachRow").style.display === "none");
  ok("picker note explains Pro adds Astra (no Elo copy)", env.registry.get("optCoachNote").textContent === "The Pro plan adds a second coach (Astra) for this profile.",
     env.registry.get("optCoachNote").textContent);
  for (const f of env.registry.get("optManageBilling").listeners.click || []) await f();
  await pump(env, 10);
  ok("portal endpoint was called", mock.calls.billing.some((c) => c.url === "/v1/billing/portal"));
  ok("unconfigured billing reads gracefully", env.registry.get("optBillingNote").textContent === "Billing isn't open yet — it arrives with the full launch.",
     env.registry.get("optBillingNote").textContent);
  // Pro: picker appears, Astra selectable, seat follows into the game + review
  mock.acct.plan = "pro";
  await signOut(env);
  await signIn(env);
  ok("plan line shows Pro after re-login", env.registry.get("optPlanLine").textContent === "Plan: Pro · tester@example.com",
     env.registry.get("optPlanLine").textContent);
  ok("coach picker visible on Pro for a Standard profile", env.registry.get("optCoachRow").style.display === "");
  ok("Sol is the default selection", env.registry.get("optCoachSolBtn").classList.contains("sel") &&
     !env.registry.get("optCoachAstraBtn").classList.contains("sel"));
  for (const f of env.registry.get("optCoachAstraBtn").listeners.click || []) await f();
  await pump(env, 10);
  ok("choosing Astra posted the profile coach update",
     mock.calls.acctProfiles.some((c) => c.op === "update" && c.body.coach === "astra"),
     JSON.stringify(mock.calls.acctProfiles));
  ok("Astra shows selected", env.registry.get("optCoachAstraBtn").classList.contains("sel") &&
     !env.registry.get("optCoachSolBtn").classList.contains("sel"));
  mock.turnHandler = (n, body) => {
    const want = body.moves.includes("g4") ? "Qh4" : "e5";
    const cand = body.candidates.find((c) => c.san === want || c.san.startsWith(want));
    return { status: 200, json: { move: (cand || body.candidates[0]).san, coach_line: "Mock line." } };
  };
  env.CoachUI._test.getDossier().calibrated = true;
  env.CoachUI.startGame("rated");
  await pump(env, 10);
  ok("the account session fixed the astra seat", env.CoachUI._test.getAcctCoachSeat() === "astra",
     String(env.CoachUI._test.getAcctCoachSeat()));
  ok("game info title names Astra", env.registry.get("gameInfoTitle").textContent === "You vs. the Coach (Astra)",
     env.registry.get("gameInfoTitle").textContent);
  playSan(env, "f3"); await pump(env);
  playSan(env, "g4"); await pump(env, 60);
  ok("review byline names Astra", env.registry.get("reviewByLine").textContent === "Review by Astra",
     env.registry.get("reviewByLine").textContent);
  mock.billingMode = "ok";
  for (const f of env.registry.get("optManageBilling").listeners.click || []) await f();
  await pump(env, 10);
  ok("configured billing: portal URL handled with the new-tab note",
     env.CoachUI._test.getBillingNote() === "Billing opened in a new tab.", env.CoachUI._test.getBillingNote());
  // BYOK caps shape -> unlimited chip + popover, no numbers
  mock.acct.plan = "byok_weekly";
  mock.acct.caps = { plan: "byok_weekly", unlimited: true, left: null, today_new: 0, saved: 0,
                     daily_credit: 0, ready_cap: 0, next_credit_at: null };
  await signOut(env);
  await signIn(env);
  ok("plan line shows BYOK", env.registry.get("optPlanLine").textContent === "Plan: BYOK · tester@example.com",
     env.registry.get("optPlanLine").textContent);
  ok("chip reads '∞ your key' on the unlimited posture", env.registry.get("gamesChip").textContent === "∞ your key",
     env.registry.get("gamesChip").textContent);
  ok("cost line names the key, no daily limit",
     env.registry.get("gameCostLine").textContent.includes("no daily limit"),
     env.registry.get("gameCostLine").textContent);
  // Lapsed: plan line Paused, honest zero copy, rated start blocked
  mock.acct.plan = "lapsed";
  mock.acct.caps = { left: 0, today_new: 0, saved: 3, daily_credit: 0, ready_cap: 0,
                     next_credit_at: new Date(Date.now() + 3600e3).toISOString() };
  await signOut(env);
  await signIn(env);
  env.CoachUI._test.getDossier().calibrated = true;
  env.CoachUI._test.renderWallet();
  ok("plan line shows Paused", env.registry.get("optPlanLine").textContent === "Plan: Paused · tester@example.com",
     env.registry.get("optPlanLine").textContent);
  ok("zero-credit cost line is honest (no promise of more games)",
     env.registry.get("gameCostLine").textContent === "No plan right now — lessons are still free",
     env.registry.get("gameCostLine").textContent);
  env.CoachUI.startGame("rated");
  ok("rated start blocked on a lapsed account with plain copy",
     env.registry.get("coachTicker").textContent === "No plan right now.",
     env.registry.get("coachTicker").textContent);
}

// ---------- Test 12: Phase 4 (Ticket 006) BYOK + temp accounts ----------
async function clickEl(env, id) {
  for (const f of env.registry.get(id).listeners.click || []) await f();
}
async function test12() {
  begin("12 Phase 4 BYOK + temp accounts");
  ok("drawer has the BYOK section (provider/model/key/test/remove) with the server-storage copy",
     html.includes('id="optByokSection"') && html.includes("Your own AI key (optional)") &&
     html.includes('id="optByokProvider"') && html.includes('id="optByokModel"') &&
     html.includes('id="optByokKey"') && html.includes('id="optByokTestBtn"') && html.includes("Test key") &&
     html.includes('id="optByokRemoveBtn"') && html.includes("Stored on our servers, never in this browser"));
  ok("guest banner + claim form + redeem entry exist; no 'grown-up' copy anywhere",
     html.includes('id="guestBanner"') && html.includes('id="guestKeepBtn"') && html.includes("Keep my progress") &&
     html.includes('id="optGuestClaim"') && html.includes('id="optRedeemCode"') && html.includes('id="optRedeemBtn"') &&
     !/grown[- ]up/i.test(html));
  mock.reset();
  const env = loadCoach(RELAY);
  await unlock(env);
  await signIn(env);
  ok("BYOK state starts empty", env.registry.get("optByokState").textContent === "No key saved",
     env.registry.get("optByokState").textContent);
  const PAGE_KEY = "sk-page-test-1234567890WXYZ";
  env.registry.get("optByokKey").value = PAGE_KEY;
  await clickEl(env, "optByokSaveBtn"); await pump(env, 10);
  const setCall = mock.calls.byok.find((c) => c.op === "set");
  ok("save posted provider+model+key to /v1/byok exactly once",
     !!setCall && setCall.body.key === PAGE_KEY && setCall.body.provider === "openai" && setCall.body.model === "gpt-6-sol",
     JSON.stringify(mock.calls.byok.map((c) => c.op)));
  ok("state shows the masked tail + added date only",
     env.registry.get("optByokState").textContent.startsWith("····WXYZ · added ") &&
     env.CoachUI._test.getByok() && env.CoachUI._test.getByok().tail === "····WXYZ",
     env.registry.get("optByokState").textContent);
  ok("key field cleared after save, and the key is nowhere in sessionStorage",
     env.registry.get("optByokKey").value === "" &&
     ![...env.sessionStorage._map.values()].join(" ").includes(PAGE_KEY));
  await clickEl(env, "optByokTestBtn"); await pump(env, 10);
  ok("test key reports the provider answered",
     env.registry.get("optByokNote").textContent.includes("Your key works"),
     env.registry.get("optByokNote").textContent);
  mock.byokTestMode = "reject";
  await clickEl(env, "optByokTestBtn"); await pump(env, 10);
  ok("test key reports a rejection plainly",
     env.registry.get("optByokNote").textContent.includes("rejected that key"),
     env.registry.get("optByokNote").textContent);
  mock.byokTestMode = "ok";
  // seat + labels on the customer's model
  env.CoachUI._test.getDossier().calibrated = true;
  env.CoachUI.startGame("rated");
  await pump(env, 10);
  ok("account session seat is byok with a key saved",
     env.CoachUI._test.getAcctCoachSeat() === "byok", String(env.CoachUI._test.getAcctCoachSeat()));
  ok("game title names 'your model'",
     env.registry.get("gameInfoTitle").textContent === "You vs. the Coach (your model)",
     env.registry.get("gameInfoTitle").textContent);
  // rejected key mid-game: named plainly, game goes visibly offline
  mock.turnHandler = () => ({ status: 502, json: { error: "byok_key_rejected" } });
  playSan(env, "e4"); await pump(env, 80);
  const coachText = collectText(env.registry.get("coachBody"));
  ok("a rejected key is named in the coach panel (not a generic outage)",
     coachText.includes("Your API key was rejected by your provider"), coachText.slice(-300));
  ok("the game continues visibly offline (Stockfish) after the rejection",
     env.CoachUI._test.getOffline() === true &&
     env.CoachUI._test.getSession().moves.some((m) => m.via === "stockfish-offline"),
     JSON.stringify(env.CoachUI._test.getSession().moves));
  mock.turnHandler = null;
  await clickEl(env, "optByokRemoveBtn"); await pump(env, 10);
  ok("remove clears the key: state empty, mock key gone",
     env.registry.get("optByokState").textContent === "No key saved" && mock.byok === null &&
     env.CoachUI._test.getByok() === null);
  // redeem -> guest -> claim, on a fresh signed-out page
  const env2 = loadCoach(RELAY);
  await unlock(env2);
  env2.registry.get("optRedeemCode").value = "WRONG-CODE";
  await clickEl(env2, "optRedeemBtn"); await pump(env2, 10);
  ok("a bad code is refused with plain copy, still signed out",
     env2.registry.get("optAcctMsg").textContent.includes("That code wasn't recognized") &&
     env2.CoachUI._test.signedIn() === false, env2.registry.get("optAcctMsg").textContent);
  env2.registry.get("optRedeemCode").value = "GOOD-CODE-1234";
  await clickEl(env2, "optRedeemBtn"); await pump(env2, 10);
  ok("a good code signs in as a guest (no email)",
     env2.CoachUI._test.signedIn() === true && env2.CoachUI._test.getAccount().guest === true &&
     env2.CoachUI._test.getAccount().email === null);
  ok("banner shows with the days-left copy; account + plan lines name the test account",
     env2.registry.get("guestBanner").style.display === "" &&
     env2.registry.get("guestBannerText").textContent.includes("test account") &&
     env2.registry.get("guestBannerText").textContent.includes("7 days left") &&
     env2.registry.get("optAccountLine").textContent === "Test account — 7 days left" &&
     env2.registry.get("optPlanLine").textContent === "Plan: Coach (test code) · 7 days left" &&
     env2.registry.get("optGuestClaim").style.display === "",
     env2.registry.get("optAccountLine").textContent + " / " + env2.registry.get("optPlanLine").textContent);
  env2.registry.get("optClaimEmail").value = "claimed@example.com";
  env2.registry.get("optClaimPw").value = "claimed-pass-1";
  await clickEl(env2, "optClaimBtn"); await pump(env2, 10);
  ok("claim converts the guest: banner + claim form hide, account line shows the email, confirmation copy lands",
     env2.CoachUI._test.getAccount().guest === false &&
     env2.registry.get("guestBanner").style.display === "none" &&
     env2.registry.get("optGuestClaim").style.display === "none" &&
     env2.registry.get("optAccountLine").textContent === "Signed in as claimed@example.com" &&
     env2.registry.get("optAcctMsg").textContent.includes("this account is yours now"),
     env2.registry.get("optAccountLine").textContent);
  // expired guest: the session refusal names the ended test account
  const env3 = loadCoach(RELAY);
  await unlock(env3);
  env3.registry.get("optRedeemCode").value = "GOOD-CODE-1234";
  await clickEl(env3, "optRedeemBtn"); await pump(env3, 10);
  mock.guestExpired = true;
  env3.CoachUI._test.getDossier().calibrated = true;
  env3.CoachUI.startGame("rated");
  await pump(env3, 40);
  const coachText3 = collectText(env3.registry.get("coachBody"));
  ok("an expired guest starting a game hears the test account ended (claim path named)",
     coachText3.includes("Your test account's 7 days are up") && coachText3.includes("Keep my progress"),
     coachText3.slice(-300));
  mock.guestExpired = false;
}

const tests = [test1, test2, test3, test4, test5, test6, test7, test8, test9, test10, test11, test12];
for (const t of tests) {
  try { await t(); }
  catch (e) { fail++; if (perTest[current]) perTest[current].fail++;
              console.log("FAIL test threw: " + (e && e.message)); }
}
console.log("\nSUMMARY");
for (const [name, r] of Object.entries(perTest))
  console.log(name + ": " + r.pass + " passed, " + r.fail + " failed");
console.log("TOTAL: " + pass + " passed, " + fail + " failed");
server.close();
process.exit(fail ? 1 : 0);
