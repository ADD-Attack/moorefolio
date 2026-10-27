// test-core.mjs — deterministic checks for coach-core.js.
// Every number BETA-REPORT.md claims for the core comes from this
// script's output (test-core-output.txt). Rerun: node test-core.mjs
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const C = require("./coach-core.js");
let pass = 0, fail = 0;
const ok = (name, cond, detail) => { cond ? pass++ : fail++; console.log((cond ? "PASS " : "FAIL ") + name + (detail ? " | " + detail : "")); };

ok("startpos FEN exact", C.fenFromState(C.startState()) === "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");
ok("20 opening legal moves", C.allLegalState(C.startState(), "w").length === 20);
const mate = C.stateFromSans(["e4", "e5", "Bc4", "Nc6", "Qh5", "Nf6", "Qxf7#"]);
ok("Scholar's mate line ends with 0 legal replies", C.allLegalState(mate, mate.turn).length === 0);

const st = C.stateFromSans(["e4", "e5"]);
const legal = C.allLegalState(st, "w");
const lines = legal.slice(0, 12).map((m, i) => ({ uci: C.uciFor(m), cp: 50 - i * 30, mate: null }));
const cand850 = C.pruneCandidates(st, lines, 850);
const cand2200 = C.pruneCandidates(st, lines, 2200);
ok("pruning at 850 caps at 10", cand850.length === 10, "n=" + cand850.length);
ok("pruning at 2200 narrows to 3", cand2200.length === 3, "n=" + cand2200.length);
ok("candidates carry only san and uci", cand850.every((c) => Object.keys(c).sort().join() === "san,uci"));

ok("failsafe: Ke2 after e4 e5 is not-in-candidates", C.validateCoachMove(st, "Ke2", cand850).reason === "not-in-candidates");
ok("failsafe: Qh5 in startpos is illegal-move", C.validateCoachMove(C.startState(), "Qh5", null).reason === "illegal-move");
ok("failsafe: a candidate passes", C.validateCoachMove(st, cand850[0].san, cand850).ok === true, cand850[0].san);

ok("eloUpdate win at 800 vs 850 is 818", C.eloUpdate(800, 850, 1) === 818);
ok("eloFromScoreRate(0.75) is +191", C.eloFromScoreRate(0.75) === 191);
ok("window widens as Elo falls", C.windowForElo(800) > C.windowForElo(1400) && C.windowForElo(1400) > C.windowForElo(2200),
   [800, 1400, 2200].map((e) => C.windowForElo(e)).join("/"));

const blunder = C.stateFromSans(["e4", "e5", "Bc4", "Nc6", "Qh5", "Nf6"]);
ok("classifier: Qxe5+ is hangs-piece", C.classifyPly(blunder, C.parseSan(blunder, "Qxe5+")) === "hangs-piece");
const bishop = C.stateFromSans(["e4", "d6", "Bc4", "Nf6", "Nf3", "g6", "Ng5", "e6"]);
ok("classifier: Bxe6 is hangs-piece", C.classifyPly(bishop, C.parseSan(bishop, "Bxe6")) === "hangs-piece");
ok("classifier: Nf3 is positional-swing", C.classifyPly(st, C.parseSan(st, "Nf3")) === "positional-swing");

function runCalibration(trail) { let t = 800; for (let m = 10; m <= trail.length; m += 10) { const w = trail.slice(m - 10, m); t = C.calibrationStep(t, w.reduce((a, b) => a + b, 0) / w.length); } return t; }
ok("calibration: even trail rests at 800", runCalibration(Array(40).fill(0)) === 800);
ok("calibration: +250 trail rests at 1200", runCalibration(Array(40).fill(250)) === 1200);
ok("calibration: -250 trail rests at the 400 floor", runCalibration(Array(40).fill(-250)) === 400);

console.log("TOTAL: " + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
