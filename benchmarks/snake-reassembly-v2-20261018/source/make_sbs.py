"""Juxtapose REFERENCE.png with frozen-camera material captures. Not a solved camera match."""
import bpy
from pathlib import Path
root = Path(r'\\wsl.localhost\OpenClawGateway\home\openclaw\.openclaw\workspace-studio-3d\tickets\snake-reassembly-v2-20261018')
ref_path = root / 'pack/reassembly-pack-v2-20261018/REFERENCE.png'
cap = root / 'repo/benchmarks/snake-reassembly-v2-20261018/material/captures'
out = root / 'repo/benchmarks/snake-reassembly-v2-20261018/material/comparisons'
out.mkdir(exist_ok=True)
H = 720
names = ['m2-full-body.png', 'm2-head-closeup.png', 'm2-seg-detail.png', 'm2-tail-detail.png', 'm2-tail_top-detail.png']
for name in names:
    ref = bpy.data.images.load(str(ref_path))
    shot = bpy.data.images.load(str(cap / name))
    def fit(im):
        w = max(1, round(im.size[0] * H / im.size[1]))
        im.scale(w, H)
        return w
    lw, rw = fit(ref), fit(shot)
    W = lw + rw + 24
    canvas = bpy.data.images.new(name, W, H + 36, alpha=False)
    px = [0.533] * (W * (H + 36) * 4)
    def blit(im, x0, y0):
        w, h = im.size
        src = list(im.pixels)
        for y in range(h):
            row = src[y * w * 4:(y + 1) * w * 4]
            dst = ((y0 + y) * W + x0) * 4
            px[dst:dst + w * 4] = row
    blit(ref, 0, 0)
    blit(shot, lw + 24, 0)
    canvas.pixels = px
    dest = out / name.replace('.png', '-sbs.png')
    canvas.filepath_raw = str(dest)
    canvas.file_format = 'PNG'
    canvas.save()
    print('WROTE', dest, canvas.size, flush=True)
    for im in (ref, shot, canvas):
        bpy.data.images.remove(im)
print('SBS_DONE', flush=True)
