# REFERENCE-SPEC — snake-reassembly-20261018 (Round 1)

Forge seat (`studio-3d`), Opus 5.5. Written 2026-10-18 from `REFERENCE.png` (1920×1280) and the three close-ups, all viewed in-session. Every claim here comes from the images. Pixel numbers come from `source/inspect_r1.py` and `source/eye_r1.py` (Blender-Python pixel sampling; these scripts are in the ticket workspace and were not pushed in Round 1), or from direct reads of the image. **px** = reference-image pixels; **D** = body-segment armour diameter.

Pack verified: zip SHA-256 `e1def3e5…6a7f` OK, and all 6 files match MANIFEST.md (`sha256sum -c`: 6/6 OK).

---

## 0. Staging read (for judged captures)

| Item | Read | Evidence |
|---|---|---|
| Backdrop | Plain, very slightly warm light grey: **#C2C3C0** at the top corners, **#BEBEBC to #BFBFBE** at the bottom corners (a faint vertical gradient). Use **#C1C1BF**. | Corner medians of 40×40 px: (194,195,192) ×2 top, (191,191,190) and (190,190,188) bottom. This confirms seat rule 2. Note: `REVIEW-STAGING.md` says "plain mid-gray". The later owner rule (sampled reference colour) supersedes that wording; see pushback P1. |
| Floor | No visible floor plane. There is a soft, wide contact shadow under the coil (darker grey, diffuse edge, densest under the front coil around y≈1150 to 1200). | Rows 1020 to 1180 read as foreground across the full width (shadow darkening), and no edge or horizon line is visible. |
| Camera | Elevated three-quarter view, about 20–25° looking down. The head is in left profile with the snout pointing −X (screen-left). Perspective is mild: the front coil reads larger than the back coil, about 330 px vs 240 px segment height. | Shape of the coil ellipse and the relative segment heights. |
| Light | A soft key from upper-left/front, with broad specular sheen on the top plates. The neck's camera-right side is darker. A soft fill keeps the recesses readable. No hard cast shadows on the body. | Highlights on the skull top, plate tops and coil tops. Shadow side on the neck's right. |
| Glow | Emissives have a tight, subtle bloom: a short halo around the eye and around the ring bars, with no wide haze. | The eye halo extends about 10 px past the lit core. |

## 1. Global proportions and pose

- **Silhouette extents (px):** snout tip x≈88 (y≈380). Coil right edge x≈1865 (y≈980). Crest-fin tips y≈34. Coil bottom y≈1195. Tail tip x≈1280, y≈1180.
- **Pose (left to right in screen space):** the head is held high at upper-left, snout forward-left and very slightly down (the skull top slopes about 10° down toward the snout). Behind the head, the neck makes a **raised S-curve**. It arches up and back from the head (x≈560 to 900, y≈150 to 450), then drops nearly vertically into the centre of the coil (x≈640 to 900, y≈450 to 850).
- **Ground coil:** one closed ground loop around the neck's base. The front run passes left-to-right across the foreground (x≈120 to 1320, y≈820 to 1195). The back run passes behind the neck (y≈600 to 830). The loop is a wide ellipse, about 1700 px across on screen.
- **Tail:** leaves the coil at the far right (x≈1860). It sweeps toward the camera and **curls back to the left**, finishing in the finned tip. The tip points screen-left and slightly toward the viewer (x≈1280, y≈1180). The tail lies on the ground plane.
- **Joint count:** about 24 lit joints are visible. With the hidden back of the coil, a ~28-segment body is consistent with the image, and with the brief.
- **Diameter:** body diameter stays roughly constant from the neck to the start of the tail. The neck is about 250 px at mid-height, versus about 330 px on the front coil (perspective). The body does not visibly fatten in the coil. The taper starts only at the last 2–3 segments before the finned tip.

## 2. Head (head-closeup.png, 941×679; cross-checked on REFERENCE.png)

Proportions in close-up px:

