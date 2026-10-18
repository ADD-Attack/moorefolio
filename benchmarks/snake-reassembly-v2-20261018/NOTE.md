# NOTE — FIX PASS (P7, handover #5, 2026-10-18) — supersedes the R2 scorecard below

Everything under "Round 2" further down is historical R2 evidence; the scorecard in THIS section is current.

## A. Deliverables (P7 build, commit on branch)
- Judged clay captures: `fix/captures/fix-p7-{full-body,head-closeup,seg-detail,tail-detail,tail_top-detail}.png` — Cycles GPU 256 / adaptive .01 / OIDN / 1920×1080, plain #C1C1BF, shadow catcher, key+rim+fill, ONE clay Principled material, no emission/glass/bloom (`fix-p7-render-settings.json`). Cameras/lights identical to P3–P6 previews.
- Same-angle overlays (Workbench clay, landmark-solved, iteration evidence): `fix/overlays/p7-head_*` (resid 9.5 px), `p7-seg_*` (resid 41.8 px — landmarks predate the S0-3 drum stretch; solve is loose, treat as indicative), `p7-tail_*` (solved tail overlay, resid 14.0 px).
- Section plots vs raw clay: `fix/sections/p7_{a_eye_station_x,b_midsnout_x,c_profile_y_nearside,d_plan_z_nostril}.png`.
- Previews `fix/previews/fix-p6-*`, `fix-p7-head` = 32 spp ITERATION PREVIEWS only.

## B. Budgets (P7)
Head 13,966 / 14,000 · module 1,303 + insert 120 = 1,423 / 1,450 · tail 1,806+556+476+84 = 2,922 / 3,000 · assembly 56,732 (30k–60k). Technical PASS. No B-form was cut for budget in this pass.

## C. Refine log R6+ (exact parameters in `fix/build-log.json`)
R6 segment axial stretch (S0-3) · R7 F8 machined panels traced from projection · R8 head shell repair (voxel isosurface of R1–R5 master, collapse) · R9 fin separation · R10 cut-in H2 seams / H3 mouth / H4 nostril (.042) / H9 insets / H7 slats / H8 rods · R11 fin face inset · R12 tail axial stretch (S0-4, L/D 1.76→2.70) · R13 tail surface + vents · R14 neck pose · R15 recess depth + piston collars · R16 module notch/brackets/fasteners · R17 tail taper from decimated hero module · R18 head fasteners · R19 tail nozzle + upper slats · R20 neck plate lap .09 · R21 fin through-cut repair · R22 fin edge frames · **R23 (new, P7) fin height ×1.38 / thickness ×1.25 about each blade midplane, 0 tris.**
Section plots c (profile) and a/b/d show the build line on the raw-clay line except at the cut-in recesses — R1–R5 forms preserved.

## D. Self-scorecard — RENDER REVIEW ONLY (Decision 36). MATCH / QUALITY
Reviewed: fix-p7 captures (all 5), p7 overlays (3), p7 sections (c viewed; a,b,d rendered, NOT individually viewed → their content UNREVIEWED), P6 previews.

