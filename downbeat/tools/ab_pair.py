"""make_pair() / make_lineup(): blind, loudness-matched A/B clip pair from two renders of the same material (studio-tools-v2).

make_pair(render_a, render_b, out_dir, slug, names=('a', 'b'), target_st=-20.0, sr=44100, lossless=True, seed=None)
  render_a / render_b: a path (anything ffmpeg decodes) or a float array (N,) / (N,2) at `sr`.
  names: what the two renders ARE (written only into ab-mapping.txt).
  1. Decode at native rate (must match), mono -> stereo.
  2. Pad the shorter with zeros to the longer's exact sample count (no trimming of material; a pair of
     renders of the same material differs only by its tail). 5 ms fade-in guard on both.
  3. Short-term-loudness match: mean ST LUFS = power mean of ffmpeg ebur128's 3 s S series over t >= 3 s
     (the legato-v2 convention). Both clips go to target_st (default -20 LU ST, the legato-v2 clip level;
     None = the quieter clip's level), iterated 3x. If either peak would exceed 0.89, both drop together.
  4. Order from `secrets` (seed= only for tests: random.Random(seed)).
  5. Writes <slug>_A.mp3 / <slug>_B.mp3 (320k, metadata stripped, no Xing) and, if lossless, <slug>_A.flac /
     <slug>_B.flac (24-bit). ab-mapping.txt in out_dir is the ONLY place the assignment is written: not in tags,
     file names, the return value, or any log. Refuses to overwrite any existing output.
  6. Verifies the DECODED mp3s: ST mean diff <= 0.2 LU, identical sample counts. Raises otherwise.
Returns dict(files=[...], st_lufs={'A','B'}, st_diff_lu, samples={'A','B'}, duration_s, peak={'A','B'}).
"""
import os
import random
import secrets
import subprocess
import tempfile
import wave

import numpy as np

from .qa import decode, ebur128

ST_TOL = 0.2
PEAK_MAX = 0.89


def write_wav24(path, y, sr=44100):
    y = np.asarray(y, dtype=np.float64)
    if y.ndim == 1:
        y = y[:, None]
    w = wave.open(path, 'wb'); w.setnchannels(y.shape[1]); w.setsampwidth(3); w.setframerate(sr)
    i = np.clip(np.round(y * 8388607), -8388608, 8388607).astype(np.int32)
    w.writeframes(np.stack([(i >> s) & 255 for s in (0, 8, 16)], -1).astype(np.uint8).tobytes()); w.close()


def st_mean(y, sr=44100, path=None):
    """Mean short-term LUFS (power mean of the 3 s S series, t >= 3 s). Array in, or path= to measure a file."""
    if path is None:
        fd, path = tempfile.mkstemp(suffix='.wav'); os.close(fd)
        write_wav24(path, y, sr); tmp = True
    else:
        tmp = False
    try:
        _, _, _, st = ebur128(path)
    finally:
        if tmp:
            os.remove(path)
    s = st[st[:, 0] >= 3.0, 1] if len(st) and st[:, 0].max() >= 3.0 else st[:, 1]
    s = s[s > -70]
    return float(10 * np.log10(np.mean(10 ** (s / 10))))


