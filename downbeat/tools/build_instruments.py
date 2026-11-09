"""Generate tools/instruments.json from the sfz files themselves (rerunnable: python3 -m tools.build_instruments).

Per patch: lokey/hikey (playable regions, release triggers excluded), velocity-layer count (max distinct
lovel/hivel ranges covering any one key), round-robin count (max seq_length, else distinct lorand ranges
on one key/vel, else 1), true source library (from resolved sample paths — several "VPO"
patches are VSCO/SSO/NoBudgetOrch underneath), and a measured unity-gain reference level:
one note at REF_VEL for REF_BEATS at 120 BPM through render_part(); ref_rms_dbfs is the RMS over the
held-note window [0, 1 s], ref_peak_dbfs the peak, both at unity (stage removed).
Reference key = the playable key nearest the middle of the range that is a region's pitch_keycenter.
"""
import collections
import datetime
import json
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools import sfz  # noqa: E402
from tools.render import render_part  # noqa: E402

SF = '/home/hatch/workspace/song/soundfonts'
HERE = os.path.dirname(os.path.abspath(__file__))
REF_VEL, REF_BEATS, BPM = 100, 2, 120

# every patch referenced by recent builds, plus VSCO FHornSus (a level-match case)
PATCHES = """
VPO/Strings/1st-violin-SEC-sustain.sfz VPO/Strings/2nd-violin-SEC-sustain.sfz VPO/Strings/viola-SEC-sustain.sfz
VPO/Strings/cello-SEC-sustain.sfz VPO/Strings/bass-SEC-sustain.sfz VPO/Strings/1st-violin-SEC-staccato.sfz
VPO/Strings/2nd-violin-SEC-staccato.sfz VPO/Strings/cello-SOLO-sustain.sfz VPO/Strings/1st-violin-SOLO-sustain.sfz
VPO/Vocals/choir-MIXED-sustain.sfz VPO/Vocals/choir-MALE-sustain.sfz VPO/Percussion/timpani-hit.sfz
VPO/Percussion/timpani-roll.sfz VPO/Woodwinds/flute-SEC-sustain.sfz VPO/Woodwinds/piccolo-SOLO-sustain.sfz
VPO/Woodwinds/oboe-SEC-sustain.sfz VPO/Woodwinds/clarinet-SEC-sustain.sfz VPO/Brass/tuba-SOLO-sustain.sfz
VPO/Brass/trumpet-SEC-sustain.sfz VPO/Brass/trombone-SEC-sustain.sfz VPO/Brass/french-horn-SEC-sustain.sfz
VPO/Brass/french-horn-SOLO-sustain.sfz VPO/Brass/bass-trombone-SOLO-sustain.sfz VPO/Brass/all-brass-SEC-sustain.sfz
VPO/Brass/all-brass-SEC-accent.sfz VSCO-2-CE/ViolinEnsSpic.sfz VSCO-2-CE/CelloEnsSpic.sfz
VSCO-2-CE/GM-StylePerc.sfz VSCO-2-CE/FHornSus.sfz SalamanderGrandPianoV3/SalamanderGrandPianoV3.sfz
VSCO-2-CE/ViolinEnsPizz.sfz VSCO-2-CE/ViolaEnsPizz.sfz VSCO-2-CE/CelloEnsPizz.sfz VSCO-2-CE/ContrabassPizz.sfz
VSCO-2-CE/Marimba.sfz
""".split()


def source(sample):
    p = sample.replace('\\', '/')
    m = re.search(r'/libs/([^/]+)/', p)
    if m:
        return m.group(1)
    for tag in ('VSCO-2-CE', 'SalamanderGrandPianoV3'):
        if f'/{tag}/' in p:
            return tag
    return 'unknown'


