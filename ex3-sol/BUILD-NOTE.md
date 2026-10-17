# Exercise 3 — Silver / Mint lighting study

## Intent and scope

A neutral product-lighting study: warm-white upper key, cool low fill and a silver back edge. Broad reflection cards reveal the width and roughness of the plates, while a darker lower hemisphere keeps the undersides and collar recesses legible. The mint stays localized to the original emitters and their housings. The arena variant reduces the studio energies to coexist with the room's existing practicals.

This is lighting only. All three supplied GLBs, their embedded materials, all supplied texture PNGs, and the game mechanics are unchanged. The authored full-model pose and joint spacing are preserved. The review close-up instances the supplied `snake_head.glb`, at the corresponding head transform from `snake_full.glb`; it does not modify or crop geometry. No snake material override, emission multiplier edit, texture repaint, mesh edit, or image post-processing was used.

## Implementation and reproduction

- `rig/lighting/mood_rig.gd`: shared rig; `in_game` selects the energy/environment variant.
- `rig/lighting/studio_reflections.gdshader`: analytic reflection-only studio sky, not a snake shader.
- `rig/lighting/staging.tscn`: plain review scene, one subject, no floor or HUD.
- `rig/lighting/ingame_study.tscn`: evidence wrapper around the original game scene, deterministic side-by-side arrangement. The primitive game snake is on the left, the supplied production model on the right.
- `rig/lighting/capture_study.gd`: reproducible captures and exact light inventories.
- `rig/main.gd`: only the original `_build_world()` environment/two-directional-light block is replaced by an instance of the in-game rig. Gameplay, arena geometry, existing practicals and game materials are untouched.

`rig/` is a project overlay, not a self-contained model distribution: `models/*.glb` and `.godot/` are deliberately excluded as requested. All original scene/script/resource files, shaders, texture dependencies, import sidecars and UIDs are included. Restore the three original GLBs into `rig/models/` before opening this delivered overlay, or use the complete modified `game-demo/` in the exercise work root. No external assets, addons or paid services are required; Godot's native lighting, sky, tonemapper and glow are sufficient.

From the exercise work root, with Godot 4.7.2 on PATH:

```sh
godot --headless --editor --path game-demo --import --quit
# Wait for the editor command to finish successfully before running:
DISPLAY=:0 godot --path game-demo --audio-driver Dummy --resolution 1920x1080 --script res://lighting/capture_study.gd
```

For the delivered overlay, replace `--path game-demo` with `--path rig` and keep `captures/` beside `rig/`. On a desktop, omit `DISPLAY=:0` if already set. Open either lighting `.tscn` to inspect the study interactively. `main.tscn` remains the playable game entry point; the fixed evidence composition is not a gameplay change.

## Framing and capture discipline

All four PNGs are **1920 × 1080**, direct Godot viewport readbacks, without retouching, cropping or color grading. Perspective cameras, Y-up world units in meters. The supplied standard specifies centered whole-subject framing rather than numeric camera coordinates; `framing.gd` fits the actual imported bounds with margin.

| Capture | Camera world position | Look target | Vertical FOV |
|---|---|---|---|
| staging-full | (2.703290, 3.826466, 6.864665) | (0.203990, 0.541672, -0.276191) | 33.7° |
| staging-head | (5.129786, 2.038178, 3.886308) | (2.480141, 0.570682, -0.190070) | 30° |
| ingame-full | (0, 18.5, 26.6), **unchanged shipping camera** | (0, 1.5, 0) | 33.7° |
| ingame-head | (7.127491, 2.480000, 5.231217) | (3.877491, 0.630000, 1.131217) | 30° |

The in-game production instance has translation (1.5, 0, 0.5), yaw -20°, scale 1. The in-game close-up moves only the evidence camera and hides the HUD; it retains the same arena, rig, practicals and model instance. The wide keeps the complete HUD/minimap at the shipping camera. Its pose is fixed and `_update_hud()` plus `minimap.update_state()` are called manually after freezing `_process`, then multiple frames and `RenderingServer.frame_post_draw` are awaited. The review head is isolated from the body so only the entire head assembly is presented on the plain background.

## Key, fill, rim and collar practicals

Colors below are sRGB hexadecimal; energies are Godot's relative, non-physical light-energy units (not lux). All directional positions are (0, 8, 0); their positions do not affect illumination. Angles are Godot XYZ Euler degrees. No spots are used.

