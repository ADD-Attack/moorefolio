# Trippy Flow — report

## Concept
A mirrored fluid. A WebGL shader warps fBm noise twice (domain warping) and folds the result through a rotating kaleidoscope, with five metaballs melting through the flow. The music moves the fluid itself: the hue drifts with the spectral centroid, the bass swells the blobs, and every kick sends a ripple through the image. Nothing flashes.

## Dials
TRIPPY 5 · COLORFUL 4 · BEAUTIFUL 3 · INTENSE 2 · DANCING 1 · TECHNICAL 0

## What drives what
| Visual element | Driven by |
|---|---|
| Overall hue | Spectral centroid over 20–12000 Hz, log-mapped and slowly smoothed (~1.2 s). Dark/bassy sounds are violet, brighter ones move toward magenta, amber and green |
| Metaball size | Low band (20–140 Hz), smoothed with a fast attack (~35 ms) and slower decay (~0.3 s) |
| Warp depth + flow speed | Mid band (140–2000 Hz) plus long-term energy (loudness, or the section `energy` in SCORE mode) |
| Fine shimmer sparkles | High band (2000–12000 Hz) |
| Ripples (radial displacement waves, mirrored by the kaleidoscope into interference patterns) | Kick. FFT mode: low-band spectral flux with an adaptive threshold (mean + 1.5σ over ~0.7 s) and a 250 ms cooldown. SCORE mode: sidecar `kick` times, 50 ms look-ahead |
| Kaleidoscope twist | Sidecar `snare` hits give a decaying angular impulse (in FFT mode there is only a slow constant rotation) |
| Melody bead (mirrored into a ring) | SCORE: each `melody` note sets the bead's radius from its pitch (normalised to the track's own melodic range), its envelope (held for `dur`, then a decay) and a pitch-class hue tint. FFT: the mid band and centroid stand in |
| Mirror count (6/8/5/7/9) | Sidecar `sections` (one count per section, with a ripple at each boundary). FFT: steps every 32 detected kicks |
| Gentle brightness lift (+14% max) | On a kick, limited to one lift per 0.4 s (≤2.5/s, under the 3/s strobe limit) |

## Invented / proud of
- **The kick as a ripple, not a flash.** Each kick is a damped sine wavefront that bends UV space before the kaleidoscope fold. Because the ripple centres are jittered off-axis, the fold mirrors each one into a different interference pattern, so no two kicks look the same.
- **Hue moves on the shortest path round the colour wheel**, so the centroid can't make the image snap from red to violet.
- **Adaptive render scale**: DPR capped at 2, dropping down to 0.5× if frames average over 24 ms, so phones keep the frame rate.
- Fallbacks: a 2D-canvas kaleidoscope if WebGL is missing, and a fresh canvas if the shader fails after a WebGL context was already taken.

## Contract checklist
- Demo autoload: fetches `../assets/demo.mp3` → "Mountain King v1 (demo)", then tries `../assets/demo.viz.json`. Any failure is caught silently and the picker stays.
- Drag-and-drop anywhere (audio or `.json`), an audio picker, and a separate sidecar picker.
- Play/pause, seek bar, current/total time, Spacebar toggle.
- One AudioContext created on the first play gesture. AnalyserNode with fftSize 2048. Bands are mapped by frequency (`bin = f / (sampleRate/2048)`).
- FFT/SCORE badge. Event cursors reset by binary search on `seeked`, on seek-bar change, and on any currentTime jump larger than 0.75 s or backwards more than 0.1 s. A demo sidecar is dropped when the user loads their own audio; a user-picked sidecar is kept.
- `prefers-reduced-motion` (watched live): calm mode runs the flow at 0.3× speed, gives ripples 35% strength and slows how fast they spread, turns off the brightness lift and snare twists, and slows the rotation.
- At 390 px: the transport row and picker row wrap, the seek bar is `min-width:0`, `overflow:hidden` on the body, and no fixed widths. No horizontal scroll.

## Deviations
- In FFT mode, snare has no detector of its own, so the twist only happens in SCORE mode. This keeps the TECHNICAL 0 brief simple. Rotation still drifts.
- The top-of-file comment comes before `<!DOCTYPE html>` because the spec asks for it at the top of the file. Modern browsers stay in standards mode with a comment before the doctype.

## Measurements / verification
- `index.html`: 27,669 bytes, single file, no external requests apart from the optional demo assets.
- JS syntax: the script was extracted and passed `node --check`. The GLSL was **not** compiled (no GPU in the build VM); I re-read it by hand for GLSL ES 1.0 rules (constant loop bounds, uniform array indexed by the loop index, float literals). Rendering is **UNVERIFIED** until it is opened in a browser.
- Idle state, traced by hand: with no file, `hasAudio` is false, so `analyse()` runs the synthetic path. That is a 0.5 Hz bass "heartbeat" (low 0.18→0.50 with an exponential decay), slow sinusoidal mid/high, the hue swinging gently around violet, and a soft ripple every 2 s. The stage shows a slowly breathing, rippling violet kaleidoscope behind the hint "drop a song anywhere · or choose one below".
- Picker path traced by hand with the demo missing: the fetch rejects or `!r.ok` throws, `.catch` swallows it, the badge stays FFT, the play button stays disabled until a file arrives, and then `loadAudioFile` calls `setAudio`, which enables the transport. At the time of building, `assets/` contains `demo.mp3` but no `demo.viz.json`, so the demo will run in FFT mode.