| Feature | M / Q | Render evidence |
|---|---|---|
| H1 skull mass / L:H | 6.5 / 6 | head overlay silhouette tracks, snout length OK |
| H2 plate seams | 5 / 4.5 | seams visible as thin cut lines; reference seams wider/bevelled |
| H3 mouth line / overbite | 4.5 / 4.5 | groove reads as a line, too shallow vs reference |
| H4 nostril recess | 4 / 4 | small dark slot, weaker than reference ridged nostril |
| H5 fins | 6 / 5.5 | after R23 taller, three separated blades; reference blades more swept/rectangular |
| H6 eye seat | 6 / 6 | ring + seat read clearly in clay |
| H7 vent box (vertical slats) | 6.5 / 6 | reads well |
| H8 pistons | 5.5 / 5.5 | two rods + collars visible, still simple |
| H9 recessed frames | 4.5 / 4.5 | insets faint in head capture |
| H10/H11 collar, hood | 5 / 5 | collar bulky; hood present in profile |
| B1–B2 drum + shield plates | 5.5 / 5.5 | machined plates, but missing reference's stepped notch outline at large scale |
| B3 grilles | 4 / 4.5 | slat grids, not mesh (weave deferred to material per P5 ruling) |
| B4/B5 pistons, brackets | 5 / 5 | visible in seg capture, undersized |
| B6 lower plate | 5 / 5 | present, flat |
| B7 fasteners | 6 / 5.5 | bolts clearly modeled on every plate (was panel 1.0) |
| B8 glow-ring housing (clay) | 5.5 / 5.5 | housing reads as ring in clay |
| B10 neck variant | 4 / 4 | neck still kinks abruptly into coil; joint gaps visible |
| T1–T4 tail taper / tip | 5 / 4.5 | torpedo tip reads (S0-4 L/D 2.7); taper pieces faceted |
| T5 tail vents/fins | 5 / 4.5 | slats present; fins soft |
| Seam speckle | — | no black speckle visible in any P7 capture |
| Silhouette (cat 2) | 6 / 5.5 | full-body coil + raised head match reference read |
| Massing (cat 3) | 5.5 / 5.5 | neck/coil transition weak |
| Modeled detail (cat 4) | 5 / 5 | detail present but simple at hero scale |

Medians ≈ MATCH 5.0 / QUALITY 5.0 — **below 7.5. NOT READY; acceptance not claimed. Technical PASS ≠ acceptance PASS.**
Lowest remaining: H4, B3, B10, H3, H9. Stall note (Decision 28): H3/H4/H9 have been depth-tuned three passes with little render gain at this tri count; next approach should be a different one (separate modeled nostril/mouth trim pieces with border bevels, budget reclaimed from collar H10), not further depth.

---

# NOTE — snake-reassembly ATTEMPT 2, Round 2 (coarse clay build) — Forge

**Readers:** the owner and the QA Clay panel. All images below were viewed in-session before this checkpoint.

**Technical status:** PASS on clay-gate purity, budgets, staging and reproducibility.

**Acceptance status: NOT READY by my own scores.** My category medians are below 7.5. The body module is the cause; the reasons are in §4. I am reporting this plainly rather than pushing a gap past the gate (attempt-1 lesson).

## 1. Judged captures (QA Clay assembled gate)

| Capture | File |
|---|---|
| Full body | `r2/captures/r2-full-body.png` |
| Head close-up | `r2/captures/r2-head-closeup.png` |
| Segment detail | `r2/captures/r2-seg-detail.png` |
| Tail detail (added for the Decision-36 render review, same staging) | `r2/captures/r2tail-tail-detail.png` |
| Settings | `r2/captures/r2-render-settings.json` |

- **Render:** Blender 4.5.14 Cycles on GPU (OptiX), 256 samples, adaptive threshold 0.01, OIDN denoise, 1920×1080.
- **Backdrop:** film transparent, composited over **#C1C1BF**, with a shadow-catcher contact shadow. Shaped key, rim and fill area lights.
- **Clay-gate purity (Rule 5):** ONE material, `clay`, on every visible mesh (Principled, linear base 0.22, roughness 0.55, no emission). The render script **asserts** this per object and aborts otherwise.
  - No glare or bloom node: the compositor is alpha-over only.
  - The eye lens and every glow insert exist as geometry and render in clay.

## 2. Same-angle comparison (Rule 4)

Overlays use a landmark-solved camera on the reference close-up. Red = build silhouette, blue = reference edges. `*_sbs` files are side-by-side.

**Head**: before R5 in `r2/before-R5/h2_*`; after R5 in `r2/after-R5/h3_overlay.png`, `h3_sbs.png`. The solve residual went from 35 px before R5 to 28 px after.
- Kept from the clay: brow over the eye, snout taper, sloping topline, mouth seam over a separate jaw mass, eye seat, vent box, collar and the three blades.
- After R5, the snout tip and the jaw underline sit on the reference lines.
- Remaining deviation: the plate seams are softer and shallower than the reference.

**Segment** (`r2/overlays/s2_overlay.png`, `s2_sbs.png`):
- Reads: drum mass, top tab, notch step, piston masses.
- Missing: grille windows, ledge, brackets, bolts. They do not survive at the budget (§4).

