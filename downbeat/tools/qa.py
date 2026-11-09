"""qa(path): the standard QA battery as one call. Returns a dict and prints a table.

Decoding: ffmpeg -> float32 at the file's NATIVE sample rate (never resampled).
Loudness: ffmpeg's `ebur128` filter (libavfilter, EBU R128 / ITU-R BS.1770; installed at /usr/bin/ffmpeg)
— integrated LUFS, LRA, true peak (peak=true), and the 3 s short-term (S) series at 0.1 s steps used for
the section ST-LUFS arc. (used when pyloudnorm is unavailable.)

Measures
  duration_s, peak (decoded sample peak), true_peak_dbtp, integrated_lufs, lra_lu
  jumps: |x[n]-x[n-1]| > 0.35 FS — BOTH conventions, named:
      jump_positions      = samples n where ANY channel jumps
      jump_channel_events = sum over channels of jumping samples
  sections: per section RMS dB, mean/max short-term LUFS, onset density (onsets/s from half-wave
      rectified spectral flux, 2048/512 STFT, peak-picked at median+2·MAD, ≥50 ms apart)
  bands: L/R correlation <200 Hz, 200–2000 Hz, >2000 Hz, full band, and >300 Hz;
      sub200_side_db = side/mid energy ratio below 200 Hz (mono-lows check: pass if < -20 dB)
  trailing_silence_s: trailing run with every channel below -90 dBFS (house convention)

  REPORT-ONLY perceptual meters (never gate or mix to these):
    harsh_3_6k_db / harsh_6_16k_db: band energy (Welch PSD) 3-6 kHz and 6-16 kHz relative to 300-1500 Hz, dB,
        per section + overall. Register direction only: a "flap" artefact once lived in these bands (no threshold).
    crest_db: sample peak / RMS, dB; plr_db: peak-to-loudness = sample peak dBFS - section mean ST LUFS.
    limiter_gr: qa() cannot know gain reduction from audio alone. A build whose master chain can report it passes
        limiter_gr=dict(max_db=..., per_section={name: db}) and qa() prints it verbatim, labelled build-reported.

sections: list of (name, start_s, end_s); default = 8 equal slices.
"""
import json
import re
import subprocess

import numpy as np
from scipy import signal

JUMP = 0.35


def decode(path):
    info = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a:0', '-show_entries',
                                      'stream=sample_rate,channels', '-of', 'json', path],
                                     capture_output=True, text=True, check=True).stdout)['streams'][0]
    sr, ch = int(info['sample_rate']), int(info['channels'])
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'f32le', '-acodec', 'pcm_f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, ch).astype(np.float64), sr


def ebur128(path):
    err = subprocess.run(['ffmpeg', '-nostats', '-v', 'verbose', '-i', path, '-af', 'ebur128=framelog=verbose:peak=true',
                          '-f', 'null', '-'], capture_output=True, text=True).stderr
    st = []
    for m in re.finditer(r't:\s*([\d.]+)\s+TARGET.*?S:\s*(-?[\d.]+|-inf)', err):
        st.append((float(m.group(1)), float(m.group(2)) if m.group(2) != '-inf' else -120.0))
    summ = err[err.rfind('Summary:'):]
    I = float(re.search(r'I:\s*(-?[\d.]+) LUFS', summ).group(1))
    LRA = float(re.search(r'LRA:\s*(-?[\d.]+) LU', summ).group(1))
    tp = re.search(r'Peak:\s*(-?[\d.]+|-inf) dBFS', summ)
    return I, LRA, (float(tp.group(1)) if tp and tp.group(1) != '-inf' else None), np.array(st)


def onsets(mono, sr):
    f, t, Z = signal.stft(mono, sr, nperseg=2048, noverlap=2048 - 512)
    mag = np.log1p(np.abs(Z) * 100)
    flux = np.maximum(np.diff(mag, axis=1), 0).sum(axis=0)
    med = signal.medfilt(flux, 31)
    mad = np.median(np.abs(flux - np.median(flux))) + 1e-9
    pk, _ = signal.find_peaks(flux, height=med + 2 * mad, distance=max(1, int(0.05 * sr / 512)))
    return t[1:][pk]


def _corr(a, b):
    return float(np.corrcoef(a, b)[0, 1]) if a.std() > 0 and b.std() > 0 else 1.0


def harsh(seg, sr):
    """(3-6k, 6-16k) energy vs 300-1500 Hz, dB. REPORT-ONLY."""
    m = seg.mean(axis=1) if seg.ndim == 2 else seg
    if len(m) < 4096:
        return None, None
    f, P = signal.welch(m, sr, nperseg=4096)
    e = lambda lo, hi: float(P[(f >= lo) & (f < hi)].sum()) + 1e-30
    ref = e(300, 1500)
    return round(10 * np.log10(e(3000, 6000) / ref), 2), round(10 * np.log10(e(6000, min(16000, sr / 2)) / ref), 2)


