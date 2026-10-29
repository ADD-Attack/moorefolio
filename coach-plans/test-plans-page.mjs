// Node harness for the Chess Coach PLANS page (Ticket 006 Phase 3).
// Static copy asserts on index.html + a vm + fake-DOM load of plans.js,
// following the sandbox pattern used by the other coach page suites:
// fake elements in a registry, fake sessionStorage / fetch / location.
import fs from "node:fs";
import vm from "node:vm";
import path from "node:path";
import { fileURLToPath } from "node:url";

const dir = path.dirname(fileURLToPath(import.meta.url));
const html = fs.readFileSync(path.join(dir, "index.html"), "utf8");
const js = fs.readFileSync(path.join(dir, "plans.js"), "utf8");

let pass = 0, fail = 0;
function ok(label, cond, detail) {
  if (cond) pass++; else fail++;
  console.log((cond ? "PASS " : "FAIL ") + label + (detail !== undefined ? " | " + detail : ""));
}

// ---------- static asserts ----------
const EXACT_STRINGS = [
  "A chess coach that plays you, talks you through it, and remembers you.",
  "Have a test code?",
  "Start playing",
  "It plays real moves",
  "A chess engine checks every one",
  "It explains as you go",
  "It remembers your games",
  "Never played? 8 short lessons, a coach that speaks every step. Any age.",
  "Know the game? Rated games and a review after each.",
  "One account, a profile for everyone in the house.",
  "2 months free",
  "Deeper coaching",
  "Sol, a patient coach for every level · 3 new games a day · Skip a day, they wait: up to 8 ready · Reviews by Sol.",
  "Everything in Coach, plus Astra · 10 a day, up to 17 ready · Choose Sol or Astra · Reviews by Astra",
  "Players around 1900 and up tend to get the most from Astra's deeper feedback.",
  "Already pay for an AI model like Claude or ChatGPT? Bring your own key: $5/week (≈$21.67/mo), no daily game limit. On its own or added to any plan.",
  "What's an API key?",
  "Not sure? You don't need this.",
  "Accounts belong to adults. New Player profiles store a display name only. No ads. No chat with strangers. Ever.",
  "Got a test code? Play free for 7 days. Keep your progress before it ends and your rating, dossier and games stay yours.",
  "Can I cancel anytime?",
  "cancel anytime",
  "up to 8 ready on Coach, 17 on Pro",
  "The model your plan uses — Sol on Coach, Astra on Pro, your own model with BYOK.",
  "keys are stored on our servers, never in your browser",
];
for (const s of EXACT_STRINGS) ok("exact string present: " + s.slice(0, 60), html.includes(s));

ok("title is exact", html.includes("<title>Chess Coach — Plans</title>"));
ok("noindex meta present", html.includes('<meta name="robots" content="noindex, nofollow">'));
ok("header test-code link points at #test-code", html.includes('<a href="#test-code">Have a test code?</a>'));
ok("Start playing links to /coach-you/", html.includes('href="/coach-you/"'));
ok("Pass 2 (d)1: hero scrolls to the two-ways fork; each way card carries its own start button",
   html.includes('id="heroStartBtn" href="#two-ways"') && html.includes('id="two-ways"') &&
   html.includes('<a class="btn" href="/coach-kids/">Start as a New Player</a>') &&
   html.includes('<a class="btn" href="/coach-you/">Start playing</a>'));
ok("Pass 2 (d)3: the parked line stands above the billing toggle",
   html.includes('id="parkedLine"') && html.includes("Plans aren't on sale yet — your beta access keeps working.") &&
   html.indexOf('id="parkedLine"') < html.indexOf('id="toggleMonthly"'));
ok("Pass 2 (d)7: reduced-motion demo captions ship as a list, revealed only under the media query",
   html.includes('id="demoStepsList"') && html.includes("prefers-reduced-motion: reduce") &&
   html.includes("Checkmate — that's the game."));
