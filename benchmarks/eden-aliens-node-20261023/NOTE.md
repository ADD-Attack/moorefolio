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
