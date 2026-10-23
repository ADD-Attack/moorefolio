# Forge snake rig — delivery note (2026-10-23, Decision 57)

**Source:** M5e @ `2bdbba4` (branch `forge-snake-reassembly-v2-20261018`), file
`benchmarks/snake-reassembly-v2-20261018/material/m5e-mapped.blend` (baked maps `textures-m5e/`).
Rigged set = the 61 visible meshes, which is the same set as `snake-p8-material-m5e.glb`. The hidden `SRC_*` library meshes (render-disabled, not in the GLB) are left out.
(The brief originally named 20b2545/M1d; the producer corrected that to M5e at 10:00 CDT.)

## Deliverables (G:\UnrealProjects\TorchVizDemo\DemoData\)

| file | bytes | sha256 |
|---|---|---|
| forge_snake_rigged.fbx | 23,860,172 | 6265ceaea06e020a774da2b457bb8eb9863560884aa29896c9fbc2759d4d9db5 |
| forge_snake_rigged.blend | 41,894,909 | 25118a82c571b3fa72b86ef9a9e4f45bd81594ffa5a186930891a202b4d21a36 |

The FBX embeds its textures. The scene is metric with scale 1.0 and was exported with `FBX_SCALE_NONE`, so UE reads it in cm.

## Rig

- **Armature `ForgeSnake_Rig`, 26 bones.** `root` sits at the origin. Under it is one connected chain running tail tip → head:
  - `spine_01..18`: tail tip to Segment_07, at equal arclength along the segment centre line.
  - `neck_01..06`: one bone per neck segment, Segment_07 → Segment_01.
  - `head`: Segment_01 → snout.
- **Bone rolls** are parallel-transported from world up, so twist stays consistent along the chain.
- **Head is one bone.** Head_node is one main shell (5,576 verts) plus symmetric detail plates. There is no separable jaw, so the whole head assembly (plates and eye lens) is 100% on `head`.
- **Weights** are computed by script: each vertex gets an arclength position along the chain, and weight blends between adjacent bone midpoints with a smoothstep.
  - Rigid barrels bend only across their own joint window.
  - Glow inserts follow their segment.
  - I didn't use Blender heat weights because 61 disjoint, non-closed shells are a known failure case for them.
- **Mesh:** the 61 meshes are joined into one `ForgeSnake` object. Joining changes no geometry or material data.

## Verification (`acceptance/rig-report.json`)

- **Geometry unchanged:** verts 47,462, faces 35,624 and **tris 57,006** are identical before and after.
- **Materials unchanged:** the same 8 PBR materials and the same texture images.
- **Bounds and orientation:** world bounds are identical (min −3.021, −3.936, −0.053; max 4.794, 2.794, 3.969 m).
- **Weights:** unweighted vertices **0**; vertices over 4 influences **0**; max influences **2**; weight sums all 1.0.

## Pose tests (`stills/`, Workbench previews, not judged captures)

`pose-straight.png`, `pose-scurve.png` (wavelength 9 m, amplitude 1.6 m), `pose-coil.png` (rising helix, r 1.8 m), `pose-rest.png`.

- **Barrels:** they stay rigid and the joints bend smoothly. Nothing shears apart or collapses in the S-curve or the coil.
- **Edge stretch:** p1–p99 is 0.59–1.35 across all poses (`acceptance/pose-metrics.json`). The maximum outliers (~14×) are sub-millimetre edges in overlapping neck/collar pieces, not visible splits.

## Weight-repair iteration (the one in scope), with fixes along the way

1. **Bug fix:** segment meshes were instanced, and in Blender 4.x vertex groups live on mesh data. I made each mesh single-user before weighting.
2. **Bug fix:** the source meshes carry stale, unnamed deform data at group index 0. This dragged 379 head vertices toward the tail (huge stretch in the first straight test). New groups are now cleared before weights are written.
3. **Repair iteration:** the neck began as 2 coarse bones, which kept the rest-pose ground-to-vertical rise baked into the straight pose. It is now one bone per neck segment (6), and the neck straightens.

## UE 5.0 acceptance (`acceptance/ue50-import-check.json`, `ue50-import.log`)

- **Setup:** headless `UnrealEditor-Cmd -run=pythonscript`, scratch project (`%TEMP%\ScratchRigCheck`); no UE process was busy, and TorchVizDemo content was not touched.
- **Result: imports as `SkeletalMesh`**. It also creates a Skeleton, a PhysicsAsset, 8 materials and their textures. LogFbx reports 27 bones (UE adds the armature node as the top root). No errors.
- **Bounds:** extent 390.76 × 336.46 × 201.11 cm, origin (88.65, 57.10, 195.83) cm. This **matches the source exactly** (Blender metres ×100, Y mirrored for UE handedness).
- **First export was rejected:** it used `FBX_SCALE_UNITS` and imported 100× small. It was re-exported with `FBX_SCALE_NONE`, and that is what's delivered.
- **Cleanup:** the import extracted a `forge_snake_rigged.fbm/` folder next to the FBX. I deleted it.

## Notes and carried items

- **Neck read:** the neck plates read jagged when straightened. That comes from the neck pieces' rest placement (carried geometry debt: collar stacking and neck flats), not from the weights. Fixing it is out of scope (no geometry edits).
- **ORM in UE:** UE's FBX material import doesn't wire the ORM maps. Materials in UE are BaseColor/Normal/Emission until someone hand-wires ORM in a UE material pass.
- **Scripts:**
  - `scripts/rig.py`: rig, weights, verification and export.
  - `scripts/pose_test.py`: poses, metrics and stills.
  - `scripts/ue50_import_check.py`: the UE import check.
