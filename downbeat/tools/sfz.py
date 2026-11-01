"""SFZ parsing + RAM-flattening shared by render.py and build_instruments.py.

parse_regions(path) -> list of effective regions (control/global/master/group/region opcodes merged,
#define substituted, #include followed, key names -> ints, sample paths absolute).
flatten(path, out_path, keys=None, volume_db=0.0) writes a RAM-loaded copy (hint_ram_based=1,
absolute sample paths) optionally keeping only regions whose key range touches `keys`.
"""
import os
import re

NOTE = {'c': 0, 'd': 2, 'e': 4, 'f': 5, 'g': 7, 'a': 9, 'b': 11}
_TOK = re.compile(r'<(\w+)>|([\w$]+)=([^\n]*?)(?=\s+[\w$]+=|\s*<|\s*\n|\s*$)')


def key(v):
    v = str(v).strip().lower()
    if re.fullmatch(r'-?\d+', v):
        return int(v)
    m = re.fullmatch(r'([a-g])(#|b)?(-?\d)', v)
    if not m:
        raise ValueError(f'bad sfz key {v!r}')
    return 12 * (int(m.group(3)) + 1) + NOTE[m.group(1)] + {'#': 1, 'b': -1, None: 0}[m.group(2)]


def _text(path, defines):
    txt = open(path, encoding='latin-1').read()
    txt = re.sub(r'/\*.*?\*/', '', txt, flags=re.S)
    txt = re.sub(r'//[^\n]*', '', txt)
    out = []
    for line in txt.split('\n'):
        m = re.match(r'\s*#define\s+(\$\w+)\s+(.*\S)', line)
        if m:
            defines[m.group(1)] = m.group(2)
            continue
        m = re.match(r'\s*#include\s+"([^"]+)"', line)
        if m:
            inc = os.path.join(os.path.dirname(path), m.group(1).replace('\\', '/'))
            out.append(_text(inc, defines))
            continue
        for k in sorted(defines, key=len, reverse=True):
            line = line.replace(k, defines[k])
        out.append(line)
    return '\n'.join(out)


def parse_regions(path):
    path = os.path.abspath(path)
    root = os.path.dirname(path)
    txt = _text(path, {})
    ctl, glob, master, group, cur = {}, {}, {}, {}, None
    regions, skipped_headers = [], set()
    for tok in _TOK.finditer(txt):
        if tok.group(1):
            h = tok.group(1)
            if h == 'control':
                cur = ctl
            elif h == 'global':
                glob, master, group = {}, {}, {}
                cur = glob
            elif h == 'master':
                master, group = {}, {}
                cur = master
            elif h == 'group':
                group = {}
                cur = group
            elif h == 'region':
                cur = {'__g': glob, '__m': master, '__grp': group}
                regions.append(cur)
            else:
                skipped_headers.add(h)
                cur = {}
        elif cur is not None:
            cur[tok.group(2)] = tok.group(3).strip()
    dp = ctl.get('default_path', '').replace('\\', '/')
    out = []
    for r in regions:
        eff = {**r.pop('__g'), **r.pop('__m'), **r.pop('__grp'), **r}
        if 'sample' not in eff:
            continue
        if 'key' in eff:
            eff['lokey'] = eff['hikey'] = eff['pitch_keycenter'] = eff.pop('key')
        eff['lokey'], eff['hikey'] = key(eff.get('lokey', 0)), key(eff.get('hikey', 127))
        if 'pitch_keycenter' in eff and eff['pitch_keycenter'] != 'sample':
            eff['pitch_keycenter'] = key(eff['pitch_keycenter'])
        eff['lovel'], eff['hivel'] = int(eff.get('lovel', 1)), int(eff.get('hivel', 127))
        s = eff['sample'].replace('\\', '/')
        if not s.startswith('*'):
            s = os.path.normpath(os.path.join(root, dp, s))
        eff['sample'] = s
        out.append(eff)
    parse_regions.skipped_headers = skipped_headers
    return out


def playable(regions):
    """Regions that sound on note-on (not release triggers, not unmapped)."""
    return [r for r in regions if r.get('trigger', 'attack') in ('attack', 'first', 'legato')
            and r['hikey'] >= 0 and r['lokey'] <= r['hikey']]


def covers(regions, m, v):
    return any(r['lokey'] <= m <= r['hikey'] and r['lovel'] <= v <= r['hivel'] for r in playable(regions))


def rr_to_seq(regions):
    """Deterministic round robins: lorand/hirand groups -> seq_length/seq_position.
    Measured 2026-10-22: sfizz_render's lorand draw is repeatable (two renders of the same MIDI: max diff 0.0),
    so this is NOT needed for determinism. What it buys is a controlled pattern: strict alternation that
    restarts at position 1 on every render (= an explicit RR reset at the loop start), never a random repeat."""
    rng = sorted({(float(r['lorand']), float(r.get('hirand', 1))) for r in regions if 'lorand' in r})
    if not rng:
        return regions
    out = []
    for r in regions:
        r = dict(r)
        if 'lorand' in r:
            pos = rng.index((float(r.pop('lorand')), float(r.pop('hirand', 1)))) + 1
            r['seq_length'], r['seq_position'] = len(rng), pos
        out.append(r)
    return out


def flatten(src, out_path, keys=None, volume_db=0.0, rr_seq=False, overrides=None):
    """rr_seq=True: lorand RR -> seq RR (deterministic). overrides: {opcode: value} set on every region
    (e.g. {'ampeg_release': 0.25}); a value of None removes the opcode (e.g. pitch_random)."""
    regions = parse_regions(src)
    if rr_seq:
        regions = rr_to_seq(regions)
    lines = ['<control>', 'hint_ram_based=1', '<global>']
    n = 0
    for r in regions:
        if keys is not None and not any(r['lokey'] <= k <= r['hikey'] for k in keys):
            continue
        r = dict(r)
        for k, v in (overrides or {}).items():
            if v is None:
                r.pop(k, None)
            else:
                r[k] = v
        r['volume'] = round(float(r.get('volume', 0)) + volume_db, 3)
        smp = r.pop('sample')
        r.pop('default_path', None)
        ops = ' '.join(f'{k}={v}' for k, v in r.items())
        lines.append(f'<region> {ops} sample={smp}')
        n += 1
    with open(out_path, 'w') as f:
        f.write('\n'.join(lines) + '\n')
    return n
