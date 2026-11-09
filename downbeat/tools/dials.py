"""Expression dials — deterministic performance layer. Nothing here is called by
existing tools; every dial is opt-in per part, and a dial at its neutral setting returns its input unchanged.

VIBRATO  (delay_s, depth_cents, rate_hz) — theremin-style vibrato: land on pitch centre, hold it for delay_s,
  then fade the modulation in over fade_s (default 0.15 s); +-depth_cents sine at rate_hz, phase 0 at the
  fade-in start (so it leaves pitch centre smoothly), back to centre at note-off.
  - vibrato_hook(notes, bpm, dial, ...) -> a function for render_part(..., _midi_hook=...): writes MIDI pitch
    bend every step_s (default 10 ms) inside each note. Reaches: any sfz voice rendered through sfizz (sfizz's
    default bend range +-200 cents; depth must be < 200). MONOPHONIC parts only — pitch bend is per channel, so
    overlapping notes would share one vibrato (asserted). Cannot reach: patches with baked-in vibrato samples
    (VSCO *SusVib, VPO solo strings) — it adds on top, it cannot remove theirs; the legato path
    (render_part(legato=True)) which writes its own bends — not combined here; audio files already rendered.
  - vibrato_cents(t, dur, dial) -> per-sample cents curve for one note, for the numpy synth path (multiply the
    note's f0 by 2**(c/1200) before integrating phase). Reaches every synth voice that integrates phase.
SWING  pct (0 = straight) — swing(notes, pct, grid=0.5): for each pair of `grid`-beat subdivisions the off-beat
  point moves late by pct% of one subdivision (33.3 = triplet feel), via an exact piecewise-linear time warp
  of every onset and note-off (on-beat points are fixed, so durations stay inside their pair). No randomness.
  Opt-in per part: call it on the parts that swing; machine layers simply aren't passed.
ATTACK  db — attack(x, onsets_s, db, sr, window_s=0.04, split_hz=2000): scales the >split_hz band by db over
  [onset, onset+window_s] (raised-cosine release over the back half of the window) using a zero-phase
  sosfiltfilt split (a causal subtracted band copy under-delivers). Measured by hf_onset_db().
"""
import numpy as np
from scipy import signal

TPQ = 480


# ---------------------------------------------------------------- vibrato
def vibrato_cents(t, dur, dial, fade_s=0.15):
    """t: array of seconds since note onset. Returns cents (0 before delay, 0 at/after dur)."""
    delay, depth, rate = dial
    t = np.asarray(t, dtype=float)
    u = t - delay
    env = np.clip(u / fade_s, 0, 1) if fade_s > 0 else (u >= 0).astype(float)
    c = depth * env * np.sin(2 * np.pi * rate * np.maximum(u, 0))
    c[(t >= dur) | (u < 0)] = 0.0
    return c


HUMANISE_DEFAULT = dict(seed=1, delay_add=(0.1, 0.6), delay_jitter=0.03, depth_range=(-0.20, 0.05),
                        depth_jitter=0.02, rate_centre=(-0.09, 0.04), rate_drift=(0.06, 0.20),
                        rate_bounds=(4.6, 6.1), swell=(0.10, 0.18), swell_hz=0.35, ramp_s=0.8, tail_s=0.5,
                        level_match=False)
# v3: defaults reproduce a hand-tuned manual vibrato set: delays dial+0.1..0.6 s (0.6/0.9/1.1 at dial 0.5),
# peaks stratified across dial x [-20 %, +5 %] (16/21/18 c at 20 c) with NO rescale to mean 1 -- the line mean
# sits below the dial as the manual set's did, and no note goes more than 5 % over it (v2's +30 % read as
# theremin-like). level_match off: the manual set used raw peaks, so v3 does too.


