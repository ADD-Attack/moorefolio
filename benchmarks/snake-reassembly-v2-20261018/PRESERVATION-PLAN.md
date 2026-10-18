# PRESERVATION-PLAN — snake-reassembly ATTEMPT 2, Round 1

How each section is derived FROM the formed clay mesh under the Construction Rule (Decision 35). Tooling: Windows Blender 4.5.14 headless, driven by scripts kept in `source/`. Every geometric step is a script, so it is reproducible and auditable.

## 0. Principles that apply to every section

1. **Two meshes per section.**
   - The **form master**: the cut, cleaned clay at high density. It is never edited by hand.
   - The **build mesh**: the in-budget retopo, refined and detailed.
   - Every build-mesh vertex comes from the form-master surface: by shrinkwrap/projection, by an edit logged as a *refine*, or by a rule-2 machined part.
   - No vertex position comes from a template, a station table, or a bounding statistic. That is the specific failure of attempt 1.
2. **Cleaning keeps the form.**
   - Specks: delete small islands.
   - Non-manifold: voxel remesh of the master at ≤0.2 % of section length.
   - The remesh is accepted only if the Hausdorff deviation to the raw clay is ≤0.15 % of section length (p99) **and** the three section profiles (§H.4) overlay within the line width.
   - If it fails, I lower the voxel size. Never smooth.
3. **"Refine" means local edits to the formed surface.** These are scripted proportional moves, crease or cut along the clay's own feature curves, and solidify of the clay's own faces.
   - Every refine is named, scoped by vertex group, and logged with a before/after section image.
   - Refines exist only to push a form the clay already has toward the reference. They cannot invent a form. If a form is absent from the clay, I flag it to the producer before modelling it.
4. **Retopo keeps local forms by construction.**
   - Edge flow is placed ON the clay's feature curves (brow lip, ridge crest, mouth seam, nostril rim, plate steps) before reduction.
   - Those curves are traced from the master as crease/high-curvature edges and given vertex-group density weight.
   - Reduction is then weighted collapse (feature groups locked or down-weighted), followed by shrinkwrap back onto the master.
   - The QA gate on the build mesh: Hausdorff to the master inside each form's vertex group is ≤0.4 % of section length (p95). Every named form must survive the section-profile overlay.
5. **Plates are cut INTO the formed surface.** Seams are knife-projected/boolean-grooved along curves on the master surface, using the reference plate layout projected at the close-up camera. Plate edges are then bevelled. Plates are never offset shells of an invented surface.
6. **Clay-gate purity** (rule 5). One neutral clay material on everything in the R2 gate captures. The eye, glow inserts and lens are built as geometry and rendered clay.
7. **Same-angle comparison is a gate, not a courtesy** (rule 4). Each section gets a camera solved to its close-up from landmarks. I render a Workbench silhouette and profile overlay of the master (baseline) and the build mesh at that camera, and view them in-session before any checkpoint.

## H. Head (budget per F8 ruling: 10–14k recommended, 18k max)

**H.0 Baseline audit (first R2 step, before any edit).** Import the raw head clay, then cut it (H.1).
- Solve the close-up camera from 4 landmarks: eye centre (331,292), snout tip (≈68,380), the middle fin root and fin tip, and the vent-box rear (≈550,290).
- Render the clay silhouette and an edge overlay against `head-closeup.png`.
- Measure skull L:H (F9) and plan taper (tip width / eye-line width, target ≈0.5).
- Record per form F-a…F-n (SPEC-CONFIRM §2): present, weak or absent.
- This verifies, on the mesh, the addendum's claim that the clay "already carries these forms" before I depend on it. Any *absent* form goes to the producer immediately (lane rule 5).

**H.1 Cuts.**
- (1) Collar plane: the plane perpendicular to the head axis just aft of the clay collar's last plate ring, in the gap before the first neck segment. Everything aft is discarded (attempt-1 ruling). H10 is kept from the clay.
- (2) Delete the 2 specks.
- (3) Cap the collar cut with a flat ring face. It is hidden by the first segment's housing.

**H.2 Form master.** Voxel remesh per §0.2, then the acceptance check. Then uniform scale to head H = 1.2–1.4 D (P3). Non-uniform scale is not allowed (F9).

**H.3 Refines, each a logged local edit of the clay surface:**

