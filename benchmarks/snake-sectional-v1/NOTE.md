# Fix-pass handoff — sectional snake v1

Order: **op-assembly-sectional-v1-fix1-20261017**. Branch: `assembly-sectional-v1-20261017`.
Built directly on **45cb5d8**; no source rebuild or other entrant consulted.
Implementation/evidence handoff only: **independent panel/producer acceptance is pending**.

## Fix-pass changes

- **Materials first:** replaced the noisy source-projected normal treatment with clean section-local manufacturing atlases. Head maps are 3072²; module and tail maps are 1024². Separate basecolor, tangent normal and packed ORM retain per-plate value/roughness/metallic variation, stepped dark seams, restrained broken edge wear, directional scuffs, recessed slotted screw heads and diamond-mesh service panels. Smooth, restrained oxidation replaces uniform gunmetal. AO is only in ORM R, not multiplied into basecolor; ORM G is roughness and B metallic. The new AO channel represents procedural recess detail, not a newly ray-baked geometric AO pass. Standalone AO files match ORM R.
- **Head:** retained and gently smoothed the delivered skull, reduced excess reconstruction density, flattened its thick source fin tips beneath three thin swept plate fins, and added actual closed angular jaw/muzzle/temple/brow shells plus stepped planar forehead cladding. Added two box-shaped cheek vent frames and real parallel vanes. No extra eye or lens was added.
- **Lens preserved exactly:** all **16** delivered lens child meshes, their transforms, topology, POSITION/NORMAL/TANGENT/UV attributes and material definitions compare unchanged against `45cb5d8` (maximum attribute error **0**). The single complete lens remains seated in the delivered location. `fix-validation.json` records the comparison.
- **Joints:** replaced the flat intersecting chord/housing layout with a recessed six-point housing profile and twelve separate two-chord emitter sectors. Housing triangles fall from 192 to 144; emitter triangles rise from 144 to 240; total is 384 per joint. Narrow ~0.8° sector gaps and the corrected radial clearance make the sectors read as a continuous teal band inside dark lips. Saturated joint emission has its own material, so the lens material remains unchanged.
- **Module:** calmed only the existing source-sampled shell's radial relief into a faceted barrel. Added four economical layered shoulder strips and a pair of eight-sided hydraulic rods; retained the existing modeled hex fasteners and side grille. All 28 rigid objects still reference **one shared mesh**, including these details.
- **Tail:** retained the original tail section/attachment, smoothed excess reconstruction micro-relief, reallocated its triangles, and extended the distal run by up to **0.62 local units**, with a 16% distal width/height reduction. Two thin angular fin plates are seated on the source tail's negative-Y curl, not left on its straight attachment axis. Its new atlas uses smaller panel spacing for a finely plated taper.

## Exact final fix-pass triangle counts

These are exported GLB counts, including every repeated node, not unique-mesh counts.

| Part | Original v1 | Fix pass | Limit |
| --- | ---: | ---: | ---: |
| Complete standalone head, including unchanged lens | 15,104 | **12,945** | 10,000–18,000 |
| Shared hero segment | 1,132 | **1,204** | — |
| One housing + emitter insert | 336 | **384** | — |
| Segment + joint | 1,468 | **1,588** | ≤1,600 |
| Tail geometry | 2,400 | **1,988** | — |
| Tail + terminal joint | 2,736 | **2,372** | ≤3,000 |
| Assembly: head + 28×(segment+joint) + tail+joint | 58,944 | **59,781** | 30,000–60,000 |

Net change: **+837** assembled triangles; **219** remain below the total cap.
28 rigid shared-mesh section nodes, 29 independent joint inserts, no armature/skins, no merged assembly, Principled-only materials, embedded images, UV0/tangents, +Y-up glTF, and Draco OFF are retained.

## Checkpoint and final evidence

