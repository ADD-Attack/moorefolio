"""deliver(): scratch encode -> decoded-file QA -> no-clobber copy to the final deliverable names.

Order (lessons 12/25 — the flow whose absence shipped dubstep_tutorial_a_v2_r2.mp3):
  0. Refuse up front (FileExistsError) if ANY target already exists — nothing is encoded or touched.
  1. Encode the master WAV to scratch names in `scratch_dir` (MP3 320k CBR via libmp3lame, FLAC).
  2. qa() each DECODED scratch file; gate: decoded peak <= peak_max (0.90) on the MP3 and the FLAC,
     plus any extra gates passed in (`max_jump_positions`, `max_trailing_s`).
  3. Copy scratch -> target with open(target, 'xb') (atomic no-clobber; never overwrites).
dry_run=True does 0-2 and reports what it would copy, writing nothing to the targets.
"""
import os
import shutil
import subprocess

from .qa import qa


def deliver(master_wav, targets, scratch_dir, peak_max=0.90, max_jump_positions=None, max_trailing_s=None,
            sections=None, dry_run=False, metadata=None):
    """targets: {'mp3': '/.../name.mp3', 'flac': '/.../name.flac'}. metadata: {'title': ...} tags. Returns dict of QA results."""
    exists = [t for t in targets.values() if os.path.exists(t)]
    if exists:
        raise FileExistsError(f'deliver refused: target(s) already exist, version up instead: {exists}')
    os.makedirs(scratch_dir, exist_ok=True)
    enc = {'mp3': ['-c:a', 'libmp3lame', '-b:a', '320k'], 'flac': ['-c:a', 'flac']}
    tags = [a for k, v in (metadata or {}).items() for a in ('-metadata', f'{k}={v}')]
    out = {}
    for fmt, tgt in targets.items():
        scratch = os.path.join(scratch_dir, 'scratch_' + os.path.basename(tgt))
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', master_wav, *enc[fmt], *tags, scratch], check=True)
        r = qa(scratch, sections=sections, quiet=True)
        fails = []
        if r['peak'] > peak_max:
            fails.append(f"decoded peak {r['peak']} > {peak_max}")
        if max_jump_positions is not None and r['jump_positions'] > max_jump_positions:
            fails.append(f"jump positions {r['jump_positions']} > {max_jump_positions}")
        if max_trailing_s is not None and r['trailing_silence_s'] > max_trailing_s:
            fails.append(f"trailing silence {r['trailing_silence_s']} > {max_trailing_s}")
        print(f"[deliver] {fmt}: decoded peak {r['peak']} | {r['integrated_lufs']} LUFS | "
              f"jumps {r['jump_positions']}/{r['jump_channel_events']} | {'FAIL ' + '; '.join(fails) if fails else 'OK'}")
        if fails:
            raise RuntimeError(f'deliver gate failed on decoded {fmt}: {fails}')
        out[fmt] = dict(scratch=scratch, target=tgt, qa=r)
    for fmt, o in out.items():
        if dry_run:
            print(f"[deliver] dry run: would copy {o['scratch']} -> {o['target']}")
            continue
        with open(o['scratch'], 'rb') as src, open(o['target'], 'xb') as dst:
            shutil.copyfileobj(src, dst)
        print(f"[deliver] wrote {o['target']}")
    return out
