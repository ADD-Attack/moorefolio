# STATUS — MATERIAL checkpoint (2026-10-25 ~00:25 CDT)

- **Built:** UVs (one shared smart-project atlas), 2K maps (basecolor sRGB, packed ORM linear, emissive sRGB), Principled material, `aliens-node.glb`.
  - Tangents ON, occlusion and metal/roughness both read from the one ORM texture, KHR_materials_emissive_strength 2.8.
  - 43,584 tris; node tree unchanged.
- **Masks are geometry-derived; no generated images:**
  - Pods: raycast-seeded flood fill bounded by the dome/rim groove, eroded 2 rings.
  - Horns: by axis and height.
  - Troughs: smoothed concavity (the EDEN-3D-01 clean-groove recipe, no AO speckle).
- `previews/SPOT-24spp-*` are iteration spot stills only, **not judged captures**.
- **Waiting on the GPU heavy slot.** At 00:21 it was held by another Blender job (V-001/V-003 per the queue). The judged Cycles set runs when it frees.