- Required renderable WIP checkpoint **833805d** was pushed before final polishing. `captures/fix1-wip-full-body.png` and `captures/fix1-wip-head-closeup.png` show that state, including its then-unresolved head texel-allocation artifacts. Work continued without waiting.
- Original `captures/wip-full-body.png` and `captures/wip-head.png` remain **byte-for-byte unchanged** against `45cb5d8`; their hashes are recorded by the independent regression.
- Final `captures/full-body.png` and `captures/head-closeup.png` are newly rendered **1920×1080** Cycles images. They reuse the original scene's gray world, exact three neutral lights, original camera directions and projected-vertex fit with 12% margin. Framing refits the changed silhouette; no background/environment/floor/HUD or image editing is used.
- Final native Godot review captures are `captures/godot-full-body.png` and `captures/godot-head-closeup.png`, also **1920×1080**, using the unchanged neutral `godot/capture.gd` fixture. Linux Xvfb/Compatibility **Mesa llvmpipe** supplies these native rendered pixels; this is not a headless-render or hardware-GPU claim.
- **PASS:** clean-cache Godot **4.7.2** import; both GLBs instantiate; **120/120 poses, zero failures, 59,781 triangles**. The delivered rest pose is checked before the driver can repair transforms. Existing arc-spacing, finite/unit-determinant frame, lens-count, texture-slot and tangent assertions all pass. `godot/import.log`, `godot/selftest.log`, `godot/selftest-result.json`, and `godot/capture.log` are regenerated for this revision.
- **PASS:** exported GLB validation, lens/WIP immutability and matching root/Godot GLB bytes. Reopened `.blend` audit confirms 28 shared-mesh sections, one complete lens, master curve and all nine used material images packed.
- This fix used local **Blender 4.5.3 LTS** and **Godot 4.7.2 Linux** because the original Windows node was offline. A CUDA render attempt exhausted available VRAM; delivered Blender captures are successful CPU renders. That failed attempt is not delivery evidence.

## Reproduce the fix (do not rerun the original source build)

From the repository root, extract the authorized original delivered scene to a separate location:

```sh
git show 45cb5d8:benchmarks/snake-sectional-v1/snake-sectional.blend > /tmp/sectional-v1-baseline.blend
ASSEMBLY_BASELINE=/tmp/sectional-v1-baseline.blend \
ASSEMBLY_OUTPUT="$PWD/benchmarks/snake-sectional-v1" \
FIX_STAGE=final blender -b -t 12 --python benchmarks/snake-sectional-v1/fix_pass.py
python3 benchmarks/snake-sectional-v1/check_fix.py --capture
ASSEMBLY_OUTPUT="$PWD/benchmarks/snake-sectional-v1" \
blender -b --python benchmarks/snake-sectional-v1/audit_blend.py
```

`GODOT` can select the Godot executable. `check_fix.py` uses a fresh temporary project with no `.godot/`, imports before testing/capture, checks the installed engine version, verifies 120 poses and exact viewport dimensions, and copies the resulting evidence back. With no DISPLAY, capture uses `xvfb-run` and software OpenGL. Do not set `FIX_STAGE=wip` on the delivery folder: that option exists for the checkpoint phase, not to overwrite protected evidence.

## Remaining visual limitations for the panel

- Under the new angular cladding, some source-derived transitions remain rounded, especially around the lower muzzle and rear temple. This is not a complete CAD retopology of the head.
- The rigid barrel modules remain more uniform than the reference's densely layered armor; much of the new service detail is deliberately texture-space to respect the multiplied budgets. The modeled shoulder strips and rods are economical, not full mechanical internals.
- Tail source transitions and the approximate raised-S/coil pose are retained. The extended terminal section is one rigid tail, not separately articulated fine subsegments. Tight bends can still reveal dark coupler gaps.
- Compatibility captures verify emitted color and material appearance, not HDR bloom or emissive GI. The 120-pose test does not establish collision-free articulation or a panel quality score.

---

# Original v1 handoff below — historical baseline only

The following preserves extraction provenance and the original delivery record. Its counts/results describe **45cb5d8**, not the fix-pass export above.

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