| Source | Type | Color | Staging energy | In-game energy | Rotation | Shadow / softness |
|---|---|---|---:|---:|---|---|
| Key_SoftWarm | DirectionalLight3D | #FFF1DF | 1.60 | 1.25 | (-48, -32, 0) | on; angular distance 8° |
| Fill_Cool | DirectionalLight3D | #D3E3F4 | 0.38 | 0.32 | (-24, 58, 0) | off |
| Rim_Silver | DirectionalLight3D | #D9EFFF | 1.80 | 1.45 | (-32, 155, 0) | on; angular distance 5° |

Key and rim: specular 1, shadow bias 0.03, normal bias 0.5, directional shadow distance 55 m, blended cascade splits. Directional shadow atlas 4096; 4× MSAA. Fill specular 1. Default light masks; no material or mesh-layer tricks.

Each of the four authored collars gets two short-range **OmniLight3D** spill lights, placed at collar center + (0, 0.05, ±0.47) in the model's coordinate system. All are #7AFFBF, energy **0.035 staging / 0.045 in-game**, range **0.75 m**, attenuation **1.5**, size **0.16 m**, specular **0.25**, shadows off. These approximate local bounce from the emissive diffuser: they gently touch the nearby lip/interior, rather than making the entire body emissive. The isolated staging head uses just its two collar lights. Exact world positions for every instance, including the isolated head, are listed below and in the JSON inventories.

## Environment and reflections

| Setting | Staging | In-game |
|---|---|---|
| Visible background | `BG_COLOR`, #65676B, featureless | `BG_COLOR`, #101A23, normally occluded by arena |
| Ambient source | SKY | SKY |
| Ambient energy | 0.50 | 0.38 |
| Ambient sky contribution | 1.0 | 1.0 |
| Reflected source | `REFLECTION_SOURCE_SKY` | same |
| Background / sky energy multiplier | 0.75 | 0.60 |
| Sky | shared analytic studio | same |
| Radiance size / process | 512 / QUALITY | same |
| Sky rotation | (0, 0, 0) | same |
| Fog | disabled | disabled |
| SSAO | on, radius 0.22, intensity 0.6, power 1.25, light affect 0 | same |
| SSR / SDFGI / baked GI / probes | disabled / none | same |

The visible backdrop is deliberately separate from the IBL: `BG_COLOR` hides the studio sky from the camera, while explicit SKY ambient and reflection sources keep it available to the metal. No scenery or reflection card geometry is visible in review.

The sky shader's linear-HDR base transitions from lower-hemisphere RGB **(0.035, 0.043, 0.052)** to upper RGB **(0.30, 0.33, 0.37)** using `smoothstep(-0.45, 0.8, direction.y)`. Two soft-edged rectangular radiance cards are added:

| Reflection-only source | Normalized direction from subject | Half extents in projected sky coordinates | Linear HDR RGB added |
|---|---|---|---|
| Broad key softbox | normalize(-0.4, 0.8, 0.5) | (0.80, 0.30) | (1.70, 1.60, 1.45) |
| Narrow silver strip | normalize(0.4, 0.5, -0.8) | (0.65, 0.13) | (0.70, 0.85, 1.05) |

Both card edges feather over 0.07 projected units. These are infinite-distance environment radiance, not extra finite-position lights. Broad versus narrow reflections make adjacent roughness values readable. The dark lower hemisphere preserves contrast and prevents a uniform chrome wash.

## Tonemap, glow and renderer

**Filmic**, exposure **1.0**, white **4.0**; no automatic exposure or custom LUT. It provides a controlled shoulder for metallic reflections and retains a colored mint emitter core. The original ACES setup was replaced: the brief specifically flags ACES emissive clipping, and expanding the emitter to a white band would hide its housing. Source emission values are untouched. The visible gray background also passes through the tonemapper, so its final pixel value is darker than the source color picker value.

Glow is enabled in Forward+: normalized levels, **ADD** blend, intensity **0.16 staging / 0.22 in-game**, strength **0.75**, bloom **0.0**, HDR threshold **0.8**, HDR scale **1.0**. Levels 1–7 are **[0, 0.50, 0.35, 0.15, 0, 0, 0]**. It is intentionally restrained: no fullscreen bloom veil, no attempt to hide the diffuser/housing distinction. The room's brighter practicals can bloom; collar spill is principally supplied by its local lights, not by exaggerated bloom.

