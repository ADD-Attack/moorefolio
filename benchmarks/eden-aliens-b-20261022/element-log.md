# element-log — EDEN-3D-01 aliens_b

Engine: ComfyUI 0.41.0, hunyuan_3d_v2.1 fp16, octree 256, 30 steps, cfg 5, surface net threshold 0.6.
Source: crops of aliens-b-3d-reference.png only (bg sampled at (228,228,228)), padded square, resized to 1024. No 2D art fed.

| time CDT | id | crop | seed | action | reason |
|---|---|---|---|---|---|
| 13:32 | — | c3-tail v1 (0,500,330,940) | — | DECLINED crop pre-send | a body/leg mass sat on the right crop edge, which would grow attached anatomy (framing law) |
| 13:33 | — | c3-tail v2 (0,600,262,900) | — | crop accepted for send | single tail unit, clear on all sides |
| 13:37 | c1-wholebody-s42 | c1 (0,20,1420,1168) whole creature, straight-on 3/4 side | 42 | SENT | base-mass candidate: body + plates + legs + tail in one formed mesh |
| 13:37 | c2-mouth-s42 | c2 (1060,250,1420,950) mouth + collar | 42 | SENT | signature feature at higher resolution; needs lip ring + cavity |
| 13:37 | c3-tail-s42 | c3 v2 | 42 | SENT | segmented tail at resolution for ≥3 rigid segments |
| 13:37 | c1-wholebody-s42 (prompt 92f9ec6c) | c1 | 42 | returned 13:40 | 686k tris, closed-reading body |
| 13:40 | c2-mouth-s42 | c2 | 42 | SENT | (c3 send deferred until after the c2 verdict, sequential foreground runs) |
| 13:44 | c1-wholebody-s42 | c1 | 42 | **APPROVED (base mass)** | the 3 dorsal plate bands, the flank plate row, 4 two-part legs and a ringed tail all formed and read right in both previews; the mouth end is shallow → mouth comes from a separate element |
| 13:44 | c2-mouth-s42 (prompt b8c4ec1c) | c2 | 42 | **DECLINED** | an open half-shell with heavy voxel stair-stepping; the cropped body edge became a flat sheet; the lip ring only partly formed |
| 13:44 | c2b-mouth | re-request: wider crop with the whole mouth + collar + a band of forehead, centred | 7 | RE-REQUEST queued | give the encoder a closed volume to read rather than a cut edge |
| 13:45 | c2b-mouth-s7 (prompt 98994a1d) | c2b (880,180,1440,1010) | 7 | **DECLINED** | the crop edge through the body became a flat wall/plane; only a partial head shell formed, and the mouth was not readable |
| 13:46 | c3-tail-s42 (prompt 9b5e0015) | c3 v2 | 42 | **DECLINED** | it formed as a relief sheet with a backing slab, not a volume; the c1 tail already reads as stacked rings |
| 13:47 | c1-wholebody-s42 | — | — | **APPROVED as SOLE source for all nodes** | a 4-side + top sheet (previews/c1-sheet.png) showed a real lip ring and cavity facing +X: the mouth comes from c1, and the separate mouth element is no longer needed. A baked ground slab (z≈-0.53) is stripped in the build |
| 14:06 | c1-wholebody-s42-mc (prompt c25e7a33) | c1 | 42 | SENT (mesher re-request: VoxelToMesh 'basic' instead of 'surface net') | tried to remove the surface-net double-walled seams that leave dark ticks |
| 14:07 | c1-wholebody-s42-mc | c1 | 42 | **DECLINED** | voxel-blocky stair-stepped surface on every form (previews/c1-wholebody-s42-mc-REJECTED.png); surface-net c1 stays |

**Lesson for the series:** part crops of a single creature that cut through the body melt into sheets/walls (c2, c2b, c3). A whole-body straight-on crop gave clean parts, including the mouth.

## FIX PASS (2026-10-22) — Decision 45 STEP 0: capability test

