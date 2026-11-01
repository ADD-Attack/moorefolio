"""Scripted legato for a monophonic sustain line (legato-prototype-v1, 2026-10-22). Reached via
render_part(..., legato=True, legato_opts={...}); with the flag off render_part is unchanged.

No free library here has true legato transitions, so this fakes the connection in the render path:
  1. Connections. Note i -> i+1 is "connected" when the gap between i's composed note-off and i+1's onset
     is <= gap_max beats. Rests longer than that are left alone (natural release, plain re-attack).
  2. Two alternating voices. Notes of each connected chain alternate between voice 0 and voice 1, which
     render as separate render_part calls (separate MIDI channels' worth of pitch bend; no shared release).
  3. Overlap. Connected note i is held past i+1's onset by ovl = min(xfade_s, ovl_frac * dur(i+1)) s.
  4. Crossfade + attack softening. Over [onset(i+1), onset(i+1)+ovl] the outgoing voice fades out
     (equal-power) and the incoming voice fades in from attack_gain (default 0.35 = -9.1 dB), so the
     re-bow transient is masked by the sustained outgoing note. The outgoing voice is then gated to 0 until
     its next note, which also removes the sample's 0.8 s release tail under a connected line.
  5. Glide. On stepwise moves (|interval| <= glide_max st, inside sfizz's default +-200 cent bend range),
     the outgoing note bends toward the next pitch across the first glide_s of the crossfade window (default:
     the whole window), i.e. only after the next
     note's onset — every composed pitch is held at pitch for its whole composed duration. Bend is reset
     to centre after the outgoing voice is gated silent.
Patch matching: VSCO ensemble sustains bow in slowly (ViolinEnsSusVib HF peak ~340 ms after an isolated
onset), so the outgoing note must be held through the incoming swell — xfade_s ~0.25, ovl_frac ~0.9 —
or the line dips at every connection (legato-prototype-v1 measured the short 90 ms default as -1.5 dB
deeper median dip than plain). Pitches, onsets and velocities are as composed (MIDI note numbers/ticks/velocities untouched; only
note-offs are extended and bend events added).

  6. Glide strength (legato-prototype-v2, 2026-10-22). glide_strength in [0, 1] scales BOTH the glide target
     (100 * interval cents) and the glide duration; 1.0 = v1 behaviour exactly (the owner's "trippy glitch-pop"
     colour), 0 = no bend at all. Overlap, crossfade, attack softening and gating (the dip fill) are untouched
     by the dial. v2's toned setting is in the v2 ticket report.
Limits / fallbacks:
  - Chords: any two notes sharing an onset or overlapping as composed -> the part is NOT monophonic; the
    function logs it and falls back to the plain render_part (current behaviour) for the whole part.
  - Gaps > gap_max: no connection (plain re-attack, natural release).
  - Leaps > glide_max: crossfade + attack softening only, no glide.
Returns render_part's dict shape (audio at unity level, plus `table`: per-connection measurements, and
`voices`: the two voice render dicts). The mixed legato audio is also written to <out_dir>/<name>.f32.npy.
"""
import json
import os

import numpy as np

from . import render as R

TPQ = 480


def _vlq(data, i):
    n = 0
    while True:
        b = data[i]; i += 1
        n = (n << 7) | (b & 0x7F)
        if not b & 0x80:
            return n, i


def _parse(path):
    raw = open(path, 'rb').read()
    hdr, trk = raw[:14], raw[22:]
    evts, i, t = [], 0, 0
    while i < len(trk):
        d, i = _vlq(trk, i); t += d
        s = trk[i]
        if s == 0xFF:
            ln = trk[i + 2]; ev = trk[i:i + 3 + ln]
        elif s & 0xF0 == 0xC0:
            ev = trk[i:i + 2]
        else:
            ev = trk[i:i + 3]
        i += len(ev)
        evts.append((t, ev))
    return hdr, evts


def _write(path, hdr, evts):
    data, last = b'', 0
    for t, ev in evts:
        data += R._var(t - last) + ev; last = t
    open(path, 'wb').write(hdr + b'MTrk' + len(data).to_bytes(4, 'big') + data)


def _bend_bytes(cents):
    v = int(round(8192 + cents / 200.0 * 8191))
    v = max(0, min(16383, v))
    return bytes([0xE0, v & 0x7F, v >> 7])


