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
# TAIL PASS (17:58; superseded framing — see GATE-RETRY below. The gate was NOT passed) — Forge, 2026-10-22

Owner direction: fix the tail on the clay with exaggerated features, no engine. **Tail-focused change.** Mouth and legs are unchanged: same pipeline, same c1 source, retopo, seam deepening, cuts and budgets. **One deliberate body edit:** the root-collar ramp reshapes the body's rear socket (the last 6 cm in front of the tail, inside |y|<0.16, -0.36<z<-0.02) so the tail flares into it. The rest of the body is unchanged (its tri count moved by 1).

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

---
# GATE-RETRY v1 — SUPERSEDED (hand-modelled in Blender, the opposite of the owner's direction; kept for the record; captures in captures/gateretry-handmodel-superseded/) (Decision 46 as corrected: the clay gate stands FAILED at re-panel Detail 5.5/4.6, 1B 6.8/6.2, F5 3.8/4.2; this is the new attempt) — Forge, 2026-10-22

Two halves, both on the clay. No engine, no generated image. Source still c1-wholebody-s42 (prompt 92f9ec6c).

**1. Tail (F5), exaggerated.** Carried from the 17:58 tail pass:
- Radial inflation 4.5 cm (root 1.3× → tip 0.7×), length ×1.5.
- Five carved ring grooves (1.3 cm deep) with rounded pillow pads.
- Root collar flaring into the body's rear socket; segment joints hidden in grooves.

**2. Detail finish (the Cat 4 QUALITY gap): deeper, cleaner grooves.**
- **Denoise first:** the surface is denoised (4 smoothing iterations) before deepening, which removes the seam waviness that the old pass amplified.
- **Deepen:** grooves are deepened ×4.0 against an 80-iteration smoothed reference (was ×2.0 / 40), concave side only, so plate domes and massing are unchanged.
- **Mouth zone:** x > 0.15 is deepened at 0.7×, and the throat cup is pushed back 12 cm and excluded from deepening, so the throat stays deep (×4.5 and an unprotected ×4.0 turned it into a ball; both declined, logged).

**Protected:** massing, silhouette, mouth unit, belly, legs and plate shapes come from the same cuts and budgets; the 9 nodes are unchanged. The only deliberate body edit is the tail-root collar in the rear socket.

**Contract:** 41,701 tris (body 17,996 · mouth 11,997 · legs ~1,500 · tail 2,374/1,936/1,400). Tangents + UV0. Draco off. One clay material; no glare; bg corner 228.

**Captures:**
- `captures/clay-full.png`, `clay-mouth.png`, `clay-tail.png` (rear-3/4 tail detail).
- `compare-full-vs-reference.png`.
- Earlier rounds are in `captures/gate1/`, `fixpass/` and `tailpass/`.

