"""MIR layer: estimate / chroma_match / beat_track (mir-tools-v1, owner-approved 2026-10-23).

Needs librosa: run with the seat venv, `/home/hatch/workspace/downbeat-seat/.venv/bin/python`
(created with --system-site-packages, so numpy 1.26.4 / scipy 1.11.4 are the system ones; librosa 0.11.0).

  estimate(path)            -> dict(tempo_bpm, key, key_confidence, key_ranking, duration_s, ...)
  chroma_match(a, b)        -> dict(score 0..1, lag_s, frames, chroma_mean_a/b, ...)
  beat_track(path)          -> dict(beat_times, tempo_bpm, grid_period_s, onset_peaks, kick_peaks, kick_grid, ...)

CLI:  .venv/bin/python -m tools.mir estimate FILE
      .venv/bin/python -m tools.mir chroma FILE_A FILE_B
      .venv/bin/python -m tools.mir beats FILE [--full] [--ref SIDECAR.json[:key]]
Audio is decoded with tools.qa.decode (ffmpeg, native rate), folded to mono, resampled to 22050 Hz (soxr_hq)
for analysis. All results are plain dicts of floats/ints/strings/lists (json-serialisable).
"""
import json
import sys

import librosa
import numpy as np

from .qa import decode

SR = 22050
HOP = 512
PITCHES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
ENHARM = {'C#': 'Db', 'Eb': 'D#', 'F#': 'Gb', 'Ab': 'G#', 'Bb': 'A#'}
# Krumhansl-Kessler key profiles (tonic first).
KK_MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
KK_MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


def _load(path, sr=SR):
    x, native = decode(path)
    y = x.mean(1).astype(np.float32)
    dur = len(y) / native
    if native != sr:
        y = librosa.resample(y, orig_sr=native, target_sr=sr, res_type='soxr_hq')
    return y, sr, native, dur


def _chroma(y, sr, hop=HOP):
    return librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop)


def _key(chroma_mean):
    """Krumhansl-Schmuckler: Pearson r of the mean chroma against all 24 rotated KK profiles.
    confidence = r of the top call; margin = r(top) - r(second)."""
    res = []
    for t in range(12):
        for mode, prof in (('major', KK_MAJOR), ('minor', KK_MINOR)):
            r = float(np.corrcoef(chroma_mean, np.roll(prof, t))[0, 1])
            res.append((r, PITCHES[t], mode))
    res.sort(reverse=True)
    return res


METRIC_RATIOS = (0.5, 2 / 3, 1.0, 1.5, 2.0)


def _acf_peak(ac, sr, hop, bpm, tol=0.06):
    """Largest whole-file onset-ACF value within +-tol of bpm's lag, parabolic-interpolated -> (bpm, ac)."""
    lag = 60.0 / bpm * sr / hop
    lo, hi = max(1, int(np.floor(lag * (1 - tol)))), min(len(ac) - 2, int(np.ceil(lag * (1 + tol))))
    i = lo + int(np.argmax(ac[lo:hi + 1]))
    a, b, c = ac[i - 1], ac[i], ac[i + 1]
    d = 0.5 * (a - c) / (a - 2 * b + c) if (a - 2 * b + c) != 0 else 0.0
    d = float(np.clip(d, -0.5, 0.5))
    return 60.0 / ((i + d) * hop / sr), float(b - 0.25 * (a - c) * d)


TEMPO_PRIOR_BPM, TEMPO_PRIOR_OCT = 105.0, 0.6


def _tempo(oenv, sr, hop=HOP, lo=40.0, hi=200.0):
    """librosa.feature.tempo (default 120-BPM log-normal prior, mean-aggregated local tempogram) gives the raw
    call T. Metrical-level resolution: for T x {1/2, 2/3, 1, 3/2, 2} inside [lo, hi] BPM, take the peak of the
    WHOLE-FILE onset autocorrelation (mean-removed, ac[0]=1) within +-6 % of each candidate's lag (parabolic
    sub-lag interpolation), weight it by a log-normal tempo prior (TEMPO_PRIOR_BPM, TEMPO_PRIOR_OCT octaves) and
    return the best. Prior chosen on the house catalogue (mir-tools-v1 tempo_validation: 25/26 files within 4 %;
    raw librosa 19/26, unweighted ACF 10/26). Returns (bpm, raw librosa bpm, candidate table, margin = best
    weighted score / runner-up; < ~1.3 means the metrical level is ambiguous)."""
    raw = float(librosa.feature.tempo(onset_envelope=oenv, sr=sr, hop_length=hop)[0])
    ac = librosa.autocorrelate(oenv - oenv.mean())
    ac = ac / ac[0]
    cands = []
    for r in METRIC_RATIOS:
        if lo <= raw * r <= hi:
            bpm, v = _acf_peak(ac, sr, hop, raw * r)
            w = v * float(np.exp(-0.5 * (np.log2(bpm / TEMPO_PRIOR_BPM) / TEMPO_PRIOR_OCT) ** 2))
            cands.append(dict(ratio=round(r, 4), bpm=round(bpm, 2), acf=round(v, 4), score=round(w, 4)))
    sc = sorted((c['score'] for c in cands), reverse=True)
    best = max(cands, key=lambda c: c['score'])
    margin = sc[0] / sc[1] if len(sc) > 1 and sc[1] > 0 else float('inf')
    return best['bpm'], raw, cands, round(margin, 3)