**Tail:** no solved overlay this round, for lack of time; this is disclosed. Fin and torpedo forms were checked by eye in `r2/iteration-previews/pv_SRC_TailTip_*`.

**Section survival test (PRESERVATION-PLAN H.4).** Files are `r2/sections/sec_*.png`. Grey = raw cut clay, red = head build, same frame.
- (a) Eye-station cross-section:
  - The build tracks the clay all round.
  - The mouth-seam notches are kept on both sides.
  - The **R1 brow ledge shows as the lip projecting outward at both upper corners**: the overhang exists as geometry.
- (b) Mid-snout cross-section.
- (c) Near-side vertical profile: the build lies on the clay line from collar to snout.
- (d) Plan section at nostril height.

## 3. Construction: what was derived from the clay, and how (Decision 35)

### Head: the formed clay surface itself

The construction chain:
1. Cut at the collar plane (x = 0.19), keeping the skull island. The clay neck is discarded.
2. Four logged local refines of the clay, then the R5 snout stretch (§5).
3. Reduce the same surface to 13,304 tris.
4. Uniform scale only (F9).

How the reduction works:
- The Hunyuan shell is not a closed volume.
- Three methods were tried and **rejected on visual evidence**: voxel remesh (the surface collapsed, area 8 → 0.7), deleting non-manifold fans plus hole-fill, and curvature-weighted collapse (both shattered the mesh).
- The working method: merge doubles, then **split** the 9,706 edges that have more than two faces (no area removed). Then unweighted quadric collapse, then a re-weld of the split seams.

Deviation against the clay, as % of head length:

| Comparison | p50 | p95 | p99 | max |
|---|---|---|---|---|
| Build vs refined master | 0.10 | **0.33** | 0.45 | 0.79 |
| Build vs raw clay, R5-stretched | 0.10 | 0.36 | 0.58 | 1.48 |

The p95 against the refined master meets the plan's ≤0.4 % retopo gate.

### Hero segment

1. Kept clay component A only.
2. Cut at the +X housing face, which drops the fused melt.
3. Removed the drip spike and culled the hidden interior cup (29,612 faces, all at r < 0.30 D).
4. **Retopo by projection (plan S.3):** a 36 × 18 cylindrical grid. Every vertex is the outermost clay surface point on its radial ray (BVH ray cast, 0 misses). Ends are capped.
5. No flip: the clay's detailed shield face looks at the camera on the front run.

The deviation p50 is 0.86 % of pitch. The p95 of 11.8 % is dominated by hidden inner clay surfaces that a single outer shell cannot represent by design. The visual result is still soft (§4).

### Neck variant (B10)

Derived from the hero build: outer plates scaled ×1.07 and lapped 0.06 forward over the next joint.

### Tail

**Tip:**
1. Slab removed (z < −0.255).
2. Cut at the torpedo base and kept the tip island.
3. Same split-and-collapse path as the head, down to 1,446 tris.

Deviation as % of tip length: p50 0.28 %, p95 0.80 %.

**Tapers ×2:** from the hero clay by the same projection at 24 × 10, with radial taper 0.86 → 0.70 → 0.52.

### Parametric parts (Rule 2, machined only)

- **H6 eye lens:** 24-sided rings (outer ring, groove, lip, bezel, domed cover) plus 8 recessed blades (P2). They are seated by ray cast on the clay eye disc, with the disc normal averaged from the clay. The radius is the clay's own ring radius (0.083 in clay units).
- **B9 glow inserts:** 20 segmented bars at the clay's measured housing radius.
- **T1 port fitting.**

### Pose (§1)

- Attempt-1 master curve, scaled by pitch / 1.03 (0.755).
- Head high at upper-left, raised S-neck, one ground loop, tail exiting right and curling toward the camera with the tip pointing left.
- 28 rigid segment nodes (6 neck variant + 22 hero), a glow insert at every body joint, 2 taper nodes, the tip and the head. 61 mesh nodes in total.

## 4. Budgets and the F8 report (evidence, no silent cuts)

