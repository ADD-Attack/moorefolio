# P8 fix round — render-reviewed iteration delivery

## Result

Technical PASS; acceptance NOT READY. This is the requested fixed-build + fresh-preview round, **not a QA clay-gate pass or a production-capture submission**. P7 panel failure remains in force. No material phase advancement.

Candidate: `fix/snake-v2-r2-fix.blend` (P8d). Build sources and cached inputs are committed. The five `fix/previews/fix-p8d-*` PNGs are Cycles GPU **32 spp, 960×540 iteration previews**, denoised. Cameras, lights, catcher, backdrop and clay settings match P7; resolution/sampling intentionally differ from P7's judged captures. One clay material; no emission, glass or bloom. `fix/p8-preview-checks.json` records hashes, dimensions, staging equality and clear full/head background samples. P7 final captures remain historical and are NOT P8 evidence.

Independent saved-blend audit: head **13,968/14,000**, module+insert **1,431/1,450**, tail **2,970/3,000**, assembly **57,006/57,600**. `fix/audit-p8.json`. Counts do not inform the scores below.

## Changes and evidence

- H2: widened/deepened existing traced seams, then flared their cross-sections to create bevel walls; locally relaxed existing plate interiors toward their fitted planes. Skull surface still too soft; the reference has distinct overlapping plate masses, not merely incisions.
- H6: seated the existing machined optical assembly against the CURRENT repaired head, not the old master; broadened the curved disc. Complete concentric disc now reads in the overlay, but reference radial layering remains simplified.
- H12: displaced existing snout ridge vertices locally; no replacement shell. Ridge-to-nostril gesture remains weak.
- H4: enlarged the recess and added surface-fitted machined rim pieces. Rim is visible, but angular and not yet integrated like the reference's formed surround.
- H9: surface-fitted frames around upper/lower existing recesses. Clearer rectangles; collar-top detail still missing/weak.
- H10: locally smoothed existing collar interior vertices, preserving its cut edge. Does not solve the missing stacked plate structure.
- B9: widened existing bars and increased separation/radial exposure, zero additional insert triangles. Segmentation reads in the module view.
- T2: locally refined existing shoulder vertices and cut surface-following beveled terminal seams. Torpedo outline and nozzle retained; still soft and under-plated.
- B10: extended existing neck-plate overlap to .14. Blank underside plate read and gaps remain. Separate `p8-neck-test.blend` rotation experiment was rendered and REJECTED; it is not the delivered candidate.
- B8: increased housing circumferential resolution; reclaimed hidden core-cap triangles. Ring reads more continuously.
- Secondary H3: flared mouth cutter walls; still a shallow line rather than articulated jaw tiers. B3: replaced four parallel slats with four crossed modeled bars per grille at the same triangle allocation. More mesh-like, still sparse.

R24–R33 are recorded in the head/tail build log and sources. Body/eye changes above are also explicit in source diffs. All sculpted work uses the existing formed mesh. Added rods/rings are machined details fitted to measured surfaces.

## Render-only self-review — Decision 36

Viewed in-session: P7 reference side-by-sides and full capture; source REFERENCE.png; P8a/P8b head/full previews; P8c and P8d all five previews; current head/body/tail comparison evidence; all four P8d section plots. Workbench overlays are iteration comparison evidence, not judged captures. Scores below derive from visible renders versus the reference, never budgets, displacement metrics or code parameters.

