# Fix-pass implementation handoff — op-assembly-sectional-v1-fix1-20261017

Ready for independent panel/producer review; **NOT an acceptance verdict**. Stopped at this handoff; no next order started.

- Built on authorized original `45cb5d8`, same branch `assembly-sectional-v1-20261017`. Required first-renderable WIP checkpoint **833805d** was pushed, then work continued without waiting.
- Changed: section-local manufactured PBR maps; angular skull cladding and thin sharp crest fins; real box cheek vents; recessed nearly continuous teal bands; layered module shoulders and hydraulic rods; longer/thinner plated tail and attached blade fins. Detailed changes and remaining visual gaps are in NOTE.md.
- Exact final GLB triangles: **head 12,945**, **segment + joint 1,588**, **tail + joint 2,372**, **total 59,781**. All caps pass, with 219 total triangles spare.
- **PASS:** GLB tangents/ORM/+Y-up/no-Draco/no-skins; 28 rigid nodes reference one shared module mesh; 29 joint inserts.
- **PASS:** original single modeled lens unchanged across all 16 child nodes, transforms, topology, vertex attributes and materials (maximum attribute error 0). No second lens.
- **PASS:** original `captures/wip-*.png` byte-for-byte unchanged. `fix-validation.json` records protected hashes and lens comparisons.
- **PASS:** fresh-cache Godot **4.7.2** import and **120/120 Path3D poses, zero failures, 59,781 triangles**; both GLBs instantiate; original rest-pose and PBR/tangent checks pass.
- **PASS:** final Blender and native Godot full-body/head images inspected at **1920x1080**, original neutral staging/fixtures retained. Native Godot backend is Compatibility/Mesa llvmpipe; Blender uses CPU Cycles. Root/Godot GLB copies are byte-identical.
- **PASS:** saved `.blend` reopened with one complete lens, master curve, 28 shared-mesh segments and all nine used material images packed.
- No current implementation blocker. Gate verdict remains with the panel/producer. See `SHA256SUMS`, `fix-validation.json`, `glb-validation.json`, `blend-audit.json`, and `godot/selftest-result.json` for evidence.

---

# Historical checkpoint/status records below

# Fix-pass WIP checkpoint — op-assembly-sectional-v1-fix1-20261017

Built directly on `45cb5d8`, same branch. First renderable head/material revision; NOT a quality-gate verdict.

- Done: replacement section-local PBR atlases, angular head overlays, thin crest fins, modeled box cheek vent; skull/tail triangle reallocation; 28 rigid nodes retain one shared mesh; one delivered lens retained.
- WIP counts: complete head **12,511**; module + joint **1,468**; tail + joint **2,236**; assembly **55,851**. GLB validation passes tangents, ORM, sharing, node counts and budgets.
- New checkpoint captures: `captures/fix1-wip-full-body.png`, `captures/fix1-wip-head-closeup.png`, neutral original staging, 1920x1080. Original `captures/wip-*.png` SHA-256 checks pass unchanged.
- In progress: resolve head-atlas projection artifacts visible in this checkpoint; improve recessed ring geometry/color; add economical layered module details and the longer, thinner tail-fin treatment.
- Remaining: final captures, clean Godot 4.7.2 import and 120-pose regression, independent lens/WIP immutability checks, final documentation and evidence hashes. Existing final/Godot evidence below this checkpoint still describes the original build until rerun.
- Native Windows node offline; Blender 4.5 LTS CPU rendering and Godot 4.7.2 are available locally. GPU render attempt exhausted the currently available VRAM; CPU captures succeeded.

---

# Final implementation handoff — op-assembly-sectional-v1-20261017

Ready for independent quality-gate review; NOT an acceptance verdict.

- Implemented: repaired source-derived sections, 28 rigid shared-mesh body nodes, 29 segmented emissive inserts/dark housings, closed internal couplers, single seated modeled lens, packed PBR maps, master curve and Godot Path3D driver.
- Final GLB counts: head including lens **15,104**; segment including joint **1,468**; tail including joint **2,736**; assembled **58,944**.
- Verified: source package SHA-256; GLB tangents, shared meshes, ORM and rigid transforms; clean fresh-cache Godot 4.7.2 import; **120/120** driver poses with zero failures; native 1920×1080 captures; saved `.blend` reopened with all nine material images packed.
- WIP checkpoint `793ec5e` was pushed at the first assembled pose. Its captures remain byte-for-byte unchanged. The two-eye defect is corrected to ONE front/review-facing lens.
- No current implementation blocker. Windows C: exhaustion interrupted one save/test-copy; ticket files were moved intact to D: and all final saves/checks succeeded there.
- Remaining for gate: judge reference fidelity and documented visual gaps in NOTE.md (soft/pitted reconstruction, approximate pose, tight-bend coupler exposure, soft tail fins). No next ticket has been started.

---

## Original first-pose checkpoint record

# WIP checkpoint — op-assembly-sectional-v1-20261017

First fully assembled pose, before polishing. NOT a quality pass.

- Done: input SHA-256 verified; brief/staging read; source section cropping; 28 rigid body nodes on master spline; separate dark housings and twelve emissive bars at 29 joints; modeled two-sided lens eyes; initial GLB exports and neutral 1920x1080 captures.
- In progress: reconstruction repair. Current staging reveals severe fragmented surfaces from the cropped source remesh. This checkpoint is evidence of the defect, not a claim that the geometry is usable.
- Counts so far (evaluated Blender assembly): head including lenses 16,952; module 735 plus 336 joint = 1,071; tail 1,955; total 49,231. These are provisional and must be independently checked against final GLB.
- Remaining: repair section surfaces and pose, finish PBR wear, inspect latest renders, verify GLB tangents/ORM/rigid instances and Godot import + 120-pose test, package final deliverables and gaps.
