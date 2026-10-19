# NOTE — material fix M4, 2026-10-19

Starting commit `66f5249`, branch `forge-snake-reassembly-v2-20261018`. Geometry and UV layout frozen. Work in progress; no acceptance claim.

## Reference vision check

Opened pack REFERENCE.png and M3 full/head captures in-session. Reference wear is narrow, directional and edge/fastener driven, with recessed grime, small warm brown-olive plate shifts and fine machining/pitting. M3 substitutes arbitrary polygonal camouflage and large copper patches. Those masks are removed, not intensified.

## Online research performed before shader construction

- Blender Manual, [Geometry / Pointiness](https://docs.blender.org/manual/en/latest/render/shader_nodes/input/geometry.html), read 2026-10-19: Pointiness is per-vertex approximate curvature; convex areas lighter, concave darker. Random Per Island is per connected component. Applied: convex wear plus fine breakup; only subtle connected-component tint. No Voronoi fake plate boundaries.
- Jennifer S. Abbott / Olde Tinkerer Studio, [Making a procedural rusted metal material, Blender 4.0](https://oldetinkererstudio.com/making-a-procedural-rusted-metal-material-blender-4-0/), read full article 2026-10-19: object-coordinate noise, ColorRamp masks, separate broad and micro bump layers, rust color controls. Applied selectively: masked oxide and independently scaled shallow micro-bump. Did NOT copy broad rust coverage or low-frequency bump; that would repeat M3.
- Blender Stack Exchange, [How can you make scratched metal procedurally?](https://blender.stackexchange.com/questions/207259/how-can-you-make-a-scratched-metal-procedurally), search excerpt read; full fetch blocked 403. Excerpt explains separate scratch-width and removal thresholds. Applied principle: thin thresholded marks interrupted by a second mask, with directional coordinate scaling and separate roughness response.
- [Noise Texture manual](https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/noise.html), search excerpt: scale controls base octave and detail adds octaves. Applied: separate high-frequency pitting, medium-scale breakup, anisotropically stretched scuffs and oxide streaks; no shared low-frequency camouflage field.
- StraySpark edge-wear tutorial was searched but its fetch exposed only site navigation; it is NOT claimed as a read technique source. ArtStation mirror was blocked 403.

## Approach

M4 uses the existing M3 material assignments and UVs, replaces shader graphs, retains exact source geometry hashes. Neutral warm gunmetal is shared across head/body; connected-component tint changes are small. AO targets recesses; curvature gates broken edge polish. Rust is subdued brown, narrow and constrained by edges/recesses. Pitting uses shallow high-frequency bump; no fabricated crack/seam pattern. Lens radius is evaluated per shading point in its fitted plane rather than interpolated vertex radius, with 28%-diameter white core, mint annulus, teal rim.

## Early checkpoint

First fresh bake completed (32 maps; `bake-m4.log`), followed by exactly one full-body production render `captures/m4-wip-full-body.png` at frozen M3 staging. Opened and judged in-session against REFERENCE.png and M3 full body before any detail refinement.

**NOT READY checkpoint:** M3 camouflage and broad copper fields are removed; head/body hue is more coherent. However the metal is too clean and reflective, near chrome on the broad highlights. Fine wear remains too weak at this distance; the optical target is over-bright and poorly sampled. Next approach: keep the topology-driven masks but increase satin roughness, make interrupted directional scuff/roughness variation readable, and improve actual lens texel allocation. Do not restore broad patch masks.

Technical audit PASS: geometry fingerprints and instance transforms exactly match P8 source, GLB node counts match, packed ORM AO/MR share image sources. Counts remain 13,968 / 1,431 / 2,970 / 57,006. This is not acceptance.

Reference clear background sampled at three regions: median #C2C3C0, close to the historical #C1C1BF stage. The existing #C1C1BF is retained unchanged for exact baseline/after staging, not silently re-lit or re-colored.
