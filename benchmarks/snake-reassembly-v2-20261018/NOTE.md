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
| Settings | `r2/captures/r2-render-settings.json` |

- **Render:** Blender 4.5.14 Cycles on GPU (OptiX), 256 samples, adaptive threshold 0.01, OIDN denoise, 1920×1080.
- **Backdrop:** film transparent, composited over **#C1C1BF**, with a shadow-catcher contact shadow. Shaped key, rim and fill area lights.
- **Clay-gate purity (Rule 5):** ONE material, `clay`, on every visible mesh (Principled, linear base 0.22, roughness 0.55, no emission). The render script **asserts** this per object and aborts otherwise.
  - No glare or bloom node: the compositor is alpha-over only.
  - The eye lens and every glow insert exist as geometry and render in clay.

## 2. Same-angle comparison (Rule 4)

Overlays use a landmark-solved camera on the reference close-up. Red = build silhouette, blue = reference edges. `*_sbs` files are side-by-side.

**Head** (`r2/overlays/h2_overlay.png`, `h2_sbs.png`):
- Kept from the clay: brow over the eye, snout taper, sloping topline, mouth seam over a separate jaw mass, eye seat, vent box, collar and the three blades.
- Deviations: the skull is shorter and taller than the reference (S0-1), and the plate seams are softer and shallower.

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
2. Four logged local refines of the clay (§5).
3. Reduce the same surface to 13,304 tris.
4. Uniform scale only (F9).

How the reduction works:
- The Hunyuan shell is not a closed volume.
- Three methods were tried and **rejected on visual evidence**: voxel remesh (the surface collapsed, area 8 → 0.7), deleting non-manifold fans plus hole-fill, and curvature-weighted collapse (both shattered the mesh).
- The working method: merge doubles, then **split** the 9,706 edges that have more than two faces (no area removed). Then unweighted quadric collapse, then a re-weld of the split seams.

Deviation against the clay, as % of head length:

| Comparison | p50 | p95 | p99 | max |
|---|---|---|---|---|
| Build vs refined master | 0.10 | **0.32** | 0.44 | 0.73 |
| Build vs raw clay | 0.10 | 0.35 | 0.55 | 1.46 |

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
| Head (incl. lenses) | 13,304 | ≤ 14,000 ✔ |
| Hero module + insert | 1,296 + 120 = **1,416** | ≤ 1,450 ✔ |
| Neck variant + insert | 1,416 | ≤ 1,450 ✔ |
| Tail section (tapers 560 + 480, insert 84, tip 1,446) | 2,570 | ≤ 3,000 ✔ |
| **Instanced assembly** | **55,522** | 30–60k ✔ |

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

- **S0-1:** head L:H is 1.30 against 1.45. Uniform scale was kept; your ruling is pending.
- **S0-2:** the crest blades are lateral in the clay and match the reference at the solved angle. The clay arrangement was kept.
- **S0-3 (new):** segment clay L:D is **0.64 against 0.85** (−24 %, out of band). Uniform scale was kept, so the drums read short and wide.
- **S0-4 (new):** tail torpedo length / base diameter is **1.76 against 2.5–3** (out of band). Uniform scale was kept.

## 7. Self-scorecard (categories 1–4; MATCH / QUALITY, 0–10)

### Category 1: per-feature shape (27 frozen features)

| # | Feature | MATCH | QUALITY | Basis |
|---|---|---|---|---|
| H1 | Skull massing | 6.5 | 6.0 | Clay taper and topline are right; short and tall (S0-1). |
| H2 | Plate breakup | 5.0 | 4.0 | Soft clay plates; no seams cut yet; speckles. |
| H3 | Jaw seam and lower jaw (+ overbite, cheek) | 6.0 | 5.0 | Full-length seam with jaw mass; groove shallow. |
| H4 | Nostril slot | 5.0 | 4.5 | Clay slot present; recess not deepened. |
| H5 | Crest fins ×3 | 6.5 | 5.5 | Three blades match the read; thin. |
| H6 | Eye lens assembly | 6.5 | 6.0 | Modelled rings, cover and recessed blades seated in the clay. |
| H7 | Cheek vent box (vertical slats) | 6.5 | 6.0 | Clay box, frame and vertical slats. |
| H8 | Head piston | 6.0 | 5.5 | Clay rod into the collar. |
| H9 | Inset panels | 4.5 | 4.0 | Window soft; placard and collar vent barely legible. |
| H10 | Collar | 6.0 | 5.0 | Clay stacked collar with top box. |
| H11 | Brow ridge + hood | 6.0 | 5.5 | Ledge lip present (section a); hood mild. |
| H12 | Snout-ridge complex | 5.5 | 5.0 | Clay ridge into the nostril; soft. |
| B1 | Drum massing | 5.0 | 5.0 | L:D 0.64 (S0-3). |
| B2 | Stepped shield plate | 4.0 | 3.5 | Tab and notch soft; no ledge. |
| B3 | Framed grilles ×3 | 1.5 | 1.5 | Not resolved at budget. |
| B4 | Waist band + pistons | 3.5 | 3.0 | Piston masses only. |
| B5 | Bracket blocks | 3.0 | 3.0 | Soft. |
| B6 | Lower plate + recess | 3.0 | 3.0 | Recess not legible. |
| B7 | Fasteners | 1.0 | 1.0 | Absent. |
| B8 | Joint housing ring | 4.0 | 4.0 | Clay ring, soft. |
| B9 | Segmented glow insert | 5.5 | 5.0 | Bars at every joint (clay). |
| B10 | Neck variant | 4.0 | 3.5 | Lapped, enlarged plates; kinks at bends. |
| T1 | Taper segments ×2 | 4.5 | 4.0 | Taper and port present; soft. |
| T2 | Torpedo terminal | 5.0 | 5.0 | Clay form; short (S0-4). |
| T3 | Dorsal fin | 6.0 | 5.5 | Clay fin. |
| T4 | Lateral fin pair | 6.0 | 5.5 | Clay fins. |
| T5 | Tail grille vents | 3.5 | 3.0 | Soft. |

Category-1 medians: **MATCH 5.0 / QUALITY 5.0**. The head items alone have a median of about 6.0 / 5.25.

### Categories 2–4

| # | Category | MATCH | QUALITY |
|---|---|---|---|
| 2 | Silhouette | 6.0 | 5.5 |
| 3 | Massing and composition (pose per §1; neck bend kinks; short drums) | 6.0 | 5.5 |
| 4 | Modelled detail | 3.5 | 3.0 |

**Gate read:** below 7.5 on every category. The head moved the right way: its forms are kept as geometry and visible in captures and sections. The blocking item is the body module (§4 ruling).

## 8. Reproduce

```
blender -b -P source/build_r2.py   -- <clay_dir> <work_dir>
blender -b <work>/snake-v2-r2.blend -P source/render_r2.py -- <work_dir> final r2 full,head,seg
blender -b <blend> -P source/overlay.py  -- SRC_Head <head-closeup.png> <out> source/lm_head.json headbuild <build-log.json>
blender -b <blend> -P source/sections.py -- <hunyuan-head.glb> <build-log.json> <out>
```

- Clay inputs are the hash-verified attempt-1 copies (F10).
- The `.blend` in this folder is `snake-v2-r2.blend`, SHA-256 `2964713b…afcb`. It holds the SRC meshes and the instanced nodes.
- Step-0 evidence is in `r2/step0/`.