The supplied project selected `gl_compatibility`; the study selects **Forward+** in `project.godot` so the intended glow, SSAO, HDR and soft shadows are actually evaluated. Captures were rendered in Godot **4.7.2.stable.official.ed1daf0bf**, Vulkan 1.4.318, llvmpipe software device. This is an offline visual study, not a shipping hardware-performance claim.

## Godot-specific traps and handling

1. **Fresh import / null textures:** verified the ZIP SHA-256 and every manifest line before work. Ran the Godot editor import pass before rendered captures, and reran import after adding resources. The capture harness additionally checks every plate surface for non-null albedo, normal and roughness textures; it reports five textured plate surfaces in the full asset. Original asset SHA-256 values are retained in `UNCHANGED-ASSETS.sha256`.
2. **Black metallic surfaces:** a flat background alone is not a reflection source. Explicit SKY reflections plus the studio radiance cards supply metal response even though the camera sees only gray.
3. **ACES / emission:** chose Filmic and restrained exposure, without changing the embedded emission materials. The source-colored core, bezel and lip remain distinct.
4. **Frozen process / stale UI:** froze only the evidence scene after constructing its game state, manually fed HUD and minimap, allowed frames to draw, and captured after `frame_post_draw`. No frozen capture logic was inserted into the playable game's process loop.
5. **API spelling:** the installed 4.7 build's reflection enum is `Environment.REFLECTION_SOURCE_SKY`; verified it with ClassDB after an initial parse error. Final import and capture logs are retained as evidence.
6. **Framing:** authored origins are not visual centers. Fit transformed imported mesh bounds, then isolated the original head asset for the review close-up. No geometry repair or pose reconstruction was performed.
7. **Emission is not GI:** the original emission material cannot light neighboring housing by itself. Small motivated collar practicals supply that local interaction; there is no material cheat or baked texture lighting.

## Complete light inventories

The following tables enumerate **every Light3D** present in each capture setup, including the original room and apple practicals. No in-game practical was removed, recolored or re-energized. JSON files beside this note retain the exact engine float values and node paths. `staging-full` and `ingame-full` inventories also apply to their corresponding views except that the isolated staging head has only its own two collar lights (separate inventory below). Omni rotations have no effect on their illumination.

### Staging full — 11 lights

| Node path | Type | sRGB | Energy | World position | World XYZ angle | Range | Shadows |
|---|---|---|---:|---|---|---:|---|
| StagingMoodRig/Key_SoftWarm | DirectionalLight3D | #FFF1DF | 1.600 | (0.0, 8.0, 0.0) | (-48.0, -32.0, 0.0) | infinite | on |
| StagingMoodRig/Fill_Cool | DirectionalLight3D | #D3E3F4 | 0.380 | (0.0, 8.0, 0.0) | (-24.0, 58.0, 0.0) | infinite | off |
| StagingMoodRig/Rim_Silver | DirectionalLight3D | #D9EFFF | 1.800 | (0.0, 8.0, 0.0) | (-32.0, 155.0, 0.0) | infinite | on |
| snake_full/CollarBounce_SnakeHeadRing_-1_0 | OmniLight3D | #7AFFBF | 0.035 | (1.738197, 0.523359, -0.753388) | (0.0, 0.0, 0.0) | 0.75 | off |
| snake_full/CollarBounce_SnakeHeadRing_1_0 | OmniLight3D | #7AFFBF | 0.035 | (1.738197, 0.523359, 0.186612) | (0.0, 0.0, 0.0) | 0.75 | off |
| snake_full/CollarBounce_SnakeSegRing_-1_0 | OmniLight3D | #7AFFBF | 0.035 | (-0.197261, 0.47, -0.897736) | (0.0, 0.0, 0.0) | 0.75 | off |
| snake_full/CollarBounce_SnakeSegRing_1_0 | OmniLight3D | #7AFFBF | 0.035 | (-0.197261, 0.47, 0.042264) | (0.0, 0.0, 0.0) | 0.75 | off |
| snake_full/CollarBounce_SnakeSegRing_001_-1_0 | OmniLight3D | #7AFFBF | 0.035 | (-1.412404, 0.47, -0.856824) | (0.0, 0.0, 0.0) | 0.75 | off |
| snake_full/CollarBounce_SnakeSegRing_001_1_0 | OmniLight3D | #7AFFBF | 0.035 | (-1.412404, 0.47, 0.083176) | (0.0, 0.0, 0.0) | 0.75 | off |
| snake_full/CollarBounce_SnakeSegRing_002_-1_0 | OmniLight3D | #7AFFBF | 0.035 | (-2.598782, 0.47, -0.915122) | (0.0, 0.0, 0.0) | 0.75 | off |
| snake_full/CollarBounce_SnakeSegRing_002_1_0 | OmniLight3D | #7AFFBF | 0.035 | (-2.598782, 0.47, 0.024878) | (0.0, 0.0, 0.0) | 0.75 | off |