| Measure | Value | Ratio |
|---|---|---|
| Head length, snout tip to the rear of the vent box/collar | ≈ 490 px (x 68 to 560) | — |
| Skull height, crown to jaw underside, excluding fins | ≈ 340 px (y 130 to 470) | L:H ≈ **1.45** |
| Eye centre | (331, 292); REFERENCE (349, 319). The close-up is ≈1:1 with REFERENCE, so the radial profiles match. | 53 % back from the snout tip, 47 % down from the crown |
| Eye lit-disc diameter | ≈ 70 px (lit to r≈35) | ≈ 0.21 H |
| Eye full assembly, outer metal ring | ≈ 110–120 px (r≈55–60) | ≈ 0.34 H |
| Crest fins | 3 blades, roots x≈250 to 505, tips up to y≈15 | fin height ≈ 0.30–0.35 H above the crown |
| Head height vs body D | head H ≈ 1.2–1.4 × D | — |

Feature reads:
- **Skull massing:** boxy and elongated, built from flat-faceted plates, not a rounded reptile dome. Planes: a broad flat crown; a steep flat cheek/side plane; a chamfered brow edge between them. The snout is **blunt and squared**, with a slightly rounded nose plate. It narrows only modestly toward the tip.
- **Plate breakup:** many overlapping armour plates (about 12–16 visible on the left side). Seams are deep and dark. Plates have bevelled, chipped edges, and round-head rivets/bolts sit at plate corners. One plate step crosses the snout top behind the nose.
- **Mouth/jaw:** a closed mouth. A horizontal jaw seam runs from the snout tip back under the eye, separating a lower jaw plate (two plate tiers) from the upper skull. The **nostril/side slot** is a dark, rounded horizontal slit on the snout side, about 60 px long, at about x 140 to 200, y≈365.
- **Eye (target of the modelled lens):** sits flush to slightly proud of the cheek plate, inside a circular plate cut-out. The radial median profile (source/eye_r1.py, REFERENCE and close-up agree within a few levels) reads, centre outward:

  | Radius (px) | Colour | Read |
  |---|---|---|
  | r 0–10 | #F8FDFF | white-hot core, ≈ 20 px diameter, ≈ 28 % of the lit disc |
  | r 10–20 | #C9FAF4 → #9EE6DA | pale mint |
  | r 20–25 | #60C4B0 | teal |
  | r 25–35 | #0C8B6C → #08624A | saturated deep green-teal (the lit-disc rim) |
  | r 35–45 | #31503F → #1D342A | dark, green-tinted bezel, carrying glow spill |
  | r 45–50 | #454F44 | a lighter thin **concentric ring** (machined lip) |
  | r 50–55 | #112016 | a very dark groove |
  | r 55–70 | #3B3730 → #49483F | the metal housing ring blending into the cheek plate |

  A glossy cover reads as a soft bright specular arc on the upper-left of the disc. **Aperture blades are not legible at reference resolution.** Inside r≈35 the core reads as a smooth radial glow. See pushback P2.
- **Cheek vent box ("ear"):** behind the eye at x≈455 to 550, y≈235 to 340 in the close-up. A chunky rectangular housing with rounded corners, a raised frame and about 6 horizontal grille slats. A **piston/rod** runs back from it into the neck collar (x≈550 to 600, y≈290).
- **Inset details:** a small rectangular window/slot panel on the upper rear skull, above and behind the eye (x≈455 to 505, y≈200 to 225). A small rectangular placard/label plate below and behind the eye (x≈420 to 470, y≈370 to 395). A small vent with 3 to 4 slots on the collar top (x≈560, y≈150).
- **Crest:** three **swept-back blade fins** in a row along the dorsal centreline over the rear skull. Each fin has a straight, steep raked leading edge and a flat-ish top. Each fin has a riveted root plate and a darker inner face. All three are about the same height; the middle one is marginally tallest. The fins are parallel, evenly spaced, and lean back about 30–35° from vertical.
- **Collar:** a stacked, multi-plate collar joins the head to the first neck segment, with a vent and a small boxed fitting on top.

## 3. Body segment (segment2-closeup.png, 844×690)

