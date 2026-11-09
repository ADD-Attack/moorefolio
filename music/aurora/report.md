# Aurora — report (brief 2)

## Concept
A night sky over a still lake. Three aurora curtains hang above a dark mountain ridge, and their reflection lies in the water. Each melody note rises from the horizon as a small light and stops at a height set by its pitch, and the notes join into a constellation that slowly fades. It's slow, calm and mostly empty space. The kick drum doesn't flash anything: it makes the lowest curtain and the horizon glow swell softly, like breathing.

## Dials
beautiful 5 · trippy 2 · colorful 3 · dancing 1 · intense 0 · technical 0

## What drives what
| Element | Driven by |
|---|---|
| Lowest curtain (green → teal) | low band 20–140 Hz; kick adds a soft swell (90 ms rise, ~0.55 s decay) |
| Middle curtain (teal → violet) | mid band 140–2000 Hz |
| Upper fringe (rose) | high band 2000–12000 Hz; snare (SCORE) adds a brief shimmer |
| Star twinkle depth | high band (+ snare shimmer) |
| Horizon glow | kick (same soft envelope) |
| Rising lights | melody notes. **Height = pitch** (mapped across the sidecar's own melody range), **hue = pitch class**, how long it stays lit = note duration, and x moves across the sky in a 22 s cycle so each phrase reads left to right. Notes less than 3.5 s apart are joined by a faint line. |
| Overall aurora intensity | section `energy` (SCORE) or long-term loudness with a ~4 s time constant (FFT) |
| Palette drift (±~25°) | spectral centroid, smoothed over 5 s; also a small hue offset per section in SCORE mode |
| Section name | shown as faint letter-spaced text over the water for 6 s at each section change (SCORE) |
| Shooting star | section changes (SCORE), a strong high-band lift (FFT, at most one per 9 s), and a rare random one in idle |

**FFT mode:** kick = low-band spectral flux against an adaptive threshold (mean + 1.6σ over the last 43 frames), with a 250 ms detection cooldown. Melody estimate = an onset in the 180–1600 Hz band, then the strongest spectral peak in that band, refined with parabolic interpolation and converted to MIDI.
**SCORE mode:** the `kick` and `melody` lists in the sidecar replace those two estimates. Events fire when `audio.currentTime + 0.05 s` passes them. The event cursors are reset by binary search on `seeking`, `seeked`, the seek bar's `change` event, and any time jump over 0.6 s. Band energies still come from the analyser.

## What I'm proud of / invented
- **Lights whose height is pitch, joined into a constellation:** you can see the shape of the melody in the sky after it has played.
- **Hue = pitch class:** a repeated motif comes back in the same colours.
- **Lake reflection:** the aurora's low-resolution buffer is drawn a second time, flipped and squashed vertically, under drifting ripple lines. It costs almost nothing and gives a symmetrical, framed look that suits a picture on a wall.
- **Soft curtains:** the aurora is drawn to a buffer at 1/3 resolution, using one stretched 1-pixel gradient strip per column, with a light fade between frames. Upscaling it gives the soft edges without a blur filter, which keeps it cheap on phones.

## Safety / quality
- **Strobe:** the kick visual can't restart within 340 ms of the last one, so the hard cap is about 2.9 swells per second. Each swell is a gradual brightness change in one curtain plus a horizon glow at 16% alpha, not a full-screen flash.
- **`prefers-reduced-motion` (calm mode):** this is tracked live. Drift runs at 35% speed and the kick swell at 35% size. Twinkle is nearly flat, there are no shooting stars, lights fade in where they are instead of rising, and the ripples move more slowly.
- **Mobile:** works at 390 px. The transport bar is `min(680px, 100% − 24px)`. At ≤480 px the file pickers wrap onto their own centred row, and the seek bar has `min-width:0`, so there's no horizontal scroll. On portrait screens the horizon sits at 70% of the height (74% in landscape).
- **Rendering:** devicePixelRatio is capped at 2, the canvas resizes with the window, and the loop runs on requestAnimationFrame.

## Spec deviations (and why)
- **Demo sidecar vs a newly loaded song:** if the user loads a different audio file, an auto-fetched demo sidecar is dropped and the badge goes back to FFT, because the demo score doesn't match another song. A sidecar the user picked themselves stays until they pick another, so audio and score can be loaded in either order. Dropping an audio file and a `.viz.json` together loads both.
- **Demo loading:** the demo mp3 is fetched as a blob and played from an object URL rather than pointed at directly. This avoids CORS problems with `MediaElementSource` on Pages. Any failure, including file:// blocking fetch, falls back silently to the picker.
- **Spacebar:** spacebar toggles play everywhere except when a button or file input has focus. There it does that element's own action, which avoids toggling twice.

## Measurements / verification
- **File size:** `index.html` is 34,131 bytes. It's a single file with no external requests apart from the optional `../assets/demo.mp3` and `demo.viz.json`.
- **Syntax:** I extracted the script and ran `node --check` on it; it passed.
- **Headless smoke test:** I ran the script in Node with stubbed DOM, canvas, Audio, AudioContext and FileReader:
  - idle for 10 s with nothing loaded;
  - a drop of an mp3 plus a `.viz.json`, which set the track name and switched the badge to SCORE;
  - Space to play;
  - 4 s of playback through kick, snare, melody and section events;
  - a seek backwards and replay;
  - pause.

  I ran the same sequence with only an audio file (FFT kick and melody estimation on random spectra). There were no exceptions in either run.
- **Visuals not tested:** no real browser or audio was used, so how it looks, the frame rate and the audio-reactive feel are untested.
- **Idle state (no audio):** with nothing loaded, the page is driven by a gentle synthetic pulse:
  - slow sine-wave band energies;
  - a soft kick swell every 3.6 s;
  - a random walk on a pentatonic scale that releases a rising light every 1.5–3.1 s;
  - a rare shooting star.

  A short line of text asks for a song. The page looks deliberate before anything is loaded.
- **Missing demo:** `assets/demo.viz.json` doesn't exist right now, so the demo loads in FFT mode. In the picker-only path (fetch fails or 404s), the play button stays disabled until a file arrives, and the hint text stays visible. I checked that logic by reading the code and in the smoke test, which had no fetch.