### Staging isolated head — 5 lights

| Node path | Type | sRGB | Energy | World position | World XYZ angle | Range | Shadows |
|---|---|---|---:|---|---|---:|---|
| StagingMoodRig/Key_SoftWarm | DirectionalLight3D | #FFF1DF | 1.600 | (0.0, 8.0, 0.0) | (-48.0, -32.0, 0.0) | infinite | on |
| StagingMoodRig/Fill_Cool | DirectionalLight3D | #D3E3F4 | 0.380 | (0.0, 8.0, 0.0) | (-24.0, 58.0, 0.0) | infinite | off |
| StagingMoodRig/Rim_Silver | DirectionalLight3D | #D9EFFF | 1.800 | (0.0, 8.0, 0.0) | (-32.0, 155.0, 0.0) | infinite | on |
| snake_head/CollarBounce_SnakeHeadRing_-1_0 | OmniLight3D | #7AFFBF | 0.035 | (1.800155, 0.523237, -0.7493) | (-0.0, -7.999998, 3.999998) | 0.75 | off |
| snake_head/CollarBounce_SnakeHeadRing_1_0 | OmniLight3D | #7AFFBF | 0.035 | (1.669332, 0.523237, 0.181552) | (-0.0, -7.999998, 3.999998) | 0.75 | off |


### In-game wide and head — 25 lights