def describe(rel, out_dir):
    path = os.path.join(SF, rel)
    regs = sfz.parse_regions(path)
    pl = sfz.playable(regs)
    lo, hi = min(r['lokey'] for r in pl), max(r['hikey'] for r in pl)
    keys = sorted({k for r in pl for k in range(r['lokey'], r['hikey'] + 1)})
    gaps = [k for k in range(lo, hi + 1) if k not in keys]
    layers = max(len({(r['lovel'], r['hivel']) for r in pl if r['lokey'] <= k <= r['hikey']}) for k in keys)
    seq = max([int(r.get('seq_length', 1)) for r in pl] + [1])
    rand = max(len({(r.get('lorand'), r.get('hirand')) for r in pl
                    if r['lokey'] <= k <= r['hikey'] and r['lovel'] <= REF_VEL <= r['hivel'] and 'lorand' in r})
               for k in keys)
    rr = max(seq, rand, 1)
    srcs = collections.Counter(source(r['sample']) for r in regs)
    centers = sorted({r['pitch_keycenter'] for r in pl if isinstance(r.get('pitch_keycenter'), int)} or set(keys))
    mid = (lo + hi) / 2
    ref = min((k for k in centers if sfz.covers(regs, k, REF_VEL)), key=lambda k: (abs(k - mid), k))
    name = re.sub(r'\W+', '_', rel[:-4])
    r = render_part(name, path, [(0, REF_BEATS, ref, REF_VEL)], out_dir, bpm=BPM, ring_s=2.0)
    a = r['audio'][: int(REF_BEATS * 60 / BPM * r['sr'])]
    rms = 20 * np.log10(np.sqrt(np.mean(a.astype(np.float64) ** 2)) + 1e-12)
    pk = 20 * np.log10(np.abs(r['audio']).max() + 1e-12)
    return dict(path=path, lokey=lo, hikey=hi, key_gaps=gaps, velocity_layers=layers, round_robin=rr,
                source_library=dict(srcs), source_primary=srcs.most_common(1)[0][0],
                regions=len(pl), ref_key=ref, ref_vel=REF_VEL, ref_rms_dbfs=round(float(rms), 2),
                ref_peak_dbfs=round(float(pk), 2), render_stage_db=r['stage_db'])


def main():
    out_dir = os.path.join(HERE, '.instrument_renders')
    cat = dict(generated=datetime.datetime.now().isoformat(timespec='seconds'),
               generator='tools/build_instruments.py', soundfonts=SF,
               reference=f'one note, vel {REF_VEL}, {REF_BEATS} beats @ {BPM} BPM via render_part; RMS over [0,1 s] at unity',
               patches={})
    for rel in PATCHES:
        d = describe(rel, out_dir)
        cat['patches'][rel] = d
        print(f"{rel:52s} {d['lokey']:3d}-{d['hikey']:3d} vel{d['velocity_layers']} rr{d['round_robin']} "
              f"{d['source_primary']:16s} ref {d['ref_key']} {d['ref_rms_dbfs']:6.1f} dBFS", flush=True)
    json.dump(cat, open(os.path.join(HERE, 'instruments.json'), 'w'), indent=1)


def add(rels):
    """Incremental: describe only `rels` and merge them into the existing instruments.json (no full re-render).
    Added 2026-10-22: VSCO pizzicato family + marimba."""
    p = os.path.join(HERE, 'instruments.json')
    cat = json.load(open(p))
    for rel in rels:
        d = describe(rel, os.path.join(HERE, '.instrument_renders'))
        cat['patches'][rel] = d
        print(f"{rel:52s} {d['lokey']:3d}-{d['hikey']:3d} vel{d['velocity_layers']} rr{d['round_robin']} "
              f"{d['source_primary']:16s} ref {d['ref_key']} {d['ref_rms_dbfs']:6.1f} dBFS", flush=True)
    cat['updated'] = datetime.datetime.now().isoformat(timespec='seconds')
    json.dump(cat, open(p, 'w'), indent=1)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        add(sys.argv[1:])
    else:
        main()
