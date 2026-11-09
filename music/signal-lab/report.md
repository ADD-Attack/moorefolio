# Signal Lab — report (producer-authored)

> Note: the Opus builder completed `index.html` but its session hit the Claude
> session limit before writing its own report. This report was written by the
> producer (Muse) from the delivered code and verified by independent QA.

## Concept
The instrument panel. Precision is the aesthetic: a log spectrum with band
shading, a triggered oscilloscope waveform, three dB meters and three lamps for
the low/mid/high bands, numeric readouts (BPM estimate, band energies, mode,
current section), a pitch roll for the melody, and a section "tape" lane.

## Dials
TECHNICAL 5 · BEAUTIFUL 2 · INTENSE 1 · COLORFUL 1 · TRIPPY 0 · DANCING 0

## What drives what
- Spectrum + band shading: AnalyserNode FFT (2048), log frequency axis.
- Oscilloscope: time-domain data, triggered.
- LOW lamp: kick — low-band spectral flux onsets in FFT mode, exact sidecar
  `kick` times in SCORE mode. This is the Raspberry Pi homage: one lamp, the
  bass drum. Flash rate gated to ≤3/s.
- MID / HIGH lamps + meters: 140–2000 Hz and 2000–12000 Hz band power (dB).
- BPM readout: median of recent kick intervals.
- Pitch roll: sidecar `melody` notes in SCORE mode; interpolated peak-bin
  pitch estimate in FFT mode.
- Section readout + tape lane: sidecar `sections`.

## Verification (producer QA, 2026-10-21)
- File: single self-contained `index.html`, ~46 KB, no external dependencies.
- Embedded JavaScript passes `node --check`.
- Contract checks pass: AnalyserNode, demo fetch (`../assets/demo.mp3`),
  `.viz.json` support, drag-and-drop, FFT/SCORE badge.
- Not yet verified in a live browser with audible playback — Christopher's
  ears/eyes pass is the remaining gate.