def estimate(path):
    """Tempo (see _tempo: librosa.feature.tempo raw call + whole-file onset-ACF metrical-level resolution; both
    reported), key (Krumhansl-Schmuckler on the time-mean of chroma_cqt; name + Pearson r confidence + margin to
    the runner-up), and duration (decoded samples / native rate)."""
    y, sr, native, dur = _load(path)
    oenv = librosa.onset.onset_strength(y=y, sr=sr, hop_length=HOP)
    tempo, raw, cands, margin = _tempo(oenv, sr)
    cm = _chroma(y, sr).mean(1)
    ranks = _key(cm)
    r0, tonic, mode = ranks[0]
    name = f"{tonic} {mode}" + (f" (= {ENHARM[tonic]} {mode})" if tonic in ENHARM else '')
    return dict(path=path, duration_s=round(dur, 4), native_sr=native, tempo_bpm=round(tempo, 2),
                tempo_librosa_raw_bpm=round(raw, 2), tempo_candidates=cands, tempo_octave_margin=margin,
                key=f"{tonic} {mode}", key_name=name, key_confidence=round(r0, 4),
                key_margin=round(r0 - ranks[1][0], 4),
                key_ranking=[dict(key=f"{t} {m}", r=round(r, 4)) for r, t, m in ranks[:5]],
                chroma_mean=[round(float(v), 4) for v in cm / (cm.max() + 1e-12)])


def _to_grid(C, period_src, period_dst):
    """Average-pool chroma frames (period_src s) onto a coarser frame grid (period_dst s)."""
    if abs(period_src - period_dst) < 1e-9:
        return C
    n_dst = int(C.shape[1] * period_src / period_dst)
    idx = np.minimum((np.arange(C.shape[1]) * period_src / period_dst).astype(int), n_dst - 1)
    out = np.zeros((12, n_dst))
    cnt = np.bincount(idx, minlength=n_dst)[:n_dst]
    for k in range(12):
        out[k] = np.bincount(idx, weights=C[k], minlength=n_dst)[:n_dst]
    return out / np.maximum(cnt, 1)


def chroma_match(path_a, path_b, max_lag_s=2.0, gate_db=-40.0):
    """Chroma similarity 0..1 between two files.

    Method: each file -> mono, 22050 Hz, chroma_cqt at hop 512 (frame period = hop / analysis rate; with a common
    analysis rate the hops are equal, but the code pools the finer grid onto the coarser one by frame averaging if
    they ever differ). Frames are L2-normalised. Both grids start at t = 0; a single global lag in +-max_lag_s
    (whole frames) is searched, and the score is the mean frame-wise cosine similarity over the overlapping
    frames where BOTH files are active (frame RMS within gate_db of that file's max). Chroma is non-negative, so
    cosine lies in 0..1. A lag search is not a DTW: tempo differences lower the score by design.
    Also returns each file's time-mean chroma (max-normalised) and the cosine between the two means (a key-level,
    time-free similarity, reported only)."""
    out = {}
    grids = []
    for tag, p in (('a', path_a), ('b', path_b)):
        y, sr, native, dur = _load(p)
        C = _chroma(y, sr)
        rms = librosa.feature.rms(y=y, hop_length=HOP)[0][:C.shape[1]]
        rdb = 20 * np.log10(rms + 1e-12)
        grids.append(dict(C=C[:, :len(rdb)], act=rdb > rdb.max() + gate_db, period=HOP / sr))
        m = C.mean(1)
        out[f'chroma_mean_{tag}'] = [round(float(v), 4) for v in m / (m.max() + 1e-12)]
        out[f'duration_{tag}_s'] = round(dur, 4)
    period = max(g['period'] for g in grids)
    for g in grids:
        if g['period'] != period:
            g['C'] = _to_grid(g['C'], g['period'], period)
            g['act'] = _to_grid(g['act'][None].astype(float), g['period'], period)[0] > 0.5
    A, B = (g['C'] / (np.linalg.norm(g['C'], axis=0, keepdims=True) + 1e-12) for g in grids)
    aa, ab = grids[0]['act'], grids[1]['act']
    best = (-1.0, 0, 0)
    L = int(round(max_lag_s / period))
    for lag in range(-L, L + 1):           # lag > 0: b is delayed relative to a
        ia = slice(max(0, -lag), None)
        ib = slice(max(0, lag), None)
        Aa, Bb, ma, mb = A[:, ia], B[:, ib], aa[ia], ab[ib]
        n = min(Aa.shape[1], Bb.shape[1])
        mask = ma[:n] & mb[:n]
        if mask.sum() < 10:
            continue
        s = float(np.mean(np.sum(Aa[:, :n] * Bb[:, :n], 0)[mask]))
        if s > best[0]:
            best = (s, lag, int(mask.sum()))
    ma_, mb_ = np.array(out['chroma_mean_a']), np.array(out['chroma_mean_b'])
    out.update(path_a=path_a, path_b=path_b, score=round(best[0], 4), lag_s=round(best[1] * period, 4),
               frames=best[2], frame_period_s=round(period, 5),
               mean_chroma_cosine=round(float(ma_ @ mb_ / (np.linalg.norm(ma_) * np.linalg.norm(mb_))), 4))
    return out


