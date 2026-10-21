# OVERDRIVE — report (brief 5)

## Concept
A reactor core in the middle of the screen that charges up with the song. Every kick sets off a particle burst and a shockwave ring. Loudness slowly fills a "charge" battery that powers everything else: spectrum rays get longer, a hexagonal warp tunnel speeds up, trails get longer and the hue cycles faster. When the song stays loud long enough, the visual latches into an OVERDRIVE climax state, so a song's climax looks like a climax and not just a louder verse.

## Dials
INTENSE 5 · COLORFUL 5 · TRIPPY 3 · DANCING 2 · BEAUTIFUL 1 · TECHNICAL 0

## What drives what
| Element | FFT mode | SCORE mode (sidecar) |
|---|---|---|
| Particle burst + shockwave ring + core "punch" + screen shake | low-band (20–140 Hz) spectral-flux kick, adaptive threshold (mean + 1.5σ over ~0.7 s), 250 ms cooldown | sidecar `kick` times, exact, 50 ms lookahead |
| Soft full-screen bloom | kick, **hard rate-limited to ≥ 400 ms apart (≤ 2.5/s)**, exponential decay | same |
| Twin spark sprays + spin impulse | mid/high spectral flux onset (180 ms cooldown) | sidecar `snare` times |
| Comets | mid-band onsets, aimed at the loudest mid ray | `melody` notes: angle = pitch (C4 points up, ±2 octaves sweeps the circle), colour = pitch class (30° per semitone), size/speed = note duration |
| Charge (energy field) | ~1.5 s loudness EMA ÷ slowly decaying loudness peak | 50/50 blend of that with the current section's `energy` |
| Section change | — | big slow ring; section name shown top-right |
| Spectrum rays (128, mirrored) | 64 log-spaced bands, 30 Hz–12 kHz; length scaled by charge | same |
| Core star | point count from high band, inner radius from mid band, glow from low band | same |
| Glitter | high band (2–12 kHz) energy | same |
| Hue | drifts over time, at a rate set by charge; offset by spectral centroid | same |
| OVERDRIVE label, faster hue/warp | charge > 0.8 held for > 1.2 s | same |

Band energies are computed from bins mapped by frequency (`bin = f / (sampleRate/2048)`). Each band is normalised against its own slowly decaying peak, then smoothed with a fast attack (~0.6 per frame) and a slower decay (~0.07 per frame), scaled to frame time.

## What I'm proud of
- **The climax is earned.** Charge is slow on purpose, so a kick in a quiet intro gives a small ring, and the same kick at the climax fires about 4× the particles, a second counter-coloured ring, more shake and longer trails. Intensity follows where you are in the song, not just the current frame.
- **Intense without strobing.** The only full-screen brightness change is the bloom, which has a hard limit of one per 400 ms and fades smoothly. Rings and particles carry the per-kick hit. The 3 flashes/s limit holds even at 200+ BPM.
- **Score-accurate melody.** With a sidecar, each melody note launches a comet whose direction is its pitch and whose colour is its pitch class, so a rising line visibly sweeps around the core.

## Calm mode (prefers-reduced-motion)
The setting is checked live. Calm mode turns off bloom and screen shake, caps particles at 260 instead of 1600, cuts motion and hue drift to 35%, and makes rings thinner and shorter-lived. It is still clearly reactive.

## Idle state (no audio)
Tested by running the script under node with a stubbed DOM, canvas and audio, for 300 idle frames. Before any file loads, a synthetic pulse at ~96 BPM fires gentle kicks (strength 0.3), so small rings breathe out of the core. The spectrum rays ripple from two slow sines, charge sits at 0.12, and "DROP A TRACK · OR PICK ONE BELOW" is shown. The idle pulse also runs while a loaded track is paused, so the stage never freezes.

## Contract checks
- Demo: fetches `../assets/demo.mp3` as a blob, then shows "Mountain King v1 (demo)" ready to play. It then tries `../assets/demo.viz.json`; that file doesn't exist in assets right now, so the demo runs in FFT mode. Any fetch failure (file:// CORS, 404) is caught silently and the picker stays usable.
- **Picker path tested** with the harness: fetch rejected as a file:// failure → picking an audio file enables the transport → 600 FFT frames played → user sidecar loaded → badge switches to SCORE → kick/snare/melody/section cursors fired → seek back to 0 resets the cursors with binary search. No exceptions on any path.
- Drag and drop works anywhere on the page, for audio files and `.json` sidecars.
- Transport: play/pause, seek bar, current and total time, spacebar toggle (buttons blur after a click and keyup is suppressed, so space never toggles twice).
- One AudioContext, created on the first play gesture. AnalyserNode fftSize 2048.
- Canvas uses devicePixelRatio (capped at 2 for fill-rate), resizes with the window and is driven by requestAnimationFrame.
- At 390 px, the controls wrap to two rows, the track name is ellipsised, and there's no horizontal scroll (`overflow: hidden`, flex wrap).

## Measurements
- `index.html`: 29,973 bytes, single file, no dependencies.
- JS syntax: `node --check` passed. The runtime smoke test passed for the idle, picker, FFT, SCORE and seek paths.
- **Not verified:** real-browser rendering and frame rate, and how kick detection behaves on real music. The harness used random spectra, so the FFT thresholds are tuned by reasoning, not by listening.

## Deviations
- A loaded sidecar replaces FFT detection for kick, snare and melody events, as the spec intends. The continuous field (bands, rays, charge) still comes from the FFT, because the sidecar has no amplitude data.
- If a different audio file is loaded, the auto-fetched demo sidecar is dropped, since it belongs to the demo. A sidecar the user picked is kept.
- The top-of-file comment comes before `<!DOCTYPE html>`, as the spec asks. Modern browsers stay in standards mode.
