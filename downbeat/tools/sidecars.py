"""Canonical score export + portfolio sidecar emitter (sidecar-emitter-v1, 2026-10-22).

score.json — the one intermediate every build emits into its ticket folder
--------------------------------------------------------------------------
{
  "format": "downbeat-score", "version": 1,
  "name": "song-of-storms-v1",          # stem for <name>.viz.json / <name>.dance.json
  "source": "free text: where the data came from",
  "duration": 170.55,                   # seconds, the delivered file's length
  "bpm": 180, "meter": "3/4",           # optional, carried into dance.json
  "notes": [{"t": s, "midi": int, "dur": s, "part": str, "vel": int, "lead": bool}, ...],
  "drums": {"kick": [s, ...], "snare": [s, ...], "<other role>": [...]},
  "sections": [{"t": s, "end": s, "name": str, "energy": 0..1}, ...]
}
All times in seconds from file start (rounded to 6 dp). `lead: true` marks the designated melody
note-by-note (handoffs between parts are allowed; the lead may change part per section). `energy` is the
section's 0..1 visual intensity. Drum roles kick/snare feed the viz; other roles are carried for later use.

Build tickets: call `write_score(path, ...)` (or build the dict and `json.dump`) at the composed stage, then
`emit_sidecars(score_path, out_dir)`.

Adapters for already-delivered tracks (no rebuild): `from_storms_notes`, `from_performance_notes`,
`from_midi_dir`. `energy_from_db` is the documented default when a build has no hand-set energy.
"""
import glob
import json
import os
import struct

R6 = lambda x: round(float(x), 6)  # noqa: E731


def energy_from_db(db_list, lo=0.15, hi=0.95):
    """Min-max map of per-section RMS dB to [lo, hi] (default heuristic; hand-set energy wins)."""
    a, b = min(db_list), max(db_list)
    return [round(lo + (hi - lo) * (d - a) / (b - a), 2) if b > a else hi for d in db_list]


def make_score(name, source, duration, notes, drums, sections, bpm=None, meter=None):
    notes = sorted(({'t': R6(n['t']), 'midi': int(n['midi']), 'dur': R6(n['dur']), 'part': n['part'],
                     'vel': int(n.get('vel', 100)), 'lead': bool(n.get('lead', False))} for n in notes),
                   key=lambda n: (n['t'], n['part'], n['midi']))
    s = {'format': 'downbeat-score', 'version': 1, 'name': name, 'source': source, 'duration': R6(duration),
         'bpm': bpm, 'meter': meter, 'notes': notes,
         'drums': {k: sorted(R6(t) for t in v) for k, v in drums.items()},
         'sections': [{'t': R6(x['t']), 'end': R6(x['end']), 'name': x['name'], 'energy': float(x['energy'])}
                      for x in sections]}
    validate(s)
    return s


def validate(s):
    assert s.get('format') == 'downbeat-score' and s.get('version') == 1, 'not a downbeat score'
    d = s['duration']
    assert all(0 <= n['t'] <= d and n['dur'] > 0 for n in s['notes']), 'note outside file'
    assert any(n['lead'] for n in s['notes']), 'no lead notes designated'
    sec = s['sections']
    assert sec and sec[0]['t'] == 0, 'sections must start at 0'
    for a, b in zip(sec, sec[1:]):
        assert a['end'] == b['t'] and a['t'] < b['t'], ('sections not contiguous', a, b)
    assert abs(sec[-1]['end'] - d) < 1.0, ('last section end vs duration', sec[-1]['end'], d)
    assert all(0 <= x['energy'] <= 1 for x in sec), 'energy outside 0..1'
    for role, ts in s['drums'].items():
        assert all(0 <= t <= d for t in ts), f'{role} onset outside file'


def write_score(path, *args, **kw):
    s = make_score(*args, **kw)
    json.dump(s, open(path, 'w'), indent=1)
    return s


