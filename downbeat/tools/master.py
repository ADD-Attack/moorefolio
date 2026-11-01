"""master(): house loudness classes as presets — gain staging + a true-peak safety limiter (studio-tools-v2, 2026-10-22).

PRESETS (charter amendment 2026-10-22 table + the loop class used by the delivered loops):
  menu       -23 LUFS integrated (menu / ambient loops)       tp -1.0 dBTP
  loop       -21 LUFS (game loops: glitch jingle, robot jig)  tp -1.0 dBTP
  cinematic  -17 ±1 LUFS (cinematic / anthem)                 tp -1.0 dBTP
  drop       -13 ±1 LUFS (drop-driven)                        tp -1.0 dBTP
A ticket may pass a stricter tp (e.g. the jig's tp=-2.0) or its own target (a brief line is required to deviate).

master(mix, cls, sr=44100, tp=None, target=None, peak_max=0.90) -> (y, info)
  mix: float array (N,2) or (N,). Chain:
  1. Static gain G so the integrated loudness (ffmpeg ebur128) hits target.
  2. Safety limiter, only where needed: 4x-oversampled (resample_poly) peak per native sample -> required gain
     ceil/peak; lookahead = 1.5 ms min-hold + 1.5 ms moving average (the average of a min-filter that spans its
     window never exceeds the required gain), release = 30 ms min-hold + 30 ms moving average. Vectorised.
     Ceiling = min(tp - 0.3 dB margin, peak_max as dBFS).
  3. Measure; if integrated misses target by > 0.05 LU, adjust G and redo 1-2 (max 4 passes); if the measured
     true peak still exceeds tp, lower the ceiling by the excess and redo.
  info: class, target, tp, gain_db, integrated_lufs, true_peak_dbtp, peak, limiter_gr=dict(max_db, samples_limited_pct,
  per_window={'0-10s': max_db, ...}) (per-window, lesson 36), passes. With no limiting needed, y == mix * G exactly.
"""
import os
import tempfile

import numpy as np
from scipy import ndimage, signal

from .ab_pair import write_wav24
from .qa import ebur128

PRESETS = {'menu': dict(target=-23.0, tp=-1.0), 'loop': dict(target=-21.0, tp=-1.0),
           'cinematic': dict(target=-17.0, tp=-1.0), 'drop': dict(target=-13.0, tp=-1.0)}
MARGIN_DB = 0.3


def _meter(y, sr):
    fd, p = tempfile.mkstemp(suffix='.wav'); os.close(fd)
    try:
        write_wav24(p, y, sr)
        I, _, tp, _ = ebur128(p)
    finally:
        os.remove(p)
    return I, tp


def _os4_peak(y, chunk=1 << 18, halo=1024):
    """4x-oversampled per-native-sample peak, computed in overlapping chunks (memory: ~chunk, not 4*len).
    The halo (>> resample_poly's filter half-length) makes the result match the one-shot version."""
    pk = np.empty(len(y))
    for a in range(0, len(y), chunk):
        b = min(len(y), a + chunk)
        lo, hi = max(0, a - halo), min(len(y), b + halo)
        os4 = signal.resample_poly(y[lo:hi], 4, 1, axis=0)
        p = np.abs(os4).max(axis=1)[:(hi - lo) * 4].reshape(hi - lo, 4).max(axis=1)
        pk[a:b] = p[a - lo:b - lo]
    return pk


def _limit_gain(y, sr, ceil_lin, la_s=0.0015, rel_s=0.03):
    pk = _os4_peak(y)
    pk = np.maximum(pk, np.abs(y).max(axis=1))
    req = np.minimum(1.0, ceil_lin / np.maximum(pk, 1e-12))
    if req.min() >= 1.0:
        return None
    L = max(1, int(la_s * sr)); R = max(1, int(rel_s * sr))
    g = ndimage.uniform_filter1d(ndimage.minimum_filter1d(req, 2 * L + 1), L)
    g = ndimage.uniform_filter1d(ndimage.minimum_filter1d(g, 2 * R + 1), R)
    return np.minimum(g, req)


def master(mix, cls, sr=44100, tp=None, target=None, peak_max=0.90):
    pre = PRESETS[cls]
    target = pre['target'] if target is None else target
    tp = pre['tp'] if tp is None else tp
    x = np.asarray(mix, dtype=np.float64)
    mono_in = x.ndim == 1
    if mono_in:
        x = x[:, None]
    I0, _ = _meter(x, sr)
    G = target - I0
    ceil_db = min(tp - MARGIN_DB, 20 * np.log10(peak_max))
    for p in range(1, 9):
        y = x * 10 ** (G / 20)
        g = _limit_gain(y, sr, 10 ** (ceil_db / 20))
        if g is not None:
            y = y * g[:, None]
        I, TP = _meter(y, sr)
        ok_I = abs(I - target) <= 0.05
        ok_tp = TP is None or TP <= tp
        if ok_I and ok_tp:
            break
        if not ok_tp:
            ceil_db -= (TP - tp) + 0.05
        if not ok_I:
            G += target - I
    gr = -20 * np.log10(g) if g is not None else np.zeros(len(y))
    win = int(10 * sr)
    info = dict(cls=cls, target=target, tp_limit=tp, input_lufs=I0, gain_db=round(G, 2), integrated_lufs=I,
                true_peak_dbtp=TP, peak=round(float(np.abs(y).max()), 4), ceiling_dbfs=round(ceil_db, 2), passes=p,
                converged=bool(ok_I and ok_tp),
                limiter_gr=dict(max_db=round(float(gr.max()), 2), samples_limited_pct=round(float(np.mean(gr > 0.01) * 100), 3),
                                per_window={f'{i // sr}-{min(len(y), i + win) // sr}s': round(float(gr[i:i + win].max()), 2)
                                            for i in range(0, len(y), win)}))
    return (y[:, 0] if mono_in else y), info
