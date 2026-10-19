# NOTE — material delivery (M2), 2026-10-19

Geometry stayed frozen. This note scores only the renders listed below. Technical checks are not acceptance. The producer convenes the material gate. Call: **NOT READY**.

## What changed since M1 (`d8ae029`)

M1 procedural shaders were too chrome on the plates and too hot on the eye and joint bars. `source/bake_materials.py` was authored and unrun.

- Recovered the unpushed 23:15–23:21 local pass as `a15c2b3` (M1b). That pass darkened the metal and cut emission, and it was still chrome on the snout and the bright segment faces.
- M1c (`f21f55a`, rejected preview) dropped the albedo too far. Head and segments went near black. Kept as evidence, not the candidate.
- M1d (same commit, accepted shader) is the candidate: warm-dark gunmetal base about `(0.145, 0.138, 0.122)` with four plate values, roughness held inside about 0.34–0.56 (no `rough-0.08` floor drop), specular IOR 0.50, edge wear no longer near-white, rust mask unchanged and still restrained. Eye emission 1.05 with a smaller white core. Joint emission 0.50, color `#71CCBD`.
- Baked from `material/m1d-procedural.blend`. Mesh hashes matched `material/inventory.json` on every source. Export `material/snake-p8-material.glb`, SHA256 `d4bccee2dfe6f75de80d17543d6d0c26853ef93f8d555b07bb03eed4ab8e50bc`.

## Captures reviewed

All five were viewed before scoring. Cycles GPU, 256 samples, adaptive 0.01, OIDN, 1920×1080, backdrop `#C1C1BF`, shadow catcher, key/rim/fill, AO multiplied into albedo, glare threshold 1.0 / strength 0.25 / size 0.125. Cameras and lights are the frozen M1b review cameras (`material/captures/m2-render-settings.json`).

- `material/captures/m2-full-body.png`
- `material/captures/m2-head-closeup.png`
- `material/captures/m2-seg-detail.png`
- `material/captures/m2-tail-detail.png`
- `material/captures/m2-tail_top-detail.png`

Comparison plates are REFERENCE.png on the left and the capture on the right, scaled to the same height. They are **not** a landmark-solved same-angle warp. The landmark overlay script forces Workbench clay and would hide this material. Plates: `material/comparisons/m2-*-sbs.png`.

M1d 32-sample previews (head, segment) were also viewed and are iteration only.

## Budgets

`source/audit_material.py` on `material/m2-mapped.blend` against `fix/snake-v2-r2-fix.blend`: fingerprints unchanged, instance transforms unchanged, GLB node triangle counts match. Technical PASS. Not an acceptance pass.

| Part | Tris | Cap |
|---|---:|---:|
| Head | 13,968 | 14,000 |
| Module + insert | 1,431 | 1,450 |
| Tail | 2,970 | 3,000 |
| Assembly | 57,006 | 57,600 |

## Map inventory

Packed ORM: AO and roughness/metal share one image per material (`audit-material.json`). Emission is on the head and the two glow inserts only.

| Map | px | bytes |
|---|---:|---:|
| Head_BaseColor / ORM / Normal / Emission | 2048 | 1,100,402 / 1,441,742 / 797,345 / 67,974 |
| SegmentHero_BaseColor / ORM / Normal / Emission | 1024 | 495,463 / 719,711 / 547,226 / 13,922 |
| SegmentNeck_BaseColor / ORM / Normal / Emission | 1024 | 504,517 / 729,538 / 533,987 / 13,922 |
| TailTaper1_BaseColor / ORM / Normal / Emission | 1024 | 453,610 / 692,744 / 586,140 / 13,922 |
| TailTaper2_BaseColor / ORM / Normal / Emission | 1024 | 439,092 / 707,627 / 646,778 / 13,922 |
| TailTip_BaseColor / ORM / Normal / Emission | 1024 | 418,364 / 601,608 / 741,658 / 13,922 |
| GlowInsert_BaseColor / ORM / Normal / Emission | 256 | 23,294 / 24,156 / 32,495 / 2,439 |
| GlowInsertT1_BaseColor / ORM / Normal / Emission | 256 | 22,766 / 20,127 / 34,048 / 2,704 |

Non-glow Emission maps are small because those meshes bake no emission. Head base color was viewed: UV islands carry grey metal variation and two green eye discs, not an empty bake.

## Self-scorecard — render review only

MATCH / QUALITY. 10 is the reference. Medians use the middle of the listed scores. Nothing here was scored from triangle counts or shader settings.

### 1. Head features