| Measure | Value |
|---|---|
| Armour drum length (plate span) : diameter | ≈ 450 : 525 px → **L:D ≈ 0.85** |
| Joint-ring band (lit bars) axial width | ≈ 45–55 px → ≈ **0.10 D** |
| Housing ring outer diameter | ≈ 0.80–0.90 D. It sits recessed inside the armour plates' silhouette. |
| Gap between consecutive armour drums | ≈ 0.15–0.20 D. This space is filled by the dark housing ring and the lit bars. |

Feature reads (side view):
- **Drum:** a cylinder, with flats implied by the plates. The side plates wrap the top and bottom.
- **Upper stepped shield plate:** a large plate with a **stepped profile**. It has a raised rectangular top tab (x 270 to 450, y 90 to 150); a **mesh-grille window** just under the tab (x 300 to 445, y 155 to 195); a diagonal notch step on the right that drops to a second level; and a second **mesh-grille window** in that lower-right step (x 425 to 580, y 240 to 305). The plate's lower edge is a horizontal ledge at about y 350.
- **Waist band:** a horizontal centre band at mid-height. **Twin hydraulic pistons** sit at each end of the band and point axially toward the adjacent joints: cylinder, rod and end-fitting (x 140 to 250 left, x 520 to 640 right). A central **lower grille slot** (x 345 to 470, y 425 to 485) sits between **two vertical bracket blocks** (x 300 to 345 and x 470 to 510).
- **Lower plate:** a large plate below the waist band (y 490 to 610), with a recessed panel and corner bolts.
- **Fasteners:** round, slotted/hex bolts at plate corners, about 6–10 per visible side.
- **Joint housing:** a thick dark ring with a raised lip on both faces.
- **Glow bars:** **segmented** vertical emissive bars, separated by thin dark ribs. They sit inside the housing and are visible as lit strips around the circumference (most visible at the side and top). Glow colour core ≈ #71CCBD (median of the lit pixels, (113,204,189)), saturating to near-white mint at the hottest points.
- **Mesh grilles:** a fine diamond/woven wire mesh behind a frame. They are dark, with lighter wire highlights.

Neck segments (REFERENCE x 560 to 900, y 150 to 850) read with **heavier, overlapping collar plates** and larger flat panels than the coil segments. The lit joints show as **partial arcs**, because the plates overlap at the bends. See pushback P6.

## 4. Tail (tail-closeup.png, 652×493; REFERENCE x 1280 to 1870, y 900 to 1200)

- **Taper run:** the last 2–3 segments before the tip taper. Diameter falls to about 0.45–0.55 D at the base of the finned tip. These segments keep the plate language: ribbed plates and smaller grilles. One has a **circular port/round fitting** (close-up x≈460, y≈355). The lit joints thin out and the last visible glow arc is at the start of the taper.
- **Finned terminal:** an elongated **torpedo/missile body**, about 2.5–3 × its base diameter long, ending in a blunt **nose cone with a small round nozzle hole** at the tip. It carries:
  - a **dorsal swept fin** near the cone rear, with a notched trailing edge (close-up x 140 to 230, y 310 to 345);
  - a **pair of lateral/ventral swept fins** at the rear (x 70 to 110, y 370 to 390, and x 230 to 300, y 400 to 440);
  - **two horizontal-slat grille vents**: one large on the upper flank with about 7 slats (x 195 to 260, y 360 to 395), one smaller near the nose (x 60 to 100, y 405 to 430);
  - riveted plate seams.

## 5. Material read (all images)