ok("BYOK disclosure is a <details> element ending with the not-sure sentence",
   /<details>[\s\S]*?Not sure\? You don't need this\.<\/p>\s*<\/details>/.test(html));
ok("test-code band present with id", html.includes('id="test-code"'));

for (const plan of ["coach", "pro", "byok_weekly"]) {
  ok('data-plan="' + plan + '" button present', html.includes('data-plan="' + plan + '"'));
}
ok("Choose Coach / Choose Pro / Bring your own key labels present",
   html.includes("Choose Coach") && html.includes("Choose Pro") && html.includes("Bring your own key"));

// BYOK band: its own band element, after the Pro card, outside plan cards.
const proIdx = html.indexOf('data-plan="pro"');
const byokIdx = html.indexOf('id="byokBand"');
const byokTextIdx = html.indexOf("Already pay for an AI model");
const planCardsEndIdx = html.indexOf('id="billingNote"');
ok("BYOK band has its own id=\"byokBand\"", byokIdx !== -1);
ok("BYOK band comes after the Pro card", byokIdx > proIdx && byokTextIdx > proIdx,
   "pro=" + proIdx + " byokBand=" + byokIdx);
ok("BYOK band is outside the plan-cards container (after the billing note that follows it)",
   byokIdx > planCardsEndIdx && planCardsEndIdx > proIdx,
   "billingNote=" + planCardsEndIdx + " byokBand=" + byokIdx);

// ---------- forbidden strings ----------
const FORBIDDEN = ["1900+", "Most popular", "requires", "unlock", "eligible",
  "advanced only", "recommended rating", "grown-up", "grown up", "in hand"];
for (const f of FORBIDDEN) {
  ok('forbidden absent from index.html: "' + f + '"', !html.toLowerCase().includes(f.toLowerCase()));
  ok('forbidden absent from plans.js: "' + f + '"', !js.toLowerCase().includes(f.toLowerCase()));
}
// "Kids" must never appear as a mode name in page copy. The one lawful
// occurrence in plans.js is inside the required account storage key
// "chessCoachAccount.kids" — an identifier, not copy — so strip the
// account keys before checking the script.
ok('forbidden absent from index.html: "Kids"', !html.includes("Kids"));
{
  let jsCopy = js;
  for (const k of ["chessCoachAccount.you", "chessCoachAccount.ben", "chessCoachAccount.test",
                   "chessCoachAccount.kids", "chessCoachAccount.beginnertest"]) {
    jsCopy = jsCopy.split(k).join("");
  }
  ok('forbidden absent from plans.js copy (outside account keys): "Kids"', !jsCopy.includes("Kids"));
}
ok("standalone word absent from index.html (word-boundary check)", !/\bbank\b/i.test(html));
ok("standalone word absent from plans.js (word-boundary check)", !/\bbank\b/i.test(js));

// ---------- plans.js static wiring ----------
const ACCOUNT_KEYS = ["chessCoachAccount.you", "chessCoachAccount.ben", "chessCoachAccount.test",
  "chessCoachAccount.kids", "chessCoachAccount.beginnertest"];
for (const k of ACCOUNT_KEYS) ok("plans.js reads session key " + k, js.includes(k));
ok("plans.js posts to the relay checkout URL",
   js.includes("https://abraham-1.tail629694.ts.net/v1/billing/checkout"));
ok("plans.js posts to the relay redeem URL (Phase 4) and no longer carries the placeholder note",
   js.includes("https://abraham-1.tail629694.ts.net/v1/redeem") &&
   !js.includes("Test codes aren't live yet"));

// ---------- fake DOM ----------
function makeStorage(preset) {
  const m = new Map(Object.entries(preset || {}));
  return { getItem: (k) => (m.has(k) ? m.get(k) : null),
           setItem: (k, v) => m.set(k, String(v)),
           removeItem: (k) => m.delete(k), _map: m };
}
function makeEl(tag) {
  const el = { tag: tag || "div", children: [], style: {}, listeners: {}, value: "", checked: false,
               disabled: false, dataset: {}, _cls: new Set() };
  let text = "", htmlText = "";
  Object.defineProperty(el, "textContent", {
    get: () => text,
    set: (v) => { text = String(v); htmlText = String(v); },
  });
  Object.defineProperty(el, "innerHTML", {
    get: () => htmlText,
    set: (v) => { htmlText = String(v); text = String(v).replace(/<[^>]*>/g, ""); },
  });
  el.classList = { add: (c) => el._cls.add(c), remove: (c) => el._cls.delete(c),
    toggle: (c, force) => { const on = force === undefined ? !el._cls.has(c) : !!force; on ? el._cls.add(c) : el._cls.delete(c); },
    contains: (c) => el._cls.has(c) };
  el.addEventListener = (n, f) => { (el.listeners[n] = el.listeners[n] || []).push(f); };
  el.getAttribute = (n) => (n === "data-plan" ? (el.dataset.plan || null) : null);
  return el;
}

function loadPlans(opts) {
  const registry = new Map();
  for (const m of html.matchAll(/ id="([^"]+)"/g)) {
    if (!registry.has(m[1])) { const e = makeEl("div"); registry.set(m[1], e); }
  }
  const planButtons = [];
  for (const m of html.matchAll(/<button\b[^>]*>/g)) {
    const tag = m[0];
    const idM = tag.match(/ id="([^"]+)"/);
    const planM = tag.match(/ data-plan="([^"]+)"/);
    if (planM && idM && registry.has(idM[1])) {
      const e = registry.get(idM[1]);
      e.dataset.plan = planM[1];
      planButtons.push(e);
    }
  }
  const sessionStorage = makeStorage(opts && opts.session);
  const locationObj = { href: "" };
  const sandbox = {
    console, Promise, JSON,
    setTimeout, clearTimeout, setInterval: () => 1, clearInterval: () => {},
    fetch: opts && opts.fetch,
    sessionStorage,
    location: locationObj,
    document: {
      getElementById: (id) => registry.get(id) || null,
      querySelectorAll: (sel) => (sel === "[data-plan]" ? planButtons.slice() : []),
    },
  };
  vm.createContext(sandbox);
  vm.runInContext(js, sandbox, { filename: "plans.js" });
  return { registry, sessionStorage, location: locationObj, planButtons };
}
async function fireClick(el) {
  for (const f of (el && el.listeners.click) || []) await f({ preventDefault: () => {} });
}
function countingFetch(handler) {
  const calls = [];
  const fn = async (url, opts) => { calls.push({ url, opts }); return handler(url, opts); };
  fn.calls = calls;
  return fn;
}
const TOKEN_PRESET = { "chessCoachAccount.you": JSON.stringify({ token: "tok-test-1" }) };

