## P8a checkpoint
Built and reviewed head/full Cycles 32-sample previews with frozen P7 staging. Eye now reads as a complete seated disc; wider skull seams are visible, but the skull/collar remain soft and neck gaps remain open. Not a gate pass. Build counts 13,967 / 1,423 / 2,922 / 56,733.
Source additionally contains R26 plate-interior relaxation and R27 inset frames, UNBUILT at this checkpoint; next action rebuild then review. No new numerical scores.

# P8 — ACTIVE, panel-directed fix round

P7 baseline verified at 361f26b; clean checkout before changes. Opened P7 full-body and head/segment/tail reference comparisons. No geometry changed during inventory. P7 counts: 13966 / 1423 / 2922 / 56732.

Panel FAIL retained: head 5/5; body+tail 6/6; silhouette 5.5/6.5; massing 5.8/5.5; detail 4.7/5. No advancement.

Open, priority order: H2, H6, H12, H4, H9, H10, B9, T2, B10, B8; secondary H3, B3. Head receives first pass. Current evidence visibly shows weak panel relief, exposed/incomplete eye seating, soft snout and neck discontinuity. No new self-scores yet.

Recovery: baseline build and staged blend remain untouched; source/build_fix.py and source/head_fix.py drive next build. Fresh previews and STATUS required at each checkpoint. Deadline 21:00 CDT.

---

# STATUS — snake-reassembly ATTEMPT 2

## FIX-PASS DELIVERY P7 (2026-10-18 CDT) — pushed, NOT READY for acceptance
- P7 = P6 + R23 fin height/thickness (0 tris). Budgets 13,966 / 1,423 / 2,922 / 56,732 — PASS.
- Final judged clay captures `fix/captures/fix-p7-*` (Cycles 256/.01/OIDN 1920×1080, #C1C1BF, catcher, clay only), overlays `fix/overlays/p7-{head,seg,tail}`, sections `fix/sections/p7_*`, NOTE §A–D (refine log R6–R23, render-only scorecard, medians ≈5.0/5.0).
- Remaining below gate: H4 nostril, H3 mouth, H9 frames, B3 grille, B10 neck kink. Seg overlay solve loose (41.8 px; landmarks predate S0-3).
- No blockers. Blind panel re-gate is the next step.

## CHECKPOINT P6 — handover #5 (Opus low, 2026-10-18 ~16:30 CDT) — CONTINUING, no producer wait

P5 (4549cf8) committed SOURCE changes only; it never rebuilt or rendered and STATUS was still the P4 text. P6 = first build + render of the P5 sources. No new geometry edits in P6.

### Inventory — fix list vs P5 sources (implementation ≠ success; see render review)
| Item | In P5 source? | P6 render review |
|---|---|---|
| F8 machined plates on S0-3 drum | yes (traced panels, body_fix) | plates/fasteners/grille frames read machined; grilles are slats not mesh (P5 ruling: weave = material phase) |
| S0-4 tail stretch L/D 2.7 | yes (axial_k 1.53) | tip reads torpedo; taper pieces faceted |
| H4 nostril deepen | yes | still weak at preview res |
| mouth groove | partial (H9-lower inset) | groove visible as a line, shallow |
| H2 seams / H9 frames cut in | yes (CUT ops) | seams visible as cut lines; frames soft |
| H8 piston crisper | yes (collars) | pistons read; ok-ish |
| H5 fins thickened + separated | frames, no through-cut | fins separated; still thin/short vs reference |
| seam-speckle re-weld | not explicitly | no black speckle visible in P6 previews |
| B10 neck kink | lap .09 | neck still abrupt at coil base |
| T5 vents | slats | slats visible on tip |
| B7 fasteners | yes (480 tris) | visible on plates |

### Budgets (P6 build, == P5)
Head 13,966/14,000 · module 1,303 + insert 120 = 1,423/1,450 · tail 2,922/3,000 · assembly 56,732 (30k–60k). PASS technical.

Previews `fix/previews/fix-p6-*` = Cycles 32spp ITERATION PREVIEWS, clay only, #C1C1BF, shadow catcher. Acceptance: NOT READY / ungated.

---

## WIP-CHECKPOINT P4 — STANDING BY (producer order, 2026-10-18 CDT)

**No further building until producer resume. Full fix-pass deadline remains 18:00 CDT.**
This is a recoverable work-in-progress checkpoint, NOT acceptance or final delivery.

### Done

- Reconciled takeover at `9b5e26a`; opened reference, head close-up and P3 head preview.
- Built inherited pending scripts successfully as P4; no new geometry edits in this checkpoint turn.
- Saved `fix/snake-v2-r2-fix.blend`, build log and required cached build inputs.
- Rendered and visually inspected fresh full-body, head, module, tail and tail-top previews in `fix/previews/fix-p4-*`.
- Cycles GPU 32 spp / adaptive .05 / OIDN / 960×540: **ITERATION PREVIEWS ONLY**, not judged captures. Plain #C1C1BF backdrop, shadow catcher, shaped lights, one neutral clay material; no glow.
- Verified P4 cameras, lights, catcher and staging settings equal P3. PNG dimensions, corner samples and hashes recorded in `fix/preview-checks.json`.
- Inherited head/tail comparison evidence retained under `fix/evidence/`; these are pre-P4, not refreshed P4 overlays.

### Technical checks

| Part | P4 tris | Hard budget | Result |
|---|---:|---:|---|
| Head | 13,966 | ≤14,000 | PASS |
| Module + insert | 1,443 | ≤1,450 | PASS |
| Tail section | 2,846 | ≤3,000 | PASS |
| Full assembly | 57,216 | 30,000–60,000 | PASS |

Build assertions and render clay-purity checks passed. This is a limited technical PASS, not proof of local-form preservation or acceptance.

### In progress — paused

Inherited R6–R14 work is built: drum stretch and traced machined panels; head shell repair, fin separation/borders, cut-in seams/recesses and fitted hardware; tail stretch/vents; neck posing. Exact operations remain in `fix/build-log.json`. Their success is NOT inferred from parameters.

P4 render review: head retains soft uneven surfaces and weak nostril/frame definition; fins appear crowded/short against reference. Neck bends remain abrupt with exposed joint gaps. Module fasteners, slats and pistons are visible but plates read broad and simplified. Tail taper pieces remain faceted and under-detailed; tail fins/vent borders are soft. **Acceptance: NOT READY; R2 blind-panel failure is not cleared.** No new numerical self-score assigned at this WIP checkpoint.

### Remains after producer resume

- Resolve reference fidelity of the above features and confirm R1–R5 preservation with same-angle evidence.
- Fresh production-quality 256-sample-class staging captures, current head/body/tail overlays, four section plots.
- Continue NOTE refine log R6+ and render-only self-scorecard; flag unreviewed forms UNREVIEWED.
- Blind-panel re-gate and full delivery checkpoint. No acceptance advancement before gate passes.

### Recovery

Build from `source/build_fix.py -- <accepted-clay-directory> <fix-directory>` in Blender 4.5.14. The fix directory includes `head-reduced.npz` and `tail-volume.npz`, used by the current build; accepted clay GLBs remain in the ticket's original clay directory. Render via `source/render_fix.py -- <fix-directory> preview fix-p4 full,head,seg,tail,tail_top <fix-directory>/previews/fix-p3-render-settings.json` after opening the saved blend.

Prior R2 STATUS is preserved in `fix/evidence/status-before-p4.md`. NOTE's existing scorecard is historical R2 evidence, not P4 scores.
