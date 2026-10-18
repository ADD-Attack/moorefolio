# STATUS — snake-reassembly ATTEMPT 2

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
