"""noise_bus(): band-limited noise source for synth drums and swells — band-limited BY DEFAULT.

Every big click count on record came from broadband noise (earlier builds measured 1,120, 735 and
12,659 jumps from unfiltered noise). Preset bands, all 4th-order Butterworth (sosfilt), from the evidence:
  'hat'    6000–10000 Hz, gain 0.7   10 kHz 4th-order LP on the drum bus + hats ×0.7 -> 0–9 jumps
  'snare'   180–10000 Hz, gain 1.0   snare/shaker noise under the same 10 kHz LP
  'shaker' 3000–10000 Hz, gain 0.7
  'swell'   700–4000 Hz,  gain 0.45  a rain swell at 900–6500 @0.6 made 677 clicks; 700–4000 + 4 kHz LP @0.45 -> 0
band=None/gain=None take the preset; override with band=(lo, hi) / gain=. Full-band noise must be asked
for explicitly with band=(0, sr/2). Still scan per-bus jumps at master gain (qa) — the preset is a start.
"""
import numpy as np
from scipy import signal

PRESETS = {'hat': ((6000, 10000), 0.7), 'snare': ((180, 10000), 1.0),
           'shaker': ((3000, 10000), 0.7), 'swell': ((700, 4000), 0.45)}


def noise_bus(n, sr=44100, kind='snare', band=None, gain=None, seed=None, order=4):
    """Return n samples of band-limited white noise (float64, nominal peak <= ~gain)."""
    pb, pg = PRESETS[kind]
    lo, hi = band if band is not None else pb
    g = pg if gain is None else gain
    x = np.random.default_rng(seed).standard_normal(n) / 4.0
    nyq = sr / 2
    if lo > 0 and hi < nyq:
        sos = signal.butter(order, [lo, hi], btype='bandpass', fs=sr, output='sos')
    elif hi < nyq:
        sos = signal.butter(order, hi, btype='lowpass', fs=sr, output='sos')
    elif lo > 0:
        sos = signal.butter(order, lo, btype='highpass', fs=sr, output='sos')
    else:
        return x * g
    return signal.sosfilt(sos, x) * g