| time CDT | id | source | action | reason |
|---|---|---|---|---|
| 15:37 | gen-rear34-01 | pack aliens-b-3d-reference.png (full image, as the edit reference); model openai/gpt-image-1.5 via image_generate; prompt: "Same creature, same 3D clay-render style, same light grey background and studio lighting. Rotate the camera to a rear three-quarter view (seen from behind-left, tail toward the viewer, mouth facing away). Keep every form identical to the reference: the same plate bands, the same 4 stub legs, and the segmented tapering tail with 6-7 stacked ring segments, clearly visible. Single creature, whole body in frame, no new features." | GENERATED (route works; completed ~16:03) | capability test passed: an in-session, reference-derived generation exists → generated/captest-rear34.png |
| 16:55 | gen-rear34-01 | — | SELF-CHECK vs reference: **PARTIAL DRIFT** | view is rear-side, not a true rear-3/4 (the mouth is still visible at right). The tail is drawn chunkier, with a two-row ring split and a heavy collar at the root, i.e. **more** tail than the reference shows — possible invention. The plate bands and the 4 legs are consistent. Awaiting producer spot-check (Decision 45 condition 2). **Not used in the build** — no GO received; the tail is built from the formed mesh |

## FIX PASS build log (no new Hunyuan calls; all work on approved c1-wholebody-s42, prompt 92f9ec6c)

| time CDT | action | verdict / reason |
|---|---|---|
| 15:38 | retopo: inward solidify 6 mm + voxel remesh 4 mm on c1 | ACCEPTED — manifold (0 boundary / 0 non-manifold, 1.33M tris); closes the open shell that made earlier remeshes collapse |
| 15:40 | drop inner wall (faces >3 mm from the original c1 surface) | ACCEPTED — exterior seam ticks gone in render; it opened the throat back (fixed 15:50) |
| 15:43 | seam deepening ×1.2 (unsharp mask along normals, concave side only) | too weak — re-run |
| 15:46 | seam deepening ×3.0, 40 smoothing iters | DECLINED — amplified surface noise into crumpled seam edges |
| 15:43–15:46 | keep the mouth-zone inner wall to close the throat | DECLINED — read as a convex ball in the throat |
| 15:50 | throat cup: cap the tube-end loop (123 edges), poke the centre back 8 cm; mouth/body cut left uncapped (the nodes abut) | ACCEPTED — deep concave throat, no disc |
| 15:50 | seam deepening ×2.0, 40 iters | ACCEPTED — grooves read; noise acceptable |
| 15:52 | tail ×1.7 thick / ×1.35 long, per-slice in the raw mesh | DECLINED — caught body-rear verts: thin neck + crumpled tip |
| 15:59 | tail per-node scale about each node's own pivot | DECLINED — segments misaligned, gaps |
| 16:03 | tail chain scaled as one unit about tail_01's root | DECLINED — tail_01 stalk stays thin; scaled segments became open tubes (previews/fix-tail-scaling-REJECTED.png) |
| 17:08 | tail = c1 formed tail, unscaled, retopo + ring deepening, budget 1.6k/1.3k/1.0k | ACCEPTED as the deadline-safe fallback — rings and taper read, size unchanged |
| — | gen-rear34-01 | NOT USED — no producer GO arrived before tail time |

## TAIL PASS (Decision 46: on the clay, exaggerated; no Hunyuan, no generated image)

| time CDT | action | verdict / reason |
|---|---|---|
| 17:41 | normal-direction inflate 3 cm + x-stretch ×1.35 pre-cut | partial — thicker and continuous, but no transverse rings |
| 17:43 | carved 6 ring grooves (my arg slip: RD=1.0 m) | DECLINED — exploded geometry (operator error, re-run) |
| 17:45 | 6 rings, normal-direction carve | DECLINED — thin washers + spikes (noisy normals) |
| 17:47 | radial displacement from the per-slice tail axis, 6 rings | partial — clean, but accordion discs; thin stalk at the socket |
| 17:49 | rounded pads, root ramp extended 6 cm into the socket | partial — root flares into the body; still disc-like |
| 17:50 | 5 pillow rings, pad ×0.9, groove 1.1 cm, 3× tail-only smoothing | ACCEPTED shape (previews/tailpass-iteration-5ring.png) |
| 17:56 | exaggeration step-up: 4.5 cm inflate, ×1.5 length, groove 1.3 cm | **ACCEPTED (delivered)** — chunkier and longer, rings read at full-shot distance |

