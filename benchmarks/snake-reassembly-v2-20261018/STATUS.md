# STATUS — P8 fix-round delivery (2026-10-18, before 21:00 CDT)

**Delivered candidate: P8d. Technical PASS; acceptance NOT READY.** P7 panel FAIL remains in force. This is a fix-round preview delivery, NOT a clay-gate pass. No material-phase work.

## Current files

- Build: `fix/snake-v2-r2-fix.blend`; reproducible sources under `source/` plus committed cached inputs.
- Fresh reviewed previews: `fix/previews/fix-p8d-{full-body,head-closeup,seg-detail,tail-detail,tail_top-detail}.png`.
- Cycles GPU 32 spp / 960×540 / denoise: **ITERATION PREVIEWS ONLY**. One neutral clay material, no emission/glass/bloom. Frozen P7 cameras/lights/catcher/backdrop; full/head clear background samples match #C1C1BF. Verification: `fix/p8-preview-checks.json`.
- Refreshed same-angle comparison evidence: `fix/overlays/p8-{head,seg,tail}_{sbs,overlay,render}.png`. Workbench iteration evidence. Residuals: head 9.5 px, segment 41.8 px (loose inherited solve), tail 14.0 px.
- Four refreshed, individually reviewed head sections: `fix/sections/p8d_*`.
- Render-only 27-feature review, unreviewed flags, categories 2–4, refine log and open items: **P8-NOTE.md**. NOTE.md's P7/R2 material is historical.

## Hard-budget audit

| Part | Triangles | Limit | Result |
|---|---:|---:|---|
| Head | 13,968 | 14,000 | PASS |
| Module + insert | 1,431 | 1,450 | PASS |
| Tail | 2,970 | 3,000 | PASS |
| Assembly | 57,006 | 57,600 | PASS |

Independent saved-blend audit: `fix/audit-p8.json`. Technical checks are not resemblance scores.

## Work performed / still open

Head-first cycles addressed H2 seams/plate interiors, H6 current-mesh eye seating, H12 formed ridge vertices, H4 recess/rim, H9 frames and H10 collar finish. Followed with B9 bar separation, T2 shoulder/plate seams, B10 overlap, B8 housing roundness; secondary mouth bevels and crossed grille bars.

**All named low-scoring features remain open for fidelity review.** Key remaining defects: soft skull plates lacking independent overlap volume; simplified eye radial layering; weak integrated ridge/nostril surround; soft collar without stacked plates/top fitting; blank neck plates and gaps; simplified terminal and module plate contours. Improvements are incremental. No feature is closed from implementation alone. T4 fin pair and hidden eye/internal forms remain explicitly unreviewed where evidence does not expose them.

The neck rotation test (`fix/p8-neck-test.blend`, `fix-p8neck-head-closeup.png`) was REJECTED and is not the candidate. P7 production captures are historical, not relabeled as P8.

## Checkpoints and recovery

Verified P7 base: 361f26b. P8 checkpoints pushed: 83b2f98 inventory; e58e361 P8a; 4ba3b6a P8b; 3363388 P8c. Current commit adds P8d and its reviewed delivery evidence.

Build with Blender 4.5.14: `-b -P source/build_fix.py -- <accepted-clay-directory> fix`. Render after opening the candidate: `-P source/render_fix.py -- fix preview fix-p8d head,full,seg,tail,tail_top fix/captures/fix-p7-render-settings.json`.

No active execution blocker. Recovered: unavailable native Git CA path (gateway push works); stale taper smooth-face indices after decimation (removed on topology-changing copies; rebuilt/audited successfully).
