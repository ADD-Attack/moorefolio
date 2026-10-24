# element-log — EDEN-3D-02 aliens_node

Engine ref: `aliens-node-3d-reference.png` (sha256 f2c9ea6f…adb03, producer MANIFEST-verified 16:13 CDT).
Settings: ComfyUI 0.41.0, fp16 hunyuan_3d_v2.1, octree 256, 30 steps cfg 5, surface net @0.6.
Feed prep: none. The feed is the full reference frame, byte-identical. CLIPVisionEncode crop is set to `none` rather than `center`, because center-crop would cut the splayed feet at the frame edge. The ~13% horizontal squash this causes in CLIP is a known affine effect, corrected at build if the silhouette compare shows it.

| # | time CDT | action | element | prompt id | seed | reason |
|---|---|---|---|---|---|---|
| 1 | 16:14 | SEND | c1-wholebody (full ref frame) | 60ea0d6b-75b4-45b4-92ed-f1382198c1b9 | 42 | Whole body first (EDEN-3D-01 lesson: part crops melt). |
| 2 | 16:16 | APPROVE (with strip) | c1-wholebody-s42 | 60ea0d6b… | 42 | Two-angle preview: front oval, low-right teardrop, top and flank rim pods, vein ridges, two horns and the root-foot ring are all present and placed per the ref. Ground slab is baked in → strip at build. Watch items: feet thinner/stubbier-tipped than ref; horns thin. |
| 3 | 16:22 | BUILD | c1 → body + 7 feet | — | — | Slab stripped. Closed via inward solidify (8 mm) → voxel remesh (5 mm) → inner wall dropped (>3.5 mm from original). X ×1.12 to undo the CLIP squash; the front silhouette was ~12% narrow vs ref. |
| 4 | 16:24 | DECLINE (own split) | face-cut feet v1 | — | — | Cycles review: black jagged gaps at the foot/body cut under the teardrop. |
| 5 | 16:25 | DECLINE (own split) | overlap split v2 | — | — | Coincident duplicate faces z-fight as a jagged band around the base. |
| 6 | 16:26 | APPROVE | stub + offset overlap split v3 | — | — | Body keeps short root stubs and each foot sheathes its stub with a 2 mm normal offset. Residual: hairline seams. |
| 7 | 16:27 | APPROVE | horn refine (F3) | — | — | Horns were thin twigs vs the ref's thick spikes. Base-weighted taper scale (xy ×2.0 at base → ×1 at tip, z ×1.45) on the formed mesh. Uniform-scale attempt declined: it gave blunt fingers. |
| 8 | 16:29 | BUILD | budget re-decimate | — | — | 46,765 tris was over the 45k cap. Re-decimated (target 40k) → 44,548 final. |

## CLAY-FIX (panel: Cat 4 FAIL 5.0/4.8) — 2026-10-23 evening
| # | action | item | reason |
|---|---|---|---|
| 9 | BUILD | F5 vein troughs (`detail.py`) | EDEN-3D-01 concave-side unsharp on the 222k-face formed mesh before decimation. Two passes: depth = vertex − 14-iteration Laplacian surface along the normal; concave side only; diffused 3 iterations; feet zone excluded. Only troughs deepen; cords untouched. |
| 10 | DECLINE | horn gnarl v1 | Gnarl applied before thickening read as crumpled high-frequency noise, and the prong didn't show. |
| 11 | APPROVE | horn gnarl v2 + left prong | Thickening moved to high-res. Low-frequency knots scaled to horn radius. Left prong grown by a gaussian pull of the horn's own vertices on its outer flank. |
| 12 | DECLINE | planar foot split v1 | The 331° foot's flood-fill leaked up the right flank, leaving a vertical crack through the flank pod. |
| 13 | APPROVE | planar foot split v2 (`build3.py`) | Each root is bisected by a flat plane across its axis, plus a horizontal plane at z 0.24 that limits the flood-fill. Both sides are capped, giving clean flush joint rings instead of jagged triangle-edge seams. The sheath/offset lip is removed. |
| 14 | APPROVE | feet thickening | +4 mm along the normal with knob modulation, tapering from 0 at the joint ring to full at 5 cm out. Within budget. |
| 15 | BUILD | budget | The extra cuts cost tris, so the decimation target was lowered to 39.2k. Final 43,648 tris (body + 7 feet). The mound gets slightly fewer tris than at the clay gate (declared trade). |