| Mesh | Tris | Target |
|---|---|---|
| Head (incl. lenses) | 13,302 | ≤ 14,000 ✔ |
| Hero module + insert | 1,296 + 120 = **1,416** | ≤ 1,450 ✔ |
| Neck variant + insert | 1,416 | ≤ 1,450 ✔ |
| Tail section (tapers 560 + 480, insert 84, tip 1,446) | 2,570 | ≤ 3,000 ✔ |
| **Instanced assembly** | **55,520** | 30–60k ✔ |

Tangents, ORM and GLB export are material/delivery-phase items and were not produced this round.

**F8 report: at 1,450 the clay-derived module cannot hold the B-forms.**
- Evidence is in `r2/overlays/s2_sbs.png` and `r2/captures/r2-seg-detail.png`.
- At 1,296 tris, the projected clay drum carries the tab, notch and piston masses. The 3 framed grilles (B3), the ledge (B2), the brackets (B5), the lower-plate recess (B6) and the bolts (B7) go below grid resolution. They are present in the clay but not in the build.
- Quadric collapse straight from the 237k clay is worse: it shattered at 1.3k (seen in-session; not kept). `r2/iteration-previews/pv_SRC_*` are Workbench iteration previews of the delivered SRC meshes.

My recommendation, for the producer to rule:
- Treat the drum and its armour plates as a **machined subject under Rule 2**.
- Rebuild the plates as crisp parametric panels whose outlines and heights are **traced from this R2 projection map**, so the layout and heights stay the clay's own. Model the grille frames as recesses, as R4 did at 1,600.
- The head, the tail tip and every sculpted form stay on the clay.
- Alternatives: raise the module budget, or raise the assembly cap.

## 5. Refine log (all local edits of the formed clay, scripted, in clay units before scale)

| ID | Form | Edit | Verts |
|---|---|---|---|
| R1 | H11 eye-brow ledge (both sides) | Outward-facing brow-roll verts at x −0.667 ± 0.16, z 0.648 ± 0.045 pushed out 0.022 and down 0.006 with cosine falloff, so the lip overhangs the socket. Section (a) confirms it. | 564 / 557 |
| R2 | H11 forehead hood (F2) | Forward brow swell inflated 0.012 along its own normals, at x −0.85 ± 0.08, z 0.57 ± 0.05. | 1,022 |
| R3 | H12 snout-ridge crests | High-curvature upper-flank verts pushed 0.005 along normals. Small; the clay ridge does most of the work. | 1,520 |
| R4 | F6 mouth serration | Along-seam z-only smoothing, 2 passes, window 0.028, \|dz\| < 0.014. Seam path and depth kept. | 3,979 |
| **R5** | S0-1 ruling: snout-only axial stretch | Verts forward of the eye ring (clay x < −0.76, i.e. eye centre − r − 0.01) are scaled along the head axis by **k = 1.320**. It is applied after R1–R4, so every local form rides along; the eye and skull are untouched. Target L:H 1.42 (minimum landing in band). **Measured on the delivered mesh: L:H = 1.444** (band 1.4065–1.4935; no overshoot past 1.45), from `r2/after-R5/head-LH.json`. Before/after evidence: `r2/before-R5/` (overlay and sections) vs `r2/after-R5/` (overlay and H.4 sections). Sections compare against the clay given the same stretch. | all forward of x0 |
| — | H6 lens seat | Ray-cast on the clay disc; normal from 24 disc samples. | — |
| — | Post-reduction weld | 8,377 head and 374 tail split-seam verts re-welded (radius 0.15 % of part size). | — |

**Not done this round (disclosed):**
- No nostril-recess deepening (H4).
- No mouth-groove deepening.
- No cutting of plate seams into the surface (H2 plate step, H9 frames).
- No fin thickening (H5).
- No jaw-underside flattening.

Residual dark speckles remain on the head and tail where split seams did not fully re-weld. They are visible in the head close-up.

## 6. Flags raised mid-round (in STATUS.md)