## Self-scores (render review: full/mouth/tail captures + the frozen-camera compare)
| Category | MATCH | QUALITY | Evidence |
|---|---|---|---|
| 4 Modeled detail | 5.5 | 5.5 | Plate and flank grooves are continuous, deeper channels with clean walls; waviness much reduced; no ticks; throat deep. Still short of the reference's tight dark slit seams (ours are wider, U-shaped channels). One tiny dark speck at the hind-leg socket (clay-tail). |
| 1B Body | 6.5 | 6.5 | F2/F2b grooves read; F5 is now thick and clearly ringed (5 rings vs ~6; flat tip; regular stacked rings vs the reference's lumpy two-row pads). |

Calibration note: on this ticket my strong categories ran ~1 low and my detail call was exact. I have held detail at 5.5/5.5 and not inflated it.

---
# GATE-RETRY v2 — OPERATIVE (owner direction via Muse's 2nd correction) — Forge, 2026-10-22

The gate stands FAILED (re-panel Detail 5.5/4.6, 1B 6.8/6.2, F5 3.8/4.2). This is the retry.

**Method:** regenerated reference → Hunyuan → tail element → Blender stitch only.
- **Base:** the bace685 clay, **unchanged**. Body, mouth and legs are verified byte-identical by per-node POSITION hash against the bace685 GLB; that includes the retopo, the seam work and the throat.
- **Changed geometry:** only tail_01..03. The v1 groove-deepening and hand-modelled tail are not in this delivery.

**Tail element provenance (Decision 45/46 fences, all logged in element-log.md):**
1. **Reference:** `generated/gen-tail-ref-01.png`. Model openai/gpt-image-1.5, an edit of the pack aliens-b-3d-reference.png. It shows the tail only, side view, exaggerated (bigger, thicker, 6 pronounced rings). I self-checked it against the reference and approved it as Hunyuan input only; it is not ground truth.
2. **Hunyuan:** `c4b-gentail-s42`, prompt **7e640c0c-87db-49fa-9a5f-d68a1a179d10**, seed 42, fp16 v2.1, octree 256, surface net 0.6. Input: gen-tail-ref-01 masked by saturation (shadow and gradient flattened to bg 228), padded to 1024². The unmasked first send (c4, prompt 72328b2e) was declined: it grew slabs.
3. **Stitch (`scripts/stitch.py`, Blender):**
   - Keep the largest island, close holes, then voxel remesh 2.5 mm into a manifold (raw collapse-decimation shattered it, so declined).
   - Rotate the root to the socket, scale to 0.42 m length, then ×1.45 thickness about the element axis.
   - Seat it 3 cm into the body at x=-0.56, z=-0.19.
   - Cut into thirds (tail_01/02/03), cap the cuts, decimate to 2,400/1,900/1,400.
   - Root pivots; chain body→tail_01→tail_02→tail_03; provisional UVs.

**Contract:** 41,694 tris. 9 nodes, same hierarchy. Tangents + UV0. Draco off. One clay material; no glare; bg corner 228.

**Captures (256 spp):** `captures/clay-full.png`, `clay-mouth.png` (unchanged geometry), `clay-tail.png` (rear-3/4 tail detail), `compare-full-vs-reference.png`.

**Self-scores (render review):**

| Category | MATCH | QUALITY | Evidence |
|---|---|---|---|
| 1B Body | 6.5 | 6.5 | F5: a chunky tapering tail, 6 pronounced pillow rings, upturned rounded tip; reads at full-shot distance. Single-row rings vs the reference's two-row pads; set a little lower and narrower at the root than the reference's. F2/F2b/F3/F4 as at bace685. |
| 4 Modeled detail | 5.0 | 5.0 | Body detail is the bace685 state (ticks gone; seams deepened ×2.0; slight waviness remains; U-channels vs the reference's slits). The new tail adds crisp, well-formed ring grooves. |

Note: Cat 4 detail beyond the tail is deliberately unchanged, per "everything else stays exactly as delivered at bace685". The stronger ×4 groove finish from v1 is available as a separate option if the producer wants it on the body.

---
# STITCH-BLEND (post-gate, owner-directed stitch refinement) — Forge, 2026-10-22 20:15 CDT

**Owner read** (matching my STATUS concern #4): the pipeline tail was a plug, not a blend; oversize; "thrown on there".

**Scope:** the seat only. Base is the operative clay 2c25df3; the Hunyuan tail element c4b is unchanged in form; Blender work is limited to the stitch.

**Changes:**
1. **Scale −10%:** length 0.42 → 0.378 m, uniform, so the ×1.45 thickness ratio and the ring forms are untouched.
2. **Root blend:** tail_01's root skirt widens radially along a 15 cm zone (up to +4.5 cm, smooth t^2.2 profile). The widening saturates at the body surface plane (x=−0.56) instead of growing inside the body, so no rim pokes out. The root is seated 8 cm into the mass and sits at z −0.18. This buries the old c1 stalk and removes the cork step.
3. **Body untouched:** body, mouth and legs are byte-identical to 2c25df3 (per-node POSITION hash). I did the blend entirely in tail_01 rather than sculpting the body socket, so the rigid tail joint stays clean for animation.

**Contract:** 41,692 tris; 9 nodes; same hierarchy; tangents + UV0; Draco off; clay.

**Captures (256 spp):** clay-full, clay-mouth (unchanged geometry), clay-tail, compare-full-vs-reference. The 2c25df3 captures moved to `captures/gateretry-v2-2c25df3/`.

**Residuals:**
- A slight rim where the widened root meets the rear-bottom curve, visible in the low tail close-up only.
- Some old c1 stalk lumps (body geometry, kept byte-identical by order) still show between the tail root and the hind leg.

Removing both properly means feathering the body socket itself. That is a body edit; I'll do it on the owner's word.

**Material phase note:** the paused material bake (b5f72d3) is on the 2c25df3 tail. When materials resume, the tail region of the atlas must be re-baked on this geometry. That is a procedural re-bake, not a repaint.

---
# STITCH-REGEN attempt 2 (owner-directed; pure-crop feed image) — Forge, 2026-10-22 21:31 CDT

**Supersedes** STITCH-BLEND 98a44eb (lip ruled against by the owner) and the failed edit-based attempt (stitch-regen-attempt2-FAILED/).

**Feed image:** `generated/gen-tail2-cand-02.png`, a **pure crop (0,560,420,960)** of the pack reference with zero generated pixels. Selected and pushed before Hunyuan (c3b6500).

**Prep (non-generative):** saturation mask → flat bg 228 → square pad → 1024² (`crops/c6-tail2-prep.png`).

**Element:** Hunyuan c6-tail2-s42, prompt **c539b9c5**, seed 42.
- The tail formed with the reference's two-row lumpy pads.
- The cut body margin grew a crumpled blob with the fused leg pad; that is discarded at the seat cut.

**Stitch** (`scripts/stitch_regen.py`). Seat + cut only: no skirt, no flare, no surface conform.
- Voxel remesh (6 mm) for a clean manifold.
- Yaw +44.9° to square the 3/4-view tail onto the body axis.
- **×1.5 stretch along the tail axis** to undo the 3/4 foreshortening (a seating transform, flagged here).
- Uniform scale 0.32.
- Root buried at (x −0.47, z −0.17), so the root top tucks under the rear plate overhang.
- Blob cut at element x −0.30.
- Chain cut into tail_01/02/03, decimated to 2,600/1,900/1,400, root pivots, same parenting.

**Acceptance test: PASS.** No visible lip/rim/gap at the root in `captures/clay-tail.png`, `captures/compare-full-vs-reference.png` or the 3× root zoom `captures/root-zoom.png`.

**Body untouched:** body, mouth and legs are byte-identical to bace685 (per-node POSITION hash). Contract: 41,893 tris, 9 nodes, tangents + UV0, Draco off, clay.

**Honest gaps:**
- The tail reads **stubby with a blunt, fan-like tip**. That residue of the reference's 3/4 foreshortening survives Hunyuan even after the ×1.5 stretch. The reference tail is longer and tapers to a point.
- It sits slightly lower and wider than the reference tail.
- The old c1 stalk lumps by the hind leg (body geometry) are still faintly visible beneath the root.

**Materials:** still paused. The material bake must be redone on this geometry when the producer gives the go.
