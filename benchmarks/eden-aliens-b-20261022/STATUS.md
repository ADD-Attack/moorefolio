# STATUS — EDEN-3D-01 aliens_b — WIP-CHECKPOINT 1 (13:5x CDT)

**Done**
- Pack SHA-256 verified (18d6b81f…d52ca0) and BRIEF read. Vision works (reference + previews viewed in-session).
- Feature list frozen: FEATURES.md (F1–F5 amended with F1b, F1c, F2b and two-part legs).
- ComfyUI engine verified up (0.41.0; an existing instance on Windows :8188 — it is unreachable from WSL localhost, so sends go through Windows embedded python, scripts/hy_send.py).
- Hunyuan c1-wholebody-s42 APPROVED as base; c2-mouth-s42 DECLINED. Previews (Workbench iteration previews, NOT judged) in previews/.

**In progress**
- c2b mouth re-request (wider crop, seed 7); c3-tail-s42 send.

**Remains**
- Choose the mouth source → segment the c1 mesh into nodes: body, mouth (with modeled interior), leg_FL/FR/BL/BR, tail_01..03+. Decimate/retopo from the formed mesh to ≤45k.
- Cycles clay staging (full + mouth detail), self-score categories 1–4, then NOTE.md + GLB + blend → delivery by 16:30. STOP.

**Tri counts so far:** c1 raw 686,512; c2 raw 552,698 (declined). Nothing decimated yet.

**Flags (not blocking)**
- Branch `eden-aliens-b-input-20261022` was not on origin at 13:46 (fetch: couldn't find remote ref). I am working from the muse.ai zip, whose SHA verified.
- The gateway `view_image` tool returns "Gateway caller authority is no longer active". The file reader shows images fine, so vision is not blocked.