| Channel | Read | Evidence |
|---|---|---|
| Base | **Dark worn gunmetal**, slightly warm (a faint yellow-brown cast, R≈G>B). | Median non-glow foreground (80,80,74). Luminance p5/p50/p95 = 2 / 77 / 210. |
| Metalness | Fully metallic. The reflections are tinted, broad and soft. | Top-plate sheen. |
| Roughness | Medium (≈0.35–0.55) with **per-plate variation**: some plates read more polished and brighter, others duller. | Neighbouring plates differ visibly in value and sheen. |
| Edge wear | Bright, worn **bare-steel edges** on plate bevels and fin edges. | The p95 luminance of 210 sits on edges and highlights. |
| Scratches | Fine, directional, light scratches over the flat plates. | Visible on the skull, snout and segment plates. |
| Grime/rust | **Brown-orange rust spotting and grime in recesses**, seams and under ledges (most visible in segment2-closeup). There are small rust pits on flat plates. | Warm dark pixels in the seams; segment2-closeup corner medians (82,73,65). |
| Recess darkness | Strong ambient occlusion in seams, grilles and the housing gaps. | — |
| Emissive | Teal-mint. Joint bars median #71CCBD. The eye runs from a white-hot #F8FDFF core to a saturated #0C8B6C rim. Emissives appear only in the eye and the joint bars. | Lit-pixel median, eye radial profile. |

## 6. What the reference does NOT show (do not invent)

- No open mouth, teeth or tongue.
- No legs, spikes or dorsal ridge beyond the 3 head fins.
- No glow on the tail tip, the fins or the head plates.
- No cables or hoses beyond the head-to-collar piston and the segment pistons.
- No decals or text. The "placard" is a blank raised plate.

---

## 7. Clay verification and verdicts (Decision 29 form: problem / evidence / alternative)

