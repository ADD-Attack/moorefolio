// Node harness for the Chess Coach page (Ticket 004).
// Loads the page inline scripts plus coach-core.js, sf-adapter.js and
// coach.js into a vm context with a hand-rolled DOM stub.
import fs from "node:fs";
import vm from "node:vm";
import path from "node:path";
import { fileURLToPath } from "node:url";

const dir = path.dirname(fileURLToPath(import.meta.url));
const html = fs.readFileSync(path.join(dir, "index.html"), "utf8");
const inlineScripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);

const IDS = ["board", "boardWrap", "branchLine", "capturedByWhite", "capturedByBlack",
  "whiteName", "blackName", "turnLine", "newGameBtn", "practiceBtn", "hintBtn",
  "resetBtn", "flipBtn", "soundBtn", "coachBody", "coachState", "coachTicker", "movesBody",
  "reviewPanel", "reviewBody", "dossierBody", "alertBody", "promoModal",
  "promoChoices", "gate", "gateInput", "gateMsg", "gateBtn"];

function makeStorage() {
  const m = new Map();
  return { getItem: (k) => (m.has(k) ? m.get(k) : null),
           setItem: (k, v) => m.set(k, String(v)),
           removeItem: (k) => m.delete(k) };
}

function loadCoach(responder) {
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
  const win = { __coachManualInit: true, _listeners: {},
                addEventListener: (n, f) => { win._listeners[n] = f; } };
  const sandbox = {
    console, setTimeout, clearTimeout, clearInterval: () => {},
    setInterval: (fn) => { pollFn = fn; return 1; },
    document: { getElementById: (id) => registry.get(id) || null,
                createElement: (t) => makeEl(t), body: makeEl("body") },
    localStorage: makeStorage(), sessionStorage: makeStorage(),
    window: win,
  };
  vm.createContext(sandbox);
  const run = (code) => vm.runInContext(code, sandbox);
  for (const code of inlineScripts) run(code);
  for (const f of ["coach-core.js", "sf-adapter.js", "coach.js"])
    vm.runInContext(fs.readFileSync(path.join(dir, f), "utf8"), sandbox, { filename: f });

  const C = run("CoachCore");
  const CoachUI = run("CoachUI");
  const fakeSf = {
    start: async () => {},
    analyze: async (fen, multipv) => {
      // CoachCore has no FEN parser, so rebuild state by replaying the
      // page history, which coach.js treats as the source of truth.
      const st = C.stateFromSans(run("history.slice()"));
      const legal = C.allLegalState(st, st.turn);
      const lines = legal.slice(0, multipv || 10).map((m) => ({ uci: C.uciFor(m), cp: 10, mate: null }));
      return { lines, bestmove: lines.length ? lines[0].uci : null };
    },
    evaluateWhite: async () => 10,
  };
  if (responder) CoachUI.init({ sf: fakeSf, responder });
  return { run, C, CoachUI, fakeSf, registry,
           poll: () => { if (pollFn) pollFn(); },
           history: () => run("history.slice()") };
}

