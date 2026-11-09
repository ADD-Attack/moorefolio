# FETCH-RECORD — Stockfish WASM for Chess Coach (Ticket 004)

Fetched: Tue 2026-10-20 (America/Chicago), via `npm pack` from the public
npm registry. No accounts, no spending, no pushes.

## Chosen build

- **Package:** `stockfish` (nmrugg / stockfish.js), **version 19.0.1** (pinned)
- **Flavor:** **lite, single-threaded** — `stockfish-19-lite-single.js` +
  `stockfish-19-lite-single.wasm`
- **Engine identity (from UCI `id name` at runtime):** `Stockfish 19 Lite WASM`
- **Upstream engine:** Stockfish 19, lite NNUE net `nn-61e7af4bb97d`
  (reported by the engine as `EvalFile` default and in the build banner)
- **License:** GPL-3.0 (engine); `Copying.txt` from the package is kept
  beside the engine files in this folder.

## Source

- npm tarball: https://registry.npmjs.org/stockfish/-/stockfish-19.0.1.tgz
- npm `dist.shasum` (SHA-1, as published): `c557a1b9f075a67f38e01332c6db7472d8df744e`
- npm `dist.integrity` (SHA-512, as published):
  `sha512-bTwsO4e9HAwPBKls1+szcfibmaWRNzTF20rQE/XPdB3LOSoT6XTZDr1zYwriwSRRFT5MkvqrglPmJrKEVXGnyQ==`
- Tarball SHA-256 (computed locally on the downloaded file, 161,366,858 bytes
  packed / package contained all five engine flavors):
  `c3695e2a3afbc61c6439c689cb8b95cec4627bcda407193f6b7c3a5702fac839`
- Extraction: only `bin/stockfish-19-lite-single.js`,
  `bin/stockfish-19-lite-single.wasm`, and `Copying.txt` were taken out of
  the tarball into this folder. The other flavors were not kept.

## Files in this folder (engine files)

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `stockfish-19-lite-single.js` | 28230 | `ccb130d7ff29408531c47d859a49f91d59d4f482d05a53eb1a3231a4f624c91a` |
| `stockfish-19-lite-single.wasm` | 1845971 | `ee4f115bdb2d32cadf96cada104a05b5ec257d7ad6f57582190b49bc71f096de` |
| `Copying.txt` | 35821 | `0b383d5a63da644f628d99c33976ea6487ed89aaa59f0b3257992deac1171e6b` |

Plus, produced for this ticket (not fetched): `FETCH-RECORD.md` (this file),
`test-stockfish.mjs` (Node smoke test), `SMOKE-OUTPUT.txt` (real captured
output of that test).

## Why this flavor (candidate evaluation)

Requirements: run in a browser page served without special COOP/COEP
headers (ideally also local), AND be drivable from Node for automated
tests. Per the upstream README's flavor table for stockfish.js 19.0.1:

| Flavor | Size (js+wasm) | Threads | Needs cross-origin isolation |
| --- | ---: | --- | --- |
| Full | ≈94 MB | Yes | Yes — rejected (headers + size) |
| Full, single-threaded | ≈94 MB | No | No — workable, rejected on size |
| Lite | ≈1.6 MB | Yes | Yes — rejected (headers) |
| **Lite, single-threaded** | **≈1.7 MB** | **No** | **No — CHOSEN** |
| ASM-JS | ≈3 MB | No | No — rejected (upstream: very slow/weak, last resort) |

Upstream's own guidance: "most likely, you should use the lite
single-threaded engine because it is fast and does not require any
complicated setup… the lite engine is still far stronger than any human
will ever be." The engine options confirm what Ticket 004 needs:
`MultiPV` (1–256), `UCI_LimitStrength` (check), `UCI_Elo` (spin,
**1320–3190**, so the spec's 1500 target is in range).

Other named candidates, not downloaded because the nmrugg lite-single
build was tested first and passed every requirement:

- `stockfish.js` 10.0.2 (npm): Stockfish 10-era build (2019 lineage) —
  long superseded by the 19.x line above.
- lichess-org `stockfish.wasm` / stockfish-web: a separate WASM line
  whose standard builds are built around multi-threaded /
  SharedArrayBuffer operation (i.e. cross-origin isolation) — the exact
  constraint this ticket wants to avoid.

## Verification (actually run, not assumed)

- Runtime: Node v24.20.0, `node test-stockfish.mjs` in this folder,
  exit code 0, `SMOKE TEST PASSED`. Full real output: `SMOKE-OUTPUT.txt`.
- Boot: `uci` → `id name Stockfish 19 Lite WASM`, `uciok`; `isready` → `readyok`.
- startpos + MultiPV=10 + `go depth 10` returned exactly 10 candidate
  lines at depth 10; top lines:
  - #1 `d2d4` +31 cp
  - #2 `e2e4` +30 cp
  - #3 `g1f3` +18 cp
  - #4 `c2c4` +17 cp
  - #5 `e2e3` +15 cp
  (all 10 in `SMOKE-OUTPUT.txt`). This section is deterministic:
  a re-run produced byte-identical output.
- Elo-limited: `UCI_LimitStrength=true`, `UCI_Elo=1500`, Ruy Lopez
  midgame FEN, `go depth 10` → final search info +42 cp (best line
  starting `c2c3`), bestmove `d2d4` in the captured run. The limiter's
  move *pick* varies run to run by design (a second run returned
  `c2c3` off the same search) — both moves are legal, plausible, and
  near the top of the candidate list, which is the behavior the spec
  wants for a 1500-strength sparring partner.

## Browser use (per upstream README for this exact flavor)

```js
const worker = new Worker("stockfish-19-lite-single.js");
worker.onmessage = (e) => console.log(e.data); // UCI output lines
worker.postMessage("uci");
worker.postMessage("position startpos");
worker.postMessage("go depth 10");
```

- The `.wasm` file must sit next to the `.js` file, and both must be
  served with correct MIME types (`text/javascript`,
  `application/wasm`).
- No COOP/COEP headers and no cross-origin isolation are required for
  this single-threaded flavor; upstream states it "works on any static
  host with no special configuration."

## Caveats — verified vs unverified

- VERIFIED: Node loading/driving of the exact two files in this folder
  (factory `require()` → object with `listener` + `processCommand()`),
  UCI boot, MultiPV=10 at depth 10, and the Elo-limited bestmove.
  See `SMOKE-OUTPUT.txt`.
- UNVERIFIED in this task: loading in a real browser tab (this worker
  has no live-browser access). The browser instructions above are the
  upstream project's documented usage for this flavor, not a local
  browser test result. Also note some browsers restrict creating
  Workers from `file://` pages at all (a browser local-file policy,
  unrelated to COOP/COEP) — for a local browser check, serve this
  folder over plain http (e.g. any static file server, no special
  headers) and open the page from there.
