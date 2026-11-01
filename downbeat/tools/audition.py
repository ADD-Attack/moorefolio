"""audition(): producer-side naked-theme audition on a real patch, no build ticket (studio-tools-v2, 2026-10-22).

audition(melody, patch, out_dir, name=None, window=None, vel=None, target_lufs=-20.0, ring_s=1.5, transpose=0)
  melody: a .mid path (read with sidecars.read_midi, tempo map honoured), a score.json path (its `notes`; the
      `lead` notes if any are marked, else all), or a list of score-shape dicts {t, midi, dur[, vel]} (seconds).
  patch: an instruments.json key or a unique case-insensitive substring of one (e.g. 'clarinet-SEC', 'Marimba').
  window: (t0, t1) seconds — keep notes with t0 <= t < t1 (e.g. one statement of a long MIDI). The clip is
      re-zeroed so the first kept note starts at 0.
  vel: override every velocity (None keeps the source's). transpose: semitones (the range assert still runs).
Renders through tools.render_part — range-asserted, strict MIDI (humanise OFF; times in seconds are written at
60 BPM so 1 beat = 1 s exactly), RAM sfz copy, int16 staging — then one static gain to target_lufs integrated
(peak capped at 0.89), centre-panned, 10 ms end fade. Writes <name>.wav (24-bit) + <name>.mp3 (320k) in out_dir;
never overwrites. Returns dict(wav, mp3, patch, notes, seconds, integrated_lufs, peak, gain_db, wall_s).
"""
import json
import os
import shutil
import subprocess
import tempfile
import time

import numpy as np

from .ab_pair import write_wav24
from .qa import ebur128
from .render import render_part
from .sidecars import read_midi

CATALOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instruments.json')


def find_patch(patch):
    P = json.load(open(CATALOG))['patches']
    if patch in P:
        return patch, P[patch]
    hits = [k for k in P if patch.lower() in k.lower()]
    assert len(hits) == 1, f'patch {patch!r}: {len(hits)} matches {hits[:8]}'
    return hits[0], P[hits[0]]


def load_melody(melody):
    if isinstance(melody, str) and melody.lower().endswith(('.mid', '.midi')):
        return [dict(t=t, midi=m, dur=d, vel=v) for t, m, d, v in read_midi(melody)]
    if isinstance(melody, str):
        notes = json.load(open(melody))['notes']
        lead = [n for n in notes if n.get('lead')]
        return lead or notes
    return list(melody)


def audition(melody, patch, out_dir, name=None, window=None, vel=None, target_lufs=-20.0, ring_s=1.5, transpose=0):
    t_start = time.time()
    key, info = find_patch(patch)
    ns = load_melody(melody)
    if window:
        ns = [n for n in ns if window[0] <= n['t'] < window[1]]
    assert ns, 'no notes to audition'
    t0 = min(n['t'] for n in ns)
    notes = [(round(n['t'] - t0, 6), round(n['dur'], 6), int(n['midi']) + transpose, int(vel or n.get('vel', 100)))
             for n in sorted(ns, key=lambda n: n['t'])]
    name = name or f"audition_{os.path.splitext(os.path.basename(key))[0]}"
    os.makedirs(out_dir, exist_ok=True)
    wav, mp3 = os.path.join(out_dir, f'{name}.wav'), os.path.join(out_dir, f'{name}.mp3')
    assert not os.path.exists(wav) and not os.path.exists(mp3), f'refusing to overwrite {name}.*'
    work = tempfile.mkdtemp(prefix='audition_')
    try:
        r = render_part(name, info['path'], notes, work, bpm=60, ring_s=ring_s)
        x = r['audio'].astype(np.float64)
        if x.shape[1] == 1:
            x = np.repeat(x, 2, 1)
        f = int(0.01 * r['sr']); x[-f:] *= np.linspace(1, 0, f)[:, None]
        tmp = os.path.join(work, 'meas.wav'); write_wav24(tmp, x, r['sr'])
        I = ebur128(tmp)[0]
        g = 10 ** ((target_lufs - I) / 20)
        g = min(g, 0.89 / (np.abs(x).max() + 1e-12))
        y = x * g
        write_wav24(wav, y, r['sr'])
        subprocess.run(['ffmpeg', '-v', 'error', '-n', '-i', wav, '-c:a', 'libmp3lame', '-b:a', '320k', mp3], check=True)
        It = ebur128(wav)[0]
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return dict(wav=wav, mp3=mp3, patch=key, notes=len(notes), seconds=round(len(y) / r['sr'], 3),
                integrated_lufs=It, peak=round(float(np.abs(y).max()), 4), gain_db=round(20 * np.log10(g), 2),
                stage_db=r['stage_db'], wall_s=round(time.time() - t_start, 2))