def _floored(rng, lo, hi, n):
    """Signed draws with |x| in U(lo, hi), signs balanced across the line (half +, half -, odd one random) and
    shuffled: no note comes out near-flat and the line can't come out all one side (v2)."""
    sg = np.array([1.0, -1.0] * (n // 2) + ([rng.choice([1.0, -1.0])] if n % 2 else []))
    return rng.permutation(sg) * rng.uniform(lo, hi, n)


def _strat(rng, lo, hi, n, jit):
    """lo..hi stratified evenly across the line, shuffled, +-U(jit), clipped back inside [lo, hi]."""
    v = rng.permutation(np.linspace(lo, hi, n) if n > 1 else np.array([(lo + hi) / 2]))
    return np.clip(v + rng.uniform(-jit, jit, n), lo, hi)


def humanise_specs(n, dial, humanise):
    """Per-note (delay, depth, rate_start, rate_end, swell, swell_phase) for n notes, seeded.
    v3: delay = dial delay + delay_add stratified (+-delay_jitter); depth = dial depth x (1 + depth_range stratified,
    +-depth_jitter, clipped to the range -- no mean rescale); centre rate = dial rate x (1 + rate_centre stratified)
    with a floored, sign-balanced within-note drift (rate_drift, fraction of centre), ends clipped to rate_bounds Hz."""
    h = dict(HUMANISE_DEFAULT, **humanise)
    delay, depth, rate = dial
    rng = np.random.default_rng(h['seed'])
    d = delay + _strat(rng, *h['delay_add'], n, h['delay_jitter'])
    m = 1 + _strat(rng, *h['depth_range'], n, h['depth_jitter'])
    rc = rate * (1 + _strat(rng, *h['rate_centre'], n, 0.0))
    dr = _floored(rng, *h['rate_drift'], n)
    r = np.clip(np.stack([rc * (1 + dr / 2), rc * (1 - dr / 2)], 1), *h['rate_bounds'])
    sw = rng.uniform(*h['swell'], n); ph = rng.uniform(0, 2 * np.pi, n)
    return h, [(d[i], depth * m[i], r[i, 0], r[i, 1], sw[i], ph[i]) for i in range(n)]


def vibrato_cents_human(t, dur, spec, h):
    """Humanised curve for one note: ramp_s depth ramp, slow swell on depth, tail ease-off, drifting rate."""
    delay, depth, r0, r1, sw, ph = spec
    t = np.asarray(t, dtype=float)
    u = np.maximum(t - delay, 0)
    env = np.clip(u / h['ramp_s'], 0, 1) * (1 + sw * np.sin(2 * np.pi * h['swell_hz'] * u + ph))
    env *= np.clip((dur - t) / h['tail_s'], 0, 1)
    phase = 2 * np.pi * (r0 * u + 0.5 * (r1 - r0) * u * u / max(dur - delay, 0.1))
    c = depth * env * np.sin(phase)
    c[(t >= dur) | (t < delay)] = 0.0
    return c


def vibrato_hook(notes, bpm, dial, step_s=0.01, fade_s=0.15, humanise=None):
    """notes as given to render_part (start_beat, dur_beats, midi, vel). Returns _midi_hook(mid_path).
    humanise=None (default) -> the calibrated uniform LFO, unchanged. humanise=dict (keys of HUMANISE_DEFAULT,
    {} = defaults) -> per-note seeded delay/depth/rate-drift/swell/tail ease (vibrato-humanise-v1)."""
    from . import legato as LG
    if humanise is not None:
        return _vibrato_hook_human(notes, bpm, dial, step_s, humanise)
    delay, depth, rate = dial
    assert 0 <= depth < 200, 'depth must sit inside sfizz default +-200 cent bend range'
    s = sorted(notes)
    for a, b in zip(s, s[1:]):
        assert a[0] + a[1] <= b[0] + 1e-9, f'vibrato via pitch bend needs a monophonic part: {a} overlaps {b}'
    tps = TPQ * bpm / 60.0

    def hook(mid):
        hdr, evts = LG._parse(mid)
        add = []
        if depth > 0:
            for sb, db, m, v in s:
                on, dur = round(sb * TPQ), db * 60.0 / bpm
                ts = np.arange(delay, dur, step_s)
                c = vibrato_cents(ts, dur, dial, fade_s)
                for t, cc in zip(ts, c):
                    k = on + int(round(t * tps))
                    if k < on + round(db * TPQ):
                        add.append((k, LG._bend_bytes(cc)))
                add.append((on + round(db * TPQ), LG._bend_bytes(0)))
        # stable merge: bends at a tick go after note-offs/ons already there; EOT stays last
        eot = evts[-1]; assert eot[1][:2] == bytes([0xFF, 0x2F])
        body = sorted(evts[:-1] + add, key=lambda e: e[0])
        LG._write(mid, hdr, body + [(max(eot[0], body[-1][0]), eot[1])])
    return hook


def _level_match(sp, dur, h):
    """level_match: scale the note's depth by 1/RMS of its (ramp x swell x tail) envelope over vibrato_measure's
    window [delay+0.3, dur-0.15], so measured depth (sqrt2*std) lands on depth x multiplier like the uniform LFO."""
    if not h['level_match']:
        return sp
    t = np.arange(sp[0] + 0.3, dur - 0.15, 0.005)
    u = t - sp[0]
    env = np.clip(u / h['ramp_s'], 0, 1) * (1 + sp[4] * np.sin(2 * np.pi * h['swell_hz'] * u + sp[5]))
    env *= np.clip((dur - t) / h['tail_s'], 0, 1)
    return (sp[0], sp[1] / np.sqrt(np.mean(env ** 2)),) + tuple(sp[2:])


def _vibrato_hook_human(notes, bpm, dial, step_s, humanise):
    from . import legato as LG
    s = sorted(notes)
    h, specs = humanise_specs(len(s), dial, humanise)
    for (sb, db, _, _), sp in zip(s, specs):
        sp = _level_match(sp, db * 60.0 / bpm, h)
        assert 0 <= sp[1] * (1 + sp[4]) < 200, 'humanised peak must stay inside +-200 cent bend'
    for a, b in zip(s, s[1:]):
        assert a[0] + a[1] <= b[0] + 1e-9, f'vibrato via pitch bend needs a monophonic part: {a} overlaps {b}'
    tps = TPQ * bpm / 60.0

    def hook(mid):
        hdr, evts = LG._parse(mid)
        add = []
        if dial[1] > 0:
            for (sb, db, m, v), sp in zip(s, specs):
                on, end, dur = round(sb * TPQ), round(sb * TPQ) + round(db * TPQ), db * 60.0 / bpm
                sp = _level_match(sp, dur, h)
                ts = np.arange(sp[0], dur, step_s)
                for t, cc in zip(ts, vibrato_cents_human(ts, dur, sp, h)):
                    k = on + int(round(t * tps))
                    if k < end:
                        add.append((k, LG._bend_bytes(cc)))
                add.append((end, LG._bend_bytes(0)))
        eot = evts[-1]; assert eot[1][:2] == bytes([0xFF, 0x2F])
        body = sorted(evts[:-1] + add, key=lambda e: e[0])
        LG._write(mid, hdr, body + [(max(eot[0], body[-1][0]), eot[1])])
    hook.specs = [_level_match(sp, db * 60.0 / bpm, h) for (sb, db, _, _), sp in zip(s, specs)]
    return hook


def f0_track(x, sr, win_s=0.03, hop_s=0.005, fmin=80, fmax=1200):
    """Autocorrelation f0 (parabolic peak) per hop. Returns times, f0 (nan where unvoiced)."""
    m = x.mean(1) if x.ndim == 2 else x
    w, h = int(win_s * sr), int(hop_s * sr)
    lo, hi = int(sr / fmax), int(sr / fmin)
    ts, fs = [], []
    for i in range(0, len(m) - w - hi, h):
        seg = m[i:i + w + hi]
        if np.sqrt(np.mean(seg ** 2)) < 1e-4:
            ts.append((i + w / 2) / sr); fs.append(np.nan); continue
        a = seg[:w]
        r = np.array([np.dot(a, seg[k:k + w]) for k in range(lo, hi)])
        r /= (np.sqrt(np.dot(a, a) * np.array([np.dot(seg[k:k + w], seg[k:k + w]) for k in range(lo, hi)])) + 1e-12)
        pk = [j for j in range(1, len(r) - 1) if r[j] >= r[j - 1] and r[j] >= r[j + 1] and r[j] >= 0.9 * r.max()]
        k = pk[0] if pk else int(np.argmax(r))   # first strong lag peak: avoids sub-harmonic (2T, 3T) picks
        if r[k] < 0.8 or k == 0 or k == len(r) - 1:
            ts.append((i + w / 2) / sr); fs.append(np.nan); continue
        d = 0.5 * (r[k - 1] - r[k + 1]) / (r[k - 1] - 2 * r[k] + r[k + 1])
        ts.append((i + w / 2) / sr); fs.append(sr / (lo + k + d))
    return np.array(ts), np.array(fs)


def vibrato_measure(x, sr, onset_s, dur_s, delay_s):
    """Depth (cents, sqrt2*std about median) and rate (Hz, FFT peak) after delay+0.3 s; pre-delay depth too."""
    t, f = f0_track(x[int(onset_s * sr):int((onset_s + dur_s) * sr)], sr)
    ok = ~np.isnan(f)
    c = 1200 * np.log2(f / np.nanmedian(f[(t > delay_s + 0.3) & ok]))
    c = (c + 600) % 1200 - 600                    # fold autocorrelation octave errors back to pitch centre
    c[ok] = signal.medfilt(np.nan_to_num(c), 5)[ok]  # 25 ms median: drop single-hop outliers
    late = ok & (t > delay_s + 0.3) & (t < dur_s - 0.15)
    pre = ok & (t > 0.1) & (t < delay_s - 0.03)
    cl = c[late] - np.mean(c[late])
    F = np.abs(np.fft.rfft(cl * np.hanning(len(cl)), 8192)); fr = np.fft.rfftfreq(8192, 0.005)
    band = (fr > 1) & (fr < 15)
    return dict(depth_cents=round(float(np.sqrt(2) * np.std(cl)), 2),
                rate_hz=round(float(fr[band][np.argmax(F[band])]), 2) if F[band].max() > 0 else 0.0,
                pre_delay_depth_cents=round(float(np.sqrt(2) * np.std(c[pre])), 2) if pre.sum() > 4 else None)


# ---------------------------------------------------------------- swing
def swing_time(b, pct, grid=0.5):
    """Map a straight beat position to its swung position (exact, piecewise linear inside each 2*grid pair)."""
    s = pct / 100.0
    P = 2 * grid
    k = np.floor(b / P + 1e-12); u = b - k * P
    if u <= grid:
        v = u * (1 + s)
    else:
        v = grid * (1 + s) + (u - grid) * (1 - s)
    return k * P + v


def swing(notes, pct, grid=0.5):
    """notes: (start_beat, dur_beats, midi, vel). pct=0 returns the same list (same objects)."""
    assert 0 <= pct < 100
    if pct == 0:
        return notes
    out = []
    for sb, db, m, v in notes:
        a, e = swing_time(sb, pct, grid), swing_time(sb + db, pct, grid)
        out.append((round(a, 6), round(e - a, 6), m, v))
    return out


def detect_onsets(x, sr, split_hz=2000, min_gap_s=0.08, rel_db=-30):
    """1 ms-hop HF-envelope onset times (s): peaks of the positive log-envelope derivative."""
    m = x.mean(1) if x.ndim == 2 else x
    hp = signal.sosfiltfilt(signal.butter(4, split_hz, 'high', fs=sr, output='sos'), m)
    h = int(0.001 * sr)
    e = np.sqrt(np.convolve(hp ** 2, np.ones(h) / h, 'same')[::h] + 1e-14)
    ld = 20 * np.log10(e)
    d = np.diff(ld, prepend=ld[0])
    d = np.convolve(d, np.ones(3) / 3, 'same')
    pk, _ = signal.find_peaks(d, height=3.0 / 3, distance=int(min_gap_s * 1000))
    pk = pk[ld[np.minimum(pk + 5, len(ld) - 1)] > ld.max() + rel_db]
    return pk * h / sr


# ---------------------------------------------------------------- attack
def attack(x, onsets_s, db, sr=44100, window_s=0.04, split_hz=2000):
    """Scale the >split_hz band by db over each onset window. db=0 returns x unchanged (same object)."""
    if db == 0:
        return x
    x = np.asarray(x, dtype=float)
    sos = signal.butter(4, split_hz, 'high', fs=sr, output='sos')
    hi = signal.sosfiltfilt(sos, x, axis=0)
    W = int(window_s * sr); half = W // 2
    shape = np.ones(W); shape[half:] = 0.5 * (1 + np.cos(np.linspace(0, np.pi, W - half)))
    pre = int(0.002 * sr)                      # 2 ms raised-cosine lead-in so the gain never steps
    lead = 0.5 * (1 - np.cos(np.linspace(0, np.pi, pre)))
    g = np.zeros(len(x))
    for o in onsets_s:
        i = int(round(o * sr))
        a = max(0, i - pre)
        g[a:i] = np.maximum(g[a:i], lead[pre - (i - a):])
        seg = shape[:max(0, min(W, len(x) - i))]
        g[i:i + len(seg)] = np.maximum(g[i:i + len(seg)], seg)
    k = 10 ** (db / 20) - 1
    return x + (k * g)[:, None] * hi if x.ndim == 2 else x + k * g * hi


def hf_onset_db(x, onsets_s, sr=44100, window_s=0.04, split_hz=2000):
    """Median over onsets of >split_hz energy in [onset, onset+window_s], dB."""
    m = x.mean(1) if x.ndim == 2 else x
    hi = signal.sosfiltfilt(signal.butter(4, split_hz, 'high', fs=sr, output='sos'), m)
    W = int(window_s * sr)
    v = [10 * np.log10(np.mean(hi[int(o * sr):int(o * sr) + W] ** 2) + 1e-20) for o in onsets_s]
    return float(np.median(v))
