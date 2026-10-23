# element-log — EDEN-3D-02 aliens_node

Engine ref: `aliens-node-3d-reference.png` (sha256 f2c9ea6f…adb03, producer MANIFEST-verified 16:13 CDT).
Settings: ComfyUI 0.41.0, fp16 hunyuan_3d_v2.1, octree 256, 30 steps cfg 5, surface net @0.6.
Feed prep: none. The feed is the full reference frame, byte-identical. CLIPVisionEncode crop is set to `none` rather than `center`, because center-crop would cut the splayed feet at the frame edge. The ~13% horizontal squash this causes in CLIP is a known affine effect, corrected at build if the silhouette compare shows it.

| # | time CDT | action | element | prompt id | seed | reason |
|---|---|---|---|---|---|---|
| 1 | 16:14 | SEND | c1-wholebody (full ref frame) | 60ea0d6b-75b4-45b4-92ed-f1382198c1b9 | 42 | Whole body first (EDEN-3D-01 lesson: part crops melt). |
| 2 | 16:16 | APPROVE (with strip) | c1-wholebody-s42 | 60ea0d6b… | 42 | Two-angle preview: front oval, low-right teardrop, top and flank rim pods, vein ridges, two horns and the root-foot ring are all present and placed per the ref. Ground slab is baked in → strip at build. Watch items: feet thinner/stubbier-tipped than ref; horns thin. |