def _load(r, sr):
    if isinstance(r, str):
        x, rsr = decode(r)
        assert rsr == sr, f'{r}: {rsr} Hz, expected {sr} (no resampling)'
    else:
        x = np.asarray(r, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    if x.shape[1] == 1:
        x = np.repeat(x, 2, axis=1)
    return x.copy()


def make_pair(render_a, render_b, out_dir, slug, names=('a', 'b'), target_st=-20.0, sr=44100, lossless=True, seed=None):
    os.makedirs(out_dir, exist_ok=True)
    outs = [f'{slug}_{L}.{e}' for L in 'AB' for e in (('mp3', 'flac') if lossless else ('mp3',))] + ['ab-mapping.txt']
    clash = [f for f in outs if os.path.exists(os.path.join(out_dir, f))]
    assert not clash, f'refusing to overwrite: {clash}'
    x = [_load(render_a, sr), _load(render_b, sr)]
    n = max(len(c) for c in x)
    g = int(0.005 * sr)
    for i in range(2):
        c = np.zeros((n, 2)); c[:len(x[i])] = x[i]; c[:g] *= np.linspace(0, 1, g)[:, None]; x[i] = c
    lv = [st_mean(c, sr) for c in x]
    tgt = min(lv) if target_st is None else target_st
    for _ in range(3):
        for i in range(2):
            x[i] *= 10 ** ((tgt - st_mean(x[i], sr)) / 20)
    pk = max(np.abs(c).max() for c in x)
    if pk > PEAK_MAX:
        for i in range(2):
            x[i] *= PEAK_MAX / pk
    order = (secrets.choice([(0, 1), (1, 0)]) if seed is None else random.Random(seed).choice([(0, 1), (1, 0)]))
    res = dict(files=[], st_lufs={}, samples={}, peak={})
    with tempfile.TemporaryDirectory() as td:
        for L, k in zip('AB', order):
            w = os.path.join(td, f'{L}.wav'); write_wav24(w, x[k], sr)
            for ext, codec in (('mp3', ['-c:a', 'libmp3lame', '-b:a', '320k', '-id3v2_version', '0', '-write_xing', '0']),
                               ('flac', ['-c:a', 'flac', '-sample_fmt', 's32']))[:2 if lossless else 1]:
                dst = os.path.join(out_dir, f'{slug}_{L}.{ext}')
                subprocess.run(['ffmpeg', '-v', 'error', '-n', '-i', w, '-map_metadata', '-1', *codec, dst], check=True)
                res['files'].append(dst)
    with open(os.path.join(out_dir, 'ab-mapping.txt'), 'x') as f:
        f.write(f'{slug} A/B mapping — SEALED, producer reveals after the owner picks.\n'
                f'A = {names[order[0]]}\nB = {names[order[1]]}\n')
    for L in 'AB':
        p = os.path.join(out_dir, f'{slug}_{L}.mp3')
        y, _ = decode(p)
        res['st_lufs'][L] = round(st_mean(None, sr, path=p), 3)
        res['samples'][L] = len(y); res['peak'][L] = round(float(np.abs(y).max()), 4)
    res['st_diff_lu'] = round(abs(res['st_lufs']['A'] - res['st_lufs']['B']), 3)
    res['duration_s'] = round(res['samples']['A'] / sr, 4)
    res['source_samples'] = n
    assert res['st_diff_lu'] <= ST_TOL, f"ST diff {res['st_diff_lu']} LU > {ST_TOL}"
    assert res['samples']['A'] == res['samples']['B'], res['samples']
    return res


def make_lineup(renders, out_dir, slug=None, names=None, target_st=-20.0, sr=44100, lossless=True, seed=None):
    """Blind N-clip lineup (dial-calibration-v1). make_pair() generalised to N >= 2 renders of the same material.

    renders: list of paths / arrays (as make_pair). names: what each render IS (ab-mapping.txt only; default
    'render 1'..'render N' in input order). slug defaults to basename(out_dir).
    Pads all to the longest render's exact sample count (5 ms fade-in guard), ST-loudness-matches ALL to one
    common target (target_st; None = the quietest render's level), iterated 3x; one shared peak guard (0.89).
    Labels A, B, C... from a `secrets` shuffle (seed= only for tests). Writes <slug>_<L>.mp3 (+ .flac if lossless)
    and ab-mapping.txt — the only place the assignment exists. Refuses to overwrite. Verifies the DECODED mp3s:
    ST spread (max - min) <= 0.2 LU, identical sample counts. Returns aggregates only (no per-letter figures:
    a per-letter peak or step can identify a level).
    """
    N = len(renders)
    assert N >= 2, 'a lineup needs at least two renders'
    names = list(names) if names is not None else [f'render {i + 1}' for i in range(N)]
    assert len(names) == N and N <= 26
    slug = slug or os.path.basename(os.path.normpath(out_dir))
    letters = [chr(65 + i) for i in range(N)]
    os.makedirs(out_dir, exist_ok=True)
    exts = ('mp3', 'flac') if lossless else ('mp3',)
    outs = [f'{slug}_{L}.{e}' for L in letters for e in exts] + ['ab-mapping.txt']
    clash = [f for f in outs if os.path.exists(os.path.join(out_dir, f))]
    assert not clash, f'refusing to overwrite: {clash}'
    x = [_load(r, sr) for r in renders]
    n = max(len(c) for c in x)
    g = int(0.005 * sr)
    for i in range(N):
        c = np.zeros((n, 2)); c[:len(x[i])] = x[i]; c[:g] *= np.linspace(0, 1, g)[:, None]; x[i] = c
    lv = [st_mean(c, sr) for c in x]
    tgt = min(lv) if target_st is None else target_st
    for _ in range(3):
        for i in range(N):
            x[i] *= 10 ** ((tgt - st_mean(x[i], sr)) / 20)
    pk = max(np.abs(c).max() for c in x)
    if pk > PEAK_MAX:
        for i in range(N):
            x[i] *= PEAK_MAX / pk
    order = list(range(N))
    (secrets.SystemRandom() if seed is None else random.Random(seed)).shuffle(order)
    res = dict(files=[], st_lufs={}, samples={}, peak={}, max_step={})
    with tempfile.TemporaryDirectory() as td:
        for L, k in zip(letters, order):
            w = os.path.join(td, f'{L}.wav'); write_wav24(w, x[k], sr)
            for ext, codec in (('mp3', ['-c:a', 'libmp3lame', '-b:a', '320k', '-id3v2_version', '0', '-write_xing', '0']),
                               ('flac', ['-c:a', 'flac', '-sample_fmt', 's32']))[:len(exts)]:
                dst = os.path.join(out_dir, f'{slug}_{L}.{ext}')
                subprocess.run(['ffmpeg', '-v', 'error', '-n', '-i', w, '-map_metadata', '-1', *codec, dst], check=True)
                res['files'].append(dst)
    with open(os.path.join(out_dir, 'ab-mapping.txt'), 'x') as f:
        f.write(f'{slug} lineup mapping — SEALED, producer reveals after the owner picks.\n'
                + ''.join(f'{L} = {names[k]}\n' for L, k in zip(letters, order)))
    for L in letters:
        p = os.path.join(out_dir, f'{slug}_{L}.mp3')
        y, _ = decode(p)
        res['st_lufs'][L] = round(st_mean(None, sr, path=p), 3)
        res['samples'][L] = len(y); res['peak'][L] = round(float(np.abs(y).max()), 4)
        res['max_step'][L] = round(float(np.abs(np.diff(y, axis=0)).max()), 4)
    v = list(res['st_lufs'].values())
    assert max(v) - min(v) <= ST_TOL, f'ST spread {max(v) - min(v):.3f} LU > {ST_TOL}'
    assert len(set(res['samples'].values())) == 1, res['samples']
    # per-letter peak/step could identify a level (e.g. the hardest attack) -> aggregates only leave this function
    return dict(files=res['files'], n=N, st_spread_lu=round(max(v) - min(v), 3),
                st_lufs_min=min(v), st_lufs_max=max(v), samples=res['samples']['A'],
                duration_s=round(res['samples']['A'] / sr, 4), source_samples=n,
                peak_max=max(res['peak'].values()), max_step_max=max(res['max_step'].values()))