## GATE-RETRY (Decision 46 corrected: the gate stands FAILED; new attempt = exaggerated tail + detail finish). No engine, no generated image.

| time CDT | action | verdict / reason |
|---|---|---|
| 17:58 | tail from TAIL-PASS carried (4.5 cm radial inflate, ×1.5, 5 pillow rings, root collar) | carried |
| 18:01 | detail: denoise the base (4 smoothing iters) before deepening; deepen ×3.0 vs a 60-iter reference | partial — waviness mostly gone, cleaner channels; still soft |
| 18:04 | deepen ×4.5 vs an 80-iter reference | DECLINED — the throat reads as a convex ball; folds/specks on the deepest dorsal seam (previews/gateretry-deep4.5-throat-ball-REJECTED.png) |
| 18:07 | ×4.0, throat-cup verts excluded from deepening | DECLINED — throat still ball-like (the tube widened around the cup) |
| 18:10 | ×4.0 body; mouth zone (x>0.15) at 0.7× (=2.8); cup pushed back 12 cm | **ACCEPTED (delivered)** — deep throat restored, body grooves at full strength |

## GATE-RETRY v2 — operative method (Muse 2nd correction: "engine" = Blender; tail via REGENERATED REFERENCE → Hunyuan; Blender only for the stitch). Supersedes the hand-modelled tail of a834870.

| time CDT | id | source / params | action | reason |
|---|---|---|---|---|
| 18:13 | gen-tail-ref-01 | edit of pack aliens-b-3d-reference.png; model openai/gpt-image-1.5 (image_generate); prompt: "Using this creature as the reference, show ONLY its tail as a single isolated object… pure side view… Exaggerate the tail: much bigger and thicker…, 6 stacked rounded pillow-like ring segments separated by deep, sharp grooves…, curving slightly upward toward a rounded tip. The wide root end is cut flat where it would join the body…" → generated/gen-tail-ref-01.png | GENERATED | fence 1 (reference-derived), fence 4 (whole unit from a missing view: an isolated tail is not visible in the pack) |
| 18:18 | gen-tail-ref-01 | self-check vs the pack reference | **APPROVED as Hunyuan input** | same material/style; tapering ringed tail with an upturned tip, as in the reference, exaggerated per order. Noted simplification: single-row rings (the reference pads split into two rows). Never used as ground truth (fence 2) |
| 18:18 | c4-gentail-s42 (prompt 72328b2e) | gen-tail-ref-01 padded square, bg (228,227,227) | SENT → **DECLINED** | the tail formed well (6 rings, round section) but fused with a ground slab and a diagonal sheet grown from the drop shadow / bg gradient |
| 18:24 | c4b-gentail-s42 (prompt 7e640c0c) | gen-tail-ref-01 masked by saturation (>70), shadow/gradient flattened to (228,228,228), padded | SENT → **APPROVED** | clean closed volume: 6 pronounced rings, round section, flat circular root cap, upturned tip; no slab, no melt (previews/c4b-gentail-s42-APPROVED.png) |
| 18:28 | stitch v1 | LEN 0.38, collapse-decimated raw element | **DECLINED** | the surface-net shell shattered into facets under 97% decimation |
| 18:31 | stitch v2 | + voxel remesh 2.5 mm (manifold: 0 boundary / 0 non-manifold) before decimation, LEN 0.42 | partial | clean rings and taper, but slender vs the reference's chunky tail |
| 18:33 | stitch v3 | + ×1.45 thickness about the element axis (pre-cut, so the chain stays aligned) | **ACCEPTED (delivered)** | chunky, 6 pronounced pillow rings, curled tip, seated 3 cm into the socket |
| 18:35 | verify | per-node POSITION buffer hash vs bace685 GLB | PASS | body, mouth and leg_FL/FR/BL/BR byte-identical; only tail_01..03 differ |

