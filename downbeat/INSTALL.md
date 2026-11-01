# Downbeat — install note

## Layout after unzip

```
downbeat/
  README.md          what the app is and how it works
  INSTALL.md         this file
  tools/
    __init__.py      package entry: render_part, qa, deliver, mark, noise_bus
    render.py        SFZ part rendering through sfizz_render
    sfz.py           SFZ parsing + flattening
    synth.py         synth sources (band-limited noise buses)
    build_instruments.py   catalog generator
    instruments.json       instrument catalog (regenerate for your libraries)
    master.py        mastering chain + true-peak limiter
    deliver.py       encode + verify + no-clobber delivery
    qa.py            audio checks
    ...              supporting modules (audition, ab_pair, legato, dials,
                       loopcheck, mir, sidecars, checkpoint)
```

## Dependencies

- Python 3.10+ with `numpy` and `scipy` (`pip install numpy scipy`)
- `sfizz_render` on PATH — the command-line renderer from the sfizz
  project. Downbeat shells out to it for every sampled part.
- `ffmpeg` on PATH — used for MP3/FLAC encoding and loudness
  measurement.

## Samples: bring your own

The bundle contains **no sample content**. Downbeat renders SFZ
instruments, and you supply the SFZ libraries (free and commercial
SFZ libraries both work). This is deliberate: the download stays
small, and sample licences stay with their owners.

## First run

1. Put the `downbeat` folder where your agent works and make sure
   the parent folder is on `sys.path` (the package imports as
   `tools`).
2. Point `tools/build_instruments.py` at your SFZ libraries and run
   `python3 -m tools.build_instruments` to regenerate
   `tools/instruments.json` for your collection.
3. Smoke test: write a tiny build script that renders one part with
   `render_part(...)` from a mapped SFZ instrument, then run it.
   A range error means the part asks for notes the instrument
   doesn't have — that check firing is the system working.

No services, no accounts, no telemetry. It is a folder of Python
that makes audio files.