| Feature | M | Q | From the renders |
|---|---:|---:|---|
| H1 skull massing | 5.5 | 5.5 | Long head, but softer and less boxy than the reference. Crown is not a broad flat. |
| H2 plate breakup | 5.0 | 5.0 | Seams and rivets exist. They do not read as 12–16 overlapping plates. |
| H3 jaw | 4.5 | 4.5 | A dark line on the snout, not a two-tier lower jaw. |
| H4 nostril | 5.0 | 5.0 | Dark side slots are there. The ridged surround is weak. |
| H5 crest fins | 4.0 | 4.5 | Two tall ear-like blades, not three swept centreline fins. |
| H6 eye | 4.0 | 4.0 | Round and lit. One green disc. No white-hot core, no radial rings, no bezel steps. |
| H7 cheek vent | 6.5 | 6.0 | Box, frame, and slats read behind the eye. |
| H8 piston | 6.0 | 5.5 | Rods run from the vent into the neck. |
| H9 insets | 4.5 | 4.5 | Small panels exist. Window, placard, and collar vent do not read as a set. |
| H10 collar | 5.0 | 5.0 | Neck is segmented. It is not a heavy stacked collar. |
| H11 brow | 4.0 | 4.0 | No overhang casting a shadow on the eye. |
| H12 snout ridges | 4.5 | 4.5 | Taper is there. The ridge-into-nostril gesture is not. |

MATCH median 4.75, mean 4.88, range 4.0–6.5. QUALITY median 4.75, mean 4.83, range 4.0–6.0.

### 2. Body and tail

| Feature | M | Q | From the renders |
|---|---:|---:|---|
| B1 drum | 6.5 | 6.0 | Repeated cylinders, a bit soft. |
| B2 shield plate | 5.5 | 5.5 | Stepped plates, not the reference notch. |
| B3 grilles | 5.5 | 5.0 | Frames and dark recesses. Backs read as an X, not a weave. |
| B4 pistons | 7.0 | 6.5 | Twin rods in the waist read clearly. |
| B5 brackets | 6.0 | 5.5 | Blocks flank the centre slot. |
| B6 lower plate | 6.5 | 6.0 | Large lower plate with a recess. |
| B7 fasteners | 7.0 | 6.5 | Round bolts at plate corners. |
| B8 housing | 6.0 | 5.5 | Dark joint gap. The ring is less thick than the reference. |
| B9 emissive bars | 7.5 | 7.0 | Segmented teal bars at the joints. Cleaner than the worn reference. |
| B10 neck | 5.5 | 5.0 | Larger neck panels, still a plain tube compared with the reference collars. |
| T1 tapers | 6.5 | 6.0 | Diameter drops, plates continue, a port is visible. |
| T2 torpedo | 5.5 | 5.5 | Tip is shorter and blunter than the reference missile. |
| T3 dorsal fin | 6.0 | 5.5 | Swept fin on the tip. |
| T4 side fins | 6.5 | 6.0 | Pair reads in the side and top views. |
| T5 vents | 5.5 | 5.0 | Flank slats read in the top view. Nose vent is weak. |

MATCH median 6.0, mean 6.20, range 5.5–7.5. QUALITY median 5.5, mean 5.77, range 5.0–7.0.

### 3–4. Silhouette, massing, modeled detail

| Category | Scores M | M med / mean / range | Scores Q | Q med / mean / range |
|---|---|---|---|---|
| Silhouette (full, head, tail) | 6.5, 5.0, 6.0 | 6.0 / 5.83 / 5.0–6.5 | 6.0, 4.5, 5.5 | 5.5 / 5.33 / 4.5–6.0 |
| Massing (coil, head, drums) | 6.5, 5.0, 6.5 | 6.5 / 6.00 / 5.0–6.5 | 6.0, 4.5, 6.0 | 6.0 / 5.50 / 4.5–6.0 |
| Modeled detail (bolts, grilles, head plates, tail fins) | 7.0, 5.5, 4.5, 6.0 | 5.75 / 5.75 / 4.5–7.0 | 6.5, 5.0, 4.5, 5.5 | 5.25 / 5.38 / 4.5–6.5 |

### 5–9. Material, scored on full, head, segment, tail

| Category | Scores | med / mean / range |
|---|---|---|
| 5 Material fidelity | 6.0, 6.0, 6.5, 6.0 | 6.0 / 6.13 / 6.0–6.5 |
| 6 Surface detail / wear | 4.0, 4.5, 5.0, 4.5 | 4.5 / 4.50 / 4.0–5.0 |
| 7 Lighting response | 6.5, 6.5, 7.0, 6.5 | 6.5 / 6.63 / 6.5–7.0 |
| 8 Color accuracy | 5.0, 5.0, 5.5, 5.0 | 5.0 / 5.13 / 5.0–5.5 |
| 9 Finish quality | 5.5, 5.0, 6.0, 5.5 | 5.5 / 5.50 / 5.0–6.0 |

Chrome is gone on the broad plates. A few curved faces, especially the snout and some upper segment plates, still throw a hard highlight. The metal reads cooler and darker than the reference's warm mid gunmetal. Rust and scratches barely show. Recesses are dark. Teal joints are in the right hue and no longer blown white. The eye is still a flat green dot.

Clay debts are still visible and were not touched: eye radial layering (H6), skull plate volume (H2/H11/H12), collar stacking (H10). The tail-top capture also shows a small loose fragment and one joint bar sitting off the taper. That is existing geometry. This phase did not move it.

## Call

**NOT READY.** No in-scope category median reaches 7.5. Technical budget audit passed. That is not a material-gate pass.
