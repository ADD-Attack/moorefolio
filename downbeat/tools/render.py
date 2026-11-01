"""render_part(): render one part through sfizz_render safely, in one call.

What it does, in order (each step prints its own `[render_part]` log line, also appended to `<out>.log`;
sfizz's own log is empty on success and on crash alike — lessons 15/22 — so it proves nothing):
  1. Range assert BEFORE anything renders: every (pitch, velocity) must hit a playable region of the
     source sfz (lokey/hikey + lovel/hivel, release triggers excluded). sfizz plays an unmapped key as
     silence and says nothing (lessons 32/34). Raises RangeError listing every offending note.
  2. RAM-loaded flattened sfz copy: `hint_ram_based=1`, absolute sample paths, only regions touching
     the part's keys (lesson 8: disk streaming drops long samples offline).
  3. MIDI via midutil.write_midi(humanize=False) — exact ticks — then a no-op CC110 `ring_s` seconds
     after the last note-off, then EOT. sfizz `--use-eot` stops at the last event, not at EOT's delta
     (lesson 13), so the CC is what buys the ring-out.
  4. Post-render checks: length vs expected, not silent, no int16 clipping.

Gain staging (sfizz_render writes int16 only, no format option):
  The flattened copy carries a uniform `volume=` offset S dB on every region (stage 0 first).
  - any sample at |x| >= 32767 (clipped)    -> S -= 6 dB and re-render (up to 4 tries);
  - peak below -24 dBFS (wasted resolution)   -> S += (-6 dBFS - peak) dB and re-render once.
  The returned float array is the int16 render divided by 10**(S/20), i.e. always at UNITY-equivalent
  level, so mix gains never need to know the stage. S is reported in the result and the log.
  Target window for a staged render: peak in (-24, 0) dBFS with zero clipped samples.
"""
import json
import os
import subprocess
import sys
import wave

import numpy as np

sys.path.insert(0, '/home/hatch/workspace/song')
import midutil  # noqa: E402
from . import sfz  # noqa: E402

SFIZZ = '/home/hatch/workspace/build/sfizz/build/library/bin/sfizz_render'
SR = 44100
RING_CC = 110


class RangeError(AssertionError):
    pass


def _log(logf, msg):
    line = f'[render_part] {msg}'
    print(line, flush=True)
    with open(logf, 'a') as f:
        f.write(line + '\n')


def check_range(sfz_path, notes):
    regs = sfz.parse_regions(sfz_path)
    bad = [(sb, m, v) for sb, db, m, v in notes if not sfz.covers(regs, m, v)]
    if bad:
        pl = sfz.playable(regs)
        lo, hi = min(r['lokey'] for r in pl), max(r['hikey'] for r in pl)
        raise RangeError(f'{len(bad)} note(s) outside {os.path.basename(sfz_path)} range '
                         f'(keys {lo}-{hi}); (beat, midi, vel): {bad[:12]}')
    return regs


def _var(n):
    return midutil.varint(n)


def write_part_midi(path, notes, bpm, ring_s, program=0):
    """Strict MIDI + ring-out CC. Returns seconds of the CC (= expected render length)."""
    midutil.write_midi(path, notes, program=program, bpm=bpm, humanize=False)
    raw = open(path, 'rb').read()
    eot = bytes([0x00, 0xFF, 0x2F, 0x00])
    assert raw.endswith(eot)
    last_off = max(round(sb * midutil.TPQ) + round(db * midutil.TPQ) for sb, db, m, v in notes)
    # delta from the last event (always the last note-off) to the ring CC
    ring_ticks = round(ring_s * bpm / 60 * midutil.TPQ)
    tail = _var(ring_ticks) + bytes([0xB0, RING_CC, 0]) + eot
    trk = raw[22:-4] + tail
    hdr = raw[:14]
    open(path, 'wb').write(hdr + b'MTrk' + len(trk).to_bytes(4, 'big') + trk)
    return (last_off + ring_ticks) / midutil.TPQ * 60 / bpm


def _read16(path):
    w = wave.open(path)
    d = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).reshape(-1, w.getnchannels())
    return d, w.getframerate()


