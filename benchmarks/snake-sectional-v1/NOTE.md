# Sectional snake v1 — implementation handoff

Order: **op-assembly-sectional-v1-20261017**. Branch: `assembly-sectional-v1-20261017`.
Quality-gate review is pending; these are implementation/evidence results, not acceptance.

## Delivered build

- Supplied skull section, one source-derived hero body module repeated as **28 rigid nodes**, and the terminal curved tail section. No armature, skin, or merged assembly.
- Raised S neck, ground coil and right-hand tail curl, retained as a master curve in the `.blend` and as `path.json` for Godot.
- **29 joints** with separate dark housing meshes and twelve separate geometric emissive teal bar sectors per insert. Joint transforms are sampled at the curve boundaries, independently of section-center frames. Dark internal couplers close the armor gaps.
- **One** modeled lens on the supplied skull's front/review-facing circular formation, following the producer correction. Six concentric housings/iris rings, eight aperture vanes, emissive center, and a curved translucent optical cover. Two outer rims have modeled machined bevels. No second lens assembly.
- Source-baked tangent normals, procedural gunmetal color/roughness variation and fine scratches, recess grime through AO/roughness/metallic response, and modeled hex fasteners and vent grilles. Principled BSDF materials only. Teal emitters retain their emission strength.

## Exact delivered GLB triangle counts

Counts traverse mesh-bearing nodes, **including every repeated instance**. See `glb-validation.json` and `counts.json`.

| Part | Triangles | Budget |
| --- | ---: | ---: |
| Skull alone | 12,000 | — |
| Complete standalone head, including one modeled lens | **15,104** | 10,000–18,000 |
| Hero segment including coupler, fasteners and vent | 1,132 | — |
| One housing + segmented emitter insert | 336 | — |
| Segment including its joint | **1,468** | ≤1,600 |
| Tail geometry | 2,400 | — |
| Tail including terminal joint | **2,736** | ≤3,000 |
| Full assembly: 15,104 + 28×1,468 + 2,736 | **58,944** | 30,000–60,000 |

The 28 section nodes reference **one shared mesh** in the exported GLB. All required primitives contain POSITION, NORMAL, TEXCOORD_0 and TANGENT. Textures are embedded; AO and metallic/roughness reference the same ORM image (R=AO, G=roughness, B=metallic). glTF +Y up; positive/unit-scale rigid transforms; Draco off; no skins.

## Base extraction and reconstruction

The provided base files were copied, not modified. The monolith was not used, and no other entrant's branch, workspace or delivery was fetched/read.

- **Head:** keep source Blender-space `x < -0.17`, `z > 0.12`; discard the long generated neck behind the skull. Transform rear attachment to local origin, preserve the three dorsal fins and circular eye formation. Smooth octree reconstruction and budgeted reduction retain the skull; high-source normal/AO projection preserves seams.
- **Segment:** keep near-side clean section `y < -0.18`, `x < 0.17`, `z > -0.53`; discard the far melted form and right neighbor appendage. The source has non-manifold overlapping topology. Direct collapse and the first voxel remesh were unusable, as recorded in the WIP. Final module uses a **closed source-sampled retopology shell**: 13 longitudinal rings × 36 angular samples, radial raycasts against the extracted source, bounded radii 0.40–0.57 to reject reconstruction spikes, closed end caps, and source-projected detail. This is an explicit rebuild from the extracted form, not an undisclosed replacement asset.
- **Tail:** retain `x > 0.28`, `y < 0.30`, `z > -0.245`: terminal approximately two tapered sections plus the finned tip. Discard the earlier run and flat reconstructed floor sheet. Reconstruct/reduce to 2,400 tris and project source details.
- Curve pitch is approximately **0.9985144** Blender units. Local section-forward is +X; Blender +Z up becomes Godot +Y up. Skull points toward local −X from the rear attachment.

Source SHA-256:

```
head     5e953eef5d4f76a4ede477132c288911819fba3219545bf773edb06d4d6a2d68
segment  591357453a5143bff8b80a2f12ae7c04c393e308439fcf0c3fd07e9783408015
tail     812328ba0a7d6ff700c960fc474d66b8902128a0c0d0b6deb5fce0c58f3d5f0c
package  1ddf88e960eb0a4549866928501f7b3d826055f8c1d4b16ff31cc14ef4ccf900
```

