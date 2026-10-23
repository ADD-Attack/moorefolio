# STATUS — EDEN-3D-01 MATERIAL PHASE — WIP-CHECKPOINT 1 (19:35 CDT)

**Base:** the 2c25df3 clay; blend hash verified identical. **Geometry FROZEN:** every bake asserts that world vertex positions are unchanged (GEOMETRY_FROZEN True, 41,694 tris). UVs were re-unwrapped into one shared 2048 atlas across the 9 nodes (UV-only).

**Method (mat.py):** a procedural, geometry-driven shader baked to maps.
- Geometry AO → dark seams/grooves, so the relief reads THROUGH the finish (the Cat 4 watch item).
- World-normal Z → master highlight band on tops and red-orange underside.
- Two-octave noise → mottling.
- A geometric mouth-interior mask (inward-facing cavity + throat cup) → maroon-to-black interior, with a faint deep-throat ember emission.
- Bakes: basecolor, ORM (R=AO, G=rough, B=metal 0), emission. Export: image Principled + glTF occlusion.

**Review captures** (wip1/, 64-spp preview, labeled preview): same staging as the clay gate; ORM R multiplied into albedo (review-only); tight FOG_GLOW glare set via sockets.

## PUSHBACK on the dispatch palette (Decision 29; feedback resolves against the image, Decision 27.2)
The dispatch asks for near-black dorsal/flank plates, a pale cream belly, plate-dark tail rings and a glowing mouth. **Neither ground-truth image shows that:**
- **2D master (alien_b_full.png):** sampled plates (251,119,21) are the same ember orange as the body; highlights (253,181,79); underside red-orange (202,60,40); near-black only in the seam outlines and the mouth cavity; the glow is on the spit projectiles, not the mouth.
- **3D pack reference:** all ember orange; mouth interior (71,11,4).

I am building to the images: all-orange body, dark seams, red-orange underside, dark maroon mouth, plus a faint deep-throat ember. That ember is a mild interpretation of "spitter glow" and is easy to raise or remove. **If the owner really wants the dispatch palette, say so** and I will switch; it is a shader-parameter change, not geometry.

**Next:** reduce specular sheen (the body reads slightly salmon); bake at 2048 / higher samples; production 256-spp captures (full, mouth, tail, side-by-side); verify the ORM in the GLB; full 1–9 self-scorecard; NOTE. Delivery is well ahead of Fri 12:00.