async function pump(env, rounds = 80) {
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

// ---------- Test 1: base game unchanged ----------
async function test1() {
  begin("1 base game");
  const env = loadCoach(null);
  const boardEl = env.registry.get("board");
  ok("64 squares render", boardEl.children.length === 64, "squares=" + boardEl.children.length);
  let pieces = 0;
  for (const sq of boardEl.children) for (const ch of sq.children) if (ch.classList.contains("piece")) pieces++;
  ok("32 pieces render", pieces === 32, "pieces=" + pieces);
  ok("allLegal('w') is 20 at start", env.run("allLegal('w').length") === 20,
     "allLegal=" + env.run("allLegal('w').length"));
  env.run("tryMove(52, 36)"); // e2-e4
  env.run("tryMove(12, 28)"); // e7-e5
  const hist = env.history();
  ok("e2-e4 then e7-e5 works and records SAN history",
     JSON.stringify(hist) === JSON.stringify(["e4", "e5"]), "history=" + JSON.stringify(hist));
}

// ---------- Test 2: stub game end to end ----------
async function test2() {
  begin("2 stub game end to end");
  const packets = [];
  const responder = async (packet) => {
    packets.push(packet);
    return { move: packet.candidates[0].san, coach_line: "Stub coach move." };
  };
  const env = loadCoach(responder);
  env.CoachUI.startGame("rated");
  playSan(env, "e4"); await pump(env);
  playSan(env, "Nf3"); await pump(env);
  playSan(env, "Bc4"); await pump(env);
  const hist = env.history();
  info("history after 3 scripted white moves: " + JSON.stringify(hist));
  ok("at least 6 plies complete", hist.length >= 6, "plies=" + hist.length);
  const session = env.CoachUI._test.getSession();
  ok("no failsafe alerts", session.alerts.length === 0, "alerts=" + JSON.stringify(session.alerts));
  ok("responder received at least 3 packets", packets.length >= 3, "packets=" + packets.length);
  ok("every packet had 1..10 candidates",
     packets.every((p) => p.candidates.length >= 1 && p.candidates.length <= 10),
     "lengths=" + packets.map((p) => p.candidates.length).join(","));
  ok("every candidate has ONLY {san, uci} keys",
     packets.every((p) => p.candidates.every((c) => Object.keys(c).sort().join(",") === "san,uci")),
     "sample keys=" + (packets.length ? Object.keys(packets[0].candidates[0]).sort().join(",") : "none"));
}

// ---------- Test 3: failsafe reprompt ----------
async function test3() {
  begin("3 failsafe reprompt");
  let calls = 0, legalSan = null;
  const responder = async (packet) => {
    calls++;
    if (calls === 1) return { move: "Qh5" };
    legalSan = packet.candidates[0].san;
    return { move: legalSan };
  };
  const env = loadCoach(responder);
  env.CoachUI.startGame("rated");
  playSan(env, "e4"); await pump(env);
  const hist = env.history();
  const session = env.CoachUI._test.getSession();
  info("history: " + JSON.stringify(hist) + " alerts: " + JSON.stringify(session.alerts.map((a) => a.kind)));
  ok("illegal Qh5 never entered history", !hist.includes("Qh5"), "history=" + JSON.stringify(hist));
  ok("exactly one FAILSAFE alert logged", session.alerts.length === 1,
     "alerts=" + session.alerts.length);
  ok("reprompt move was applied", hist.length === 2 && hist[1] === legalSan,
     "history[1]=" + hist[1] + " repromptSan=" + legalSan);
}

// ---------- Test 4: failsafe double failure ----------
async function test4() {
  begin("4 failsafe double failure");
  const responder = async () => ({ move: "Qh5" });
  const env = loadCoach(responder);
  env.CoachUI.startGame("rated");
  playSan(env, "e4"); await pump(env);
  const hist = env.history();
  const session = env.CoachUI._test.getSession();
  info("history: " + JSON.stringify(hist) + " alerts: " + JSON.stringify(session.alerts.map((a) => a.kind)));
  ok("fallback move was applied", hist.length === 2, "history=" + JSON.stringify(hist));
  ok("sessionRecord.flagged is true", session.flagged === true, "flagged=" + session.flagged);
  ok("two alerts exist", session.alerts.length === 2, "alerts=" + session.alerts.length);
}

// ---------- Test 5: blunder review classification ----------
async function test5() {
  begin("5 blunder review");
  const env = loadCoach(null);
  const C = env.C;
  const sans = ["e4", "e5", "Bc4", "Nc6", "Qh5", "Nf6", "Qxe5+", "Nxe5"];
  const plies = [];
  for (let i = 0; i < sans.length; i++) {
    const before = C.stateFromSans(sans.slice(0, i));
    plies.push({ san: sans[i], mover: i % 2 === 0 ? "w" : "b",
                 stateBefore: before, move: C.parseSan(before, sans[i]) });
  }
  const trail = [0, 30, 20, 30, 25, 30, 30];
  const scoreLog = [];
  for (let i = 0; i < 6; i++) {
    const mover = i % 2 === 0 ? "w" : "b";
    scoreLog.push({ ply: i, san: sans[i], mover,
                    swing: (trail[i + 1] - trail[i]) * (mover === "w" ? 1 : -1) });
  }
  // Judged post-recapture per spec: +30 before Qxe5+, -550 after Nxe5.
  scoreLog.push({ ply: 6, san: "Qxe5+", mover: "w", swing: -550 - 30 });
  scoreLog.push({ ply: 7, san: "Nxe5", mover: "b", swing: 0 });
  const review = C.buildReview(scoreLog, plies, "w", "test game", 800, 800);
  info("moments: " + JSON.stringify(review.moments));
  info("focusClass=" + review.focusClass + " focusLesson=" + review.focusLesson);
  const qxe5 = review.moments.find((m) => m.ply === 6);
  ok("review moments include the Qxe5 ply", !!qxe5, "moments=" + JSON.stringify(review.moments.map((m) => m.ply)));
  ok("Qxe5 ply reasonClass is hangs-piece", !!qxe5 && qxe5.reasonClass === "hangs-piece",
     "actual class=" + (qxe5 ? qxe5.reasonClass : "none"));
  ok("focus lesson is the hangs-piece lesson",
     review.focusClass === "hangs-piece" && review.focusLesson === C.LESSON_BY_CLASS["hangs-piece"],
     "focusClass=" + review.focusClass);
}

// ---------- Test 6: dossier after a finished game ----------
async function test6() {
  begin("6 dossier");
  const env = loadCoach(async (packet) => ({ move: packet.candidates[0].san }));
  const gamesBefore = env.CoachUI._test.getDossier().games;
  const eloBefore = env.CoachUI._test.getDossier().elo;
  env.CoachUI.startGame("rated");
  playSan(env, "f3");
  playSan(env, "e5");
  playSan(env, "g4");
  playSan(env, "Qh4");
  info("gameOver=" + env.run("gameOver") + " history=" + JSON.stringify(env.history()));
  ok("Fool's Mate ends the page game", env.run("gameOver") === true);
  await pump(env, 40);
  const dossier = env.CoachUI._test.getDossier();
  const expectedElo = env.C.eloUpdate(eloBefore, eloBefore + 50, 0);
  info("dossier games=" + dossier.games + " elo=" + dossier.elo + " expectedElo=" + expectedElo);
  ok("dossier.games incremented", dossier.games === gamesBefore + 1,
     "before=" + gamesBefore + " after=" + dossier.games);
  ok("elo changed per CoachCore.eloUpdate", dossier.elo === expectedElo,
     "elo=" + dossier.elo + " expected=" + expectedElo);
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
  const env = loadCoach(async (packet) => ({ move: packet.candidates[0].san, coach_line: "Base mock line." }));
  await pump(env, 20);
  const ticker = () => env.registry.get("coachTicker").textContent;
  ok("setCoachState mirrors into the ticker",
     ticker() === "Coach is ready. Start a new game when you are.", "ticker=" + ticker());
  env.CoachUI.startGame("rated");
  ok("coachLine mirrors into the ticker (game start)",
     ticker().includes("New game.") && ticker().includes("Your move."), "ticker=" + ticker());
  // NB: the stub's escapeHtml returns "" (its div has no real innerHTML),
  // so a relay coach_line reaches coachLine as just "<b>Coach:</b> " here;
  // the game-over line is fully internal text and exercises the same path.
  playSan(env, "f3");
  playSan(env, "e5");
  playSan(env, "g4");
  playSan(env, "Qh4");
  await pump(env, 60);
  ok("latest coach line wins the ticker (tags stripped, text only)",
     ticker().startsWith("Game over.") && ticker().includes("Your review session is below the board."),
     "ticker=" + ticker());
}

const tests = [test1, test2, test3, test4, test5, test6, test7];
for (const t of tests) {
  try { await t(); }
  catch (e) { fail++; if (perTest[current]) perTest[current].fail++;
              console.log("FAIL test threw: " + (e && e.message)); }
}
console.log("\nSUMMARY");
for (const [name, r] of Object.entries(perTest))
  console.log(name + ": " + r.pass + " passed, " + r.fail + " failed");
console.log("TOTAL: " + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
