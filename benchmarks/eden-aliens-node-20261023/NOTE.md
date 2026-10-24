# EDEN-3D-02 aliens_node — QA Clay assembled gate delivery (2026-10-23)

Builder: Forge (studio-3d), claude-opus-5-5 at thinking low. **STOPPED at the clay gate. No material work has started.**

## Deliverables
- `aliens-node-clay.glb`: glTF, +Y up, modifiers applied, Draco off. **44,548 tris** against a 45k budget.
  - Hierarchy: `aliens_node` (root empty) → `body` (horns ride it) → `foot_01`…`foot_07`, each a separate rigid node pivoted at its root end.
  - One Principled material, `clay`.
  - **Tangents are off.** The clay mesh has no UVs yet, and tangents need UVs. They will be turned on at the material phase once UVs exist.
- `aliens-node-clay.blend`: the staged judged scene.
- `scripts/`: `hy_send.py`, `graph-template.json`, `build1.py` (slab strip and close), `build2.py` (squash fix, decimate, foot split), `horns.py` (F3 refine), `stage.py` (judged captures and GLB export), `preview.py`, `sbs.py`.
- `captures/`, all at identical staging:
  - `clay-full-front`, `-34`, `-side`, `-back`, `clay-pods-front` (pod-field detail), `compare-front-vs-ref`.
  - `workbench-preview-*` (flat iteration previews, not judged).
  - Judged renders: Cycles, 256 adaptive samples, denoise, GPU OPTIX. Backdrop = ref background sampled at sRGB (220,210,202). Key, fill and rim area lights; shadow-catcher contact shadow; one neutral clay material, with no emissive and no bloom.

## Method and provenance
- **Element c1 (the only Hunyuan element):** the full reference frame, `aliens-node-3d-reference.png`, byte-identical with no prep.
  - Prompt `60ea0d6b-75b4-45b4-92ed-f1382198c1b9`, seed 42, fp16 v2.1, octree 256, surface net.
  - CLIPVisionEncode crop is `none`, not `center`, so the splayed feet at the frame edge aren't cut off. The resulting squash was undone with X ×1.12, checked against the front silhouette.
- **Build from the formed mesh (D35):** the slab was stripped, the shell closed, it was decimated, the feet were segmented, and the horns were refined by deforming their own vertices. Nothing was rebuilt from primitives.
- **GPU:** one Hunyuan generation and the judged Cycles renders, all run under the producer's 16:12 "proceed". Flagging this here in case the D55 slot needed a separate explicit grant.

## Self-scorecard (categories 1–4, MATCH / QUALITY)
Scored from `compare-front-vs-ref.png` and the four staging angles only (D36). Shaded down per my calibration history.

| Cat | MATCH | QUALITY | Evidence |
|---|---|---|---|
| 1 Per-feature shape | 5.5 | 5.5 | **F2 pods:** layout matches (front oval, low-right teardrop, three top, two flank), rims are rolled, domes are proud. **F1 mound:** right massing, but the sub-lobes are softer. **F3 horns:** thick and tapered now, but the right horn is short and the left horn's secondary prong is weak. **F4 feet:** 7 thinner roots vs the ref's ~9 thick forked ones. **F5 veins:** present as soft cords, not the ref's crisp, branching, deep-trough cords. |
| 2 Silhouette | 6.0 | 6.0 | Front outline: mound width/height, crown pods and the foot spread track the ref. The horns now break the top line. |
| 3 Massing / composition | 6.0 | 5.5 | Pod sizes, placement and balance match. The base reads slightly tall and narrow next to the ref's squat root flare. |
| 4 Modeled detail | 5.0 | 5.0 | Rims and dome edges are modeled geometry. Vein troughs are shallow, the crown region between the top pods is muddy, and the back is generic lumps. |

## Honest remaining gaps
1. **Hairline seams** at the foot/body junctions, visible in `clay-pods-front` and `clay-full-side`. They come from the rigid-node sheath overlap.
2. **F5 veins are too soft.** The EDEN-3D-01 concave-side unsharp recipe can deepen them. I propose that as the first fix if the panel flags detail.
3. **Feet are thinner and fewer** (7 nodes, against the contract's ≥4) than the ref's root mass. Thickening the root bases would cost tris.
4. **The back of the mound** is unreferenced and was hallucinated by Hunyuan as lumps and pods. It is plausible but has no ground truth.
5. **The crown between the top pods** is muddy compared with the ref's clean vein knot.

---
# CLAY-FIX addendum (2026-10-23, after the panel's Cat 4 fail at 5.0/4.8)

Detail-only. **Frozen and unchanged in method:** mound form, pod field, massing/proportions (same X ×1.12 correction), and node structure (`aliens_node` → `body` → `foot_01..07`). One `clay` material. **43,648 tris** against the 45k cap. Captures are in `captures-fix/`, with identical staging plus one added `clay-base-34` close-up of the foot junctions. The original clay-gate captures remain in `captures/`.

## What changed (all on the formed mesh; no generated images, no new Hunyuan run)
1. **F5 veins:** concave-side unsharp (EDEN-3D-01 recipe) at 222k faces before decimation. Troughs between the cords and around the pod rims are deeper and the floors stay clean, with no noise added.
2. **Horns:** thickening moved to high-res, low-frequency gnarl knots added, and the **left-horn secondary prong** grown from the horn's own vertices.
3. **Foot seams:** each foot is now separated by planar cuts, a flat plane across the root plus a horizontal limiter, with both sides capped. The joint reads as a clean ring rather than a jagged crack. The z-offset sheath from the clay gate is gone.
4. **Feet:** +4 mm knobby thickening tapered from the joint. **Trade declared:** to pay for the cut and cap geometry, the mound decimation target went from 40k to 39.2k (body is ~1k tris lighter).

## Self-scores (render review only: `captures-fix/compare-front-vs-ref`, `clay-pods-front`, `clay-base-34`, side, back)
| Item | MATCH | QUALITY | Evidence |
|---|---|---|---|
| Cat 4 Modeled detail | 5.5 | 5.5 | Vein troughs now read as grooves under the key light (front and pod close-up). Horns are knotted and the left horn has a prong. The base no longer has jagged scars. Still short of the ref: its crisp branching vein network, and the crown knot between the top pods remains muddy. |
| 1B · F3 horns | 5.0 | 5.0 | Gnarled with a visible left prong. The right horn is still short and stubby against the ref's tall spike. |
| 1B · F4 feet | 5.0 | 5.0 | Slightly thicker with knobby forks. Still 7 roots and thinner than the ref's heavy root mass, because massing is frozen. |
| 1B · F5 veins | 4.5 | 5.0 | Clean deeper troughs. The cords are still Hunyuan's layout, softer and less branched than the ref. |

## Remaining gaps (honest)
- **Joint rings are visible** as clean lines at each root. That's inherent to rigid foot nodes. They are no longer cracks.
- **Two tiny specks** at the z 0.24 limiter cut on the front base (visible in `clay-base-34`, centre-left and centre-right, just above the roots).
- **Crown between the top pods** is still muddy. **Right horn** is short.
- **The back** remains unreferenced (Hunyuan's guess).

STOPPED for the spot re-panel (Cat 4 + Cat 1B). Materials are held.