| Frozen feature | MATCH / QUALITY | Visible finding |
|---|---|---|
| H1 Skull massing | 5.5 / 5.5 | Wedge retained; broad/soft cheek planes |
| H2 Skull plate breakup | 4.5 / 4.5 | More legible cuts, insufficient overlapping plate volume |
| H3 Jaw seam and lower jaw | 4.5 / 4.5 | Continuous line, weak two-tier jaw |
| H4 Nostril/side slot | 4.5 / 4.5 | Visible rim/slot, angular and poorly integrated |
| H5 Crest fins ×3 | 5.5 / 5.5 | Three blades; overlay shows height/outline mismatch |
| H6 Eye lens assembly | 5.0 / 5.5 | Seated disc and rings read; simplified radial layers |
| H7 Cheek vent box | 6.0 / 6.0 | Housing and vertical slats visible |
| H8 Head piston rod | 5.5 / 5.5 | Rod/barrel/collars visible, simple |
| H9 Inset panels | 5.0 / 5.0 | Upper/lower frames clearer; collar-top vent weak |
| H10 Head–neck collar | 4.5 / 4.5 | Still a soft thick collar, not stacked plates |
| H11 Brow-ridge plate | 5.0 / 5.0 | Overhang survives; ridge rolled rather than plate-like |
| H12 Snout-ridge complex | 4.5 / 4.5 | Weak continuous ridge-to-slot gesture |
| B1 Drum massing | 6.0 / 6.0 | Cylindrical drum with faceted plate flats |
| B2 Stepped shield plate | 5.5 / 5.5 | Tab/notch present, reference contour simplified |
| B3 Framed mesh grilles | 5.5 / 5.5 | Crossed bars and deep framed backs; sparse lattice |
| B4 Waist band/twin pistons | 5.5 / 5.5 | Readable but undersized/simplified |
| B5 Centre bracket blocks | 5.5 / 5.5 | Visible paired blocks, blocky |
| B6 Lower plate | 5.5 / 5.5 | Recess present; broad plain plate |
| B7 Fasteners | 6.0 / 5.5 | Repeated modeled bolt heads visible |
| B8 Joint housing ring | 5.5 / 6.0 | Continuous rim, simplified profile |
| B9 Segmented bars | 5.5 / 5.5 | Segmented insert visible; integration still basic |
| B10 Neck read | 5.0 / 4.5 | Overlap improved slightly; blank faces/gaps remain |
| T1 Taper segments | 5.5 / 5.5 | Body plate language continues, coarse transition |
| T2 Torpedo terminal | 5.0 / 5.0 | Elongated tip/nozzle and seams; soft shell |
| T3 Dorsal fin | 5.0 / 5.0 | Swept fin present; outline and edge finish weak |
| T4 Lateral/ventral fin pair | UNREVIEWED as a pair | Near fin visible; far-side paired form not sufficiently exposed |
| T5 Tail grille vents | 5.5 / 5.5 | Upper/side slats present, borders soft |
| Category 2: silhouette | 5.5 / 6.0 | Coil/S-neck recognizable; head fins/neck contour differ |
| Category 3: massing | 5.5 / 5.5 | Coarse masses retained; collar/neck proportions unresolved |
| Category 4: modeled detail | 5.0 / 5.5 | More visible geometric detail, still much simpler than reference |

Unreviewed subforms: hidden eye aperture blades under the opaque clay cover; far-side/internal head detail; concealed joint interiors. No score is inferred for those from source parameters. Categories 5–9 are outside this clay review.

## Open quality work / next approach

No requested low-scoring feature is declared closed merely because it was edited. Priorities remain H2/H6/H12/H4/H9/H10, then B9/T2/B10/B8. The main head problem is plate volume and local shape, not seam darkness. Further depth-only tuning is unlikely to help. Next substantial pass should segment/retopologize the existing formed plate surfaces and recover their distinct planes/overhangs within the same budget; do not replace the head with primitives. A web search of Blender decimation guidance and a reported weighted-border failure informed caution about blindly adding vertex-group protection; no unverified weighting procedure was applied.

Known comparison limitation: inherited segment landmarks predate the drum stretch; its loose registration is indicative only. Head and tail use inherited solved landmarks. Section evidence compares to source clay, NOT the target reference, so preservation is not resemblance.

## Recovery / checkpoint history

P7 baseline 361f26b; P8 inventory 83b2f98; P8a e58e361; P8b 4ba3b6a; P8c 3363388. All pushed. Final P8d continues from these.

Build: Blender 4.5.14 `-b -P source/build_fix.py -- <accepted-clay-dir> fix`.
Preview: open `fix/snake-v2-r2-fix.blend`, run `source/render_fix.py -- fix preview fix-p8d head,full,seg,tail,tail_top fix/captures/fix-p7-render-settings.json`.

Recovered blockers: native Git pointed to an unavailable CA bundle (gateway-managed push succeeded); stale smooth-face metadata on decimated taper caused an IndexError (removed on topology-changing copies; rebuild and independent audit pass). No active execution blocker at delivery.
