## Material fix M3 — NOT READY (2026-10-19, after panel FAIL on 20b2545)

M3 rebake is the candidate. The first bake had reused the M1d PNGs; those were deleted and baked again. Geometry fingerprints unchanged. Budgets PASS: head 13,968 / 14,000, module+insert 1,431 / 1,450, tail 2,970 / 3,000, assembly 57,006 / 57,600. GLB SHA256 `f704d979ac15e66f7a066c3ac8d855471010afd1745c12c3e1cc3ac0fedadbc6`.

Judged captures: `material/captures/m3-{full-body,head-closeup,seg-detail,tail-detail,tail_top-detail}.png`. Scorecard: `material/NOTE.md`. Exercise 2 review shots were not found. The Exercise 3 copy of that texture set does not match these UVs and was not applied. R4-fresh head/full captures were viewed; that mesh was not transferred.

Render-only call remains **NOT READY**. Texture/color/bump are above the panel floor and still under 7.5. Head-feature MATCH median 4.75. No self-approval.

## Material delivery M2 — NOT READY, panel FAIL (2026-10-19)

Candidate is baked M2 from the M1d shaders. Geometry fingerprints unchanged. Budgets PASS: head 13,968 / 14,000, module+insert 1,431 / 1,450, tail 2,970 / 3,000, assembly 57,006 / 57,600. GLB `material/snake-p8-material.glb` SHA256 `d4bccee2dfe6f75de80d17543d6d0c26853ef93f8d555b07bb03eed4ab8e50bc`.

Judged captures: `material/captures/m2-{full-body,head-closeup,seg-detail,tail-detail,tail_top-detail}.png` (Cycles GPU 256 / adaptive 0.01 / OIDN / 1920×1080). Scorecard and map list: `material/NOTE.md`. Comparison plates are side-by-side with REFERENCE.png at the frozen review cameras, not a solved warp: `material/comparisons/`.

Render-only medians stay under 7.5. Head features MATCH median 4.75. Body+tail MATCH median 6.0. Wear median 4.5. Color median 5.0. Chrome on the broad plates is reduced; the metal is still too dark and cool, rust barely reads, and the eye is a flat green disc. Clay debts (eye radial layering, skull plate volume, collar stacking) are still visible and were not rebuilt. **NOT READY.** No self-approval. Producer convenes the material gate.

Recovery: M1b `a15c2b3`. Correction checkpoint `f21f55a` (M1c rejected dark preview + M1d shaders).

# Material phase — history

QA Clay assembled gate PASSED BY OWNER OVERRIDE at 20:45 CDT on P8d @17e59a9. P7 panel FAIL and P8 render-only scores remain historical calibration. Eye radial layering, skull plate volume and collar stacking remain open clay debts; they do not block materials and are NOT permission to rebuild geometry.

M1 (`d8ae029`) assigned procedural shaders. Plate highlights were too chrome-like and emissives over-bright. Bake had not been run. The 2026-10-18 23:05–23:37 material run did no online research.

Hard budgets remain 14,000 / 1,450 / 3,000 / 57,600. No vertex-position, topology or instance-transform changes were made in this phase.

Deadline for this delivery was 2026-10-19 17:00 CDT.
- 2026-10-20 M5d: gunmetal value, recess grime, thin joint line; captures `material/captures/m5d-*`; self-check medians 5.5/5.5 → NOT READY (frozen-geometry blockers). See material/NOTE.md.
- 2026-10-20 Material gate PASSED BY OWNER OVERRIDE on M5d @dc998d0 (panel 5.0/5.5). Debts carried; see material/NOTE.md.