def emit_sidecars(score_json, out_dir, name=None, version=1, emitter='v1', audio=None, authored=None):
    """score.json (path or dict) -> <name>.viz.json + <name>.dance.json. Never overwrites.

    emitter='v1' (default, unchanged): starter-scaffold dance.json (intent/action/palette null, events []).
    emitter='v2' (sidecar-vocab-v2): ruled cue vocabulary via tools.dance_v2 — needs audio (delivered file, for
    shimmer/energy) and authored (per-track production values: section intent/stance/feel, moments, builds).
    v2 writes <name>.dance.v2.json and no viz (viz.json is unchanged between emitters)."""
    s = json.load(open(score_json)) if isinstance(score_json, str) else score_json
    validate(s)
    name = name or s['name']
    if emitter == 'v2':
        from .dance_v2 import emit_dance_v2
        assert audio and authored, 'emitter v2 needs audio= and authored='
        os.makedirs(out_dir, exist_ok=True)
        p = os.path.join(out_dir, f'{name}.dance.v2.json')
        emit_dance_v2(s, audio, authored, p)
        return {'dance': p}
    assert emitter == 'v1', emitter
    viz = {'version': version, 'source': s['source'], 'duration': s['duration'],
           'kick': s['drums'].get('kick', []), 'snare': s['drums'].get('snare', []),
           'melody': [{'t': n['t'], 'midi': n['midi'], 'dur': n['dur']} for n in s['notes'] if n['lead']],
           'sections': [{'t': x['t'], 'name': x['name'], 'energy': x['energy']} for x in s['sections']]}
    lead_part = lambda a, b: sorted({n['part'] for n in s['notes'] if n['lead'] and a <= n['t'] < b})  # noqa
    dance = {'track': name, 'duration_s': s['duration'], 'bpm': s.get('bpm'), 'meter': s.get('meter'),
             'note': 'Starter scaffold from score.json: timings are real; intent/action/palette are a '
                     'build-time creative act — fill them in, the emitter does not invent choreography.',
             'sections': [{'n': i + 1, 'name': x['name'], 'start_s': x['t'], 'end_s': x['end'],
                           'energy': x['energy'], 'lead_parts': lead_part(x['t'], x['end']),
                           'intent': None, 'action': None, 'palette': None}
                          for i, x in enumerate(s['sections'])],
             'events': []}
    os.makedirs(out_dir, exist_ok=True)
    out = {}
    for kind, obj in (('viz', viz), ('dance', dance)):
        p = os.path.join(out_dir, f'{name}.{kind}.json')
        assert not os.path.exists(p), f'refusing to overwrite {p} (version up)'
        json.dump(obj, open(p, 'w'), indent=1)
        out[kind] = p
    return out


# ------------------------------------------------------------------ adapters
def from_storms_notes(notes_json, name, duration, section_names, energies, source, drum_roles=('kick', 'snare'),
                      bpm=None, meter=None):
    """storms-style notes.json: {notes:[{part,t,d,p,v,mel}], SEC:{n:[t0,t1]}}. Drum parts named by role."""
    j = json.load(open(notes_json))
    notes, drums = [], {r: [] for r in drum_roles}
    for n in j['notes']:
        if n['part'] in drums:
            drums[n['part']].append(n['t'])
        else:
            notes.append({'t': n['t'], 'midi': n['p'], 'dur': n['d'], 'part': n['part'], 'vel': n['v'],
                          'lead': n.get('mel', False)})
    keys = sorted(j['SEC'], key=int)
    secs = [{'t': j['SEC'][k][0], 'end': j['SEC'][k][1], 'name': nm, 'energy': e}
            for k, nm, e in zip(keys, section_names, energies)]
    secs[-1]['end'] = duration  # SEC rounds the last bar up past the file end
    return make_score(name, source, duration, notes, drums, secs, bpm, meter)