## MATERIAL PHASE (2026-10-22)
| time CDT | action | verdict / reason |
|---|---|---|
| 19:27 | palette sampled from the 2D master + pack ref | the dispatch palette (near-black plates, cream belly, glowing mouth) conflicts with both images → built to the images; pushback in STATUS |
| 19:29 | pass 1 (1K) | DECLINED — the mouth blew out yellow (emission 3.0 over the whole cavity); the body read salmon |
| 19:33 | pass 2 (1K) | partial — dark maroon interior + deep-throat ember OK; sheen still pinkish |
| 19:36 | pass 3 (2K, specular 0.3) | partial — saturated ember; the lower-body gradient was weaker than the refs |
| 19:43 | pass 4 (2K, stronger red-orange underside band) | **ACCEPTED (delivered)** |
| — | generated images | none used in the material phase |

## STITCH-BLEND (owner-directed, post-gate, 2026-10-22). Same Hunyuan tail element c4b (prompt 7e640c0c); no new generation.
| time CDT | variant (stitch.py args) | verdict / reason |
|---|---|---|
| 20:05 | −10% (LEN 0.378), flare 4 cm / 6 cm zone + conform-to-body | DECLINED — lampshade collar, spike streak; old c1 stalk visible |
| 20:07 | flare 3.5 cm / 12 cm, no conform, seat 6 cm | partial — smoother; rim and stalk still visible |
| 20:09 | flare 5.5 cm / 15 cm, seat 8 cm | partial — stalk buried; trumpet rim protrudes at the rear-bottom |
| 20:11 | + conform outside root verts onto the body | DECLINED — crumpled facets (unstable nearest-point snaps) |
| 20:13 | flare 4.5 cm / 15 cm, **saturating at the body surface**, seat 8 cm, z −0.18 | **ACCEPTED** — the tail swells out of the rear mass with no cork step in the full view; small residual rim at the low close-up |
| 20:15 | verify: per-node POSITION hash vs the 2c25df3 GLB | PASS — body, mouth, 4 legs byte-identical; only tail_01..03 differ |

## MATERIALS (final, blended base 98a44eb) — 2026-10-22 20:46
| action | verdict / reason |
|---|---|
| re-bake mat.py (pass-4 settings, unchanged) on 98a44eb geometry; base hash verified; GEOMETRY_FROZEN True | ACCEPTED — the finish sits on the re-seated tail and skirt; map sizes consistent with the prior bake |
| generated images | none used |

## STITCH-REGEN attempt 2 (owner override, 2026-10-22 20:52–21:08). Base = bace685 body; tail re-installed from a fresh element; seat + cut only.
| time CDT | id | source / params | action | reason |
|---|---|---|---|---|
| 20:52 | gen-tailroot-c1/c2/c3 | 3 edits of the pack aliens-b-3d-reference.png, openai/gpt-image-1.5; prompt: rear-end close-up, tail + margin of the rear-body contour, "two rows of lumpy rounded pads (an upper row and a lower row…, as in the reference)", bigger/thicker, root flows out of the body, no collar/ring/step, no ground shadow | GENERATED ×3 | fences 1/4; anatomy per the reference |
| 20:55 | c1 | self-check | DECLINED | a dorsal plate bulges over the root and would fuse into the element |
| 20:55 | c3 | self-check | DECLINED | best pads, but a leg bulge at the right crop edge would grow as attached anatomy |
| 20:55 | c2 | self-check | **APPROVED** | cleanest organic root flow; two-row lumpy pads like the reference |
| 20:56 | c5-tailroot-s42 (prompt a65d389d) | c2, saturation-masked to flat bg 228, padded | SENT → **APPROVED** | clean closed volume: Hunyuan closed the cropped margin into a small rear-body blob with the tail growing out of it; two-row pads and the transition are formed in the element; no melt/slabs |
| 21:02 | seat A | S 0.40, transition at (−0.58,−0.20), blob cut at element x +0.10 | **FAIL** | the element's blob pokes out of our body: open dark cavity at the rear + blob plate fragments as an extra hump |
| 21:05 | seat B | S 0.44, transition at −0.53, cut at element x −0.05 | **FAIL** | a dark gap at the top of the root (the open cut exposed where our rear recedes) + a plate-edge rim on the transition top |
| 21:08 | seat C | S 0.46, transition at −0.48, cut at element x −0.12 | **FAIL** | smaller, but a dark slit still shows at the top of the root in the full view, and the transition edge reads as a rim in the close-up |
| 21:08 | — | — | STOP per order item 6 | the element cannot seat without a visible lip/gap; no further seat fix invented |

