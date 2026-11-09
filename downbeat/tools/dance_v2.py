"""Sidecar emitter v2 — the ruled cue vocabulary.

emit_dance_v2(score, audio_path, authored, out_path) -> dict written to <out_path> (never overwrites).

Vocabulary = the cue spec (§10) + the 2D Dancers set.
  measured / derived from the score (and, for shimmer + energy, the delivered audio):
    events : pulse (strike = accent flag on pulse), thump (kick class, gesture hop), drum gestures
             (snare spin, hat flick, shaker shimmy), cascade (one event, members = pulse ids), freeze
    spans  : swell, build/release (paired, anchored on authored moments), air, legato
    channels: energy, pitch, density, shimmer (10 Hz); tension (1 Hz, candidate formula); harmony (change list)
    every event carries anticipation_s (pre-beat wind-up, Dancers rule generalised — see ANTIC)
  authored (values come from production data, the emitter writes them):
    sections: intent / action / palette / formation / stance / feel; spans: stance, feel, formation
  NOT emitted: echo, exchange (not cue data), pan, tail (deferred: mix-metadata route).

The authored dict (per track, kept in the ticket folder) supplies:
  {"source": str, "sections": {name: {intent, action, palette, formation, stance, feel}},
   "feel_settings": {...}, "moments": [{id, t, what, cite}],
   "freezes": [{at, release}], "builds": [{id, start, end, release, hit_class}]}
`at/release/start/end/release` reference moment ids, so anchors land on documented moments by construction.
"""
import hashlib
import json
import os
import subprocess

import numpy as np

EMITTER = 'v2'
VOCABULARY = 'spec-10-ruled-2026-10-25'
EXCLUDED = ('echo', 'exchange', 'pan', 'tail')          # by ruling; asserted absent from output
RATE = 10                                                # Hz, continuous channels
FORMATIONS = ('line', 'vee', 'arc', 'two_rows', 'ring_around_lead', 'zigzag', 'huddle')  # Dancers FORMS order
GESTURE = {'kick': 'hop', 'snare': 'spin', 'hat': 'flick', 'shaker': 'shimmy', 'rim': 'flick'}
# wind-up weight per class: Dancers crouch window = min(0.24 s, 0.45 beat); other classes scale it
ANTIC = {'hop': 1.0, 'cascade': 1.0, 'freeze': 1.0, 'strike': 0.6, 'spin': 0.5, 'pulse': 0.35,
         'flick': 0.25, 'shimmy': 0.15}
HARD_ATTACK_PARTS = {'piano', 'pf', 'harp', 'bass'}
P = dict(onset_merge_s=0.012, strike_pct=85, strike_local_db=10, strike_local_win_s=2.0, strike_short_s=0.2,
         cascade_ioi_s=0.18, cascade_min_notes=4, cascade_min_span=3, swell_min_s=1.0, air_all_min_s=0.5,
         air_lead_min_beats=2.0, drum_ring_s=0.1, legato_overlap_s=0.005, legato_min_s=1.0, energy_win_s=0.5,
         shimmer_fft=4096, tension_hop_s=1.0, density_win_s=1.0)
R = lambda x, n=3: round(float(x), n)  # noqa: E731

PC = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
CHORDS = {'': (0, 4, 7), 'm': (0, 3, 7), '7': (0, 4, 7, 10), 'maj7': (0, 4, 7, 11), 'm7': (0, 3, 7, 10),
          'sus4': (0, 5, 7), 'sus2': (0, 2, 7), 'dim': (0, 3, 6), '5': (0, 7)}
ROMAN = ['I', 'bII', 'II', 'bIII', 'III', 'IV', '#IV', 'V', 'bVI', 'VI', 'bVII', 'VII']


def _decode_mono(path, sr=44100):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-map', '0:a', '-ac', '1', '-ar', str(sr),
                          '-f', 'f32le', '-'], check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.float32), sr


def _norm(x, lo=None, hi=None):
    x = np.asarray(x, float)
    lo = x.min() if lo is None else lo
    hi = x.max() if hi is None else hi
    return np.clip((x - lo) / (hi - lo), 0, 1) if hi > lo else np.zeros_like(x)