def render_part(name, sfz_path, notes, out_dir, bpm=midutil.BPM, ring_s=4.0, program=0, sr=SR,
                stage_db=0.0, legato=False, legato_opts=None, _midi_hook=None, rr_seq=False, overrides=None):
    """notes: (start_beat, dur_beats, midi, vel). Returns dict(audio=float32 (N,2) unity-level,
    wav=int16 staged wav, stage_db, peak_dbfs, rms_dbfs, clipped, seconds, expected_s).
    legato=True: scripted legato for a monophonic sustain line (tools/legato.py; off by default — with the
    flag off this function's behaviour is unchanged). _midi_hook(mid_path): internal, used by legato.py.
    rr_seq / overrides: passed to sfz.flatten (deterministic RR; per-part opcode overrides such as ampeg_release)."""
    if legato:
        from .legato import render_legato
        return render_legato(name, sfz_path, notes, out_dir, bpm=bpm, ring_s=ring_s, program=program, sr=sr,
                             stage_db=stage_db, **(legato_opts or {}))
    notes = [tuple(n) for n in notes]
    assert notes, f'{name}: no notes'
    check_range(sfz_path, notes)          # raises before anything is written or rendered
    os.makedirs(out_dir, exist_ok=True)
    logf = os.path.join(out_dir, f'{name}.log')
    open(logf, 'w').close()
    _log(logf, f'{name}: range OK — {len(notes)} notes inside {os.path.basename(sfz_path)}')
    mid = os.path.join(out_dir, f'{name}.mid')
    expected = write_part_midi(mid, notes, bpm, ring_s, program)
    if _midi_hook is not None:
        _midi_hook(mid)
    _log(logf, f'{name}: midi strict, ring CC{RING_CC} at {expected:.3f} s'
               + (f'; rr_seq={rr_seq} overrides={overrides}' if rr_seq or overrides else ''))
    keys = sorted({m for _, _, m, _ in notes})
    wav = os.path.join(out_dir, f'{name}.wav')
    tries = 0
    while True:
        tries += 1
        ram = os.path.join(out_dir, f'{name}_ram.sfz')
        nreg = sfz.flatten(sfz_path, ram, keys=keys, volume_db=stage_db, rr_seq=rr_seq, overrides=overrides)
        if os.path.exists(wav):
            os.remove(wav)
        p = subprocess.run([SFIZZ, '--sfz', ram, '--midi', mid, '--wav', wav, '--use-eot', '-s', str(sr)],
                           capture_output=True, text=True)
        if p.returncode != 0 or not os.path.exists(wav):
            _log(logf, f'{name}: FAIL sfizz rc={p.returncode} {p.stderr[-300:]}')
            raise RuntimeError(f'{name}: sfizz_render failed rc={p.returncode}')
        d, wsr = _read16(wav)
        clipped = int(np.sum(np.abs(d.astype(np.int32)) >= 32767))
        peak = float(np.abs(d).max()) / 32768
        peak_db = 20 * np.log10(max(peak, 1e-9))
        _log(logf, f'{name}: render try {tries} stage {stage_db:+.1f} dB, {nreg} RAM regions, '
                   f'peak {peak_db:.1f} dBFS, clipped {clipped}')
        if clipped and tries < 5:
            stage_db -= 6.0
            continue
        if -120 < peak_db < -24 and tries < 5 and not clipped:
            stage_db += round(-6.0 - peak_db, 1)
            continue
        break
    secs = len(d) / wsr
    ok_len = expected - 0.05 <= secs <= expected + 1.0
    _log(logf, f'{name}: length {secs:.3f} s vs expected {expected:.3f} s — {"OK" if ok_len else "FAIL"}')
    x = d.astype(np.float32) / 32768 / (10 ** (stage_db / 20))
    act = x[np.abs(x).max(axis=1) > 10 ** (-90 / 20) / 10 ** (stage_db / 20)]
    rms_db = 20 * np.log10(np.sqrt(np.mean(act ** 2)) + 1e-12) if len(act) else -200.0
    silent = peak_db < -60
    _log(logf, f'{name}: not-silent — {"FAIL" if silent else "OK"} (staged peak {peak_db:.1f} dBFS, '
               f'unity active RMS {rms_db:.1f} dBFS)')
    _log(logf, f'{name}: clipping — {"FAIL" if clipped else "OK"} ({clipped} samples at int16 rail)')
    res = dict(wav=wav, mid=mid, sfz=ram, stage_db=stage_db, peak_dbfs=peak_db, rms_dbfs=float(rms_db),
               clipped=clipped, seconds=secs, expected_s=expected, sr=wsr)
    json.dump(res, open(os.path.join(out_dir, f'{name}.render.json'), 'w'), indent=1)
    if not ok_len or silent or clipped:
        raise RuntimeError(f'{name}: post-render check failed (see {logf})')
    res['audio'] = x
    return res