## RESTRUCTURE attempt 2 — STEP 1 (step-gated walkthrough, owner direction 20:51 CDT; the order reached me at ~21:10)
Source for all three: edit of the pack aliens-b-3d-reference.png (never from scratch). Model: openai/gpt-image-1.5 (image_generate), one request, count 3, generated 20:52 CDT.
Prompt: "Edit of this exact creature, same 3D clay-render style, same smooth orange material, same light grey plain background, same soft studio lighting. Show a close-up, straight-on side view of ONLY the rear end: the tail together with the rounded rear part of the body it grows out of (include a margin of the rear body contour around the tail root so the transition from body to tail is clearly visible and continuous). Keep the tail's anatomy exactly as in the reference: two rows of lumpy rounded pads (an upper row and a lower row of segments, as in the reference), tapering and curving slightly upward to a rounded tip, but make the tail a bit bigger and thicker with the pad grooves pronounced and readable. The tail root must flow organically out of the body with no collar, no ring, no step. No legs, no mouth, no front of the creature; plain background, no shadow on the ground, single object."

| file | my verdict (one line) |
|---|---|
| generated/gen-tail2-cand-01.png | Two-row pads read well, but a large dorsal plate bulges down over the tail root and would fuse into the element. |
| generated/gen-tail2-cand-02.png | **My pick:** the cleanest organic root flow out of the rear body; two-row lumpy pads; the body runs off the right edge (a margin to discard). |
| generated/gen-tail2-cand-03.png | Best-defined pads and a deep groove line, but a leg bulge sits at the lower-right crop edge (attached-anatomy risk). |

Disclosure: before this step-gated order reached me, I had already run cand-02 through prep + Hunyuan + three seat tests under the earlier attempt-2 order. All three seats failed acceptance (record: stitch-regen-attempt2-FAILED/, d9cc3e6). Those results are **not** acted on; they are archived and await the owner's pick and the producer's step-2 go like everything else.

## STEP 1 AMENDED (owner ruling 20:57: the feed image must be a CROP of the reference). The edit-based candidates are moved to generated/superseded-edits/gen-tail2-edit-0N.png (not candidates).
All three: source = pack aliens-b-3d-reference.png (1840×1168), **reference pixels only**, padded to a square with flat colour sampled from each crop's own top-left background pixel (228,228,228), +40 px canvas margin. **No generation, no outpainting, no redraw, no smoothing.** Regions: the crop rectangle = reference; everything outside it = flat padding.

| file | crop box (x0,y0,x1,y1) | canvas / paste offset | my verdict |
|---|---|---|---|
| generated/gen-tail2-cand-01.png | (0,600,355,920) — tight: whole tail + thin rear-body margin, stopping just before the hind-leg pad | 395² / (20,37) | Cleanest tail read with no leg occlusion. The transition margin is thin and the body is hard-cut at the right/top edges (melt/wall risk, in the discard zone). |
| generated/gen-tail2-cand-02.png | (0,560,420,960) — medium: tail + root transition + more rear body | 460² / (20,30) | **My pick:** the most root transition in frame. The hind-leg shoulder pad intrudes at the lower right (attached-anatomy risk); body hard-cut at the right edge. |
| generated/gen-tail2-cand-03.png | (0,420,520,1000) — wide: adds the plate overhang above the root and the hind-leg pad/leg | 620² / (50,20) | Most context, but the leg and plate overhang occlude/compete with the root and would likely fuse into the element. |

## STEP 1 FINAL FORM (owner 20:58: strike the margins clause; zero generated pixels and no canvas extension)
gen-tail2-cand-01/02/03.png are re-saved as **bare crop rectangles**: identical reference pixels, no padding. Boxes are unchanged: 01 (0,600,355,920) 355×320 · 02 (0,560,420,960) 420×400 · 03 (0,420,520,1000) 520×580. Squaring/padding and any background flattening move to the separately gated PREP step. Verdicts unchanged (pick: cand-02; concerns as in STATUS).