def _cluster_grid_fit(times, period, bin_s=0.04, win_s=0.06, min_frac=0.25):
    """Fit peaks to a periodic PATTERN: phase of each peak mod `period` is histogrammed (bin_s bins, circular);
    bins holding >= min_frac of the fullest bin are cluster centres (local maxima); peaks within win_s of a
    centre are inliers; joint LS  t_i = t0[cluster_i] + P * k_i  (one shared P, one offset per cluster).
    Returns (P, residual rms s, inliers, n clusters, cluster phases s)."""
    t = np.asarray(times, float)
    P = float(period)
    for _ in range(3):
        ph = np.mod(t, P)
        nb = max(4, int(round(P / bin_s)))
        h = np.bincount(np.minimum((ph / P * nb).astype(int), nb - 1), minlength=nb)
        hs = h + 0.5 * (np.roll(h, 1) + np.roll(h, -1))
        cen = [(i + 0.5) * P / nb for i in range(nb)
               if hs[i] >= min_frac * hs.max() and hs[i] >= hs[i - 1] and hs[i] > hs[(i + 1) % nb]]
        if not cen:
            break
        cen = np.array(cen)
        d = (ph[:, None] - cen[None, :] + P / 2) % P - P / 2           # circular phase distance
        c = np.argmin(np.abs(d), 1)
        keep = np.abs(d[np.arange(len(t)), c]) < win_s
        if keep.sum() < len(cen) + 2:
            break
        k = np.round((t - cen[c] - d[np.arange(len(t)), c]) / P)       # cycle index
        X = np.zeros((keep.sum(), len(cen) + 1))
        X[np.arange(keep.sum()), c[keep]] = 1.0
        X[:, -1] = k[keep]
        sol, *_ = np.linalg.lstsq(X, t[keep], rcond=None)
        P = float(sol[-1])
        res = t[keep] - X @ sol
    return P, float(np.sqrt(np.mean(res ** 2))), int(keep.sum()), len(cen), [round(float(v), 4) for v in cen]


def _match(est, ref, tol=0.05):
    """Greedy one-to-one match of est to ref times within tol s -> (matched, precision, recall, median offset s)."""
    est, ref = np.asarray(est), np.asarray(ref)
    used = np.zeros(len(ref), bool)
    offs = []
    for e in est:
        j = np.argmin(np.where(used, np.inf, np.abs(ref - e))) if len(ref) else None
        if j is not None and not used[j] and abs(ref[j] - e) <= tol:
            used[j] = True
            offs.append(e - ref[j])
    m = len(offs)
    return m, m / max(len(est), 1), m / max(len(ref), 1), float(np.median(offs)) if offs else float('nan')


