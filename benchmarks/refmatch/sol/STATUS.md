# WIP checkpoint — mechanical snake reference match

**2026-10-17. PAUSED at producer request. Awaiting RESUME.**
This is an implementation checkpoint, not final delivery or acceptance.

## DONE

- Verified input ZIP SHA-256 exactly matches `61625934b41126627cd6e1422bf1f491ac19ed250adc785f6e65d59f7ba82e49`; every packaged manifest entry passed.
- Read SOL-BRIEF.md, the applicable dossier modeling/export/texturing/animation guidance, and REVIEW-STAGING.md. Studied the supplied reference and repeatedly reviewed own renders.
- Built new parametric armored head, 28 rigid body sections, and tapered armored/finned tail in a raised S/coil pose.
- Modeled one camera eye: machined outer housing, concentric recessed barrel, individual aperture blades, internal illuminated iris/core, and separate curved transparent optical cover.
- Added overlapping, thick armor plates, deep seams, fasteners, grilles, segmented cyan emissive joint bands in dark housings, and three thin socket-mounted metal crest fins with rails and ribs.
- Generated worn-metal head/body trim maps, grille maps, normal maps and ORM maps. Varied shared body atlas sampling per section.
- Performed selected-to-active head normal baking from a beveled/micro-displaced high source; consolidated head color/normal/ORM/emission into a single final UV0 atlas. Its ORM includes a real Cycles AO bake. Head export is one opaque PBR material plus the optical cover.
- Exported all three GLBs with +Y up, applied modifiers, normals and tangents, Draco disabled. All game materials are Principled-derived.
- Structural GLB checks pass: triangle budgets, tangents on every primitive, unit positive transforms, packed AO/MR texture references, rigid segment design.
- Godot 4.7.2 editor import completed without errors. All three scenes loaded, all materials resolved, zero missing materials; tangent surfaces confirmed. See `godot-import.log`, `godot-check.log`, and `validation.json`.
- Runtime curve driver supplied. Headless Godot tests pass: 28 section pivots at 0.92 m spacing on a straight path, and 120 deterministic raised-path poses with finite, right-handed transforms. See `godot-curve.log`.
- Current `.blend`, scripts, GLBs, texture PNGs, preview captures and neutral studio staging captures are included.

## CURRENT TRIANGLE COUNTS (LOD0, exported GLBs)

| Asset | Triangles | Limit |
|---|---:|---:|
| snake_head.glb | 17,370 | 10,000–18,000 |
| snake_segment.glb | 1,484 | Full assembly budget governs |
| snake_full.glb | 59,886 | ≤60,000 |

Full scene: 30 rigid mesh nodes (head + 28 body sections + tail). No skeleton or skin is required. Section origins are forward joint pivots; geometry trails toward local -Z in glTF. Game forward is +Z, up is +Y. `animate_curve.gd` samples a tail-to-head Path3D at 0.92 m intervals and writes each mesh's global transform; the head follows the first joint and the tail follows the last.

## IN PROGRESS AT PAUSE

- Final visual review of the newly consolidated head atlas and latest staging captures. The final render process was already running when the checkpoint arrived; it finished during checkpoint packaging. Its output is included but has not yet been visually reviewed.
- Close comparison of final material wear, lens readability, and framing against REFERENCE.png.

## REMAINS (only after RESUME)

- Review the newest captures; correct any visually evidenced atlas, material, or framing defects.
- Finalize NOTE.md with complete texture inventory, reproduction steps, exact animation scheme, validation results and honest remaining reference-match gaps.
- Final delivery commit/push following that review. No new build work will begin until RESUME.

## KNOWN SELF-ASSESSMENT / LIMITS

- Armor layout is more regular and simplified than the reference; connector/piston and fine hardware density is lower.
- Wear is procedurally authored, not an exact hand-painted reproduction. Current metal can read brighter/more brushed than the darker, dirtier reference.
- Head/fin proportions and coil layout echo, but do not exactly reproduce, the reference.
- Body/tail AO is authored in trim ORM maps rather than a full assembled contact bake. Head AO is baked.
- Runtime pose tests are headless transform checks, not a finished gameplay/LOD/performance playtest. Arbitrary sharp 90-degree body turns have not been visually validated.
- Staging images are work-in-progress review evidence. Only the final post-RESUME review can establish which captures should be treated as final.
