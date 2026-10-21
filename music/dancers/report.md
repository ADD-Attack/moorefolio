# Dancers — report (producer-authored + producer amendment)

> Note: the Opus builder completed `index.html` but its session hit the Claude
> session limit before writing its own report. This report was written by the
> producer (Muse) from the delivered code and verified by independent QA.
> The dance-guide support below is a producer amendment added after delivery.

## Concept
A troupe of seven geometric characters on a lit dance floor. They don't mirror
bars — they choreograph: anticipation crouches before the beat, stretch-hops
on it, spins on snare/hat onsets, and re-formations when the song changes
section. The lead dancer carries the melody with arm height.

## Dials
DANCING 5 · COLORFUL 4 · INTENSE 3 · BEAUTIFUL 2 · TRIPPY 1 · TECHNICAL 0

## What drives what
- Kick: anticipation crouch → stretch + hop, alternating groups rippling out
  from the lead; rate-limited floor-tile colour change.
- Snare / hat onsets: full-body spins.
- Mid energy: arm sway + light beams.
- Melody pitch: lead dancer's arm height + note sparks (sidecar notes in
  SCORE mode).
- Sections (sidecar, or detected energy shifts / every 16 beats in FFT mode):
  formation changes. Overall energy: how many dancers jump.

## Producer amendment — dance guide (.dance.json)
Added 2026-10-21 after the Downbeat contract landed mid-build. If a
`.dance.json` is present (auto-fetched `../assets/demo.dance.json` for the
demo, or any dropped file with "dance" in its name), then per stage moment:
the troupe re-forms around the new lead at each handoff, the stage hue lerps
toward the moment's `palette`, caption crossfades to
"On stage: <stage> — <feeling> · <dance>", and `energy` feeds the section
energy. No dance guide → original behavior unchanged.

## Verification (producer QA, 2026-10-21)
- File: single self-contained `index.html`, ~39 KB (post-amendment), no
  external dependencies. Embedded JavaScript passes `node --check` both
  before and after the amendment.
- Contract checks pass: AnalyserNode, demo fetch, `.viz.json` support,
  drag-and-drop, FFT/SCORE badge.
- Not yet verified in a live browser with audible playback — Christopher's
  pass is the remaining gate.