def render_legato(name, sfz_path, notes, out_dir, bpm=R.midutil.BPM, ring_s=4.0, program=0, sr=R.SR,
                  stage_db=0.0, gap_max=0.25, xfade_s=0.09, ovl_frac=0.45, attack_gain=0.35, glide_max=2,
                  glide_step_s=0.005, glide_s=None, glide_strength=1.0):
    notes = sorted(tuple(n) for n in notes)
    spb = 60.0 / bpm
    os.makedirs(out_dir, exist_ok=True)
    logf = os.path.join(out_dir, f'{name}.legato.log')
    open(logf, 'w').close()
    log = lambda m: R._log(logf, f'{name} [legato] {m}')
    mono = all(b[0] >= a[0] + a[1] - 1e-3 for a, b in zip(notes, notes[1:]))
    if not mono:
        log('FALLBACK: line is not monophonic (shared/overlapping onsets) — plain render_part, no legato')
        r = R.render_part(name, sfz_path, notes, out_dir, bpm=bpm, ring_s=ring_s, program=program, sr=sr,
                          stage_db=stage_db)
        r['table'], r['fallback'] = [], True
        return r
    n = len(notes)
    conn = [notes[i + 1][0] - (notes[i][0] + notes[i][1]) <= gap_max + 1e-9 for i in range(n - 1)] + [False]
    # voice assignment: alternate inside chains, restart at voice 0 after a break
    voice, v = [], 0
    for i in range(n):
        voice.append(v)
        v = 1 - v if conn[i] else 0
    table, ext = [], [list(x) for x in notes]
    for i in range(n - 1):
        if not conn[i]:
            continue
        on_next = notes[i + 1][0] * spb
        ovl = min(xfade_s, ovl_frac * notes[i + 1][1] * spb)
        ext[i][1] = (on_next + ovl) / spb - notes[i][0]
        iv = notes[i + 1][2] - notes[i][2]
        glide = abs(iv) <= glide_max and iv != 0 and glide_strength > 0
        table.append(dict(i=i, from_midi=notes[i][2], to_midi=notes[i + 1][2], interval=iv, onset_s=round(on_next, 4),
                          gap_beats=round(notes[i + 1][0] - notes[i][0] - notes[i][1], 4),
                          overlap_ms=round(ovl * 1e3, 1), xfade_ms=round(ovl * 1e3, 1),
                          glide_ms=round(glide_strength * min(ovl, glide_s or ovl) * 1e3, 1) if glide else 0.0,
                          glide_cents=glide_strength * 100 * iv if glide else 0, glide_strength=glide_strength,
                          attack_gain=attack_gain, attack_db=round(20 * np.log10(attack_gain), 1),
                          voices=f'{voice[i]}->{voice[i + 1]}'))
    log(f'{n} notes, {sum(conn)} connections, {sum(1 for t in table if t["glide_ms"])} glides; '
        f'gap_max {gap_max} beat, xfade {xfade_s * 1e3:.0f} ms, attack_gain {attack_gain}, glide_strength {glide_strength}')

    voices = []
    for vv in (0, 1):
        idx = [i for i in range(n) if voice[i] == vv]
        if not idx:
            voices.append(None); continue
        vnotes = [tuple(ext[i]) for i in idx]
        bends = []   # (tick, cents)
        for t in table:
            if voice[t['i']] != vv or not t['glide_ms']:
                continue
            t0, g = t['onset_s'], t['glide_ms'] / 1e3
            k = max(2, int(g / glide_step_s))
            for j in range(1, k + 1):
                x = j / k
                c = t['glide_cents'] * (0.5 - 0.5 * np.cos(np.pi * x))
                bends.append((round((t0 + x * g) / spb * TPQ), c))
            bends.append((round((t0 + g + 0.010) / spb * TPQ), 0.0))

        def hook(mid, bends=bends):
            if not bends:
                return
            hdr, evts = _parse(mid)
            body, tail = evts[:-2], evts[-2:]          # tail = ring CC + EOT, stays last
            assert all(b[0] <= tail[0][0] for b in bends)
            body += [(tk, _bend_bytes(c)) for tk, c in bends]
            body.sort(key=lambda e: (e[0], 0 if e[1][0] & 0xF0 == 0x80 else 1))
            _write(mid, hdr, body + tail)

        r = R.render_part(f'{name}_v{vv}', sfz_path, vnotes, out_dir, bpm=bpm, ring_s=ring_s, program=program,
                          sr=sr, stage_db=stage_db, _midi_hook=hook)
        voices.append(r)

    L = max(r['audio'].shape[0] for r in voices if r)
    out = np.zeros((L, 2), np.float64)
    for vv, r in enumerate(voices):
        if not r:
            continue
        a = np.zeros((L, 2)); a[:len(r['audio'])] = r['audio']
        g = np.ones(L)
        for t in table:
            s0 = int(round(t['onset_s'] * sr)); m = max(1, int(round(t['xfade_ms'] / 1e3 * sr)))
            x = np.arange(m) / m
            if voice[t['i']] == vv:        # outgoing: equal-power fade out, then gate to the voice's next onset
                g[s0:s0 + m] *= np.cos(x * np.pi / 2)
                nxt = [notes[i][0] * spb for i in range(t['i'] + 1, n) if voice[i] == vv]
                e = int(round(nxt[0] * sr)) if nxt else L
                g[s0 + m:e] = 0.0
            else:                          # incoming: fade in from attack_gain (equal-power shape)
                g[s0:s0 + m] *= attack_gain + (1 - attack_gain) * np.sin(x * np.pi / 2)
        out += a * g[:, None]
    out = out.astype(np.float32)
    np.save(os.path.join(out_dir, f'{name}.f32.npy'), out)
    json.dump(table, open(os.path.join(out_dir, f'{name}.legato.json'), 'w'), indent=1)
    log(f'mixed {L / sr:.3f} s, peak {20 * np.log10(np.abs(out).max() + 1e-12):.1f} dBFS (unity level)')
    return dict(audio=out, table=table, voices=voices, fallback=False, seconds=L / sr, sr=sr,
                peak_dbfs=float(20 * np.log10(np.abs(out).max() + 1e-12)))