- **S0-1: RULED.** The snout-only stretch is permitted. It is applied as R5; measured L:H is 1.444.
- **S0-2: RULED, keep.** The clay's lateral blades stay. H5's centreline wording is recorded as a spec-text erratum, the same class as F1.
- **S0-3 (new):** segment clay L:D is **0.64 against 0.85** (−24 %, out of band). Uniform scale was kept, so the drums read short and wide.
- **S0-4 (new):** tail torpedo length / base diameter is **1.76 against 2.5–3** (out of band). Uniform scale was kept.

## 7. Self-scorecard (categories 1–4; MATCH / QUALITY, 0–10)

**Basis (Decision 36): every score below comes ONLY from my review of the delivered renders against the reference.** No score rests on tri counts, Hausdorff/deviation numbers, refine parameters, construction intent or effort; those are technical data (§3–§5).

**Renders reviewed in-session:**
- `r2/captures/r2-full-body.png` vs `REFERENCE.png`;
- `r2/captures/r2-head-closeup.png` and the matched-angle `r2/after-R5/h3_sbs.png` / `h3_overlay.png` vs `head-closeup.png`;
- `r2/captures/r2-seg-detail.png` and `r2/overlays/s2_sbs.png` vs `segment2-closeup.png`;
- `r2/captures/r2tail-tail-detail.png` vs `tail-closeup.png`. This capture was added for this rescoring, with identical staging, so the tail could be reviewed rather than guessed.
- Section plots `r2/sections/sec_*` show build vs clay only. They are used solely to confirm that an overhang exists, not to score match.

**How to read the table:**
- A form that sits inside a render's view but is not legible is a reviewed finding and is scored low.
- A form outside every render's view is marked **UNREVIEWED**.
- **These scores replace my earlier §7. Those were higher (median 5.0 / 5.0) because they partly credited construction intent, which Decision 36 excludes.**

### Category 1: per-feature shape (27 frozen features)

| # | Feature | MATCH | QUALITY | What the renders show |
|---|---|---|---|---|
| H1 | Skull massing | 6.5 | 5.0 | Long, low wedge, deepest at the eye line, tapering in profile and plan (head capture, h3_sbs). The surface is faceted and shard-broken rather than flat-faceted plates. |
| H2 | Plate breakup | 2.5 | 2.0 | No readable plate pattern, seams or rivets. Facet shards and dark speckle cracks instead. |
| H3 | Jaw seam + lower jaw (+ overbite, cheek) | 5.5 | 4.5 | Continuous seam line from the snout to under the eye, with jaw mass below (head capture, h3_sbs). Partly jagged, so it still reads slightly toothy. The overbite is not legible. A cheek mass below the eye reads. |
| H4 | Nostril slot | 4.5 | 4.0 | A dark slot is visible near the snout tip side (h3_sbs). The framed recess and ridge surround are not legible. |
| H5 | Crest fins ×3 | 3.0 | 3.5 | At the matched angle only ONE blade reads (h3_sbs); the full body shows one or two. The reference shows three distinct blades. Blade edges are ragged. |
| H6 | Eye lens assembly | 6.0 | 5.5 | Concentric proud ring with a seated lens disc, in the right place and at the right relative size (head capture, h3_sbs). |
| H7 | Cheek vent box | 5.0 | 4.5 | Chunky box with a raised frame behind the eye. Only 2–3 vertical bars are legible; the reference shows about 7–8. |
| H8 | Head piston | 2.0 | 2.0 | Not legible in any head render, although the region is in view. |
| H9 | Inset panels | 2.5 | 2.5 | A small recess may be present on the upper rear skull. The placard and the collar vent are not legible. |
| H10 | Collar | 3.5 | 3.0 | A blocky rear mass. Stacked plate rings and the boxed top fitting do not read. |
| H11 | Brow ridge + hood | 6.0 | 5.0 | A brow hood over the eye casts a shadow on the top of the eye ring (head capture). Section (a) confirms the overhang exists. The forehead hood is not separately legible. |
| H12 | Snout-ridge complex | 4.5 | 4.0 | A soft raised edge runs from the eye toward the snout. Its convergence into the nostril surround is not legible. |
| B1 | Drum massing | 4.5 | 4.0 | Cylindrical drums that read short and barrel-like against the reference. No plate flats (seg capture). |
| B2 | Stepped shield plate | 3.0 | 3.0 | A top-tab recess and side notches form an I-shape. No diagonal step to a second level and no ledge. |
| B3 | Framed grilles ×3 | 1.0 | 1.0 | Absent in every render. |
| B4 | Waist band + pistons | 2.5 | 2.0 | Blocky side protrusions at mid-height. No band and no cylinder/rod/fitting read. |
| B5 | Bracket blocks | 1.5 | 1.5 | Not distinguishable. |
| B6 | Lower plate + recess | 1.5 | 1.5 | The lower drum is plain. |
| B7 | Fasteners | 1.0 | 1.0 | None visible. |
| B8 | Joint housing ring | 2.5 | 2.5 | Joints show a thin dark slot. No thick ring with a lip reads. |
| B9 | Segmented insert | 4.0 | 4.0 | Segmented bars read where a joint opens: the right joint in the seg capture and the tail capture's taper ring. Mostly hidden in the coil. |
| B10 | Neck variant | 2.5 | 2.0 | The neck reads as an offset, kinked stack of drums with gaps (full body). No heavier overlapping collar plates. The reference neck is a smooth S. |
| T1 | Taper segments ×2 | 4.0 | 3.5 | Two smaller drums step down, with the port boss and the glow ring at the taper start visible (tail capture). No plate language. |
| T2 | Torpedo terminal | 3.5 | 2.5 | A stubby cone, much shorter than the reference torpedo. No nozzle hole visible. Shattered, speckled surface. |
| T3 | Dorsal fin | 3.5 | 3.0 | A small swept dorsal stub is visible. The notched trailing edge is not legible. |
| T4 | Lateral/ventral fin pair | 3.5 | 3.0 | One swept lower fin is visible. **Far fin UNREVIEWED**: it is outside every render's view, so the pair is not confirmed. |
| T5 | Tail grille vents | 1.0 | 1.0 | None visible. |

