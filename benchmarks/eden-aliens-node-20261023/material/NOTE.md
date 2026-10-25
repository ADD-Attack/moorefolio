# EDEN-3D-02 aliens_node — MATERIALS-FINAL (2026-10-25 ~01:35 CDT)

Geometry is frozen at HORNS-FIX `64ae665` (43,584 tris; `aliens_node` → `body` → `foot_01..07`). F3 is accepted under Decision 62.

## Deliverables
- `aliens-node.glb`
  - glTF, +Y up, Draco off, **tangents ON**, one shared UV atlas (TEXCOORD_0).
  - One Principled material, `aliens_node`: baseColor, **ORM packed** (R = AO in the occlusion slot, G = roughness, B = metallic, all read from the same texture), emissive texture with `KHR_materials_emissive_strength` 2.8.
- `textures/`: `aliens_node_basecolor.png` (sRGB), `aliens_node_orm.png` (linear), `aliens_node_emissive.png` (sRGB). All 2048².
- `aliens-node-mat.blend` (source scene) and `aliens-node-mat-staged.blend` (judged staging).
- `captures/`
  - `mat-full-front`, `-34`, `-side`, `-back`, `mat-pods-front` (pod detail), `mat-horns`, `mat-base-34`, `compare-master-ref-mat` (master | ref | ours).
  - Render settings: Cycles 256 adaptive with denoise. Backdrop is the sampled ref background. Key/fill/rim lighting with a shadow catcher. ORM AO is multiplied into base colour in the render material only (AO rule). FOG_GLOW glare at threshold 1.0, strength 0.35, set through the Blender 4.5 sockets.
  - Rendered in the heavy slot at 01:28–01:32, after V-001 and V-003 had cleared.
- `scripts/` and `masks/`: everything is reproducible from the formed mesh. No generated images.

## Method
- **No hand painting.** Every map is derived from geometry, rasterised from per-vertex fields into the UV atlas, with 12 px edge padding.
- **Pods:** raycast-seeded flood fill from 9 pod centres, bounded by each dome's rim groove, eroded 2 rings so rims stay flesh. Emission and colour run from a darker orange edge to a bright amber centre, using a smoothed distance-into-pod. Roughness 0.10 (glassy).
- **Troughs:** smoothed concavity (the EDEN-3D-01 clean-groove recipe: Laplacian depth over edge length, diffused 8 iterations), mapped to a clean deep red (92,26,12). No short-radius AO and no noise mottling.
- **Value structure:** a highlight band on convex, up-facing areas (224,118,48); a red underside toward the base; ember body (186,84,32). AO is compressed to 0.55–1.
- **Horns:** dark (44,27,21), with convex areas lightened slightly, blending into the flesh at the base.
- **Feet:** body palette with stronger groove and underside darkening.

## Self-scorecard (cats 1–9, MATCH / QUALITY), from render review against `compare-master-ref-mat` and the staging set
Shaded down per my calibration history (my past material MATCH ran about 2 points high against the panel).

| Cat | MATCH | QUALITY | Evidence |
|---|---|---|---|
| 1 Per-feature shape | 5.0 | 5.0 | F1/F2 hold. F3 horns are tall and flame-branched against the ref's short chunky spikes (accepted under D62). F4/F5 as passed. |
| 2 Silhouette | 5.5 | 5.5 | Matches apart from the tall horns. |
| 3 Massing | 5.5 | 5.5 | Unchanged from the passed clay. |
| 4 Modeled detail | 5.0 | 5.0 | Unchanged from the fix round. Horn faceting is visible in `mat-horns`. |
| 5 Colour | 5.0 | 5.5 | Ember body, amber pods and dark horns follow the master's hue split. Our body runs slightly redder/darker than the ref's tan-orange. |
| 6 Bump/normal | 4.0 | 4.5 | **No normal map is shipped.** All relief is modeled geometry, so there are no micro-surface pores or dimples (the ref has fine pitting). |
| 7 Texture maps | 4.5 | 4.5 | Maps are clean and noise-free but vertex-resolution: smooth gradients, no fine texture. Atlas coverage is only 26%, a loose pack. |
| 8 Materials | 4.5 | 5.0 | Glassy pods versus satin flesh read correctly. The pods lack the ref's inner depth/refraction; they read as emissive glossy domes. |
| 9 Lighting/effects | 5.0 | 5.5 | Tight bloom on the pods and contact shadow. The glow is close to the master's. |
| Overall | 5.0 | 5.0 | Reads as the creature; the main debts are the horns and the missing micro-surface. |

## Honest gaps
1. **No normal map.** The micro pitting and bark lines on the feet are absent. This is the biggest risk for cat 6.
2. **Top-left pod glow spills onto part of its rim** (visible in `mat-base-34`, upper left).
3. **The back pods** sit where the ref gives no ground truth (Hunyuan's back); they glow for consistency.
4. **Horns:** tall flame-branched form (accepted F3 state), and facets show in the close-up.
5. **Loose UV packing (26%)** wastes texel density. It's harmless at vertex-resolution maps but would matter for added micro detail.
6. **Foot darkening is subtle;** the feet still read flatter than the ref's barky roots.

STOPPED for the full material panel (cats 1–9).
