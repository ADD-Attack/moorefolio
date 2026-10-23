# NOTE — EDEN-3D-01 MATERIAL PHASE delivery — Forge, 2026-10-22

**Base:** the operative clay 2c25df3 (blend hash verified). **Geometry FROZEN:** every bake asserts that world vertex positions are unchanged (`GEOMETRY_FROZEN True`), 41,694 tris, 9 nodes, same hierarchy. The only mesh-data change is UVs: one shared 2048 atlas across the 9 nodes, replacing the provisional per-node unwraps.

## Deliverables
- `aliens_b.glb`: Principled material `aliens_b`.
  - Base colour from basecolor.png.
  - metallicRoughness and occlusion from the **same** `orm.png` (R=AO, G=roughness, B=metal 0); verified in the GLB JSON.
  - Emissive from emission.png ×0.6.
  - +Y up; tangents; Draco OFF.
  - Uses the KHR_materials_specular extension (specular level 0.3, to kill the salmon sheen). A Godot importer that ignores it falls back to default specular and reads slightly glossier.
- `aliens_b_mat.blend`, `textures/` (2048² PNG), `mat.py` (bake), `stage_mat.py` (review staging).
- `captures/`: mat-full, mat-mouth, mat-tail (256 spp Cycles, the clay-gate staging/camera/lights/backdrop) and mat-compare-master-ref-render (master | pack ref | render).
  - Review-only: ORM R multiplied into albedo so AO renders.
  - FOG_GLOW glare set via sockets: Threshold 0.8, Strength 0.25, Size 0.125.
  - The backdrop corner reads 229 vs 228 (glare lifts it by 1).

## Method
A procedural shader driven by the real geometry, baked to maps:
- **Seams and grooves:** geometry AO (24 samples, 3.5 cm) mixes toward dark brown (62,16,6). The relief reads **through** the finish and is never painted over (Cat 4 watch item).
- **Value structure from the master:** world-normal Z gives the warm highlight band on tops (250,150,40) and the red-orange underside (190,52,28 from the master's 202,60,40). Two-octave noise gives a mottled red-orange variation.
- **Mouth interior:** a geometric mask (inward-facing cavity surfaces + the throat cup) gives maroon at the rim → near-black deep (3D ref 71,11,4; master black), plus a faint ember emission rising with depth (depth⁴), deep throat only.
- **Roughness:** 0.55–0.68 satin, noise-varied. Metal 0.

## Palette ruling (pushback, Decision 29 / 27.2)
The dispatch's near-black plates, cream belly, plate-dark tail rings and glowing mouth appear in **neither** the 2D master nor the pack reference. Both show an all-ember-orange creature with near-black seam lines and a dark mouth; the glow belongs to the spit projectiles. I built to the images. Switching to the dispatch palette is a shader-parameter change if the owner wants it.

## Honest gaps
- **Flatter shading than the master:** the master's strong two-tone cel structure (bright yellow highlight blobs, deep red lower half) reads softer here. A PBR material under the lighting carries less of that than the hand-shaded sprite.
- **No normal map:** relief comes only from the modeled geometry + baked AO. Fine micro-detail (pores, wear) is absent; the reference is smooth clay too.
- **Tiny dark specks** at a few geometric pits (AO); faint UV-seam/joint lines at the tail segment joints.
- **Seam outline width:** the master's black outlines are bolder than the AO darkening reads at distance.
- **Many tiny UV islands** in the atlas (from the remeshed topology); texel use is ~60%.

## Self-scorecard (render review: mat-full / mouth / tail + the 3-way compare; calibrated down per my material history)
| # | Category | MATCH | QUALITY | Evidence |
|---|---|---|---|---|
| 1A | Mouth unit | 6.5 | 6.0 | Dark maroon cavity with lip ring and collar reads like the master's open maw; the ember is subtle. |
| 1B | Body features | 6.5 | 6.0 | Plates, flank seams and tail rings now carry dark seam lines like the master; geometry unchanged. |
| 2 | Silhouette | 5.5 | 6.0 | Unchanged geometry (clay 5.8/6.5). |
| 3 | Massing | 6.0 | 6.5 | Unchanged (clay 6.3/6.7). |
| 4 | Modeled detail | 5.0 | 5.0 | Grooves read **more** strongly than in clay, through the AO seam darkening; specks remain. |
| 5 | Color | 6.0 | 5.5 | The ember hue matches the samples; the red-orange underside is present; less contrasty than the master. |
| 6 | Bump/normal | 4.5 | 4.5 | No normal map; geometry + AO only. |
| 7 | Texture maps | 5.0 | 5.0 | Clean 2K bakes, ORM packed correctly; mottling generic; tiny-island atlas. |
| 8 | Materials | 5.0 | 5.0 | Satin clay-like skin fits the 3D ref; less vivid than the sprite. |
| 9 | Lighting/effects | 5.0 | 5.0 | Faint deep-throat ember with tight glare; no projectile FX (out of scope). |
| — | Overall | 5.5 | 5.5 | Reads as the right creature in the right colours; finish is solid but not yet rich. |
