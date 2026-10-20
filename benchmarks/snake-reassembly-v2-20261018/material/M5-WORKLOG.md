# M5 material-only work log — 2026-10-20

Owner amended mandate: iterate autonomously until self-judged READY for material gate, or report inability. Geometry/UV/transforms remain frozen. M4 is not a submission.

## Recovery

No old render/bake processes survived. Initial `material_m5.py` stopped on a syntax error before saving anything. Corrected and reran once from M4 procedural. No partial bake existed.

## M5 first pass — live preview review

- Replaced coarse polygon-centre grille assignment on tail with metal and per-shading-point vent bounds. Viewed all four detail previews: no more woven pattern on shell/fins.
- Existing joint insert gets dark material edge rails and a narrower teal emitting centre; no opacity/hiding or geometry change. Viewed head/segment/tails: tiles substantially less broad/bright.
- Reduced pitting amplitude, reinforced existing geometry-distance edge masks and warm streaks. Reviewed against reference: still too clean/uniform. NOT READY.
- Geometry and UV hashes exact before/after (`m5-shader-audit.json`). Checkpoint `dd68548` pushed.

## M5b second pass

- Varied alloy tone by existing material/connected component: cooler upper steel, warmer lower plate, darker fin inset; no Voronoi patches or invented seams.
- Increased interrupted streak/scratch contrast and roughness variation; preserved confined vent mask.
- Viewed all five 960x540 live previews against reference. Material differentiation improves modestly but remains weak; detailed judgment deferred to 1920x1080 live diagnostic head/segment previews (64 samples, NOT production).

## Research actually consulted this continuation

Blender Manual Geometry node (fetched 2026-10-20; actual relevant body read from extracted file): https://docs.blender.org/manual/en/latest/render/shader_nodes/input/geometry.html . Pointiness approximates per-vertex curvature; Random per Island supplies one value per connected component. Applied the latter only to real separate parts, not fake procedural plate regions; retained the previously rasterized physical-edge masks for edge specificity. The latest Bump page fetch returned 404 and is not claimed as a read source. Earlier M4 research remains recorded in NOTE.md.

## M5b high-resolution review → M5c

1920×1080 live head/segment review exposed global brushing that the small previews understated. Rejected that global scratch treatment. M5c confines both new and inherited hairline color masks to existing physical-edge neighborhoods, reduces interior scratch coverage, strengthens restrained alloy-tone separation on existing parts, and slightly strengthens brown-grey streaking. No geometry, normals, UV layout or transforms edited. Tail contamination and narrower luminous band corrections retained. Preparing separate `textures-m5/`, mapped blend and GLB so the original M4 maps/export remain recoverable and unmodified.
