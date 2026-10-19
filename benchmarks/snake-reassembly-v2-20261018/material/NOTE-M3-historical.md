# NOTE — material fix M3, 2026-10-19

Continues from `20b2545`. Geometry stayed frozen. This scorecard is from the five M3 production captures only. Technical checks are not acceptance. Call: **NOT READY**.

## What was looked at before the pass

Exercise 2 review captures (head and full body) were not found. No file in this workspace or the Cadre checkouts is named as that 2026-10-17 materials exercise.

The Exercise 2 texture set that Exercise 3 uses with `snake_full.glb` is on disk: albedo, ORM, normal, and glow under `workspace-studio-builder-2/exercise3-input/game-demo/models/`. I opened the albedo. It is a cool blue-grey panel atlas. Those UVs do not match the v2 smart-projected islands, and the color is the opposite of the warm reference, so the images were not applied.

R4B was not a labeled file. I opened `r4-fresh-head-closeup.png` and `r4-fresh-full-body.png` from `forge-snake-r4-fresh`. That is a different mesh. Its eye has a pale core and a green ring, which is the radial idea used here. Its packed ORM was not transferred onto these UVs.

## What changed

M1d was smooth, cool, and dark, and the panel put texture maps at 2.0 / 2.5. M3 bakes object-space plate steps, seam darkening, pit marks, and orange-brown rust into the maps. Roughness stays in a satin band. The eye radius is painted on the lens vertices (a hot core, a mint ring, a darker teal rim) and the eye UV islands were scaled up so the bake can hold that.

The first M3 bake reused the existing M1d PNGs and the renders looked unchanged. Those PNGs were deleted and the bake was run again. `source/bake_materials.py` no longer reuses an existing PNG.

## Captures reviewed

Cycles GPU, 256 samples, adaptive 0.01, OIDN, 1920×1080, backdrop `#C1C1BF`, frozen M1b cameras. All five were viewed before scoring.

- `material/captures/m3-full-body.png`
- `material/captures/m3-head-closeup.png`
- `material/captures/m3-seg-detail.png`
- `material/captures/m3-tail-detail.png`
- `material/captures/m3-tail_top-detail.png`

## Budgets

`source/audit_material.py`: fingerprints unchanged, GLB triangles match. Technical PASS. Not an acceptance pass.

| Part | Tris | Cap |
|---|---:|---:|
| Head | 13,968 | 14,000 |
| Module + insert | 1,431 | 1,450 |
| Tail | 2,970 | 3,000 |
| Assembly | 57,006 | 57,600 |

GLB `material/snake-p8-material.glb` SHA256 `f704d979ac15e66f7a066c3ac8d855471010afd1745c12c3e1cc3ac0fedadbc6`.

## Map sizes (bytes)

Head 2048: BaseColor 972,479 / ORM 1,180,425 / Normal 850,160 / Emission 56,448.

Segment hero 1024: 315,790 / 733,665 / 768,419 / 13,922. Segment neck 1024: 333,792 / 739,093 / 759,428 / 13,922.

Tail taper 1: 280,489 / 700,152 / 734,275 / 13,922. Taper 2: 276,731 / 712,017 / 783,059 / 13,922. Tip: 393,773 / 583,563 / 907,718 / 13,922.

Glow inserts are 256. Non-glow emission maps stay small.

## Self-scorecard — these five renders only

MATCH / QUALITY. Shape is still the frozen P8 mesh. I am not rescoring it as if the maps rebuilt the head.

### 1. Head features

H1 5.5/5.5, H2 5.0/5.0, H3 4.5/4.5, H4 5.0/5.0, H5 4.0/4.5, H6 5.0/4.5, H7 6.5/6.0, H8 6.0/5.5, H9 4.5/4.5, H10 5.0/5.0, H11 4.0/4.0, H12 4.5/4.5.

H6 is the only change from the M2 card. The production head shows a brighter core and a darker green edge. It is not a clean white / mint / teal target. The other head marks are the same clay debts.

MATCH median 4.75, mean 4.96, range 4.0–6.5. QUALITY median 4.75, mean 4.88, range 4.0–6.0.

### 2. Body and tail

Unchanged from the M2 shape card. MATCH median 6.0, mean 6.20, range 5.5–7.5. QUALITY median 5.5, mean 5.77, range 5.0–7.0.

Rust and cracks sit on those forms. They do not fix the drum notch, the grille weave, or the short tail tip.

### 3–4. Silhouette, massing, modeled detail

| Category | M med / mean / range | Q med / mean / range |
|---|---|---|
| Silhouette (full, head, tail) | 6.0 / 5.83 / 5.0–6.5 | 5.5 / 5.33 / 4.5–6.0 |
| Massing (coil, head, drums) | 6.5 / 6.00 / 5.0–6.5 | 6.0 / 5.50 / 4.5–6.0 |
| Modeled detail (bolts, grilles, plates, fins) | 5.75 / 5.75 / 4.5–7.0 | 5.25 / 5.38 / 4.5–6.5 |

### 5–9. From full, head, segment, tail

| Category | Scores | med / mean / range |
|---|---|---|
| Texture maps | 6.0, 6.5, 5.5, 6.0 | 6.0 / 6.00 / 5.5–6.5 |
| Bump / normal | 5.5, 6.0, 5.0, 5.5 | 5.5 / 5.50 / 5.0–6.0 |
| Color | 6.0, 6.5, 5.5, 6.0 | 6.0 / 6.00 / 5.5–6.5 |
| Materials | 6.0, 6.0, 5.5, 6.0 | 6.0 / 5.88 / 5.5–6.0 |
| Lighting | 6.5, 6.5, 6.0, 6.5 | 6.5 / 6.38 / 6.0–6.5 |

Rust reads on the head, the neck, and the lower body plates. Seams are darker. The metal is warmer than M1d and the broad plates are not chrome. The rust is in large patches, not fine grime, and a lot of plate area is still a flat dark grey. The normal reads as cracks more than machined pitting.

The tail-top capture still shows a loose fragment and a joint bar off the taper. That is existing geometry. This pass did not move it.

## Call

**NOT READY.** Texture, color, and bump are up from the panel floor. No category median is 7.5. Head shape is still the binding miss, and the maps are not fine enough to carry the material gate alone.
