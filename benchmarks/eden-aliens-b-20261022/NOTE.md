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

---
# FIX PASS (2026-10-22, after the clay-gate panel: Cat 4 FAIL, F5 FAIL) — Forge

Thinking: the medium bump was approved but not patchable on this runtime, so the pass ran at **low**. The session also hit its limit at 16:03 and resumed at ~17:05.

## Changes (detail only; massing / silhouette / mouth / belly / legs protected — same c1 source, same cut planes, same 9 nodes)
1. **Seam ticks (target 1): FIXED.**
   - Clean retopo onto the c1 surface: inward solidify 6 mm → voxel remesh 4 mm (manifold) → drop the inner wall (faces >3 mm from the original c1).
   - This removes the surface-net double walls that caused the ticks. None are visible in either capture.
2. **Seam depth (target 2) + F2b (target 4): IMPROVED.** A geometric unsharp mask along normals, concave side only (×2.0 against a 40-iteration smoothed copy), deepens the dorsal-band and flank-plate grooves without inflating plate domes. Modeled geometry, no normal map.
3. **Mouth throat:** the open throat end is capped with a concave cup (the tube-end loop poked back 8 cm). The mouth/body cut is left uncapped since the nodes abut. The throat now reads deep instead of ending at a disc.
4. **F5 tail (target 3): NOT ENLARGED. HONEST GAP.**
   - Three enlargement methods were tried and declined in render (see element-log).
   - The delivered tail is c1's own tail, retopologized with deepened ring grooves and a higher budget (3.9k tris). It reads as ringed and tapering, but is still smaller and thinner than the reference.
   - Next step: generated image gen-rear34-01 → Hunyuan tail element, once the producer GO arrives, or a hand sculpt pass.

## Provenance
- Every node comes from Hunyuan c1-wholebody-s42 (prompt 92f9ec6c).
- **No element passed through a generated image.** gen-rear34-01 (CAPTEST, gpt-image-1.5) is logged and committed but unused (no GO; self-check found partial drift: rear-side rather than rear-3/4, and an invented-looking two-row tail and root collar).

## Contract
39,886 tris (body 17,999 · mouth 11,999 · legs 4×~1,500 · tail 1,596/1,298/998). Hierarchy unchanged. Tangents + TEXCOORD_0 present. Draco off. One clay material; no glare. Rendered bg corner 228.
Captures: captures/clay-full.png, clay-mouth.png, compare-full-vs-reference.png (gate-1 captures moved to captures/gate1/).

## Self-scores — re-panel categories only (render review: the fix captures vs the reference)
| Category | MATCH | QUALITY | Evidence |
|---|---|---|---|
| 4 Modeled detail | 5.5 | 5.5 | Ticks gone; plate and flank grooves read as modeled channels; throat deep. Grooves are still shallower and softer than the reference's dark cut seams; some seam edges carry slight surface waviness. |
| 1B Body (F2/F2b/F3/F4/F5) | 6.0 | 6.0 | F2b seams now defined. F5 is unchanged in size (the rings read a little better) and remains the weak feature, ~4/5. |

---
# TAIL PASS (post-gate improvement, Decision 46) — Forge, 2026-10-22

Owner direction: fix the tail on the clay with exaggerated features, no engine. **Tail-only change**: body, mouth and legs are built byte-identically by the same pipeline (same c1 source, retopo, seam deepening, cuts and budgets; verified tri counts unchanged within ±1 for those nodes).

**Method (scripts/build.py, TS/TL/RD block)** — sculpting on c1's formed tail before the node cuts:
1. Radial inflation from the tail's own axis (per-1 cm slice centroids): 4.5 cm × (1.3 at the root → 0.7 at the tip), so it tapers. The ramp runs 6 cm into the socket, so the root flares into the body as a thick collar.
2. Length ×1.5 from the socket (x-stretch only, so the segments stay aligned).
3. Five carved transverse ring grooves (1.3 cm deep, Gaussian width 5.5 mm), with rounded pillow pads between them (|sin|^0.35 profile); 3× tail-only smoothing.
4. Segment cuts are placed in grooves 1 and 3, so the tail_01→02→03 joints hide in seams. Pivots are at the segment roots; the chain is unchanged.

**Provenance:** no Hunyuan call and no generated image in this pass. All tail geometry is c1-wholebody-s42 (prompt 92f9ec6c), sculpted.

**Contract:** 41,679 tris (tail 2,386 / 1,899 / 1,400; body 17,998; mouth 11,999; legs ~1,500 each). 9 nodes, same hierarchy. Tangents + UV0 present; Draco off; one clay material; no glare; bg corner 228.

**Captures:**
- `captures/clay-full.png`, `clay-mouth.png`, and the new `clay-tail.png` (rear-3/4 tail detail, az −45°, el 14°).
- `compare-full-vs-reference.png`.
- The fix-pass captures moved to `captures/fixpass/`.

**Self-score F5 (render review: clay-full + clay-tail vs the reference): MATCH 5.5 / QUALITY 5.5** (up from panel 3.8/4.2).
- Thick, tapering and clearly ringed, with a fleshy root collar.
- The ring count is 5 against the reference's ~6, and the ring profile is more regular and stacked than the reference's lumpy two-row pads.
- The tip end is flatter than the reference's rounded tip.
- The tail sits slightly low behind the hind leg in the full view.
