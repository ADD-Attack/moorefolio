# STATUS — snake-reassembly-20261018 · Round 2 coarse build · WIP-CHECKPOINT

Forge seat (`studio-3d`), Opus 5.5. Status as of 2026-10-18 08:57 CDT. All renders and close-ups were viewed in-session against REFERENCE.png and the three close-ups.

## Done
- **Sections rebuilt to budget** as clean procedural game geometry (`source/build.py`, deterministic and headless). Each section has a clay-only simple material set: clay grey, dark recess/housing, teal emissive, eye core/iris, and eye cover glass.
- **Head (H1–H10).** A boxy superellipse loft, with section stations from the clay head cut at the collar (D-H1). These are blended 0.25 clay + 0.75 reference template, because the clay's rear stations carry neck mass. Scale comes from the spec, per P3 (H = 1.4 D, L:H = 1.45). The head also has:
  - riveted plate rows with seams, a mouth line and a two-tier jaw;
  - a nostril slot;
  - 3 swept plated crest blades (raked ~30°);
  - a cheek vent box with 6 modelled slats and a rear piston rod;
  - inset window, placard and collar vent;
  - a stacked collar with a rear bulkhead and boxed top fitting.
- **Lens eye (H6), modelled, ×2.** Concentric outer metal ring, dark groove, light machined lip, dark bezel bowl, and 8 aperture blades recessed behind the core (P2). Layered emissive iris (saturated rim, then mint, then a white-hot core ≈28 % of the lit disc). A curved glass cover. Radii follow the §2 radial profile (assembly 0.34 H, lit disc 0.21 H).
- **Hero body module (B1–B9)**, one mesh instanced 22× (coil segments):
  - drum L:D 0.85 with 0.18 D joint gap (pitch 1.03 D; measured on the reference front coil at ≈1.04);
  - stepped shield plate with raised top tab and lower-right notch step;
  - 3 framed, recessed grille windows per side (frames and recesses modelled; the weave is left for a normal map, per P5);
  - waist band with twin axial pistons at each end (barrel, rod and end-fitting), centre bracket blocks flanking the lower grille slot, lower plate, bolts;
  - dark housing ring with a raised lip at the +X end.
- **Neck variant (B10)**, one mesh instanced 6× (P6 b). Heavier overlapping plating, a framed side window, and heavy collar bands at both drum ends.
- **Glow inserts (B9) at EVERY joint.** Separate insert meshes: 26 segmented emissive bars (thin dark ribs) per body joint. The tail taper joints and the tip joint use 16-bar inserts. That is 31 inserts across 31 joints; segment 1's ring sits against the head collar.
- **Tail (T1–T5).** Two taper segments are tapered "lite" variants of the hero module (YZ taper 0.86→0.70→0.52, lengths ×0.90 / ×0.80), with a circular port fitting on taper 1. The finned torpedo terminal has: a nose cone with nozzle hole, a dorsal swept fin with notched trailing edge, a lateral fin pair, a 7-slat flank vent, a 4-slat nose vent, a seam band and its own joint housing.
- **Assembly.** Head (static) + 28 body segments (6 neck + 22 hero) + 2 taper segments + tip. Each is its own rigid node, placed by chord on a Catmull-Rom master curve, with each glow insert parented to its segment node. That makes 63 mesh nodes, with no skinning and no merged mesh.
- **Pose (spec §1).** The head is held high at upper-left, snout −X and slightly down. A raised S-neck drops into the coil centre. The ground coil is about 1.3 laps: the front run is continuous across the frame; the left end turns back; the right side has two layers (an inner turn and an outer lower run). The tail exits right and curls toward the camera, tip pointing left, at front-right.
- **Judged staging captures** (`captures/`):
  - Cycles 256 spp, adaptive 0.01, OIDN, 1920×1080, GPU OptiX (the device is disclosed; it is not CPU).
  - Film is transparent and composited over **#C1C1BF**. Measured backdrop corners are (193,193,191) in all three captures (`captures/backdrop-check.json`).
  - Shadow-catcher contact shadow; shaped key, rim and fill area lights; Standard view transform; tight FOG_GLOW glare (threshold 0.9, strength 0.3, size 0.12).
  - Full-body and head close-up per REVIEW-STAGING.md, plus a segment detail view (extra evidence, not a review deliverable).

## Tri counts (exact, triangulated)

| Section | Mesh | Tris | Budget |
|---|---|---|---|
| Head (incl. 2 lens assemblies, fins, vents, collar) | Head | **10,250** | 10,000–18,000 ✓ |
| Hero module + joint | SegmentHero 1,546 + GlowInsert 52 | **1,598** | ≤1,600 ✓ |
| Neck variant + joint | SegmentNeck 1,408 + GlowInsert 52 | **1,460** | ≤1,600 ✓ |
| Tail section (2 tapers + tip + 3 joints) | 900+32 + 804+32 + 852+32 | **2,652** | ≤3,000 ✓ |
| **Full assembly, instanced** | 63 mesh nodes | **56,818** | 30,000–60,000 ✓ |

## Self-score: rubric categories 1–4 (clay renders; MATCH / QUALITY)