def from_performance_notes(perf_json, name, duration, bpm, beats_per_bar, sections, lead, drum_roles, source,
                           meter=None):
    """anthem-style performance_notes.json: {part: [[bar0, beat, dur_beats, midi, vel], ...]}.
    lead: list of (part, bar_from, bar_to, min_midi) — the designated melody per span.
    drum_roles: {part: role}, e.g. {'drum_low': 'kick', 'drum_mid': 'snare'}."""
    j = json.load(open(perf_json))
    beat = 60.0 / bpm
    notes, drums = [], {}
    for part, ns in j.items():
        for bar, bt, d, m, v in ns:
            t = (bar * beats_per_bar + bt) * beat
            if part in drum_roles:
                drums.setdefault(drum_roles[part], []).append(t)
                continue
            is_lead = any(p == part and b0 <= bar <= b1 and m >= mn for p, b0, b1, mn in lead)
            notes.append({'t': t, 'midi': m, 'dur': d * beat, 'part': part, 'vel': v, 'lead': is_lead})
    return make_score(name, source, duration, notes, drums, sections, bpm, meter)


def _vlq(b, i):
    v = 0
    while True:
        c = b[i]; i += 1
        v = (v << 7) | (c & 0x7F)
        if not c & 0x80:
            return v, i


def read_midi(path):
    """Minimal SMF reader -> [(t_s, midi, dur_s, vel)]. Honours tempo meta events (single tempo map)."""
    b = open(path, 'rb').read()
    assert b[:4] == b'MThd'
    _, ntrk, tpq = struct.unpack('>HHH', b[8:14])
    i, events = 14, []
    for _ in range(ntrk):
        assert b[i:i + 4] == b'MTrk'
        ln = struct.unpack('>I', b[i + 4:i + 8])[0]
        j, end, tick, run = i + 8, i + 8 + ln, 0, 0
        while j < end:
            dt, j = _vlq(b, j); tick += dt
            st = b[j]
            if st == 0xFF:
                typ = b[j + 1]; ml, j = _vlq(b, j + 2)
                if typ == 0x51:
                    events.append((tick, 'tempo', int.from_bytes(b[j:j + 3], 'big'), 0))
                j += ml; continue
            if st in (0xF0, 0xF7):
                ml, j = _vlq(b, j + 1); j += ml; continue
            if st & 0x80:
                run = st; j += 1
            hi = run & 0xF0
            if hi in (0xC0, 0xD0):
                d = b[j:j + 1]; j += 1
            else:
                d = b[j:j + 2]; j += 2
            if hi == 0x90 and d[1] > 0:
                events.append((tick, 'on', d[0], d[1]))
            elif hi == 0x80 or (hi == 0x90 and d[1] == 0):
                events.append((tick, 'off', d[0], 0))
        i = end
    events.sort(key=lambda e: (e[0], e[1] != 'tempo', e[1] == 'on'))
    sec, last_tick, us = 0.0, 0, 500000
    out, open_ = [], {}
    for tick, kind, a, v in events:
        sec += (tick - last_tick) * us / 1e6 / tpq; last_tick = tick
        if kind == 'tempo':
            us = a
        elif kind == 'on':
            open_.setdefault(a, []).append((sec, v))
        elif open_.get(a):
            t0, v0 = open_[a].pop(0)
            out.append((t0, a, sec - t0, v0))
    return sorted(out)


def from_midi_dir(midi_dir, name, duration, sections, lead_parts, drum_roles, source, bpm=None, meter=None):
    """One .mid per part (filename = part). lead_parts: [(part, t_from, t_to, min_midi)]; drum_roles: {part: role}."""
    notes, drums = [], {}
    for p in sorted(glob.glob(os.path.join(midi_dir, '*.mid'))):
        part = os.path.splitext(os.path.basename(p))[0]
        for t, m, d, v in read_midi(p):
            if part in drum_roles:
                drums.setdefault(drum_roles[part], []).append(t)
                continue
            notes.append({'t': t, 'midi': m, 'dur': d, 'part': part, 'vel': v,
                          'lead': any(p == part and t0 <= t < t1 and m >= mn for p, t0, t1, mn in lead_parts)})
    return make_score(name, source, duration, notes, drums, sections, bpm, meter)