Category-1 medians: **MATCH 3.5 / QUALITY 3.0**. The head items alone come to 4.5 / 4.0.

### Categories 2–4 (from the full-body capture vs REFERENCE.png)

| # | Category | MATCH | QUALITY | What the renders show |
|---|---|---|---|---|
| 2 | Silhouette | 5.0 | 4.0 | **Reads:** head high upper-left, one ground loop, tail curling to the front with the tip pointing left. **Gaps:** the body reads as separate beaded barrels with pinches at the joints, where the reference is a continuous armoured tube. The neck is jagged, and the crest reads as one or two blades. |
| 3 | Massing and composition | 5.5 | 4.5 | **Reads:** layout and coil footprint follow the reference, and head-to-body scale is plausible. **Gaps:** the neck stack is offset and kinked, the drums are short, and the tail tip is stubby. |
| 4 | Modelled detail | 2.0 | 1.5 | Almost no key detail is legible (grilles, bolts, vents, panels). The head has eye-ring and vent-box detail only; surfaces show shard and speckle artefacts. |

**Gate read:** below 7.5 on every category, and well below. The renders show where the build stands:
- The head's large forms are present: wedge, eye seat, brow hood, mouth line, vent box.
- Its surface quality and every key detail are not.
- The body module and the tail detail are far from the reference.

## 8. Reproduce

```
blender -b -P source/build_r2.py   -- <clay_dir> <work_dir>
blender -b <work>/snake-v2-r2.blend -P source/render_r2.py -- <work_dir> final r2 full,head,seg
blender -b <blend> -P source/overlay.py  -- SRC_Head <head-closeup.png> <out> source/lm_head.json headbuild <build-log.json>
blender -b <blend> -P source/sections.py -- <hunyuan-head.glb> <build-log.json> <out>
```

- Clay inputs are the hash-verified attempt-1 copies (F10).
- The `.blend` in this folder is `snake-v2-r2.blend`, SHA-256 `ac92c8f9…3084703`. It holds the SRC meshes and the instanced nodes.
- Step-0 evidence is in `r2/step0/`.