## ATTEMPT 2 — FEED IMAGE SELECTED (21:02 CDT, before any Hunyuan run)
**SELECTED: generated/gen-tail2-cand-02.png — pure crop (0,560,420,960) of the pack aliens-b-3d-reference.png, 420×400, zero generated pixels.**
Reason: the most root transition in frame. The hind-leg pad sits in the body margin, which lands inside our body after seating and is discarded at the seat cut.

## ATTEMPT 2 (pure crop) — PREP → HUNYUAN → STITCH (21:03–21:31 CDT)
| time | id | params | action | reason |
|---|---|---|---|---|
| 21:05 | prep c6-tail2-prep.png | gen-tail2-cand-02 → saturation mask (>70) → bg flattened to (228,228,228) → square pad ×1.12 → 1024² (non-generative) | DONE | removes shadow/gradient (slab prevention); tail pixels unchanged |
| 21:20 | c6-tail2-s42 (prompt c539b9c5-cd39-446b-a4b3-8fcf43e7e1db, seed 42) | fp16 v2.1, octree 256, surface net 0.6 | **APPROVED (tail portion)** | two-row lumpy pads formed from the real reference tail; the body-margin end grew a crumpled blob with the fused leg pad (crop-edge effect), which is discarded at the seat cut; the tail axis is yawed −45° (the reference's 3/4 view) |
| 21:23 | seat 1 | yaw +44.9°, stretch 1.45 (undo 3/4 foreshortening), S 0.27, root at (−0.50,−0.19), blob cut at element x −0.30 | partial | no lip; tail too stubby |
| 21:26 | seat 2 | S 0.32, stretch 1.5, z −0.18 | **FAIL (close)** | the zoom shows a small dark slit between the top of the root and the plate overhang |
| 21:29 | seat 3 | root 3 cm deeper (−0.47) and 1 cm higher (−0.17) | **PASS → delivered** | no lip/rim/gap in the tail close-up, the full compare or the root zoom |
| 21:31 | verify | per-node POSITION hash vs the bace685 GLB | PASS | body, mouth, 4 legs byte-identical; only tail_01..03 differ |

## OWNER PROCESS (21:15 CDT): crop → edit the CROP → 3Dify the edit. Applied as v3.
**Archived as INELIGIBLE feeds under this process** (wrong input): generated/gen-tail2-cand-01/02/03.png (bare crops, no edit) and generated/superseded-edits/gen-tail2-edit-0N.png (whole-image edits). The 3af2f2a STITCH-REGEN (from bare crop cand-02) is superseded by this process.

| time | file | detail |
|---|---|---|
| 21:32 | **generated/tail3-crop.png** | pure crop of the pack aliens-b-3d-reference.png, box (0,560,420,960), 420×400: tail + rear-body margin (+ hind-leg pad at lower right) |
| 21:33 | **generated/tail3-edit.png** | image edit run ON THE CROP. Model openai/gpt-image-1.5 (image_generate), count 1. **Exact prompt:** "Edit this cropped image. Keep this exact tail — same two rows of lumpy rounded pads, same number of segments, same orange clay material, same soft studio lighting — and show it in a pure side view (tail running horizontally from the body on the right to the tip on the left, not angled toward the camera), so its full length and the upward curve to the rounded tip are visible. Keep the rounded rear body on the right that the tail grows out of, and complete its contour smoothly where the crop cuts it off. Remove the leg at the lower right. Plain flat light grey background, no ground shadow, nothing else in the frame." |
| 21:33 | tail3-edit self-check | **ACCEPTED as feed.** Same two-row lumpy pads, now true side view with full length and an upturned rounded tip (fixes the 3/4 foreshortening behind the stubby v2 tail); leg removed; rear body completed as a smooth bulb (still cut at the right frame edge, in the discard zone). Pad count reads as ~5 upper / 4 lower vs the crop's ~5/5: minor. |
