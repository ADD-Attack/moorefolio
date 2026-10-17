# Mechanical Snake — Reference-Match Build

## Build and source

Built from the package's Exercise-2 `base/build_snake.py` and `assets/` model/texture set. The package archive SHA-256 matched the supplied value (`61625934b41126627cd6e1422bf1f491ac19ed250adc785f6e65d59f7ba82e49`); all entries in `MANIFEST.sha256` verified `OK`.

`prepare_textures.py` starts from `base-textures/snake_albedo.png` and deterministically neutralizes its strong blue cast into worn steel; the remaining source texture channels are kept from Exercise 2. `build_snake.py` creates a one-eye armored head, center-pivot body segment with raised covers, vents, fasteners and recessed mint joint housings, a tapered finned tail, and a long S-curved showcase assembly. `render_staging.py` produces the plain-background review shots. `snake.blend` has its image files packed.

## Geometry and export

| GLB | Triangles | Contents |
|---|---:|---|
| `snake_head.glb` | 15,024 | Static head assembly with one physical eye/lens, jaw piece, crest fins and neck joint |
| `snake_segment.glb` | 1,556 | Reusable rigid body cell, centered pivot, armor panels and joint housing |
| `snake_full.glb` | 58,516 | Complete assembled S-pose, including head, repeated body cells and tail |

Counts were computed from the exported GLB index accessors. Head and full-snake counts satisfy the brief's 10,000–18,000 and ≤60,000 triangle contracts. The segment is slightly above the dossier's indicative 800–1,500 segment range.

All three files are binary glTF 2.0. Export uses +Y up, modifier application, tangents, embedded materials/images, and Draco disabled. The source mesh is authored along Blender +X for the procedural path builder; an export-only -90° Z rotation makes the asset's front Blender -Y, which the +Y-up conversion maps to Godot model-front +Z. Dimensions are in meters. Each rigid body segment's object origin is its logical cell center; its geometry is 1.2 m long and adjacent cells are placed at 1.0 m pitch for overlap. The head origin is at the neck attachment.

## Textures

The GLBs each embed four image textures:

- `textures/snake_albedo.png` — 2048×2048, sRGB albedo.
- `textures/snake_normal.png` — 2048×2048 tangent normal, Non-Color.
- `textures/snake_orm.png` — 2048×2048 ORM, Non-Color; R=AO, G=roughness, B=metallic.
- `textures/snake_glow.png` — 256×64, sRGB joint-emission gradient.

`base-textures/snake_albedo.png` is the unmodified Exercise-2 source used by `prepare_textures.py`. `snake_height.png` is not used by the shipped materials.

## Animation / game usability

The character uses the dossier's per-segment rigid-mesh route; it has no skeleton or baked animation clips. In game, instance `snake_head.glb` at the first cell and one `snake_segment.glb` per remaining body cell; set each cell transform from the grid/path history and orient its local +Z model-forward toward the head after import. Interpolate node transforms between cell updates if smooth movement is desired. Add/remove instances for growth. The tail asset is a tapered end cap for the last cell. `snake_full.glb` is a static assembled display pose, not the gameplay-driven asset. The separated jaw is static in this build.

## Godot import check

Godot 4.7.2 editor import pass completed for all three exact GLBs in a fresh copy of the supplied `game-demo/` project using `--headless --editor --import --quit` (exit 0). Logs show `DONE import` for `snake_full.glb`, `snake_head.glb`, and `snake_segment.glb`; no errors or warnings were reported. The GLBs contain the four embedded image textures/material channels. This check was editor import only; no runtime gameplay or animation test was performed.

## Reference-match gaps (self-assessed)

- The eye has a housing, lens and emissive core, but its internal optical/iris detailing is simpler than the reference.
- The repeating armor covers and vents are clean, uniform procedural geometry; the reference has more irregular, densely machined plates, deeper wear, and finer fasteners.
- The joint bands read as narrow green emissive bands rather than the reference's broader, brighter teal-mint light cores.
- The head/neck are elevated, but the overall pose is still a ground-hugging broad coil rather than the reference's taller raised S-curve. The tail is tapered and finned but less mechanically elaborate.

Review captures are plain neutral-gray studio staging with no environment or HUD: `staging-full.png` (1920×1080) and `staging-head.png` (1600×1200).