Sizes as found at `C:\Users\Moore\`. Each was copied to the workspace and its SHA-256 matched the source. All sizes equal the brief's numbers.

| Base | Size as found | SHA-256 | Tris / verts | Connected comps | Non-manifold edges | Bounds (glTF units) |
|---|---|---|---|---|---|---|
| hunyuan-head.glb | **6,246,676 B** | 5e953eef…2d68 | 352,296 / 168,060 | 3 (1 main + 2 specks of 34/28 v) | 22,966 | 1.96 × 0.76 × 1.93 |
| hunyuan-segment2.glb | **10,452,216 B** | 59135745…8015 | 588,568 / 282,249 | 7 (A 186,899 v; B 94,997 v; 5 specks) | 33,292 | 1.48 × 1.96 × 1.32 |
| hunyuan-tail.glb | **10,083,376 B** | 812328ba…f0c | 615,828 / 224,253 | 2 (1 main + 1 speck) | 211,194 | 1.96 × 1.93 × 0.59 |
| hunyuan-test-snake.glb (pose ref only) | 12,935,016 B | d2c12637…de86 | 801,942 / 275,775 | 2 | 315,824 | 1.96 × 1.96 × 1.46 |

Evidence: `source/inspect_r1.py` (bmesh component walk, bounds, manifold count). Workbench clay previews (**iteration previews only, not judged captures**) are in `r1/*_{front,side,top,3q,back3q}.png` in the ticket workspace.

### Head: USABLE WITH NAMED DEFECTS
- **D-H1. The file is a head plus about 6 neck segments.** A C-shaped run of neck segments hangs off the skull, all in ONE connected component. The brief describes it only as a "plated skull". Evidence: front and 3q previews. *Alternative:* section-cut at the collar plane behind the vent box. Use the skull only as the head form reference. Do **not** use the clay neck segments: they are lumpy, melt-softened plates.
- **D-H2. Softened plate language.** Seams are shallow and plate edges are rounded. The snout underside is more bulbous than the reference's squared snout. *Alternative:* take massing and plate layout from the clay; take edge crispness and snout squareness from REFERENCE (spec §2).
- **D-H3. Good features present:** the circular eye formation is clean (a raised ring around a flat disc), and it is the correct seat for the lens. The vent box with slats and the rear piston rod are legible. The 3 crest fins are present but thin; they fuse into one blade in the straight-on view.
- **D-H4.** 2 floating specks and about 23k non-manifold edges (marching-cubes artefacts). These are irrelevant, because the head is rebuilt as clean retopo.

### Segment (segment2): USABLE WITH NAMED DEFECTS
- **D-S1. The melt is not only the detached appendage.** Component B (94,997 v, +Y) is the detached melted neighbour; discard it. But component A, the clean drum, **also carries a fused partial neighbour** (bulging melted plates past its +X joint ring). *Alternative:* plane-cut A at its +X housing-ring face, then mirror or derive the joint from the clean −X end.
- **D-S2.** A drip spike hangs under the drum. The end face is a cupped, hollow shell. The housing ring and insert hide both, so this costs nothing.
- **D-S3. Good form match** to segment2-closeup: the stepped shield plate with top tab, the notch step, the right window, the waist band with twin pistons, the centre slot between brackets, and the lower plate. **No mesh grilles and no glow bars are in the clay.** Those are modelled per spec §3.

### Tail: USABLE WITH NAMED DEFECTS, with PUSHBACK
- **D-T1. A ground sheet is fused into the mesh.** A large flat floor/shadow slab from the generation (visible in the top and 3q previews) is part of the main component. *Alternative:* delete faces on the slab plane before reading form.
- **D-T2. The terminal segments are the worst part of this clay.** The ~2 segments just before the finned tip are melted and lumpy, with no legible plates. The best segments are at the far (thick) end of the run, and they do not taper. The brief's instruction to "take the terminal ~2 segments + finned tip" would import the weakest geometry. *Alternative (proposed):* take the **finned tip** from this clay. It is well-formed: a torpedo cone with a tip, a dorsal fin, paired lateral fins, a side rod and grille relief. Build the 2 taper segments as **scaled/tapered derivatives of the hero segment module** (from segment2), and use the tail clay only for taper ratio and curvature. *Fallback:* one fresh Hunyuan shape generation (~3 min, fp16 v2.1) of ONE taper segment framed straight-on, cropped from tail-closeup.png.

### Monolith: pose and silhouette reference only, as briefed
It also contains a fused ground plane. Its pose matches REFERENCE §1 (raised S-neck, one ground loop, tail sweeping out to the finned tip). None of its geometry will be used.

### Pushback on the brief / technical assumptions
- **P1. Backdrop colour.** `REVIEW-STAGING.md` says "plain mid-gray". The sampled reference is #C1C1BF (§0), and the later owner rule (seat rule 2) says the backdrop must match the reference. *Proposal:* judged captures use #C1C1BF plus a shadow-catcher.
- **P2. Eye aperture blades vs the image.** The brief requires aperture blades. The reference shows none: inside r≈35 px it is a smooth radial glow with a white core. Prominent dark blades would *lower* the match score. *Proposal:* model the blades (the brief wins on structure), but recess them under the cover and behind the emissive core, so the captured read stays the smooth glow profile in §2. Producer to confirm.
- **P3. Clay scale is meaningless across bases.** Each base is normalised to a ~1.96-unit bounding box, so the head is not to scale with the segment. *Proposal:* set all section scales from the reference ratios (head H ≈ 1.2–1.4 D; drum L:D ≈ 0.85; tail cone base ≈ 0.5 D), not from the clay.
- **P4. Clay detail density.** Clay surface detail is at blob scale and every hard edge is softened. Per seat rule 7, the grilles, fasteners and vents are modelled geometry rebuilt from the spec. The clay is used only for massing and plate layout. "Using its clay base as the form reference" is read in that sense.
- **P5. The ≤1,600-tri module budget is tight** for drum + stepped plates + 3 framed grilles + 4 pistons + housing + segmented bars. It is achievable, as R4 hit 1,600 exactly with a similar list. Grille *mesh* would have to be a thin modelled lattice or an alpha-free normal plus a recessed backplate. *Ask:* confirm that the mesh weave may be a normal map over modelled frames and a recessed backplate (the micro-detail clause of seat rule 7).
- **P6. Neck segments differ from coil segments in the reference.** The neck has heavier, overlapping collar plates (§3), but the brief mandates one instanced hero module. *Options:* (a) accept one module and the neck-read gap; or (b) allow ONE neck-variant module (≤1,600 tris, for the ~6 neck instances), still inside the 30–60k total. *Recommend (b).* Producer decides.