def _sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


# ------------------------------------------------------------------ audio channels
def audio_channels(audio_path, n_frames):
    x, sr = _decode_mono(audio_path)
    hop = sr // RATE
    # energy: RMS dB over a centred 0.5 s window, normalised p1..p99.5 of the track
    w = int(P['energy_win_s'] * sr)
    c2 = np.concatenate([[0.0], np.cumsum(x.astype(np.float64) ** 2)])
    cen = np.arange(n_frames) * hop
    a, b = np.clip(cen - w // 2, 0, len(x)), np.clip(cen + w // 2, 0, len(x))
    rms_db = 10 * np.log10(np.maximum((c2[b] - c2[a]) / np.maximum(b - a, 1), 1e-12))
    inside = cen < len(x)                                    # score may outlast the trimmed file
    lo, hi = np.percentile(rms_db[inside], 5), np.percentile(rms_db[inside], 99.5)
    energy = _norm(rms_db, lo, hi)
    # shimmer: spectral centroid (Hz) of a Hann-windowed 4096 frame at each hop, smoothed 0.3 s
    nf = P['shimmer_fft']
    win = np.hanning(nf).astype(np.float32)
    freqs = np.fft.rfftfreq(nf, 1 / sr)
    cent = np.zeros(n_frames)
    tail = max(nf, n_frames * hop + nf - len(x))           # score may outlast the trimmed file: pad with silence
    pad = np.concatenate([np.zeros(nf // 2, np.float32), x, np.zeros(tail, np.float32)])
    for i0 in range(0, n_frames, 256):
        idx = np.arange(i0, min(n_frames, i0 + 256))
        fr = np.stack([pad[c:c + nf] for c in idx * hop]) * win
        mag = np.abs(np.fft.rfft(fr, axis=1))
        cent[idx] = (mag * freqs).sum(1) / np.maximum(mag.sum(1), 1e-9)
    loud = rms_db > lo                                       # centroid of near-silence is noise; hold
    for i in range(1, n_frames):
        if not loud[i]:
            cent[i] = cent[i - 1]
    k = np.ones(3) / 3
    cent = np.convolve(np.pad(cent, 1, mode='edge'), k, 'valid')
    shimmer = _norm(cent, np.percentile(cent, 2), np.percentile(cent, 98))
    audio_s = len(x) / sr
    return dict(energy=energy, energy_db=rms_db, shimmer=shimmer, centroid_hz=cent, audio_s=audio_s,
                norms=dict(energy_db_p5=R(lo, 2), energy_db_p99_5=R(hi, 2),
                           centroid_p2=R(np.percentile(cent, 2), 1), centroid_p98=R(np.percentile(cent, 98), 1)))


# ------------------------------------------------------------------ score-derived pieces
def pulses(notes):
    ns = sorted(notes, key=lambda n: n['t'])
    out, cur = [], []
    for n in ns:
        if cur and n['t'] - cur[0]['t'] > P['onset_merge_s']:
            out.append(cur); cur = []
        cur.append(n)
    if cur:
        out.append(cur)
    ps = []
    for i, g in enumerate(out):
        ps.append({'id': f'p{i:04d}', 't': g[0]['t'], 'type': 'pulse', 'vel': R(max(n['vel'] for n in g) / 127),
                   'n': len(g), 'parts': sorted({n['part'] for n in g}), 'lead': any(n['lead'] for n in g),
                   'midi_top': max(n['midi'] for n in g),
                   '_hard': any(n['part'] in HARD_ATTACK_PARTS or n['dur'] <= P['strike_short_s'] for n in g)})
    v = np.array([p['vel'] for p in ps]) * 127
    t = np.array([p['t'] for p in ps])
    gate = np.percentile(v, P['strike_pct'])
    for i, p in enumerate(ps):
        m = np.abs(t - t[i]) <= P['strike_local_win_s']
        local = np.median(v[m])
        p['strike'] = bool(p['_hard'] and v[i] >= max(gate, local + P['strike_local_db']))
        del p['_hard']
    return ps, dict(strike_vel_gate=R(gate, 1))


def cascades(notes, ps):
    by_t = {}
    for p in ps:
        by_t[R(p['t'], 6)] = p['id']
    pid = lambda tt: min(by_t.items(), key=lambda kv: abs(kv[0] - tt))[1]  # noqa: E731
    out = []
    for part in sorted({n['part'] for n in notes}):
        on = {}
        for n in notes:
            if n['part'] == part:
                on[n['t']] = max(on.get(n['t'], 0), n['midi'])  # top note per onset
        ts = sorted(on)
        run = [ts[0]] if ts else []
        for a, b in zip(ts, ts[1:] + [None]):
            if b is not None and b - a <= P['cascade_ioi_s']:
                run.append(b); continue
            mids = [on[x] for x in run]
            if (len(run) >= P['cascade_min_notes'] and max(mids) - min(mids) >= P['cascade_min_span']
                    and len(set(mids)) >= 3):
                d = mids[-1] - mids[0]
                out.append({'t': run[0], 'end': run[-1], 'type': 'cascade', 'part': part, 'n': len(run),
                            'direction': 'up' if d > 0 else 'down' if d < 0 else 'turn',
                            'midi_lo': min(mids), 'midi_hi': max(mids), 'members': [pid(x) for x in run]})
            run = [b] if b is not None else []
    out.sort(key=lambda c: c['t'])
    merged = []                                              # runs sharing pulses (e.g. harp + piano roll) = one gesture
    for c in out:
        c['parts'] = [c.pop('part')]
        m = next((x for x in merged if set(x['members']) & set(c['members'])), None)
        if m is None:
            merged.append(c); continue
        m['members'] = sorted(set(m['members']) | set(c['members']))
        m['parts'] = sorted(set(m['parts']) | set(c['parts']))
        m['end'], m['n'] = max(m['end'], c['end']), len(m['members'])
        m['midi_lo'], m['midi_hi'] = min(m['midi_lo'], c['midi_lo']), max(m['midi_hi'], c['midi_hi'])
        if m['direction'] != c['direction']:
            m['direction'] = 'mixed'
    out = merged
    for i, c in enumerate(out):
        c['id'] = f'c{i:03d}'
    return out


def drum_events(score, sec_energy_at, energy_at, beat):
    out = []
    counts = {}
    for role, ts in score['drums'].items():
        g = GESTURE.get(role, 'flick')
        for t in ts:
            k = counts[role] = counts.get(role, 0) + 1
            ph = (t / beat) % 4
            e = {'t': t, 'type': 'thump' if role == 'kick' else 'gesture', 'drum': role, 'gesture': g}
            if role == 'kick':
                e['strength'] = 1.0 if min(ph, 4 - ph) < 0.05 else 0.7     # bar-line kick vs pushed kick
                inten = 0.5 * energy_at(t) + 0.5 * sec_energy_at(t)      # Dancers intensity()
                e['hop_group'] = 'all' if inten > 0.78 else ('even' if k % 2 == 0 else 'odd')
            elif role == 'snare':
                e['spin_group'] = 'even' if k % 2 == 0 else 'odd'         # Dancers (i + snareCount) % 2
                e['lead_spins'] = k % 4 == 0
            out.append(e)
    return out


def anticipation(events, beat):
    """Dancers crouch window min(0.24, 0.45*beat), scaled per class, clipped to 0.45 x gap since prev same class."""
    base = min(0.24, 0.45 * beat)
    last = {}
    for e in sorted(events, key=lambda e: e['t']):
        cls = e.get('gesture') or ('strike' if e.get('strike') else e['type'])
        a = base * ANTIC.get(cls, 0.35)
        if cls in last:
            a = min(a, 0.45 * (e['t'] - last[cls]))
        e['anticipation_s'] = R(max(a, 0.01), 3)
        last[cls] = e['t']


def harmony(notes, duration, beat, key_pc):
    """Per-beat pitch-class profile of sounding non-lead notes (dur-overlap x vel, bass x2) -> chord template."""
    acc = [n for n in notes if not n['lead']]
    nb = int(np.ceil(duration / beat))
    lowest = {}
    prof = np.zeros((nb, 12))
    for n in acc:
        b0, b1 = int(n['t'] // beat), int(min(nb - 1, (n['t'] + n['dur']) // beat))
        for b in range(b0, b1 + 1):
            ov = min(n['t'] + n['dur'], (b + 1) * beat) - max(n['t'], b * beat)
            if ov <= 0:
                continue
            prof[b, n['midi'] % 12] += ov * n['vel'] * (2.0 if n['midi'] < 52 else 1.0)
            if n['midi'] < lowest.get(b, (999,))[0]:
                lowest[b] = (n['midi'], n['midi'] % 12)
    labels = []
    for b in range(nb):
        pr = prof[b]
        if pr.sum() <= 0:
            labels.append(None); continue
        best, bs = None, -1e9
        for r in range(12):
            for q, iv in CHORDS.items():
                inn = sum(pr[(r + i) % 12] for i in iv)
                s = inn - 0.6 * (pr.sum() - inn) - 0.08 * len(iv) * pr.max()
                if b in lowest and lowest[b][1] == r:
                    s += 0.05 * pr.max()
                if s > bs:
                    best, bs = (r, q), s
        labels.append(best)
    # suppress one-beat flickers between equal neighbours
    for b in range(1, nb - 1):
        if labels[b - 1] == labels[b + 1] and labels[b] != labels[b - 1]:
            labels[b] = labels[b - 1]
    out = []
    for b, lab in enumerate(labels):
        name = 'N.C.' if lab is None else PC[lab[0]] + lab[1]
        if out and out[-1]['chord'] == name:
            continue
        rec = {'t': R(b * beat, 6), 'chord': name}
        if lab is None:
            rec.update(root='none', quality='none', roman='N.C.')
        else:
            rec.update(root=PC[lab[0]], quality=lab[1] or 'maj',
                       roman=ROMAN[(lab[0] - key_pc) % 12] + ('' if lab[1] in ('', '7', 'maj7', '5', 'sus4', 'sus2')
                                                              else lab[1]))
        out.append(rec)
    return out


def spans_from_notes(notes, drums, duration, beat):
    lead = sorted((n for n in notes if n['lead']), key=lambda n: n['t'])
    sw = [{'t': n['t'], 'end': R(n['t'] + n['dur'], 6), 'type': 'swell', 'part': n['part'], 'midi': n['midi'],
           'vel': R(n['vel'] / 127)} for n in lead if n['dur'] >= P['swell_min_s']]
    # air, scope all: nothing notated sounding (drum hits ring drum_ring_s)
    iv = sorted([(n['t'], n['t'] + n['dur']) for n in notes] +
                [(t, t + P['drum_ring_s']) for ts in drums.values() for t in ts])
    air, cur = [], 0.0
    for a, b in iv:
        if a - cur >= P['air_all_min_s']:
            air.append({'t': R(cur, 6), 'end': R(a, 6), 'type': 'air', 'scope': 'all'})
        cur = max(cur, b)
    if duration - cur >= P['air_all_min_s']:
        air.append({'t': R(cur, 6), 'end': R(duration, 6), 'type': 'air', 'scope': 'all'})
    cur, thr = 0.0, P['air_lead_min_beats'] * beat
    for n in lead + [{'t': duration, 'dur': 0}]:
        if n['t'] - cur >= thr:
            air.append({'t': R(cur, 6), 'end': R(n['t'], 6), 'type': 'air', 'scope': 'lead'})
        cur = max(cur, n['t'] + n['dur'])
    # legato: per part, chains of notes where the next onset lands strictly before the previous release (overlap)
    leg = []
    for part in sorted({n['part'] for n in notes}):
        ns = sorted((n for n in notes if n['part'] == part), key=lambda n: n['t'])
        chain = [ns[0]]
        for n in ns[1:] + [None]:
            if n is not None and n['t'] > chain[-1]['t'] and n['t'] < max(c['t'] + c['dur'] for c in chain) - P['legato_overlap_s']:
                chain.append(n); continue
            if n is not None and n['t'] == chain[-1]['t']:
                chain.append(n); continue                                # chord tone, same onset
            end = max(c['t'] + c['dur'] for c in chain)
            if len({c['t'] for c in chain}) >= 2 and end - chain[0]['t'] >= P['legato_min_s']:
                leg.append({'t': chain[0]['t'], 'end': R(end, 6), 'type': 'legato', 'part': part,
                            'n': len(chain), 'lead': any(c['lead'] for c in chain)})
            chain = [n] if n is not None else []
    return sw, air, leg


# ------------------------------------------------------------------ main
def emit_dance_v2(score, audio_path, authored, out_path, key_pc=None):
    s = json.load(open(score)) if isinstance(score, str) else score
    A = json.load(open(authored)) if isinstance(authored, str) else authored
    assert not os.path.exists(out_path), f'refusing to overwrite {out_path} (version up)'
    dur, bpm = s['duration'], s['bpm']
    assert bpm, 'v2 needs bpm (anticipation window, harmony grid)'
    beat = 60.0 / bpm
    notes = s['notes']
    secs = s['sections']
    n_frames = int(np.floor(dur * RATE)) + 1
    tt = np.arange(n_frames) / RATE

    au = audio_channels(audio_path, n_frames)
    energy_at = lambda t: float(au['energy'][min(n_frames - 1, int(round(t * RATE)))])  # noqa: E731
    sec_of = lambda t: next((x for x in secs if x['t'] <= t < x['end']), secs[-1])  # noqa: E731

    # pitch (lead) — step channel held through rests; active flag marks a sounding lead note
    lead = sorted((n for n in notes if n['lead']), key=lambda n: n['t'])
    lo_m, hi_m = min(n['midi'] for n in lead), max(n['midi'] for n in lead)
    midi = np.full(n_frames, float(lead[0]['midi']))
    active = np.zeros(n_frames, int)
    for i, n in enumerate(lead):
        a = int(np.ceil(n['t'] * RATE - 1e-6))
        nxt = lead[i + 1]['t'] if i + 1 < len(lead) else dur + 1
        midi[a:int(np.ceil(nxt * RATE - 1e-6))] = n['midi']
        active[a:int(np.ceil((n['t'] + n['dur']) * RATE - 1e-6))] = 1
    # density — onsets/s (notes + drums) in a centred 1 s window
    on = np.sort(np.array([n['t'] for n in notes] + [t for ts in s['drums'].values() for t in ts]))
    h = P['density_win_s'] / 2
    dens = np.searchsorted(on, tt + h) - np.searchsorted(on, tt - h)
    # tension — candidate formula, 1 s hop, from the score: mean(norm density, norm lead register, norm dynamics)
    hop = P['tension_hop_s']
    nt = int(np.ceil(dur / hop))
    nd, reg, dyn = np.zeros(nt), np.zeros(nt), np.zeros(nt)
    has_lead = np.zeros(nt, bool)
    for k in range(nt):
        a, b = k * hop, (k + 1) * hop
        ons = [n for n in notes if a <= n['t'] < b]
        nd[k] = len(ons)
        dyn[k] = np.mean([n['vel'] for n in ons]) if ons else 0
        lw = [(n['midi'], min(b, n['t'] + n['dur']) - max(a, n['t'])) for n in lead if n['t'] < b and n['t'] + n['dur'] > a]
        if lw:
            has_lead[k] = True
            reg[k] = sum(m * w for m, w in lw) / sum(w for _, w in lw)
    nd_n = _norm(nd)
    dyn_n = _norm(dyn, dyn[dyn > 0].min() if (dyn > 0).any() else 0, dyn.max())
    dyn_n[dyn == 0] = 0
    reg_n = np.zeros(nt)
    reg_n[has_lead] = _norm(reg[has_lead], lo_m, hi_m)
    tension = (nd_n + reg_n + dyn_n) / 3

    # events
    ps, pinfo = pulses(notes)
    cs = cascades(notes, ps)
    member = {m: c['id'] for c in cs for m in c['members']}
    for p in ps:
        p['in_cascade'] = p['id'] in member
    sec_e = lambda t: sec_of(t)['energy']  # noqa: E731
    dr = drum_events(s, sec_e, energy_at, beat)
    mom = {m['id']: m for m in A['moments']}
    fz = [{'t': mom[f['at']]['t'], 'type': 'freeze', 'moment': f['at'], 'release_t': mom[f['release']]['t'],
           'release_cue': f['release']} for f in A['freezes']]
    events = ps + cs + dr + fz
    anticipation(events, beat)
    for e in events:
        e['t'] = R(e['t'], 6)
    events.sort(key=lambda e: (e['t'], e['type']))

    # spans
    sw, air, leg = spans_from_notes(notes, s['drums'], dur, beat)
    bl = []
    for b in A['builds']:
        bl.append({'t': mom[b['start']]['t'], 'end': mom[b['end']]['t'], 'type': 'build', 'id': b['id'],
                   'from_cue': b['start'], 'aims_at': b['release'], 'release_id': b['id'] + '_rel'})
        nxt = min([m['t'] for m in A['moments'] if m['t'] > mom[b['release']]['t']] + [dur])
        bl.append({'t': mom[b['release']]['t'], 'end': R(min(nxt, mom[b['release']]['t'] + 4 * beat), 6),
                   'type': 'release', 'id': b['id'] + '_rel', 'build_id': b['id'], 'moment': b['release'],
                   'hit_class': b['hit_class']})
    au_sec = []
    for x in secs:
        a = A['sections'][x['name']]
        au_sec.append({'t': x['t'], 'end': x['end'], 'type': 'stance', 'section': x['name'], 'stance': a['stance']})
        au_sec.append({'t': x['t'], 'end': x['end'], 'type': 'feel', 'section': x['name'], **a['feel']})
        au_sec.append({'t': x['t'], 'end': x['end'], 'type': 'formation', 'section': x['name'],
                       'formation': a['formation'], 'formation_index': FORMATIONS.index(a['formation'])})
    spans = sorted(sw + bl + air + leg + au_sec, key=lambda z: (z['t'], z['type']))

    key_pc = PC.index(A.get('key', 'Db').split()[0]) if key_pc is None else key_pc
    harm = harmony(notes, dur, beat, key_pc)

    sections = []
    for i, x in enumerate(secs):
        a = A['sections'][x['name']]
        sections.append({'n': i + 1, 'name': x['name'], 'start_s': x['t'], 'end_s': x['end'], 'energy': x['energy'],
                         'lead_parts': sorted({n['part'] for n in lead if x['t'] <= n['t'] < x['end']}),
                         'intent': a['intent'], 'action': a['action'], 'palette': a['palette'],
                         'formation': a['formation'], 'stance': a['stance'], 'feel': a['feel']['label']})

    d = {'track': s['name'], 'duration_s': dur, 'bpm': bpm, 'meter': s.get('meter'),
         'emitter': EMITTER, 'vocabulary': VOCABULARY,
         'source': {'score': s['source'], 'audio': os.path.basename(audio_path), 'audio_sha256': _sha(audio_path),
                    'audio_duration_s': R(au['audio_s'], 6),
                    'authored': A['source']},
         'note': 'Cue layer v2. Measured/derived: pulse(+strike flag), thump, drum gestures, cascade, freeze, swell, '
                 'build/release, air, legato, energy, pitch, harmony, density, shimmer, tension (candidate formula). '
                 'Authored from production data: intent/action/palette/formation/stance/feel. Times in seconds; '
                 'anticipation_s = wind-up starts at t - anticipation_s.',
         'key': A.get('key', 'Db major'),
         'gesture_map': GESTURE, 'formations': list(FORMATIONS),
         'params': dict(P, strike_vel_gate=pinfo['strike_vel_gate'], anticipation_base_s=R(min(0.24, 0.45 * beat)),
                        anticipation_weights=ANTIC, hard_attack_parts=sorted(HARD_ATTACK_PARTS)),
         'feel_settings': A['feel_settings'],
         'moments': A['moments'],
         'sections': sections, 'events': events, 'spans': spans,
         'channels': {
             'rate_hz': RATE, 'frames': n_frames,
             'energy': {'unit': '0..1 (RMS dB over 0.5 s, track p5..p99.5 of in-file frames)', 'values': [R(v) for v in au['energy']],
                        'norm': {k: v for k, v in au['norms'].items() if k.startswith('energy')}},
             'pitch': {'unit': 'MIDI (lead, held through rests)', 'midi': [int(v) for v in midi],
                       'norm': [R(v) for v in _norm(midi, lo_m, hi_m)], 'active': active.tolist(),
                       'range_midi': [lo_m, hi_m]},
             'density': {'unit': 'onsets/s (notes+drums, centred 1 s)', 'values': dens.astype(int).tolist(),
                         'norm': [R(v) for v in _norm(dens)]},
             'shimmer': {'unit': '0..1 (spectral centroid of the delivered audio, track p2..p98)',
                         'values': [R(v) for v in au['shimmer']], 'centroid_hz': [int(round(v)) for v in au['centroid_hz']],
                         'norm': {k: v for k, v in au['norms'].items() if k.startswith('centroid')}},
             'tension': {'rate_hz': 1 / hop, 'frames': nt,
                         'formula': 'CANDIDATE (not yet pinned in PIPELINE-SPEC §10): per 1 s hop [k, k+1), '
                                    'tension = (D + Rg + Dy) / 3, where D = note onsets in the hop, Rg = '
                                    'duration-weighted mean MIDI of lead notes sounding in the hop (0 if none), Dy = '
                                    'mean MIDI velocity of note onsets in the hop (0 if none); D min-max over the '
                                    "track's hops, Rg over the track's lead range, Dy over the track's non-empty hops.",
                         'values': [R(v) for v in tension],
                         'terms': {'density': [R(v) for v in nd_n], 'register': [R(v) for v in reg_n],
                                   'dynamics': [R(v) for v in dyn_n]}},
             'harmony': {'unit': 'chord change list (per-beat template match of non-lead notes)', 'changes': harm},
         }}
    validate_v2(d)
    with open(out_path, 'w') as f:
        json.dump(d, f, indent=1)
    return d


def count_nulls(o, path='', acc=None):
    acc = [] if acc is None else acc
    if o is None:
        acc.append(path)
    elif isinstance(o, dict):
        for k, v in o.items():
            count_nulls(v, f'{path}.{k}', acc)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            count_nulls(v, f'{path}[{i}]', acc)
    return acc


def validate_v2(d):
    assert d['emitter'] == EMITTER and d['vocabulary'] == VOCABULARY
    nulls = count_nulls(d)
    assert not nulls, ('nulls in v2 output', nulls[:10])
    dur = d['duration_s']
    kinds = {e['type'] for e in d['events']} | {z['type'] for z in d['spans']} | set(d['channels'])
    assert not kinds & set(EXCLUDED), ('excluded vocabulary emitted', kinds & set(EXCLUDED))
    def keys(o):
        if isinstance(o, dict):
            for k, v in o.items():
                yield k.lower()
                yield from keys(v)
        elif isinstance(o, list):
            for v in o:
                yield from keys(v)
    bad = set(keys(d)) & set(EXCLUDED)
    assert not bad, f'excluded vocabulary used as a key: {bad}'   # section names (e.g. "Tail") are values, allowed
    for e in d['events']:
        assert 0 <= e['t'] <= dur and e['anticipation_s'] > 0, e
    for z in d['spans']:
        assert 0 <= z['t'] < z['end'] <= dur + 1e-6, z
    for x in d['sections']:
        for k in ('intent', 'action', 'palette', 'formation', 'stance', 'feel'):
            assert isinstance(x[k], str) and x[k], (x['name'], k)
    ids = {z['id']: z for z in d['spans'] if z['type'] in ('build', 'release')}
    for z in ids.values():
        if z['type'] == 'build':
            r = ids[z['release_id']]
            assert abs(r['t'] - z['end']) < 1e-6, ('build must end on its release', z, r)
    mts = {m['t'] for m in d['moments']}
    for e in d['events']:
        if e['type'] == 'freeze':
            assert e['t'] in mts and e['release_t'] in mts and e['release_t'] > e['t'], e
    pid = {e['id'] for e in d['events'] if e['type'] == 'pulse'}
    for e in d['events']:
        if e['type'] == 'cascade':
            assert set(e['members']) <= pid, e['id']
    ch = d['channels']
    for k in ('energy', 'pitch', 'density', 'shimmer'):
        arr = ch[k].get('values', ch[k].get('midi'))
        assert len(arr) == ch['frames'], k
    return True
