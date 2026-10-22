# NOTE — EDEN-3D-01 aliens_b — QA Clay assembled gate delivery (Forge, 2026-10-22)

**Stop point reached: QA Clay assembled. No materials were started. Standing by for the blind panel.**

## Deliverables
- `aliens_b_clay.glb` — 38,854 tris (budget ≤45k), +Y up, modifiers applied, tangents ON (provisional Smart-UV), Draco OFF, one Principled clay material.
- `aliens_b_clay.blend` — same scene.
- `captures/clay-full.png` (1840×1168) and `captures/clay-mouth.png` (1400×1400) — judged Cycles captures.
- `captures/compare-full-vs-reference.png` — frozen-camera side-by-side with aliens-b-3d-reference.png (the left half is the reference, in colour; the right half is the clay).
- `element-log.md`, `FEATURES.md` (frozen at checkpoint 1), `scripts/`, `crops/`, `previews/`.

## Node tree (animatable)
```
aliens_b_body (17,973)
├─ leg_FL / leg_FR / leg_BL / leg_BR (~1,495 each; pivot at hip cut, z=-0.34)
├─ mouth (11,984; own node, modeled interior cavity; pivot at the collar cut x=0.40 → open/close + spit origin)
└─ tail_01 (1,196) → tail_02 (996) → tail_03 (722)   (rigid chain, pivots at segment roots)
```

## Build method (Decision 35 — from the formed mesh)
1. Source: Hunyuan3D v2.1 fp16, ComfyUI 0.41.0, prompt **92f9ec6c-0412-45da-bcdb-4c83f78fef9d**, seed 42, 30 steps, cfg 5, octree 256, surface net 0.6. Input: crop **c1** = (0,20,1420,1168) of aliens-b-3d-reference.png, padded square on the sampled bg (228,228,228) → 1024². No 2D art was fed (Decision 44).
2. `scripts/build.py`: weld → strip the baked ground slab (z < -0.505) → keep the main island → fill small loops ≤120 edges → bisect at planes x=-0.56/-0.625/-0.675 (tail segments), x=0.40 (mouth), z=-0.34 (legs) → split by region → cap only the cut loops → per-node quadric decimate to budget → weld 1 mm + fill ≤40-edge loops → pivots + hierarchy → export.
3. No primitives anywhere; every node is the c1 formed surface.
4. Element loop: 6 Hunyuan calls, 1 approved and 5 declined (see element-log.md). The separate mouth/tail elements were declined because their cut-edge crops melted. c1's own mouth carries the lip ring and cavity.

## Staging (captures/render-settings.json)
- Cycles, 256 spp, adaptive 0.01, denoise ON, Standard view transform.
- World = the sampled reference bg (228,228,228); the rendered corner verified at 228.
- Area-light key 90 W / fill 25 W / rim 70 W, shadow catcher.
- ONE material `QA_clay` (asserted), no emission, no glass, compositor off (no glare).
- Full shot: az 32°, el 9°, 85 mm. Mouth detail: az 55°, el 10°, 50 mm.

## Self-scorecard — categories 1–4 (from render review only: clay-full, clay-mouth, the compare sheet)
Calibrated down per my history (I ran ~1–2 high versus panels).

| # | Category | MATCH | QUALITY | Evidence (render) |
|---|---|---|---|---|
| 1 | Per-feature shape (F1–F5, frozen) | 5.5 | 5.0 | F1 lip ring with bean rim and a lower lip that juts, read in clay-mouth; F1b cavity modeled but shallower than the reference's; F1c collar band present. F2 four dorsal bands overhanging, with split front plates by the mouth ✔; F2b flank plates present, but seams are shallow, not the reference's deep dark grooves. F3 smooth belly ✔. F4 two-part legs with shoulder pads ✔ but thinner/shorter. F5 tail present but thin and faint — the rings barely read, versus the reference's chunky 6-ring tail. |
| 2 | Silhouette | 5.5 | 5.5 | The body reads taller and rounder than the reference's longer egg; the mouth bulge position matches; the tail profile is small. |
| 3 | Massing / composition | 5.5 | 5.5 | Plate mass over belly and leg placement inside the footprint match; the tail is under-massed; the legs are slightly spindly. |
| 4 | Modeled detail | 4.5 | 4.0 | Seams are modeled but soft and shallow. **Defect:** small dark tick marks along several seams and at the lower inner lip (surface-net double-walled seams; see gaps). |

## Honest remaining gaps
1. **Seam ticks (defect, visible in both captures).** Native to the Hunyuan surface-net output (present undecimated too).
   - Tried and rejected: topological normal recalc (cleaned undecimated, re-broke after decimation), post-decimate fold relax (worse), a hidden inner core (spiked), ray-parity orientation (worse), voxel remesh (shell leaks → collapsed), and the marching-cubes mesher (blocky).
   - Proposed fix for the next pass: retopologize the formed surface (shrinkwrap a clean manifold cage onto c1) and keep the seams as modeled grooves.
2. **Tail under-massed and rings faint** — needs a re-gen strategy that doesn't cut the body (e.g. a rear-3/4 whole-body crop) or local sculpt from c1.
3. **Seam depth** — the reference's dark plate grooves are much deeper than c1's.
4. **Proportion** — the body is taller and rounder than the reference.
5. **UVs are provisional** (Smart UV, for tangents only); the material phase re-UVs.
6. Archive branch `eden-aliens-b-input-20261022` was not on origin when checked at 13:46. The muse.ai zip SHA verified.

## Thinking level
Ran at LOW (Decision 38/40). Proposal only, not applied: a medium bump for the retopo pass on gap 1.
