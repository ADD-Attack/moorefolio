"""loopcheck(): the full loop audit in one call (studio-tools-v2, 2026-10-22).

loopcheck(path, bpm, bars, beats_per_bar=4, passes=4, start_offset_samples=0, quiet=False)
  path: the LOOP file (WAV/FLAC; never the MP3 — encoder padding breaks the join).
  start_offset_samples: the file starts this many samples AFTER the bar-1 downbeat (e.g. a zero-crossing start);
      interior bar lines are placed at round(b * bar_s * sr) - offset.
Measures (decoded at native rate, lessons 30/31, SOP §7):
  samples, duration_s, expected_s (bars x beats x 60/bpm) and the sample delta to round(expected*sr)
  seam_step: max over channels |x[0] - x[-1]| (sample continuity across the wrap), against the file's
      99th-percentile interior one-sample step
  join_db[w] for w in 0.2/0.4 s: RMS dB of the w after the seam minus the w before it (wrapping), next to
      the same quantity at every interior bar line -> interior min/max, `inside` (join within that range) and
      `not_above` (join <= interior max: the gate-relevant reading; a join below every bar line is not a bump)
  tile (passes copies, written to a temp 24-bit WAV): jumps >0.35 both conventions, integrated LUFS, LRA,
      true peak — the looped figures
  file true peak + integrated (one pass), sample peak, mono fold delta = RMS((L+R)/2) - RMS(stereo), dB
Returns a dict; prints a short table unless quiet.
"""
import os
import tempfile

import numpy as np

from .ab_pair import write_wav24
from .qa import JUMP, decode, ebur128


def _db(s):
    return 20 * np.log10(np.sqrt(np.mean(s ** 2)) + 1e-12)


def loopcheck(path, bpm, bars, beats_per_bar=4, passes=4, start_offset_samples=0, quiet=False):
    x, sr = decode(path)
    n = len(x)
    bar_s = beats_per_bar * 60.0 / bpm
    exp_s = bars * bar_s
    tiled = np.concatenate([x, x, x])           # wrap-safe window reads around the seam
    def step(i, w):
        W = int(round(w * sr)); i += n
        return float(_db(tiled[i:i + W]) - _db(tiled[i - W:i]))
    lines = [round(b * bar_s * sr) - start_offset_samples for b in range(1, bars)]
    join = {}
    for w in (0.2, 0.4):
        inner = [step(i, w) for i in lines]
        j = step(0, w)
        join[f'{w:.1f}s'] = dict(join_db=round(j, 2), interior_min=round(min(inner), 2), interior_max=round(max(inner), 2),
                                 inside=bool(min(inner) <= j <= max(inner)), not_above=bool(j <= max(inner)))
    seam = float(np.abs(x[0] - x[-1]).max())
    p99 = float(np.percentile(np.abs(np.diff(x, axis=0)).max(1), 99))
    I1, LRA1, tp1, _ = ebur128(path)
    t = np.tile(x, (passes, 1))
    jm = np.abs(np.diff(t, axis=0)) > JUMP
    fd, tmp = tempfile.mkstemp(suffix='.wav'); os.close(fd)
    try:
        write_wav24(tmp, t, sr)
        It, LRAt, tpt, _ = ebur128(tmp)
    finally:
        os.remove(tmp)
    mono = x.mean(1) if x.shape[1] == 2 else x[:, 0]
    r = dict(path=path, sr=sr, samples=n, duration_s=round(n / sr, 5), expected_s=round(exp_s, 5),
             expected_samples=round(exp_s * sr), sample_delta=n - round(exp_s * sr),
             seam_step=round(seam, 4), interior_step_p99=round(p99, 4), join=join,
             tile=dict(passes=passes, jump_positions=int(jm.any(1).sum()), jump_channel_events=int(jm.sum()),
                       integrated_lufs=It, lra_lu=LRAt, true_peak_dbtp=tpt),
             file=dict(integrated_lufs=I1, lra_lu=LRA1, true_peak_dbtp=tp1, peak=round(float(np.abs(x).max()), 4)),
             mono_fold_db=round(float(_db(mono) - _db(x)), 2))
    if not quiet:
        print(f"LOOPCHECK {os.path.basename(path)}: {n} samples = {r['duration_s']} s (expected {r['expected_s']} s, "
              f"delta {r['sample_delta']} smp) | seam step {r['seam_step']} (interior p99 {r['interior_step_p99']})")
        for k, v in join.items():
            print(f"  join {k}: {v['join_db']:+.2f} dB vs interior {v['interior_min']:+.2f}..{v['interior_max']:+.2f}"
                  f" -> {'inside' if v['inside'] else ('below range (quieter than every bar line)' if v['not_above'] else 'ABOVE RANGE')}")
        tl = r['tile']
        print(f"  {passes}-pass tile: jumps {tl['jump_positions']}/{tl['jump_channel_events']} | {tl['integrated_lufs']} LUFS"
              f" | TP {tl['true_peak_dbtp']} dBTP || one pass: {I1} LUFS, TP {tp1} dBTP, peak {r['file']['peak']}"
              f" | mono fold {r['mono_fold_db']:+.2f} dB")
    return r