// ---------- behavioral ----------
async function behavior() {
  // (1) toggle swaps prices annual <-> monthly
  {
    const fetch = countingFetch(async () => ({ status: 200, json: async () => ({}) }));
    const env = loadPlans({ fetch });
    ok("toggle: Coach starts at $12 /mo",
       env.registry.get("coachPrice").textContent === "$12" && env.registry.get("coachSuffix").textContent === "/mo",
       env.registry.get("coachPrice").textContent + env.registry.get("coachSuffix").textContent);
    await fireClick(env.registry.get("toggleAnnual"));
    ok("toggle: annual swaps Coach price to $120 /yr",
       env.registry.get("coachPrice").textContent === "$120" && env.registry.get("coachSuffix").textContent === "/yr",
       env.registry.get("coachPrice").textContent + env.registry.get("coachSuffix").textContent);
    ok("toggle: annual swaps Pro price to $290 /yr",
       env.registry.get("proPrice").textContent === "$290" && env.registry.get("proSuffix").textContent === "/yr",
       env.registry.get("proPrice").textContent + env.registry.get("proSuffix").textContent);
    await fireClick(env.registry.get("toggleMonthly"));
    ok("toggle: monthly swaps Coach price back to $12 /mo",
       env.registry.get("coachPrice").textContent === "$12" && env.registry.get("coachSuffix").textContent === "/mo",
       env.registry.get("coachPrice").textContent + env.registry.get("coachSuffix").textContent);
  }
  // (2) plan click with no token: create-account note, no fetch
  {
    const fetch = countingFetch(async () => ({ status: 200, json: async () => ({}) }));
    const env = loadPlans({ fetch });
    const proBtn = env.planButtons.find((b) => b.dataset.plan === "pro");
    await fireClick(proBtn);
    const note = env.registry.get("billingNote").textContent;
    ok("no token: the parked note shows instead of the create-account pointer (Pass 2 (d)3)", note === "Plans aren't on sale yet — your beta access keeps working.", note);
    ok("no token: the parked note stands alone, no coach-page link appended (Pass 2 (d)3)", !note.includes("Open a coach page"), note);
  }
  // (3) token + 503 billing_configured:false: exact note, body {plan:pro, interval:monthly}
  {
    const fetch = countingFetch(async () => ({ status: 503, json: async () => ({ billing_configured: false }) }));
    const env = loadPlans({ fetch, session: TOKEN_PRESET });
    const proBtn = env.planButtons.find((b) => b.dataset.plan === "pro");
    await fireClick(proBtn);
    const note = env.registry.get("billingNote").textContent;
    ok("503: exact billing-not-open note shown",
       note === "Plans aren't on sale yet — your beta access keeps working.", note);
    ok("503: exactly one fetch made", fetch.calls.length === 1, "calls=" + fetch.calls.length);
    if (fetch.calls.length === 1) {
      const call = fetch.calls[0];
      ok("503: fetch went to the checkout URL", call.url === "https://abraham-1.tail629694.ts.net/v1/billing/checkout", call.url);
      ok("503: Authorization header carries the token",
         !!(call.opts && call.opts.headers && call.opts.headers.Authorization === "Bearer tok-test-1"),
         JSON.stringify(call.opts && call.opts.headers));
      const body = JSON.parse(call.opts.body);
      ok("503: fetch body was {plan:\"pro\", interval:\"monthly\"}",
         body.plan === "pro" && body.interval === "monthly", JSON.stringify(body));
    }
  }
  // (4) BYOK click sends interval weekly (and a returned url navigates)
  {
    const fetch = countingFetch(async () => ({ status: 200, json: async () => ({ url: "https://checkout.example/session-1" }) }));
    const env = loadPlans({ fetch, session: TOKEN_PRESET });
    const byokBtn = env.planButtons.find((b) => b.dataset.plan === "byok_weekly");
    await fireClick(byokBtn);
    ok("byok: exactly one fetch made", fetch.calls.length === 1, "calls=" + fetch.calls.length);
    if (fetch.calls.length === 1) {
      const body = JSON.parse(fetch.calls[0].opts.body);
      ok("byok: fetch body was {plan:\"byok_weekly\", interval:\"weekly\"}",
         body.plan === "byok_weekly" && body.interval === "weekly", JSON.stringify(body));
    }
    ok("byok: returned checkout url navigates", env.location.href === "https://checkout.example/session-1", env.location.href);
  }
  // (5) redeem with an empty input: plain note, no fetch
  {
    const fetch = countingFetch(async () => ({ status: 200, json: async () => ({}) }));
    const env = loadPlans({ fetch });
    await fireClick(env.registry.get("redeemBtn"));
    ok("redeem empty: 'enter your code' note, NO fetch made",
       env.registry.get("redeemNote").textContent === "Enter your test code first." && fetch.calls.length === 0,
       env.registry.get("redeemNote").textContent);
  }
  // (6) redeem with a bad code: one POST to /v1/redeem, 401 copy
  {
    const fetch = countingFetch(async () => ({ status: 401, json: async () => ({ error: "code not recognized" }) }));
    const env = loadPlans({ fetch });
    env.registry.get("testCodeInput").value = "  NOPE-CODE  ";
    await fireClick(env.registry.get("redeemBtn"));
    ok("redeem bad code: exactly one fetch, to the redeem URL, trimmed code in the body",
       fetch.calls.length === 1 && fetch.calls[0].url === "https://abraham-1.tail629694.ts.net/v1/redeem" &&
       JSON.parse(fetch.calls[0].opts.body).code === "NOPE-CODE",
       "calls=" + fetch.calls.length);
    ok("redeem bad code: not-recognized copy, nothing stored",
       env.registry.get("redeemNote").textContent === "That code wasn't recognized — check it and try again." &&
       env.sessionStorage._map.size === 0, env.registry.get("redeemNote").textContent);
  }
  // (7) redeem with a good code: guest blob stored under EVERY coach key
  {
    const fetch = countingFetch(async () => ({ status: 200, json: async () => ({
      token: "guest-tok-1", exp: 1799999999,
      account: { email: null, plan: "coach", guest: true, guest_days_left: 7,
                 guest_expires_at: "2026-11-03T00:00:00.000Z" },
      profiles: [], active_profile_id: null, caps: {} }) }));
    const env = loadPlans({ fetch });
    env.registry.get("testCodeInput").value = "GOOD-CODE-1234";
    await fireClick(env.registry.get("redeemBtn"));
    const note = env.registry.get("redeemNote").textContent;
    ok("redeem good code: accepted copy with the coach link",
       note.includes("Test code accepted — you're in for 7 days. Choose how to play:") && note.includes("New Player") && note.includes("Standard"), note);
    let allStored = true, parsed = null;
    for (const k of ACCOUNT_KEYS) {
      const raw = env.sessionStorage.getItem(k);
      if (!raw) { allStored = false; break; }
      parsed = JSON.parse(raw);
    }
    ok("redeem good code: the guest session blob sits under all five account keys",
       allStored && env.sessionStorage._map.size === 5, "keys=" + env.sessionStorage._map.size);
    ok("redeem good code: blob carries token + guest flag + days left (no email)",
       !!parsed && parsed.token === "guest-tok-1" && parsed.guest === true &&
       parsed.guest_days_left === 7 && parsed.email === null && parsed.plan === "coach",
       JSON.stringify(parsed));
  }
  // (8) redeem rate-limited: 429 copy
  {
    const fetch = countingFetch(async () => ({ status: 429, json: async () => ({ error: "redemption locked" }) }));
    const env = loadPlans({ fetch });
    env.registry.get("testCodeInput").value = "SOME-CODE-1234";
    await fireClick(env.registry.get("redeemBtn"));
    ok("redeem 429: slow-down copy",
       env.registry.get("redeemNote").textContent === "Too many tries — wait a bit and try again.",
       env.registry.get("redeemNote").textContent);
  }
}

await behavior();

console.log("\nRESULT: " + pass + " passed, " + fail + " failed");
process.exitCode = fail ? 1 : 0;
