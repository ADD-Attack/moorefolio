# Downbeat — the headless music app

Downbeat is a music-making tool with no interface. There is no DAW, no
timeline, no piano roll — an LLM (or a human who likes code) writes a
Python build script that describes the music, and Downbeat renders it
to finished audio: WAV master plus encoded deliverables.

It exists because an agent can't drag notes around a grid, but it can
write code. So the composition surface is code, the instruments are
files, and every step — render, mix, master, encode — is a function
call that either succeeds or raises.

## How the app works

A build script drives the whole thing:

1. **Describe the music in code** — notes, timing, velocities and
   parts as data, assembled by your build script.
2. **Render the sampled parts** — each part is rendered through sfizz
   from SFZ instruments, with range checks before anything renders
   (an unmapped note fails loudly instead of playing silence) and
   automatic gain staging.
3. **Synthesise the rest** — a small synth toolkit (band-limited noise
   buses for drums and swells, plus utilities for legato, vibrato and
   other performance shaping) covers parts that don't come from
   samples.
4. **Master** — loudness-targeted mastering with a true-peak safety
   limiter.
5. **Deliver** — encode to MP3/FLAC, verify the *decoded* files, and
   copy to the final names with no-clobber semantics: a deliverable
   that already exists is never overwritten.

## What's inside

| File | What it does |
|---|---|
| `tools/render.py` | Renders one part through `sfizz_render`: range assertion against the SFZ first, RAM-loaded flattened SFZ, exact-tick MIDI, gain staging, post-render sanity checks |
| `tools/sfz.py` | SFZ parser and flattener shared by the renderer and the catalog builder |
| `tools/synth.py` | Synth sources, starting with band-limited noise buses for drums and swells |
| `tools/build_instruments.py` | Generates `instruments.json` from your own SFZ files: playable ranges, velocity layers, round-robins, reference levels |
| `tools/instruments.json` | The instrument catalog the renderer checks against (regenerate it for your libraries) |
| `tools/master.py` | Loudness-targeted mastering chain with a lookahead true-peak safety limiter |
| `tools/deliver.py` | Scratch encode → decoded-file verification → no-clobber copy to final deliverable names |
| `tools/qa.py` | Audio checks used by the delivery gate: peaks, jumps, silence, length |
| `tools/audition.py`, `tools/ab_pair.py` | Render short auditions and A/B comparison pairs |
| `tools/legato.py`, `tools/dials.py` | Performance shaping: legato handling and named control "dials" |
| `tools/loopcheck.py`, `tools/mir.py`, `tools/sidecars.py`, `tools/checkpoint.py` | Loop verification, music-information helpers, sidecar metadata, and build checkpoints |

## Requirements

- Python 3 with `numpy` and `scipy`
- `sfizz_render` on your PATH (the SFZ rendering engine; from the
  sfizz project)
- `ffmpeg` on your PATH (encoding and loudness measurement)
- **Your own SFZ sample libraries.** The bundle ships code only —
  no samples — which keeps it small and keeps sample licensing where
  it belongs: with you. Point the catalog builder at your libraries
  and it generates your `instruments.json`.

## Quickstart (for an agent)

1. Unzip and put the `downbeat` folder in your workspace.
2. Read this file and `INSTALL.md`.
3. Run `python3 -m tools.build_instruments` against your SFZ
   libraries to build your catalog.
4. Write a build script against `render_part` (sampled parts) and
   `noise_bus` (synth parts), then `master()` and `deliver()`.

Downbeat is the tool behind the music published as MooreStudios.
This page shares the app; bring your own samples, your own build
scripts, and your own taste.
