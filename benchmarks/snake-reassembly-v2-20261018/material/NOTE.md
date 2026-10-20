# NOTE — material fix M4, delivered 2026-10-20

Starting commit `66f5249`, branch `forge-snake-reassembly-v2-20261018`. Geometry frozen. Historical working notes follow; the final render-only scorecard and NOT READY delivery call are at the end. Optical UV refinement is recorded below.

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


## Post-checkpoint refinement log

- Remote WIP `6f6de42` pushed before detail work. Native Git encountered the host certificate-proxy path; gateway Git push succeeded without changing TLS verification.
- M4b previews showed satin metal but overly uniform brushing. M4c added fine recessed weave and tested an edge-normal-difference mask; full-resolution live-shader head/segment checks were explicitly diagnostic, not delivered baked captures.
- Additional online source read: Mark B. Tomlinson / BlenderNation, [How to set up an Edge Wear node](https://www.blendernation.com/2023/08/02/how-to-set-up-a-edge-wear-node-in-blender/), 2023-08-02. Article describes Cycles bevel-sample edge-mask group; [Blender Artists discussion](https://blenderartists.org/t/why-do-i-get-edge-masks-by-dot-producting-bevel-nodes-and-geometry-normal/1494877) search excerpt explains bevel/geometry-normal dot product. Applied as a shader-only edge probe, not a bevel modifier. Article illustration fetch was blocked; not claimed viewed.
- Generic curvature alone did not produce sufficient head edge specificity. Added a material-only seam-distance attribute fitted to the existing P8 modeled cuts recorded in `head_fix.py`. It confines broken polish/oxide to the shoulders of those cuts; it does not generate new boundaries.
- Added high-frequency interrupted hairline scratches in color/roughness, not deep relief; shallow pitting remains separate. Removed broad brushed stain dominance.
- Eye: P8 source lathe confirms lit cover radius is 0.60 of full assembly radius. Radial target now applies only within that cover; outer lip/groove/bezel remain non-emissive metal. Lens-only planar UV allocation uses the already reserved eye boxes to obtain real disc texel area. All other UVs remain untouched.

## Recovery at 21:04 CDT

The agent turn was interrupted around 18:30 by Astra auth-profile unavailability; no Blender failure is present in the recovered logs. The 4096/2048 bake completed and all six geometry-distance masks finished rasterizing after the last message. The masks are not yet incorporated in that baked blend. Recovery checkpoint preserves these outputs and the pending source changes before further building. Revised delivery estimate on resumption: 45–60 minutes.

### Final approach correction

The interrupted Voronoi-edge hairline experiment (M4e) was **rejected visually** because connected lines still looked like cracks, even in color alone. Final M4 uses disconnected anisotropic noise marks instead. The Stack Exchange scratch-removal approach informed the experiment, but its cell-edge pattern is not in the final material.

Geometry-fitted edge masks rasterize the unchanged UV triangles and measure distance to actual boundary/convex and concave edges (28° normal threshold). R controls broken edge wear; G augments recessed grime. They do not alter normals, vertices, topology, or instance transforms. Shader bump remains shallow pitting, separate from edge masks. The final bake is 4096 head, 2048 body/tail, 256 glow inserts, with packed ORM and emission maps.

## M4 finish / first-panel handoff — 2026-10-20

As-is checkpoint **9ecb2df25fc064652ef56a5f5a9345e164a631ec**, pushed before finish work. The research and iteration history above is preserved from the recovered working NOTE and corroborated against `source/material_setup_m4.py`, bake/render logs and the saved mask/map products. This finish session performed no new online research and does not claim to have re-read those external articles. Final implementation uses geometry-distance edge/recess masks, interrupted directional noise marks, sparse oxide, shallow pitting and separately allocated optical UVs; the rejected Voronoi crack experiment is not the final technique.

### Inventory and technical result

All five requested M4 production PNGs existed, decoded successfully at 1920×1080, and were personally viewed against pack `REFERENCE.png`: full-body, head-closeup, seg-detail, tail-detail and tail_top-detail. **Zero rerenders; zero rebakes; no geometry or material edits in this finish session.** All 32 texture files decode and match every SHA-256 and dimension in `m4-map-manifest.json`. `m4-capture-checks.json` records final capture hashes and sampled backdrop corners. Comparison sheets are unwarped side-by-sides, not solved reference-camera overlays.

Recovered `audit-material.json`: geometry fingerprints and instance transforms unchanged; GLB node counts match; AO and metallic/roughness share packed image sources. Budgets: head **13,968**, module+insert **1,431**, tail **2,970**, assembly **57,006**. Engine import reports 61 meshes / 57,006 triangles / PASS. GLB SHA-256: `d2a74ef1f2451a9e249373429c58a53358ae9a27c1c79457ea17606dfca0914b`.

Production log reaches `RENDER_COMPLETE`; saved stage record specifies Cycles-class final GPU rendering, 256 samples, adaptive 0.01, OIDN, backdrop #C1C1BF, AO multiplied into review albedo, glare threshold 1.0 / strength 0.25 / size 0.125. Technical PASS is separate from visual acceptance.

### Render-only self-scorecard

Scores are **MATCH / QUALITY**, out of 10, assigned anew from the five viewed M4 renders and the reference—not inherited from M3 scores, geometry measurements, budgets or shader intent. Owner acceptance of P8d clay remains in force; these scores describe its current material-render read and do not authorize geometry changes. Reference-camera angles are not exactly solved; hidden surfaces are unreviewed. H7 is judged against the image's vertical slats, per the recorded spec correction.

#### 1. Frozen per-feature shape (27)

| ID | Feature | MATCH | QUALITY | Visible evidence |
|---|---|---:|---:|---|
| H1 | Skull massing | 6 | 6 | Elongated taper present; crown/cheek softer than reference. |
| H2 | Skull plate breakup | 5 | 5 | Black incisions dominate instead of layered plate edges. |
| H3 | Jaw seam and lower jaw | 5.5 | 5.5 | Closed seam readable; two-tier jaw weak. |
| H4 | Nostril/side slot | 5.5 | 5 | Slot present, surround angular and underdeveloped. |
| H5 | Crest fins ×3 | 6 | 5.5 | Three visible in head view; thick, upright blade read. |
| H6 | Eye lens assembly | 7 | 7 | White core/mint/teal concentric target; lacks reference iris intricacy. |
| H7 | Cheek vent box | 7 | 6.5 | Raised rounded housing and vertical slats; dark weave dominates. |
| H8 | Head piston rod | 6.5 | 6 | Visible rods; bulky transition to collar. |
| H9 | Inset panels | 6 | 5.5 | Dark windows visible, less fitted layered hardware. |
| H10 | Head–neck collar | 5 | 4.5 | Broad irregular cuff rather than stacked machined plates. |
| H11 | Brow-ridge plate | 5.5 | 5 | Socket ridge visible, weak overhanging plate separation. |
| H12 | Snout-ridge complex | 5.5 | 5 | Taper present; ridges merge into soft shell. |
| B1 | Drum massing | 7 | 6.5 | Repeated cylinders clear, angular plate wrap. |
| B2 | Stepped shield plate | 6 | 5.5 | Step visible but simplified, raised tabs look detached. |
| B3 | Framed grilles | 6 | 5.5 | Three openings read; weave and framing inconsistent. |
| B4 | Waist band/twin pistons | 6.5 | 6 | Mechanical band readable; coarse fittings. |
| B5 | Centre bracket blocks | 6 | 5.5 | Blocks visible beside centre grille, low separation. |
| B6 | Lower plate | 6.5 | 6 | Recess present; broad uniform plate. |
| B7 | Fasteners | 6.5 | 6 | Visible corner bolts, faceted and plain. |
| B8 | Joint housing ring | 6 | 5.5 | Dark ring present; exposed gaps weaken recessed housing. |
| B9 | Segmented emissive bars | 6 | 5.5 | Segmented around joints, but broad bright tiles project outward. |
| B10 | Neck read | 5.5 | 5 | Broad inner flats and exposed joints unlike dense overlapping reference. |
| T1 | Taper segments | 6.5 | 5.5 | Diameter steps and port visible; protruding hardware. |
| T2 | Torpedo terminal | 5.5 | 5 | Tapered nose exists; shell lumpy, plate language sparse. |
| T3 | Dorsal fin | 5.5 | 5 | Swept fin visible, rough edge and pattern spill. |
| T4 | Lateral/ventral pair | 5.5 | 5 | Fins visible in both tail views; irregular attachment. |
| T5 | Tail grille vents | 6 | 4.5 | Large/small vents readable; weave spills beyond openings. |

#### Categories 2–9 and overall

Each row is a holistic render judgment, not a technical metric or blind-panel median.

| Category | MATCH | QUALITY | Render evidence |
|---|---:|---:|---|
| 2. Silhouette | 6.5 | 6 | Raised head, coil and curled taper recognizable; neck angular, head tipped more steeply. |
| 3. Massing/composition | 6 | 6 | Coil rhythm works; open coil, narrow neck and broad collar diverge from reference. |
| 4. Modeled detail | 5.5 | 5 | Hardware present; coarse fasteners, soft head/tail surfaces and stray tail-top bar remain conspicuous. |
| 5. Color | 7 | 7 | Coherent warm-grey metal and mint lights; too little local warm/cool plate differentiation. |
| 6. Bump/normal mapping | 6.5 | 6 | Fine pitting reads on segment highlights; head/tail still look hammered rather than finely machined. |
| 7. Texture maps | 6 | 5.5 | Sparse streaks and wear visible; repeated distribution, black grille-pattern spill on tail shell/fins. |
| 8. Materials | 6.5 | 6.5 | Satin-metal response more plausible; uniform plate treatment and pale luminous joint blocks remain unlike reference. |
| 9. Lighting/effects | 7 | 7 | Shaped highlights, soft contact shadow and restrained eye glow; dark hardware loses separation, joint tiles too flat/bright. |
| Overall (supplemental) | 6 | 5.5 | Recognizable mechanical snake; not reference-quality assembly/material finish. |

### Call and panel boundary

**NOT READY for acceptance.** Technical checks pass, but visual fidelity remains below the 7.5 gate. Strongest material blockers are tail grille-pattern contamination, overly uniform weathering/plate response, and broad luminous joint tiles. The tail-top stray bar and coarse head/collar/tail form read are explicitly recorded, not silently repaired: geometry is frozen.

This is the M4 delivery for the **first panel review**, not a panel PASS. No panel result is claimed. Stop at this handoff; no additional fix cycle, rebake or geometry work was undertaken. The five canonical captures, GLB, maps and this note are the review package.

### Finish verification addendum

`m4-verification.json` and `verify-m4-finish.log` record **M4_ACTIVE_STAGE_UV_AO_PASS** from reopening both saved Blender stages: exact active-stage equality, Cycles GPU/256/OIDN, frozen camera records, AO graph connectivity and unchanged non-optical UVs. Blender exited successfully, with a tiny shutdown memory-allocation warning after the PASS.

PNG background sampling: full/head/segment are [193,193,191], tail is [192,192,190]. Tail-top's upper-left contains geometry, so the checker now records an explicit unobstructed patch at (900,260), which is [153,153,151] **under the broad contact-shadow field**, not a clean backdrop match. Thus four clear corners match the stage within one level; the tail-top image does not establish a clean background-color match. This is a staging limitation, not PNG corruption, and is retained under the owner's missing/corrupt-only rerender instruction. Saved compositor background and paired staging equality still pass. No image pixels were edited.