def qa(path, sections=None, quiet=False, limiter_gr=None):
    x, sr = decode(path)
    n, ch = x.shape
    dur = n / sr
    peak = float(np.abs(x).max())
    jm = np.abs(np.diff(x, axis=0)) > JUMP
    I, LRA, tp, st = ebur128(path)
    if sections is None:
        sections = [(f'S{i+1}', dur * i / 8, dur * (i + 1) / 8) for i in range(8)]
    mono = x.mean(axis=1)
    on = onsets(mono, sr)
    rows = []
    for name, a, b in sections:
        seg = x[int(a * sr):int(b * sr)]
        rms = 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-12)
        sel = st[(st[:, 0] > a + 0.05) & (st[:, 0] <= b + 0.05), 1] if len(st) else np.array([])
        sel = sel[sel > -70]
        rows.append(dict(name=name, start=round(a, 3), end=round(b, 3), rms_db=round(float(rms), 2),
                         st_lufs_mean=round(float(10 * np.log10(np.mean(10 ** (sel / 10)))), 2) if len(sel) else None,
                         st_lufs_max=round(float(sel.max()), 2) if len(sel) else None,
                         onsets_per_s=round(float(np.sum((on >= a) & (on < b)) / max(b - a, 1e-9)), 2)))
        h3, h6 = harsh(seg, sr)
        pk = 20 * np.log10(np.abs(seg).max() + 1e-12)
        ro = dict(harsh_3_6k_db=h3, harsh_6_16k_db=h6, crest_db=round(float(pk - rms), 2),
                  plr_db=round(float(pk - rows[-1]['st_lufs_mean']), 2) if rows[-1]['st_lufs_mean'] is not None else None)
        rows[-1]['report_only'] = ro
    bands = {}
    if ch == 2:
        L, R = x[:, 0], x[:, 1]
        for nm, kw in [('lt200', dict(btype='lowpass', Wn=200)), ('200_2k', dict(btype='bandpass', Wn=[200, 2000])),
                       ('gt2k', dict(btype='highpass', Wn=2000)), ('gt300', dict(btype='highpass', Wn=300))]:
            sos = signal.butter(4, fs=sr, output='sos', **kw)
            bands[nm] = round(_corr(signal.sosfilt(sos, L), signal.sosfilt(sos, R)), 3)
        bands['full'] = round(_corr(L, R), 3)
        sos = signal.butter(6, 200, fs=sr, output='sos')
        M, S = signal.sosfilt(sos, (L + R) / 2), signal.sosfilt(sos, (L - R) / 2)
        bands['sub200_side_db'] = round(float(10 * np.log10((np.mean(S ** 2) + 1e-20) / (np.mean(M ** 2) + 1e-20))), 1)
        bands['sub200_mono_ok'] = bands['sub200_side_db'] < -20
    loud = np.abs(x).max(axis=1) >= 10 ** (-90 / 20)
    trail = (n - 1 - int(np.nonzero(loud)[0][-1])) / sr if loud.any() else dur
    res = dict(path=path, sr=sr, channels=ch, duration_s=round(dur, 3), peak=round(peak, 4),
               true_peak_dbtp=tp, integrated_lufs=I, lra_lu=LRA,
               jump_positions=int(jm.any(axis=1).sum()), jump_channel_events=int(jm.sum()),
               worst_jump=round(float(np.abs(np.diff(x, axis=0)).max()), 4),
               onsets_total=int(len(on)), onsets_per_s=round(len(on) / dur, 2),
               trailing_silence_s=round(trail, 3), bands=bands, sections=rows)
    h3, h6 = harsh(x, sr)
    res['report_only'] = dict(label='REPORT-ONLY: not a gate, do not mix to it',
                              harsh_3_6k_db=h3, harsh_6_16k_db=h6,
                              crest_db=round(float(20 * np.log10(peak + 1e-12) - 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)), 2),
                              plr_db=round(float(20 * np.log10(peak + 1e-12) - I), 2),
                              limiter_gr=dict(limiter_gr, source='build-reported') if limiter_gr else 'not reported (needs build hook)')
    if not quiet:
        print_table(res)
    return res


def print_table(r):
    print(f"QA {r['path']}  ({r['sr']} Hz native, {r['channels']} ch)")
    print(f"  duration {r['duration_s']:.3f} s | peak {r['peak']:.4f} | true peak {r['true_peak_dbtp']} dBTP")
    print(f"  integrated {r['integrated_lufs']} LUFS | LRA {r['lra_lu']} LU | onsets {r['onsets_per_s']}/s")
    print(f"  jumps >{JUMP}: positions(any ch) {r['jump_positions']} | per-channel events "
          f"{r['jump_channel_events']} | worst {r['worst_jump']}")
    print(f"  trailing silence {r['trailing_silence_s']} s | bands {r['bands']}")
    print(f"  {'section':10s} {'start':>8s} {'end':>8s} {'RMS dB':>8s} {'ST mean':>8s} {'ST max':>8s} {'onset/s':>8s}")
    for s in r['sections']:
        print(f"  {s['name']:10s} {s['start']:8.2f} {s['end']:8.2f} {s['rms_db']:8.2f} "
              f"{str(s['st_lufs_mean']):>8s} {str(s['st_lufs_max']):>8s} {s['onsets_per_s']:8.2f}")
    ro = r['report_only']
    print(f"  REPORT-ONLY meters (not gates): overall 3-6k {ro['harsh_3_6k_db']} dB | 6-16k {ro['harsh_6_16k_db']} dB "
          f"(vs 300-1500 Hz) | crest {ro['crest_db']} dB | PLR {ro['plr_db']} dB | limiter GR {ro['limiter_gr']}")
    print(f"  {'section':10s} {'3-6k':>8s} {'6-16k':>8s} {'crest':>8s} {'PLR':>8s}   [REPORT-ONLY]")
    for s in r['sections']:
        o = s['report_only']
        print(f"  {s['name']:10s} {str(o['harsh_3_6k_db']):>8s} {str(o['harsh_6_16k_db']):>8s} {o['crest_db']:8.2f} {str(o['plr_db']):>8s}")


if __name__ == '__main__':
    import sys
    qa(sys.argv[1])