My scores steer; the blind panel gates. **I do not expect these to clear 7.5. Medians are below the gate, and I am reporting that rather than inflating.**

**Category 1, per-feature shape (frozen 25):**

| Feature | MATCH / QUALITY | Note |
|---|---|---|
| H1 skull massing | 6.5 / 6.5 | Proportions OK. The crown is still a touch domed; the reference is flatter and more faceted. |
| H2 plate breakup | 6 / 6 | — |
| H3 jaw seam | 5 / 5.5 | The two-tier jaw reads weakly. |
| H4 nostril slot | 4.5 / 5 | Small and low-contrast. |
| H5 crest fins | 6 / 6 | — |
| H6 lens eye | 7 / 7 | — |
| H7 vent box | 6.5 / 6.5 | — |
| H8 rod | 6.5 / 6 | — |
| H9 insets | 5 / 5.5 | — |
| H10 collar | 5.5 / 5.5 | Reads as a ribbed sleeve more than stacked plates. |
| B1 drum | 7 / 7 | — |
| B2 stepped shield | 6.5 / 6.5 | — |
| B3 framed grilles | 7 / 7 | — |
| B4 pistons | 6 / 5.5 | The waist reads cluttered. |
| B5 brackets | 6.5 / 6 | — |
| B6 lower plate | 6 / 6 | — |
| B7 fasteners | 4.5 / 5 | Only 3 per side inside the 1,600 cap; the reference shows 6–10. |
| B8 housing | 7 / 7 | — |
| B9 glow bars | 7 / 7 | — |
| B10 neck variant | 6 / 6 | — |
| T1 taper | 6.5 / 6.5 | — |
| T2 torpedo | 6.5 / 6.5 | — |
| T3 dorsal fin | 6 / 6 | — |
| T4 fin pair | 6 / 6 | — |
| T5 vents | 6.5 / 6.5 | — |
| **Median** | **6.25 / 6.25** | — |

**Other categories:**

| Category | MATCH / QUALITY | Note |
|---|---|---|
| 2. Silhouette | 6 / 6.5 | The head and S-neck read right, and the tip is at front-right pointing left. The coil footprint is wider and more open than the reference. The reference's turns are tighter than rigid 1.03 D-pitch drums can bend without heavy interpenetration (~40° per joint), so the extra length goes into a visible back lap. |
| 3. Massing / composition | 6.5 / 6.5 | Body diameter is constant to the taper, and head vs body is at the spec maximum (1.4 D). The neck rises from the coil centre. |
| 4. Modelled detail | 5.5 / 6 | Grilles, vents, slats, pistons and lens are modelled. Fastener density is low, and the plate bevels are single-step. |

## In progress / remains
- **Round 3 (material):** worn gunmetal, ORM packing, scratches, grime, rust in recesses, grille weave normals, and bloom tuned on final emissives. Material is not in scope here.
- **If the panel fails 1–4, my fix brief targets, lowest first:**
  1. B7 fasteners: free budget by sharing the housing and panel edge loops, to reach 6–8 bolts per side.
  2. H3/H4/H9: a deeper mouth line and a lower-jaw tier step, plus a bigger nostril.
  3. Silhouette: tighten the coil by allowing nested drum overlap on inner turns. I would test whether 30–35° bends read acceptably, and research how rigid-segment snake rigs hide inner-side overlap.
  4. H10: rebuild the collar as stacked plates instead of lathe bands.
- **Not yet done** (scheduled for Round 4 per the brief): GLB export, the Godot import, and the 120-pose Path3D test.

## Clay usage (honest accounting)
- **Head:** clay stations (width / z-extent at 16 x-stations, crest excluded, z > 0.05) are logged in `build-log.json` and drive 25 % of the section massing. The clay neck is discarded (D-H1).
- **Segment:** the plate layout was matched by eye. The clay drum A agrees with segment2-closeup on the stepped shield, tab, notch, window, waist pistons, centre slot and lower plate, and the module dimensions come from the close-up. **No clay vertex data drives the module.** Component B is discarded, and drum A is not imported.
- **Tail:** the ground slab is removed in the analysis (D-T1). A PCA radius profile of the finned tip is extracted and logged (`clay_tail_tip_radius_profile`). **The torpedo lathe currently uses spec ratios, not that profile.** The fin and vent layout follows the clay and the tail close-up. The taper segments are hero-module derivatives, as ruled.

## Files
- `source/build.py`: full section build plus assembly (rerun regenerates `snake-r2.blend`).
- `source/render.py`: staging and judged renders.
- `source/bgcheck.py`: backdrop verification.
- `source/inspect_r1.py`, `source/eye_r1.py`, `source/crop.py`: Round-1 reference and clay analysis.
- `captures/r2-wip-full-body.png`, `captures/r2-wip-head-closeup.png`: judged pair, 1920×1080. `captures/r2-wip-seg-detail.png`: extra evidence.
- `captures/r2-wip-render-settings.json`, `captures/backdrop-check.json`.
- `build-log.json`: tri counts, clay profiles, curve length, node count.
- `snake-r2.blend`: recoverable checkpoint (lane rule 5).