| Node path | Type | sRGB | Energy | World position | World XYZ angle | Range | Shadows |
|---|---|---|---:|---|---|---:|---|
| InGameMoodRig/Key_SoftWarm | DirectionalLight3D | #FFF1DF | 1.250 | (0.0, 8.0, 0.0) | (-48.0, -32.0, 0.0) | infinite | on |
| InGameMoodRig/Fill_Cool | DirectionalLight3D | #D3E3F4 | 0.320 | (0.0, 8.0, 0.0) | (-24.0, 58.0, 0.0) | infinite | off |
| InGameMoodRig/Rim_Silver | DirectionalLight3D | #D9EFFF | 1.450 | (0.0, 8.0, 0.0) | (-32.0, 155.0, 0.0) | infinite | on |
| Arena/@OmniLight3D@247 | OmniLight3D | #7FB2D9 | 1.200 | (0.0, 1.5, -12.5) | (0.0, 0.0, 0.0) | 15.0 | off |
| Arena/@OmniLight3D@248 | OmniLight3D | #2FB9D8 | 1.300 | (0.0, 5.2, -15.2) | (0.0, 0.0, 0.0) | 20.0 | off |
| Arena/@OmniLight3D@249 | OmniLight3D | #FFB37A | 1.100 | (11.0, 12.0, 11.0) | (0.0, 0.0, 0.0) | 42.0 | off |
| Arena/@OmniLight3D@251 | OmniLight3D | #FF9A3C | 1.400 | (-13.0, 5.6, -15.85) | (0.0, 0.0, 0.0) | 9.0 | off |
| Arena/@OmniLight3D@253 | OmniLight3D | #FF9A3C | 1.400 | (0.0, 5.6, -15.85) | (0.0, 0.0, 0.0) | 9.0 | off |
| Arena/@OmniLight3D@255 | OmniLight3D | #FF9A3C | 1.400 | (13.0, 5.6, -15.85) | (0.0, 0.0, 0.0) | 9.0 | off |
| Arena/@OmniLight3D@256 | OmniLight3D | #33506B | 0.350 | (-13.0, 10.5, 0.0) | (0.0, 0.0, 0.0) | 26.0 | off |
| Arena/@OmniLight3D@258 | OmniLight3D | #FF9A3C | 1.000 | (-8.0, 4.2, -15.4) | (0.0, 0.0, 0.0) | 13.0 | off |
| Arena/@OmniLight3D@260 | OmniLight3D | #FF9A3C | 1.000 | (8.0, 4.2, -15.4) | (0.0, 0.0, 0.0) | 13.0 | off |
| Arena/@OmniLight3D@380 | OmniLight3D | #FF2A1E | 0.800 | (-10.35, 1.4, -10.35) | (0.0, 0.0, 0.0) | 2.5 | off |
| Arena/@OmniLight3D@382 | OmniLight3D | #FF2A1E | 0.800 | (-10.35, 1.4, 10.35) | (0.0, 0.0, 0.0) | 2.5 | off |
| Arena/@OmniLight3D@384 | OmniLight3D | #FF2A1E | 0.800 | (10.35, 1.4, -10.35) | (0.0, 0.0, 0.0) | 2.5 | off |
| Arena/@OmniLight3D@386 | OmniLight3D | #FF2A1E | 0.800 | (10.35, 1.4, 10.35) | (0.0, 0.0, 0.0) | 2.5 | off |
| Apple/@OmniLight3D@433 | OmniLight3D | #FFB300 | 2.000 | (0.0, 0.62, 7.2) | (0.0, 0.0, 0.0) | 3.5 | off |
| ProductionSnake_LightingEvidence/CollarBounce_SnakeHeadRing_-1_0 | OmniLight3D | #7AFFBF | 0.045 | (3.391045, 0.523359, 0.386545) | (0.0, -20.0, 0.0) | 0.75 | off |
| ProductionSnake_LightingEvidence/CollarBounce_SnakeHeadRing_1_0 | OmniLight3D | #7AFFBF | 0.045 | (3.069546, 0.523359, 1.269856) | (0.0, -20.0, 0.0) | 0.75 | off |
| ProductionSnake_LightingEvidence/CollarBounce_SnakeSegRing_-1_0 | OmniLight3D | #7AFFBF | 0.045 | (1.621679, 0.47, -0.411063) | (0.0, -20.0, 0.0) | 0.75 | off |
| ProductionSnake_LightingEvidence/CollarBounce_SnakeSegRing_1_0 | OmniLight3D | #7AFFBF | 0.045 | (1.30018, 0.47, 0.472248) | (0.0, -20.0, 0.0) | 0.75 | off |
| ProductionSnake_LightingEvidence/CollarBounce_SnakeSegRing_001_-1_0 | OmniLight3D | #7AFFBF | 0.045 | (0.465826, 0.47, -0.788222) | (0.0, -20.0, 0.0) | 0.75 | off |
| ProductionSnake_LightingEvidence/CollarBounce_SnakeSegRing_001_1_0 | OmniLight3D | #7AFFBF | 0.045 | (0.144327, 0.47, 0.095089) | (0.0, -20.0, 0.0) | 0.75 | off |
| ProductionSnake_LightingEvidence/CollarBounce_SnakeSegRing_002_-1_0 | OmniLight3D | #7AFFBF | 0.045 | (-0.629066, 0.47, -1.248769) | (0.0, -20.0, 0.0) | 0.75 | off |
| ProductionSnake_LightingEvidence/CollarBounce_SnakeSegRing_002_1_0 | OmniLight3D | #7AFFBF | 0.045 | (-0.950565, 0.47, -0.365458) | (0.0, -20.0, 0.0) | 0.75 | off |

For all retained room/apple omnis: attenuation 1, size 0, specular 0.5, shadows off. For the collar omnis: attenuation 1.5, size 0.16, specular 0.25, shadows off. Directional softness and bias settings are specified above. These tables are generated from the final running scenes, not estimated from the source.

## Verification record

- Input ZIP SHA-256 matched `0e9f1b16d91b8e087b992a3ae1722f7a7b8702271c132defeda55158c76dfbe4`; all 46 input manifest entries passed before edits.
- All 17 original model/texture source files in `UNCHANGED-ASSETS.sha256` still match their input hashes.
- Four 1920×1080 PNGs rendered successfully and were visually inspected.
- `evidence/capture.log` includes runtime texture assertions and capture return codes; `evidence/import.log` records the completed final editor pass.
- `SHA256SUMS` inventories the delivered files (excluding itself).

- Clean overlay check: copied only delivered rig files plus the original GLBs into a fresh project with no `.godot/`; editor import and headless playable-scene boot both exited 0 with no errors. Logs are in `evidence/clean-overlay-*.log`.