| Form | Refine on the formed mesh | How it survives |
|---|---|---|
| F-b eye-brow ledge | Select the clay brow-roll lower band (curvature trace + vertex group). Translate it outward along the local normal and down over the socket until the lip projects past the socket rim. Use the depth read from the close-up shadow line. Crease the lip edge. | The lip edge is a locked retopo loop. The section through the eye centre must show an undercut. |
| F-c forehead hood | Same treatment on the forward brow swell. Its lower edge becomes a creased lip over the snout top. | Locked loop; checked in the mid-snout section. |
| F-a taper | Only if H.0 shows the plan taper is short of ≈0.5: proportional pull-in of the snout flank vertices with falloff from the eye line. The topline stays clay. | Plan-view overlay vs H.0 measure. |
| F-d snout ridge | Trace the clay ridge crest from under the eye to the nostril. Sharpen it with a crest crease and a small outward normal move along the trace. | The crest is a locked loop continuous into the nostril rim. |
| F-e nostril | Extend the clay's nostril pit along the ridge direction to ≈0.12 head-length as a capsule. The cutter's end-caps are the only parametric element and are placed on the clay surface. The floor depth is ≥ the slot width. The clay surround becomes the dished recess, lowered by a proportional push inside the ridge rim. | Rim loop locked; the slot is a real hole, not a decal. |
| F-f mouth seam | Keep the clay seam path. Smooth only the tooth serration (Laplacian on the seam's lip vertex group, restricted to along-seam). Then deepen the groove by a normal push of the seam floor so it reads dark at the staging angle. | The seam floor and both lips are locked loops for its full length. |
| F-g / F-h jaw, overbite | Keep the clay jaw mass. If H.0 shows the overbite missing, push the jaw-front vertices back under the nose cap. | Jaw underside profile overlay. |
| F-i cheek | Clay as-is. | — |
| F-k fins | Solidify the clay fin faces to the reference thickness and re-shrinkwrap the sides. The clay outline is kept. | Fin silhouettes in the overlay. |
| D-H2 bulbous underside | Planar-flatten the snout-underside vertex group toward the reference's squared underside, plane fitted to the clay's own flattest underside patch. | Jaw underside profile. |

**H.4 Section profiles (the survival test).** Three planar sections through the master and the build mesh, overlaid as line plots:
- (a) a vertical section through the eye centre: brow undercut, mouth seam groove, jaw tiers;
- (b) a vertical section at mid-snout: hood lip, ridge crests, seam;
- (c) a horizontal section at nostril height: plan taper, nostril depth.

These plots, plus the same-angle overlay, go into NOTE.md for the owner and the panel.

**H.5 Retopo.**
1. Feature-curve loops (§0.4): brow lip, hood lip, both ridge crests, nostril rim, mouth seam lips and floor, jaw tier steps, eye socket ring, vent-box frame, fin roots, collar rings.
2. Weighted collapse to the budget.
3. Shrinkwrap (nearest surface point) to the master, with locked loops excluded and re-snapped to their traced curves.
4. Run the §0.4 Hausdorff gate.

**H.6 Plates and detail cut INTO the build mesh.**
- Plate seams follow the reference layout (12–16 per side, H2), projected through the solved camera onto the surface. Cut as grooves with bevelled and chipped edges.
- The snout-top plate step is cut on the clay surface.
- H9 frames are raised-frame/recessed-floor cuts at their positions, per F5.
- H7 slats: vertical, per F1.

**Legitimately parametric in the head (rule 2, machined, fitted to measured clay):**
- the H6 lens rings, bezel, blades and cover, fitted to the clay eye-ring radius and seated on its disc plane;
- the H8 piston, fitted to the clay rod's axis and diameter;
- the H7 slats inside the clay box recess (the box housing stays clay);
- the bolts and rivets (H2), instanced on the surface.

## S. Hero segment (B1–B9; target ≤1,450 incl. insert per F8)

**S.1 Cuts.**
- Keep component A only. Component B and the 5 specks are discarded (attempt-1 ruling).
- Plane-cut A at its +X housing-ring face, which removes the fused melted neighbour (D-S1).
- Delete the drip spike (D-S2). It is a melt artefact, not a form: faces below the lower plate's envelope, by connected selection from the spike tip.

**S.2 Form master.** Voxel remesh per §0.2. Measure the clay's own L:D, then uniform scale to D (target L:D ≈0.85). If off by more than ±8 %, report it per F9.

**S.3 Retopo.**
- The clay drum is mapped to (u = around, v = axial).
- The plate step edges are traced as radial-height discontinuities ON the clay: top tab, notch diagonal, ledge, waist band edges, bracket blocks, lower plate edges.
- Edge loops are placed on those traces, never on a template grid. The remaining verts are distributed between them.
- Every vertex is projected radially onto the master, so tab height, step depth and ledge overhang are the clay's own heights.
- The lower-plate recess (B6) comes from the clay recess.

**Legitimately parametric (rule 2, machined, fitted to measured clay):**
- the B8 housing ring, fitted to the clean −X end's measured ring OD and lip;
- the B9 segmented bar insert (separate mesh), fitted inside the housing;
- the B4 pistons, fitted to the clay piston axes and lengths;
- the B3 grille frames, as recessed frames cut at the clay window/slot positions, with a recessed backplate and weave as micro-detail normal (P5);
- the B7 bolts, as instanced low-poly at the clay's plate corners.

**Survival test.**
- Same-angle overlay against `segment2-closeup.png` with a solved side camera.
- Two sections, through the tab/notch and through the waist band, master vs build.

## N. Neck variant (B10, ≤ module budget, ~6 instances)

Derived from the **hero build mesh** of S, so it inherits the clay-derived drum and plates. The heavier collar plates are made by:
- enlarging the clay-derived upper shield and lower plate faces along u (extending their own curvature);
- solidifying them thicker with an overlap lip onto the next joint.

The lit joint then reads as a partial arc, which is the reference read (§3). The plates are armour panels on a machined drum, so this extension falls under rule 2. No new invented surface is introduced.

*Option for the producer:* the head clay's first neck segment behind the collar is the least-melted of the discarded neck run and shows the overlapping collar-plate language. Attempt 1's ruling discarded it. If the producer prefers, I can use it as the form master for B10 instead. Recommendation: the hero-derived path, because it gives a cleaner instance match.

## T. Tail (T1–T5; ≤3,000 incl. insert)

**T.1 Cuts.**
- Delete the fused ground slab (D-T1): faces whose normals and plane fit the slab, by connected planar selection.
- Delete the speck.
- Plane-cut at the finned tip's base, where the torpedo body meets the last melted segment, and keep the tip. The melted taper segments are discarded (attempt-1 ruling).

**T.2 Terminal (T2–T5) from clay.**
- Voxel-remesh master (§0.2), uniform scale to base ≈0.45–0.55 D.
- Retopo the torpedo body with loops on its traced plate seams, projected onto the master.
- The fins (T3 dorsal with the notched trailing edge, T4 pair) are retopo of the clay fin outlines. The notch is a locked loop. They are solidified to the reference thickness.
- T5 vents: slats cut into the clay's existing grille-relief positions (about 7 slats upper, a small nose vent).

**Legitimately parametric:** the nozzle hole (machined bore, fitted to the clay tip), the slats, and the rivets.

**T.3 Taper segments ×2 (T1)** are derived from the S hero build mesh (approved ruling).
- They are scaled down step-wise toward the terminal base diameter, which is measured on the cut clay tip.
- The taper ratio and the curvature path come from the tail clay's own run.
- One carries the circular port fitting (machined, parametric).
- The last glow insert sits at the start of the taper.

**Survival test.** Same-angle overlay against `tail-closeup.png`, plus fin outline overlays.

## A. Assembly and gate captures (R2)

- About 28 rigid segment nodes posed per §1, with the monolith as pose reference only. Inserts sit at every joint as separate geometry.
- Gate captures: Cycles production settings, #C1C1BF plus shadow-catcher, shaped neutral light, ONE clay material on everything, no emissive and no bloom.
- Each capture is paired with the same-angle overlays and the §H.4 section plots.
- NOTE.md is built for two readers, owner and panel. It carries:
  - captures, overlays and section plots inline;
  - the 27-feature MATCH+QUALITY self-scorecard (categories 1–4 at R2);
  - the refine log;
  - budgets;
  - every deviation and open flag.
- If my own scores flag a fixable form, I fix it before the checkpoint. I do not push a known gap (attempt-1 lesson).

## Order of R2 work (blockers surface first)

1. H.0 baseline audit, plus the S.1/T.1 cuts and masters. Any *absent* form or out-of-band ratio goes to the producer immediately.
2. Head refines, sections, retopo, plates.
3. Hero → neck → tail.
4. Assembly, overlays, self-scores, NOTE, checkpoint.

Recoverable `.blend` checkpoints are saved after each section's master and each section's retopo.
