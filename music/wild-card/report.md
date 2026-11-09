# Loom — report (producer-authored)

> Note: the Opus builder completed `index.html` but its session hit the Claude
> session limit before writing its own report. This report was written by the
> producer (Muse) from the delivered code and verified by independent QA.
> The one-line pitch below is the builder's own, from its in-file header.

## One-line pitch (builder's)
**LOOM — "every song leaves a cloth."** The song is woven, in real time, into
a textile: when the track ends, what remains on screen is the whole song as a
finished piece of cloth.

## Concept
Song time weaves the cloth top → bottom, so the finished track is one
complete textile. The unwoven warp threads below the weaving line vibrate like
harp strings, each tuned to its own frequency band.

## Dials (builder-set, creative discretion)
BEAUTIFUL 4 · TECHNICAL 3 · COLORFUL 3 · TRIPPY 1 · DANCING 1 · INTENSE 1

## What drives what
- Weft colour across the width: the live log spectrum (low crimson → mid
  gold → high teal).
- Kick: the reed beats up, the low lamp bead flashes, a madder pick is woven
  across the bass threads, and the shuttle throws.
- Melody (sidecar notes, or FFT pitch estimate): embroidered running stitches
  on the thread of that pitch — which also plucks that string.
- High band: fibre glints. Left selvage: loudness / section energy. Right
  selvage: high band + snare ticks.
- SCORE mode also pins the upcoming melody as a chalk "cartoon" behind the
  warp — a tapestry weaver's draft of what's about to be woven.

## Verification (producer QA, 2026-10-21)
- File: single self-contained `index.html`, ~32 KB, no external dependencies.
  Embedded JavaScript passes `node --check`.
- Contract checks pass: AnalyserNode, demo fetch, `.viz.json` support,
  drag-and-drop, FFT/SCORE badge.
- Not yet verified in a live browser with audible playback — Christopher's
  pass is the remaining gate.
