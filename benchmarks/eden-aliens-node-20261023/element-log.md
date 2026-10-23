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