def beat_track(path, kick_fmax=150.0, ref_kicks=None, lo_s=0.25, hi_s=4.5):
    """Beat times + onset-envelope peaks + a kick grid.

    beats: librosa.beat.beat_track on the full-band onset envelope, driven at the tempo _tempo() resolves (the same
        octave-resolved figure estimate() reports; no external seed).
    onset_peaks: librosa.onset.onset_detect on the full-band envelope (s).
    kick_peaks: onset_detect on the onset envelope of mel bands <= kick_fmax Hz (s).
    kick grid: the kick envelope's whole-file autocorrelation picks the strongest repetition period in
        [lo_s, hi_s] s (parabolic sub-lag); that period seeds _cluster_grid_fit on the kick peaks (pattern-aware: a
        kick pattern like 1 / a-of-2 / 3 is several phase clusters sharing one period). grid_period_s is the
        fitted period; grid_beats_at_tempo = period / (60 / tempo_bpm) says how many beats it spans.
    ref_kicks (optional list of s): independent ground truth -> match stats (+-50 ms) for kick_peaks."""
    y, sr, native, dur = _load(path)
    oenv = librosa.onset.onset_strength(y=y, sr=sr, hop_length=HOP)
    tempo, raw, cands, margin = _tempo(oenv, sr)
    _, beats = librosa.beat.beat_track(onset_envelope=oenv, sr=sr, hop_length=HOP, bpm=tempo)
    bt = librosa.frames_to_time(beats, sr=sr, hop_length=HOP)
    ons = librosa.onset.onset_detect(onset_envelope=oenv, sr=sr, hop_length=HOP, units='time')
    S = librosa.feature.melspectrogram(y=y, sr=sr, hop_length=HOP, n_mels=128, fmax=sr / 2)
    low = librosa.mel_frequencies(n_mels=128, fmax=sr / 2) <= kick_fmax
    kenv = librosa.onset.onset_strength(S=librosa.power_to_db(S[low]), sr=sr, hop_length=HOP)
    kp = librosa.onset.onset_detect(onset_envelope=kenv, sr=sr, hop_length=HOP, units='time')
    ac = librosa.autocorrelate(kenv - kenv.mean())
    ac = ac / ac[0]
    fr = HOP / sr
    lags = np.arange(int(lo_s / fr), int(hi_s / fr) + 1)
    L = int(lags[np.argmax(ac[lags])])
    acf_period, acf_val = _acf_peak(ac, sr, HOP, 60.0 / (L * fr), tol=0.03)
    acf_period = 60.0 / acf_period
    kP, kres, kn, ncl, cph = _cluster_grid_fit(kp, acf_period)
    bd = np.diff(bt)
    bP = float(np.polyfit(np.arange(len(bt)), bt, 1)[0]) if len(bt) > 4 else float('nan')
    beat_s = 60.0 / tempo
    out = dict(path=path, duration_s=round(dur, 4), tempo_bpm=round(tempo, 2), tempo_librosa_raw_bpm=round(raw, 2),
               tempo_octave_margin=margin,
               beat_times=[round(float(v), 4) for v in bt], n_beats=len(bt),
               beat_period_s=round(bP, 5), beat_bpm=round(60 / bP, 3),
               beat_ioi_median_s=round(float(np.median(bd)), 5) if len(bd) else None,
               onset_peaks=[round(float(v), 4) for v in ons], n_onsets=len(ons),
               kick_peaks=[round(float(v), 4) for v in kp], n_kick_peaks=len(kp),
               kick_grid=dict(acf_period_s=round(acf_period, 5), acf=round(acf_val, 4), period_s=round(kP, 5),
                              residual_rms_s=round(kres, 4), inliers=kn, clusters=ncl, cluster_phases_s=cph),
               grid_period_s=round(kP, 5), grid_beats_at_tempo=round(kP / beat_s, 3),
               grid_bpm=round(60.0 * round(kP / beat_s) / kP, 3) if round(kP / beat_s) else None)
    if ref_kicks is not None:
        m, prec, rec, off = _match(kp, ref_kicks)
        out['kick_vs_ref'] = dict(ref=len(ref_kicks), matched=m, precision=round(prec, 3), recall=round(rec, 3),
                                  median_offset_s=round(off, 4))
    return out


def _main(argv):
    if len(argv) < 2 or argv[0] not in ('estimate', 'chroma', 'beats'):
        print(__doc__); return 2
    if argv[0] == 'estimate':
        r = estimate(argv[1])
    elif argv[0] == 'chroma':
        r = chroma_match(argv[1], argv[2])
    else:
        ref = None
        if '--ref' in argv:                    # --ref sidecar.json[:key]  (list of seconds; default key 'kick')
            spec = argv[argv.index('--ref') + 1]
            f, _, key = spec.partition(':')
            ref = json.load(open(f))[key or 'kick']
        r = beat_track(argv[1], ref_kicks=ref)
        if '--full' not in argv:
            r = {k: (f"[{len(v)} values]" if isinstance(v, list) and len(v) > 12 else v) for k, v in r.items()}
    print(json.dumps(r, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(_main(sys.argv[1:]))