## Godot evidence

**PASS:** fresh-cache Godot 4.7.2 editor import completed with no errors; both GLBs instantiate; **120/120 poses pass, zero failures, 58,944 triangles**. Native Compatibility rendering used an NVIDIA GeForce RTX 3070 Ti; both saved viewport images are exactly **1920×1080** and were inspected. The saved `.blend` was reopened and its 28 shared-mesh sections, single lens, master curve, and nine packed material images were independently verified. Results are recorded with the delivery logs and JSON reports. The supplied `godot/driver.gd` constructs a real Path3D/Curve3D and reposes all rigid sections by arc length, with right-handed orthonormal frames. `set_pose(phase)` changes the path, not mesh vertices. Head and tail follow the endpoint frames; each joint is reset to its boundary frame.

The self-test checks the **exported rest pose before the driver can repair it**, one complete lens assembly, 28 sections, tangents/material/PBR texture slots, total triangle budget, 120 deformed curve poses, finite unit-determinant transforms, section and joint arc positions, and independent straight-path spacing. Both GLBs are instantiated.

## Captures and reproduction

- `captures/wip-full-body.png`, `captures/wip-head.png`: **unchanged** first-pose evidence from WIP commit `793ec5e`, including the fragmentation/two-eye defect. These are NOT final review images.
- `captures/full-body.png`, `captures/head-closeup.png`: final Blender Cycles neutral-studio views, **1920×1080**, featureless gray world, no floor/grid/environment/HUD. The head view isolates the head assembly. Geometry-based projected framing.
- `captures/godot-full-body.png`, `captures/godot-head-closeup.png`: native Godot import review, plain gray visible background with a reflection-only sky, neutral directional lighting, fixed 1920×1080 viewport. Capture-only fixture is separate from the path driver. Camera/settings are logged by `godot/capture.gd`.
- `.blend` packs its images; exported GLBs embed their textures. Separate source-generated texture maps are also supplied in `textures/`.

Blender 4.5.14 and Godot 4.7.2 native Windows executables were used. Windows C: filled during final evidence preparation, truncating a temporary fresh-check copy and preventing one save. This ticket's working directory was relocated intact to **D:/OpenClaw/assembly-sol-op-20261017**, which has ample space; final evidence must come from the successful rerun, not that failed temporary copy.

Build with the three supplied GLBs in the work directory (`hunyuan-head.glb`, `hunyuan-segment2.glb`, `hunyuan-tail.glb`). Set `ASSEMBLY_WORKDIR` and optionally `ASSEMBLY_OUTPUT` to override the default work/output paths, then run Blender headlessly with `build.py`, followed by `assemble.py`. This writes `sections.blend`, final exports, textures, path and captures. Run `validate_glb.py` with `ASSEMBLY_OUTPUT` pointing at the delivery folder.

For Godot, open/import `godot/project.godot`, then run:

```
Godot_v4.7.2-stable_win64_console.exe --headless --editor --path <godot-folder> --import --quit
Godot_v4.7.2-stable_win64_console.exe --headless --path <godot-folder> --script res://selftest.gd
Godot_v4.7.2-stable_win64_console.exe --path <godot-folder> --rendering-method gl_compatibility --resolution 1920x1080 --script res://capture.gd
```

The project-local GLBs are byte-identical copies of the delivery-root GLBs. Exclude `.godot/` when testing a fresh import. `SHA256SUMS` identifies delivered assets/evidence.

## Remaining visual gaps against the reference

- Source reconstruction has softer/pitted plate boundaries than the reference's crisp manufactured panels; normal projection does not turn this into CAD-quality geometry.
- This is an approximate S/coil/tail-curl match, not a pixel-matched pose. Tight inside bends expose more dark coupler than the reference; the rigid driver does not guarantee collision-free armor for arbitrary new curves.
- Tail fins and terminal transitions remain softer than the reference. The tail is one static source-derived section, not individually articulated terminal subsegments.
- Native Compatibility-renderer evidence verifies emitted color and material import, not HDR bloom or emissive GI. No postprocess glow is claimed for that renderer.
- The 120-pose check establishes transform/material/import behavior, not gameplay, collision, or reference-quality acceptance.
