// sf-adapter.js — promise wrapper over a Stockfish UCI worker.
// The engine is the page's silent scorer + candidate pruner.
// It is never shown to the player and never named to the coach (LLM).
"use strict";
const SF = (() => {
  let worker = null, readyPromise = null, busy = Promise.resolve();
  const listeners = new Set();
  function dispatch(line) { for (const f of [...listeners]) f(line); }
  function start(url) {
    if (readyPromise) return readyPromise;
    readyPromise = new Promise((resolve, reject) => {
      try {
        worker = new Worker(url);
      } catch (e) { reject(e); return; }
      worker.onmessage = (e) => dispatch(typeof e.data === "string" ? e.data : String(e.data));
      worker.onerror = (e) => reject(new Error("stockfish worker error: " + (e.message || e)));
      const onLine = (line) => {
        if (line === "uciok") send("isready");
        if (line === "readyok") { listeners.delete(onLine); resolve(); }
      };
      listeners.add(onLine);
      send("uci");
      setTimeout(() => reject(new Error("stockfish start timeout")), 20000);
    });
    return readyPromise;
  }
  function send(cmd) { worker.postMessage(cmd); }
  function setOption(name, value) { send("setoption name " + name + (value !== undefined ? " value " + value : "")); }
  // Serialize all engine work: UCI is a single conversation.
  function job(fn) { const run = busy.then(fn, fn); busy = run.catch(() => {}); return run; }
  function analyze(fen, multipv, depth) {
    return job(() => new Promise((resolve) => {
      const lines = new Map();
      let best = null;
      const onLine = (line) => {
        if (line.startsWith("info") && line.includes(" multipv ")) {
          const pv = / pv ([a-h][1-8][a-h][1-8][qrbn]?)/.exec(line);
          const mpv = / multipv (\d+)/.exec(line);
          const cpM = / score cp (-?\d+)/.exec(line);
          const mateM = / score mate (-?\d+)/.exec(line);
          if (pv && mpv) lines.set(Number(mpv[1]), {
            uci: pv[1], cp: cpM ? Number(cpM[1]) : null,
            mate: mateM ? Number(mateM[1]) : null,
          });
        }
        if (line.startsWith("bestmove")) {
          best = (line.split(/\s+/)[1] || null);
          listeners.delete(onLine);
          resolve({ lines: [...lines.entries()].sort((a, b) => a[0] - b[0]).map(([, v]) => v), bestmove: best });
        }
      };
      listeners.add(onLine);
      setOption("MultiPV", multipv);
      send("position fen " + fen);
      send("go depth " + depth);
      setTimeout(() => { listeners.delete(onLine); resolve({ lines: [...lines.values()], bestmove: best }); }, 30000);
    }));
  }
  // Position score in centipawns, WHITE point of view. Mate -> +-100000.
  async function evaluateWhite(fen, depth) {
    const turn = fen.split(" ")[1] || "w";
    const { lines } = await analyze(fen, 1, depth || 10);
    if (!lines.length) return null;
    let s = lines[0].mate !== null && lines[0].mate !== undefined
      ? (lines[0].mate > 0 ? 100000 : -100000) : (lines[0].cp || 0);
    return turn === "w" ? s : -s;
  }
  async function bestmoveAtElo(fen, elo, depth) {
    return job(() => new Promise((resolve) => {
      const onLine = (line) => {
        if (line.startsWith("bestmove")) { listeners.delete(onLine); resolve(line.split(/\s+/)[1] || null); }
      };
      listeners.add(onLine);
      setOption("UCI_LimitStrength", "true");
      setOption("UCI_Elo", Math.max(1320, Math.min(3190, Math.round(elo))));
      setOption("MultiPV", 1);
      send("position fen " + fen);
      send("go depth " + (depth || 12));
      setTimeout(() => { listeners.delete(onLine); resolve(null); }, 30000);
    })).then((mv) => { try { setOption("UCI_LimitStrength", "false"); } catch (_) {} return mv; });
  }
  return { start, analyze, evaluateWhite, bestmoveAtElo, setOption };
})();
if (typeof module !== "undefined" && module.exports) module.exports = SF;
